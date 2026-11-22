"""The sample file: writing, reading back, and clear errors for bad files."""
import json

import numpy as np
import pytest

from protolith.sample import Phase, Sample, SampleError


def _olivine(fo=0.9, grams=10.0):
    mg, fe = 2 * fo, 2 * (1 - fo)                                  # per formula Mg2SiO4-Fe2SiO4
    wt = {"MgO": mg * 40.3044, "FeO": fe * 71.8444, "SiO2": 60.0843}
    return Phase("olivine", grams, wt, {"fo": fo, "fa": 1 - fo}, "", "test")


def _sample(*phases):
    return Sample(conditions={"t_c": 1200.0, "p_bar": 1000.0, "fo2": "QFM", "log_fo2": None},
                  bulk_wt_pct={"SiO2": 50.0, "MgO": 50.0}, total_grams=sum(p.grams for p in phases),
                  phases=list(phases), written_by={"app": "test"})


def test_round_trip(tmp_path):
    s = _sample(_olivine())
    path = s.save(tmp_path / "rock")
    assert path.suffix == ".sample"
    back = Sample.load(path)
    assert back.id == s.id and back.phases[0].grams == 10.0
    assert back.phases[0].wt_pct == pytest.approx(s.phases[0].wt_pct)
    kid = back.child(note="altered")
    assert kid.parent == s.id and kid.id != s.id and kid.note == "altered"


@pytest.mark.parametrize("change, words", [
    ({"format": "other"}, "not a Protolith sample"),
    ({"version": 99}, "newer than this app reads"),
    ({"bulk_wt_pct": {"Unobtanium": 1}}, "unknown oxide"),
    ({"conditions": {"t_c": "hot", "p_bar": 1}}, "number for t_c"),
])
def test_bad_files_say_what_is_wrong(tmp_path, change, words):
    d = _sample(_olivine()).to_dict()
    d.update(change)
    p = tmp_path / "bad.sample"
    p.write_text(json.dumps(d))
    with pytest.raises(SampleError, match=words):
        Sample.load(p)
