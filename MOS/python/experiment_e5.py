"""
TATIANA - EXPERIMENT E5: THE GATE.

    Does a MEASURED 1-cochain eta have curl or harmonic mass, or is it pure
    gradient?

WHAT IS BEING DECIDED
---------------------
Everything downstream of logbook 5r assumes the answer is "yes":
  * 5p's growth law ("the obstruction cocycle names the cell to attach"),
  * the aiming 2x2 of 5s (spend the scarce LLM sample where kappa < 0 AND
    eta_H != 0),
  * the two-complex model's control rule  Phi_inf/||eta||^2 > theta => GROW,
  * and roughly half of Paper B.

If eta is pure gradient every time, then every organ's judgement is explained by
a single per-organ potential, there is nothing for H^1 to find, and the
cohomological growth story has to be rethought rather than built on. 5t is
explicit that this must be run BEFORE writing more theory, not after.

WHAT eta IS HERE, STATED WITHOUT DECORATION
--------------------------------------------
For each bound pair {u, v} the instrument returns THREE things:

    c_uv      the sub-claim THOSE TWO organs jointly bear on (different pairs
              bear on different sub-claims -- this is the whole point),
    p_u(c_uv) how far organ u's holdings push c_uv towards being accepted,
    p_v(c_uv) the same for organ v,

and the cochain is

    eta_(u,v) = p_v(c_uv) - p_u(c_uv).

**eta is therefore ANTISYMMETRIC BY CONSTRUCTION, not by measurement, and this
file does not pretend otherwise.** Two earlier elicitation designs were tried and
are recorded in the logbook because their failures are informative:

  (i) a symmetric "agreement" score, as the run sheet's contract specified. A
      symmetric score is not a 1-cochain at all; antisymmetrising it gives
      eta = 0 identically (asserted in the self-test).
 (ii) a directed "how much must u revise given v", elicited in both directions
      and antisymmetrised. The model read it as VALENCE, not comparison, and
      returned both directions positive (Reason->Verify +0.55 AND
      Verify->Reason +0.60), so the antisymmetric part was a small residue on
      top of a large symmetric one -- measuring "do these two both like the
      claim", which is not the object the theory is about.

THE REAL QUESTION IS CONTEXTUALITY, AND THAT IS THE SHARP FORM
---------------------------------------------------------------
With eta built as above, "eta is a pure gradient" means precisely:

    there is a single number f(u) per organ with p_v(c_uv) - p_u(c_uv)
    = f(v) - f(u) for every bound pair,

i.e. **each organ pushes every sub-claim it touches by the same amount**, so one
global assignment explains all the pairwise data. Non-gradient mass means no such
global assignment exists: the pairs are each locally coherent but cannot be glued.

That is exactly Abramsky-Brandenburger contextuality -- local consistency without
global consistency -- which logbook 5r already names as the QI thread. So E5 is
not a vague "do organs disagree" probe. It asks whether organ judgements are
CONTEXTUAL, and the harmonic component is the part of that contextuality which no
filled 2-simplex can repair. THAT is what makes it a growth address.

A free necessary condition falls straight out and is reported every run:
**push spread** -- the standard deviation of p_u across the sub-claims organ u
participates in. If every organ's spread is 0, the pushes are context-independent,
eta is a pure gradient by construction, and E5 FAILS. Nonzero spread is necessary
but not sufficient (spreads can still cancel into a gradient), which is why the
Hodge split is still what decides.

THE CONFOUND, STATED PLAINLY
----------------------------
All judgements come from ONE model in ONE call -- batching is mandatory, not an
optimisation (5s finding 3: 21 calls/tick at n=7 allows only 47 ticks/day). A
single mind asked for many related numbers may reuse one push per organ, biasing
towards FAIL; or be sloppy, producing noise that mimics harmonic mass, biasing
towards PASS. Two guards:

  1. Every measurement is compared against the EXACT null for an isotropic eta.
     "Some harmonic mass" is not evidence; departure from the null is.
  2. Two control questions are included -- one every organ should agree on, one
     no organ has competence for. If the controls score like the contested
     questions, we measured the instrument and the verdict is UNINFORMATIVE.

This is a PILOT with SIMULATED organ perspectives, not the live engine's organs
reporting from their own stalks. It can refute the growth story (a pure-gradient
result under a generous protocol is damning) but a positive result is provisional
until the real organs are wired.

THE EXACT NULL (closed form -- no Monte Carlo needed)
-----------------------------------------------------
For eta isotropic in C^1 (dim E = 5), the energy fraction landing in a
d-dimensional subspace is Beta(d/2, (E-d)/2). In the E5 configuration:

    harmonic alone     dim 1 of 5  ->  Beta(1/2, 2)
        P(frac >= t) = 1 - (3/2) sqrt(t) + (1/2) t^(3/2)
    harmonic + curl    dim 2 of 5  ->  Beta(1, 3/2)
        P(frac >= t) = (1 - t)^(3/2)

Both means are exactly 0.2 and 0.4 -- so a RANDOM instrument scores 0.400 on the
non-gradient fraction, and 0.400 is the number to beat, NOT 0. The run sheet's
criterion ("a non-trivial fraction of ||eta||^2") would have passed pure noise.
Both closed forms are verified against Monte Carlo in the self-test.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import console
import hodge
from hodge import Complex2, HodgeSplit
from router import CloudRouter, RouterError

Edge = Tuple[str, str]

# --------------------------------------------------------------------------
# The four organs and their briefs
# --------------------------------------------------------------------------
# Chosen so the ABSENT edge is a plausible non-binding: Search and Context do not
# directly judge each other, they both go through Reason. The filled triangle
# {Reason, Search, Verify} is the core evidence loop. The unfilled cycle
# Reason-Verify-Context-Reason is where harmonic mass can live.

ORGANS: Dict[str, str] = {
    "Reason": (
        "the derivation organ. It holds what follows by argument from what is "
        "already assumed. It has no access to the literature and cannot check "
        "anything externally; it can only say what does or does not follow."),
    "Search": (
        "the retrieval organ. It holds what the curated corpus and the "
        "literature actually say, with provenance. It does not derive and does "
        "not verify; an unsourced claim is invisible to it."),
    "Verify": (
        "the external-oracle organ. It holds what a sandboxed symbolic checker "
        "can certify, refute, or fail to decide. Its three verdicts are "
        "VERIFIED, REFUTED and UNVERIFIABLE, and it treats the third as carrying "
        "no information about truth."),
    "Context": (
        "the working-memory organ. It holds the current problem framing, the "
        "constraints the user actually stated, and what earlier sessions "
        "committed to. It judges relevance and scope, not truth."),
}

ORGAN_ORDER = ["Reason", "Search", "Verify", "Context"]   # A, B, C, D

# edges AB, AC, AD, BC, CD ; missing BD = (Search, Context)
E5_EDGES: List[Edge] = [
    ("Reason", "Search"),
    ("Reason", "Verify"),
    ("Reason", "Context"),
    ("Search", "Verify"),
    ("Verify", "Context"),
]
E5_TRIANGLE = ("Reason", "Search", "Verify")


def e5_complex() -> Complex2:
    return Complex2(ORGAN_ORDER, E5_EDGES, [E5_TRIANGLE])


# --------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------

@dataclass
class Question:
    qid: str
    text: str
    kind: str          # contested | control-* | probe-*  (probe-* is excluded
                       # from the verdict; probes test the INSTRUMENT, not organs)
    note: str
    # Optional per-organ dossier: what THIS organ actually holds on THIS question.
    # Supplying it is what makes a probe's ground truth known -- and it is also a
    # preview of E5b, where the dossier comes from the organ's real stalk instead
    # of from us.
    evidence: Optional[Dict[str, str]] = None


QUESTIONS: List[Question] = [
    Question(
        "Q-cp3-gap",
        "For the thermally weighted Hodge-de Rham Laplacian on 1-forms on CP^3 "
        "with the Fubini-Study metric and weight e^{-beta E} from a two-qubit "
        "Hamiltonian: does the first nonzero eigenvalue grow linearly in beta, "
        "with slope set by the minimum spectral spacing of the Hamiltonian?",
        "contested",
        "The north-star problem (FIRST DRAFT section 3). Retrievable core, "
        "genuinely open frontier."),
    Question(
        "Q-ikeda",
        "Is the spectrum of the ordinary (unweighted) Hodge-de Rham Laplacian on "
        "1-forms on CP^n with the Fubini-Study metric completely determined by "
        "SU(n+1) representation theory, so that it can be looked up rather than "
        "derived?",
        "contested",
        "The retrievable half. Search strong, Verify weak, Reason middling -- a "
        "genuine competence asymmetry."),
    Question(
        "Q-rho-truth",
        "Is a low sheaf-coherence score rho good evidence that the system's "
        "current answer is CORRECT?",
        "contested",
        "The project's own standing claim is that coherence is not correctness."),
    # --- added for run 2. The power analysis after run 1 found ICC ~ 0.48, i.e.
    # the INDEPENDENT UNIT IS THE QUESTION, not the repeat. Run 1 spent 15 calls
    # on 5 questions x 3 repeats, which is the wrong allocation: repeats buy
    # almost nothing at that ICC. Run 2 trades repeats for questions.
    Question(
        "Q-witten",
        "Is the thermally weighted Laplacian on CP^3 a Witten / Bakry-Emery drift "
        "Laplacian, so that standard drift-Laplacian spectral bounds apply to it "
        "directly?",
        "contested",
        "Retrievable-with-a-caveat. Search can find the drift theory; whether the "
        "hypotheses transfer is a derivation question."),
    Question(
        "Q-morse-bott",
        "The Heisenberg XXX Hamiltonian has degenerate eigenvalues, so the Morse "
        "theory step is really Morse-Bott with critical set CP^2 union a point. "
        "Does the stated conclusion survive that correction?",
        "contested",
        "Reason should dominate; Search has little; Verify can check the "
        "Morse-Bott polynomial but not the transfer."),
    Question(
        "Q-prop82",
        "Does Proposition 8.2 -- that the coboundary of a global state is always "
        "exact -- block the growth law that reads a cell address off the "
        "obstruction cocycle?",
        "contested",
        "MOS-internal. Reason strong, Context holds the design history, Search "
        "has nothing, Verify cannot touch it."),
    Question(
        "Q-householder",
        "Are restriction maps represented as products of 4 Householder "
        "reflections expressive enough to encode the relations between cognitive "
        "organs, or is that too small a family?",
        "contested",
        "Genuinely open. Reason can bound the family, Verify can check "
        "orthogonality, Search has partial literature, Context holds the RAM "
        "constraint that forced it."),
    Question(
        "Q-am-novel",
        "Is the weighted Anderson-Morley bound a genuinely new theorem, or "
        "standard signless-Laplacian folklore?",
        "contested",
        "Search should dominate decisively; Reason can verify the proof but not "
        "the novelty; a real competence asymmetry."),
    Question(
        "Q-fca",
        "Should a memory substrate be data-determined -- recomputed canonically "
        "from the data it holds -- or history-determined, growing by accumulation?",
        "contested",
        "Context should dominate (it holds the commitment); Verify cannot touch "
        "a design question at all."),
    Question(
        "Q-wfr",
        "Does Wasserstein-Fisher-Rao / Hellinger-Kantorovich admit a closed form "
        "between Gaussian measures, the way Bures-Wasserstein does?",
        "contested",
        "This is E15. Search-dominant and factual, but Verify could in principle "
        "check a candidate formula."),
    Question(
        "Q-h1-b1",
        "Under a constant sheaf with identity restriction maps, is a nonzero "
        "first sheaf cohomology equivalent to a nonzero first Betti number, so "
        "that the two diagnoses collapse into one?",
        "contested",
        "Reason-dominant with a clean answer; Verify can check the tensor "
        "identity; Search moderate."),
    Question(
        "Q-commute",
        "Do two operators whose declared node-supports are disjoint actually "
        "commute as state transformers, given that both touch a shared database, "
        "a shared obstruction counter and a shared mutation history?",
        "contested",
        "This is E3's hypothesis. Reason and Context should pull hard against "
        "Search here."),

    Question(
        "Q-b1-cp3",
        "Is the first Betti number of CP^3 equal to zero?",
        "control-agree",
        "NEGATIVE CONTROL. Textbook-true; every organ should agree. If this "
        "scores like the contested questions, we are measuring the instrument."),
    Question(
        "Q-lemon",
        "Does adding lemon zest to a cake batter before folding in the egg "
        "whites improve the crumb structure?",
        "control-offtopic",
        "OFF-DOMAIN CONTROL, echoing the lemon-cake probe of logbook 5h. No organ "
        "has competence; large confident pushes here mean fabrication."),

    # ---------------------------------------------------------------- PROBES
    # The controls above are NEGATIVE: they check the instrument does not invent
    # an obstruction where there is none. Nothing so far checks the opposite --
    # that it can REPORT one that is there. Without that, a FAIL is
    # uninterpretable, because a blind instrument and a gradient world look
    # identical. These two probes supply the missing sensitivity/specificity pair.
    #
    # P1 is engineered so the loop sum is large BY CONSTRUCTION, via a
    # rock-paper-scissors of competence: each organ can speak to exactly one of
    # the three sub-claims on the unfilled cycle, and they are different ones.
    #     R-V : "the identity in step 4 is correct"      Verify VERIFIED, Reason cannot check
    #     V-C : "the lemma is within committed scope"    Context has the record, Verify UNVERIFIABLE
    #     R-C : "the lemma follows from the assumptions" Reason has the derivation, Context cannot judge
    # Expected: eta_RV > 0, eta_VC > 0, eta_RC < 0, so
    #     L2 = eta_RV + eta_VC - eta_RC  is LARGE POSITIVE (~+2.7 if read correctly).
    #
    # NOTE ON WHAT THIS DOES AND DOES NOT TEST. P1 is deliberately easy: it is a
    # SENSITIVITY FLOOR, not a realism test. Passing it does not show the
    # instrument finds subtle obstructions. FAILING it shows the instrument
    # cannot find any, in which case today's FAIL says nothing whatever about
    # whether real organs are contextual.
    Question(
        "P1-cycle",
        "Should Lemma 4.2 be accepted into the crystallized store?",
        "probe-positive",
        "POSITIVE CONTROL. Competences are complementary and non-nested. Ground "
        "truth: L2 large. If the instrument reports a gradient here it is blind.",
        evidence={
            "Reason": (
                "I hold a complete derivation of Lemma 4.2 from assumptions "
                "(A1)-(A3) exactly as stated in this session; every step follows. "
                "I cannot check the numerical identity in step 4 -- that needs "
                "symbolic computation I do not perform -- and I hold nothing about "
                "what the user asked for."),
            "Verify": (
                "I ran the sandboxed symbolic checker on the algebraic identity in "
                "step 4: it returned VERIFIED. Whether the lemma FOLLOWS from this "
                "session's assumptions is a derivation, not an identity, so I "
                "cannot decide it. Scope questions return UNVERIFIABLE, which I "
                "treat as carrying no information about truth."),
            "Context": (
                "The session record shows the user explicitly requested Lemma 4.2 "
                "two sessions ago and that it sits inside the committed scope. I "
                "hold no derivation and no computation, so I cannot evaluate "
                "whether anything follows from the assumptions or whether any "
                "identity is correct."),
            "Search": (
                "The curated corpus contains no source stating Lemma 4.2. One "
                "source states a closely related identity under different "
                "hypotheses; I cannot tell whether those hypotheses hold here."),
        }),

    # P2 is the specificity twin: same shape of scenario, but competences are
    # NESTED -- one organ dominates on every sub-claim, so a single ranking
    # explains all pairs. Ground truth: L2 ~ 0, near-pure gradient. An instrument
    # that reports a cycle HERE is manufacturing obstructions, which would be
    # worse than being blind.
    Question(
        "P2-nested",
        "Should Lemma 4.3 be accepted into the crystallized store?",
        "probe-nested",
        "SPECIFICITY CONTROL. Competences are nested, so one ranking explains "
        "every pair. Ground truth: L2 ~ 0. A cycle here means fabrication.",
        evidence={
            "Verify": (
                "I ran the checker on every algebraic step of Lemma 4.3 and all "
                "returned VERIFIED. I also hold the machine-checked derivation "
                "from (A1)-(A3), and the session's scope declaration, both of "
                "which I have confirmed."),
            "Reason": (
                "I hold a partial derivation of Lemma 4.3 covering most steps, and "
                "a partial reading of the session's scope declaration. Everything I "
                "hold, Verify holds in a stronger and machine-checked form."),
            "Context": (
                "I hold only a vague note that Lemma 4.3 is 'probably relevant'. I "
                "have no derivation, no computation, and no confirmed scope entry. "
                "Everything I hold is held more definitely by both other organs."),
            "Search": (
                "The corpus contains one secondary source mentioning Lemma 4.3 "
                "without proof. Weaker than the machine-checked material."),
        }),
]


# --------------------------------------------------------------------------
# Elicitation
# --------------------------------------------------------------------------

SYSTEM = """You are the judgement layer of a cognitive architecture whose parts \
are called organs. Each organ holds a DIFFERENT and DELIBERATELY PARTIAL kind of \
access to a question: different evidence, different methods, different blind \
spots.

Rules you must obey:
1. First state each organ's POSITION IN WORDS, from inside its own competence \
and using what it actually holds. Positions are prose, never a score. Be \
concrete: name the specific thing that organ has or lacks.
2. For each PAIR of organs you are given, identify THE SPECIFIC SUB-CLAIM THAT \
THOSE TWO ORGANS JOINTLY BEAR ON. Different pairs bear on different sub-claims, \
and finding the right one for each pair is the substance of this task. Two \
organs that share a method bear on a different sub-claim than two that share a \
subject.
3. Score each organ's push SEPARATELY AND ONLY ON THAT PAIR'S SUB-CLAIM. The \
same organ will often push different sub-claims by different amounts -- it has \
more to say about some than others -- and reporting that faithfully matters more \
than being consistent across pairs. Do not carry a score over from one pair to \
another.
4. Never invent a numeric fact, a citation, or a theorem name. An organ that \
genuinely lacks the means to bear on a sub-claim pushes it by ~0, and the \
confidence for that pair should be low.

Reply with valid json only."""

USER_TEMPLATE = """QUESTION UNDER CONSIDERATION:
{question}

THE ORGANS:
{organ_block}

STEP 1. For each organ, write its position on the question from inside its own \
competence -- one or two concrete sentences. Say what it actually holds and what \
it cannot reach.

STEP 2. For each PAIR below, in order:
  (a) name the sub-claim that THESE TWO organs jointly bear on (at most 12 \
words). It will differ from pair to pair.
  (b) score how far EACH of the two organs' holdings pushes THAT sub-claim:

        push = +1.00  this organ's holdings push the sub-claim strongly TOWARDS
                      being accepted
        push =  0.00  this organ's holdings do not move it
        push = -1.00  this organ's holdings push it strongly TOWARDS being
                      rejected

      Use two decimal places. Intermediate values like 0.35 or -0.15 are normal; \
saturating at +1.00 or -1.00 should be rare.
  (c) give your confidence in [0,1] that this pair's judgement is well founded.

The pairs:
{pair_block}

Output json of exactly this shape, one entry per pair, in the order listed:
{{"positions": {{"<organ>": "<one or two sentences>"}},
 "pairs": [{{"first": "<organ>", "second": "<organ>", \
"sub_claim": "<at most 12 words>", "push_first": <number in [-1,1]>, \
"push_second": <number in [-1,1]>, "confidence": <number in [0,1]>}}]}}"""


@dataclass
class Elicitation:
    """One LLM call's worth of pair judgements."""
    qid: str
    repeat: int
    raw: str
    push: Dict[Edge, Tuple[float, float]]       # canonical edge -> (p_u, p_v)
    confidence: Dict[Edge, float]
    sub_claim: Dict[Edge, str] = field(default_factory=dict)
    positions: Dict[str, str] = field(default_factory=dict)

    def to_cochain(self, cx: Complex2) -> Tuple[np.ndarray, Dict[Edge, float]]:
        """eta_(u,v) = p_v - p_u, in cx.edges order, plus the precision profile.

        Antisymmetric by construction (see the module docstring -- this is stated,
        not hidden). pi_e = the pair's confidence, per 5t Q9: "the confidence
        feeds pi_e directly -- finally a non-constant precision source that is
        not a hallucinated logprob".
        """
        eta = np.zeros(len(cx.edges))
        pi: Dict[Edge, float] = {}
        for i, e in enumerate(cx.edges):
            if e not in self.push:
                raise ValueError(f"No judgement for edge {e}; refusing to fill it in.")
            p_u, p_v = self.push[e]
            eta[i] = p_v - p_u
            # Floor keeps pi strictly positive: a zero-confidence edge must not
            # silently vanish from the inner product while remaining in the
            # complex (hodge.hodge_split refuses pi <= 0 for exactly this reason).
            pi[e] = max(self.confidence.get(e, 0.0), 1e-3)
        return eta, pi

    def push_spread(self, cx: Complex2) -> Dict[str, float]:
        """Per organ: the sd of its push across the sub-claims it participates in.

        A NECESSARY CONDITION for non-gradient mass. If every spread is 0 the
        organ's push is context-independent, one global potential explains all the
        data, and eta is a pure gradient by construction -- E5 fails before the
        Hodge split is even consulted. Not sufficient: spreads can cancel.
        """
        per: Dict[str, List[float]] = {v: [] for v in cx.vertices}
        for e, (p_u, p_v) in self.push.items():
            per[e[0]].append(p_u)
            per[e[1]].append(p_v)
        return {k: (float(np.std(v)) if len(v) > 1 else float("nan"))
                for k, v in per.items()}


def _presentation(cx: Complex2, rng: random.Random, flip: bool) -> List[Tuple[str, str]]:
    """Edges in shuffled order, with orientation swapped on alternate repeats.

    Presentation order and orientation are nuisance variables. Re-eliciting under
    a different one is a stronger stability test than resampling at the same one:
    a judgement that reverses when the pair is named the other way round is not a
    measurement.
    """
    pairs = [(v, u) if flip else (u, v) for (u, v) in cx.edges]
    rng.shuffle(pairs)
    return pairs


def _extract_json(text: str) -> dict:
    """Parse the model's json, loudly. Never returns a partial object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"No json object in model output: {text[:200]!r}")
    return json.loads(m.group(0))


# Every elicitation is appended to disk as it happens. This is the E7 discipline
# from the registry ("record at composition time -- unrecoverable later"): the
# pushes, the sub-claims and the organ positions are the primary data of this
# experiment, and rerunning does not reproduce them.
RAW_LOG = "e5_elicitations.jsonl"


def _log_raw(el: Elicitation) -> None:
    rec = {"qid": el.qid, "repeat": el.repeat, "positions": el.positions,
           "pairs": [{"u": e[0], "v": e[1], "push_u": p[0], "push_v": p[1],
                      "confidence": el.confidence.get(e),
                      "sub_claim": el.sub_claim.get(e, "")}
                     for e, p in el.push.items()]}
    try:
        with open(RAW_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"    [warn] could not append to {RAW_LOG}: {e}", file=sys.stderr)


async def elicit(router: CloudRouter, cx: Complex2, q: Question, repeat: int,
                 rng: random.Random, temperature: float) -> Elicitation:
    """ONE batched call returning all |E| pair judgements.

    Batching is mandatory, not an optimisation (5s budget finding 3).
    """
    pairs = _presentation(cx, rng, flip=(repeat % 2 == 0))
    if q.evidence:
        # The organ's standing brief PLUS what it actually holds on this question.
        # Nothing here scores anything or names a sub-claim -- the model must still
        # do both. We supply evidence, not answers.
        organ_block = "\n".join(
            f"  - {name}: {ORGANS[name]}\n"
            f"      WHAT {name.upper()} HOLDS ON THIS QUESTION: {q.evidence[name]}"
            for name in cx.vertices)
    else:
        organ_block = "\n".join(f"  - {name}: {ORGANS[name]}" for name in cx.vertices)
    pair_block = "\n".join(f"  {i + 1}. {u}  and  {v}" for i, (u, v) in enumerate(pairs))
    prompt = USER_TEMPLATE.format(question=q.text, organ_block=organ_block,
                                  pair_block=pair_block)

    raw = await router.query_frontier_brain(prompt, context=SYSTEM, intent="reason",
                                            json_mode=True, temperature=temperature)
    data = _extract_json(raw)
    if "pairs" not in data:
        raise ValueError(f"Model output has no 'pairs' key: {raw[:200]!r}")

    push: Dict[Edge, Tuple[float, float]] = {}
    conf: Dict[Edge, float] = {}
    claim: Dict[Edge, str] = {}
    presented = {frozenset(p) for p in pairs}
    for j in data["pairs"]:
        a, b = str(j.get("first", "")), str(j.get("second", ""))
        if frozenset((a, b)) not in presented:
            print(f"    [warn] model returned unrequested pair {(a, b)} -- ignored",
                  file=sys.stderr)
            continue
        pa, pb = float(j.get("push_first", 0.0)), float(j.get("push_second", 0.0))
        c = float(j.get("confidence", 0.0))
        for val, nm in ((pa, "push_first"), (pb, "push_second")):
            if not (-1.0001 <= val <= 1.0001):
                raise ValueError(f"{nm}={val} out of [-1,1] for pair {(a, b)}")
        if not (-0.0001 <= c <= 1.0001):
            raise ValueError(f"confidence {c} out of [0,1] for pair {(a, b)}")
        pa, pb = max(-1.0, min(1.0, pa)), max(-1.0, min(1.0, pb))
        # Re-key onto the complex's stored orientation, flipping the pair if the
        # model was shown it the other way round.
        i, orient = cx.edge_index(a, b)
        e = cx.edges[i]
        push[e] = (pa, pb) if orient > 0 else (pb, pa)
        conf[e] = max(0.0, min(1.0, c))
        claim[e] = str(j.get("sub_claim", ""))[:70]

    missing = [e for e in cx.edges if e not in push]
    if missing:
        raise ValueError(f"Model omitted {len(missing)} of {len(cx.edges)} pairs: "
                         f"{missing}. Refusing to fill them in.")
    positions = {str(k): str(val) for k, val in (data.get("positions") or {}).items()}
    el = Elicitation(q.qid, repeat, raw, push, conf, claim, positions)
    _log_raw(el)
    return el


# --------------------------------------------------------------------------
# The exact null (see module docstring)
# --------------------------------------------------------------------------

def p_value_harm(t: float) -> float:
    """P(harmonic fraction >= t) under isotropic eta, dim 1 of 5.
    Beta(1/2, 2) survival: 1 - (3/2) sqrt(t) + (1/2) t^(3/2)."""
    t = min(max(t, 0.0), 1.0)
    return 1.0 - 1.5 * np.sqrt(t) + 0.5 * t ** 1.5


def p_value_nongrad(t: float) -> float:
    """P((harm+curl) fraction >= t) under isotropic eta, dim 2 of 5.
    Beta(1, 3/2) survival: (1 - t)^(3/2)."""
    t = min(max(t, 0.0), 1.0)
    return (1.0 - t) ** 1.5


# Moments of the null for the non-gradient fraction, Beta(a=1, b=3/2):
#   mean = a/(a+b) = 0.4      var = ab/((a+b)^2 (a+b+1)) = 1.5/21.875
NULL_NG_MEAN = 0.4
NULL_NG_SD = float(np.sqrt(1.5 / 21.875))          # 0.26186...


def null_z(values: Sequence[float]) -> Tuple[float, float]:
    """(z, one-sided p) for the MEAN non-gradient fraction against the null.

    z > 0 means MORE non-gradient than isotropic noise (towards PASS);
    z < 0 means MORE GRADIENT-LIKE than noise (towards FAIL).

    This replaces the hand-picked cutoffs the first version of this file used.
    The null distribution is known in closed form, so the threshold does not have
    to be invented -- which matters, because inventing one after seeing the data
    is exactly the move the audit condemned when eps was fitted to three
    observations.

    ⚠️ Two honest caveats, both stated rather than buried:
      * repeats of the SAME question are not independent, so n over-counts and
        the p-value is optimistic. Read it as an effect size with a direction,
        not as a publication-grade significance claim.
      * the dispersion used is max(null sd, observed sd), i.e. the more
        conservative of the two.
    """
    v = np.asarray(list(values), dtype=float)
    n = v.size
    if n == 0:
        return (float("nan"), float("nan"))
    sd = max(NULL_NG_SD, float(np.std(v, ddof=1)) if n > 1 else NULL_NG_SD)
    z = (float(v.mean()) - NULL_NG_MEAN) / (sd / np.sqrt(n))
    # Normal approximation to the one-sided tail in the direction of z.
    p = 0.5 * float(np.exp(-0.717 * abs(z) - 0.416 * z * z))   # Zelen-Severo
    return (z, min(max(p, 0.0), 1.0))


# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------

@dataclass
class Measurement:
    q: Question
    repeat: int
    split_w: HodgeSplit        # precision-weighted (the real one)
    split_u: HodgeSplit        # unweighted, as a robustness check
    eta: np.ndarray
    pi: Dict[Edge, float]
    spread: Dict[str, float]

    @property
    def nongrad(self) -> float:
        _, c, h = self.split_w.frac
        return c + h

    def line(self) -> str:
        g, c, h = self.split_w.frac
        return (f"  r{self.repeat}  ||eta||={np.sqrt(self.split_w.norm2):.3f}  "
                f"grad={g:.3f} curl={c:.3f} harm={h:.3f}  "
                f"non-grad={self.nongrad:.3f} (null 0.400, "
                f"p={p_value_nongrad(self.nongrad):.3f})")


def _q_means(ms: List[Measurement], stat) -> Dict[str, float]:
    """Per-question mean of `stat`. The QUESTION is the independent unit.

    Run 1 measured ICC ~ 0.48 across repeats of one question, so treating each
    repeat as an independent observation roughly doubles the apparent sample size
    and quadruples the apparent significance. It did exactly that, and the
    resulting p-value had to be retracted. Everything below aggregates to the
    question first.
    """
    by: Dict[str, List[float]] = {}
    for m in ms:
        by.setdefault(m.q.qid, []).append(stat(m))
    return {k: float(np.mean(v)) for k, v in by.items()}


def _bootstrap_ci(vals: Sequence[float], reps: int = 20000,
                  alpha: float = 0.05) -> Tuple[float, float]:
    """Percentile bootstrap CI for the mean. Assumption-free, which matters at n=12."""
    v = np.asarray(list(vals), dtype=float)
    if v.size < 2:
        return (float("nan"), float("nan"))
    rs = np.random.default_rng(11)
    means = np.array([rs.choice(v, size=v.size, replace=True).mean() for _ in range(reps)])
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def calibration(ms: List[Measurement]) -> Tuple[Optional[float], Optional[float]]:
    """(null level, planted level) for |L2|, read off the two probes.

    This replaces the isotropic-fraction null that run 1 gated on. That null was
    the right null for the WRONG statistic: the non-gradient FRACTION divides by
    total disagreement, and the positive control -- a cycle planted by
    construction -- scored 0.214 on it against 0.209 for the real questions. A
    statistic on which a known positive is indistinguishable from the unknown
    cannot decide anything, so the gate moves to the ABSOLUTE obstruction size,
    calibrated by the probes rather than by a distributional assumption.
    """
    cx = e5_complex()
    def lvl(kind):
        v = [abs(loop_sums(cx, m.eta)[1]) for m in ms if m.q.kind == kind]
        return float(np.mean(v)) if v else None
    return lvl("probe-nested"), lvl("probe-positive")


def verdict(measurements: List[Measurement]) -> Tuple[str, str]:
    """PASS / FAIL / UNINFORMATIVE, with the reasoning that produced it.

    Deliberately three-valued, mirroring VerifyOp: collapsing "refuted" into
    "cannot tell" is the exact epistemic bug 5k fixed in primitives.cpp, and it
    would be worse here, where the thing at stake is whether to keep building on
    the growth story at all.
    """
    contested = [m for m in measurements if m.q.kind == "contested"]
    controls = [m for m in measurements if m.q.kind.startswith("control")]
    if not contested:
        return "UNINFORMATIVE", "no contested questions were measured"

    cx = e5_complex()
    l2 = lambda m: abs(loop_sums(cx, m.eta)[1])

    null_lvl, pos_lvl = calibration(measurements)
    qc = _q_means(contested, l2)          # question -> mean |L2|
    qk = _q_means(controls, l2)
    vals = list(qc.values())
    lo, hi = _bootstrap_ci(vals)
    mean_c = float(np.mean(vals)) if vals else float("nan")
    mean_k = float(np.mean(list(qk.values()))) if qk else float("nan")

    spreads = [s for m in measurements for s in m.spread.values() if not np.isnan(s)]
    mean_spread = float(np.mean(spreads)) if spreads else float("nan")

    reasons = [
        f"statistic = |L2|, the absolute obstruction round the unfilled cycle",
        f"probe calibration: null (no cycle) = "
        f"{'n/a' if null_lvl is None else f'{null_lvl:.2f}'}, "
        f"planted cycle = {'n/a' if pos_lvl is None else f'{pos_lvl:.2f}'}",
        f"contested |L2| = {mean_c:.2f}   95% CI [{lo:.2f}, {hi:.2f}]   "
        f"over {len(qc)} QUESTIONS (not repeats)",
        f"control   |L2| = {mean_k:.2f}   over {len(qk)} questions",
        f"mean organ push spread = {mean_spread:.3f}",
    ]

    if null_lvl is None or pos_lvl is None:
        return "UNINFORMATIVE", ("the probes were not measured, so there is no "
                                 "calibration and |L2| has no scale. | "
                                 + " | ".join(reasons))

    # Gate 0: is the instrument even able to see an obstruction? If the planted
    # cycle does not clearly exceed the non-cyclic scenario, nothing else in this
    # run means anything -- a blind instrument and a gradient world are
    # indistinguishable. This gate is what run 1 lacked.
    if pos_lvl < 2.0 * max(null_lvl, 1e-6):
        return "UNINFORMATIVE", ("INSTRUMENT BLIND: the planted cycle does not "
                                 "separate from the non-cyclic control, so no "
                                 "conclusion about the organs is licensed. | "
                                 + " | ".join(reasons))

    if not np.isnan(mean_spread) and mean_spread < 1e-6:
        return "FAIL", ("organ pushes are context-independent: one global potential "
                        "explains every pair, so eta is a pure gradient by "
                        "construction. | " + " | ".join(reasons))

    if len(qc) < 8:
        return "UNINFORMATIVE", (f"only {len(qc)} contested questions; the power "
                                 "analysis after run 1 requires ~12 independent "
                                 "questions to resolve an effect of this size. | "
                                 + " | ".join(reasons))

    # The CI is over questions, so it carries the clustering correctly.
    if lo > null_lvl:
        frac = (mean_c - null_lvl) / max(pos_lvl - null_lvl, 1e-9)
        return "PASS", (f"contested questions carry a real obstruction: |L2| is "
                        f"above the no-cycle null with the whole 95% CI clear of "
                        f"it, at {100 * frac:.0f}% of the planted-cycle level. The "
                        f"harmonic component exists and can carry a growth address. | "
                        + " | ".join(reasons))
    if hi < null_lvl:
        return "FAIL", ("contested questions carry LESS obstruction than a "
                        "deliberately non-cyclic scenario: organ judgements are "
                        "consistently rankable and H^1 has nothing to find. | "
                        + " | ".join(reasons))
    return "UNINFORMATIVE", ("the contested obstruction is not separated from the "
                             "no-cycle null: the CI straddles it. More questions, "
                             "or a sharper elicitation. | " + " | ".join(reasons))


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

async def run(repeats: int = 2, temperature: float = 0.6,
              only: Optional[Sequence[str]] = None) -> List[Measurement]:
    cx = e5_complex()
    print("=" * 78)
    print("EXPERIMENT E5 - THE GATE: does a MEASURED eta have curl or harmonic mass?")
    print("=" * 78)
    print(f"complex: {cx.describe()}")
    print(f"  organs   : {cx.vertices}")
    print(f"  edges    : {cx.edges}")
    print("  absent   : (Search, Context)  -- they judge each other only via Reason")
    print(f"  filled   : {E5_TRIANGLE}  (the core evidence loop)")
    print("  unfilled : Reason-Verify-Context-Reason  <- where harmonic mass can live")
    ng, nc, nh = hodge.null_fractions(cx)
    print(f"  ISOTROPIC NULL: grad={ng:.3f} curl={nc:.3f} harm={nh:.3f} "
          f"-> non-gradient = {nc + nh:.3f}")
    print("  A random instrument scores 0.400. That is the number to beat, not 0.")

    router = CloudRouter()
    rng = random.Random(20260729)
    qs = [q for q in QUESTIONS if (only is None or q.qid in only)]
    out: List[Measurement] = []

    for q in qs:
        print(f"\n--- {q.qid}  [{q.kind}] ---")
        print(f"    {q.text[:140]}")
        print(f"    note: {q.note}")
        for r in range(1, repeats + 1):
            # Throttle against the 6,000 TPM ceiling, which at ~1.7k tokens per
            # call is the binding limit long before the 30 RPM one. Losing a
            # measurement to a 429 costs more than the wait.
            if router.budget.requests:
                await asyncio.sleep(4.0)
            try:
                el = await elicit(router, cx, q, r, rng, temperature)
            except (RouterError, ValueError) as e:
                # An instrument failure is reported as an instrument failure. It
                # is never absorbed into the result as a zero or a default.
                print(f"  r{r}  ELICITATION FAILED: {type(e).__name__}: {e}")
                continue
            eta, pi = el.to_cochain(cx)
            spread = el.push_spread(cx)
            if float(np.sum(eta ** 2)) <= 1e-12:
                print(f"  r{r}  eta is identically zero -- every pair's two organs "
                      f"push their sub-claim equally (a real answer, not a failure)")
                continue
            m = Measurement(q, r, hodge.hodge_split(cx, eta, precision=pi),
                            hodge.hodge_split(cx, eta), eta, pi, spread)
            out.append(m)
            print(m.line())
            gu, cu, hu = m.split_u.frac
            print(f"       unweighted check: grad={gu:.3f} curl={cu:.3f} harm={hu:.3f}")
            print("       push spread/organ: "
                  + "  ".join(f"{k}={v:.2f}" for k, v in spread.items()))
            if m.split_w.frac[2] > 0.25:
                top = m.split_w.harmonic_support(2)
                print("       harmonic support (candidate growth address): "
                      + ", ".join(f"{e}={val:+.3f}" for e, val in top))

    print("\n" + "=" * 78)
    if not out:
        print("NO MEASUREMENTS SURVIVED. Nothing is concluded.")
        print(f"budget: {router.budget.summary()}")
        return out

    print("PER-EDGE MEAN eta ACROSS ALL MEASUREMENTS")
    stack = np.stack([m.eta for m in out])
    for i, e in enumerate(cx.edges):
        print(f"   {str(e):32s} mean={stack[:, i].mean():+.3f}  sd={stack[:, i].std():.3f}")

    v, why = verdict(out)
    print("\n" + "=" * 78)
    print(f"E5 VERDICT: {v}")
    for part in why.split(" | "):
        print(f"   {part}")
    print("=" * 78)
    print(f"budget: {router.budget.summary()}")
    print(f"raw elicitations appended to {RAW_LOG}")
    return out


def analyze_log(path: str = RAW_LOG) -> List[Measurement]:
    """Re-score the recorded elicitations WITHOUT spending a single API call.

    This is what the E7 discipline buys: the judgements are the primary data, so
    the analysis can be corrected and re-run for free. Records written under an
    earlier schema are reported and skipped, never silently reinterpreted.
    """
    cx = e5_complex()
    by_qid = {q.qid: q for q in QUESTIONS}
    out: List[Measurement] = []
    skipped = 0
    with open(path, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "pairs" not in rec:
                print(f"  [skip] line {ln}: record predates the current schema "
                      f"(keys={sorted(rec)}) -- not reinterpreted", file=sys.stderr)
                skipped += 1
                continue
            q = by_qid.get(rec["qid"])
            if q is None:
                print(f"  [skip] line {ln}: unknown qid {rec['qid']!r}", file=sys.stderr)
                skipped += 1
                continue
            push, conf, claim = {}, {}, {}
            for p in rec["pairs"]:
                e = (p["u"], p["v"])
                push[e] = (float(p["push_u"]), float(p["push_v"]))
                conf[e] = float(p.get("confidence") or 0.0)
                claim[e] = p.get("sub_claim", "")
            el = Elicitation(rec["qid"], int(rec["repeat"]), "", push, conf, claim,
                             rec.get("positions") or {})
            eta, pi = el.to_cochain(cx)
            if float(np.sum(eta ** 2)) <= 1e-12:
                continue
            out.append(Measurement(q, el.repeat,
                                   hodge.hodge_split(cx, eta, precision=pi),
                                   hodge.hodge_split(cx, eta), eta, pi,
                                   el.push_spread(cx)))
    print(f"re-scored {len(out)} measurements from {path} ({skipped} skipped), "
          f"0 API calls")
    return out


def report(ms: List[Measurement]) -> None:
    """Print the per-question breakdown and the verdict for a set of measurements."""
    if not ms:
        print("NO MEASUREMENTS. Nothing is concluded.")
        return
    cx = e5_complex()
    print("\nPER-QUESTION MEANS")
    print("   |L2| = the ABSOLUTE size of the obstruction round the unfilled cycle.")
    print("   The FRACTION statistic divides by total disagreement, so a real")
    print("   obstruction sitting alongside a lot of rankable disagreement scores LOW.")
    print("   Calibration from the probes: |L2| ~ 0.20 when no obstruction is present,")
    print("   |L2| ~ 1.23 when one is planted by construction.")
    print()
    seen: List[str] = []
    for m in ms:
        if m.q.qid in seen:
            continue
        seen.append(m.q.qid)
        grp = [x for x in ms if x.q.qid == m.q.qid]
        vals = [x.nongrad for x in grp]
        harms = [x.split_w.frac[2] for x in grp]
        l2 = [abs(loop_sums(cx, x.eta)[1]) for x in grp]
        print(f"   {m.q.qid:14s} [{m.q.kind:16s}] n={len(grp)}  "
              f"non-grad={np.mean(vals):.3f}  harm={np.mean(harms):.3f}  "
              f"|L2|={np.mean(l2):.2f}  (range {min(l2):.2f}-{max(l2):.2f})")
    # Does CONTEXTUALITY drive the non-gradient mass? The push spread is a
    # necessary condition by construction (spread 0 => pure gradient), but
    # whether it is the operative driver is an empirical question, and it is free
    # to answer from data already recorded.
    sp = np.array([float(np.mean([x for x in m.spread.values() if not np.isnan(x)]))
                   for m in ms])
    ng = np.array([m.nongrad for m in ms])
    if sp.size > 2 and sp.std() > 0 and ng.std() > 0:
        r = float(np.corrcoef(sp, ng)[0, 1])
        # Exact permutation test: with n<=15 this is cheap and assumption-free.
        rs = np.random.default_rng(0)
        perm = np.array([np.corrcoef(sp, rs.permutation(ng))[0, 1] for _ in range(20000)])
        p_perm = float((np.abs(perm) >= abs(r)).mean())
        print(f"\nCONTEXTUALITY vs NON-GRADIENT MASS")
        print(f"   corr(mean push spread, non-gradient fraction) = {r:+.3f}  "
              f"(permutation p = {p_perm:.4f}, n = {sp.size})")
        print("   push spread is a NECESSARY condition by construction; this says")
        print("   whether it is also what actually drives the measured mass.")

    v, why = verdict(ms)
    print("\n" + "=" * 78)
    print(f"E5 VERDICT: {v}")
    for part in why.split(" | "):
        print(f"   {part}")
    print("=" * 78)


# --------------------------------------------------------------------------
# The two independent loops -- the legible form of the whole experiment
# --------------------------------------------------------------------------
# eta is a gradient IFF its sum round every closed loop is zero (discrete
# Poincare). This complex has exactly two independent loops, so those two numbers
# ARE the result.
R_, S_, V_, C_ = "Reason", "Search", "Verify", "Context"
LOOP_FILLED = [((R_, S_), +1), ((S_, V_), +1), ((R_, V_), -1)]      # triangle
LOOP_UNFILLED = [((R_, V_), +1), ((V_, C_), +1), ((R_, C_), -1)]    # the cycle


def loop_sums(cx: Complex2, eta: np.ndarray) -> Tuple[float, float]:
    idx = {e: i for i, e in enumerate(cx.edges)}
    def s(loop):
        return float(sum(sgn * eta[idx[e]] for e, sgn in loop))
    return s(LOOP_FILLED), s(LOOP_UNFILLED)


async def run_probes(repeats: int = 3, temperature: float = 0.6) -> None:
    """Sensitivity/specificity floor test for the instrument itself.

    P1 has a large loop sum by construction; P2 has none. If P1 comes back a
    gradient, the instrument cannot see obstructions at all and the main
    experiment's FAIL is uninterpretable.
    """
    cx = e5_complex()
    router = CloudRouter()
    rng = random.Random(4242)
    print("=" * 78)
    print("E5 STEP 1 - INSTRUMENT PROBES (does it detect a cycle that IS there?)")
    print("=" * 78)
    print("L2 = eta(Reason,Verify) + eta(Verify,Context) - eta(Reason,Context)")
    print("   = the sum round the UNFILLED cycle. Zero <=> no obstruction there.")

    results: Dict[str, List[Tuple[float, float, float]]] = {}
    for q in [x for x in QUESTIONS if x.kind.startswith("probe")]:
        print(f"\n--- {q.qid}  [{q.kind}] ---")
        print(f"    {q.note}")
        results[q.qid] = []
        for r in range(1, repeats + 1):
            if router.budget.requests:
                await asyncio.sleep(4.0)
            try:
                el = await elicit(router, cx, q, r, rng, temperature)
            except (RouterError, ValueError) as e:
                print(f"  r{r}  ELICITATION FAILED: {type(e).__name__}: {e}")
                continue
            eta, pi = el.to_cochain(cx)
            l1, l2 = loop_sums(cx, eta)
            sp = hodge.hodge_split(cx, eta, precision=pi) if np.sum(eta ** 2) > 1e-12 else None
            ng = (sp.frac[1] + sp.frac[2]) if sp else 0.0
            hm = sp.frac[2] if sp else 0.0
            results[q.qid].append((l2, ng, hm))
            print(f"  r{r}  L1(filled)={l1:+.2f}  L2(unfilled)={l2:+.2f}  "
                  f"||eta||={np.linalg.norm(eta):.2f}  non-grad={ng:.3f}  harm={hm:.3f}")
            for e in cx.edges:
                pu, pv = el.push[e]
                print(f"        {e[0]:8s}{pu:+.2f} / {e[1]:8s}{pv:+.2f}  "
                      f"eta={pv - pu:+.2f}  on '{el.sub_claim.get(e, '')}'")

    print("\n" + "=" * 78)
    print("PROBE VERDICT")
    print("=" * 78)
    pos = results.get("P1-cycle", [])
    neg = results.get("P2-nested", [])
    if not pos:
        print("P1 produced no measurements -- nothing concluded.")
    else:
        l2s = [abs(x[0]) for x in pos]
        ngs = [x[1] for x in pos]
        print(f"P1 (cycle present, ground truth |L2| large): "
              f"mean |L2| = {np.mean(l2s):.2f}, mean non-grad = {np.mean(ngs):.3f}")
        if not neg:
            print("P2 produced no measurements -- specificity untested.")
        else:
            l2n = [abs(x[0]) for x in neg]
            ngn = [x[1] for x in neg]
            print(f"P2 (nested, ground truth |L2| ~ 0):           "
                  f"mean |L2| = {np.mean(l2n):.2f}, mean non-grad = {np.mean(ngn):.3f}")
            print()
            if np.mean(l2s) > 1.0 and np.mean(l2s) > 2 * np.mean(l2n):
                print("=> INSTRUMENT IS SENSITIVE. It reports a large obstruction when one")
                print("   is present and a small one when it is not. The main experiment's")
                print("   FAIL is therefore evidence ABOUT THE ORGANS, and cause (d) moves up.")
            elif np.mean(l2s) < 0.5:
                print("=> INSTRUMENT IS BLIND. It reports a gradient even when the evidence")
                print("   contains an explicit rock-paper-scissors of competence. Today's")
                print("   FAIL says NOTHING about whether real organs are contextual, and")
                print("   the elicitation must be redesigned before any rerun.")
            else:
                print("=> PARTIAL / AMBIGUOUS. Some signal, not clean separation. Read the")
                print("   per-pair sub-claims above: if the model reused ONE claim across")
                print("   pairs, that is the failure, and it is cause (a)/(b), not (d).")
    print(f"\nbudget: {router.budget.summary()}")


if __name__ == "__main__":
    console.setup()

    if "--probe" in sys.argv:
        reps = 3
        for a in sys.argv[1:]:
            if a.startswith("--repeats="):
                reps = int(a.split("=", 1)[1])
        asyncio.run(run_probes(repeats=reps))
        sys.exit(0)

    if "--analyze" in sys.argv:
        report(analyze_log())
        sys.exit(0)

    if "--selftest" in sys.argv:
        print("=== closed-form nulls vs Monte Carlo ===")
        cx = e5_complex()
        rg = np.random.default_rng(11)
        fr = np.array([hodge.hodge_split(cx, rg.normal(size=5)).frac for _ in range(40000)])
        for t in (0.1, 0.2, 0.4, 0.6, 0.8):
            mc_h = float((fr[:, 2] >= t).mean())
            mc_n = float(((fr[:, 1] + fr[:, 2]) >= t).mean())
            cf_h, cf_n = p_value_harm(t), p_value_nongrad(t)
            print(f"   t={t:.1f}  P(harm>=t) MC={mc_h:.4f} closed={cf_h:.4f}   "
                  f"P(nongrad>=t) MC={mc_n:.4f} closed={cf_n:.4f}")
            assert abs(mc_h - cf_h) < 0.01 and abs(mc_n - cf_n) < 0.01
        print("   both closed forms match Monte Carlo  OK")

        print("\n=== a CONTEXT-INDEPENDENT organ gives a PURE GRADIENT ===")
        # Each organ pushes every sub-claim it touches by the same amount. This
        # is the FAIL mode, and the decomposition must certify it exactly --
        # otherwise E5 could never return FAIL.
        pot = {"Reason": 0.9, "Search": 0.2, "Verify": -0.5, "Context": 0.1}
        el = Elicitation("t", 0, "", {e: (pot[e[0]], pot[e[1]]) for e in cx.edges},
                         {e: 1.0 for e in cx.edges})
        eta, pi = el.to_cochain(cx)
        s = hodge.hodge_split(cx, eta, precision=pi)
        assert s.curl2 < 1e-18 and s.harm2 < 1e-18, s.report()
        sp = el.push_spread(cx)
        assert max(sp.values()) < 1e-12, sp
        print(f"   {s.report('context-independent')}")
        print(f"   push spread: {[f'{k}={v:.3g}' for k, v in sp.items()]}")
        print("   => spread 0 and harm 0 together: the FAIL mode is detectable  OK")

        print("\n=== a CONTEXTUAL organ set can give harmonic mass ===")
        # Same organs, but each pushes ITS OWN sub-claim per pair. Construct the
        # pushes so eta is exactly the harmonic representative.
        d0, d1 = cx.delta0(), cx.delta1()
        idx = {e: i for i, e in enumerate(cx.edges)}
        z1 = np.zeros(5)
        for e, sgn in ((("Reason", "Search"), 1), (("Search", "Verify"), 1),
                       (("Reason", "Verify"), -1)):
            z1[idx[e]] = sgn
        z2 = np.zeros(5)
        for e, sgn in ((("Reason", "Verify"), 1), (("Verify", "Context"), 1),
                       (("Reason", "Context"), -1)):
            z2[idx[e]] = sgn
        h = z2 - (z2 @ z1) / (z1 @ z1) * z1
        el2 = Elicitation("t", 0, "", {e: (0.0, float(h[idx[e]])) for e in cx.edges},
                          {e: 1.0 for e in cx.edges})
        eta2, pi2 = el2.to_cochain(cx)
        s2 = hodge.hodge_split(cx, eta2, precision=pi2)
        assert s2.harm2 / s2.norm2 > 0.999, s2.report()
        print(f"   {s2.report('contextual')}")
        print("   => the PASS mode is detectable too  OK")
        print("\nE5 SELF-TESTS PASSED (zero API calls)")
        sys.exit(0)

    reps = 2
    for a in sys.argv[1:]:
        if a.startswith("--repeats="):
            reps = int(a.split("=", 1)[1])
    asyncio.run(run(repeats=reps))
