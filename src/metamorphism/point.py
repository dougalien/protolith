"""One equilibrium: the stable assemblage of a rock at T and P, reported as minerals.

``equilibrium`` runs the core's Gibbs energy minimizer (``protolith.core.hp.minimize.equilibrate``) on the
rock's components and turns its phases into ``Mineral`` rows: the mineral's name, its grams and mode,
its own oxide composition, end-member fractions, structural formula and the usual numbers (An, Mg#,
garnet end members).  The melt is a row too (``Liq``) when the point is above the solidus; the fluid
is kept apart, since with water in excess its amount means nothing.

Modes are wt% of the rock without its free fluid (solids plus any melt).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from protolith.core.hp.minimize import COMPONENTS, PHASE_SETS, Result, equilibrate

from . import names
from .bulk import Bulk, grams, solver_moles, to_wt_pct

FLUIDS = ("fl", "H2O")      # the igneous set's fluid model, the metapelite set's pure water
TRACE_WT = 0.01        # wt% of the rock; a phase below this is listed as a trace and left out of the label


@dataclass
class Mineral:
    abbr: str                     # Whitney and Evans (2010), e.g. "Grt"
    name: str                     # "garnet"
    hp: str                       # the core's phase it came from, e.g. "g"
    grams: float                  # per 100 g of the analysis
    mode: float                   # wt% of the rock without its free fluid
    wt_pct: dict[str, float]      # its own oxide composition
    end_members: dict[str, float] = field(default_factory=dict)
    formula: str = ""
    numbers: dict[str, float] = field(default_factory=dict)
    oxide_moles: list = field(default_factory=list)    # moles of COMPONENTS in this mineral


@dataclass
class Point:
    t_c: float
    p_kbar: float
    minerals: list                # Mineral, by mode, largest first (the melt included)
    fluid: Mineral | None
    traces: list                  # Mineral below TRACE_WT
    converged: bool
    max_driving_force: float      # kJ; how far from equilibrium the worst phase left out is (>= -tol)
    g: float                      # total G, kJ
    water: str
    raw: Result | None = None     # the solver's answer, for a warm start at the next point

    @property
    def assemblage(self) -> tuple:
        """Abbreviations of every phase present, in label order (the fluid as H2O, a solvus pair twice)."""
        a = [m.abbr for m in self.minerals] + (["H2O"] if self.fluid is not None else [])
        return tuple(sorted(a, key=lambda x: names.ORDER.get(x, 99)))

    @property
    def label(self) -> str:
        return names.label(self.assemblage)

    @property
    def melt(self) -> Mineral | None:
        return next((m for m in self.minerals if m.abbr == "Liq"), None)

    def light(self) -> "Point":
        """The same point without the solver's internals (for storing many points)."""
        d = dict(self.__dict__)
        d["raw"] = None
        return Point(**d)

    def to_dict(self) -> dict:
        d = asdict(self.light())
        d.pop("raw")
        d["assemblage"] = list(self.assemblage)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Point":
        d = dict(d)
        d.pop("assemblage", None)
        d["minerals"] = [Mineral(**m) for m in d["minerals"]]
        d["traces"] = [Mineral(**m) for m in d.get("traces", [])]
        d["fluid"] = Mineral(**d["fluid"]) if d.get("fluid") else None
        return cls(**d)


def _mineral(ph) -> Mineral:
    c = ph.composition
    if ph.prop is None:
        x = {ph.name: 1.0}
    else:
        x = {e: float(v) for e, v in zip(ph.end_members, ph.prop) if abs(v) > 1e-10}
    abbr = names.abbreviation(ph.name, x, c)
    m = ph.oxide_moles
    return Mineral(abbr, names.MINERALS.get(abbr, ph.name), ph.name, grams(m), 0.0, to_wt_pct(m), x,
                   names.formula(ph.name, c), names.numbers(ph.name, c), [float(v) for v in m])


def wrap(r: Result, water: str) -> Point:
    """The solver's Result as a Point."""
    rows = [_mineral(ph) for ph in r.phases]
    fluid_rows = [m for m in rows if m.hp in FLUIDS]
    rock = [m for m in rows if m.hp not in FLUIDS]
    fluid = None
    if fluid_rows:
        om = np.sum([np.array(m.oxide_moles) for m in fluid_rows], axis=0)
        fluid = Mineral("H2O", "water", fluid_rows[0].hp, grams(om), 0.0, to_wt_pct(om),
                        fluid_rows[0].end_members, "", {}, [float(v) for v in om])
    total = sum(m.grams for m in rock)
    for m in rock:
        m.mode = 100.0 * m.grams / total if total > 0 else 0.0
    rock.sort(key=lambda m: -m.grams)
    kept = [m for m in rock if m.mode >= TRACE_WT]
    traces = [m for m in rock if m.mode < TRACE_WT]
    return Point(round(r.t - 273.15, 6), round(r.p, 6), kept, fluid, traces, bool(r.converged),
                 float(r.max_driving_force), float(r.g), water, r)


def equilibrium(bulk: Bulk, t_c: float, p_kbar: float, previous: Point | None = None,
                phases=None, seed: int = 0) -> Point:
    """The stable assemblage of `bulk` at t_c (degC) and p_kbar.

    previous: the answer at a nearby point; its assemblage is tried first (much faster along a path).
    phases: the core's solution phases to allow (default: all of the bulk's phase set; pure phases are always
    on).  The phase set is the bulk's (``Bulk.system``).  With water in excess, a point that
    comes out without a fluid is solved again with three times the water."""
    if p_kbar <= 0:
        raise ValueError("pressure must be above zero")
    if t_c + 273.15 < 300:
        raise ValueError("temperature must be above 27 C")
    raw_prev = previous.raw if previous is not None else None
    system = PHASE_SETS[bulk.system]
    phases = None if phases is None else tuple(phases)
    r = equilibrate(solver_moles(bulk), t_c + 273.15, p_kbar, phases=phases, previous=raw_prev, seed=seed,
                    system=system)
    pt = wrap(r, bulk.water)
    if bulk.water == "excess" and pt.fluid is None:
        r = equilibrate(solver_moles(bulk, 3.0), t_c + 273.15, p_kbar, phases=phases, seed=seed, system=system)
        pt = wrap(r, bulk.water)
    return pt


def components_present(bulk: Bulk) -> int:
    """Number of components in the system (for the phase rule): those the solver is given."""
    m = solver_moles(bulk)
    return int(np.sum(m > 1e-10))


__all__ = ["Mineral", "Point", "equilibrium", "wrap", "components_present", "COMPONENTS"]
