"""The rock's bulk for the solver, and mineral names."""
import numpy as np
import pytest

from metamorphism import bulk, names
from protolith.core.hp.minimize import COMPONENTS

I = {c: i for i, c in enumerate(COMPONENTS)}


def test_wt_pct_round_trip_keeps_ferric_iron():
    wt = bulk.PRESETS["metabasite"]
    b = bulk.from_wt_pct(wt)
    assert b.moles[I["O"]] == pytest.approx(b.wt_pct["Fe2O3"] / bulk.MOLAR_MASS["Fe2O3"])
    back = bulk.to_wt_pct(b.moles)
    total = sum(wt.values())
    for ox, v in wt.items():
        assert back[ox] == pytest.approx(100 * v / total, rel=1e-9)
    assert b.grams == pytest.approx(100.0)


def test_left_out_oxides_are_listed():
    b = bulk.from_wt_pct({**bulk.PRESETS["pelite"], "MnO": 0.2, "P2O5": 0.15})
    assert set(b.left_out) == {"MnO", "P2O5"}
    assert b.grams == pytest.approx(100.0 - sum(b.left_out.values()), rel=1e-6)


def test_bad_compositions_are_refused():
    with pytest.raises(ValueError, match="unknown"):
        bulk.from_wt_pct({"SiO2": 50, "Xx": 1})
    with pytest.raises(ValueError, match="negative"):
        bulk.from_wt_pct({"SiO2": 50, "MgO": -1})
    with pytest.raises(ValueError, match="water"):
        bulk.from_wt_pct({"SiO2": 50}, water="lots")


def test_excess_water_is_far_more_than_the_rock_holds():
    b = bulk.from_wt_pct(bulk.PRESETS["pelite"], water="excess")
    m = bulk.solver_moles(b)
    assert m[I["H2O"]] >= 0.5 * (m.sum() - m[I["H2O"]]) * 0.999
    assert bulk.solver_moles(bulk.from_wt_pct(bulk.PRESETS["pelite"]))[I["H2O"]] == b.moles[I["H2O"]]


def test_names_follow_composition():
    c = np.zeros(len(COMPONENTS))
    assert names.abbreviation("fsp", {"ab": 0.7, "an": 0.3}, c) == "Pl"
    assert names.abbreviation("fsp", {"san": 0.9, "ab": 0.1}, c) == "Kfs"
    assert names.abbreviation("mu", {"pa": 0.8, "mu": 0.2}, c) == "Pg"
    assert names.abbreviation("cpx", {"jd": 0.5, "di": 0.5}, c) == "Omp"
    assert names.abbreviation("st", {"fst": 1.0}, c) == "St"
    assert names.abbreviation("ctd", {"fctd": 1.0}, c) == "Cld"
    assert names.label(("Qz", "Grt", "H2O", "Amp", "Amp")) == "Grt 2Amp Qz H2O"
