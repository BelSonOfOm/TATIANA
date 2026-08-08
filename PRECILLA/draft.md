# §0 VERDICT

The optimal framework is a **stochastic dynamical system on ℝᴺ × ℝᵈ** (activation × context), with the edge matrix W derived as the minimiser of a variational free energy F_MOS, the temporal component of W structured as the successor representation, and a sheaf on the Alexandrov topology of the directed reachability preorder as the auxiliary structure for topological reading. The dynamics, not the geometry, produce the assemblies; the free energy, not the modeller, sets the weights; the inhibition, not a constant, sets the width. **The single strongest objection:** the semantic term w₁·S remains in W as a prior, so if the free energy minimum places large weight on w₁, the emergent topology is the embedding's topology restated. The formalism does not structurally prevent this — the validation battery does. The formalism's contribution is making the circularity *visible* (five separated, learned terms) rather than hiding it in a single metric.

# §1 SURVEY

| Framework | Buys | Costs here | Verdict |
|---|---|---|---|
| **Stochastic dynamical system on ℝᴺ** | Natural tick loop; competition and emergence are native; O(N²) per tick; lag-CRP is a dynamical consequence | State space is continuous, assemblies are thresholded subsets (discontinuous projection); alone it has no principled source for W | **PRIMARY** |
| Random dynamical system / Markov chain on 2^V | Assemblies are the state; transitions are the dynamics | 2^1074 states — computationally dead on arrival; loses graded activation that drives competition | **REJECTED**: intractable |
| Energy-based (Hopfield / modern Hopfield) | Attractors = assemblies; modern Hopfield = attention = softmax; clean fixed-point theory | Hopfield energy requires symmetric W — w₃ breaks it; if you write the energy with K basins you find K clusters (the circularity trap, §2) | **REJECTED**: cannot represent directed edges; would encode the answer |
| Information geometry / variational free energy | Hooks existing F_MOS; principled derivation of all five weights from one objective; predictive term is native | Requires a generative model p(x,z) and recognition model q(z|x) — extra structure; alone it gives the objective, not the dynamics | **AUXILIARY**: provides the learning objective for W |
| Successor representation M = (I − γT)⁻¹ | Temporal edge w₃ is native; learnable online by TD; known relationship to place/grid structure; gives forward asymmetry for free | It is a representation of expected occupancy, not a dynamics — no competition, no context, no assembly formation | **AUXILIARY**: provides the structure of the temporal edge |
| Sheaf / cellular sheaf over contexts | Existing ι! ⊣ ι* ⊣ ι_* connects; contexts as base space; cohomology for topology | Standard sheaf cohomology needs symmetric neighbourhoods — w₃ breaks this; gives static structure, not dynamics | **AUXILIARY** (reformulated): Alexandrov topology on directed preorder |
| Directed graph / quiver representation | Directed edges native; path algebra gives reachability; well-studied cohomology | No dynamics, no competition, no emergence; quiver cohomology is less connected to the cover/partition questions | **ABSORBED into the sheaf auxiliary**: sheaf on Alexandrov topology = quiver representation |

**What each rejected framework would have bought:**
- *Markov chain on 2^V*: a clean transition kernel P(A(t+1) | A(t)) and exact stationary distribution. We lose this; we approximate it with the continuous dynamics + threshold.
- *Hopfield*: a Lyapunov function and convergence guarantees. We lose this; the directed W means no global energy function in the Hopfield sense. The free energy F_MOS is not a Lyapunov function for the activation dynamics — it is the learning objective.
- *Pure quiver*: path algebra cohomology, which is cleaner than Alexandrov sheaf cohomology. We absorb this: sheaves on Alexandrov spaces *are* quiver representations, so we keep the cohomology and gain the adjunction.

# §2 OBJECTS

**Concept set.** V = {1, …, N}, N ≈ 1074. `[ENGINEERING CHOICE]`

**State space.** 𝒮 = ℝᴺ × ℝᵈ × ℝᴺ × ℝᴺ × (2ⱽ)ᴸ × ℝᵈᵍ, with elements (a, c, φ, B, WM, g):
- a ∈ ℝᴺ: activation, nonneg. The assembly is A(t) = {i : a_i(t) > θ}, θ = ½.
- c ∈ ℝᵈ: context vector, ‖c‖ = 1, d ≪ N (d ≈ 100). `[ENGINEERING CHOICE]`
- φ ∈ ℝᴺ: fatigue (nonneg).
- B ∈ ℝᴺ: base-level strength.
- WM ∈ (2ⱽ)ᴸ: ordered buffer of L recent assemblies.
- g ∈ ℝᵈᵍ: goal/task vector.

**Edge matrix.** W ∈ ℝᴺˣᴺ, asymmetric. W = Σ₅ₖ₌₁ wₖ Mₖ where:
- M₁(i,j) = cos(v_i, v_j): semantic, fixed from abtt embeddings. `[MEASURED]`
- M₂(i,j): episodic, Hebbian co-activation count, learned online.
- M₃(i,j) = [(I − γT)⁻¹]ᵢⱼ: temporal successor representation, learned by TD. `[DERIVED]` from Dayan (1993).
- M₄(i,j): predictive, derived from F_MOS.
- M₅(i,j): task, goal-conditioned co-relevance.

**Inhibition.** λ > 0, global competition strength. The single parameter that replaces k = 24.

**Measure.** Standard Lebesgue on ℝᴺ × ℝᵈ × ℝᴺ × ℝᴺ × ℝᵈᵍ; counting measure on (2ⱽ)ᴸ.

**Tick.** A tick is a map Tₜ: 𝒮 × ℝᴺ → 𝒮, (sₜ₋₁, xₜ) ↦ sₜ. It is a deterministic morphism composed of: cue formation → inner activation loop → assembly formation → state update. Stochasticity enters through xₜ (external input, possibly empty) and through σ noise if added.

# §3 DYNAMICS

**EQ-1 (Cue formation).** The cue qₜ ∈ ℝᴺ blends external input, context, and goal:

$$q_t = \alpha \, x_t + \beta \, c_{t-1} + \gamma_g \, g_t$$

where α, β, γ_g are precision-weighted mixing coefficients (see §4 for derivation from F_MOS).

**EQ-2 (Activation spread, inner loop).** For inner step k = 0, …, K−1 (K ≈ 3–5):

$$a^{(k+1)} = \sigma\!\left(W \, a^{(k)} + q_t + B - \lambda \, (\mathbf{1}^\top a^{(k)}) \, \mathbf{1}_N - \phi_{t-1}\right)$$

with a⁽⁰⁾ = a_{t−1} (persistence) or 0 (cold start), and σ the logistic sigmoid.

**EQ-3 (Assembly).** After K inner steps:

$$A(t) = \{i \in V : a_i^{(K)} > \theta\}, \quad \theta = \tfrac{1}{2}$$

**EQ-4 (Context update).**

$$c_t = \frac{\rho \, c_{t-1} + \beta_c \, f(A(t))}{\|\rho \, c_{t-1} + \beta_c \, f(A(t))\|}$$

where f(A) = |A|⁻¹ Σ_{i∈A} v_i is the assembly centroid.

**EQ-5 (Fatigue).**

$$\phi_t = \kappa \, \phi_{t-1} + a_t$$

**EQ-6 (Base-level).**

$$B_i(t) = \ln\!\left(\sum_{k} (t - t_{i,k})^{-d}\right)$$

where t_{i,k} are past activation times of concept i, d > 0 the decay exponent.

**EQ-7 (Working memory).**

$$\text{WM}_t = \text{push}(A(t), \, \text{evict}_{\text{oldest}}(\text{WM}_{t-1}, L))$$

**EQ-8 (Edge weight learning).** The five scalar weights w₁,…,w₅ are updated by gradient descent on F_MOS:

$$w_k \leftarrow w_k - \eta_k \sum_{i,j} \frac{\partial F_{\text{MOS}}}{\partial W_{ij}} \, M_k(i,j)$$

**EQ-9 (Episodic edge update).**

$$M_2(i,j) \leftarrow (1 - \zeta) \, M_2(i,j) + \eta_H \, a_i(t) \, a_j(t)$$

**EQ-10 (Temporal edge update, TD for SR).** When concept i is active at t and j at t+1:

$$M_3(i, \cdot) \leftarrow M_3(i, \cdot) + \eta_{\text{TD}} \left[\mathbf{e}_i + \gamma \, M_3(j, \cdot) - M_3(i, \cdot)\right]$$

**EQ-11 (Predictive edge).**

$$M_4(i,j) = \log \frac{p(i,j)}{p(i)\,p(j)} = \log p(j \mid i) - \log p(j)$$

estimated online from co-activation counts. This is the pointwise mutual information, which is the predictive component of F_MOS (see §4).

**EQ-12 (Task edge).**

$$M_5(i,j) = \mathbf{1}[g^\top v_i > \tau_g \;\wedge\; g^\top v_j > \tau_g]$$

for goal g and threshold τ_g. `[ENGINEERING CHOICE]` on the threshold form; the weight w₅ is still learned.

# §4 DERIVATIONS

### D1. Successor representation of a forward chain is upper-triangular

`[DERIVED]` For a deterministic forward chain with T(i, i+1) = 1, the successor representation M = (I − γT)⁻¹ has M(i,j) = γ^{j−i} for j ≥ i and M(i,j) = 0 for j < i. This is the source of the temporal asymmetry.

```python
# EQ-10 / D1: SR of a 3-node forward chain
from sympy import Matrix, symbols, eye, simplify

gamma = symbols('gamma')
T = Matrix([[0, 1, 0],
            [0, 0, 1],
            [0, 0, 0]])
I3 = eye(3)
M = (I3 - gamma * T).inv()
expected = Matrix([[1, gamma, gamma**2],
                  [0, 1, gamma],
                  [0, 0, 1]])
assert simplify(M - expected) == Matrix.zeros(3, 3)
```

### D2. Free-energy gradient gives the edge-weight learning rule

`[DERIVED]` The variational free energy, in the mean-field (point-estimate) approximation where q(A(t)) = δ(A(t) − Â(t)), reduces to the negative log-likelihood of the observed transition:

$$F_{\text{MOS}} \approx -\log p(\hat{A}(t) \mid \hat{A}(t-1)) - \log p(x_t \mid \hat{A}(t))$$

The transition model is logistic: p(j ∈ A(t) | A(t−1)) = σ(h_j) where h_j = Σ_{i∈A(t−1)} W_{ij} + B_j + q_{t,j} − λS − φ_j. The gradient of the transition log-likelihood with respect to W_{ij} is:

$$\frac{\partial F_{\text{MOS}}}{\partial W_{ij}} = -a_i(t{-}1) \cdot \left(y_j - \sigma(h_j)\right)$$

where y_j = 𝟏[j ∈ Â(t)]. This is the standard logistic regression gradient. The learning rule EQ-8 projects this gradient onto each basis matrix M_k.

```python
# D2: Free-energy gradient = logistic gradient
from sympy import symbols, simplify, diff, log, exp

W_ij, a_i, b_j = symbols('W_ij a_i b_j')
h_j = W_ij * a_i + b_j
sig = 1 / (1 + exp(-h_j))

# Case y_j = 1 (j is in assembly): loss = -log(sig)
L_active = -log(sig)
grad_active = diff(L_active, W_ij)
expected_active = -a_i * (1 - sig)
assert simplify(grad_active - expected_active) == 0

# Case y_j = 0 (j not in assembly): loss = -log(1 - sig)
L_inactive = -log(1 - sig)
grad_inactive = diff(L_inactive, W_ij)
expected_inactive = a_i * sig
assert simplify(grad_inactive - expected_inactive) == 0

# Combined: dF/dW_ij = -a_i * (y_j - sig(h_j))
# y_j=1: -a_i*(1-sig) = grad_active  ✓
# y_j=0: -a_i*(0-sig) = a_i*sig = grad_inactive  ✓
```

### D3. The predictive term M₄ is the mutual information, which is part of F_MOS

`[DERIVED]` The predictive component of the free energy is the expected log-likelihood of the transition. The pointwise mutual information PMI(i,j) = log p(j|i) − log p(j) measures how much i reduces surprise about j. In the free energy:

$$F_{\text{MOS}} \supset -\mathbb{E}_q[\log p(j \in A(t) \mid i \in A(t{-}1))]$$

The optimal predictive edge weight satisfies ∂F_MOS/∂M₄(i,j) = 0, which gives M₄(i,j) ∝ PMI(i,j). The coupling is direct: M₄ is not a parallel objective — it is the transition log-likelihood component of the same F_MOS that drives all five weights.

### D4. Assembly size emerges from the self-consistency equation

`[DERIVED]` At the inner-loop fixed point, the total activation S = Σ_i a_i satisfies:

$$S = \sum_{i=1}^{N} \sigma(h_i - \lambda S)$$

where h_i = (W·a)_i + q_i + B_i − φ_i is the pre-inhibition activation. In the high-gain limit (σ → step function), and with h_i ~ N(μ, σ_h²) i.i.d. (mean-field approximation):

$$S = N \cdot P(h > \lambda S) = N \left(1 - \Phi\!\left(\frac{\lambda S - \mu}{\sigma_h}\right)\right)$$

Setting k* = S (each active concept contributes ≈1 in the step limit):

$$k^* = N \left(1 - \Phi\!\left(\frac{\lambda k^* - \mu}{\sigma_h}\right)\right)$$

Rearranging:

$$\lambda k^* = \mu + \sigma_h \, \Phi^{-1}\!\left(1 - \frac{k^*}{N}\right)$$

This is the fixed-point equation. Assembly width is a function of λ, μ, σ_h, N — not a hand-set constant.

```python
# D4: Assembly size fixed point — algebraic rearrangement
from sympy import symbols, sqrt, erfinv, erf, simplify

k, lam, mu, sigma_h, N = symbols('k lambda mu sigma_h N', positive=True)

# Phi(x) = (1 + erf(x/sqrt(2)))/2
# Self-consistency: k = N * (1 - Phi((lam*k - mu)/sigma_h))
# => k/N = 1 - (1 + erf(z))/2  where z = (lam*k - mu)/(sigma_h*sqrt(2))
# => erf(z) = 1 - 2*k/N
# => z = erfinv(1 - 2*k/N)
# => lam*k = mu + sigma_h * sqrt(2) * erfinv(1 - 2*k/N)

z = (lam * k - mu) / (sigma_h * sqrt(2))
# Verify: substituting z = erfinv(1 - 2k/N) into the self-consistency equation
z_solved = erfinv(1 - 2*k/N)
# Phi(z_solved) = (1 + erf(erfinv(1 - 2k/N)))/2 = (1 + (1 - 2k/N))/2 = 1 - k/N
phi_at_solution = (1 + erf(z_solved)) / 2
# So N * (1 - phi_at_solution) = N * (1 - (1 - k/N)) = N * k/N = k
self_consistency_check = N * (1 - phi_at_solution)
assert simplify(self_consistency_check - k) == 0
```

### D5. Stability of the assembly-size fixed point

`[DERIVED]` The fixed point k* = f(k*) where f(k) = N(1 − Φ((λk − μ)/σ_h)) is stable when |f'(k*)| < 1:

$$f'(k) = -\frac{N \lambda}{\sigma_h} \, \varphi\!\left(\frac{\lambda k - \mu}{\sigma_h}\right)$$

where φ is the standard normal PDF. Stability requires:

$$\frac{N \lambda}{\sigma_h} \, \varphi(z^*) < 1, \quad z^* = \frac{\lambda k^* - \mu}{\sigma_h}$$

Since φ(z) ≤ 1/√(2π), a sufficient condition is:

$$\lambda < \frac{\sigma_h \sqrt{2\pi}}{N}$$

This is an *upper* bound: too much inhibition destabilises the competition (all concepts flip on/off together). The assembly size is stable in an intermediate range of λ — large enough to produce small assemblies, small enough to avoid bistability.

```python
# D5: Stability condition — derivative of the fixed-point map
from sympy import symbols, sqrt, pi, exp, simplify, diff, erf

k, lam, mu, sigma_h, N = symbols('k lambda mu sigma_h N', positive=True)

# f(k) = N * (1 - Phi((lam*k - mu)/sigma_h))
# Phi(x) = (1 + erf(x/sqrt(2)))/2
z = (lam * k - mu) / sigma_h
Phi_z = (1 + erf(z / sqrt(2))) / 2
f_k = N * (1 - Phi_z)

# f'(k) = d/dk [N * (1 - Phi(z))]
# = N * (-phi(z)) * dz/dk  where phi(z) = exp(-z^2/2)/sqrt(2*pi)
# = N * (-exp(-z^2/2)/sqrt(2*pi)) * (lam/sigma_h)
# = -N*lam/sigma_h * exp(-z^2/2)/sqrt(2*pi)

f_prime = diff(f_k, k)
# The derivative should be -N*lam/sigma_h * exp(-z^2/2) / sqrt(2*pi)
expected_f_prime = -N * lam / sigma_h * exp(-z**2 / 2) / sqrt(2 * pi)
assert simplify(f_prime - expected_f_prime) == 0

# Stability: |f'(k*)| < 1
# N*lam/sigma_h * exp(-z*^2/2) / sqrt(2*pi) < 1
# Sufficient (since exp(-z^2/2) <= 1):
# N*lam / (sigma_h * sqrt(2*pi)) < 1
# => lam < sigma_h * sqrt(2*pi) / N
```

### D6. Lag-CRP forward asymmetry from SR asymmetry

`[DERIVED]` After recalling item at position i, the probability of next recalling j is proportional to exp(a_j(t+1)), where:

$$a_j(t{+}1) \propto \sigma\!\left(\sum_i W_{ij} \, a_i(t) + \beta \, c_t \cdot v_j + \cdots\right)$$

The temporal component of W_{ij} is w₃ · M₃(i,j). For a forward chain (D1), M₃(i, i+ℓ) = γ^ℓ and M₃(i, i−ℓ) = 0. The context component c_t · v_j is approximately symmetric in ℓ (context is a recency-weighted sum of item vectors; items at equal distances contribute equally). The semantic component is approximately symmetric. So:

$$\frac{P(+\ell \mid i)}{P(-\ell \mid i)} \propto \exp\!\left(w_3 \, \gamma^\ell \, a_i \right) > 1$$

The forward asymmetry is a direct consequence of the SR's upper-triangular structure. The decay with |ℓ| comes from γ^ℓ (temporal) and ρ^ℓ (context drift). The peak at |ℓ| = 1 comes from both terms being maximised at ℓ = 1.

```python
# D6: Lag-CRP forward asymmetry ratio
from sympy import symbols, exp, simplify

w3, a_i, ell, gamma = symbols('w3 a_i ell gamma', positive=True)

# Forward temporal contribution: w3 * gamma^ell * a_i (M3(i,i+ell) = gamma^ell)
# Backward temporal contribution: 0 (M3(i,i-ell) = 0 for forward chain)
forward_temporal = w3 * gamma**ell * a_i
backward_temporal = 0

# Context and semantic contributions are approximately symmetric:
# c_t . v_{i+ell} ≈ c_t . v_{i-ell}  (by symmetry of recency weighting)
# S(i, i+ell) ≈ S(i, i-ell)  (by approximate symmetry of cosine at equal distance)
symmetric_contribution = 0  # cancels in the ratio

# Log ratio = forward_temporal - backward_temporal + symmetric (cancels)
log_ratio = forward_temporal - backward_temporal + symmetric_contribution
ratio = exp(log_ratio)

# The ratio is exp(w3 * gamma^ell * a_i) > 1 for w3 > 0
assert simplify(ratio - exp(w3 * gamma**ell * a_i)) == 0
# This is strictly > 1 when w3 > 0, gamma > 0, a_i > 0, ell > 0
```

### D7. Mixing coefficients from free energy

`[DERIVED]` The cue qₜ = αxₜ + βc_{t−1} + γ_g gₜ is the posterior mean of the input under a Gaussian generative model with three sources. The optimal mixing weights are precision-weighted:

$$\alpha = \frac{\pi_x}{\pi_x + \pi_c + \pi_g}, \quad \beta = \frac{\pi_c}{\pi_x + \pi_c + \pi_g}, \quad \gamma_g = \frac{\pi_g}{\pi_x + \pi_c + \pi_g}$$

where π_x, π_c, π_g are the precisions (inverse variances) of each source. These are parameters of F_MOS and are learned alongside W. `[CITATION NEEDED: Friston active inference precision weighting]`

# §5 EMERGENCE

**The fixed point.** Assembly width k* satisfies (D4):

$$\lambda k^* = \mu + \sigma_h \, \Phi^{-1}\!\left(1 - \frac{k^*}{N}\right)$$

where μ, σ_h are the mean and standard deviation of pre-inhibition activations h_i across concepts. This is an implicit equation — k* is not closed-form but is uniquely determined given λ, μ, σ_h, N in the stable regime.

**k* as a function of λ.** Differentiating the fixed-point equation:

$$\frac{dk^*}{d\lambda} = -\frac{k^*}{\lambda + \frac{\sigma_h}{N \, \varphi(z^*)}}$$

where z* = (λk* − μ)/σ_h. This is negative: increasing λ decreases k*. The assembly shrinks as inhibition strengthens. `[DERIVED]`

**Stability.** The fixed point is stable when (D5):

$$\frac{N \lambda}{\sigma_h} \, \varphi(z^*) < 1$$

For N = 1074, σ_h ≈ 1, this gives λ < √(2π)/1074 ≈ 0.0023 as a *sufficient* condition. In practice, φ(z*) ≪ 1/√(2π) because most concepts are far from threshold, so the stable range is much wider. `[INFERRED]`

**What this deletes.** The hand-set k = 24 is replaced by k*(λ, μ, σ_h, N). The model has one fewer hand-set constant. If the validation battery (§6) constrains λ, then k* is determined — it is not a free parameter. This is the A17 test: the variable λ *changes a number* (assembly size) *that no other variable changes*, and it *deletes a decision* (k = 24).

# §6 LAG-CRP

**Setup.** A list of L items is presented sequentially. Each presentation activates the corresponding concept and updates the context. After presentation, free recall is simulated by running the tick loop with xₜ = ∅. The lag-CRP is the conditional probability P(next recall at position j | current recall at position i), plotted as a function of lag = j − i.

**Derivation sketch.**

1. **Context encodes temporal position.** During study, cₜ = ρc_{t−1} + β_c v_{item(t)}. After L items, c_L = Σₖ ρ^{L−k} β_c v_k — a recency-weighted sum. Items at adjacent positions have similar context vectors. `[DERIVED]` This is the TCM mechanism. `[CITATION NEEDED: Howard & Kahana temporal context model]`

2. **Retrieval is cued by context.** At recall, a_j ∝ σ(β cₜ · v_j + …). The context term cₜ · v_j is maximised for items near the currently-recalled item's temporal position, giving the peak at |lag| = 1. `[DERIVED]`

3. **The temporal edge w₃ breaks the symmetry.** The activation spread includes w₃ M₃(i,j) a_i. For a forward chain, M₃(i, i+ℓ) = γ^ℓ > 0 and M₃(i, i−ℓ) = 0 (D1). So forward neighbours receive temporal activation that backward neighbours do not. `[DERIVED]`

4. **The ratio.** Combining the symmetric context/semantic contributions (which cancel in the ratio) with the asymmetric temporal contribution (D6):

$$\frac{P(+\ell)}{P(-\ell)} = \exp\!\left(w_3 \, \gamma^\ell \, a_i\right) > 1$$

This gives: (a) peaked at |lag| = 1 (from context), (b) decaying with |lag| (from γ^ℓ and ρ^ℓ), (c) forward asymmetry (from M₃). All three features of the empirical lag-CRP are derivable consequences. `[DERIVED]`

5. **What produces each feature.**

| Feature | Source | Ablation prediction |
|---|---|---|
| Peak at \|lag\| = 1 | Context drift (ρ) | Remove c → peak disappears |
| Decay with \|lag\| | γ^ℓ (temporal) + ρ^ℓ (context) | Remove w₃ → decay slows, becomes symmetric |
| Forward asymmetry | SR asymmetry M₃(i,j) ≠ M₃(j,i) | Remove w₃ → asymmetry vanishes |

**If the framework cannot produce this**, it fails the G1 gate and the architecture is wrong. The derivation above shows it can, *provided* the SR is learned on a forward sequence. The open question is whether MOS's concept representation supports a context vector that drifts coherently — this is the G1 hypothesis. `[OPEN HYPOTHESIS]`

# §7 CONSTRAINTS MET

1. **Circularity.** The framework makes it structurally impossible to recover topology requiring co-activation of concepts that are never simultaneously reachable by the dynamics. It does *not* structurally prevent recovering the embedding's topology — if w₁ dominates, the topology is the embedding's. The formalism makes this *visible* (five separated, learned terms) rather than hidden. The validation battery, not the formalism, is the escape.

2. **State variables.** a → assembly (nothing else determines it). c → lag-CRP (nothing else produces temporal contiguity). WM → recency + capacity (nothing else limits buffer size). φ → prevents sticking (without it, the model stays in one attractor; ablation changes the dynamics). B → spacing effect (nothing else produces power-law retention). g → source clustering (nothing else produces task-conditioned recall). λ → assembly size (nothing else sets width; deletes k = 24). All seven earn their place.

3. **Assembly size.** k* = N(1 − Φ((λk* − μ)/σ_h)), derived in D4, stable in D5. No hand-set k.

4. **Edge weights.** W = Σ wₖ Mₖ, wₖ learned by ∂F_MOS/∂wₖ = 0 (EQ-8, D2). M₂ by Hebbian (EQ-9), M₃ by TD (EQ-10), M₄ = PMI from F_MOS (D3, EQ-11). No hand-set weights.

5. **Directed edges.** w₃ (SR) makes W asymmetric. This breaks: (a) symmetric sheaf cohomology (standard neighbourhoods are symmetric), (b) Hopfield-style energy landscape (requires symmetric W), (c) Poincaré duality if it was used. Replacement: sheaf on the Alexandrov topology of the reachability preorder, with ι! ⊣ ι* ⊣ ι* reformulated as Kan extensions. The cohomology becomes quiver cohomology. `[OPEN HYPOTHESIS]` on whether this produces the same topological readings.

6. **F_MOS.** The predictive term M₄ = PMI(i,j) is the transition log-likelihood component of F_MOS (D3). The same F_MOS provides the gradient for all five weights (D2). No parallel objective.

7. **Simulable.** Per tick: W·a is O(N²) ≈ 1.15M flops; Hebbian update O(N²); context update O(Nd); TD update O(N) (one row of M₃); competition O(N log N). Total ≈ 2.5M flops/tick ≈ 2.5 ms. No N×N×N object. No matrix inverse per tick — the SR is learned by TD (EQ-10), not computed as (I − γT)⁻¹. Dense W at N = 1074 is 9 MB. `[MEASURED]` from the document's compute estimates.

8. **Lag-CRP.** Forward asymmetry derived in D6 as exp(w₃ γ^ℓ a_i) > 1, a direct consequence of the SR's upper-triangular structure (D1). Not fitted — it follows from the temporal edge being the successor representation of a forward sequence.

# §8 PREDICTIONS

1. **Assembly size follows k*(λ).** Plot k* against λ; it should follow N(1 − Φ((λk* − μ)/σ_h)). **Refuted if:** k* is not a smooth, monotonically decreasing function of λ, or if it jumps discontinuously (indicating bistability rather than emergence).

2. **w₃ ablation kills the asymmetry but not the peak.** Setting w₃ = 0 should eliminate the forward asymmetry (P(+1)/P(−1) → 1) while preserving the peak at |lag| = 1 (from context). **Refuted if:** removing w₃ eliminates the entire lag-CRP (the peak is temporal, not contextual) or leaves the asymmetry intact (the asymmetry is not from SR).

3. **Embedding shuffle preserves lag-CRP, destroys semantic clustering.** Permuting concept labels in M₁ (the semantic term) should not change the lag-CRP or serial position curve, but should reduce semantic clustering to chance. **Refuted if:** the lag-CRP changes under embedding shuffle (the model is circular — the temporal dynamics depend on the embedding).

4. **Fatigue ablation causes sticking.** Setting φ = 0 should cause the model to remain in a single attractor indefinitely. **Refuted if:** the model still transitions between assemblies without fatigue (φ did not earn its place and should be deleted).

# §9 ASSUMPTIONS

1. `[ASSUMPTION]` F_MOS has the standard variational form F = E_q[log q] − E_q[log p(x,z)]. The document references F_MOS and π_e but does not define them; I assume the standard form. If F_MOS has a different structure, D2 and D3 need revision.

2. `[ASSUMPTION]` The generative transition model is logistic: p(j ∈ A(t) | A(t−1)) = σ(h_j). This is the simplest choice consistent with the activation dynamics; other link functions would change the gradient in D2.

3. `[ASSUMPTION]` Pre-inhibition activations h_i are approximately i.i.d. Gaussian in the mean-field limit. This is needed for the closed-form assembly size in D4. If the distribution is non-Gaussian, the fixed-point equation still holds but lacks the Φ form.

4. `[ASSUMPTION]` Item vectors v_i are approximately uncorrelated, so context contributions are approximately symmetric in lag. This is needed for D6. If item vectors are highly correlated, the context term may contribute to the asymmetry, and the clean separation in D6 breaks.

5. `[ASSUMPTION]` The inner loop converges in K ≈ 3–5 iterations. This is an engineering choice; if it does not converge, the dynamics are not well-defined.

6. `[ASSUMPTION]` The TD learning of M₃ converges. Standard for SR with a fixed policy `[DERIVED]` from Dayan (1993), but the policy here (the activation dynamics) is not fixed — it co-evolves with W. Convergence is `[OPEN HYPOTHESIS]`.

7. `[ASSUMPTION]` The mixing coefficients α, β, γ_g are precision-weighted (D7). This follows from the Gaussian generative model; if the model is non-Gaussian, the weights take a different form.

8. `[ASSUMPTION]` The sheaf on the Alexandrov topology recovers the same topological features (covers, partitions, persistent cycles) as the standard sheaf on a symmetric space. This is `[OPEN HYPOTHESIS]` — the directed cohomology may see different structure.

# §10 WHAT I COULD NOT DO

1. **I could not define F_MOS precisely.** The document references it but gives no equation. I assumed the standard variational free energy. If F_MOS is structured differently (e.g., with a specific generative model for text), the gradient in D2 and the predictive term in D3 need rederivation. This is the single largest gap.

2. **I could not prove uniqueness of the assembly-size fixed point.** The self-consistency equation k* = N(1 − Φ((λk* − μ)/σ_h)) may have multiple solutions for certain (μ, σ_h, λ). The stability condition in D5 identifies the stable branch, but I did not prove there is exactly one stable fixed point. If there are two, the assembly size is bistable and the "emergence" claim weakens.

3. **I could not verify the sheaf cohomology on the Alexandrov topology produces the same topological readings as the existing treatment.** The reformulation as Kan extensions on a preorder is mathematically clean, but whether directed flag complexes or quiver cohomology recover the same cover/partition/hierarchy distinctions that the original sheaf cohomology was designed to detect is an open question. The direction information may change what counts as a "cover."

4. **I could not derive the exact decay rate of the lag-CRP.** The derivation in D6 gives the asymmetry ratio as exp(w₃ γ^ℓ a_i), but the absolute shape of the lag-CRP depends on the learned transition matrix T (which determines M₃) and the context drift rate ρ. These are learned, not derived from first principles. The *form* (exponential decay, forward asymmetry) is derivable; the *parameters* are not.

5. **I could not show that the five edge weights w₁,…,w₅ converge to unique values.** The free energy landscape may have multiple minima, especially since W is N²-dimensional and the five weights are a 5-dimensional projection. The validation battery constrains the weights, but I did not prove the constraints select a unique minimum.

6. **I could not verify the TD convergence for M₃ when the policy co-evolves.** Standard SR convergence assumes a fixed transition matrix T. Here, T is the temporal co-activation structure, which changes as W changes. This is a non-stationary TD problem, and convergence is not guaranteed. `[CITATION NEEDED: non-stationary TD convergence]`

7. **I could not address whether the framework escapes the circularity trap on its own.** The honest answer is: it does not. The semantic term M₁ is the embedding, and if w₁ is large, the topology is the embedding's. The formalism makes this *visible* (you can read off w₁ and ask whether it dominates) but does not *prevent* it. The validation battery is the escape, not the formalism. If this is unsatisfactory, the alternative is to derive w₁ from F_MOS with a prior that penalises embedding dependence — but that prior would itself be a hand-set decision, which is the trap.