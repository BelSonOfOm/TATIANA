# PRECILLA

**P**rior-art **R**esolution · **E**scalating **C**ouncil · **I**nvariant **L**edger · **L**iterature **A**nchoring

A research console for deriving things correctly on almost no budget, built to
the discipline in `THE_GENERATIVE_THOUGHT_MODEL.md` and `WHY_A_MODEL_OF_COGNITION.md`.

Python 3.9+, **stdlib only**, no install, no API key for job 1.
Sized for a 4-core / 5.9 GB machine that sleeps.

---

## The thesis

Frontier capability is not one model being clever. It is three jobs with wildly
different cost profiles, kept separate:

| job | what it costs | what it needs |
|---|---|---|
| **1. prior art** — does this citation exist, and does it say what I think? | **$0** | free bibliographic APIs, no LLM at all |
| **2. resolution** — the actual derivation | cents, if context stays flat | a good reasoning model, briefly |
| **3. verification** — is this step true? | **$0** | SymPy, numerics, dimensional analysis |

Nearly all the money people spend on job 2 is actually spent re-sending a
growing transcript. PRECILLA's ledger keeps context **flat** — you resend a
digest, never the conversation. That single lever beats every model choice.

All three are built. Job 1 and job 3 cost nothing; job 2 is guarded.

---

## Why the citation module comes first

Your own standing rule:

> ⚠️ All citations below are from model knowledge and were NOT searched this
> session. They are named so they can be found, not quoted as authority.

`precilla cite` is the machine that discharges that rule. It reads the prose,
pulls the citations out, resolves them against OpenAlex/Crossref/arXiv, and
returns one of:

| status | meaning |
|---|---|
| `VERIFIED` | record found, all named authors present, unambiguous, prose agrees |
| `VERIFIED_CORRECTED` | right paper, wrong prose — year off, author dropped, name misspelt. Diff attached. |
| `PARTIAL` | plausible but not confirmed |
| `AMBIGUOUS` | two records fit equally well; a human must look |
| `UNRESOLVED` | nothing matched |
| `ERRORED` | providers unreachable — **explicitly not** evidence about the citation |

That last row matters. A network failure silently reading as "citation is fake"
would be exactly the class of instrument artefact Tier 0 kept catching.

### It refuses to run uncalibrated

Discipline rule 3 — *every instrument passes its full battery at ONE shared
parameter setting, or it is not used* — is enforced in code. The battery is
three classes, analogous to partition / cover / structure-free:

```
gold      real papers, correctly remembered   -> must reach VERIFIED
nearmiss  real papers, garbled by the model   -> must NOT reach plain VERIFIED
decoy     papers that do not exist            -> must reach UNRESOLVED
```

`decoy` is the positive control. Without it, an instrument that says VERIFIED
to everything scores 100% on gold. The decoys are deliberately nasty — one of
them states your own hypothesis as though it were published prior art, which is
the single most dangerous hallucination this project could suffer.

`cite verify` **refuses to emit VERIFIED** without a passing stamp for the
current config hash. Change a weight, and the stamp is invalidated — you have
to re-earn it.

---

## Use

Everything free, in one command:

```bash
export PRECILLA_MAILTO="charbel.dargham01@gmail.com"
export OPENROUTER_API_KEY=sk-or-...
./preflight.sh context/*.md
```

`preflight.sh` runs the three offline batteries, `cite doctor`, `cite
calibrate --promote`, `cite verify`, slug confirmation, and a **dry run** of the
first paid call. It charges nothing and ends with a ~6-line report block. If the
network is down it degrades to `INCONCLUSIVE` and `cite verify` refuses — the
failure path is exercised, not assumed.

Or step by step:

```bash
cd precilla
export PRECILLA_MAILTO="charbel.dargham01@gmail.com"   # OpenAlex polite pool

# what does the prose actually claim?
python3 -m precilla cite extract context/WHY_A_MODEL_OF_COGNITION.md

# earn the right to run  (~35 live queries, cached forever after)
python3 -m precilla cite calibrate --verbose

# now resolve for real
python3 -m precilla cite verify context/*.md --bibtex --log

# flat context for a model prompt -- resend THIS, never the transcript
python3 -m precilla ledger digest
```

Every subcommand writes **one JSON object to stdout**, commentary to stderr,
exit 0 = ran / 1 = ran and the answer is no / 2 = usage error. That contract is
why this is a CLI: an agent can run `precilla cite verify doc.md | jq .summary`
without a screenshot. You and I drive the identical tool.

```bash
python3 tests/test_offline.py     # cite battery,  no network
python3 tests/test_check.py       # check battery, no network
python3 tests/test_derive.py      # derive battery, no network, no spend
python3 -m precilla budget        # what it all costs, computed
```

Only `check` needs a dependency (`pip install sympy`). Everything else is
stdlib.

---

## Status of this build

**Verified here:** extractor, matcher, discrepancy detection, calibration
logic, refusal semantics — all green against a synthetic bibliographic
universe (25 records, containing every gold paper and no decoy). Run on your
two documents it finds **13 citations, zero false positives**, correctly
splitting `(Dayan; Stachenfeld, Botvinick & Gershman)` into two works
twenty-four years apart.

**NOT verified here:** the live provider calls. My sandbox is blocked from
`api.openalex.org`, `api.crossref.org` and `export.arxiv.org`, so the request
construction and JSON parsing are exercised only against mocks. First real run
is on your machine. `cite calibrate` is exactly the command that will tell you
whether the live path works, which is the point.

**The gold fixtures are `[UNVERIFIED SEED]`** — written from *my* model
knowledge, the precise thing PRECILLA exists to distrust. They are not
authority. `cite calibrate --promote` replaces each seed with a resolved DOI
and flips it to `[MEASURED]`. Until that runs, a gold failure is ambiguous
between a bad fixture and a bad resolver, and the report says so rather than
guessing.

**Price table corrected against the source of truth.** OpenRouter's live
`/api/v1/models` was fetched on 2026-08-06 and disagreed with the aggregator
pages this build originally trusted:

| | aggregator said | OpenRouter API says |
|---|---|---|
| `z-ai/glm-5.2` | $0.406 / $1.276 | **$0.76 / $2.42** |
| red-team slug | `deepseek/deepseek-chat` (guessed) | **not present** — a failed call |

The confirmed cheap slug is `deepseek/deepseek-v4-flash-0731` at **$0.09 /
$0.18** with 1M context — cheaper than the V3.2 row it replaces *and* verified
to exist. Both defaults in `derive/run.py` are now `[MEASURED]` rather than
assumed. Cost per full lead+red-team cycle: **$0.775**, about 10 cycles inside
$7.70.

Three defects the battery caught during construction, all fixed:

1. citing a 3-author paper as 2 authors scored a perfect 1.0 author recall —
   recall over *cited* names can't see an omission. Now reported, and the
   status becomes `VERIFIED_CORRECTED` rather than a silent pass or a wrong
   rejection.
2. a five-year-wrong year still verified on author+title strength alone.
3. `Howerd`/`Howard` failed fuzzy matching (SequenceMatcher ratio 0.833 < 0.90).
   Fixed with an edit-distance rule, **not** by lowering the constant to 0.83 —
   that would be fitting a threshold to one example, which is rule 7.

---

## `precilla check` — job 3, built

Verifies a derivation draft. No model, no cost, no network.

```bash
python3 -m precilla check draft.md --log
```

It pulls every `# EQ-n` block out of the draft and, for each one:

1. **statically screens it** — model-generated code is executed, so an AST
   allowlist refuses imports outside `sympy/math`, dunder attribute escapes,
   `eval`/`exec`/`open`, and `with`. Defence in depth, not a security boundary:
   run in a container if the source is untrusted.
2. **runs it in a subprocess** with an alarm, so a runaway `simplify` degrades
   to `TIMEOUT` instead of hanging the batch.
3. **re-derives the identity independently**, symbolically *and* numerically
   over 200 random rational substitutions.

**The block's own `assert` is evidence, not proof.** A model can write
`assert simplify(lhs - rhs) == 0` against things it quietly defined to be
equal, and the assert passes while proving nothing. The verdict comes from the
re-derivation. The test suite plants exactly that case — a passing assert on a
false `lhs`/`rhs` — and requires it to come back `FAIL`.

| verdict | meaning |
|---|---|
| `PASS` | symbolic and numeric agree the identity holds |
| `FAIL` | numeric counterexample, or a symbolic residual |
| `SUSPECT` | simplify says nonzero, every substitution vanishes — **a missing assumption**, e.g. an undeclared positivity |
| `REFUSED` | failed the static screen; never executed |
| `UNCHECKABLE` | ran, but defined no `lhs`/`rhs` to verify against |
| `DECLARED_UNCHECKED` | the draft honestly marked it `[UNCHECKED]` |
| `TIMEOUT` | did not finish |

The gate is harsh on purpose: it fails if **any** equation mentioned in prose
has no block. A draft with three beautiful proofs and one unmechanised step is
not 75% verified — the unmechanised step is where the error lives, because it
is the one the model could not render.

`tests/fixture_draft.md` is the positive control, planting all seven classes
including a malicious block that writes to `/tmp`. The suite asserts the file
is never created.

## Roadmap

## `precilla derive` — job 2, built

The only module that spends money, so it is the most guarded.

```bash
export OPENROUTER_API_KEY=sk-or-...
python3 -m precilla derive models --filter glm     # confirm the slug first
python3 -m precilla derive lead  --docs context/*.md --bib bib.json \
        --out draft.md --dry-run                   # free: assemble and price
python3 -m precilla derive lead  --docs context/*.md --bib bib.json --out draft.md
python3 -m precilla check draft.md                 # free
python3 -m precilla derive redteam --draft draft.md --out critique.md
python3 -m precilla derive spend                   # running total
```

- **`--dry-run` assembles and prices the call without sending it.** Measured on
  the real documents: **10,930 input tokens, $0.105 projected** for a lead pass.
- **Two spend guards.** `--max-usd` refuses any single call projected above it;
  `--budget` refuses when the cumulative total from the ledger would exceed it.
  Neither guard ever reaches the transport — the test suite asserts that.
- **Flat context is enforced, not suggested.** Pass 1 sends the documents. Every
  later pass sends the digest plus the artefact under review and *omits the
  documents entirely* — a tested property, not a convention.
- **Real cost, not estimated.** Provider-reported cost is preferred over the
  local price table, reasoning tokens are counted as output, and
  `projection_error` records how wrong the estimate was so the budget model
  improves against reality.
- **OpenAI-compatible.** `PRECILLA_BASE_URL` points it at Moonshot, DeepSeek
  direct, or a local `ds4-server` with no code change.

## Roadmap

**G3 — the loop, automated.** An escalation ladder, cheapest rung first,
promoting only on failed verification:

```
cheap model drafts  ->  check/ rejects  ->  re-draft  ->  still failing
                    ->  escalate one rung  ->  ...  ->  frontier, rarely
```

Plus a **council**: a *different* cheap model red-teams the derivation, told an
error exists. Cross-model disagreement is a strong error signal and costs
cents. That is the closest thing to a lab partner, and it is where "as good as
frontier, at a fraction of the price" actually comes from — not from any single
model, but from cheap generation plus free deterministic rejection.

**G3 — provider layer.** Deliberately OpenAI-compatible so anything speaking
`/v1/chat/completions` drops in unchanged, including a local `ds4-server`.

---

## Layout

```
precilla/
  cli.py            argparse; the JSON contract
  ledger.py         append-only JSONL; audit trail AND flat-context digest
  cite/
    extract.py      prose -> candidates. Two citation shapes that mean
                    opposite things, plus cross-reference rejection
    resolve.py      OpenAlex / Crossref / arXiv. Permanent disk cache =
                    reproducibility months later, and the audit trail
    match.py        scoring, discrepancies, classification thresholds
    verify.py       the pipeline; bibtex for confirmed entries only
    calibrate.py    the positive control and the refusal stamp
    fixtures.json   gold / nearmiss / decoy
tests/test_offline.py    cite battery
tests/test_check.py      check battery
tests/test_derive.py     derive battery (fake transport, no spend)
tests/fixture_draft.md   planted derivation: true/false/suspect/malicious
PROMPT.md                the single derivation prompt + red-team prompt
```

Everything writes under `~/.precilla/` (`PRECILLA_STATE`, `PRECILLA_CACHE` to
override). The cache is never invalidated on purpose: a verification result
must be reproducible later, and these APIs are live.
