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


def from_step(result, *, fo2=None, run: dict | None = None, note: str = "", parent: str | None = None,
              keep_melt: bool = True) -> Sample:
    """A sample of one step of a Magma run (an ``HPResult`` or an ``EquilibriumResult``).

    ``keep_melt`` False keeps only the solids (the rock left after the melt is extracted)."""
    hp = isinstance(result, hp_engine.HPResult)
    phases, fluid = [], None
    for s in result.solids:
        if s.grams <= 0:
            continue
        p = phase_of(s)
        if p.name in FLUID_NAMES:
            fluid = {"grams": p.grams, "wt_pct": p.wt_pct}
        else:
            phases.append(p)
    melt = None
    if keep_melt and result.liquid is not None and result.liquid_grams > 1e-9:
        melt = {"grams": float(result.liquid_grams), "wt_pct": normalized(dict(result.liquid.wt))}
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
