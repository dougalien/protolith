"""The metapelite set against MAGEMin's own results for it (tests/core/data/mp_magemin_points.json).

Each point is solved from scratch with the core's minimizer; the stable assemblage must be MAGEMin's and
the system G must agree to 0.01 kJ per mole of oxides.  A few points across the grid run here (each takes
a few seconds); scripts/compare_mp_magemin.py runs all of them.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from protolith.core.hp.minimize import COMPONENTS, METAPELITE, equilibrate

REF = json.loads((Path(__file__).parent / "data" / "mp_magemin_points.json").read_text())
_B = dict(zip(REF["bulk_oxides"], REF["bulk"]))
BULK = np.array([_B.get(c, 0.0) for c in COMPONENTS])
BULK = BULK / BULK.sum()
CASES = [(2.01, 400.0), (4.01, 600.0), (8.01, 600.0), (8.01, 700.0), (6.01, 800.0)]


def _ref(p, t):
    return next(pt for pt in REF["points"] if pt["P"] == p and pt["T_C"] == t)


@pytest.mark.parametrize("p,t_c", CASES, ids=[f"{t:.0f}C-{p:.0f}kbar" for p, t in CASES])
def test_matches_magemin(p, t_c):
    ref = _ref(p, t_c)
    r = equilibrate(BULK, t_c + 273.15, p, system=METAPELITE)
    assert r.converged
    assert sorted(ph.name for ph in r.phases) == sorted(ref["phases"])
    assert r.g == pytest.approx(ref["G"], abs=0.01)
