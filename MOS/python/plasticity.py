"""
TATIANA - Plasticity: the neuro control layer (plan 5p, mechanisms (2) and (3)).

Two small, independently-tested objects that turn the coarse complex from a
hand-tuned object into a self-tuning one, killing two magic numbers:

  Homeostat          (3) Butz-van Ooyen structural plasticity: growth is driven
                         by a leaky-integrated DEVIATION from a target discord,
                         not by an instantaneous spike. Thrash-proof trigger for
                         the search-controller. Kills reactive over-triggering.

  CriticalityMonitor (2) Beggs-Plenz self-organised criticality: keep the
                         binding process near branching ratio sigma ~ 1 (maximal
                         dynamic range), and auto-calibrate the RESOLVE gate
                         epsilon as an empirical quantile of observed rho instead
                         of the hardcoded 0.10. Kills the guessed threshold.

HONESTY
-------
* Both are SLOPE mechanisms: they need accumulated history. Cold start => they
  return the old fixed behaviour (empty homeostat triggers nothing; the monitor
  falls back to a default epsilon). They earn their keep over time.
* Criticality statistics are only meaningful where N is large: at the 6-organ
  COARSE level, sigma is underpowered and we use it only as a coarse nudge -
  real criticality belongs to the FINE (concept) complex. The rho-quantile gate
  is the honest, usable coarse-level tool; the sigma controller is provided for
  the fine level and documented as such.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np


# ============================================================ (3) HOMEOSTAT ===
class Homeostat:
    """Per-organ leaky integrator of local discord vs a target setpoint.

    integral_v <- (1-leak)*integral_v + leak*discord_v      (each observation)
    An organ whose integrated local discord PERSISTENTLY exceeds the setpoint is
    the one to grow structure at. A single spike cannot cross the setpoint - it
    must be sustained - which is exactly the anti-thrash property we want before
    spending an (expensive) attachment sample.
    """

    def __init__(self, setpoint: float, leak: float = 0.25):
        if not (0.0 < leak <= 1.0):
            raise ValueError("leak must be in (0,1]")
        self.setpoint = setpoint
        self.leak = leak
        self.integral: Dict[str, float] = {}

    def observe(self, per_organ_discord: Dict[str, float]) -> None:
        """Fold one measurement in. Organs absent from this observation relax
        toward 0 (their discord right now is 0 - they are not disagreeing)."""
        seen = set(per_organ_discord)
        for v in set(self.integral) | seen:
            d = float(per_organ_discord.get(v, 0.0))
            prev = self.integral.get(v, 0.0)
            self.integral[v] = (1.0 - self.leak) * prev + self.leak * d

    def error(self, organ: str) -> float:
        """Integrated deviation from setpoint (positive => grow here)."""
        return self.integral.get(organ, 0.0) - self.setpoint

    def organs_needing_growth(self) -> List[str]:
        """Organs whose PERSISTENT local discord has crossed the setpoint,
        worst first. These are where an attachment sample should be aimed."""
        hot = [(v, self.integral[v]) for v in self.integral
               if self.integral[v] > self.setpoint]
        hot.sort(key=lambda t: -t[1])
        return [v for v, _ in hot]

    @staticmethod
    def per_organ_discord(per_edge: Dict, ) -> Dict[str, float]:
        """Aggregate a CoherenceReport.per_edge into per-organ local discord
        (each organ gets the sum of its incident edge discords)."""
        out: Dict[str, float] = {}
        for (u, v), d in per_edge.items():
            out[u] = out.get(u, 0.0) + d
            out[v] = out.get(v, 0.0) + d
        return out


# ==================================================== (2) CRITICALITY MONITOR ==
class CriticalityMonitor:
    """Auto-calibrated RESOLVE gate + branching-ratio nudge toward sigma~1."""

    def __init__(self, default_eps_rho: float = 0.10, min_history: int = 20,
                 quantile: float = 0.75, window: int = 500):
        self.default_eps_rho = default_eps_rho
        self.min_history = min_history
        self.quantile = quantile
        self.window = window
        self.rho_history: List[float] = []
        self.avalanches: List[int] = []

    # --- the honest coarse-level tool: empirical-quantile gate --------------
    def record_rho(self, rho: Optional[float]) -> None:
        if rho is not None:
            self.rho_history.append(float(rho))
            if len(self.rho_history) > self.window:
                self.rho_history = self.rho_history[-self.window:]

    def eps_rho(self) -> float:
        """eps_rho: the RESOLVE/EXPLORE THRESHOLD on rho, auto-calibrated as the
        q-quantile of observed rho. Below min_history we cannot calibrate, so we
        return the documented default (0.10 from 5h) rather than guess from noise.

        NAMED eps_rho, NOT epsilon (C6-2). MOS has a second, unrelated epsilon:
        eps_flow, the STEP SIZE in the curvature flow `w <- w*exp(eps_flow*kappa)`
        (5ad). A threshold and a step size share nothing but a Greek letter --
        one is compared against a measurement, the other multiplies a rate -- and
        the prose in Part C already conflated them once. The flow is not in the
        engine yet, so this rename is preventive: by the time eps_flow lands
        there is no name left for it to collide with.
        """
        if len(self.rho_history) < self.min_history:
            return self.default_eps_rho
        return float(np.quantile(self.rho_history, self.quantile))

    # --- the fine-level tool (underpowered at coarse; provided for fine) ----
    def record_avalanche(self, n_binds: int) -> None:
        self.avalanches.append(int(n_binds))
        if len(self.avalanches) > self.window:
            self.avalanches = self.avalanches[-self.window:]

    def branching_ratio(self) -> Optional[float]:
        """sigma proxy: mean binds triggered per reasoning act. sigma>1
        supercritical (runaway binding), <1 subcritical (nothing sticks),
        ~1 critical (maximal dynamic range). None until there is history.
        MEANINGFUL ONLY AT SCALE - see module docstring."""
        if not self.avalanches:
            return None
        return float(np.mean(self.avalanches))

    def suggest_decay(self, current_decay: float, target_sigma: float = 1.0,
                      gain: float = 0.1) -> float:
        """Nudge the decay rate to push sigma toward 1: supercritical => decay
        faster (prune more), subcritical => decay slower (let coalitions live).
        A slow proportional controller; returns the adjusted decay (clamped >0)."""
        sigma = self.branching_ratio()
        if sigma is None:
            return current_decay
        adjusted = current_decay + gain * (sigma - target_sigma)
        return max(adjusted, 1e-3)


if __name__ == "__main__":
    print("=== 1. HOMEOSTAT: a transient spike does NOT trigger growth ===")
    h = Homeostat(setpoint=0.30, leak=0.25)
    # one big spike, then quiet
    h.observe({"Reason": 1.0, "Search": 0.0})
    for _ in range(5):
        h.observe({"Reason": 0.0, "Search": 0.0})
    print(f"    Reason integral after spike+quiet = {h.integral['Reason']:.3f} "
          f"(setpoint {h.setpoint})")
    assert h.organs_needing_growth() == [], "a single spike must not trigger growth"
    print("    growth triggered:", h.organs_needing_growth(), " (correctly none)")

    print("\n=== 2. HOMEOSTAT: SUSTAINED discord DOES trigger growth ===")
    h2 = Homeostat(setpoint=0.30, leak=0.25)
    for _ in range(10):
        h2.observe({"Reason": 0.5, "Search": 0.05})
    print(f"    Reason integral (sustained 0.5) = {h2.integral['Reason']:.3f}")
    print(f"    Search integral (sustained 0.05) = {h2.integral['Search']:.3f}")
    assert h2.organs_needing_growth() == ["Reason"], h2.organs_needing_growth()
    print("    growth aimed at:", h2.organs_needing_growth(), " (Reason only)")

    print("\n=== 3. HOMEOSTAT: per-organ aggregation of per_edge ===")
    agg = Homeostat.per_organ_discord({("A", "B"): 0.2, ("B", "C"): 0.5})
    assert abs(agg["B"] - 0.7) < 1e-12 and abs(agg["A"] - 0.2) < 1e-12
    print("    B (in two edges) =", round(agg["B"], 3), " A =", round(agg["A"], 3))

    print("\n=== 4. CRITICALITY: cold start returns the documented default ===")
    m = CriticalityMonitor(default_eps_rho=0.10, min_history=20)
    assert m.eps_rho() == 0.10
    print("    eps_rho() with no history =", m.eps_rho(), " (falls back, no guessing)")

    print("\n=== 5. CRITICALITY: eps_rho auto-calibrates to the rho quantile ===")
    rng = np.random.default_rng(0)
    for _ in range(400):
        m.record_rho(float(abs(rng.normal(0.05, 0.03))))  # a realistic low-rho stream
    eps = m.eps_rho()
    q75 = float(np.quantile(m.rho_history, 0.75))
    print(f"    eps_rho() = {eps:.4f}  (== 75th percentile {q75:.4f})")
    assert abs(eps - q75) < 1e-9

    print("\n=== 6. CRITICALITY: decay controller pushes sigma toward 1 ===")
    m.avalanches = [3, 4, 3, 5]        # supercritical (sigma ~ 3.75 > 1)
    up = m.suggest_decay(0.10)
    m.avalanches = [0, 0, 1, 0]        # subcritical (sigma ~ 0.25 < 1)
    down = m.suggest_decay(0.10)
    print(f"    supercritical -> decay {0.10} -> {up:.3f} (faster pruning)")
    print(f"    subcritical   -> decay {0.10} -> {down:.3f} (slower pruning)")
    assert up > 0.10 > down

    print("\nALL PLASTICITY SELF-TESTS PASSED")
