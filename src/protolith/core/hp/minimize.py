"""Gibbs energy minimization for the Holland & Powell engine.

The stable assemblage at fixed T, P and bulk composition is found by linear programming with column
generation, the "levelling" idea behind Perple_X and MAGEMin, in our own form:

1. Each solution phase is represented by a few trial compositions ("columns"), each pure phase by one.
   A linear programme picks the amounts that minimize G with mass balance exact; its dual values are
   the chemical potentials gamma of the oxide components.
2. For every solution phase, the composition p that minimizes the driving force
   f(p) = G(p) - c(p) . gamma (per formula unit) is found with the site fractions kept >= 0.  Any
   column with f < 0 lowers G and is added.
3. Steps 1-2 repeat until no phase has a negative driving force.  The columns in use are then the
   stable phases; a phase may appear twice across a solvus (two feldspars, two amphiboles).

Units: kJ, K, kbar, moles of oxides.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog, minimize

from .endmembers import DATASETS, OXIDES, R, gibbs
from .solutions import SOLUTIONS, HPSolution
from .solutions_mp import SOLUTIONS_MP

# MnO is last so that the first eleven keep the places they had before it was added (2026-11-03)
COMPONENTS = ("SiO2", "Al2O3", "CaO", "MgO", "FeO", "K2O", "Na2O", "TiO2", "O", "Cr2O3", "H2O", "MnO")
_IDX = [OXIDES.index(o) for o in COMPONENTS]

# pure phases of the igneous set (MAGEMin's list less the buffers, O2 and pure H2O, which the fluid covers)
PURE_PHASES = ("q", "crst", "trd", "coe", "stv", "ky", "sill", "and", "ru", "sph", "cor", "ne")
SOLUTION_PHASES = ("liq", "fl", "ol", "opx", "cpx", "g", "spl", "ilm", "fsp", "amp", "bi", "mu", "cd", "ep", "chl")
MELT_MIN_T = 773.15          # K; no liquid below this (as in MAGEMin)
# pure phases of the metapelite set (MAGEMin's list less the buffers and O2); water is pure H2O, no fluid model
MP_PURE_PHASES = ("q", "crst", "trd", "coe", "stv", "ky", "sill", "and", "ru", "sph", "zo", "cor", "H2O")


@dataclass(frozen=True)
class PhaseSet:
    """A consistent set of phases: solution models, pure phases and the end-member dataset they use."""
    name: str
    solutions: dict
    pure: tuple
    default: tuple                # the solution phases switched on when none are named
    dataset: str


IGNEOUS = PhaseSet("igneous", SOLUTIONS, PURE_PHASES, SOLUTION_PHASES, "636")
# MAGEMin's metapelite set carries two alternative models of two phases and uses one of each: spinel
# (sp, "Sp LT") rather than magnetite (mt), and ilmenite without Mg and Mn (ilm) rather than ilmm (its
# defaults mpSp = 0, mpIlm = 0).  The default here is the same; name mt or ilmm in `phases` to use them.
METAPELITE = PhaseSet("metapelite", SOLUTIONS_MP, MP_PURE_PHASES,
                      tuple(n for n in SOLUTIONS_MP if n not in ("mt", "ilmm")), "62")
PHASE_SETS = {s.name: s for s in (IGNEOUS, METAPELITE)}
SF_MIN = 1e-10
TRACE = 2e-5                 # mole fraction below which a component is left out


@dataclass
class Phase:
    name: str
    amount: float                 # moles of formula units
    prop: np.ndarray | None       # end-member proportions (solution phases)
    end_members: tuple
    composition: np.ndarray       # moles of each component per formula unit
    g: float                      # G per formula unit, kJ

    @property
    def oxide_moles(self) -> np.ndarray:
        return self.amount * self.composition


@dataclass
class Result:
    t: float
    p: float
    bulk: np.ndarray
    phases: list
    gamma: np.ndarray             # chemical potentials of COMPONENTS, kJ
    g: float                      # total G, kJ
    iterations: int
    converged: bool
    max_driving_force: float = field(default=0.0)

    def by_name(self) -> dict:
        out = {}
        for ph in self.phases:
            out.setdefault(ph.name, []).append(ph)
        return out


class _Reduced:
    """A solution phase restricted to the end members whose components are present in the bulk."""

    def __init__(self, s: HPSolution, present: np.ndarray):
        comp = s.compositions()[:, _IDX]
        keep = np.all((comp == 0) | present[None, :], axis=1)
        # an end member made with a negative amount of an absent component is still impossible
        self.s, self.keep = s, np.where(keep)[0]
        self.comp = comp[self.keep]
        self.a = s.constraints[:, self.keep]
        used = np.any(self.a != 0, axis=1)
        self.a_used = self.a[used]
        # end members that alone fill some site species can never be negative: the Newton polish
        # carries them as logarithms so that trace amounts (fo in the fluid) stay positive
        only = (self.a_used != 0).sum(axis=1) == 1
        self.positive = np.zeros(len(self.keep), bool)
        for row in self.a_used[only]:
            self.positive[np.where(row != 0)[0][0]] = True
        sub = s.restricted(self.keep)
        self._mu, self._jac = sub.mu, sub.mu_jacobian
        self.newton = _gibbs_duhem_holds(sub)

    def full(self, q: np.ndarray) -> np.ndarray:
        p = np.zeros(self.s.n)
        p[self.keep] = q
        return p

    def mu(self, q, t, p):
        return self._mu(q, t, p)

    def g(self, q, t, p) -> float:
        return float(q @ self.mu(q, t, p))

    def feasible(self, q) -> bool:
        return bool(np.all(self.a_used @ q >= -1e-12))


_BASIS = {}
_GD = {}


def _gibbs_duhem_holds(sub) -> bool:
    """Whether sum_k q_k d mu_k = 0 along the composition (so that mu - c.gamma is the gradient of the
    driving force, which the Newton search needs).  It fails for a model whose activities are not
    those of one G(q), such as the metapelite spinel with its ratio sites: those keep SLSQP."""
    key = (id(sub.s), tuple(sub.keep))
    ok = _GD.get(key)
    if ok is None:
        n = len(sub.keep)
        ok = True
        if n > 1:
            q = np.full(n, 1.0 / n)
            out = sub.mu_jacobian(q, 1000.0, 5.0)
            if out is None:
                ok = False
            else:
                res = q @ out[1] @ _tangent_basis(n)
                ok = bool(np.max(np.abs(res)) < 1e-8 * max(1.0, np.max(np.abs(out[1]))))
        _GD[key] = ok
    return ok


def _tangent_basis(n: int) -> np.ndarray:
    """Orthonormal basis (n, n-1) of the directions with sum zero."""
    z = _BASIS.get(n)
    if z is None:
        q, _ = np.linalg.qr(np.column_stack([np.ones(n), np.eye(n)[:, :n - 1]]))
        z = _BASIS[n] = q[:, 1:]
    return z


def _newton_df(r: _Reduced, cg, t, p, q0, max_iter: int = 60):
    """Minimize f(q) = q . (mu(q) - cg) on sum q = 1 with every site fraction > 0, by Newton steps with
    the exact second derivatives (mu_jacobian).  The RT ln terms keep the minimum off the sites' edges,
    so the steps only have to stop short of an edge.  Returns (f, q), or None when this does not apply
    (a model without Gibbs-Duhem, a start on an edge, no convergence): the caller then uses SLSQP.
    It finds the same minima as SLSQP (tests/core/test_hp_fast_paths.py) in a few iterations, where
    SLSQP took about 60, and with much less Python overhead per iteration."""
    if not r.newton:
        return None
    n = len(q0)
    q = np.asarray(q0, float) / np.sum(q0)
    if r.a_used.size and np.min(r.a_used @ q) <= SF_MIN:
        return None
    if n == 1:
        with np.errstate(invalid="ignore", divide="ignore"):
            mu = r.mu(q, t, p)
        return (float(q @ (mu - cg)), q) if np.all(np.isfinite(mu)) else None
    z = _tangent_basis(n)
    out = r._jac(q, t, p)
    if out is None:
        return None
    mu, jac = out
    g = mu - cg
    f = float(q @ g)
    for _ in range(max_iter):
        gz = z.T @ g
        # converged: the gradient is at the rounding level of mu (kJ values of 1e3 carry ~1e-12 relative)
        if np.max(np.abs(gz)) < 1e-8:
            return (f, q) if np.isfinite(f) else None
        h = z.T @ (0.5 * (jac + jac.T)) @ z
        try:
            dz = -np.linalg.solve(h, gz)
            if gz @ dz >= 0:            # not a descent direction (inside a solvus): shift the Hessian
                raise np.linalg.LinAlgError
        except np.linalg.LinAlgError:
            w = np.linalg.eigvalsh(h)
            shift = max(0.0, -w[0]) + 1e-6 * max(1.0, abs(w[-1]))
            dz = -np.linalg.solve(h + shift * np.eye(n - 1), gz)
        d = z @ dz
        # the longest step that keeps every site fraction above zero (with a margin)
        ad = r.a_used @ d
        aq = r.a_used @ q
        neg = ad < 0
        step = 1.0
        if np.any(neg):
            step = min(1.0, 0.9 * float(np.min((aq[neg] - SF_MIN) / -ad[neg])))
        slope = float(g @ d)
        noise = 1e-12 * (abs(float(q @ mu)) + abs(float(q @ cg)) + 1.0)
        while step > 1e-10:
            qn = q + step * d
            with np.errstate(invalid="ignore", divide="ignore"):
                mun = r.mu(qn, t, p)
            fn = float(qn @ (mun - cg))
            if np.isfinite(fn) and fn <= f + 1e-4 * step * slope + noise:
                break
            step *= 0.5
        else:
            return None
        out = r._jac(qn, t, p)
        if out is None:
            return None
        q, (mu, jac), f = qn, out, fn
        g = mu - cg
    return None


def _driving_force_min(r: _Reduced, gamma, t, p, starts, rng):
    """Minimize f(q) = G(q) - c(q).gamma over feasible q, from several starts; returns (f, q) list."""
    cg = r.comp @ gamma
    n = len(r.keep)
    cons = [{"type": "eq", "fun": lambda q: q.sum() - 1.0, "jac": lambda q: np.ones(n)},
            {"type": "ineq", "fun": lambda q: r.a_used @ q - SF_MIN, "jac": lambda q: r.a_used}]

    def f(q):
        with np.errstate(invalid="ignore", divide="ignore"):    # log(0) at a site's edge: handled below
            mu = r.mu(q, t, p)
        if not np.all(np.isfinite(mu)):
            return 1e6, np.zeros(n)
        d = mu - cg
        return float(q @ d), d

    out = []
    for q0 in starts:
        found = _newton_df(r, cg, t, p, q0)
        if found is not None:
            out.append(found)
            continue
        try:
            # f gives the value and the gradient together: one evaluation of mu per point, not two
            res = minimize(f, q0, jac=True, method="SLSQP", constraints=cons,
                           options={"maxiter": 200, "ftol": 1e-10})
        except (ValueError, FloatingPointError):
            continue
        q = res.x
        if r.feasible(q) and np.all(r.a_used @ q > 0) or r.feasible(q):
            val = f(q)[0]
            if np.isfinite(val):
                out.append((val, q))
    return out


def _random_starts(r: _Reduced, k: int, rng) -> list:
    n = len(r.keep)
    starts = [np.full(n, 1.0 / n)]
    for _ in range(k):
        starts.append(rng.dirichlet(np.full(n, 0.5)))
    for i in range(n):           # near each end member
        q = np.full(n, 0.02 / max(n - 1, 1))
        q[i] = 0.98
        starts.append(q / q.sum())
    return starts


def o2_potential(t_k: float, log_fo2: float) -> float:
    """Chemical potential of O2 (kJ) at fugacity 10**log_fo2 bar: G(O2, T, 1 bar) + RT ln fO2."""
    return gibbs("O2", t_k, 0.001) + R * t_k * np.log(10.0) * log_fo2


def equilibrate(bulk, t_k: float, p_kbar: float, phases=None, max_iter: int = 120, tol: float = 1e-4,
                seed: int = 0, verbose: bool = False, log_fo2: float | None = None,
                previous: Result | None = None, system: PhaseSet = IGNEOUS) -> Result:
    """Stable assemblage of `bulk` (moles of COMPONENTS) at T (K) and P (kbar).

    log_fo2: if given, oxygen is open: an O2 reservoir at this fugacity (log10 bar) exchanges O with the
    system, so the excess-oxygen component (Fe3+) follows the buffer.  Result.bulk is then the bulk after
    that exchange.
    previous: the answer at a nearby T, P or bulk (the previous step of a path).  Its assemblage is first
    solved exactly at the new conditions and checked; only if some phase then has a negative driving
    force does the full search run, starting from its compositions.
    """
    bulk = np.asarray(bulk, float).copy()
    if len(bulk) < len(COMPONENTS):                 # a bulk written before MnO was added: no MnO
        bulk = np.concatenate([bulk, np.zeros(len(COMPONENTS) - len(bulk))])
    # a component below TRACE of the bulk (a few ppm) is dropped: the starting columns of a solution
    # always carry some of each of their components, so a trace one would make mass balance impossible
    bulk[bulk < TRACE * bulk[bulk > 0].sum()] = 0.0
    present = bulk > 1e-10
    io = COMPONENTS.index("O")
    if log_fo2 is not None:
        present[io] = present[io] or present[COMPONENTS.index("FeO")]
    rng = np.random.default_rng(seed)
    names = [n for n in (phases or system.default) if n in system.solutions]
    if t_k < MELT_MIN_T:
        names = [n for n in names if n != "liq"]
    reduced = {}
    for n in names:
        r = _Reduced(system.solutions[n], present)
        if len(r.keep):
            reduced[n] = r

    # columns: (phase name, q or None, composition, g)
    cols = []
    data = DATASETS[system.dataset]
    for n in system.pure:
        c = np.array([data[n].comp.get(o, 0.0) for o in COMPONENTS])
        if np.all((c == 0) | present):
            cols.append((n, None, c, gibbs(n, t_k, p_kbar, "equilibrium", system.dataset)))
    warm = {}
    for ph in (previous.phases if previous is not None else []):
        if ph.prop is not None and ph.name in reduced:
            q = np.asarray(ph.prop, float)[reduced[ph.name].keep]
            if q.sum() > 0:
                warm.setdefault(ph.name, []).append(q / q.sum())
    o2_col = None
    if log_fo2 is not None and present[io]:
        o2_col = len(cols)
        cols.append(("O2", None, np.array([2.0 if c == "O" else 0.0 for c in COMPONENTS]),
                     o2_potential(t_k, log_fo2)))
    for n, r in reduced.items():
        # around a warm composition, a small cloud of neighbours: with only the exact old composition the
        # LP is degenerate (one liquid column can equal the bulk) and cannot move toward a new phase
        cloud = []
        for q in warm.get(n, []):
            for i in range(len(q)):
                for d in (0.03, -0.03):
                    qq = q.copy()
                    qq[i] += d
                    if qq.sum() > 0:
                        cloud.append(qq / qq.sum())
        trial = warm.get(n, []) + cloud + _random_starts(r, 2 if n in warm else 6, rng)
        for q in trial:
            if r.feasible(q):
                g = r.g(q, t_k, p_kbar)
                if np.isfinite(g):
                    cols.append((n, q, q @ r.comp, g))

    if previous is not None:
        fast = _from_previous(previous, reduced, cols, bulk, present, o2_col, t_k, p_kbar, tol, rng,
                              system.dataset)
        if fast is not None:
            phases_out, gamma, bulk_out, worst = fast
            phases_out = _merge_twins(phases_out)
            total_g = float(sum(ph.amount * ph.g for ph in phases_out))
            if verbose:
                print(f"previous assemblage holds: worst={worst:.2e}")
            return Result(t_k, p_kbar, bulk_out, phases_out, gamma, total_g, 0, True, worst)
        # the old assemblage could not be carried over: search from scratch.  (Seeding the search with
        # the old melt can stall it: in fractional crystallization that melt column equals the bulk.)
        return equilibrate(bulk, t_k, p_kbar, phases=phases, max_iter=max_iter, tol=tol, seed=seed,
                           verbose=verbose, log_fo2=log_fo2, previous=None, system=system)

    b = bulk[present]
    gamma = np.zeros(len(COMPONENTS))
    it, converged, worst = 0, False, 0.0
    best_q = {n: list(q) for n, q in warm.items()}
    coarse = 0.05                 # kJ; below this the Newton polish takes over
    final = None
    bounds = [(0, None)] * len(cols)
    for it in range(1, max_iter + 1):
        a_eq = np.array([c[2][present] for c in cols]).T
        cost = np.array([c[3] for c in cols])
        bounds += [(0, None)] * (len(cols) - len(bounds))
        if o2_col is not None:
            bounds[o2_col] = (None, None)
        lp = linprog(cost, A_eq=a_eq, b_eq=b, bounds=bounds, method="highs")
        if lp.status != 0:
            raise RuntimeError(f"linear programme failed: {lp.message}")
        gamma = np.zeros(len(COMPONENTS))
        gamma[present] = lp.eqlin.marginals
        x = lp.x
        for k in np.where(x > 1e-12)[0]:
            if cols[k][1] is not None:
                best_q.setdefault(cols[k][0], []).append(cols[k][1])

        worst = 0.0
        added = 0
        for n, r in reduced.items():
            starts = [q for q in best_q.get(n, [])[-3:]]
            if (it <= 2 and n not in warm) or not starts:
                starts += _random_starts(r, 4, rng)[:6]
            found = _driving_force_min(r, gamma, t_k, p_kbar, starts, rng)
            for val, q in sorted(found, key=lambda z: z[0])[:3]:
                worst = min(worst, val)
                if val < -tol:
                    cols.append((n, q, q @ r.comp, r.g(q, t_k, p_kbar)))
                    added += 1
        if verbose:
            print(f"iter {it}: G={lp.fun:.4f} cols={len(cols)} added={added} worst={worst:.2e}")
        if worst >= -coarse or it % 6 == 0:     # (every few rounds: the tail of column generation is slow)
            # close: solve the assemblage exactly, then check every phase against the exact gamma
            final = _finish(cols, lp.x, o2_col, reduced, bulk, gamma, t_k, p_kbar)
            if final is not None:
                phases_out, gam_f, bulk_f = final
                worst_f, extra = _check(reduced, cols, phases_out, best_q, gam_f, t_k, p_kbar, tol, rng)
                if verbose:
                    print(f"  polished: worst={worst_f:.2e} extra={len(extra)}")
                if extra:
                    # a new phase is supersaturated: add it to the assemblage and solve again (the LP alone
                    # can stall here, since the old melt column may equal the bulk exactly)
                    aug = _augment(phases_out, extra, reduced, cols, best_q, bulk, gam_f, o2_col,
                                   t_k, p_kbar, tol, rng)
                    if aug is not None:
                        phases_out, gam_f, bulk_f, worst_f = aug
                        extra = []
                if not extra:
                    converged = True
                    worst = worst_f
                    final = (phases_out, gam_f, bulk_f)
                    worst = worst_f
                    break
                cols.extend(extra)
                coarse = 0.0          # the polish was not enough; finish by column generation
            elif added == 0:
                converged = True
                break
        if added == 0 and worst >= -tol:
            converged, final = True, None
            break
    if final is None or not converged or worst < -tol:
        final = _finish(cols, lp.x, o2_col, reduced, bulk, gamma, t_k, p_kbar, polish_ok=True)
    phases_out, gamma, bulk = final
    phases_out = _merge_twins(phases_out)
    total_g = float(sum(ph.amount * ph.g for ph in phases_out))
    return Result(t_k, p_kbar, bulk, phases_out, gamma, total_g, it, converged, worst)


def _from_previous(previous, reduced, cols, bulk, present, o2_col, t, p, tol, rng, dataset="636"):
    """Solve the previous assemblage exactly at the new conditions; None unless it is still stable."""
    phases = []
    for ph in previous.phases:
        if ph.prop is None:
            if not np.all((ph.composition == 0) | present):
                return None
            phases.append(Phase(ph.name, ph.amount, None, ph.end_members, ph.composition,
                                gibbs(ph.name, t, p, "equilibrium", dataset)))
        else:
            if ph.name not in reduced:
                return None
            r = reduced[ph.name]
            q = np.asarray(ph.prop, float)[r.keep]
            if q.sum() <= 0 or abs(q.sum() - ph.prop.sum()) > 1e-9:
                return None
            phases.append(Phase(ph.name, ph.amount, r.full(q), r.s.names, q @ r.comp, r.g(q, t, p)))
    if not phases:
        return None
    o2_mu = None if o2_col is None else cols[o2_col][3]
    polished = _polish(phases, reduced, bulk, previous.gamma, t, p, o2_mu=o2_mu)
    if polished is None and len(phases) > 1:
        # the old assemblage does not fit the new bulk (some phase would go negative): start again from
        # its main phase alone and let the check add the others back
        main = max(phases, key=lambda ph: ph.amount)
        polished = _polish([main], reduced, bulk, previous.gamma, t, p, o2_mu=o2_mu)
    if polished is None:
        return None
    phases, gamma, d_o = polished
    total = sum(max(ph.amount, 0.0) for ph in phases)
    if any(ph.amount < 1e-9 * total for ph in phases):
        # a phase is used up (in fractional crystallization the crystals were just taken out): drop it
        kept = [ph for ph in phases if ph.amount >= 1e-9 * total]
        if not kept:
            return None
        polished = _polish(kept, reduced, bulk, gamma, t, p, o2_mu=o2_mu)
        if polished is None:
            return None
        phases, gamma, d_o = polished
        if any(ph.amount < 1e-9 * total for ph in phases):
            return None
    worst, extra = _check(reduced, cols, phases, {}, gamma, t, p, tol, rng)
    b = bulk.copy()
    b[COMPONENTS.index("O")] -= d_o
    if extra:
        # a new phase joins: add it and solve again (with the bulk as it was before this polish)
        return _augment(phases, extra, reduced, cols, {}, bulk, gamma, o2_col, t, p, tol, rng)
    return phases, gamma, b, worst


def _augment(phases, extra, reduced, cols, best_q, bulk, gamma, o2_col, t, p, tol, rng, rounds: int = 6):
    """Add the most supersaturated new phase(s) at a trace amount and Newton-solve again; drop phases that
    run out.  Returns (phases, gamma, bulk, worst) once nothing is supersaturated, or None."""
    io = COMPONENTS.index("O")
    o2_mu = None if o2_col is None else cols[o2_col][3]
    total = sum(ph.amount for ph in phases)
    for _ in range(rounds):
        best = {}
        for c in extra:
            val = c[3] - c[2] @ gamma
            if c[0] not in best or val < best[c[0]][0]:
                best[c[0]] = (val, c)
        if not best:
            return None
        allnew = sorted(best.values(), key=lambda z: z[0])
        # all new phases at once, else only the worst one; a trace amount, else a little more
        trials = [(allnew, 1e-4), (allnew[:1], 1e-4), (allnew, 1e-2), (allnew[:1], 1e-2)]
        trials += [([one], frac) for one in allnew[1:] for frac in (1e-4, 1e-2)]   # each of the others alone
        for chosen, frac in trials:
            new = list(phases)
            for val, (n, q, c, g) in chosen:
                amt = frac * total
                if q is None:
                    new.append(Phase(n, amt, None, (n,), c, g))
                else:
                    r = reduced[n]
                    new.append(Phase(n, amt, r.full(q), r.s.names, c, g))
            pol = _polish(new, reduced, bulk, gamma, t, p, o2_mu=o2_mu)
            if pol is None:
                continue
            ph2, gam2, d_o = pol
            if any(ph.amount <= 1e-10 * total for ph in ph2):
                ph2 = [ph for ph in ph2 if ph.amount > 1e-10 * total]
                pol = _polish(ph2, reduced, bulk, gam2, t, p, o2_mu=o2_mu)
                if pol is None:
                    continue
                ph2, gam2, d_o = pol
            phases, gamma = ph2, gam2
            break
        else:
            return None
        worst, extra = _check(reduced, cols, phases, best_q, gamma, t, p, tol, rng)
        if not extra:
            b = bulk.copy()
            b[io] -= d_o
            return phases, gamma, b, worst
    return None


def _merge_twins(phases, merge: float = 0.01) -> list:
    """Two copies of one solution phase that the solve brought to the same composition are one phase."""
    out = []
    for ph in phases:
        for o in out:
            if (o.name == ph.name and o.prop is not None and ph.prop is not None
                    and np.max(np.abs(o.prop - ph.prop)) < merge):
                o.amount += ph.amount
                break
        else:
            out.append(Phase(ph.name, ph.amount, ph.prop, ph.end_members, ph.composition, ph.g))
    return out


def _finish(cols, x, o2_col, reduced, bulk, gamma, t, p, polish_ok: bool = False):
    """Phases from the LP answer, polished by Newton.  Returns (phases, gamma, bulk) or None if the
    polish fails (with polish_ok, the LP answer is returned instead)."""
    bulk = bulk.copy()
    io = COMPONENTS.index("O")
    if o2_col is not None:
        bulk[io] = max(bulk[io] - 2.0 * x[o2_col], 0.0)    # O2 taken from the system (or given to it)
        x = x.copy()
        x[o2_col] = 0.0
    phases = _collect(cols, x, reduced, t, p)
    total = sum(ph.amount for ph in phases)
    phases = [ph for ph in phases if ph.amount > 1e-7 * total]      # LP crumbs would make the Newton singular
    polished = _polish(phases, reduced, bulk, gamma, t, p, o2_mu=None if o2_col is None else cols[o2_col][3])
    if polished is None:
        return (phases, gamma, bulk) if polish_ok else None
    phases, gamma, d_o = polished
    bulk[io] -= d_o
    return phases, gamma, bulk


def _check(reduced, cols, phases, best_q, gamma, t, p, tol, rng):
    """Driving force of every solution phase and pure phase at the polished gamma.  Returns the most
    negative value and new columns for any phase below -tol."""
    worst, extra = 0.0, []
    for c in cols:
        if c[1] is None and c[0] != "O2":
            val = c[3] - c[2] @ gamma
            worst = min(worst, val)
            if val < -tol:
                extra.append(c)           # already a column; this only sends the LP round again
    for n, r in reduced.items():
        # the phase's own composition(s), plus the corners, so that a new phase or a solvus split is seen
        starts = [ph.prop[r.keep] for ph in phases if ph.name == n] + best_q.get(n, [])[-3:]
        starts += _random_starts(r, 1, rng)
        for val, q in sorted(_driving_force_min(r, gamma, t, p, starts, rng), key=lambda z: z[0])[:2]:
            worst = min(worst, val)
            if val < -tol:
                extra.append((n, q, q @ r.comp, r.g(q, t, p)))
    return worst, extra


def _polish(phases, reduced, bulk, gamma, t, p, max_iter: int = 80, o2_mu: float | None = None):
    """Newton solve of the exact equilibrium on the assemblage found by the LP.

    Unknowns: moles of every end member of every solution phase, moles of each pure phase, and gamma.
    Equations: mu_i = c_i . gamma for every end member and pure phase, and mass balance.  Returns
    (phases, gamma, oxygen given up), or None if it does not converge (the LP answer is then kept).
    With o2_mu, oxygen is open: one more unknown (O moved out to the reservoir) and one more equation
    (2 gamma_O = mu_O2).
    """
    present = bulk > 1e-10
    io = COMPONENTS.index("O")
    if o2_mu is not None:
        present = present.copy()
        present[io] = True
    jo = int(present[:io].sum())         # position of O among the present components
    nc = int(present.sum())
    blocks = []                   # (kind, name, reduced or None, size)
    x0 = []
    for ph in phases:
        if ph.prop is None:
            blocks.append(("pure", ph.name, None, 1))
            x0.append([ph.amount])
        else:
            # a solution phase is carried as log(amount) and its proportions, so that a trace phase
            # (a little spinel) is as easy to solve as a major one; proportions that can never be
            # negative are carried as logarithms too
            r = reduced[ph.name]
            blocks.append(("ss", ph.name, r, len(r.keep) + 1))
            q = ph.prop[r.keep] / ph.prop[r.keep].sum()
            z = np.where(r.positive, np.log(np.maximum(q, 1e-14)), q)
            x0.append(np.concatenate([[np.log(max(ph.amount, 1e-30))], z]))
    x = np.concatenate(x0 + [gamma[present]] + ([[0.0]] if o2_mu is not None else []))
    nvar = len(x)
    b = bulk[present]

    # layout of x and of the residual: one proportion-sum row per solution phase, then each phase's
    # rows (one per end member, or one for a pure phase), then the O2 row (open oxygen), then mass balance
    n_ss = sum(1 for kind, *_ in blocks if kind == "ss")
    var0, row0, sum_row, comp = [], [], [], []
    v, row, k_ss = 0, n_ss, 0
    for (kind, name, r, size), ph in zip(blocks, phases):
        var0.append(v)
        row0.append(row)
        v += size
        if kind == "ss":
            sum_row.append(k_ss)
            k_ss += 1
            row += len(r.keep)
            comp.append(r.comp[:, present])
        else:
            sum_row.append(None)
            row += 1
            comp.append(ph.composition[present])
    gam0 = v
    o2_row = row if o2_mu is not None else None
    mass0 = row + (1 if o2_mu is not None else 0)
    nrow = mass0 + nc
    pure_g = {ph.name: ph.g for ph in phases if ph.prop is None}

    def ss_part(r, v):
        """(proportion-sum residual, mu, moles of components) of a solution phase from its unknowns."""
        q = np.where(r.positive, np.exp(np.minimum(v[1:], 50.0)), v[1:])
        n = np.exp(min(v[0], 50.0)) * q
        tot = n.sum()
        if tot <= 0:
            return None
        qn = n / tot
        if not r.feasible(qn) or np.any(r.a_used @ qn <= 0):
            return None
        mu = r.mu(qn, t, p)
        if not np.all(np.isfinite(mu)):
            return None
        return q.sum() - 1.0, mu, n

    def unpack(x):
        out = []
        for (kind, name, r, size), k in zip(blocks, var0):
            v = x[k:k + size]
            if kind == "ss":
                q = np.where(r.positive, np.exp(np.minimum(v[1:], 50.0)), v[1:])
                v = np.exp(min(v[0], 50.0)) * q
            out.append(v)
        return out, x[gam0:gam0 + nc]

    def residual(x, keep=None):
        """The residual vector, or None; `keep` (a list) receives each phase's ss_part for the Jacobian."""
        gam = x[gam0:gam0 + nc]
        f = np.empty(nrow)
        mass = np.zeros(nc)
        for i, (kind, name, r, size) in enumerate(blocks):
            v, c, r0 = x[var0[i]:var0[i] + size], comp[i], row0[i]
            if kind == "pure":
                f[r0] = pure_g[name] - c @ gam
                mass += v[0] * c
                part = None
            else:
                part = ss_part(r, v)
                if part is None:
                    return None
                s_, mu, n = part
                f[sum_row[i]] = s_
                f[r0:r0 + len(mu)] = mu - c @ gam
                mass += n @ c
            if keep is not None:
                keep.append(part)
        if o2_mu is not None:
            mass[jo] += x[-1]
            f[o2_row] = 2.0 * gam[jo] - o2_mu
        f[mass0:] = mass - b
        return f if np.all(np.isfinite(f)) else None

    def jacobian(x, parts):
        """d residual / d x.  Only a solution phase's own unknowns move its mu, so each column is a
        finite difference of that one phase (not of the whole residual); the rest is linear and exact."""
        jac = np.zeros((nrow, nvar))
        for i, (kind, name, r, size) in enumerate(blocks):
            c, r0, k0 = comp[i], row0[i], var0[i]
            if kind == "pure":
                jac[r0, gam0:gam0 + nc] = -c
                jac[mass0:, k0] = c
                continue
            m = len(r.keep)
            jac[r0:r0 + m, gam0:gam0 + nc] = -c
            s_, mu, n = parts[i]
            mass = n @ c
            v = x[k0:k0 + size]
            for j in range(size):
                h = 1e-7 * max(1.0, abs(v[j]))
                vp = v.copy()
                vp[j] += h
                part = ss_part(r, vp)
                if part is None:
                    vp[j] -= 2 * h
                    part = ss_part(r, vp)
                    if part is None:
                        return None
                    h = -h
                jac[sum_row[i], k0 + j] = (part[0] - s_) / h
                jac[r0:r0 + m, k0 + j] = (part[1] - mu) / h
                jac[mass0:, k0 + j] = (part[2] @ c - mass) / h
        if o2_mu is not None:
            jac[o2_row, gam0 + jo] = 2.0
            jac[mass0 + jo, nvar - 1] = 1.0
        return jac

    parts = []
    f = residual(x, parts)
    if f is None:
        return None
    for _ in range(max_iter):
        if np.max(np.abs(f)) < 1e-7:
            break
        jac = jacobian(x, parts)
        if jac is None:
            return None
        try:
            dx = np.linalg.lstsq(jac, -f, rcond=None)[0]
        except np.linalg.LinAlgError:
            return None
        step, norm0 = 1.0, np.linalg.norm(f)
        while step > 1e-8:
            new_parts = []
            fn = residual(x + step * dx, new_parts)
            if fn is not None and np.linalg.norm(fn) < norm0:
                break
            step *= 0.5
        else:
            return None
        x, f, parts = x + step * dx, fn, new_parts
    if np.max(np.abs(f)) > 1e-5:
        return None
    parts, gam = unpack(x)
    if any(n.sum() < -1e-9 for (kind, *_), n in zip(blocks, parts) if kind == "pure"):
        return None
    out = []
    for (kind, name, r, size), n, ph in zip(blocks, parts, phases):
        if kind == "pure":
            out.append(Phase(name, float(n[0]), None, ph.end_members, ph.composition, ph.g))
        else:
            tot = float(n.sum())
            q = n / tot
            out.append(Phase(name, tot, r.full(q), r.s.names, q @ r.comp, r.g(q, t, p)))
    if any(ph.amount < 0 for ph in out):
        return None
    gamma = np.zeros(len(COMPONENTS))
    gamma[present] = gam
    return out, gamma, (float(x[-1]) if o2_mu is not None else 0.0)


def _collect(cols, x, reduced, t, p, merge: float = 0.03) -> list:
    """Active columns to phases; columns of one phase closer than `merge` in composition are combined."""
    groups = {}
    for k in np.where(x > 1e-10)[0]:
        n, q, c, g = cols[k]
        groups.setdefault(n, []).append((x[k], q, c, g))
    out = []
    for n, items in groups.items():
        if items[0][1] is None:
            amt = sum(i[0] for i in items)
            out.append(Phase(n, amt, None, (n,), items[0][2], items[0][3]))
            continue
        r = reduced[n]
        clusters = []
        for amt, q, c, g in sorted(items, key=lambda i: -i[0]):
            for cl in clusters:
                if n in ("liq",) or np.max(np.abs(cl["q"] - q)) < merge:
                    tot = cl["amt"] + amt
                    cl["q"] = (cl["q"] * cl["amt"] + q * amt) / tot
                    cl["amt"] = tot
                    break
            else:
                clusters.append({"amt": amt, "q": q.copy()})
        for cl in clusters:
            q = cl["q"]
            out.append(Phase(n, cl["amt"], r.full(q), r.s.names, q @ r.comp, r.g(q, t, p)))
    return out
