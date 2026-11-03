"""The metapelite set (White et al. 2014, ported from MAGEMin by scripts/port_magemin_mp.py): every model
is checked against itself.  Each end member alone has activity 1 and mu equal to its recipe, every site
fraction of a mixed composition is >= 0, and mu is the derivative of G.  Comparison with MAGEMin's own
results is in test_hp_metapelite_magemin.py.
"""
import numpy as np
import pytest

from protolith.core.hp.endmembers import DATASETS, gibbs
from protolith.core.hp.minimize import IGNEOUS, METAPELITE
from protolith.core.hp.solutions_mp import SOLUTIONS_MP

T, P = 873.15, 7.0


def _mix(s):
    """An interior composition: mostly the first end member with some of every other."""
    p = np.full(s.n, 0.6 / (s.n - 1))
    p[0] = 0.4
    return p


def test_all_end_members_are_in_ds62():
    for s in SOLUTIONS_MP.values():
        for e in s.end_members:
            for _, name, _ in e.recipe:
                assert name in DATASETS["62"], (s.name, name)
            assert np.isfinite(e.g(T, P))


@pytest.mark.parametrize("name", sorted(SOLUTIONS_MP))
def test_pure_end_members(name):
    s = SOLUTIONS_MP[name]
    g0 = s.g0(T, P)
    for i in range(s.n):
        p = np.zeros(s.n)
        p[i] = 1.0
        with np.errstate(divide="ignore", invalid="ignore"):
            assert s.ln_activity_ideal(p)[i] == pytest.approx(0.0, abs=3e-5)   # (MAGEMin's rounded constants)
            assert s.mu(p, T, P)[i] == pytest.approx(g0[i], abs=1e-3)


@pytest.mark.parametrize("name", sorted(SOLUTIONS_MP))
def test_mu_is_derivative_of_g(name):
    s = SOLUTIONS_MP[name]
    n0 = _mix(s)
    assert np.all(s.constraints @ n0 >= 0)
    mu = s.mu(n0, T, P)
    # feldspar's Al-avoidance activities and the simplified spinel of White et al. (2002) are not one
    # entropy's derivative (MAGEMin uses them as they are), so only their excess terms are held to this
    exact = name not in ("fsp", "sp")
    if not exact:
        mu = s.mu_excess(n0, T, P)
    h = 1e-6
    for i in range(s.n):
        up, dn = n0.copy(), n0.copy()
        up[i] += h
        dn[i] -= h
        if exact:
            d = (up.sum() * s.gibbs(up / up.sum(), T, P) - dn.sum() * s.gibbs(dn / dn.sum(), T, P)) / (2 * h)
        else:
            d = (up.sum() * s.g_excess(up / up.sum(), T, P) - dn.sum() * s.g_excess(dn / dn.sum(), T, P)) / (2 * h)
        assert d == pytest.approx(mu[i], abs=1e-3)


def test_white_2014_recipes():
    st, g = SOLUTIONS_MP["st"], SOLUTIONS_MP["g"]
    assert st.g0(T, P)[0] == pytest.approx(gibbs("mst", T, P, dataset="62") - 8.0)
    assert g.names == ("py", "alm", "spss", "gr", "kho")
    assert g.g0(T, P)[4] == pytest.approx(gibbs("andr", T, P, dataset="62") - gibbs("gr", T, P, dataset="62")
                                          + gibbs("py", T, P, dataset="62") + 27.0)


def test_sets_are_apart():
    assert IGNEOUS.dataset == "636" and METAPELITE.dataset == "62"
    assert "st" not in IGNEOUS.solutions and "st" in METAPELITE.solutions
    assert "H2O" in METAPELITE.pure and "fl" not in METAPELITE.solutions
