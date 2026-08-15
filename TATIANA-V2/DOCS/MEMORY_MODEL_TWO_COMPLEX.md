# The Two-Complex Memory Model for MOS

**Status:** design specification. Theorems are marked as such; everything else is
proposal. Written in the `.tex`'s claims-and-non-claims register.
**Date:** 2026-07-27
**Supersedes:** the memory schema of `MOS_BOOK.md` §47, and closes finding F10 of
`AUDIT_SCRUTINY_AND_BOOK.md` (the undecided category).

---

## 0. What this fixes

The book's memory schema stated a storage law (`content` = $K_0$ class, `structure` =
$\mathrm{Ext}^1$) in a category it never chose, and both categories it offered fail —
holonomic $\mathcal{D}$-modules make every memory a single indivisible atom, quiver
representations make the content class a bare dimension vector.

The error was trying to make memory **canonical**. Canonicity requires the store to be
a function of the data, which throws away exactly the history that makes it a memory.

This model instead makes memory **two-timescale**: a slow store that is history-
dependent by construction, and a fast working complex that is problem-dependent, with
an explicit, adjoint pair of maps between them. Nothing needs to be canonical. What
needs to be well-defined is the *cycle*.

**Prior art.** This is Complementary Learning Systems (McClelland, McNaughton &
O'Reilly 1995; Kumaran, Hassabis & McClelland 2016), realised sheaf-theoretically.
The design should cite it: independent convergence on a thirty-year-old empirically
forced architecture is evidence, not embarrassment.

---

## 1. Two stratification axes, not one

The `.tex` uses *coarse/fine* for a **scale** distinction: organs vs. concepts. The
new design introduces a **timescale** distinction: crystallized vs. working. These are
orthogonal and must not share vocabulary, or every later statement becomes ambiguous.

| axis | levels | what varies |
|---|---|---|
| **scale** | organ / concept | granularity of a vertex |
| **timescale** | crystallized $\mathbb{K}$ / working $W$ | persistence and update rate |

Both levels of the scale axis exist inside both levels of the timescale axis. The
working complex has its own organs and its own concepts; so does the store.

Notation from here: $\mathbb{K}$ = the crystallized store, $W$ = the working complex.

---

## 2. The objects

> **Definition 2.1 (Crystallized store).** $\mathbb{K} = (\mathcal{C}_\mathbb{K},
> \mathcal{F}_\mathbb{K}, \mathbf{w})$ where $\mathcal{C}_\mathbb{K}$ is a stratified
> simplicial complex, $\mathcal{F}_\mathbb{K}$ a cellular sheaf of finite-dimensional
> real inner-product spaces on it, and $\mathbf{w} : \mathcal{C}_\mathbb{K} \times
> \mathbb{N} \to [0,1]$ the coupling weights.
>
> $\mathbb{K}$ carries **no distinguished section.** It is a space of possible states,
> not a state. This is the formal content of "crystallized": the store holds structure,
> not a current thought.

> **Definition 2.2 (Working complex).** $W = (\mathcal{C}_W, \mathcal{F}_W, s_W)$ with
> $\mathcal{C}_W \subseteq \mathcal{C}_\mathbb{K}$ a **downward-closed** subcomplex and
> $s_W \in C^0(W;\mathcal{F}_W)$ a distinguished 0-cochain — the current state.
>
> $\mathcal{F}_W$ is *initialised from* $\mathcal{F}_\mathbb{K}$ but is not required to
> equal it. The divergence is what the session learns.

Write $\iota : W \hookrightarrow \mathbb{K}$ for the inclusion. Since both are
simplicial complexes and $\mathcal{C}_W$ is downward closed, $\iota$ is an inclusion of
face posets, i.e. a full subposet inclusion.

**Design invariant.** $|\mathcal{C}_W| \ll |\mathcal{C}_\mathbb{K}|$, enforced by a
hard budget. The working complex is RAM; it must fit.

---

## 3. How the two complexes talk: the sheaf adjunctions

This is the precise answer to "there should be a way for both complexes to
communicate." It is not a metaphor and it is not new mathematics — it is the standard
functoriality of cellular sheaves on posets (Curry, *Sheaves, Cosheaves and
Applications*, ch. 4–6).

A cellular sheaf on a complex is a functor from its face poset to $\mathbf{Vect}$. A map
of posets induces three functors between sheaf categories.

> **Theorem 3.1 (standard).** For the poset inclusion $\iota : W \hookrightarrow
> \mathbb{K}$ there are functors
> $$\iota_! \;\dashv\; \iota^* \;\dashv\; \iota_*$$
> where
> - $\iota^*\mathcal{F} = \mathcal{F}\circ\iota$ — **restriction** (pullback);
> - $\iota_!$ = left Kan extension along $\iota$: $(\iota_!\mathcal{G})(\tau) =
>   \operatorname*{colim}_{\sigma\in W,\ \sigma\trianglelefteq\tau}\mathcal{G}(\sigma)$
>   — **extension by zero** (zero on cells with no $W$-face);
> - $\iota_*$ = right Kan extension: $(\iota_*\mathcal{G})(\tau) =
>   \lim_{\sigma\in W,\ \tau\trianglelefteq\sigma}\mathcal{G}(\sigma)$.
>
> Because $\iota$ is a full subposet inclusion, the (co)units are isomorphisms:
> $$\iota^*\iota_! \cong \mathrm{id}, \qquad \iota^*\iota_* \cong \mathrm{id}.$$

**Read cognitively.**

| functor | operation | meaning |
|---|---|---|
| $\iota^*$ | store $\to$ cache | **instantiate**: load the relevant fragment into working memory |
| $\iota_!$ | cache $\to$ store | **write back what was touched, and only that** |
| $\iota_*$ | cache $\to$ store | write back, filling untouched cells by limits from above |

The round-trip identity $\iota^*\iota_! \cong \mathrm{id}$ is the guarantee that
loading a fragment, working on it, and writing it back does not corrupt the fragment.
That is a theorem, not a hope, and it is the reason to use this machinery rather than
ad-hoc copying.

**Which write-back?** Use $\iota_!$. The cache should assert nothing about cells it
never touched, and extension by zero is exactly that discipline. ($\iota_*$ would
silently invent values on untouched cells.) This is the sheaf-theoretic form of the
`.tex`'s $\bot$-invariant: *no measurement is not the same as a measurement of zero.*

> **Claims and non-claims.** Theorem 3.1 is standard category theory and is stated,
> not proved, here. What is *proposed* is the identification of instantiation with
> $\iota^*$ and consolidation with $\iota_!$ followed by the update rule of §6. Note
> also that this is a genuine adjunction, unlike the `.tex`'s $\mathcal{L}\dashv
> \mathcal{M}$, whose triangle identities are explicitly unverified.

---

## 4. The cycle

$$\mathbb{K} \;\xrightarrow{\ \text{(I) instantiate}\ }\; W \;\xrightarrow{\ \text{(II) adapt}\ }\; W' \;\xrightarrow{\ \text{(III) verify}\ }\; W'' \;\xrightarrow{\ \text{(IV) consolidate}\ }\; \mathbb{K}'$$

### (I) Instantiation — building the cache

Given a query $q$, choose a seed set $S \subseteq \mathcal{C}_\mathbb{K}$ and set

$$\mathcal{C}_W \;=\; \overline{\mathrm{St}}^{\,k}(S),$$

the $k$-fold closed star of $S$ — take all cofaces, then all their faces, iterate $k$
times. This is downward closed by construction, so $W$ is a simplicial complex, and it
is the minimal such neighbourhood containing $S$ at radius $k$.

$k$ is the **working-memory radius** and is budget-gated: grow $k$ until the cell
budget is hit. This replaces "retrieve the top-$n$ nearest neighbours" with a
structural query whose result is a *complex*, not a list.

Initialise $\mathcal{F}_W^{(0)} = \iota^*\mathcal{F}_\mathbb{K}$ and $s_W^{(0)}$ from
the query embedding on seed cells, $\bot$ elsewhere.

**Seed selection** is the only approximate step, and it should be the *last* filter,
not the first (per the audit's §47.3 discussion): stratum/support query, then content,
then embedding tiebreak.

### (II) Adaptation — where the sheaf stops being constant

Two things evolve on $W$, at different rates.

**State (fast).** The section descends the discord. With a measured 1-cochain $\eta$
(§5),
$$\dot s_W \;=\; -(\delta^0_W)^\top\big(\delta^0_W s_W - \eta\big).$$

**Restriction maps (slower).** Local predictive-coding update, already implemented in
`python/predictive_coding.py`:
$$\Delta R_{u,e} \;=\; -\eta_{\text{lr}}\,\pi_e\,\varepsilon_e\,x_u^\top,
\qquad R \leftarrow \Pi_{O(d)}(R + \Delta R)$$
with $\Pi_{O(d)}$ the polar retraction (SVD, $R \mapsto UV^\top$).

**This is the answer to "adapted to the current problem."** The store's maps say how
two concepts relate *in general*. The cache's maps, after adaptation, say how they
relate *in this problem*. The session's learning is precisely

$$\Delta R \;:=\; R^W - \iota^*R^\mathbb{K}.$$

**Orthogonality is not optional.** By finding F2 of the audit, the Anderson–Morley
bound — and hence $\rho\in[0,1]$ — requires $\|R_{v\trianglelefteq e}\|\le 1$.
Restricting to $O(d)$ guarantees it. `coherence.py` already warns rather than clamps
when this is violated; keep that behaviour.

### (III) Verification

$\nu : \mathcal{C}_W \to \{\textsf{Verified}, \textsf{Unverifiable},
\textsf{Refuted}\}$, assigned by the external oracle.

With Lean in the loop the pipeline is: a **neural moderator** (the $\mathcal{L}$ lift)
turns a candidate claim into a Lean proposition plus proof attempt; Lean's kernel
type-checks it; the trichotomy is *type-checks* / *refuted or contradiction found* /
*timeout, or not formalisable*.

> **Honest limit.** Most of what MOS handles will not be Lean-formalisable, so
> \textsf{Unverifiable} will be the common verdict. The architecture must not treat
> that as failure — the `.tex` already gets this right ($\Omega$ untouched on
> \textsf{Unverifiable}), and that discipline is load-bearing here.

$\nu$ is a **third filtration parameter** alongside time and weight. Note the
consequence, stated so nobody hopes otherwise: three filtration parameters means
multiparameter persistence, and **there is no barcode** (Carlsson–Zomorodian 2009).
Use fibered barcodes along fixed slices (e.g. hold $\nu = $ \textsf{Verified}, vary
weight and time). Anyone offering a multiparameter barcode is selling something.

### (IV) Consolidation — crystallization

Three things write back, and they write back differently.

**(a) New cells.** Concepts and coalitions created during the session are added to
$\mathcal{C}_\mathbb{K}$ via $\iota_!$. Gated on $\nu \neq$ \textsf{Refuted}.

**(b) Restriction maps — the CLS transfer rule.** For each incidence in $W$:

$$\boxed{\ R^\mathbb{K}_{\sigma\trianglelefteq\tau} \;\longleftarrow\; \Pi_{O(d)}\Big(R^\mathbb{K}_{\sigma\trianglelefteq\tau} \;+\; \gamma(\nu)\,\big(R^W_{\sigma\trianglelefteq\tau} - R^\mathbb{K}_{\sigma\trianglelefteq\tau}\big)\Big)\ }$$

with consolidation rate

$$\gamma(\nu) = \begin{cases}\gamma_0 & \nu = \textsf{Verified}\\ \epsilon\gamma_0 & \nu = \textsf{Unverifiable}\\ 0 & \nu = \textsf{Refuted}.\end{cases}$$

**This one formula carries the whole CLS story.** $\gamma_0 \ll 1$ is slow neocortical
learning: one session cannot overwrite the store, which is exactly the protection
against catastrophic interference that CLS exists to provide. $\gamma_0 = 1$ is
overwrite — catastrophic by construction. $\gamma_0 = 0$ is a system that cannot learn.
And $\gamma$ gated on $\nu$ is the project's own principle — *truth gates
consolidation* — made into a coefficient.

For small $\gamma$ the convex-combination-plus-retraction is a first-order approximation
to geodesic interpolation on $O(d)$; use the exact geodesic only if it is ever shown to
matter.

**(c) Weights.** Hebbian update on $\mathbf{w}$ for coalitions co-active in the
session. This is what "molds the bigger complex" means concretely: the store's *shape*
changes, not just its data, because weights crossing the bind threshold create edges
and weights decaying below it collapse them.

**What is deliberately NOT written back: $s_W$.** The session's particular state is
discarded. This is crystallization in the precise sense: **content and wiring persist,
the episode does not.** It is the associated-graded operation of the book's §32 in the
only form that survives the category problem — no $K_0$, no $\mathrm{Ext}$, just "keep
the structure, drop the section."

Testable prediction, inherited from CLS: a correctly consolidated MOS should retain
*what it knows* and lose *the particular reasoning path it took*. If it loses facts
instead, this is not what is being implemented.

---

## 5. How topology molds the gradient descent

This is the constitutive move — the sheaf stops scoring the computation and starts
shaping it. Three mechanisms, all rigorous, all cheap.

**Prerequisite:** a genuinely *measured* 1-cochain $\eta \in C^1(W;\mathcal{F}_W)$ —
pairwise judgements emitted by organs, **not** $\delta$ of any global assignment. This
is forced: by Proposition 8.2 of the book, $[\delta s] = 0$ in $H^1$ unconditionally,
so a derived cochain carries no obstruction and cannot aim anything.

Hodge decomposition on $W$ (Lim; Jiang–Lim–Yao–Ye):
$$\eta \;=\; \underbrace{\eta_G}_{\in\,\operatorname{im}\delta^0} \;\oplus\; \underbrace{\eta_H}_{\in\,\ker\Delta_1} \;\oplus\; \underbrace{\eta_C}_{\in\,\operatorname{im}(\delta^1)^\top}.$$

### 5.1 The irreducible discord — a stopping rule computable before flowing

> **Proposition 5.1.** The flow $\dot s = -(\delta^0)^\top(\delta^0 s - \eta)$
> converges to $s^\star = (\delta^0)^+\eta$, and
> $$\lim_{t\to\infty}\|\delta^0 s(t) - \eta\|^2 \;=\; \|\eta_H\|^2 + \|\eta_C\|^2 \;=:\; \Phi_\infty.$$
>
> *Proof.* The flow is gradient descent on $\tfrac12\|\delta^0 s - \eta\|^2$, a convex
> quadratic; it converges to the least-squares solution $s^\star=(\delta^0)^+\eta$, at
> which $\delta^0 s^\star = P_{\operatorname{im}\delta^0}\eta = \eta_G$. The residual is
> $\|\eta - \eta_G\|^2$, which by orthogonality of the Hodge summands is
> $\|\eta_H\|^2+\|\eta_C\|^2$. $\blacksquare$

**Why this matters.** $\Phi_\infty$ is computable by two least-squares solves
**before running the flow at all.** So the system can ask, in advance: *how much of
this disagreement is even fixable by reconciliation?*

Control rule:
$$\text{if } \frac{\Phi_\infty}{\|\eta\|^2} > \theta \quad\Longrightarrow\quad \textbf{do not flow. Grow.}$$

That is homology molding the descent in the strict sense: a topological computation
decides whether the dynamics runs.

### 5.2 Typed remediation

$\eta_C \ne 0$ — inconsistency closing around a **filled** triangle. Locally
identifiable, locally repairable: one 2-simplex is wrong. Repair, do not grow.

$\eta_H \ne 0$ — inconsistency closing around an **unfilled** 1-cycle. Not locally
repairable by any choice of state. **This is the growth signal**, and $\eta_H$ is
supported on specific edges, so it is *the address*.

This is the mechanism the logbook §5p asks for ("the obstruction cocycle names the cell
to attach") and which Proposition 8.2 shows is unreachable from $\delta s$. The
harmonic component is the object that actually has an address.

### 5.3 $b_1$ bounds the growth budget

> **Proposition 5.2.** $\ker\Delta_1 \cong H^1(W;\mathcal{F}_W)$, so the number of
> independent obstruction classes is $\dim H^1$. Attaching a 2-cell along a cycle
> reduces $\dim H^1$ by at most 1. Hence **at most $\dim H^1(W;\mathcal{F}_W)$ cell
> attachments suffice to make $W$ fully reconcilable.** For the constant sheaf,
> $\dim H^1 = b_1(W)\cdot d$.

So $b_1$ is not decoration: it is an *a priori bound on how much structure the system
must grow* before the current problem becomes solvable by reconciliation alone. That is
a budget, computed from shape, before any LLM call is spent.

> **Claims and non-claims.** Propositions 5.1 and 5.2 are proved/standard. That the
> resulting control rule *improves outcomes* is a proposal and is the content of
> experiment E5.

---

## 6. Why the sheaf is no longer constant — and how to measure that

Three independent sources of non-trivial restriction maps, in increasing order of value:

1. **Learned by predictive coding** on $W$ (§4-II), consolidated to $\mathbb{K}$ (§4-IV-b).
   *Already implemented in Python; not yet engine-wired.*
2. **Dispersion stalks.** Summarise an organ by the top-$k$ eigenspace of its concept
   cloud's second moment, not its centroid. The centroid collapses toward the encoder's
   anisotropy centre; the second moment does not. Restriction maps become principal-angle
   alignments. (Book §10; genuinely good and independent of everything above.)
3. **The store/cache split itself.** Even initialised at identity, $R^W$ and
   $R^\mathbb{K}$ diverge under adaptation. *The divergence is the content of the
   session.*

### A second LLM-independent learning metric

$$\boxed{\ \mathcal{Q}(t) \;=\; \frac{1}{|E_\mathbb{K}|}\sum_{e}\big\|R^\mathbb{K}_{e}(t) - I\big\|_F^2\ }$$

The constant sheaf is $\mathcal{Q}=0$: *every concept means the same thing in every
context*, i.e. nothing has been learned about the wiring. Departure from constancy is
accumulated relational knowledge, and **the LLM contributes nothing to it directly**
— it is produced by the local update rule.

$\mathcal{Q}(t)$ is therefore a second falsification instrument alongside the workload
compression curve $\Lambda(t)$. If $\mathcal{Q}$ stays at zero, the system is not
learning structure, whatever else it is doing. Cost: a log.

---

## 7. Day-one degradation

Following the `.tex`'s own slope-not-intercept discipline. With
$$k=1,\quad R \equiv I,\quad \gamma_0 = 0,\quad \eta := \delta s,\quad \theta = \infty,$$
the model degrades **exactly** to current MOS behaviour: identity restrictions,
constant sheaf, no consolidation, derived cochain, always flow. Every mechanism is a
slope mechanism. Nothing visibly changes on day one, deliberately.

---

## 8. Implementation order

| # | item | cost | unlocks |
|---|---|---|---|
| 1 | Split $\mathbb{K}$ / $W$ as distinct objects; $\iota^*$ instantiation | moderate | everything below |
| 2 | Log $\mathcal{Q}(t)$ | a log | the second learning metric — do immediately |
| 3 | Measured $\eta$ pilot on one filled triangle (E5) | 3 LLM calls | §5 entirely; the growth signal |
| 4 | $\Phi_\infty$ stopping rule | 2 least-squares solves | flow/grow decision |
| 5 | Consolidation rule with $\gamma(\nu)$ | small | crystallization; CLS |
| 6 | Engine-wire the PC learner (exists in Python) | moderate | non-constant sheaf in the store |
| 7 | Dispersion stalks | moderate | non-constant sheaf independent of learning |
| 8 | Lean moderator | large | genuine $\nu$; do last |

**Item 3 is the gate.** If the measured $\eta$ turns out to be pure gradient on real
content — no curl, no harmonic mass — then §5 has nothing to act on and the
cohomological growth story needs rethinking. Better to learn that from three LLM calls
than from a month of engineering.

---

## 9. What is not claimed

- Nothing here raises the LLM's per-call reasoning quality. As always, the bet is
  on accumulation.
- $\Phi_\infty$ says how much discord is *irreducible by reconciliation*. It says
  nothing about which organ is right. VerifyOp remains the sole arbiter of truth.
- The adjunction of Theorem 3.1 guarantees the load/work/store round trip is faithful.
  It guarantees nothing about whether what is stored is *worth* storing; that is
  $\gamma(\nu)$'s job, and $\gamma$'s dependence on $\nu$ is only as good as the oracle.
- $\mathcal{Q}(t) > 0$ means the wiring has changed. It does not mean the wiring has
  improved. Pair it with $\Lambda(t)$, which is workload-grounded.
- No barcode exists for the three-parameter filtration (time, weight, $\nu$). This is a
  theorem, not a gap in the literature.
- The category question (audit F10) is **dissolved, not answered.** This model does not
  require memories to have canonical atoms, so it does not need Jordan–Hölder, $K_0$, or
  $\mathrm{Ext}^1$. If canonical atoms are wanted later for some other purpose, the
  question returns unchanged.
