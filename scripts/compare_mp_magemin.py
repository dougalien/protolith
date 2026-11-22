"""Every point of MAGEMin's metapelite reference grid (tests/core/data/mp_magemin_points.json) against the core.

    python scripts/compare_mp_magemin.py            (all points; a few seconds each)
    python scripts/compare_mp_magemin.py 600:8      (only T_C:P points, P rounded)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from protolith.core.hp.minimize import COMPONENTS, METAPELITE, equilibrate  # noqa: E402

REF = json.loads((Path(__file__).resolve().parents[1] / "tests/core/data/mp_magemin_points.json").read_text())


def main(args):
    b = dict(zip(REF["bulk_oxides"], REF["bulk"]))
    bulk = np.array([b.get(c, 0.0) for c in COMPONENTS])
    bulk /= bulk.sum()
    want = {tuple(map(float, a.split(":"))) for a in args}
    same = 0
    pts = [p for p in REF["points"] if not want or (p["T_C"], round(p["P"])) in want]
    for p in pts:
        t0 = time.time()
        r = equilibrate(bulk, p["T_C"] + 273.15, p["P"], system=METAPELITE)
        ours, ref = sorted(ph.name for ph in r.phases), sorted(p["phases"])
        same += ours == ref
        print(f"{p['T_C']:4.0f} C {p['P']:5.2f} kbar {time.time() - t0:4.0f} s  dG {r.g - p['G']:+.4f}  "
              f"{'same' if ours == ref else 'DIFF'}  ours: {' '.join(ours)}" + ("" if ours == ref else f"  MAGEMin: {' '.join(ref)}"),
              flush=True)
    print(f"{same} of {len(pts)} assemblages the same")


if __name__ == "__main__":
    main(sys.argv[1:])
