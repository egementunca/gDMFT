from __future__ import annotations

import math

import pytest

from gdmft.atlas.dos import elliptic_k, square_dos_table


def test_elliptic_k_reference_values() -> None:
    assert elliptic_k(0.0) == pytest.approx(math.pi / 2, rel=1e-14)
    # K(1/2) = Gamma(1/4)^2 / (4 sqrt(pi))
    assert elliptic_k(0.5) == pytest.approx(1.8540746773013719, rel=1e-12)
    assert elliptic_k(0.99) == pytest.approx(3.6956373629898747, rel=1e-10)
    with pytest.raises(ValueError):
        elliptic_k(1.0)


def test_square_dos_table_normalization_symmetry_and_moment() -> None:
    energies, weights = square_dos_table(512)
    assert len(energies) == 512
    assert sum(weights) == pytest.approx(1.0, abs=1e-12)
    # even midpoint grid keeps the van Hove point off-grid
    assert all(eps != 0.0 for eps in energies)
    # particle-hole symmetric
    for k in range(256):
        assert energies[k] == pytest.approx(-energies[511 - k], abs=1e-14)
        assert weights[k] == pytest.approx(weights[511 - k], rel=1e-12)
    # second moment of the D=1 square DOS is 1/4 (matches the Bethe bath
    # moment — the benchmark notes' validation anchor)
    second_moment = sum(
        w * eps * eps for eps, w in zip(energies, weights, strict=True)
    )
    assert second_moment == pytest.approx(0.25, abs=2e-3)


def test_square_dos_requires_even_grid() -> None:
    with pytest.raises(ValueError):
        square_dos_table(511)
