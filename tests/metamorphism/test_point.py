"""One equilibrium: textbook assemblages from the metapelite set of White et al. (2014), with MnO."""
import pytest

from metamorphism import bulk, point

# an aluminous, calcium-poor pelite (the chloritoid-staurolite sequence of Barrovian schists)
AL_PELITE = {"SiO2": 50.0, "TiO2": 0.8, "Al2O3": 26.0, "FeO": 11.0, "Fe2O3": 0.5, "MnO": 0.2, "MgO": 1.5,
             "CaO": 0.1, "Na2O": 0.5, "K2O": 3.5, "H2O": 6.0}


@pytest.fixture(scope="module")
def al_pelite():
    return bulk.from_wt_pct(AL_PELITE, water="excess", name="Al pelite")


def test_chloritoid_zone(al_pelite):
    pt = point.equilibrium(al_pelite, 500, 6)
    assert pt.converged
    assert {"Cld", "Chl", "Ms", "Qz", "H2O"} <= set(pt.assemblage)
    assert "St" not in pt.assemblage
    cld = next(m for m in pt.minerals if m.abbr == "Cld")
    assert cld.numbers["Mg#"] < 20                     # iron-rich chloritoid, as in Barrovian schists
    assert cld.formula.endswith("O5(OH)2")


def test_staurolite_zone(al_pelite):
    pt = point.equilibrium(al_pelite, 600, 8)
    assert {"St", "Grt", "Bt", "Ms", "Qz"} <= set(pt.assemblage)
    assert "Cld" not in pt.assemblage
    st = next(m for m in pt.minerals if m.abbr == "St")
    assert 10 < st.mode < 40
    grt = next(m for m in pt.minerals if m.abbr == "Grt")
    assert grt.numbers["Alm"] > 70 and 0 < grt.numbers["Sps"] < 15     # almandine with some spessartine
    assert sum(m.mode for m in pt.minerals) == pytest.approx(100.0)
    assert pt.fluid is not None and pt.fluid.grams > 0


def test_warm_start_gives_the_same_answer(al_pelite):
    a = point.equilibrium(al_pelite, 600, 8)
    b = point.equilibrium(al_pelite, 610, 8, previous=a)
    c = point.equilibrium(al_pelite, 610, 8)
    assert b.assemblage == c.assemblage
    assert b.g == pytest.approx(c.g, abs=1e-3)


def test_point_round_trips_through_a_dict(al_pelite):
    pt = point.equilibrium(al_pelite, 600, 8)
    back = point.Point.from_dict(pt.to_dict())
    assert back.assemblage == pt.assemblage
    assert back.minerals[0].wt_pct == pt.minerals[0].wt_pct


def test_igneous_set_still_runs(al_pelite):
    ig = bulk.from_wt_pct(AL_PELITE, water="excess", system="igneous")
    assert "MnO" in ig.left_out
    pt = point.equilibrium(ig, 600, 8)
    assert pt.converged and pt.fluid is not None and pt.fluid.hp == "fl"


def test_bad_conditions_are_refused(al_pelite):
    with pytest.raises(ValueError):
        point.equilibrium(al_pelite, 500, 0)
