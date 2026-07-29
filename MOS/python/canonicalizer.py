import json
import re
import sys

from embeddings import embed, EMBED_DIM
from module_vertex import ModuleVertex


class Canonicalizer(ModuleVertex):
    """The Canonicalizer organ — a SPECIAL vertex of the coarse complex K.

    Special because its operators act on the TOPOLOGY ITSELF: `merge` and `link`
    are the typed structural operations that mutate K (Construction 1). Every
    other organ moves within the complex; this one reshapes it.

    Its stalk is the cluster of concepts it is currently deciding about, so its
    position reflects the region of meaning-space it is actively reorganising.
    """

    def __init__(self, db_manager, cloud_router):
        super().__init__("Canonicalizer")
        self.db = db_manager
        self.router = cloud_router

    def operators(self) -> list:
        """Structural operators: these MUTATE the complex, not just move in it."""
        return ["merge", "link", "insert_node", "log_mutation"]
        
    def get_embedding(self, text: str) -> list:
        """Real semantic geometry for the sheaf stalk F (EMBED_DIM=384, local CPU).

        Previously this returned a hash-seeded RANDOM 128-d vector. That meant every
        concept sat at random coordinates, so every Wasserstein/cosine distance the
        engine computed was measuring noise. Now it delegates to embeddings.py, the
        one source of truth shared with the Communicator and the C++ engine.
        """
        return embed(f"{text}")
        
    async def canonicalize_and_store(self, extracted_objects: list):
        """
        Takes a list of newly extracted Mathematical Objects.
        For each object, compares it against the existing Knowledge Graph to 
        deduplicate (canonicalize) synonyms, establish n-ary dependencies, or create new nodes.
        """
        for obj in extracted_objects:
            obj_type = obj.get("type", "Unknown")
            title = obj.get("title", "Unknown")
            content = obj.get("content", "")
            provenance = obj.get("provenance", "Unknown")
            dependencies = obj.get("dependencies", [])
            
            # Generate the fixed-dimension embedding (Global Section `s`)
            embedding = self.get_embedding(f"{title} {content}")
            
            # Fetch potentially related nodes from the local DB
            candidates = self._fetch_local_candidates(title)
            
            if not candidates:
                # No collisions, safe to insert as new
                self._insert_new_node(obj_type, title, content, provenance, dependencies, embedding)
                continue
                
            # Use Frontier LLM to decide on canonicalization
            decision = await self._decide_canonicalization(title, content, candidates)
            
            if decision['action'] == "MERGE":
                print(f"[+] Canonicalizer MERGING '{title}' into existing node: '{decision['target_id']}'")
                self._add_provenance_to_existing(decision['target_id'], provenance)
                # Log the discrete topological surgery (graph mutation)
                self.db.log_graph_mutation(f"mut_merge_{title.replace(' ', '_').lower()}", "merge", decision['target_id'], {}, {"added_provenance": provenance})
                
            elif decision['action'] == "LINK":
                print(f"[+] Canonicalizer LINKING related concept '{title}' to '{decision['target_id']}'")
                new_id = self._insert_new_node(obj_type, title, content, provenance, dependencies, embedding)
                # Create true n-ary relation instead of pairwise semantic_edge
                rel_id = f"rel_{new_id}_{decision['target_id']}"
                self.db.insert_n_ary_relation(rel_id, "related_to", [new_id, decision['target_id']], 1.0)
                self.db.log_graph_mutation(f"mut_link_{new_id}", "link", rel_id, {}, {"nodes": [new_id, decision['target_id']]})
                
            else: # "NEW"
                print(f"[+] Canonicalizer creating NEW distinct node: '{title}'")
                self._insert_new_node(obj_type, title, content, provenance, dependencies, embedding)

    def _fetch_local_candidates(self, title: str) -> list:
        # Simple local search for potential synonyms based on title overlap
        try:
            with self.db.conn:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT id, node_type, content FROM semantic_nodes LIMIT 50")
                all_nodes = cursor.fetchall()
                
                # Crude filter: if any word in title matches
                title_words = set(title.lower().split())
                candidates = []
                for n_id, n_type, n_content in all_nodes:
                    if any(w in n_id.lower() or w in n_content.lower() for w in title_words if len(w) > 4):
                        candidates.append({"id": n_id, "type": n_type, "content": n_content})
                        if len(candidates) >= 3:
                            break
                return candidates
        except Exception as e:
            print(f"[-] Canonicalizer DB fetch failed: {e}", file=sys.stderr)
            return []

    async def _decide_canonicalization(self, title: str, content: str, candidates: list) -> dict:
        candidates_str = json.dumps(candidates, indent=2)
        prompt = f"""
        You are the Canonicalizer for a Mathematical OS.
        A new mathematical object has been extracted:
        Title: {title}
        Content: {content}
        
        Compare this with the following existing graph nodes:
        {candidates_str}
        
        Determine if the new object is:
        1. Exact synonym (MERGE) - e.g., "Strong solution" vs "Classical solution" in the same context.
        2. Related but distinct (LINK) - e.g., "Sobolev Space W^1,p" vs "Sobolev Space H^1".
        3. Completely distinct (NEW).
        
        Respond ONLY with a JSON object: {{"action": "MERGE"|"LINK"|"NEW", "target_id": "id_of_node_if_merge_or_link"}}
        """
        try:
            res = await self.router.query_frontier_brain(prompt=prompt, context="", intent="triage")
            match = re.search(r'\{.*\}', res, re.DOTALL)
            return json.loads(match.group(0)) if match else {"action": "NEW"}
        except Exception:
            return {"action": "NEW"}

    def _insert_new_node(self, node_type, title, content, provenance, dependencies, embedding) -> str:
        node_id = title.replace(" ", "_").lower()
        self.db.insert_semantic_node(node_id, node_type, content, provenance, 1.0)
        
        # Persist the Hilbert space embedding (s \in F)
        self.db.insert_concept_embedding(f"emb_{node_id}", node_id, embedding)
        
        if dependencies:
            dep_ids = [dep.replace(" ", "_").lower() for dep in dependencies]
            relation_nodes = [node_id] + dep_ids
            rel_id = f"rel_dep_{node_id}"
            # True geometric simplex binding the new concept and all its dependencies
            self.db.insert_n_ary_relation(rel_id, "depends_on", relation_nodes, 1.0)
            self.db.log_graph_mutation(f"mut_dep_{node_id}", "link", rel_id, {}, {"nodes": relation_nodes})
            
        return node_id
        
    def _add_provenance_to_existing(self, target_id: str, provenance: str):
        """Append a source to an existing node's provenance list.

        HONESTY FIX: this was a bare `pass`, yet it is called on EVERY merge -
        so every merge silently destroyed the record of where the knowledge came
        from, violating the design requirement that every node carry its sources.
        Failures are now reported loudly: losing provenance is data loss, not a
        cosmetic issue.
        """
        if not provenance:
            return
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT provenance FROM semantic_nodes WHERE id = ?", (target_id,))
            row = cursor.fetchone()
            existing = row[0] if (row and row[0]) else ""

            # Accumulate as a JSON list so multiple sources coexist.
            try:
                sources = json.loads(existing) if existing.strip().startswith("[") else ([existing] if existing else [])
            except json.JSONDecodeError:
                sources = [existing] if existing else []

            if provenance in sources:
                return  # already recorded; nothing to do
            sources.append(provenance)

            self.db.execute_update(
                "UPDATE semantic_nodes SET provenance = ? WHERE id = ?",
                (json.dumps(sources), target_id),
            )
        except Exception as e:
            print(f"[-] Canonicalizer FAILED to record provenance for '{target_id}': {e}",
                  file=sys.stderr)
