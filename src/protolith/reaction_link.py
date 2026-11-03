"""A sample's solids as reactants for Reaction's card.

Reaction's card takes minerals by its database names (forsterite, anorthite, K-feldspar ...), in grams.
Each sample phase is recast onto a short list of Reaction minerals chosen for that phase (olivine onto
forsterite, fayalite and monticellite; plagioclase onto anorthite, albite and K-feldspar, and so on) by a
non-negative least-squares fit on its cations.  This uses only the phase's oxide composition, so it is the
same for both of Magma's engines and does not depend on how either solution model chooses end members.

Nothing is dropped silently.  Whatever part of a phase the chosen minerals cannot hold (manganese, the
magnesium of geikielite, a phase with no counterpart at all) is listed in ``Recast.left_over`` with its
grams of oxide and a sentence for the card.  Titanium goes on as rutile, ilmenite or sphene (titanite),
which Reaction can react now that dissolved Ti is defined from rutile solubility
(``reaction/thermo/titanium.py``).

On Reaction's Holland & Powell data (``database="hp"``, Protolith's shared core) more of a rock goes on as
minerals: the ulvospinel and hercynite of a spinel, the geikielite and pyrophanite of an ilmenite, and
manganese as tephroite and spessartine.

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
    # titanium minerals: in Reaction's data once dissolved Ti is defined (reaction/thermo/titanium.py)
    "rutile": "TiO2", "ilmenite": "FeTiO3", "sphene": "CaTiSiO5",
}

_PX = ("diopside", "hedenbergite", "enstatite", "ferrosilite", "jadeite", "Ca-Al-pyroxene", "rutile")
_SPL = ("spinel", "magnetite", "chromite", "hematite", "ilmenite")     # ulvospinel's Ti as ilmenite
# sample phase name -> the Reaction minerals it is recast onto
RECIPES = {
    "olivine": ("forsterite", "fayalite", "monticellite"),
    "feldspar": ("anorthite", "albite", "K-feldspar"), "alkali-feldspar": ("anorthite", "albite", "K-feldspar"),
    "plagioclase": ("anorthite", "albite", "K-feldspar"),
    "clinopyroxene": _PX, "pigeonite": _PX, "orthopyroxene": _PX,
    "spinel": _SPL, "titanomagnetite": _SPL, "rhombohedral": ("ilmenite", "hematite", "magnetite", "rutile"),
    "garnet": ("pyrope", "almandine", "grossular", "andradite", "rutile"),
    "hornblende": ("tremolite", "pargasite", "glaucophane", "grunerite", "K-feldspar", "rutile"),
    "biotite": ("phlogopite", "annite", "muscovite", "rutile"),
    "muscovite": ("muscovite", "paragonite", "phlogopite", "annite"),
    "cordierite": ("cordierite", "spinel", "quartz"), "epidote": ("clinozoisite", "epidote"),
    "chlorite": ("clinochlore", "daphnite"),
    "quartz": ("quartz",), "coesite": ("coesite",), "kyanite": ("kyanite",), "sillimanite": ("sillimanite",),
    "andalusite": ("andalusite",), "corundum": ("corundum",), "nepheline": ("nepheline", "kalsilite"),
    "apatite": ("hydroxyapatite",), "rutile": ("rutile",), "sphene": ("sphene",), "titanite": ("sphene",),
}
# minerals Reaction has only on the Holland & Powell data (reaction/thermo/hp_minerals.py, HP_ONLY)
HP_FORMULAS = {"ulvospinel": "Fe2TiO4", "hercynite": "FeAl2O4", "geikielite": "MgTiO3",
               "pyrophanite": "MnTiO3", "tephroite": "Mn2SiO4", "spessartine": "Mn3Al2Si3O12"}
FORMULAS.update(HP_FORMULAS)
_SPL_HP = ("spinel", "hercynite", "magnetite", "ulvospinel", "chromite", "hematite")
HP_RECIPES = {
    "olivine": ("forsterite", "fayalite", "monticellite", "tephroite"),
    "spinel": _SPL_HP, "titanomagnetite": _SPL_HP,
    "rhombohedral": ("ilmenite", "geikielite", "pyrophanite", "hematite", "magnetite", "rutile"),
    "garnet": ("pyrope", "almandine", "grossular", "andradite", "spessartine", "rutile"),
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


def recipes(database: str = "current") -> dict[str, tuple[str, ...]]:
    """Sample phase -> the Reaction minerals it is recast onto, for Reaction's ``database``."""
    return {**RECIPES, **HP_RECIPES} if database == "hp" else RECIPES


def recast_phase(p: Phase, database: str = "current") -> tuple[dict[str, float], dict[str, float], str]:
    """(grams of each Reaction mineral, grams of each oxide not carried, note) for one phase."""
    name = p.name.lower()
    note = ""
    if name in STAND_INS:
        m = STAND_INS[name]
        note = f"{p.name} goes on the card as {m}, the same composition (Reaction has no {p.name})"
        minerals = (m,)
    else:
        minerals = recipes(database).get(name, ())
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


def to_reactants(sample: Sample, scale_to: float | None = None, database: str = "current") -> Recast:
    """The sample's solids as Reaction reactants (grams), merged across phases.

    ``scale_to`` grams: rescale so the solids total that much (a water/rock ratio set on the card)."""
    out = Recast()
    total: dict[str, float] = {}
    f = scale_to / sample.solid_grams if scale_to and sample.solid_grams > 0 else 1.0
    for p in sample.phases:
        grams, left, note = recast_phase(replace(p, grams=p.grams * f), database)
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


# ---- the whole card: solids as minerals, melt as glass ------------------------------------------------
TAKE = ("rock", "melt", "both")
MAX_ON_CARD = 12                 # Reaction's card holds at most this many reactants (scenario.MAX_REACTANTS)


def glass_oxides(wt: dict[str, float]) -> tuple[dict[str, float], float]:
    """(oxide wt% with total iron as FeO, Fe3+/total Fe by moles): the form Reaction's glasses take.
    Water is left with the sample's fluid."""
    feo, fe2o3 = wt.get("FeO", 0.0), wt.get("Fe2O3", 0.0)
    n2, n3 = feo / 71.8444, 2 * fe2o3 / 159.6882
    out = {ox: v for ox, v in wt.items() if ox not in ("FeO", "Fe2O3", "H2O") and v > 0}
    if n2 + n3 > 0:
        out["FeO"] = (n2 + n3) * 71.8444
    s = sum(out.values())
    out = {ox: float(f"{100 * v / s:.6g}") for ox, v in out.items()}
    return out, (n3 / (n2 + n3) if n2 + n3 > 0 else 0.0)


def glass_reactant(name: str, wt: dict[str, float], grams: float, source: str) -> dict:
    oxides, ff = glass_oxides(wt)
    return {"name": name, "amount": float(f"{grams:.6g}"), "unit": "g", "oxides": oxides,
            "ferric_fraction": float(f"{ff:.6g}"), "source": source}


def _t(sample: Sample) -> str:
    return f"{sample.conditions['t_c']:.0f} °C"


def card_for(sample: Sample, grams: float = 1000.0, take: str = "rock", database: str = "current") -> Recast:
    """Reactants for Reaction's card from a sample: ``take`` "rock" (the solids, as minerals), "melt" (the
    melt, quenched to glass) or "both"; ``grams`` is the total put on the card.

    Whatever the minerals cannot hold (titanium, a phase with no counterpart) and the smallest minerals
    beyond what the card holds go on as one more glass, "rest of ...", of their oxides, so all of the
    sample's mass is on the card."""
    if take not in TAKE:
        raise ValueError(f"take must be one of {', '.join(TAKE)}")
    app = sample.written_by.get("app", "sample")
    melt_g = sample.melt["grams"] if sample.melt and take in ("melt", "both") else 0.0
    solid_g = sample.solid_grams if take in ("rock", "both") else 0.0
    if melt_g + solid_g <= 0:
        raise ValueError("this sample has no melt" if take == "melt" else "this sample has no solids")
    f = grams / (melt_g + solid_g)
    out = Recast()
    if solid_g > 0:
        out = to_reactants(sample, scale_to=solid_g * f, database=database)
        out.notes = [n for n in out.notes if "of melt" not in n]
    rest: dict[str, float] = {}
    for left in out.left_over.values():
        for ox, g in left.items():
            rest[ox] = rest.get(ox, 0.0) + g
    slots = MAX_ON_CARD - (1 if melt_g > 0 else 0)
    if len(out.reactants) + (1 if rest else 0) > slots:
        keep = slots - 1                         # one slot for the rest glass
        extra, out.reactants = out.reactants[keep:], out.reactants[:keep]
        for r in extra:
            f_ = parse_formula(FORMULAS[r["name"]])
            mm = molar_mass(FORMULAS[r["name"]])
            for el, n in f_.items():
                if el in ("O", "H"):
                    continue
                ox = next(o for o, (e, _k, _o) in OXIDE_CATION.items() if e == el and o != "Fe2O3")
                e, k, o = OXIDE_CATION[ox]
                rest[ox] = rest.get(ox, 0.0) + r["amount"] / mm * n / k * (k * ATOMIC_WEIGHT[e] + o * ATOMIC_WEIGHT["O"])
        out.notes.append(f"the smallest minerals ({', '.join(r['name'] for r in extra)}) go on inside the rest "
                         f"glass, as the card holds at most {MAX_ON_CARD} reactants")
    if rest:
        g = sum(rest.values())
        name = f"rest of {app} rock {_t(sample)}"
        out.reactants.append(glass_reactant(name, rest, g, f"the part of a {app} sample not on the card as "
                                                         f"minerals ({', '.join(sorted(rest))}), as a glass"))
        out.notes.append(f"{g:.3g} g goes on as the glass '{name}' ({', '.join(sorted(rest))}), dissolving "
                         f"congruently; where Reaction has no dissolved species for an element the run leaves it "
                         f"out and says so")
    if melt_g > 0:
        out.reactants.append(glass_reactant(f"{app} glass {_t(sample)}", sample.melt["wt_pct"], melt_g * f,
                                            f"the melt of a {app} sample at {_t(sample)} and "
                                            f"{sample.conditions['p_bar']:g} bar, quenched to glass"))
    out.notes.insert(0, f"from a {app} sample at {_t(sample)} and {sample.conditions['p_bar']:g} bar; the card's "
                        f"own temperature and pressure are not changed")
    return out
