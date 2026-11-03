"""Write src/reaction/data/miron_aq17.tsv from the ThermoFun aq17 dataset file.

aq17 holds the aqueous species of Miron et al. (2016, 2017), whose HKF parameters were fitted to mineral
solubility experiments with the minerals of the Holland & Powell dataset, so that the two are consistent.
Only the numbers (G, S and the HKF coefficients at 25 C, 1 bar) are taken, each row with its sources.

    python scripts/extract_aq17.py path/to/aq17-thermofun.json

The json is in github.com/thermohub/thermofun (Resources/databases/aq17-thermofun.json).
"""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "src" / "reaction" / "data" / "miron_aq17.tsv"
# aq17 symbols that OBIGT spells differently ("@" marks a neutral aqueous species in aq17)
NAMES = {"CO@": "CO"}
FORMULAS = {"CO@": "CO"}
SKIP = {"H2O@", "H+",                  # the solvent, and H+ (zero by convention in both)
        "CH4@", "CO2@",                # Akinfiev-Diamond model, not HKF: OBIGT's stay
        "H2@", "O2@"}                  # no HKF parameters in aq17: OBIGT's stay

HEADER = """# Aqueous species consistent with the Holland & Powell minerals: HKF parameters of Miron, Wagner, Kulik and
# Heinrich (2016, Geochim. Cosmochim. Acta 187, 41-78; system Na-K-Al-Si-O-H-Cl) and Miron, Wagner, Kulik and
# Lothenbach (2017, Am. J. Sci. 317, 755-806; adds Ca, Mg and C), as tabulated in the aq17 dataset of ThermoFun
# (github.com/thermohub/thermofun, Resources/databases/aq17-thermofun.json).  Written by scripts/extract_aq17.py.
# Units: G J/mol (apparent, from the elements), S J/K/mol, and the HKF coefficients unscaled in calories:
# a1 cal/mol/bar, a2 cal/mol, a3 cal K/mol/bar, a4 cal K/mol, c1 cal/mol/K, c2 cal K/mol, omega cal/mol.
"""


def main(src: str) -> None:
    d = json.loads(Path(src).read_text("utf-8"))
    rows = []
    for s in d["substances"]:
        if list(s["aggregate_state"].values())[0] != "AS_AQUEOUS" or s["symbol"] in SKIP:
            continue
        hkf = [m for m in s["TPMethods"] if "solute_hkf88_reaktoro" in m["method"].values()]
        if not hkf:
            raise SystemExit(f"{s['symbol']}: no HKF parameters")
        a1, a2, a3, a4, c1, c2, w = hkf[0]["eos_hkf_coeffs"]["values"][:7]
        sym = s["symbol"]
        name = NAMES.get(sym, sym.replace("@", ""))
        formula = FORMULAS.get(sym, s["formula"].replace("@", ""))
        g, sv = s["sm_gibbs_energy"]["values"][0], s["sm_entropy_abs"]["values"][0]
        refs = " ".join(r.strip("[]") for r in s.get("datasources", []))
        rows.append([name, formula, f"{s['formula_charge']:g}", f"{g:.10g}", f"{sv:.8g}",
                     *(f"{x:.8g}" for x in (a1, a2, a3, a4, c1, c2, w)), refs])
    cols = ["name", "formula", "charge", "G", "S", "a1", "a2", "a3", "a4", "c1", "c2", "omega", "sources"]
    OUT.write_text(HEADER + "\t".join(cols) + "\n" + "".join("\t".join(r) + "\n" for r in rows), "utf-8")
    print(f"{len(rows)} species -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
