"""Magma results as samples: one step of a crystallization or melting run, written as a ``Sample``.

Works for both of Magma's engines.  The Holland & Powell engine gives each phase's oxide moles directly;
the MELTS engine gives end-member moles, turned into oxides with that end member's stoichiometry.
"""
from __future__ import annotations

from magma import __version__ as magma_version
from magma.composition import MOLAR_MASS
from magma.hp import engine as hp_engine
from magma.thermo.phases import OXIDES_OF

from .sample import Phase, Sample, mix, normalized

HP_DATASET = "Holland and Powell (2011) dataset ds636, solution models of Holland, Green and Powell (2018)"
MELTS_DATASET = "MELTS (Ghiorso and Sack 1995; Berman 1988 minerals), parameter values from ThermoEngine"
FLUID_NAMES = ("water", "fluid")


def _melts_oxides(moles: dict[str, float]) -> dict[str, float]:
    """Grams of each oxide in a MELTS-engine phase, from its end-member moles."""
    out: dict[str, float] = {}
    for em, n in moles.items():
        for ox, k in OXIDES_OF[em].items():
            out[ox] = out.get(ox, 0.0) + n * k * MOLAR_MASS[ox]
    return out


def phase_of(s) -> Phase:
    """One Magma solid (either engine) as a sample phase."""
    if isinstance(s, hp_engine.HPPhase):
        wt = dict(hp_engine.to_composition(s.oxide_moles).wt)
        model = f"HP {s.hp}" if s.hp else "HP"
        formula = s.formula
    else:
        wt = normalized(_melts_oxides(s.moles))
        model = f"MELTS {s.name}"
        formula = ""
    return Phase(name=s.name, grams=float(s.grams), wt_pct=wt, end_members={k: float(v) for k, v in s.x.items()},
                 formula=formula, model=model)


def step_phases(result) -> tuple[list[Phase], dict | None]:
    """(the solids, the fluid or None) of one Magma step."""
    phases, fluid = [], None
    for s in result.solids:
        if s.grams <= 0:
            continue
        p = phase_of(s)
        if p.name in FLUID_NAMES:
            fluid = {"grams": p.grams, "wt_pct": p.wt_pct}
        else:
            phases.append(p)
    return phases, fluid


def merge(a: list[Phase], b: list[Phase]) -> list[Phase]:
    """Phases of two piles together, one row per name: grams add, compositions mix by mass (the solids of
    fractional crystallization, removed step by step, piled up as a cumulate)."""
    out = {p.name: Phase(p.name, p.grams, dict(p.wt_pct), dict(p.end_members), p.formula, p.model) for p in a}
    for p in b:
        if p.name not in out:
            out[p.name] = Phase(p.name, p.grams, dict(p.wt_pct), dict(p.end_members), p.formula, p.model)
            continue
        q = out[p.name]
        g = q.grams + p.grams
        if g > 0:
            q.wt_pct = mix([(q.grams, q.wt_pct), (p.grams, p.wt_pct)])
            keys = set(q.end_members) | set(p.end_members)
            q.end_members = {k: (q.grams * q.end_members.get(k, 0.0) + p.grams * p.end_members.get(k, 0.0)) / g
                             for k in keys}
            q.formula = ""                    # a pile of zoned crystals has no one formula
        q.grams = g
    return sorted(out.values(), key=lambda p: -p.grams)


def from_step(result, *, fo2=None, run: dict | None = None, note: str = "", parent: str | None = None,
              keep_melt: bool = True, solids: list[Phase] | None = None, melt: dict | None = None) -> Sample:
    """A sample of one step of a Magma run (an ``HPResult`` or an ``EquilibriumResult``).

    ``keep_melt`` False keeps only the solids (the rock left after the melt is extracted).  ``solids``
    replaces the step's own solids (the cumulate of a fractional run); ``melt`` replaces its melt (the
    pooled melt of fractional melting), as {"grams", "wt_pct"}."""
    hp = isinstance(result, hp_engine.HPResult)
    phases, fluid = step_phases(result)
    if solids is not None:
        phases = solids
    if melt is None and result.liquid is not None and result.liquid_grams > 1e-9:
        melt = {"grams": float(result.liquid_grams), "wt_pct": normalized(dict(result.liquid.wt))}
    if not keep_melt:
        melt = None
    parts = [(p.grams, p.wt_pct) for p in phases]
    if melt:
        parts.append((melt["grams"], melt["wt_pct"]))
    if fluid:
        parts.append((fluid["grams"], fluid["wt_pct"]))
    total = sum(g for g, _ in parts)
    log_fo2 = getattr(result, "log_fo2", None)
    return Sample(
        conditions={"t_c": float(result.t_c), "p_bar": float(result.p_bar),
                    "fo2": fo2 if isinstance(fo2, str) else None,
                    "log_fo2": float(log_fo2) if log_fo2 is not None else None},
        bulk_wt_pct=mix(parts), total_grams=float(total), phases=phases, melt=melt, fluid=fluid,
        provenance={"engine": "hp" if hp else "melts", "dataset": HP_DATASET if hp else MELTS_DATASET,
                    "run": run or {}},
        note=note, written_by={"app": "Magma", "version": magma_version}, parent=parent)
