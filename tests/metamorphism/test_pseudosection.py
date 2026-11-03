"""The grid, its fields and boundaries, on the aluminosilicate system (pure phases: fast and exact)."""
import numpy as np
import pytest

from metamorphism import bulk, pseudosection
from protolith.core.hp.endmembers import gibbs

AL2SIO5 = {"SiO2": 60.083, "Al2O3": 101.961}       # one mole of each


@pytest.fixture(scope="module")
def grid():
    b = bulk.from_wt_pct(AL2SIO5, name="Al2SiO5")
    return pseudosection.compute(b, pseudosection.axis(400, 800, 50), pseudosection.axis(1, 10, 1), workers=1)


def _stable(t_c, p):
    g = {n: gibbs(n, t_c + 273.15, p) for n in ("ky", "sill", "and")}
    return {"ky": "Ky", "sill": "Sil", "and": "And"}[min(g, key=g.get)]


def test_every_cell_is_the_polymorph_with_lowest_g(grid):
    for i, p in enumerate(grid.p_kbar):
        for j, t in enumerate(grid.t_c):
            assert grid.points[i][j].assemblage == (_stable(t, p),)


def test_three_fields_around_the_triple_point(grid):
    assert sorted(f.label for f in grid.fields) == ["And", "Ky", "Sil"]
    assert all(f.variance == 3 for f in grid.fields)        # two components, one phase
    assert sum(len(f.cells) for f in grid.fields) == 9 * 10
    assert grid.field_at(400, 10).label == "Ky"
    assert grid.field_at(800, 3).label == "Sil"
    assert grid.field_at(400, 1).label == "And"


def test_boundaries_separate_fields(grid):
    segs = grid.boundaries()
    assert segs
    for (t1, p1), (t2, p2) in segs:
        assert t1 == t2 or p1 == p2                           # grid edges
        assert 375 <= min(t1, t2) and max(t1, t2) <= 825


def test_mode_grid_and_file_round_trip(grid, tmp_path):
    ky = grid.mode_grid("Ky")
    assert np.nanmax(ky) == pytest.approx(100.0)
    back = pseudosection.Pseudosection.load(grid.save(tmp_path / "a.pseudosection"))
    assert [f.label for f in back.fields] == [f.label for f in grid.fields]
    assert back.field_of == grid.field_of


def test_parallel_rows_match(grid):
    b = bulk.from_wt_pct(AL2SIO5)
    par = pseudosection.compute(b, grid.t_c, grid.p_kbar, workers=2)
    assert par.field_of == grid.field_of


def test_axis():
    assert pseudosection.axis(450, 500, 25) == [450, 475, 500]
    with pytest.raises(ValueError):
        pseudosection.axis(500, 450, 25)
