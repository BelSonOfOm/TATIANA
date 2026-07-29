"""
TATIANA — THE FULL LOOP.

Natural language -> pi (Groq) -> Operad DAG -> validate -> local embeddings ->
FlatBuffers -> IPC -> C++ engine -> operators execute -> rho measured over the
coarse complex K.

This is the "prove the loop" test. It exercises the entire adjunction:

    S --pi--> U --Phi--> B

and then reads back what the engine reports about its OWN internal coherence.

Costs 1 Groq call.
"""

from __future__ import annotations

import os
import struct
import subprocess
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import console
console.setup()

from communicator import Communicator

ENGINE = os.path.join(os.path.dirname(__file__), "..", "build", "Debug", "mos.exe")

QUERY = ("Assume M is a compact Kahler manifold. Compute the eigenvalues of the "
         "Hodge-de Rham Laplacian on 1-forms, then report the spectrum.")


def crc32(buf: bytes) -> int:
    crc = 0xFFFFFFFF
    for b in buf:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 & -(crc & 1))
    return (~crc) & 0xFFFFFFFF


def main() -> int:
    engine = os.path.abspath(ENGINE)
    if not os.path.exists(engine):
        print(f"engine not found: {engine}")
        return 1
    if not os.environ.get("GROQ_API_KEY"):
        print("GROQ_API_KEY not set")
        return 1

    # --- pi: language -> DAG (Groq) ----------------------------------------
    c = Communicator.__new__(Communicator)
    c.c_chat = []
    c.api_url = "https://api.groq.com/openai/v1/chat/completions"
    c.model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    c.api_key = os.environ["GROQ_API_KEY"]

    print("=" * 68)
    print("STEP 1 — pi: projecting language into an Operad DAG")
    print("=" * 68)
    dag = c.pi_morphism(QUERY)
    if dag.get("type") == "ERROR":
        print(f"pi failed: {dag}")
        return 1
    nodes = dag.get("nodes", [])
    if not nodes:
        print("pi produced no nodes (classified as noise?) — cannot test the loop.")
        return 1
    print(f"\n{len(nodes)} nodes; validation: {Communicator.validate_dag(dag) or 'CLEAN'}")

    # --- serialize: local embeddings + FlatBuffers -------------------------
    print("\n" + "=" * 68)
    print("STEP 2 — embedding every operator locally, serialising to FlatBuffers")
    print("=" * 68)
    payload = bytes(c.serialize_to_flatbuffer(dag))
    print(f"payload: {len(payload)} bytes "
          f"(includes {len(nodes)} x 384-d operator geometries)")

    # --- IPC into the C++ engine -------------------------------------------
    print("\n" + "=" * 68)
    print("STEP 3 — IPC -> C++ engine (Phi): execute DAG, measure rho over K")
    print("=" * 68)
    proc = subprocess.Popen([engine, "--ipc-server"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    frame = struct.pack("<I", len(payload)) + struct.pack("<I", crc32(payload)) + payload
    proc.stdin.write(frame)
    proc.stdin.flush()
    time.sleep(6)  # let the engine execute and report
    proc.stdin.close()
    try:
        out = proc.stdout.read().decode("utf-8", "replace")
    finally:
        proc.terminate()

    print(out.strip()[:3000])

    ok = "coherence:" in out
    print("\n" + "=" * 68)
    print("LOOP COMPLETE" if ok else "LOOP INCOMPLETE (no coherence report seen)")
    print("=" * 68)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
