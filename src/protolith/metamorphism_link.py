"""Samples in and out of Metamorphism.

``bulk_from_sample`` takes the rock to metamorphose from a ``.sample`` file (from Magma or Reaction):
the whole sample, the rock without its melt, or the melt alone (a melt crystallized at depth becomes the
protolith).  ``to_sample`` writes one point of a Metamorphism run (a single equilibrium or a cell of a
pseudosection) as a new sample, the source sample as its parent.
"""
from __future__ import annotations

from metamorphism import __version__ as metamorphism_version
from metamorphism.bulk import Bulk, from_wt_pct
from metamorphism.point import Point

from .sample import Phase, Sample, mix, rock_only

DATASETS = {
    "metapelite": "Holland and Powell (2011) dataset ds62; metapelite solution models of White et al. (2014)",
    "igneous": "Holland and Powell (2011) dataset ds636; solution models of Holland, Green and Powell (2018)",
}
PARTS = ("whole", "rock", "melt")


def bulk_from_sample(s: Sample, part: str = "whole", water: str = "bulk", system: str = "metapelite") -> Bulk:
    """The bulk composition to metamorphose, from a sample.

    part: "whole" (melt, solids and fluid together), "rock" (without the melt) or "melt" (the melt only).
    water: "bulk" keeps the sample's own water, "excess" keeps a free fluid at every point.
    system: the phase set, "metapelite" (White et al. 2014, with MnO) or "igneous"."""
    if part not in PARTS:
        raise ValueError(f"part must be one of {', '.join(PARTS)}")
    if part == "melt":
        if not s.melt:
            raise ValueError("this sample has no melt")
        wt = s.melt["wt_pct"]
    elif part == "rock":
        if not s.phases and not s.fluid:
            raise ValueError("this sample has no solids")
        wt = rock_only(s).bulk_wt_pct if s.melt else s.bulk_wt_pct
    else:
        wt = s.bulk_wt_pct
    name = s.note or (s.written_by or {}).get("app", "sample")
    return from_wt_pct(wt, water=water, name=f"{name} ({part})", system=system)


def _phase(m) -> Phase:
    return Phase(name=m.name, grams=float(m.grams), wt_pct=dict(m.wt_pct),
                 end_members={k: float(v) for k, v in m.end_members.items()}, formula=m.formula,
                 model=f"HP {m.hp}")


def to_sample(pt: Point, bulk: Bulk, *, parent: str | None = None, note: str = "", run: dict | None = None,
              keep_fluid: bool = True) -> Sample:
    """One point as a sample: its minerals as phases, its melt and fluid, grams per 100 g of the analysis.

    With water in excess the fluid is whatever water the solver needed to keep one; keep_fluid False
    leaves it out (the rock as it would be collected)."""
    phases = [_phase(m) for m in pt.minerals if m.abbr != "Liq"]
    liq = pt.melt
    melt = {"grams": float(liq.grams), "wt_pct": dict(liq.wt_pct)} if liq is not None else None
    fluid = ({"grams": float(pt.fluid.grams), "wt_pct": dict(pt.fluid.wt_pct)}
             if pt.fluid is not None and keep_fluid else None)
    parts = [(p.grams, p.wt_pct) for p in phases]
    if melt:
        parts.append((melt["grams"], melt["wt_pct"]))
    if fluid:
        parts.append((fluid["grams"], fluid["wt_pct"]))
    left = ", ".join(f"{ox} {v:.2f} wt%" for ox, v in bulk.left_out.items())
    notes = [note] if note else []
    notes.append(f"{pt.label} at {pt.t_c:g} C, {pt.p_kbar:g} kbar")
    if left:
        notes.append(f"left out by the solver: {left}")
    return Sample(
        conditions={"t_c": float(pt.t_c), "p_bar": float(pt.p_kbar) * 1000.0, "fo2": None, "log_fo2": None},
        bulk_wt_pct=mix(parts), total_grams=float(sum(g for g, _ in parts)), phases=phases, melt=melt,
        fluid=fluid,
        provenance={"engine": "hp", "dataset": DATASETS[bulk.system],
                    "run": {"module": "metamorphism", "water": bulk.water, "phase_set": bulk.system,
                            **(run or {})}},
        note="; ".join(notes), written_by={"app": "Metamorphism", "version": metamorphism_version},
        parent=parent)
