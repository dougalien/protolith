"""The P-T path: point spacing, the facies background, a short path solved, and the window's inputs."""
import pytest

from metamorphism import bulk as bulk_mod
from metamorphism import facies, path
from metamorphism.app.server import CARDS, parse_inputs


def test_points_even_and_through_the_ends():
    tp = path.points([(450, 4), (600, 7.5), (700, 8)], 16)
    assert len(tp) == 16 and tp[0] == (450, 4) and tp[-1] == (700, 8)
    assert all(a[0] < b[0] for a, b in zip(tp, tp[1:]))
    with pytest.raises(ValueError):
        path.points([(450, 4)], 5)


def test_al2sio5_triple_point_from_ds62():
    d = facies.diagram()
    t, p = d["triple_point"]
    assert 500 < t < 560 and 3.5 < p < 5            # ds6.2 puts it near 536 degC and 4.3 kbar
    assert {ln["label"] for ln in d["lines"]} >= {"Ky = And", "Ky = Sil", "And = Sil"}
    assert len(d["facies"]) == 8


def test_parse_path_and_every_path_card():
    for c in CARDS:
        if c["kind"] != "path":
            continue
        b, run = parse_inputs({"bulk": bulk_mod.PRESETS[c["rock"]], "system": c["system"], "water": c["water"],
                               "kind": "path", "path": c["path"], "n": c["n"]})
        assert len(run["tp"]) == c["n"]
    with pytest.raises(ValueError):
        parse_inputs({"bulk": bulk_mod.PRESETS["pelite"], "kind": "path", "path": [[450, 4]], "n": 5})


def test_short_path_solves():
    b = bulk_mod.from_wt_pct(bulk_mod.PRESETS["pelite"], water="excess", name="pelite", system="metapelite")
    pts, failed = path.compute(b, [(500, 5), (560, 6)], workers=1)
    assert not failed and all(p is not None for p in pts)
    assert "Grt" in pts[1].assemblage
