"""The sample file and the Magma -> Reaction link."""
import json

import numpy as np
import pytest

from protolith.reaction_link import FORMULAS, recast_phase, to_reactants
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


def test_olivine_recast_keeps_fo_and_mass():
    grams, left, note = recast_phase(_olivine(0.9, 10.0))
    assert not left and not note
    assert sum(grams.values()) == pytest.approx(10.0)
    # Fo90 by moles: forsterite 140.69 g/mol, fayalite 203.77 g/mol
    n_fo, n_fa = grams["forsterite"] / 140.6931, grams["fayalite"] / 203.7771
    assert n_fo / (n_fo + n_fa) == pytest.approx(0.9, abs=1e-5)


def test_plagioclase_an60():
    an, ab = 0.6, 0.4
    wt = {"CaO": an * 56.0774, "Na2O": ab * 0.5 * 61.979, "Al2O3": (an + ab * 0.5) * 101.961,
          "SiO2": (2 * an + 3 * ab) * 60.0843}
    grams, left, _ = recast_phase(Phase("feldspar", 5.0, wt))
    assert not left
    n_an, n_ab = grams["anorthite"] / 278.207, grams["albite"] / 262.223
    assert n_an / (n_an + n_ab) == pytest.approx(0.6, abs=1e-4)


def test_titanium_is_listed_not_dropped():
    wt = {"FeO": 60.0, "Fe2O3": 30.0, "TiO2": 10.0}              # a titanomagnetite
    grams, left, note = recast_phase(Phase("titanomagnetite", 2.0, wt))
    assert "magnetite" in grams
    assert left["TiO2"] == pytest.approx(0.2, rel=0.02)
    assert "TiO2" in note and "no mineral" in note
    assert sum(grams.values()) + sum(left.values()) == pytest.approx(2.0)


def test_phase_without_counterpart_is_reported():
    s = _sample(_olivine(), Phase("sphene", 1.0, {"CaO": 28.6, "TiO2": 40.8, "SiO2": 30.6}))
    r = to_reactants(s, scale_to=1000.0)
    assert sum(x["amount"] for x in r.reactants) == pytest.approx(1000.0 * 10 / 11, rel=1e-4)
    assert r.left_over["sphene"]["TiO2"] == pytest.approx(1000 / 11 * 0.408, rel=1e-3)
    assert any("sphene" in n and "not on the card" in n for n in r.notes)


def test_tridymite_goes_on_as_quartz():
    grams, left, note = recast_phase(Phase("tridymite", 1.0, {"SiO2": 100.0}))
    assert grams == {"quartz": pytest.approx(1.0)} and not left and "as quartz" in note


def test_hp_run_to_reaction_card():
    """A Holland & Powell basalt step goes all the way to card reactants, with every gram accounted for."""
    from magma.composition import Composition
    from magma.hp import engine
    from protolith.magma_link import from_step

    basalt = Composition({"SiO2": 50.5, "TiO2": 1.7, "Al2O3": 14.7, "FeO": 9.4, "Fe2O3": 1.1, "MgO": 7.6,
                          "CaO": 11.4, "Na2O": 2.8, "K2O": 0.16})
    r = engine.equilibrium(engine.to_components(basalt), 1100.0, 1000.0, fo2="QFM")
    s = from_step(r, fo2="QFM", note="basalt at 1100 C")
    assert s.provenance["engine"] == "hp" and s.phases
    assert s.total_grams == pytest.approx(r.liquid_grams + sum(p.grams for p in r.solids), rel=1e-9)
    assert sum(s.bulk_wt_pct.values()) == pytest.approx(100.0)
    back = Sample.from_dict(json.loads(json.dumps(s.to_dict())))
    card = to_reactants(back)
    carried = sum(x["amount"] for x in card.reactants)
    left = sum(sum(v.values()) for v in card.left_over.values())
    assert carried + left == pytest.approx(back.solid_grams, rel=1e-4)
    for x in card.reactants:
        assert x["name"] in FORMULAS and x["unit"] == "g"


def test_formulas_match_reactions_database(eos_db_current):
    """Each mineral named here is in Reaction's database with the same cations."""
    from protolith.reaction_link import parse_formula

    for name, f in FORMULAS.items():
        sp = eos_db_current.species.get(name)
        assert sp is not None, f"{name} is not in Reaction's database"
        ours = {e: n for e, n in parse_formula(f).items() if e not in ("O", "H")}
        theirs = {e: n for e, n in sp.elements.items() if e not in ("O", "H")}
        assert ours == pytest.approx(theirs), name
