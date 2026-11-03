"""Staurolite, chloritoid and sapphirine (White et al. 2014): self-consistency of the models.

MAGEMin's test points carry none of these phases, so they are checked against themselves: each end member
alone has activity 1 and G equal to its recipe, every site sums to 1, and mu is the derivative of G.
"""
import numpy as np
import pytest

from protolith.core.hp.endmembers import gibbs
from protolith.core.hp.solutions import SOLUTIONS

NEW = ("st", "ctd", "sa")
# a composition inside each model (sapphirine with some order-disorder, spro negative is allowed)
MIX = {"st": [0.25, 0.6, 0.05, 0.1], "ctd": [0.2, 0.75, 0.05], "sa": [0.5, 0.25, 0.1, 0.1, 0.05]}
T, P = 873.15, 7.0
SITES = {"st": ("X", "Y"), "ctd": ("M1A", "M1B"), "sa": ("M3", "M456", "T")}


@pytest.mark.parametrize("name", NEW)
def test_pure_end_members(name):
    s = SOLUTIONS[name]
    g0 = s.g0(T, P)
    for i in range(s.n):
        p = np.zeros(s.n)
        p[i] = 1.0
        assert s.ln_activity_ideal(p)[i] == pytest.approx(0.0, abs=1e-6)   # (3.0792 in mstt is rounded)
        assert s.mu(p, T, P)[i] == pytest.approx(g0[i], abs=1e-5)


@pytest.mark.parametrize("name", NEW)
def test_sites_sum_to_one(name):
    s = SOLUTIONS[name]
    sf = dict(zip(s.site_names, s.site_fractions(MIX[name])))
    assert min(sf.values()) >= 0
    for site in SITES[name]:
        assert sum(v for k, v in sf.items() if k.endswith(site)) == pytest.approx(1.0, abs=1e-12), site


@pytest.mark.parametrize("name", NEW)
def test_mu_is_derivative_of_g(name):
    s = SOLUTIONS[name]
    n0 = np.array(MIX[name], float)
    mu = s.mu(n0, T, P)
    h = 1e-6
    for i in range(s.n):
        up, dn = n0.copy(), n0.copy()
        up[i] += h
        dn[i] -= h
        d = (up.sum() * s.gibbs(up / up.sum(), T, P) - dn.sum() * s.gibbs(dn / dn.sum(), T, P)) / (2 * h)
        assert d == pytest.approx(mu[i], abs=1e-3)


def test_recipes_follow_white_2014():
    st, ctd = SOLUTIONS["st"], SOLUTIONS["ctd"]
    assert st.g0(T, P)[0] == pytest.approx(gibbs("mst", T, P) - 8.0)
    assert ctd.g0(T, P)[2] == pytest.approx(0.25 * gibbs("andr", T, P) - 0.25 * gibbs("gr", T, P)
                                            + gibbs("mctd", T, P) + 13.5)


def test_not_in_magmas_default_set():
    from protolith.core.hp.minimize import SOLUTION_PHASES

    assert not set(NEW) & set(SOLUTION_PHASES)
