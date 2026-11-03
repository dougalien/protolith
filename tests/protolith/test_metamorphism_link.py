"""Samples in and out of Metamorphism."""
import pytest

from metamorphism import bulk, point
from protolith.metamorphism_link import bulk_from_sample, to_sample
from protolith.sample import Phase, Sample


def _sample():
    return Sample(conditions={"t_c": 1100.0, "p_bar": 5000.0, "fo2": None, "log_fo2": None},
                  bulk_wt_pct={"SiO2": 50.0, "Al2O3": 16.0, "MgO": 10.0, "CaO": 12.0, "FeO": 9.0, "Na2O": 3.0},
                  total_grams=100.0,
                  phases=[Phase("olivine", 20.0, {"SiO2": 40.0, "MgO": 50.0, "FeO": 10.0})],
                  melt={"grams": 80.0, "wt_pct": {"SiO2": 52.5, "Al2O3": 20.0, "CaO": 15.0, "FeO": 8.75,
                                                  "Na2O": 3.75}},
                  written_by={"app": "Magma"})


def test_parts_of_a_sample():
    s = _sample()
    assert bulk_from_sample(s, "whole").wt_pct["MgO"] == pytest.approx(10.0)
    assert bulk_from_sample(s, "rock").wt_pct["MgO"] == pytest.approx(50.0)
    assert "MgO" not in bulk_from_sample(s, "melt").wt_pct
    assert bulk_from_sample(s, "melt", water="excess").water == "excess"
    with pytest.raises(ValueError):
        bulk_from_sample(s, "glass")


def test_point_to_sample_and_back(tmp_path):
    b = bulk.from_wt_pct(bulk.PRESETS["pelite"], water="excess")
    pt = point.equilibrium(b, 600, 6)
    s = to_sample(pt, b, parent="abc")
    assert s.parent == "abc" and s.written_by["app"] == "Metamorphism"
    assert s.conditions["p_bar"] == pytest.approx(6000.0)
    assert {p.name for p in s.phases} == {m.name for m in pt.minerals}
    back = Sample.load(s.save(tmp_path / "pt.sample"))
    assert back.total_grams == pytest.approx(s.total_grams)
    dry = to_sample(pt, b, keep_fluid=False)
    assert dry.fluid is None and dry.total_grams < s.total_grams
    # a rock out of Metamorphism goes back in as the same bulk (less the excess water)
    again = bulk_from_sample(dry, "whole")
    assert again.wt_pct["SiO2"] > b.wt_pct["SiO2"]
