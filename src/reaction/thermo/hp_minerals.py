"""Minerals from Protolith's shared Holland & Powell core, and aqueous species fitted to them.

This is Reaction's side of the shared core (``protolith.core.hp``): a mineral that the Holland & Powell
dataset (ds6.36) holds is computed there, so a rock from Magma and the same rock reacted here carry the
same Gibbs energies.  Changing the minerals alone would shift every solubility by the few kJ that the HP
and SUPCRT/HKF traditions disagree by, so the main aqueous species change with them: the HKF parameters of
Miron et al. (2016, 2017), fitted to mineral solubility experiments with the HP minerals
(``data/miron_aq17.tsv``).  Everything else (Fe, Ti, S and trace-metal species, minerals HP does not hold)
stays as in OBIGT, and each species' provenance says which data it came from.

Energy scale.  HP tabulates G = H - T S with H from the elements and S the third-law entropy; OBIGT and
HKF use the apparent Gibbs energy of formation (Benson-Helgeson), whose value at 25 C is dGf.  The two
differ by Tr times the entropy of the elements in the formula, a constant per mineral, which is added here
(element entropies as in ``berman.py``).  The HP pressure is the HP pressure (bar here, kbar in the core).
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from protolith.core.hp import endmembers as hp

from .berman import element_entropy
from .hkf import HKFSpecies
from .obigt import ObigtData, ObigtSpecies, parse_formula

T_REF = 298.15
CAL = 4.184
SOURCE = "Holland & Powell ds6.36 (Protolith core)"
MIRON_SOURCE = "Miron et al. 2016, 2017 (aq17)"
MIRON_DATA = Path(__file__).resolve().parents[1] / "data" / "miron_aq17.tsv"

# moles of each element in one mole of the HP oxide components ("O" is the oxygen beyond FeO, "Sel" is S)
_OXIDE_ELEMENTS = {
    "SiO2": {"Si": 1, "O": 2}, "Al2O3": {"Al": 2, "O": 3}, "CaO": {"Ca": 1, "O": 1}, "MgO": {"Mg": 1, "O": 1},
    "FeO": {"Fe": 1, "O": 1}, "K2O": {"K": 2, "O": 1}, "Na2O": {"Na": 2, "O": 1}, "TiO2": {"Ti": 1, "O": 2},
    "O": {"O": 1}, "MnO": {"Mn": 1, "O": 1}, "Cr2O3": {"Cr": 2, "O": 3}, "H2O": {"H": 2, "O": 1},
    "CO2": {"C": 1, "O": 2}, "Sel": {"S": 1}, "Cl": {"Cl": 1},
}

# Reaction's (OBIGT's) mineral name -> HP end member.  A pair is used only if the formulas agree, or one is a
# whole multiple of the other (HP writes the orthopyroxenes per two silicons, OBIGT per one).
SHARED = {
    "akermanite": "ak", "albite": "ab", "albite,low": "ab", "albite,high": "abh", "almandine": "alm",
    "analcime": "anl", "andalusite": "and", "andradite": "andr", "annite": "ann", "anorthite": "an",
    "anthophyllite": "anth", "antigorite": "atg", "aragonite": "arag", "bixbyite": "bix", "brucite": "br",
    "Ca-Al-pyroxene": "cats", "calcite": "cc", "chrysotile": "chr", "clinochlore": "clin",
    "clinozoisite": "cz", "coesite": "coe", "cordierite": "crd", "corundum": "cor", "daphnite": "daph",
    "diaspore": "dsp", "diopside": "di", "dolomite": "dol", "enstatite": "en", "epidote": "ep",
    "fayalite": "fa", "ferro-actinolite": "fact", "ferrosilite": "fs", "forsterite": "fo",
    "gehlenite": "geh", "glaucophane": "gl", "graphite": "gph", "grossular": "gr", "grunerite": "grun",
    "halite": "hlt", "hedenbergite": "hed", "hematite": "hem", "ilmenite": "ilm", "iron": "iron",
    "jadeite": "jd", "K-feldspar": "mic", "K-feldspar,low": "mic", "K-feldspar,high": "san",
    "kalsilite": "kls", "kaolinite": "kao", "kyanite": "ky", "larnite": "lrn", "laumontite": "lmt",
    "lawsonite": "law", "lime": "lime", "magnesite": "mag", "magnetite": "mt", "manganosite": "mang",
    "margarite": "ma", "meionite": "me", "merwinite": "merw", "monticellite": "mont", "muscovite": "mu",
    "nepheline": "ne", "paragonite": "pa", "pargasite": "parg", "periclase": "per", "phlogopite": "phl",
    "prehnite": "pre", "pseudowollastonite": "pswo", "pumpellyite": "mpm", "pyrite": "pyr",
    "pyrope": "py", "pyrophyllite": "prl", "quartz": "q", "rhodochrosite": "rhc", "rutile": "ru",
    "siderite": "sid", "sillimanite": "sill", "sphene": "sph", "spinel": "sp", "sudoite": "sud",
    "sylvite": "syv", "talc": "ta", "tremolite": "tr", "wairakite": "wrk", "wollastonite": "wo",
}

# HP end members that OBIGT lacks, added under these names (the Fe-Ti oxides and garnets of igneous rocks,
# and the zeolites and sheet silicates of alteration)
HP_ONLY = {
    "ulvospinel": "usp", "hercynite": "herc", "geikielite": "geik", "pyrophanite": "pnt",
    "tephroite": "teph", "spessartine": "spss", "acmite": "acm", "Mg-Tschermak pyroxene": "mgts",
    "tschermakite": "ts", "cummingtonite": "cumm", "riebeckite": "rieb", "celadonite": "cel",
    "eastonite": "east", "Fe-epidote": "fep", "heulandite": "heu", "stilbite": "stlb",
    "Fe-pumpellyite": "fpm", "amesite": "ames", "chloritoid": "mctd", "Fe-chloritoid": "fctd",
    "staurolite": "mst", "Fe-staurolite": "fst",
}


def hp_elements(em: str) -> dict[str, float]:
    """The elements in one formula unit of an HP end member."""
    out: dict[str, float] = {}
    for oxide, n in hp.DATA[em].comp.items():
        for el, k in _OXIDE_ELEMENTS[oxide].items():
            out[el] = out.get(el, 0.0) + n * k
    return {el: n for el, n in out.items() if abs(n) > 1e-9}


def same_formula(a: dict[str, float], b: dict[str, float]) -> bool:
    return formula_ratio(a, b) == 1.0


def formula_ratio(a: dict[str, float], b: dict[str, float]) -> float | None:
    """k with b = k a for every element, or None."""
    if set(a) != set(b) or not a:
        return None
    k = next(iter(b.values())) / a[next(iter(b))]
    if all(abs(b[el] - k * a[el]) < 1e-6 * max(1.0, abs(b[el])) for el in a):
        return round(k, 6)
    return None


def formula_of(elements: dict[str, float]) -> str:
    order = ["K", "Na", "Ca", "Mg", "Fe", "Mn", "Al", "Cr", "Ti", "Zr", "Si", "C", "S", "Cl", "H", "O"]
    keys = sorted(elements, key=lambda el: order.index(el) if el in order else len(order))
    num = lambda n: "" if n == 1 else (f"{n:g}")  # noqa: E731
    return "".join(f"{el}{num(elements[el])}" for el in keys)


@dataclass(frozen=True)
class HPMineral:
    """A mineral computed by the shared core, on the OBIGT energy scale (J/mol)."""
    name: str                  # Reaction's name
    endmember: str             # HP abbreviation
    s_elements: float          # J/K, entropy of the elements in the HP formula at Tr
    per: float = 1.0           # HP formula units in one of Reaction's (0.5: MgSiO3 against Mg2Si2O6)

    @classmethod
    def of(cls, name: str, endmember: str, per: float = 1.0) -> "HPMineral":
        return cls(name, endmember, element_entropy(hp_elements(endmember)), per)

    @property
    def v0(self) -> float:
        """Molar volume at 25 C, 1 bar, cm3/mol (HP tabulates kJ/kbar = 10 cm3)."""
        return hp.DATA[self.endmember].v * 10.0 * self.per

    @property
    def t_max(self) -> float:
        return math.inf

    def gibbs(self, t_k: float, p_bar: float) -> float:
        return self.per * (hp.gibbs_j(self.endmember, t_k, p_bar) + T_REF * self.s_elements)

    def extrapolated(self, t_k: float) -> bool:
        return False


def load_miron() -> list[ObigtSpecies]:
    """The aqueous species of Miron et al. (2016, 2017) as OBIGT-style species with HKF parameters."""
    text = MIRON_DATA.read_text("utf-8")
    rows = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    out = []
    for r in csv.DictReader(rows, delimiter="\t"):
        f = lambda k: float(r[k])  # noqa: E731
        elements, charge = parse_formula(r["formula"])
        z = f("charge")
        eos = HKFSpecies(r["name"], z, f("G"), f("S"), f("a1") * CAL, f("a2") * CAL, f("a3") * CAL,
                         f("a4") * CAL, f("c1") * CAL, f("c2") * CAL, f("omega") * CAL)
        refs = tuple(r["sources"].split()[:2]) + ("",) * (2 - len(r["sources"].split()[:2]))
        out.append(ObigtSpecies(r["name"], "aq", r["formula"], elements, z, "HKF", eos,
                                "miron_aq17.tsv", refs))
    return out


# HP minerals whose energies are calorimetric rather than part of the solubility fit: on the Miron alkali scale
# (Na+ and K+ some 5.7 kJ above OBIGT's) they come out about a log unit too soluble at 25 C (halite log K 0.56
# against the measured 1.58), so OBIGT's are kept, bridged like every other OBIGT species
NOT_FROM_HP = {"halite", "sylvite"}
# other names for a mapped mineral, dropped when it comes from HP: "one name, not a tie" (as obigt.py does)
ALIASES = {"albite,low": "albite", "K-feldspar,low": "K-feldspar",
           "quartz,beta": "quartz"}            # HP quartz carries its own alpha-beta transition (Landau)
# elements whose aqueous basis species Miron et al. refitted, and their basis species
_MIRON_MASTERS = {"Na": "Na+", "K": "K+", "Ca": "Ca+2", "Mg": "Mg+2", "Al": "Al+3", "Si": "SiO2",
                  "C": "HCO3-", "Cl": "Cl-"}
# elements with HP minerals but no refitted aqueous species: OBIGT's species of them are moved by one constant
# per atom, fitted so the HP minerals of that element dissolve as OBIGT's do (the bridge)
BRIDGED_ELEMENTS = ("Fe", "Mn")
_FIT_T = (25.0, 100.0, 150.0, 200.0, 250.0, 300.0)


class Bridged:
    """An OBIGT species moved onto the scale of the HP minerals and Miron species.

    Its G gains, for each element, n times the change in that element's basis species (Miron's G minus
    OBIGT's, at the same T and P) plus n times the element's bridge constant.  So its log K of formation
    from the basis species stays exactly OBIGT's, while the basis species themselves are Miron's."""

    def __init__(self, eos, shifts: list[tuple[float, object, object]], constant: float):
        self.eos, self.shifts, self.constant = eos, shifts, constant

    def gibbs(self, t_k: float, p_bar: float) -> float:
        return (self.eos.gibbs(t_k, p_bar) + self.constant
                + sum(n * (new.gibbs(t_k, p_bar) - old.gibbs(t_k, p_bar)) for n, new, old in self.shifts))

    def extrapolated(self, t_k: float) -> bool:
        return self.eos.extrapolated(t_k) if hasattr(self.eos, "extrapolated") else False

    def __getattr__(self, name):                  # v0, t_max, charge, ... of the species itself
        return getattr(self.eos, name)


@dataclass
class Overlay:
    """What :func:`apply` changed, for the database notes and the comparison report."""
    minerals: list[str]
    added_minerals: list[str]
    aqueous: list[str]
    added_aqueous: list[str]
    mismatched: list[str]
    bridge: dict[str, float] = field(default_factory=dict)          # element -> J per atom
    bridge_fit: dict[str, list[tuple[str, float]]] = field(default_factory=dict)   # element -> (mineral, kJ)
    bridged: int = 0


def _psat(t_c: float) -> float:
    from .eosdb import reference_pressure_bar
    return reference_pressure_bar(t_c)


def apply(data: ObigtData, *, minerals: bool = True, aqueous: bool = True) -> Overlay:
    """Put the HP minerals and the Miron aqueous species into loaded OBIGT data, in place, and move every
    species left from OBIGT onto their scale (see :class:`Bridged`)."""
    ov = Overlay([], [], [], [], [])
    original = dict(data.species)
    from_hp: dict[str, ObigtSpecies] = {}         # Reaction name -> the HP species replacing OBIGT's
    replaced: dict[str, ObigtSpecies] = {}        # Reaction name -> OBIGT's own (first polymorph)
    if minerals:
        for name, em in SHARED.items():
            if name in NOT_FROM_HP or name in ALIASES:
                continue
            poly = data.polymorphs(name)
            if not poly:
                continue
            k = formula_ratio(poly[0].elements, hp_elements(em))
            if k is None:
                ov.mismatched.append(f"{name} ({poly[0].formula}) is not HP {em} "
                                     f"({formula_of(hp_elements(em))}); OBIGT's is kept")
                continue
            try:
                eos = HPMineral.of(name, em, 1.0 / k)
            except ValueError as exc:     # an element without a tabulated entropy
                ov.mismatched.append(f"{name}: {exc}; OBIGT's is kept")
                continue
            for p in poly:
                del data.species[(p.name, p.state)]
            replaced[name] = poly[0]
            from_hp[name] = data.species[(name, "cr")] = ObigtSpecies(
                name, "cr", poly[0].formula, dict(poly[0].elements), 0.0, "HP", eos, SOURCE, ("HP11", em))
            ov.minerals.append(name)
        for alias, base in ALIASES.items():
            if base in from_hp:
                for p in data.polymorphs(alias):
                    del data.species[(p.name, p.state)]
        have = {n for (n, st) in data.species if st.startswith("cr")}
        for name, em in HP_ONLY.items():
            if name in have:
                continue
            els = hp_elements(em)
            try:
                eos = HPMineral.of(name, em)
            except ValueError:            # an element without a tabulated entropy
                continue
            from_hp[name] = data.species[(name, "cr")] = ObigtSpecies(
                name, "cr", formula_of(els), els, 0.0, "HP", eos, SOURCE, ("HP11", em))
            ov.added_minerals.append(name)
    miron: set[tuple[str, str]] = set()
    if aqueous:
        for sp in load_miron():
            key = (sp.name, "aq")
            if key in data.species:
                old = data.species[key]
                if not same_formula(old.elements, sp.elements) or old.charge != sp.charge:
                    ov.mismatched.append(f"aqueous {sp.name}: Miron formula differs from OBIGT's; OBIGT's is kept")
                    continue
                ov.aqueous.append(sp.name)
            else:
                ov.added_aqueous.append(sp.name)
            data.species[key] = sp
            miron.add(key)

    # the bridge: element by element, how far each basis species moved
    moved = {el: (data.species[(m, "aq")].eos, original[(m, "aq")].eos) for el, m in _MIRON_MASTERS.items()
             if (m, "aq") in miron and (m, "aq") in original}

    def shifts_for(elements):
        return [(n, *moved[el]) for el, n in elements.items() if el in moved]

    def basis_shift(elements, t_k, p_bar):
        return sum(n * (new.gibbs(t_k, p_bar) - old.gibbs(t_k, p_bar)) for n, new, old in shifts_for(elements))

    for el in BRIDGED_ELEMENTS:
        pairs = [(nm, hp_sp, replaced[nm]) for nm, hp_sp in from_hp.items()
                 if nm in replaced and hp_sp.elements.get(el, 0) > 0
                 and all(e in moved or e in ("O", "H", el) for e in hp_sp.elements)]
        num = den = 0.0
        per_mineral = []
        for nm, hp_sp, ob_sp in pairs:
            n = hp_sp.elements[el]
            gaps = []
            for t_c in _FIT_T:
                t_k, p = t_c + 273.15, _psat(t_c)
                try:
                    g_ob = _Polymorphs(data_polymorphs(original, nm)).gibbs(t_k, p)
                except Exception:
                    continue
                gaps.append(hp_sp.eos.gibbs(t_k, p) - g_ob - basis_shift(hp_sp.elements, t_k, p))
            if gaps:
                num += n * sum(gaps)
                den += n * n * len(gaps)
                per_mineral.append((nm, n, sum(gaps) / len(gaps)))
        if den > 0:
            delta = num / den
            ov.bridge[el] = delta
            ov.bridge_fit[el] = [(nm, (gap - n * delta) / 1000.0) for nm, n, gap in per_mineral]

    hp_keys = {(n, "cr") for n in from_hp}
    for key, sp in list(data.species.items()):
        if key in hp_keys or key in miron or sp.eos is None or sp.eos == "water":
            continue
        sh = shifts_for(sp.elements)
        const = sum(n * ov.bridge.get(el, 0.0) for el, n in sp.elements.items())
        if sh or const:
            data.species[key] = replace(sp, eos=Bridged(sp.eos, sh, const))
            ov.bridged += 1
    return ov


def data_polymorphs(species: dict, name: str) -> list:
    return sorted((sp for (n, st), sp in species.items() if n == name and re.fullmatch(r"cr\d?", st)),
                  key=lambda sp: sp.state)


class _Polymorphs:
    """G of a mineral from its OBIGT polymorphs, the lowest one that holds at T (as eosdb._Crystal)."""

    def __init__(self, poly):
        self.poly = poly

    def gibbs(self, t_k, p_bar):
        for p in self.poly:
            if not p.eos.extrapolated(t_k):
                return p.eos.gibbs(t_k, p_bar)
        raise ValueError("no data at this temperature")
