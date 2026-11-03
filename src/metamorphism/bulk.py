"""A rock's bulk composition for the solver: oxide wt% in, moles of the core's components out.

The core works in twelve components (``protolith.core.hp.minimize.COMPONENTS``): SiO2, Al2O3, CaO, MgO,
FeO, K2O, Na2O, TiO2, O, Cr2O3, H2O, MnO.  Iron is all FeO, with O the oxygen in excess of FeO (one O per
Fe2O3), so the rock keeps the ferric iron it started with: the system is closed to oxygen.

Which oxides the solver can use depends on the phase set: the metapelite set of White et al. (2014,
the default) is MnNCKFMASHTO, so it takes MnO and has no Cr2O3; the igneous set takes Cr2O3 and no MnO.
The others (NiO, CoO, P2O5, CO2 and whichever of MnO / Cr2O3 the set lacks) are left out and listed,
never dropped silently.

Water: ``"bulk"`` uses the H2O in the analysis, so a rock can be water-undersaturated; ``"excess"`` adds
water until a free fluid is present at every point, the usual setting for prograde metamorphism.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from protolith.core.hp.minimize import COMPONENTS

# g/mol, from the IUPAC 2013 atomic weights (Si 28.085, Al 26.982, Ca 40.078, Mg 24.305, Fe 55.845,
# K 39.098, Na 22.990, Ti 47.867, Cr 51.996, Mn 54.938, P 30.974, C 12.011, Ni 58.693, Co 58.933,
# O 15.999, H 1.008)
MOLAR_MASS = {
    "SiO2": 60.083, "TiO2": 79.865, "Al2O3": 101.961, "Fe2O3": 159.687, "Cr2O3": 151.989, "FeO": 71.844,
    "MnO": 70.937, "MgO": 40.304, "NiO": 74.692, "CoO": 74.932, "CaO": 56.077, "Na2O": 61.979,
    "K2O": 94.195, "P2O5": 141.943, "H2O": 18.015, "CO2": 44.009,
}
COMPONENT_MASS = np.array([15.999 if c == "O" else MOLAR_MASS[c] for c in COMPONENTS])
SYSTEMS = ("metapelite", "igneous")
LEFT_OUT = {"metapelite": ("Cr2O3", "NiO", "CoO", "P2O5", "CO2"),
            "igneous": ("MnO", "NiO", "CoO", "P2O5", "CO2")}
WATER_MODES = ("bulk", "excess")
_I = {c: i for i, c in enumerate(COMPONENTS)}


@dataclass
class Bulk:
    """A rock for the solver: moles of COMPONENTS in 100 g of the analysis as given (left-out oxides
    count toward the 100 g, so grams of phases add to 100 less what was left out)."""
    moles: np.ndarray
    wt_pct: dict[str, float]                    # the analysis, normalized to 100
    left_out: dict[str, float] = field(default_factory=dict)    # wt% of oxides the solver cannot use
    water: str = "bulk"
    name: str = ""
    system: str = "metapelite"                  # the phase set: "metapelite" or "igneous"

    @property
    def grams(self) -> float:
        return grams(self.moles)


def from_wt_pct(wt: dict[str, float], water: str = "bulk", name: str = "", system: str = "metapelite") -> Bulk:
    """A Bulk from oxide wt% (any total; normalized to 100).  Iron may be given as FeO, Fe2O3 or both."""
    if water not in WATER_MODES:
        raise ValueError(f"water must be one of {', '.join(WATER_MODES)}")
    if system not in SYSTEMS:
        raise ValueError(f"the phase set must be one of {', '.join(SYSTEMS)}")
    unknown = sorted(set(wt) - set(MOLAR_MASS))
    if unknown:
        raise ValueError(f"unknown oxide(s): {', '.join(unknown)}")
    if any(float(v) < 0 for v in wt.values()):
        raise ValueError("an oxide amount is negative")
    total = sum(float(v) for v in wt.values())
    if total <= 0:
        raise ValueError("the composition is empty")
    norm = {ox: 100.0 * float(v) / total for ox, v in wt.items() if float(v) > 0}
    n = {ox: v / MOLAR_MASS[ox] for ox, v in norm.items()}
    left = {ox: v for ox, v in norm.items() if ox in LEFT_OUT[system]}
    m = np.zeros(len(COMPONENTS))
    for c in COMPONENTS:
        if c not in ("FeO", "O") and c not in left:
            m[_I[c]] = n.get(c, 0.0)
    m[_I["FeO"]] = n.get("FeO", 0.0) + 2.0 * n.get("Fe2O3", 0.0)
    m[_I["O"]] = n.get("Fe2O3", 0.0)
    if not (m > 0).any() or m[_I["SiO2"]] <= 0 and m[_I["Al2O3"]] <= 0:
        raise ValueError("the composition has none of the rock-forming oxides the solver uses")
    return Bulk(m, norm, left, water, name, system)


def solver_moles(b: Bulk, scale: float = 1.0) -> np.ndarray:
    """The moles the solver is given.  With water in excess, H2O is raised to `scale` times the larger of
    the rock's own water and half its moles of the other components (far more than any hydrous assemblage
    holds), so a fluid is always left over."""
    m = b.moles.copy()
    if b.water == "excess":
        dry = m.sum() - m[_I["H2O"]]
        m[_I["H2O"]] = scale * max(m[_I["H2O"]], 0.5 * dry)
    return m


def grams(moles: np.ndarray) -> float:
    return float(np.asarray(moles) @ COMPONENT_MASS)


def to_wt_pct(moles: np.ndarray) -> dict[str, float]:
    """Oxide wt% (normalized) of moles of COMPONENTS, ferric iron as Fe2O3."""
    moles = np.asarray(moles, float)
    g = {}
    for c in COMPONENTS:
        if c not in ("FeO", "O") and moles[_I[c]] > 1e-12:
            g[c] = moles[_I[c]] * MOLAR_MASS[c]
    fe2o3 = max(moles[_I["O"]], 0.0)
    feo = max(moles[_I["FeO"]] - 2.0 * fe2o3, 0.0)
    if feo > 1e-12:
        g["FeO"] = feo * MOLAR_MASS["FeO"]
    if fe2o3 > 1e-12:
        g["Fe2O3"] = fe2o3 * MOLAR_MASS["Fe2O3"]
    s = sum(g.values())
    return {ox: 100.0 * v / s for ox, v in g.items()} if s > 0 else {}


# Starting rocks for trying the module out.  "pelite" and "metabasite" are rounded, typical compositions
# (not a published analysis): a shale-derived pelite and a MORB-like basalt, each with the water of a
# hydrated protolith.  "world median pelite" is Forshaw and Pattison (2023), the default bulk of MAGEMin's
# metapelite set, here as wt% from its moles (with the Fe2O3 of its O and without its excess water).
PRESETS = {
    "pelite": {"SiO2": 59.8, "TiO2": 0.8, "Al2O3": 16.6, "FeO": 6.0, "Fe2O3": 0.6, "MnO": 0.1, "MgO": 2.6,
               "CaO": 1.1, "Na2O": 1.7, "K2O": 3.7, "H2O": 6.0},
    "metabasite": {"SiO2": 50.1, "TiO2": 1.3, "Al2O3": 14.9, "FeO": 9.0, "Fe2O3": 1.5, "MgO": 7.6,
                   "CaO": 11.4, "Na2O": 2.6, "K2O": 0.2, "H2O": 4.0},
}
_FPWM_MOL = {"SiO2": 70.999, "Al2O3": 12.8065, "CaO": 0.771, "MgO": 3.978, "FeO": 6.342, "K2O": 2.7895,
             "Na2O": 1.481, "TiO2": 0.758, "O": 0.72933, "MnO": 0.075}
PRESETS["world median pelite"] = {
    **{ox: n * MOLAR_MASS[ox] for ox, n in _FPWM_MOL.items() if ox not in ("FeO", "O")},
    "FeO": (_FPWM_MOL["FeO"] - 2 * _FPWM_MOL["O"]) * MOLAR_MASS["FeO"],
    "Fe2O3": _FPWM_MOL["O"] * MOLAR_MASS["Fe2O3"],
    "H2O": 5.0 * MOLAR_MASS["H2O"],
}
