"""Mineral names for the core's phases, with the abbreviations of Whitney and Evans (2010).

One HP model can stand for more than one mineral, told apart by composition: feldspar is plagioclase or
K-feldspar, white mica muscovite or paragonite, clinopyroxene diopside-augite, omphacite, jadeite or
pigeonite, amphibole a calcic amphibole, glaucophane or cummingtonite, the rhombohedral oxide ilmenite or
hematite, spinel spinel or magnetite, epidote epidote or clinozoisite.
"""
from __future__ import annotations

import numpy as np

from protolith.core.hp.minimize import COMPONENTS

# abbreviation -> (name, the order it takes in an assemblage label)
MINERALS = {
    "Liq": "melt", "Grt": "garnet", "Omp": "omphacite", "Jd": "jadeite", "Cpx": "clinopyroxene",
    "Pgt": "pigeonite", "Opx": "orthopyroxene", "Ol": "olivine", "Amp": "amphibole", "Gln": "glaucophane",
    "Cum": "cummingtonite", "Bt": "biotite", "Ms": "muscovite", "Pg": "paragonite", "Chl": "chlorite",
    "St": "staurolite", "Cld": "chloritoid", "Spr": "sapphirine", "Ep": "epidote", "Czo": "clinozoisite",
    "Crd": "cordierite", "Pl": "plagioclase", "Kfs": "K-feldspar",
    "Ky": "kyanite", "Sil": "sillimanite", "And": "andalusite", "Qz": "quartz", "Trd": "tridymite",
    "Crs": "cristobalite", "Coe": "coesite", "Stv": "stishovite", "Nph": "nepheline", "Crn": "corundum",
    "Rt": "rutile", "Ttn": "titanite", "Ilm": "ilmenite", "Hem": "hematite", "Mag": "magnetite",
    "Spl": "spinel", "H2O": "water",
}
ORDER = {a: i for i, a in enumerate(MINERALS)}
PURE = {"q": "Qz", "crst": "Crs", "trd": "Trd", "coe": "Coe", "stv": "Stv", "ky": "Ky", "sill": "Sil",
        "and": "And", "ru": "Rt", "sph": "Ttn", "cor": "Crn", "ne": "Nph"}
SIMPLE = {"g": "Grt", "opx": "Opx", "ol": "Ol", "bi": "Bt", "chl": "Chl", "cd": "Crd", "liq": "Liq", "fl": "H2O",
          "st": "St", "ctd": "Cld", "sa": "Spr"}
MODEL = {
    "ol": "olivine", "fsp": "feldspar", "spl": "spinel", "ilm": "ilmenite-hematite", "g": "garnet",
    "bi": "biotite", "mu": "white mica", "opx": "orthopyroxene", "cpx": "clinopyroxene",
    "amp": "amphibole", "cd": "cordierite", "ep": "epidote", "chl": "chlorite", "liq": "melt",
    "fl": "fluid", "st": "staurolite", "ctd": "chloritoid", "sa": "sapphirine",
}
# anhydrous oxygens per formula unit, for the structural formula
OXYGENS = {"ol": 4, "opx": 6, "cpx": 6, "fsp": 8, "spl": 4, "ilm": 3, "g": 12, "amp": 23, "bi": 11, "mu": 11,
           "cd": 18, "ep": 12.5, "chl": 14, "st": 46, "ctd": 6, "sa": 20}
_TAIL = {"amp": "O22(OH)2", "bi": "O10(OH)2", "mu": "O10(OH)2", "chl": "O10(OH)8", "ep": "O12(OH)",
         "st": "O44(OH)4", "ctd": "O5(OH)2"}
_CATION = {"SiO2": ("Si", 1, 2), "TiO2": ("Ti", 1, 2), "Al2O3": ("Al", 2, 3), "Cr2O3": ("Cr", 2, 3),
           "MgO": ("Mg", 1, 1), "CaO": ("Ca", 1, 1), "Na2O": ("Na", 2, 1), "K2O": ("K", 2, 1)}
_I = {c: i for i, c in enumerate(COMPONENTS)}


def abbreviation(hp: str, x: dict[str, float], c: np.ndarray) -> str:
    """The mineral an HP phase is, from its end-member fractions x and its components per formula unit c."""
    if hp in PURE:
        return PURE[hp]
    if hp in SIMPLE:
        return SIMPLE[hp]
    if hp == "fsp":
        return "Kfs" if x.get("san", 0.0) > 0.5 else "Pl"
    if hp == "mu":
        return "Pg" if x.get("pa", 0.0) > 0.5 else "Ms"
    if hp == "ilm":
        return "Hem" if x.get("hm", 0.0) > 0.5 else "Ilm"
    if hp == "spl":
        return "Mag" if x.get("nmt", 0.0) + x.get("imt", 0.0) + x.get("usp", 0.0) > 0.5 else "Spl"
    if hp == "ep":
        return "Czo" if x.get("cz", 0.0) > 0.5 else "Ep"
    if hp == "amp":
        if x.get("glm", 0.0) > 0.5:
            return "Gln"
        if x.get("cumm", 0.0) + x.get("grnm", 0.0) > 0.5:
            return "Cum"
        return "Amp"
    if hp == "cpx":
        jd = x.get("jd", 0.0)
        if jd > 0.8:
            return "Jd"
        if jd > 0.2:
            return "Omp"
        ca, mg, fe = c[_I["CaO"]], c[_I["MgO"]], c[_I["FeO"]]
        return "Pgt" if ca + mg + fe > 0 and ca / (ca + mg + fe) < 0.25 else "Cpx"
    return hp


def label(assemblage) -> str:
    """'Grt Bt Ms Pl Qz Ilm H2O', with a mineral that is there twice (across a solvus) written '2Amp'."""
    out, seen = [], {}
    for a in assemblage:
        seen[a] = seen.get(a, 0) + 1
    for a in sorted(seen, key=lambda a: ORDER.get(a, 99)):
        out.append(a if seen[a] == 1 else f"{seen[a]}{a}")
    return " ".join(out)


def formula(hp: str, c: np.ndarray) -> str:
    """Cations per OXYGENS[hp] anhydrous oxygens, e.g. Ca0.85Mg0.90Fe0.21Al0.08Si1.96O6."""
    if hp not in OXYGENS:
        return ""
    fe3 = 2.0 * max(c[_I["O"]], 0.0)
    fe2 = max(c[_I["FeO"]] - fe3, 0.0)
    cat, oxy = {}, 0.0
    for ox, (el, k, o) in _CATION.items():
        v = c[_I[ox]]
        if v > 0:
            cat[el] = k * v
            oxy += o * v
    cat["Fe"] = fe2 + fe3
    oxy += fe2 + 1.5 * fe3
    if oxy <= 0:
        return ""
    f = OXYGENS[hp] / oxy
    order = ("K", "Na", "Ca", "Mg", "Fe", "Ti", "Cr", "Al", "Si")
    parts = [f"{el}{cat[el] * f:.2f}" for el in order if cat.get(el, 0) * f >= 0.005]
    return "".join(parts) + _TAIL.get(hp, f"O{OXYGENS[hp]:g}")


def numbers(hp: str, c: np.ndarray) -> dict[str, float]:
    """The numbers a petrologist reads off a mineral: An of plagioclase, Mg# of ferromagnesian phases,
    the garnet end members as mole %."""
    fe3 = 2.0 * max(c[_I["O"]], 0.0)
    fe2 = max(c[_I["FeO"]] - fe3, 0.0)
    mg, ca = c[_I["MgO"]], c[_I["CaO"]]
    out = {}
    if hp == "fsp":
        na, k = 2 * c[_I["Na2O"]], 2 * c[_I["K2O"]]
        s = ca + na + k
        if s > 0:
            out = {"An": 100 * ca / s, "Ab": 100 * na / s, "Or": 100 * k / s}
    elif hp == "g":
        s = mg + fe2 + ca
        if s > 0:
            out = {"Prp": 100 * mg / s, "Alm": 100 * fe2 / s, "Grs": 100 * ca / s}
    if hp in ("g", "bi", "chl", "cd", "amp", "cpx", "opx", "ol", "mu", "st", "ctd", "sa") and mg + fe2 > 0:
        out["Mg#"] = 100 * mg / (mg + fe2)
    return out
