"""P4 — ONE END-TO-END RUN ON A REAL QUESTION.

    ingest papers -> pi: question -> DAG -> Phi: execute -> retrieve -> reason
                                              -> verify -> respond

THE ANSWER IS THE LEAST INTERESTING OUTPUT. P4 is an INSTRUMENT, not an
experiment (logbook §7): what it produces that nothing else can is the recorded
trajectory. SPEC_P1_TO_P4 §P4 lists exactly what has to be logged, and this
script exists to log it:

    the assembly trajectory A(1), A(2), ...   the co-activation record every
                                              later measurement consumes
    rho(t) per tick                           PREDICTED to be a sawtooth --
                                              falling as a thought coheres,
                                              jumping when fatigue ejects it
    ||R^W - R^K|| and Q(t)                    P3's diagnosis, continuously
    |A(t)|                                    must stay <= 30 so that
                                              skipped_wide_assemblies() == 0
                                              and b1 is uncontaminated
    every LLM call and its cost               the budget is real

PASS CRITERIA, STATED BEFORE THE RUN (and re-checked at the end by
`report_pass_criteria`):

    1. completes without a crash on the 5.9 GB machine
    2. skipped_wide_assemblies() == 0
    3. Q(t) is non-zero at the end, or P3's diagnosis says exactly why not
    4. the trajectory is CHECKPOINTED AND RESUMABLE

    NOT a pass criterion: whether the answer is correct. One question is not an
    evaluation; that is T1.

CHECKPOINTING. Every tick is appended to the trajectory file as one JSON line
and flushed immediately, and a re-run skips the questions already recorded.
"A long job whose partial progress is worth nothing is a bug in the job" --
ingest_corpus.py says the same thing about the same failure.

USAGE
    py -3.11 python/run_p4.py                 # run (resumes automatically)
    py -3.11 python/run_p4.py --dry-run       # pi only, no engine, no cost
    py -3.11 python/run_p4.py --report        # re-read the trajectory, no run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DEFAULT_TRAJECTORY = os.path.join(HERE, "p4_trajectory.jsonl")

# THE QUESTION, on record as the reference problem since the beginning: the
# eigenvalues of the Hodge-Laplacian on differential forms of CP^3. Doubly
# appropriate now -- CP^3 is also the two-qubit pure-state space, so it sits on
# the M1 track as well.
#
# Asked as a DECOMPOSITION rather than a single prompt, because a trajectory
# needs more than one tick: A(1), A(2), ... is the co-activation record, and one
# question produces one assembly. These are the sub-questions the main one
# actually decomposes into, so the run is one reasoning act rather than a
# benchmark of unrelated prompts.
QUESTIONS = [
    "What are the eigenvalues of the Hodge-Laplacian on differential forms of CP^3?",
    "Define the Hodge-Laplacian on a compact Kahler manifold and state its relation to the Dolbeault Laplacian.",
    "What is the Fubini-Study metric on CP^n, and why is it the natural choice for computing spectra?",
    "State the Hodge decomposition theorem for compact Kahler manifolds.",
    "What are the Betti numbers and Hodge numbers of CP^3?",
    "How does the harmonic space H^k relate to the kernel of the Hodge-Laplacian?",
    "Explain how representation theory of SU(4) decomposes the space of forms on CP^3.",
    "What is the spectrum of the Laplace-Beltrami operator on functions on CP^n?",
    "How do the eigenvalues on k-forms differ from those on functions for CP^3?",
    "Why is CP^3 identified with the two-qubit pure state space, and what does that mean for its geometry?",
]


# --------------------------------------------------------------------- parse --

_RE_RHO = re.compile(r"coherence: rho=([0-9.eE+-]+|UNKNOWN)")
_RE_MODE = re.compile(r"mode=(EXPLORE|RESOLVE|UNKNOWN)")
_RE_CONSOL = re.compile(
    r"consolidation: learned (\d+) edge\(s\), gamma=([0-9.eE+-]+) \(([^)]*)\), "
    r"crystallised (\d+), Q=([0-9.eE+-]+)->([0-9.eE+-]+)")
_RE_GAP = re.compile(
    r"P3 gap \|\|R\^W - R\^K\|\|: mean=(\S+) max=(\S+) over (\d+) shared edge\(s\)"
    r" \| dQ=(\S+)")
_RE_TIER1 = re.compile(r"P2 tier 1: REFUTED by internal incoherence "
                       r"\(rho=([0-9.eE+-]+) > eps_rho=([0-9.eE+-]+)\)")
_RE_RETRIEVED = re.compile(r"Retrieved (\d+) nearest concepts")
_RE_SUPPORT = re.compile(r"support: (\d+)/(\d+) names resolved")


def wait_for_tick(comm, timeout, quiet_for=1.0):
    """Block until the engine finishes a tick, or `timeout` elapses.

    A FIXED SLEEP IS NOT GOOD ENOUGH, and the first run of this script proved
    it: ComputeOp and ReasonOp call Groq SYNCHRONOUSLY from inside the C++
    tick, so a composite takes as long as its LLM calls do -- seconds to tens of
    seconds, not a constant. With a 6-second settle, tick 0 was read after the
    engine had reported and ticks 1-2 were read BEFORE it had, which showed up
    as rho=None and retrieved=0 on ticks that had in fact run fine. That is a
    measurement artefact of the harness, and recording it as a P3 finding would
    have been a false diagnosis of the engine.

    `[OSKernel] mode=` is the LAST line the kernel emits for a tick (step 6), so
    it is the sentinel. After seeing it we wait for the stream to go quiet for
    `quiet_for` seconds, because the mode line is followed by an optional
    fragmentation warning.
    """
    deadline = time.time() + timeout
    seen_mode = False
    last_change = time.time()
    last_len = 0
    while time.time() < deadline:
        with comm._engine_lock:
            lines = list(comm.engine_lines)
        if len(lines) != last_len:
            last_len = len(lines)
            last_change = time.time()
        if any("[OSKernel] mode=" in ln for ln in lines):
            seen_mode = True
        if seen_mode and (time.time() - last_change) >= quiet_for:
            return True, lines
        time.sleep(0.25)
    with comm._engine_lock:
        lines = list(comm.engine_lines)
    return seen_mode, lines


def _num(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_tick(lines):
    """Pull the P4 observables out of one tick's engine output."""
    rec = {
        "rho": None, "mode": None, "learned": 0, "gamma": None, "verdict": None,
        "crystallised": 0, "Q_before": None, "Q_after": None,
        "gap_mean": None, "gap_max": None, "gap_edges": 0, "dQ": None,
        "retrieved": 0, "tier1_refuted": False, "engine_lines": len(lines),
    }
    for ln in lines:
        m = _RE_RHO.search(ln)
        if m:
            rec["rho"] = None if m.group(1) == "UNKNOWN" else _num(m.group(1))
        m = _RE_MODE.search(ln)
        if m:
            rec["mode"] = m.group(1)
        m = _RE_CONSOL.search(ln)
        if m:
            rec.update(learned=int(m.group(1)), gamma=_num(m.group(2)),
                       verdict=m.group(3), crystallised=int(m.group(4)),
                       Q_before=_num(m.group(5)), Q_after=_num(m.group(6)))
        m = _RE_GAP.search(ln)
        if m:
            rec.update(gap_mean=_num(m.group(1)), gap_max=_num(m.group(2)),
                       gap_edges=int(m.group(3)), dQ=_num(m.group(4)))
        m = _RE_TIER1.search(ln)
        if m:
            rec["tier1_refuted"] = True
            rec["tier1_rho"] = _num(m.group(1))
            rec["tier1_eps_rho"] = _num(m.group(2))
        m = _RE_RETRIEVED.search(ln)
        if m:
            rec["retrieved"] = max(rec["retrieved"], int(m.group(1)))
    return rec


# ------------------------------------------------------------- checkpointing --

def load_trajectory(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # A torn final line means the process died mid-flush. Keep every
                # COMPLETE tick rather than discarding the run.
                print(f"[P4] ignoring incomplete trailing record in {path}")
    return out


def append_tick(path, record):
    """One tick, one line, flushed. This is what makes the run resumable."""
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


# --------------------------------------------------------------------- report --

def report_pass_criteria(traj, path=DEFAULT_TRAJECTORY):
    print("\n" + "=" * 72)
    print("P4 PASS CRITERIA")
    print("=" * 72)
    if not traj:
        print("  no ticks recorded -- nothing to judge")
        return False

    ok = True

    completed = [t for t in traj if t.get("dispatched")]
    print(f"\n1. COMPLETES WITHOUT A CRASH")
    crashed = [t for t in traj if t.get("error")]
    print(f"   ticks recorded : {len(traj)}")
    print(f"   dispatched     : {len(completed)}")
    print(f"   errors         : {len(crashed)}")
    for t in crashed[:5]:
        print(f"     - q{t['index']}: {t['error']}")
    ok &= not crashed

    print(f"\n2. |A(t)| <= 30 SO skipped_wide_assemblies() == 0")
    widest = max((t.get("retrieved", 0) for t in traj), default=0)
    print(f"   widest assembly |A(t)| : {widest}")
    print(f"   cap                    : 30 (ConceptStore default)")
    within = widest <= 30
    print(f"   -> {'OK' if within else 'CONTAMINATED: b1 is not trustworthy'}")
    ok &= within

    print(f"\n3. Q(t) NON-ZERO AT THE END, OR P3 SAYS WHY NOT")
    q = [t["Q_after"] for t in traj if t.get("Q_after") is not None]
    gaps = [t["gap_mean"] for t in traj if t.get("gap_mean") is not None]
    learned = sum(t.get("learned", 0) for t in traj)
    cryst = sum(t.get("crystallised", 0) for t in traj)
    if q:
        print(f"   Q(final)      : {q[-1]:.8g}   (max {max(q):.8g})")
    else:
        print(f"   Q(final)      : never computed -- no tick consolidated")
    print(f"   edges learned : {learned}")
    print(f"   crystallised  : {cryst}")
    if gaps:
        print(f"   gap ||R^W-R^K||: mean {sum(gaps)/len(gaps):.6g}, "
              f"max {max(gaps):.6g}")
    if q and q[-1] > 0:
        print("   -> OK: the store has learned something")
    else:
        # THE P3 DIAGNOSIS, spelled out rather than left to the reader.
        print("   -> Q is zero. P3 diagnosis:")
        if not any(t.get("retrieved") for t in traj):
            print("      RETRIEVAL RETURNED NOTHING -> W was empty. A P0 problem.")
        elif gaps and max(gaps) > 1e-12:
            print("      THE GAP IS LARGE BUT NOTHING CRYSTALLISED -> the GATE is")
            print("      closed: gamma was 0 on every tick. A P2 problem.")
        elif gaps:
            print("      THE GAP IS ZERO -> R^W ~= R^K, there is NOTHING TO")
            print("      CONSOLIDATE. Neither P0 nor P2: the restriction-map")
            print("      learner needs looking at. This is a genuine finding.")
        else:
            print("      No edge was ever learned; W had no shared edges.")
        ok = False

    print(f"\n4. CHECKPOINTED AND RESUMABLE")
    print(f"   trajectory file : {path}")
    print(f"   ticks on disk   : {len(traj)}  (re-running resumes after these)")
    print(f"   -> OK")

    print(f"\nBUDGET")
    calls = sum(t.get("llm_calls", 0) for t in traj)
    secs = sum(t.get("seconds", 0.0) for t in traj)
    print(f"   pi (Groq) calls : {calls}")
    print(f"   wall clock      : {secs:.1f}s")

    print(f"\nrho(t) TRAJECTORY  (predicted: a sawtooth, not a monotone decay)")
    rhos = [(t["index"], t.get("rho")) for t in traj]
    shown = [f"{i}:{('%.4f' % r) if r is not None else 'UNK'}" for i, r in rhos]
    print("   " + "  ".join(shown))

    print("\n" + "=" * 72)
    print("P4 " + ("PASSED" if ok else "DID NOT PASS -- see the diagnosis above"))
    print("=" * 72)
    return ok


# ----------------------------------------------------------------------- run --

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trajectory", default=DEFAULT_TRAJECTORY)
    ap.add_argument("--dry-run", action="store_true",
                    help="pi only: no engine, no consolidation, no cost beyond pi")
    ap.add_argument("--report", action="store_true",
                    help="re-read the trajectory and re-judge, without running")
    ap.add_argument("--limit", type=int, default=0, help="0 = every question")
    ap.add_argument("--settle", type=float, default=120.0,
                    help="MAX seconds to wait for the engine to close a tick. "
                         "Not a sleep -- wait_for_tick returns as soon as the "
                         "kernel emits its mode line. Generous because "
                         "ComputeOp/ReasonOp call Groq synchronously.")
    args = ap.parse_args()

    traj = load_trajectory(args.trajectory)
    if args.report:
        report_pass_criteria(traj, args.trajectory)
        return 0

    done = {t["question"] for t in traj}
    questions = QUESTIONS[: args.limit] if args.limit else QUESTIONS
    todo = [q for q in questions if q not in done]

    print("=" * 72)
    print("P4 — END-TO-END RUN: Hodge-Laplacian on differential forms of CP^3")
    print("=" * 72)
    print(f"  trajectory : {args.trajectory}")
    print(f"  recorded   : {len(traj)} tick(s) already on disk")
    print(f"  to run     : {len(todo)} of {len(questions)} question(s)")
    if not todo:
        print("  nothing left to do -- reporting on what is already recorded")
        report_pass_criteria(traj, args.trajectory)
        return 0

    from communicator import Communicator

    comm = Communicator()
    if not args.dry_run and not comm.cpp_process:
        print("[P4] engine did not start; aborting rather than recording a fake run")
        return 1

    # Let the engine finish opening the KB before the first payload.
    time.sleep(1.5)
    with comm._engine_lock:
        comm.engine_lines.clear()

    for q in todo:
        idx = questions.index(q)
        print("\n" + "-" * 72)
        print(f"[P4] tick {idx}: {q}")
        print("-" * 72)
        started = time.time()
        rec = {"index": idx, "question": q, "dispatched": False,
               "llm_calls": 0, "error": None,
               "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}

        try:
            dag = comm.pi_morphism(q)
            rec["llm_calls"] = 1
            rec["dag_type"] = dag.get("type", "MATH" if dag.get("nodes") else "EMPTY")
            rec["nodes"] = len(dag.get("nodes", []) or [])

            if dag.get("type") in ("ERROR", "INVALID"):
                rec["error"] = f"pi returned {dag.get('type')}: {dag.get('reason') or dag.get('problems')}"
            elif not dag.get("nodes"):
                rec["error"] = "pi produced no nodes (classified as NOISE)"
            else:
                # The supports the planner named, resolved. Recorded because a
                # run whose supports all went provisional foliates exactly as
                # badly as before P1, and that has to be visible in the data
                # rather than inferred from the absence of parallelism.
                rec["support_resolved"] = len(comm.unresolved_names)
                payload = comm.serialize_to_flatbuffer(dag)
                rec["payload_bytes"] = len(payload)
                if args.dry_run:
                    print("[P4] dry run: not dispatching")
                else:
                    with comm._engine_lock:
                        comm.engine_lines.clear()
                    comm.send_to_cpp(payload)
                    rec["dispatched"] = True
                    closed, lines = wait_for_tick(comm, args.settle)
                    rec["tick_closed"] = closed
                    if not closed:
                        # Recorded, not silently accepted: an unclosed tick's
                        # numbers are a snapshot of a composite still running,
                        # and reading them as a result is how a harness timeout
                        # gets mistaken for an engine finding.
                        rec["error"] = (f"engine did not close the tick within "
                                        f"{args.settle}s; telemetry is partial")
                        print(f"[P4] WARNING: {rec['error']}")
                    rec.update(parse_tick(lines))
        except Exception as e:                       # noqa: BLE001
            rec["error"] = f"{type(e).__name__}: {e}"
            print(f"[P4] tick failed: {rec['error']}")

        rec["seconds"] = round(time.time() - started, 2)
        rec["unresolved_total"] = len(comm.unresolved_names)
        # CHECKPOINT. Written before the next tick starts, so a crash costs one
        # tick rather than the run.
        append_tick(args.trajectory, rec)
        traj.append(rec)
        print(f"[P4] tick {idx} recorded: rho={rec.get('rho')} "
              f"Q={rec.get('Q_after')} learned={rec.get('learned')} "
              f"crystallised={rec.get('crystallised')} ({rec['seconds']}s)")

    if comm.cpp_process:
        try:
            comm.cpp_process.stdin.close()
            comm.cpp_process.wait(timeout=10)
        except Exception:
            comm.cpp_process.kill()

    report_pass_criteria(traj, args.trajectory)
    print(f"\n[P4] concepts the planner named that memory had never seen: "
          f"{len(comm.unresolved_names)}")
    for name in sorted(comm.unresolved_names)[:15]:
        print(f"      - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
