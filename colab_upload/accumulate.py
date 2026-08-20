"""Phase 3, stage 2: drive the engine until there are enough E7 ticks for Tier 0.

WHAT THIS COSTS, WHICH IS THE PART THAT WAS WRONG IN THE PLANNING.
The logbook's "47 events/day" is the QUADRATIC PAIRWISE JUDGEMENT cost -- n=7
organs => 21 calls. Tier 0 needs none of that. It needs assemblies, and an
assembly comes from SearchOp's retrieval, whose geometry is embedded LOCALLY by
embeddings.py (bge-small, 384-d, ONNX). Only ReasonOp's generate_thought reaches
Groq.

So a SEARCH-only accumulation run makes ZERO API calls and is bounded by CPU,
not by quota. That is why this driver builds its DAGs directly instead of going
through Communicator.pi_morphism, which would spend a completion per tick to
plan something we already know the shape of.

    THE VALIDITY COST OF THAT CHOICE, STATED PLAINLY: a SEARCH-only corpus
    describes MOS's RETRIEVAL structure, not its reasoning. If Tier 0 passes on
    this stream, the honest claim is "the retrieval co-activation of this corpus
    is better explained by overlapping latent causes than by a partition" -- NOT
    "MOS's organs are a cover". Use --mixed to spend quota on ReasonOp ticks and
    buy the stronger claim.

PROVENANCE IS RECORDED, NOT ASSUMED. Every run writes a sidecar manifest naming
the task stream, its source, the git commit, and the tick range it produced. A
cover verdict computed from assemblies whose origin nobody can reconstruct is
not evidence, and this file exists so that can never be the situation.

    python accumulate.py --tasks tasks.txt --ticks 1500 --dry-run
    python accumulate.py --tasks tasks.txt --ticks 1500
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from assembly_log import DEFAULT_PATH as ASSEMBLY_LOG_PATH  # noqa: E402


def load_tasks(path: str) -> List[str]:
    """One task per line. Blank lines and # comments ignored."""
    with open(path, encoding="utf-8") as fh:
        tasks = [ln.strip() for ln in fh]
    return [t for t in tasks if t and not t.startswith("#")]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def count_existing_ticks(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for ln in fh if ln.strip())


def build_search_dag(comm, query: str) -> bytearray:
    """A one-node SEARCH DAG. No LLM planning, so no quota.

    The payload geometry is embedded locally, which is the same path
    Communicator.serialize_to_flatbuffer takes for a planned DAG -- the engine
    cannot tell the difference and does not need to.

    THE NESTING IS LOAD-BEARING. serialize_to_flatbuffer reads
    node["operator"]["type"] and node["operator"]["payload"]; a flat
    {"op_type": ..., "payload": ...} is not rejected, it is silently serialised
    as an UNKNOWN operator with an empty payload and NO geometry. The result is
    a structurally valid 80-byte DAG that runs, retrieves nothing, and logs a
    tick with an empty assembly -- so an accumulation run would produce
    thousands of blank rows and only the cover fit would ever notice.
    `verify_dag` below exists because of exactly that.
    """
    return comm.serialize_to_flatbuffer({
        "nodes": [{
            "id": 0,
            "operator": {"type": "SEARCH", "payload": query, "support": []},
            "children_ids": [],
        }]
    })


def verify_dag(payload: bytearray, query: str, expect_dim: int) -> None:
    """Parse the buffer back and assert it says what it was meant to say.

    Serialising without throwing proves almost nothing here -- the failure mode
    that matters produces a well-formed buffer with the content missing.
    """
    import mos.fbs.OperadDAG as OperadDAG
    import mos.fbs.OpType as OpType

    dag = OperadDAG.OperadDAG.GetRootAsOperadDAG(bytearray(payload), 0)
    if dag.NodesLength() != 1:
        raise AssertionError(f"expected 1 node, got {dag.NodesLength()}")
    op = dag.Nodes(0).Operator()
    if op.Type() != OpType.OpType.SEARCH:
        raise AssertionError(
            f"op type is {op.Type()}, not SEARCH ({OpType.OpType.SEARCH}) -- "
            "the node dict shape is wrong")
    got = op.Payload().decode() if op.Payload() else ""
    if got != query:
        raise AssertionError(f"payload round-trip failed: {got!r} != {query!r}")
    if op.GeometryLength() != expect_dim:
        raise AssertionError(
            f"geometry is {op.GeometryLength()}-d, expected {expect_dim}. "
            "SearchOp would fall back to a REMOTE embedding call, which both "
            "costs quota and fails against a completions-only provider.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", help="file of task strings, one per line")
    ap.add_argument("--tasks-npz", default=None,
                    help="a queries.npz from colab_prepare_corpus.ipynb (texts, "
                         "vectors). Uses the PRECOMPUTED geometry, so this "
                         "machine never loads the embedding model -- the local "
                         "cost drops to engine ticks, which are microseconds.")
    ap.add_argument("--ticks", type=int, required=True,
                    help="target TOTAL ticks in the log, not additional ones")
    ap.add_argument("--log", default=ASSEMBLY_LOG_PATH)
    ap.add_argument("--manifest", default=None,
                    help="provenance sidecar (default: <log>.manifest.json)")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate tasks, embeddings and DAG serialisation "
                         "WITHOUT starting the engine or writing to the log")
    ap.add_argument("--settle", type=float, default=0.05,
                    help="seconds between dispatches; the IPC is a pipe and the "
                         "engine is single-threaded per tick")
    args = ap.parse_args()

    if not args.tasks and not args.tasks_npz:
        print("[accumulate] need --tasks or --tasks-npz", file=sys.stderr)
        return 2

    precomputed = None
    if args.tasks_npz:
        import numpy as np
        data = np.load(args.tasks_npz, allow_pickle=True)
        tasks = [str(t) for t in data["texts"]]
        # Keyed by the exact query string, because that is what
        # serialize_to_flatbuffer will look up when it asks for geometry.
        precomputed = {t: [float(x) for x in v]
                       for t, v in zip(tasks, data["vectors"])}
        print(f"[accumulate] precomputed geometry: {len(precomputed)} queries "
              f"at {data['vectors'].shape[1]}-d (no model loaded here)")
    else:
        tasks = load_tasks(args.tasks)

    if not tasks:
        print("[accumulate] no usable tasks", file=sys.stderr)
        return 2

    already = count_existing_ticks(args.log)
    needed = max(0, args.ticks - already)
    manifest_path = args.manifest or (args.log + ".manifest.json")

    print(f"[accumulate] tasks available : {len(tasks)}")
    print(f"[accumulate] ticks in log    : {already}")
    print(f"[accumulate] ticks to run    : {needed}  (target {args.ticks})")
    print(f"[accumulate] assembly log    : {args.log}")
    print(f"[accumulate] manifest        : {manifest_path}")

    if needed == 0:
        print("[accumulate] target already met; nothing to do.")
        return 0

    if len(tasks) < needed:
        # Cycling is allowed but must be VISIBLE. Repeated tasks retrieve
        # near-identical concept sets, so the assemblies are correlated far
        # beyond the temporal correlation block-CV is designed to absorb, and
        # the effective sample size is closer to len(tasks) than to needed.
        reps = (needed + len(tasks) - 1) // len(tasks)
        print(f"[accumulate] WARNING: only {len(tasks)} distinct tasks for "
              f"{needed} ticks -- each will repeat ~{reps}x.")
        print("[accumulate] Repeated tasks retrieve near-identical concept sets,")
        print("[accumulate] so effective sample size is nearer "
              f"{len(tasks)} than {needed}. Tier 0 on this would overstate its")
        print("[accumulate] confidence. Supply more distinct tasks.")

    def attach_geometry(comm):
        """Point the serialiser at precomputed vectors instead of the model.

        serialize_to_flatbuffer calls self.get_embedding(payload_text), so
        replacing that one method is the whole integration. A MISS RAISES rather
        than falling back to embedding: a silent fallback would load the model
        and re-embed on the very machine this exists to spare, and the run would
        look identical while taking a thousand times longer.
        """
        if precomputed is None:
            return
        def lookup(text: str):
            try:
                return precomputed[text]
            except KeyError:
                raise KeyError(
                    f"no precomputed geometry for {text[:60]!r}. The task file "
                    "and the .npz must be the same stream.")
        comm.get_embedding = lookup

    from communicator import Communicator  # deferred: loads the embedding model

    if args.dry_run:
        print("\n[accumulate] DRY RUN -- engine not started, log not written.\n")
        comm = Communicator.__new__(Communicator)   # no subprocess spawn
        if precomputed is not None:
            attach_geometry(comm)
            EMBED_DIM = len(next(iter(precomputed.values())))
        else:
            from embeddings import embed as embed_text, EMBED_DIM
            comm.get_embedding = embed_text
        ok = 0
        t0 = time.time()
        for i, task in enumerate(tasks[:min(5, len(tasks))]):
            try:
                payload = build_search_dag(comm, task)
                verify_dag(payload, task, EMBED_DIM)
                ok += 1
                print(f"  [ok] task {i}: {len(payload):5d} bytes, SEARCH, "
                      f"{EMBED_DIM}-d geometry -- {task[:52]}")
            except Exception as e:
                print(f"  [FAIL] task {i}: {e}")
                return 1
        dt = time.time() - t0
        print(f"\n[accumulate] {ok}/{min(5, len(tasks))} sample tasks serialise cleanly.")
        print(f"[accumulate] ~{dt/max(ok,1):.3f}s per tick to build "
              f"=> ~{needed*dt/max(ok,1)/60:.1f} min of CPU for {needed} ticks.")
        print("[accumulate] API calls this run: 0 (SEARCH-only).")
        print("[accumulate] geometry: " + ("PRECOMPUTED -- no model on this machine."
                                           if precomputed else
                                           "embedded locally; --tasks-npz avoids that."))
        print("\n[accumulate] Dry run OK. Re-run without --dry-run to accumulate.")
        return 0

    comm = Communicator()
    attach_geometry(comm)
    started = time.time()
    dispatched = 0
    try:
        for i in range(needed):
            task = tasks[i % len(tasks)]
            comm.send_to_cpp(build_search_dag(comm, task))
            dispatched += 1
            if args.settle:
                time.sleep(args.settle)
            if (i + 1) % 50 == 0:
                print(f"[accumulate] {i+1}/{needed} dispatched "
                      f"({time.time()-started:.0f}s elapsed)")
    except KeyboardInterrupt:
        print("\n[accumulate] interrupted; writing manifest for what did run.")
    finally:
        # Manifest is written even on interrupt: a partial run whose provenance
        # is unrecorded is worse than no run, because it is indistinguishable
        # from a complete one when someone reads the log later.
        final = count_existing_ticks(args.log)
        manifest = {
            "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "git_commit": git_commit(),
            "task_file": os.path.abspath(args.tasks) if args.tasks else None,
            "tasks_npz": os.path.abspath(args.tasks_npz) if args.tasks_npz else None,
            "geometry": "precomputed (Colab)" if precomputed else "embedded locally",
            "n_distinct_tasks": len(tasks),
            "tasks_cycled": len(tasks) < needed,
            "dag_shape": "SEARCH-only, one node, no LLM planning",
            "api_calls": 0,
            "ticks_before": already,
            "ticks_after": final,
            "dispatched": dispatched,
            "corpus_claim": (
                "Retrieval co-activation only. A Tier-0 verdict from this log "
                "describes the RETRIEVAL structure of this task stream, not "
                "MOS's reasoning."),
        }
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        print(f"[accumulate] ticks {already} -> {final}; manifest at {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
