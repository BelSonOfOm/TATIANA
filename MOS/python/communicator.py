import os
import sys
import json
import struct
import subprocess
import threading
import zlib
import flatbuffers
import requests

# Local semantic geometry (single source of truth, EMBED_DIM=384). Runs on CPU,
# costs no API quota. Imported under an alias so `embed` isn't shadowed locally.
from embeddings import embed as embed_text, EMBED_DIM

# P1: concept-name -> vertex-id resolution against the live knowledge base.
from concept_resolver import ConceptResolver, DEFAULT_DB

# Generated FlatBuffers bindings (regenerate with:
#   vendor/flatbuffers/flatc.exe --python -o python/ proto/operad.fbs)
try:
    import mos.fbs.OpType as OpType
    import mos.fbs.Operator as Operator
    import mos.fbs.OperadNode as OperadNode
    import mos.fbs.OperadDAG as OperadDAG
    import mos.fbs.ConstraintPayload as ConstraintPayload
    import mos.fbs.ConstraintType as ConstraintType
    _FBS_OK = True
except ImportError as _e:
    _FBS_OK = False
    print(f"[WARNING] Could not import generated flatbuffers ({_e}). "
          "Run: vendor/flatbuffers/flatc.exe --python -o python/ proto/operad.fbs")

def crc32_ieee(data: bytes) -> int:
    """The same CRC-32 `main.cpp:compute_crc32` computes, for the IPC frame.

    That function is the textbook reflected CRC-32 (init 0xFFFFFFFF, polynomial
    0xEDB88320, final complement) -- i.e. IEEE 802.3, which is exactly what
    `zlib.crc32` implements. Using zlib rather than re-deriving the bit loop in
    Python keeps the two sides from drifting and is ~200x faster on a 1 MB DAG.
    `python/test_full_loop.py` carries the explicit bit-banged version, so the
    two implementations cross-check each other.
    """
    return zlib.crc32(data) & 0xFFFFFFFF


class Communicator:
    """
    The Communicator (Frontend LLM Layer).
    Acts as the Projection Morphism (pi) from the Language Space (S) to the Universal Syntax Space (U).
    """
    def __init__(self, model: str = None, api_key: str = None, kb_path: str = None):
        self.c_chat = [] # Episodic Cache (C_chat)

        # P1. name -> id against the SAME knowledge base the engine opens, so
        # both sides agree on what an id means by construction rather than by
        # coincidence. main.cpp opens "mos_brain_ipc.db" relative to the working
        # directory it inherits from us, so the default matches without either
        # side being told twice.
        self.resolver = ConceptResolver(kb_path or DEFAULT_DB)
        self.unresolved_names = {}

        # Engine telemetry, tapped by the listener thread. P4 reads it to build
        # the trajectory; nothing else depends on it.
        self.engine_lines = []
        self._engine_lock = threading.Lock()
        if self.resolver.loaded:
            print(f"[Communicator] P1 resolver: {self.resolver.size} concept(s) "
                  f"in {self.resolver.db_path}")
        else:
            # Cold start is legitimate, but it is not silent: with nothing in
            # memory every name resolves provisionally, and reading a run's
            # support columns without knowing that would be misleading.
            print(f"[Communicator] P1 resolver: NO STORE ({self.resolver.load_error}). "
                  "Every named concept will get a provisional id.")
        # SPLIT BRAIN: reasoning runs REMOTELY on Groq (this machine cannot host a
        # local LLM); embeddings run LOCALLY via embeddings.py so that ingesting
        # documents never consumes API quota.
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            print('[Communicator] WARNING: GROQ_API_KEY is not set. Set it with:'
                  '  setx GROQ_API_KEY "your_key"   (then reopen the terminal).')

        # Start C++ Engine via IPC (pipe stdin)
        mos_exe_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "build", "Debug", "mos.exe")
        if not os.path.exists(mos_exe_path):
            mos_exe_path = "mos.exe" # Fallback if in PATH
            
        print(f"[Communicator] Launching C++ IPC Server ({mos_exe_path})...")

        # E7. Tell the engine exactly where to append assembly events, rather
        # than letting it fall back to a cwd-relative default -- we do not pass
        # cwd= below, so the child inherits ours, and the log would otherwise
        # land wherever the user happened to run this from. The registry says
        # this data is impossible to recover later, so "usually the right
        # directory" is not good enough.
        from assembly_log import DEFAULT_PATH as ASSEMBLY_LOG_PATH
        child_env = dict(os.environ)
        child_env["MOS_ASSEMBLY_LOG"] = ASSEMBLY_LOG_PATH
        print(f"[Communicator] E7 assembly log -> {ASSEMBLY_LOG_PATH}")

        try:
            # BINARY PIPES, NOT TEXT. This was `text=True`, which makes stdin a
            # TextIOWrapper -- so `stdin.write(bytes)` raises TypeError and the
            # FlatBuffer never left the process. Combined with the missing CRC
            # word above, the IPC path could not have carried a single payload.
            # The engine also puts stdin in _O_BINARY (main.cpp:34) precisely so
            # that no newline translation touches the frame; sending text from
            # this side would undo that on every 0x0A byte.
            #
            # stdout stays a pipe and is decoded in the listener thread instead,
            # where a malformed UTF-8 byte can be replaced rather than killing
            # the reader.
            self.cpp_process = subprocess.Popen(
                [mos_exe_path, "--ipc-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                env=child_env
            )
            
            # Start background listener thread
            self.listener_thread = threading.Thread(target=self._read_cpp_output, daemon=True)
            self.listener_thread.start()
            
        except Exception as e:
            print(f"[Communicator] Failed to launch C++ engine: {e}")
            self.cpp_process = None
            
    def _read_cpp_output(self):
        """Asynchronously reads from the C++ process stdout and prints to the terminal."""
        if not self.cpp_process or not self.cpp_process.stdout:
            return
        
        try:
            # The pipe is binary now (see Popen), so decode here. `replace`
            # rather than `strict`: the engine writes UTF-8, but a torn write at
            # process exit must not kill the reader and lose the last lines of
            # a run's diagnostics.
            for raw in iter(self.cpp_process.stdout.readline, b''):
                if raw:
                    line = raw.decode("utf-8", errors="replace")
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    # P4 needs the engine's own telemetry (rho, Q, the P3 gap)
                    # per tick, and the engine reports it on this stream. Kept
                    # under a lock because the reader is a background thread and
                    # run_p4.py drains this list from the main one.
                    with self._engine_lock:
                        self.engine_lines.append(line.rstrip("\r\n"))
        except Exception as e:
            print(f"[Communicator] Listener thread terminated: {e}")
    
    def get_embedding(self, text: str) -> list:
        """
        Real semantic geometry for the sheaf stalk, computed LOCALLY on CPU.

        Delegates to embeddings.py (the single source of truth, EMBED_DIM=384).
        No truncation, no padding, no zero-vector fallback: a silently-wrong
        embedding poisons every distance the C++ engine computes, so we let a
        failure surface instead of manufacturing fake geometry.
        """
        return embed_text(text)

    def invoke_pi_llm(self, prompt: str) -> dict:
        """
        The pi morphism's engine: maps natural language to the categorical syntax (U).

        Runs on Groq (remote). This is the CHEAP, high-frequency call, so it uses
        the small fast model; the scarce budget is reserved for heavy reasoning.
        """
        system_prompt = (
            "You are the Syntactic Projection Operator (pi). Classify the user's input and "
            "project it into an Operad DAG, replying ONLY with a single JSON object.\n"
            "(The literal word 'json' must appear in this prompt for the API's JSON mode.)\n"
            "If the input is purely conversational (greetings, jokes, personal remarks, nonsense), "
            "output exactly: {\"type\": \"NOISE\"}\n"
            "If it contains mathematical reasoning, output {\"type\": \"MATH\", \"nodes\": [...]}.\n"
            "\n"
            "CRITICAL - EXECUTION ORDER: 'children_ids' lists nodes that must execute AFTER this "
            "node. It is NOT a list of prerequisites or sub-parts. Therefore background/assumption "
            "nodes (CONTEXT) must be PARENTS of the operations that rely on them, never children. "
            "A CONTEXT node that establishes an assumption must list the COMPUTE/REASON node in its "
            "children_ids.\n"
            "\n"
            "REQUIRED: exactly one terminal RESPOND node with no children, which every other branch "
            "eventually leads into. Without it the system produces no answer.\n"
            "REQUIRED: at least one SEARCH node, placed BEFORE any COMPUTE or REASON node that "
            "depends on recalled material. This system has a permanent memory of mathematics it "
            "has already read; a question about known mathematics must consult it rather than "
            "being answered from the model's own weights. A DAG with no SEARCH never touches "
            "memory, so nothing is retrieved, nothing co-activates, and the system learns nothing "
            "from having thought about the question.\n"
            "The graph must be connected and acyclic, with a single entry point.\n"
            "\n"
            "OpTypes: CONTEXT (inject an assumption), SEARCH (retrieve external knowledge), "
            "COMPUTE (perform a calculation), REASON (derive/infer), RESPOND (emit the answer).\n"
            "\n"
            "'support' is the list of mathematical CONCEPTS this operator acts on, written as "
            "NAMES, e.g. \"support\": [\"Stokes' theorem\", \"de Rham cohomology\"]. Name the "
            "concepts you are actually reasoning about; do not invent plausible-sounding ones, "
            "and do not list a concept merely because it is nearby. Naming NOTHING is worse than "
            "naming a concept the system has not heard of: an empty support means 'this touches "
            "everything', which forces the operator to run alone.\n"
            "\n"
            "'constraints' apply to CONTEXT nodes only. Each is {\"type\": \"FLUID\"} or "
            "{\"type\": \"RIGID\"}. Use RIGID ONLY for a constraint explicitly stated by the user, "
            "because RIGID is enforced as an unbreakable geometric projection. Anything you infer "
            "or recall yourself MUST be FLUID. Never invent numeric facts (dimensions, signatures, "
            "curvatures) - if the user did not state it, do not assert it.\n"
            "\n"
            "Example: {\"type\": \"MATH\", \"nodes\": ["
            "{\"id\": 1, \"operator\": {\"type\": \"CONTEXT\", \"payload\": \"Assume X is continuous\", "
            "\"support\": [\"continuity\"], \"constraints\": [{\"type\": \"RIGID\"}]}, \"children_ids\": [2]}, "
            "{\"id\": 2, \"operator\": {\"type\": \"COMPUTE\", \"payload\": \"Integrate X over [0,1]\", "
            "\"support\": [\"Riemann integral\", \"continuity\"]}, \"children_ids\": [3]}, "
            "{\"id\": 3, \"operator\": {\"type\": \"RESPOND\", \"payload\": \"Report the integral\", "
            "\"support\": [\"Riemann integral\"]}, \"children_ids\": []}]}"
        )
        
        if not self.api_key:
            print("[Communicator] No GROQ_API_KEY -> cannot run pi. Treating input as chat.")
            return {"type": "NOISE"}

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,          # pi is a projection, not a creative act
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            # NOTE: an API failure is NOT the same as "the user said something
            # non-mathematical". Returning NOISE here would silently route every failed
            # math query to chat and look completely normal. Errors get their own type.
            if response.status_code == 429:
                print("[Communicator] Groq RATE LIMIT (free tier: 30 RPM / 6k TPM / ~1k RPD).")
                return {"type": "ERROR", "reason": "rate_limit", "nodes": []}
            print(f"[Communicator] Groq error {response.status_code}: {response.text[:300]}")
            return {"type": "ERROR", "reason": f"http_{response.status_code}", "nodes": []}
        except Exception as e:
            print(f"[Communicator] Groq call FAILED: {type(e).__name__}: {e}")
            return {"type": "ERROR", "reason": type(e).__name__, "nodes": []}

    def pi_morphism(self, user_input: str) -> dict:
        """
        Projects messy human language into a rigorous mathematical DAG using a real LLM.
        """
        print("[Communicator] Projecting language through Groq (pi)...")
        dag_json = self.invoke_pi_llm(user_input)
        
        if dag_json.get("type") == "NOISE":
            print("[Communicator] Identified as purely conversational noise (Kernel mapping).")
            self.c_chat.append(user_input)
            print("[Communicator] Appended to C_chat. C++ Engine remains asleep.")
            return {"nodes": []}
            
        if dag_json.get("type") == "ERROR":
            # An upstream failure is NOT a classification. Do not fall through and
            # announce "identified as rigorous mathematics" over an error payload.
            print(f"[Communicator] pi FAILED ({dag_json.get('reason')}). "
                  "No DAG produced; nothing will be sent to the engine.")
            return dag_json

        print("[Communicator] Identified as rigorous mathematics. Extracted DAG:")
        print(json.dumps(dag_json, indent=2))

        problems = self.validate_dag(dag_json)
        if problems:
            print("[Communicator] DAG VALIDATION FAILED - refusing to cross the boundary:")
            for p in problems:
                print(f"    - {p}")
            # Do NOT ship a malformed DAG to C++. The engine trusts what it receives.
            return {"type": "INVALID", "nodes": [], "problems": problems}

        return dag_json
        
    @staticmethod
    def validate_dag(dag_json: dict) -> list:
        """Structurally validate a DAG before it crosses the adjunction boundary.

        The C++ engine trusts whatever it receives, so every structural guarantee has
        to be established HERE. Returns a list of human-readable problems; empty means
        the DAG is well-formed. These checks exist because live testing showed the
        model producing: inverted edges, disconnected forests, and DAGs with no
        terminal RESPOND (so nothing was ever returned to the user).
        """
        problems = []
        nodes = dag_json.get("nodes", []) or []
        if not nodes:
            return problems  # empty DAG is legitimate (pure NOISE)

        ids = [n.get("id") for n in nodes]
        if len(set(ids)) != len(ids):
            problems.append(f"duplicate node ids: {ids}")
        id_set = set(ids)

        # Dangling children
        edges = {}
        for n in nodes:
            kids = n.get("children_ids", []) or []
            edges[n.get("id")] = kids
            for k in kids:
                if k not in id_set:
                    problems.append(f"node {n.get('id')} references unknown child {k}")

        # Cycle detection (DFS with colouring)
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {i: WHITE for i in id_set}

        def visit(u):
            colour[u] = GREY
            for v in edges.get(u, []):
                if v not in colour:
                    continue
                if colour[v] == GREY:
                    problems.append(f"cycle detected involving node {v}")
                    return True
                if colour[v] == WHITE and visit(v):
                    return True
            colour[u] = BLACK
            return False

        for i in id_set:
            if colour[i] == WHITE:
                visit(i)

        # Terminal RESPOND: without it the pipeline produces no user-visible answer
        types = [(n.get("operator", {}) or {}).get("type") for n in nodes]
        if "RESPOND" not in types:
            problems.append("no RESPOND node: this DAG would execute and return nothing")

        # At least one SEARCH: without it the engine never reads its own memory.
        #
        # MEASURED, not anticipated. The first P4 run produced DAGs of
        # CONTEXT -> COMPUTE -> REASON -> RESPOND with no SEARCH anywhere, so
        # `retrieved` was 0 on every tick, W was empty, consolidation never ran
        # and Q(t) stayed undefined. The engine was working correctly; it was
        # simply never asked to recall anything. A DAG that skips retrieval
        # reduces MOS to an LLM wrapper -- the reasoning happens entirely in the
        # model's weights, and the permanent store contributes nothing and
        # learns nothing.
        if "SEARCH" not in types:
            problems.append(
                "no SEARCH node: this DAG never consults the knowledge base, so "
                "nothing is retrieved, nothing co-activates, and the consolidation "
                "loop cannot run")

        # Connectivity (undirected): a forest means uncontrolled parallel branches
        adj = {i: set() for i in id_set}
        for u, kids in edges.items():
            for v in kids:
                if v in adj:
                    adj[u].add(v)
                    adj[v].add(u)
        seen = set()
        stack = [next(iter(id_set))]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(adj.get(cur, ()) - seen)
        if len(seen) != len(id_set):
            problems.append(
                f"disconnected DAG: {len(id_set) - len(seen)} node(s) unreachable "
                f"({sorted(id_set - seen)})")

        return problems

    def serialize_to_flatbuffer(self, dag_json: dict) -> bytearray:
        """
        Translates the JSON DAG into a highly optimized binary FlatBuffers payload.
        This physically enforces the Adjunction.
        """
        nodes = dag_json.get("nodes", [])
        if not nodes:
            return bytearray()
            
        print(f"[Communicator] Serializing {len(nodes)} nodes to FlatBuffers binary format...")
        builder = flatbuffers.Builder(1024)
        
        node_offsets = []
        for node in nodes:
            op_data = node.get("operator", {})
            op_type_str = op_data.get("type", "UNKNOWN")
            
            # Map string OpType to Enum
            op_type = getattr(OpType.OpType, op_type_str, OpType.OpType.UNKNOWN)
            
            payload_str = builder.CreateString(op_data.get("payload", ""))
            
            # P1. RESOLVE THE SUPPORT, rather than discarding it.
            #
            # The planner now emits concept NAMES, which is what it actually
            # knows, and they are resolved here against the live store. What
            # used to happen instead: names were dropped one by one and the
            # support arrived empty, which reads as "global mutation" to
            # `select_commuting_slice` -- so nothing ever commuted.
            #
            # Integers are still accepted so a caller that already holds real
            # ids (accumulate.py builds its DAGs by hand) does not have to round
            # trip through names.
            raw_support = op_data.get("support", []) or []
            support_list = []
            names_to_resolve = []
            for s in raw_support:
                if isinstance(s, bool):
                    continue  # bool is an int subclass; never a vertex id
                if isinstance(s, int):
                    support_list.append(s)
                elif isinstance(s, str) and s.strip().lstrip("-").isdigit():
                    support_list.append(int(s.strip()))
                elif isinstance(s, str) and s.strip():
                    names_to_resolve.append(s)
                else:
                    print(f"[Communicator] Ignoring uninterpretable support entry {s!r}.")

            if names_to_resolve:
                res = self.resolver.resolve(names_to_resolve)
                support_list.extend(i for i in res.ids if i not in support_list)
                # An unresolved name is an EVENT: the planner is reasoning about
                # something not yet in memory. It keeps a stable provisional id
                # so co-scoping still works, and it is reported rather than
                # silently folded into "we don't know".
                if res.unresolved:
                    self.unresolved_names.update(res.unresolved)
                    print(f"[Communicator] support: {res.summary()} "
                          f"-> not in memory: {sorted(res.unresolved)}")
                elif res.resolved:
                    print(f"[Communicator] support: {res.summary()}")

            Operator.OperatorStartSupportVector(builder, len(support_list))
            for s in reversed(support_list):
                builder.PrependInt32(s)
            support_vec = builder.EndVector()
            
            # Build Constraints if any
            constraint_list = op_data.get("constraints", [])
            constraint_offsets = []
            if constraint_list and _FBS_OK:
                # Embed the payload ONCE, not once per constraint: every constraint
                # on this operator shares the same payload geometry.
                geom = self.get_embedding(op_data.get("payload", ""))
                for c in constraint_list:
                    ctype_str = c.get("type", "RIGID")
                    ctype = getattr(ConstraintType.ConstraintType, ctype_str,
                                    ConstraintType.ConstraintType.RIGID)

                    ConstraintPayload.ConstraintPayloadStartGeometryVector(builder, len(geom))
                    for g in reversed(geom):
                        builder.PrependFloat32(g)
                    geom_vec = builder.EndVector()

                    ConstraintPayload.ConstraintPayloadStart(builder)
                    ConstraintPayload.ConstraintPayloadAddType(builder, ctype)
                    ConstraintPayload.ConstraintPayloadAddGeometry(builder, geom_vec)
                    constraint_offsets.append(ConstraintPayload.ConstraintPayloadEnd(builder))
            
            constraints_vec = None
            if constraint_offsets and hasattr(Operator, 'OperatorStartConstraintsVector'):
                Operator.OperatorStartConstraintsVector(builder, len(constraint_offsets))
                for co in reversed(constraint_offsets):
                    builder.PrependUOffsetTRelative(co)
                constraints_vec = builder.EndVector()

            # Payload geometry: embed LOCALLY (free, no API quota) so the C++
            # engine receives a position for this operator-organ without ever
            # deriving meaning from a string. This is what makes rho measurable
            # during a real DAG execution rather than only in tests.
            # NOTE: all nested vectors must be built BEFORE OperatorStart().
            geometry_vec = None
            payload_text = op_data.get("payload", "") or ""
            if payload_text.strip() and hasattr(Operator, "OperatorStartGeometryVector"):
                g = self.get_embedding(payload_text)
                Operator.OperatorStartGeometryVector(builder, len(g))
                for x in reversed(g):
                    builder.PrependFloat32(x)
                geometry_vec = builder.EndVector()

            # Build Operator
            Operator.OperatorStart(builder)
            Operator.OperatorAddType(builder, op_type)
            Operator.OperatorAddPayload(builder, payload_str)
            Operator.OperatorAddSupport(builder, support_vec)
            if constraints_vec is not None:
                Operator.OperatorAddConstraints(builder, constraints_vec)
            if geometry_vec is not None:
                Operator.OperatorAddGeometry(builder, geometry_vec)
            operator_offset = Operator.OperatorEnd(builder)
            
            # Create children_ids vector
            children_list = node.get("children_ids", [])
            OperadNode.OperadNodeStartChildrenIdsVector(builder, len(children_list))
            for c in reversed(children_list):
                builder.PrependInt32(c)
            children_vec = builder.EndVector()
            
            # Build OperadNode
            OperadNode.OperadNodeStart(builder)
            OperadNode.OperadNodeAddId(builder, node.get("id", 0))
            OperadNode.OperadNodeAddOperator(builder, operator_offset)
            OperadNode.OperadNodeAddChildrenIds(builder, children_vec)
            node_offsets.append(OperadNode.OperadNodeEnd(builder))
            
        # Create nodes vector
        OperadDAG.OperadDAGStartNodesVector(builder, len(node_offsets))
        for n in reversed(node_offsets):
            builder.PrependUOffsetTRelative(n)
        nodes_vec = builder.EndVector()
        
        # Build OperadDAG
        OperadDAG.OperadDAGStart(builder)
        OperadDAG.OperadDAGAddNodes(builder, nodes_vec)
        dag_offset = OperadDAG.OperadDAGEnd(builder)
        
        builder.Finish(dag_offset)
        return builder.Output()

    def send_to_cpp(self, binary_payload: bytearray):
        if self.cpp_process and self.cpp_process.poll() is None:
            # THE FRAME IS [size][crc32][payload], all little-endian.
            #
            # This used to send [size][payload]. `main.cpp` has read a CRC word
            # since the integrity check was added, so the engine took the
            # FlatBuffer's first four bytes as the checksum and the rest of the
            # stream was off by four for the remainder of the session. Every
            # payload then failed either the CRC compare or the FlatBuffers
            # verifier, and the loop printed a boundary rejection rather than a
            # framing error -- so it looked like malformed DAGs, not a protocol
            # mismatch. `test_full_loop.py` framed it correctly all along, which
            # is why the bug never showed up there.
            payload = bytes(binary_payload)
            frame = (struct.pack("<I", len(payload))
                     + struct.pack("<I", crc32_ieee(payload))
                     + payload)
            try:
                self.cpp_process.stdin.write(frame)
                self.cpp_process.stdin.flush()
                print(f"[Communicator] Dispatched {len(payload)} bytes over IPC "
                      f"(framed with CRC32).")
            except Exception as e:
                print(f"[Communicator] IPC Write Error: {e}")
        else:
            print("[Communicator] C++ Engine is not running. Could not dispatch payload.")

def main():
    print("========================================================")
    print(" TATIANA Communicator (Frontend LLM Adjunction Layer)")
    print("========================================================")
    
    communicator = Communicator()
    
    while True:
        try:
            user_input = input("\nUSER > ")
            if user_input.strip().lower() in ["exit", "quit"]:
                break
                
            # 1. Syntactic Projection (pi)
            dag_json = communicator.pi_morphism(user_input)
            
            # 2. Binary Serialization
            binary_payload = communicator.serialize_to_flatbuffer(dag_json)
            
            # 3. IPC to Professor (C++ Engine)
            if len(binary_payload) > 0:
                print(f"[Communicator] Dispatching binary payload ({len(binary_payload)} bytes) to C++ Professor (Phi morphism)...")
                communicator.send_to_cpp(binary_payload)
            else:
                print("[Communicator] Empty payload. C++ Engine untouched.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
