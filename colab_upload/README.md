# What goes to Colab, and why `find` isn't finding things

## The two reasons files aren't found

**1. `concepts.npz` and `queries.npz` do not exist yet.**
They are **outputs** the notebook *creates*, not inputs you upload. `find / -name "concepts.npz"`
returns nothing until you have actually run cells 1-6 of `colab_prepare_corpus.ipynb`. After the
run they land in `/content/` and auto-download to your laptop.

**2. `run_tier0.py` needs two files that were missing.**
It imports `cover.py` and `assembly_log.py`. Both are now in this folder. Nothing else from the
repo is needed — the import closure is exactly:

    run_tier0.py -> cover.py       (numpy only)
                 -> assembly_log.py (stdlib only)

No C++, no build, no engine. That is why you do **not** need to upload the TATIANA repo.

---

## What actually runs where

The work splits across two machines because one step needs the compiled engine and the
others do not.

| step | where | why |
|---|---|---|
| 1. build + embed the corpus | **Colab** | pure CPU, and this is the step that melted the laptop |
| 2. ingest vectors into the KB | **local** | writes `MOS/mos_brain.db`; seconds, no model loaded |
| 3. accumulate ticks | **local only** | spawns `mos.exe` — a Windows binary, cannot run on Colab |
| 4. Tier 0 verdict | **either** | pure numpy; ~81 s at T=3000 |

### Step 1 — Colab
Upload `colab_prepare_corpus.ipynb`, Runtime -> Run all. Fetches ~1200 arXiv abstracts,
embeds them with the pinned `bge-small` (384-d), downloads:

- `concepts.npz`
- `queries.npz`
- `corpus_manifest.json`

**Read the cell-5 table before leaving Colab.** It measures how many concepts a query
retrieves at each threshold. The engine's default is `max(0.1, 1/dim)` = 0.1 on *squared*
distance, which means `cos >= 0.95` — a near-duplicate filter. If that yields ~1 concept per
tick there are no co-activation pairs and Tier 0 cannot fit anything, so the threshold has to
be set from that table rather than left at its default.

### Steps 2-3 — local
Put the three downloaded files in `MOS/python/`, then:

```
python ingest_corpus.py --vectors concepts.npz
python accumulate.py --tasks-npz queries.npz --ticks 3000
```

`--tasks-npz` uses the precomputed geometry, so no embedding model is loaded on your machine
(0.001 s/tick instead of 0.476 s/tick). Produces `assembly_events.jsonl`.

### Step 4 — either machine

Locally:
```
python run_tier0.py
```

Or on Colab, upload `run_tier0.py`, `cover.py`, `assembly_log.py` **and your
`assembly_events.jsonl`**, then:
```
!python run_tier0.py --log assembly_events.jsonl
```

---

## `accumulate.py` is in this folder for reference only

It will upload fine and it will **not** run on Colab. It drives the engine over stdin/stdout
IPC, and `mos.exe` is compiled MSVC/Windows (`#include <Windows.h>` unconditionally in
`main.cpp`, `colibri_kernel.cpp`, `primitives.cpp`). Step 3 has to happen on your machine.
