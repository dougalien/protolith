"""A sample's solids as reactants for Reaction's card.

Reaction's card takes minerals by its database names (forsterite, anorthite, K-feldspar ...), in grams.
Each sample phase is recast onto a short list of Reaction minerals chosen for that phase (olivine onto
forsterite, fayalite and monticellite; plagioclase onto anorthite, albite and K-feldspar, and so on) by a
non-negative least-squares fit on its cations.  This uses only the phase's oxide composition, so it is the
same for both of Magma's engines and does not depend on how either solution model chooses end members.

Nothing is dropped silently.  Whatever part of a phase the chosen minerals cannot hold (titanium today,
since Reaction's database has no Ti minerals; manganese; a phase with no counterpart at all) is listed in
``Recast.left_over`` with its grams of oxide and a sentence for the card.  Closing those gaps (rutile,
ilmenite, titanite and ulvospinel from the Holland and Powell dataset, with aqueous Ti fitted to rutile
solubility) is the next step of the shared-data plan.

Mineral formulas are the ideal end-member formulas; ``tests/protolith/test_reaction_link.py`` checks each
against Reaction's own database when that data is installed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

import numpy as np
from scipy.optimize import nnls

from .sample import Phase, Sample

ATOMIC_WEIGHT = {"H": 1.00794, "O": 15.9994, "Na": 22.98976928, "Mg": 24.305, "Al": 26.9815386,
                 "Si": 28.0855, "P": 30.973762, "K": 39.0983, "Ca": 40.078, "Ti": 47.867, "Cr": 51.9961,
                 "Mn": 54.938045, "Fe": 55.845, "Ni": 58.6934, "Co": 58.933195, "C": 12.0107}
OXIDE_CATION = {"SiO2": ("Si", 1, 2), "TiO2": ("Ti", 1, 2), "Al2O3": ("Al", 2, 3), "Fe2O3": ("Fe", 2, 3),
                "Cr2O3": ("Cr", 2, 3), "FeO": ("Fe", 1, 1), "MnO": ("Mn", 1, 1), "MgO": ("Mg", 1, 1),
                "NiO": ("Ni", 1, 1), "CoO": ("Co", 1, 1), "CaO": ("Ca", 1, 1), "Na2O": ("Na", 2, 1),
                "K2O": ("K", 2, 1), "P2O5": ("P", 2, 5), "H2O": ("H", 2, 1), "CO2": ("C", 1, 2)}
CATIONS = ("Si", "Ti", "Al", "Fe", "Cr", "Mn", "Mg", "Ca", "Na", "K", "P", "Ni", "Co")

# Reaction database minerals used here, as ideal formulas (Reaction's names)
FORMULAS = {
    "forsterite": "Mg2SiO4", "fayalite": "Fe2SiO4", "monticellite": "CaMgSiO4",
    "anorthite": "CaAl2Si2O8", "albite": "NaAlSi3O8", "K-feldspar": "KAlSi3O8",
    "diopside": "CaMgSi2O6", "hedenbergite": "CaFeSi2O6", "enstatite": "MgSiO3", "ferrosilite": "FeSiO3",
    "jadeite": "NaAlSi2O6", "Ca-Al-pyroxene": "CaAl2SiO6",
    "spinel": "MgAl2O4", "magnetite": "Fe3O4", "chromite": "FeCr2O4", "hematite": "Fe2O3",
    "pyrope": "Mg3Al2Si3O12", "almandine": "Fe3Al2Si3O12", "grossular": "Ca3Al2Si3O12",
    "andradite": "Ca3Fe2Si3O12",
    "quartz": "SiO2", "coesite": "SiO2",
    "tremolite": "Ca2Mg5Si8O24H2", "pargasite": "NaCa2Mg4Al3Si6O24H2", "glaucophane": "Na2Mg3Al2Si8O24H2",
    "grunerite": "Fe7Si8O24H2",
    "phlogopite": "KMg3AlSi3O12H2", "annite": "KFe3AlSi3O12H2", "muscovite": "KAl3Si3O12H2",
    "paragonite": "NaAl3Si3O12H2",
    "cordierite": "Mg2Al4Si5O18", "clinozoisite": "Ca2Al3Si3O13H", "epidote": "Ca2FeAl2Si3O13H",
    "clinochlore": "Mg5Al2Si3O18H8", "daphnite": "Fe5Al2Si3O18H8",
    "kyanite": "Al2SiO5", "sillimanite": "Al2SiO5", "andalusite": "Al2SiO5", "corundum": "Al2O3",
    "nepheline": "NaAlSiO4", "kalsilite": "KAlSiO4", "hydroxyapatite": "Ca5P3O13H",
}

_PX = ("diopside", "hedenbergite", "enstatite", "ferrosilite", "jadeite", "Ca-Al-pyroxene", "K-feldspar")
_SPL = ("spinel", "magnetite", "chromite", "hematite")
# sample phase name -> the Reaction minerals it is recast onto
RECIPES = {
    "olivine": ("forsterite", "fayalite", "monticellite"),
    "feldspar": ("anorthite", "albite", "K-feldspar"), "alkali-feldspar": ("anorthite", "albite", "K-feldspar"),
    "plagioclase": ("anorthite", "albite", "K-feldspar"),
    "clinopyroxene": _PX[:-1], "pigeonite": _PX[:-1], "orthopyroxene": _PX[:-1],
    "spinel": _SPL, "titanomagnetite": _SPL, "rhombohedral": ("hematite", "magnetite"),
    "garnet": ("pyrope", "almandine", "grossular", "andradite"),
    "hornblende": ("tremolite", "pargasite", "glaucophane", "grunerite", "K-feldspar"),
    "biotite": ("phlogopite", "annite", "muscovite"),
    "muscovite": ("muscovite", "paragonite", "phlogopite", "annite"),
    "cordierite": ("cordierite", "spinel", "quartz"), "epidote": ("clinozoisite", "epidote"),
    "chlorite": ("clinochlore", "daphnite"),
    "quartz": ("quartz",), "coesite": ("coesite",), "kyanite": ("kyanite",), "sillimanite": ("sillimanite",),
    "andalusite": ("andalusite",), "corundum": ("corundum",), "nepheline": ("nepheline", "kalsilite"),
    "apatite": ("hydroxyapatite",),
}
# phases Reaction has only as a polymorph: carried as that mineral, and the card says so
STAND_INS = {"tridymite": "quartz", "cristobalite": "quartz", "stishovite": "quartz"}

TOLERANCE = 0.005          # a left-over cation share of the phase below this is rounding, not a gap


def parse_formula(f: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for el, n in re.findall(r"([A-Z][a-z]?)(\d*\.?\d*)", f):
        out[el] = out.get(el, 0.0) + (float(n) if n else 1.0)
    return out


def molar_mass(f: str) -> float:
    return sum(ATOMIC_WEIGHT[el] * n for el, n in parse_formula(f).items())


def cation_moles(wt: dict[str, float], grams: float) -> dict[str, float]:
    """Moles of each cation in ``grams`` of a phase of oxide composition ``wt``."""
    s = sum(wt.values())
    out: dict[str, float] = {}
    for ox, v in wt.items():
        el, k, o = OXIDE_CATION[ox]
        mm = k * ATOMIC_WEIGHT[el] + o * ATOMIC_WEIGHT["O"]
        out[el] = out.get(el, 0.0) + grams * v / s / mm * k
    return out


@dataclass
class Recast:
    reactants: list[dict] = field(default_factory=list)        # [{"name", "amount", "unit": "g"}]
    by_phase: dict[str, dict[str, float]] = field(default_factory=dict)
    left_over: dict[str, dict[str, float]] = field(default_factory=dict)   # phase -> oxide -> grams
    notes: list[str] = field(default_factory=list)


def recast_phase(p: Phase) -> tuple[dict[str, float], dict[str, float], str]:
    """(grams of each Reaction mineral, grams of each oxide not carried, note) for one phase."""
    name = p.name.lower()
    note = ""
    if name in STAND_INS:
        m = STAND_INS[name]
        note = f"{p.name} goes on the card as {m}, the same composition (Reaction has no {p.name})"
        minerals = (m,)
    else:
        minerals = RECIPES.get(name, ())
    have = cation_moles(p.wt_pct, p.grams)
    if not minerals:
        left = {ox: p.grams * v / sum(p.wt_pct.values()) for ox, v in p.wt_pct.items()}
        return {}, left, (f"{p.name} ({p.grams:.3g} g) has no counterpart in Reaction's minerals yet, so it "
                          f"is not on the card")
    els = [e for e in CATIONS if e in have or any(e in parse_formula(FORMULAS[m]) for m in minerals)]
    a = np.array([[parse_formula(FORMULAS[m]).get(e, 0.0) for m in minerals] for e in els])
    b = np.array([have.get(e, 0.0) for e in els])
    n, _ = nnls(a, b)
    grams = {m: float(k * molar_mass(FORMULAS[m])) for m, k in zip(minerals, n) if k > 0}
    rest = b - a @ n
    total = b.sum()
    left = {}
    for e, r in zip(els, rest):
        if total > 0 and r / total > TOLERANCE:
            ox = next(o for o, (el, _k, _o) in OXIDE_CATION.items() if el == e and o not in ("Fe2O3",))
            el, k, o = OXIDE_CATION[ox]
            left[ox] = float(r / k * (k * ATOMIC_WEIGHT[el] + o * ATOMIC_WEIGHT["O"]))
    # minerals carry their ideal oxygen and water: scale so the reactants weigh what the phase did, less
    # what is left over
    carried = p.grams - sum(left.values())
    s = sum(grams.values())
    if s > 0 and carried > 0:
        grams = {m: g * carried / s for m, g in grams.items()}
    if left:
        what = ", ".join(f"{g:.3g} g {ox}" for ox, g in left.items())
        extra = f"Reaction has no mineral for this part of {p.name}: {what}"
        note = f"{note}; {extra}" if note else extra
    return grams, left, note


def to_reactants(sample: Sample, scale_to: float | None = None) -> Recast:
    """The sample's solids as Reaction reactants (grams), merged across phases.

    ``scale_to`` grams: rescale so the solids total that much (a water/rock ratio set on the card)."""
    out = Recast()
    total: dict[str, float] = {}
    f = scale_to / sample.solid_grams if scale_to and sample.solid_grams > 0 else 1.0
    for p in sample.phases:
        grams, left, note = recast_phase(replace(p, grams=p.grams * f))
        out.by_phase[p.name] = grams
        if left:
            out.left_over[p.name] = left
        if note:
            out.notes.append(note)
        for m, g in grams.items():
            total[m] = total.get(m, 0.0) + g
    out.reactants = [{"name": m, "amount": float(f"{g:.6g}"), "unit": "g"}
                     for m, g in sorted(total.items(), key=lambda kv: -kv[1]) if g > 0]
    if sample.melt:
        out.notes.append(f"the sample also holds {sample.melt['grams']:.3g} g of melt; to react it as glass, "
                         f"open it as a glass sample (coming next)")
    return out
