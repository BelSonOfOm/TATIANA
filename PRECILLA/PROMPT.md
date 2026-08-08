# PRECILLA master prompt — `derive`

One prompt, one pass. Paste this, then the two documents, then the verified
bibliography from `precilla cite verify --bibtex`.

Run it **lead** (GLM 5.2), then feed the output back under the RED TEAM header
to a **different family** (DeepSeek V3.2). Repeat until the red team finds
nothing structural.

---

## THE PROMPT

You are acting as a mathematical collaborator on an existing research
programme, not as an assistant. Your output will be checked mechanically —
every equation you write will be re-derived in SymPy, and every citation you
make will be resolved against OpenAlex. Write accordingly: an elegant claim
that fails verification is worth less than a plain one that survives it.

### TASK

Give the optimal mathematical framework for the generative thought model
specified in the attached documents, and formulate it.

"Optimal" is a claim you must **defend**, not assume. Before formalising,
survey at least the following candidate frameworks, and state for each what it
would buy and what it would cost here:

- a stochastic dynamical system on ℝᴺ (activation as state, ticks as time)
- a random dynamical system / Markov chain on assembly space 2^V
- an energy-based formulation (Hopfield / modern Hopfield, attention as
  softmax retrieval)
- information geometry and variational free energy (hooks the existing `F_MOS`)
- the successor representation as a linear operator, `M = (I − γT)⁻¹`
- a sheaf / cellular-sheaf formulation over a base of contexts
- a directed-graph / quiver representation, given `w₃` asymmetry

Then **choose one as primary**, name which others survive as auxiliary
structure, and say plainly what each rejected framework would have bought you.
A survey that ends "all are useful" has not answered the question.

### THE HARD CONSTRAINTS

These are not preferences. A formulation violating any of them is wrong for
this project regardless of its mathematical merit.

1. **The circularity trap.** The framework must not encode the answer in its
   update rule. If activation spreads over a graph built from embedding
   similarity, the recovered topology is the embedding's, restated. State
   explicitly, for your chosen formalism, *what topological conclusions it
   makes structurally impossible to reach* — and if the answer is "none", the
   formalism is unfalsifiable here and you must say so.

2. **Every state variable earns its place or is deleted.** For each of
   `a, c, WM, φ, B, g, λ` give either (i) a number it changes that no other
   variable changes, or (ii) a hand-set decision it deletes. Any variable
   failing both must be dropped from your formulation, explicitly, with the
   deletion stated.

3. **Assembly size must emerge.** `k = 24` is a hand-set constant. Derive
   assembly width from the inhibition/excitation balance — give width as a
   function of `λ` and the activation distribution, with the fixed-point
   argument that makes it stable. This is the single cleanest test that the
   architecture is an improvement rather than an elaboration.

4. **No hand-set edge weights.** The five terms of `W` must be *learned* from
   the validation battery or *derived* from free energy. If you set them, the
   trap in (1) has already closed. Show the derivation or the learning
   objective.

5. **Directed edges.** `w₃` (temporal succession) makes `W` asymmetric. State
   precisely what this breaks in the existing cohomological treatment and what
   replaces it. Do not wave at this; it is the most interesting open question
   the architecture raises.

6. **`F_MOS` is not optional.** The predictive term must hook the existing free
   energy rather than run a parallel objective. Show the coupling.

7. **It must be simulable on the actual machine.** N ≈ 1074 concepts, dense
   `W`, 4 cores, 5.9 GB, jobs = 2, ~2.5 ms/tick. If your formulation needs an
   `N × N × N` object or a matrix inverse per tick, it is not admissible —
   say so and give the tractable approximation.

8. **The lag-CRP is the gate.** Your formulation must make the forward
   asymmetry of the lag-CRP a *derivable consequence*, not a fitted outcome.
   Show the derivation sketch. If your framework cannot produce it, say so
   plainly — that is a result, and a cheap one.

### EPISTEMIC RULES

- Tag every load-bearing claim: `[MEASURED]` `[DERIVED]` `[INFERRED]`
  `[ENGINEERING CHOICE]` `[OPEN HYPOTHESIS]` `[SPECULATION]`.
- Cite only from the attached verified bibliography. If you need a result that
  is not in it, write `[CITATION NEEDED: <author> <topic>]` — **do not** supply
  a reference from memory. Fabricated citations are the specific failure this
  project is built to prevent.
- Where you are extending TCM/CMR/ACT-R/SR/CLS rather than inventing, say so.
  The contribution is claimed to be the *formalisation*, not the architecture.
  If you think that claim is wrong, say that too.
- Distinguish what you derived from what you assumed. Assumptions get their own
  numbered list at the end.

### OUTPUT CONTRACT

```
§0  VERDICT           the chosen framework, in three sentences, plus the single
                      strongest objection to it
§1  SURVEY            candidates, what each buys, what each costs, why rejected
§2  OBJECTS           state space, measure, what a "tick" is as a morphism
§3  DYNAMICS          the tick loop as equations, each numbered EQ-n
§4  DERIVATIONS       EQ-n justified. For every equation give a SymPy block:
                          # EQ-7
                          lhs = ...
                          rhs = ...
                          assert simplify(lhs - rhs) == 0
                      Any step you cannot render this way, mark [UNCHECKED].
§5  EMERGENCE         assembly width from λ; the fixed point; stability
§6  LAG-CRP           derivation sketch of forward asymmetry
§7  CONSTRAINTS MET   constraints 1-8, each answered explicitly, one line each
§8  PREDICTIONS       ≥3 falsifiable, each with the number that would refute it
§9  ASSUMPTIONS       numbered, tagged
§10 WHAT I COULD NOT DO   be specific; this section is not optional and an
                          empty one will be treated as a failed pass
```

Length is not a virtue. §4 and §6 carry the weight.

---

## THE RED TEAM PROMPT

Run against a **different model family** than produced the draft.

> Below is a mathematical formulation produced by another model, together with
> the specification it was working from.
>
> **There is at least one substantive error.** It may be an algebra slip, a
> circular derivation that assumes what it proves, a state variable that does
> no work, a constraint silently violated, a citation that does not support the
> claim, or an emergence argument that is really a hidden hand-set constant.
>
> Find it. Rank what you find by severity. For each: quote the exact step, say
> what is wrong, and give the minimal repair.
>
> Do not summarise the document. Do not praise it. If after genuine effort you
> find only cosmetic issues, say "no structural error found" and list the three
> weakest points anyway — but that verdict is itself a claim you are
> accountable for, so do not reach it cheaply.
>
> Pay closest attention to §5 (emergence) and §6 (lag-CRP). Those are where a
> fitted result would be disguised as a derived one, and that is the specific
> failure mode this project has already suffered four times.

---

## LOOP

```bash
# 1. anchor the literature (free, no LLM)
python3 -m precilla cite verify docs/*.md --bibtex --log > bib.json

# 2. flat context -- resend THIS, never the transcript
python3 -m precilla ledger digest > state.md

# 3. lead pass   : PROMPT.md + docs + bib   -> draft.md
# 4. red team    : RED TEAM + draft.md      -> critique.md
# 5. verify      : extract §4 SymPy blocks, run them          [G1, not yet built]
# 6. record      : precilla ledger add --kind decision --tag DERIVED --text "..."
# 7. repeat 3-6 with critique.md appended, until the red team finds nothing
```

Stop when the red team returns "no structural error found" **and** every §4
block executes clean. Not before, and — importantly — not on the model's own
say-so that it is done.
