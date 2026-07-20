"""Square-lattice density of states via the complete elliptic integral.

Pure stdlib: K(m) through the arithmetic-geometric mean, machine precision.
The table is in reduced units (half bandwidth D = 1, t = 1/4):
rho(eps) = (2/pi^2) * K(1 - eps^2) on (-1, 1), with the van Hove log at 0
avoided by an even midpoint grid (no sample sits exactly on eps = 0).
"""

from __future__ import annotations

import math


def elliptic_k(m: float) -> float:
    """Complete elliptic integral K(m) with parameter m = k^2 (AGM).

    The termination tolerance must sit above machine epsilon (2.2e-16):
    once the two means plateau one ulp apart, a tighter test never becomes
    false and the loop spins forever. AGM converges quadratically, so the
    iteration cap is generous headroom, not a precision limit.
    """
    if not 0.0 <= m < 1.0:
        raise ValueError(f"elliptic_k requires 0 <= m < 1, got {m}")
    a = 1.0
    b = math.sqrt(1.0 - m)
    for _ in range(64):
        if abs(a - b) <= 4e-16 * a:
            break
        a, b = (a + b) / 2.0, math.sqrt(a * b)
    else:  # pragma: no cover - quadratic convergence makes this unreachable
        raise ArithmeticError(f"AGM did not converge for m={m}")
    return math.pi / (2.0 * a)


def square_dos_table(nodes: int = 512) -> tuple[list[float], list[float]]:
    """Midpoint-sampled square DOS: (energies, weights with sum = 1)."""
    if nodes % 2:
        raise ValueError("node count must be even (keeps eps = 0 off-grid)")
    step = 2.0 / nodes
    energies = [-1.0 + (k + 0.5) * step for k in range(nodes)]
    density = [
        (2.0 / math.pi**2) * elliptic_k(1.0 - eps * eps) for eps in energies
    ]
    total = sum(density)
    weights = [value / total for value in density]
    return energies, weights
