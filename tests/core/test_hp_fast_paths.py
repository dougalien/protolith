"""The solver's fast paths give the same numbers as the plain formulas they replace."""
import numpy as np
import pytest

from protolith.core.hp import minimize as M
from protolith.core.hp.solutions import R, SOLUTIONS
from protolith.core.hp.solutions_mp import SOLUTIONS_MP

ALL = list(SOLUTIONS.items()) + [("mp " + k, v) for k, v in SOLUTIONS_MP.items()]
CONDITIONS = ((1473.15, 0.001), (873.15, 6.0))


def _plain_mu(s, prop, t, p):
    with np.errstate(all="ignore"):
        return s.g0(t, p) + R * t * s.ln_activity_ideal(prop) + s.mu_excess(prop, t, p)


@pytest.mark.parametrize("name, s", ALL, ids=[n for n, _ in ALL])
def test_mu_matches_the_plain_formula(name, s):
    rng = np.random.default_rng(0)
    for t, p in CONDITIONS:
        for k in range(20):
            prop = rng.dirichlet(np.ones(s.n))
            keep = np.arange(s.n) if k % 2 == 0 else np.sort(rng.choice(s.n, rng.integers(1, s.n + 1), replace=False))
            full = np.zeros(s.n)
            full[keep] = prop[keep] / prop[keep].sum()
            ref = _plain_mu(s, full, t, p)
            with np.errstate(all="ignore"):
                assert np.allclose(s.mu(full, t, p), ref, rtol=0, atol=1e-9, equal_nan=True)
                sub = s.restricted(keep).mu(full[keep], t, p)
            assert np.allclose(sub, ref[keep], rtol=0, atol=1e-9, equal_nan=True)


@pytest.mark.parametrize("name, s", ALL, ids=[n for n, _ in ALL])
def test_mu_jacobian_matches_finite_differences(name, s):
    rng = np.random.default_rng(1)
    sub = s.restricted(np.arange(s.n))
    for t, p in CONDITIONS:
        q = rng.dirichlet(np.full(s.n, 3.0))
        out = sub.mu_jacobian(q, t, p)
        assert out is not None
        mu, jac = out
        assert np.allclose(mu, sub.mu(q, t, p), rtol=0, atol=1e-9)
        fd = np.empty_like(jac)
        for i in range(s.n):
            h = 1e-7
            qp, qm = q.copy(), q.copy()
            qp[i] += h
            qm[i] -= h
            fd[:, i] = (sub.mu(qp, t, p) - sub.mu(qm, t, p)) / (2 * h)
        assert np.max(np.abs(jac - fd)) < 1e-4 * max(1.0, np.max(np.abs(fd)))


def test_newton_and_slsqp_find_the_same_minimum():
    """The Newton search of a driving force lands where SLSQP does (olivine and liquid of a basalt)."""
    bulk = np.zeros(len(M.COMPONENTS))
    for c, v in {"SiO2": 0.84, "Al2O3": 0.144, "CaO": 0.203, "MgO": 0.188, "FeO": 0.145, "Na2O": 0.045,
                 "K2O": 0.002, "TiO2": 0.021, "O": 0.01}.items():
        bulk[M.COMPONENTS.index(c)] = v
    t, p = 1473.15, 0.001
    res = M.equilibrate(bulk, t, p)
    for name in ("ol", "liq", "cpx"):
        r = M._Reduced(SOLUTIONS[name], bulk > 0)
        cg = r.comp @ res.gamma
        start = np.full(len(r.keep), 1.0 / len(r.keep))
        newton = M._newton_df(r, cg, t, p, start)
        assert newton is not None
        r.newton = False                      # the SLSQP path alone
        slsqp = min(M._driving_force_min(r, res.gamma, t, p, [start], None), key=lambda z: z[0])
        assert newton[0] == pytest.approx(slsqp[0], abs=1e-6)
        assert np.max(np.abs(newton[1] - slsqp[1])) < 1e-3
