"""Write one Holland & Powell end-member dataset from MAGEMin's TC_endmembers.c as a core TSV.

    python scripts/extract_hp_dataset.py <MAGEMin>/src/TC_database/TC_endmembers.c 62 src/protolith/core/data/hp_ds62.tsv

The columns are those of hp_ds636.tsv: the 15 oxides and atoms, H S V, Cp a b c d, alpha0 kappa0 kappa0'
kappa0'' and the order-disorder flag and parameters (the elastic block is not used and is left out).
"""
import re
import sys

HEADER = ("name SiO2 Al2O3 CaO MgO FeO K2O Na2O TiO2 O MnO Cr2O3 H2O CO2 Sel Cl atoms H S V a b c d alpha0 "
          "kappa0 kappa0p kappa0pp od od1 od2 od3 od4 od5 od6").split()


def main(src, dataset, out):
    text = open(src, encoding="utf-8").read()
    start = text.index(f"arr_em_db_tc_ds{dataset}[")
    end = text.index("};\n", start)
    block = text[start:end]
    rows = []
    for m in re.finditer(r'\{\s*"([^"]+)",\s*\{([^}]*)\},\s*\{([^}]*)\},\s*\{([^}]*)\},\s*\{([^}]*)\},\s*\{([^}]*)\}',
                         block):
        name = m.group(1)
        nums = [float(v) for g in m.groups()[1:5] for v in g.split(",")]
        if len(nums) != len(HEADER) - 1:
            raise SystemExit(f"{name}: {len(nums)} numbers")
        rows.append([name] + [repr(v) for v in nums])
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# Holland & Powell end-member dataset ds{dataset} (Holland and Powell 2011, J. Metamorphic Geol. 29,\n"
                "# 333-383), the dataset of the metapelite set of White et al. (2014); numbers as distributed in MAGEMin\n"
                "# (src/TC_database/TC_endmembers.c), written by scripts/extract_hp_dataset.py, taken at Douglas's\n"
                "# request 2026-11-03.  Units and columns as in hp_ds636.tsv.\n")
        f.write("\t".join(HEADER) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    print(len(rows), "end members")


if __name__ == "__main__":
    main(*sys.argv[1:4])
