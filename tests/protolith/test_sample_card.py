"""Samples onto Reaction's card: rock as minerals, melt as glass, and both apps' ends of the link."""
import json
import threading
import urllib.request

import pytest

from magma.composition import Composition
from magma.hp import engine as hp
from protolith.magma_link import from_step, merge, step_phases
from protolith.reaction_link import MAX_ON_CARD, card_for, glass_oxides
from protolith.sample import Sample, rock_only

BASALT = Composition({"SiO2": 50.5, "TiO2": 1.7, "Al2O3": 14.7, "FeO": 9.4, "Fe2O3": 1.1, "MgO": 7.6,
                      "CaO": 11.4, "Na2O": 2.8, "K2O": 0.16})


@pytest.fixture(scope="module")
def step():
    return hp.equilibrium(hp.to_components(BASALT), 1100.0, 1000.0, fo2="QFM")


@pytest.fixture(scope="module")
def sample(step):
    return from_step(step, fo2="QFM")


def _mass(card):
    return sum(r["amount"] for r in card.reactants)


@pytest.mark.parametrize("take", ["rock", "melt", "both"])
def test_card_carries_the_grams_asked_for(sample, take):
    card = card_for(sample, 1000.0, take)
    assert len(card.reactants) <= MAX_ON_CARD
    assert _mass(card) == pytest.approx(1000.0, rel=2e-3)        # hydrous minerals in the rest glass lose their H2O
    glasses = [r for r in card.reactants if "oxides" in r]
    if take == "rock":
        assert all(r["name"].startswith("rest of") for r in glasses)     # only what has no mineral
    else:
        melt = next(r for r in glasses if r["name"] == "Magma glass 1100 °C")
        share = sample.melt["grams"] / (sample.melt["grams"] + (sample.solid_grams if take == "both" else 0))
        assert melt["amount"] == pytest.approx(1000.0 * share, rel=1e-5)
        assert sum(melt["oxides"].values()) == pytest.approx(100.0, abs=1e-3)


def test_glass_oxides_put_iron_as_feo_with_its_ferric_share():
    ox, ff = glass_oxides({"SiO2": 50.0, "FeO": 9.0, "Fe2O3": 1.0, "H2O": 2.0})
    assert "Fe2O3" not in ox and "H2O" not in ox
    n2, n3 = 9.0 / 71.8444, 2 * 1.0 / 159.6882
    assert ff == pytest.approx(n3 / (n2 + n3))
    assert ox["FeO"] / ox["SiO2"] == pytest.approx((n2 + n3) * 71.8444 / 50.0, rel=1e-5)


def test_titanium_goes_on_as_titanium_minerals(sample):
    card = card_for(sample, 1000.0, "rock")
    assert not any("TiO2" in v for v in card.left_over.values())
    names = {r["name"] for r in card.reactants}
    if any(p.wt_pct.get("TiO2", 0) > 0 for p in sample.phases):
        assert names & {"rutile", "ilmenite", "sphene"}


def test_rock_only_drops_the_melt_and_keeps_the_parent(sample):
    rock = rock_only(sample)
    assert rock.melt is None and rock.parent == sample.parent
    assert rock.total_grams == pytest.approx(sample.solid_grams)


def test_merge_piles_up_a_cumulate(step):
    a, _ = step_phases(step)
    pile = merge(merge([], a), a)
    for p, q in zip(sorted(a, key=lambda p: p.name), sorted(pile, key=lambda p: p.name)):
        assert q.grams == pytest.approx(2 * p.grams)
        assert q.wt_pct == pytest.approx(p.wt_pct)


def test_reaction_reads_a_glass_card_back(sample):
    """The glass keeps its oxides through Reaction's card: saved, reloaded, and named again in text."""
    from reaction.app import rocks
    from reaction.app.scenario import Scenario

    card = card_for(sample, 500.0, "both")
    sc, problems = Scenario().changed({"reactants": card.reactants})
    assert not problems, problems
    back = Scenario.from_dict(json.loads(json.dumps(sc.to_dict())))
    glass = next(r for r in back.reactants if r["name"] == "Magma glass 1100 °C")
    assert glass["oxides"] and 0 < glass["ferric_fraction"] < 1
    rocks.GLASSES.clear()                                   # a fresh session: the saved card brings it back
    Scenario.from_dict(sc.to_dict())
    assert rocks.find("Magma glass 1100 °C") is not None
    text = "; ".join(f"{r['amount']} {r['unit']} {r['name']}" for r in back.reactants)
    again, problems = Scenario().changed({"reactants": text})
    assert not problems
    assert next(r for r in again.reactants if r["name"] == "Magma glass 1100 °C")["oxides"] == glass["oxides"]


def test_magma_saves_a_sample_of_a_run(tmp_path):
    """Magma's server keeps a sample per step and serves it as a file Sample.load can read."""
    from magma.app.server import make_server

    httpd = make_server(0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        st = httpd.state
        st.start({"engine": "hp", "process": "crystallize", "mode": "fractional", "t_start": 1150, "t_end": 1130,
                  "step": 10, "p_bar": 1000, "fo2": "QFM", "bulk": BASALT.wt})
        while st.status == "running":
            with st.cond:
                st.cond.wait(timeout=5)
        assert st.status == "done", st.message
        assert len(st.samples) == len(st.steps) and all(st.samples)
        port = httpd.server_address[1]
        for part in ("all", "rock"):
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/sample?step=-1&part={part}",
                                         headers={"Host": f"127.0.0.1:{port}"})
            with urllib.request.urlopen(req) as r:
                assert "attachment" in r.headers["Content-Disposition"]
                p = tmp_path / f"{part}.sample"
                p.write_bytes(r.read())
            smp = Sample.load(p)
            assert (smp.melt is None) == (part == "rock")
            assert smp.written_by["app"] == "Magma" and smp.provenance["engine"] == "hp"
        # the cumulate: the last sample's solids are every step's solids together
        removed = sum(p["grams"] for p in st.steps[-1]["solids"] if p["name"] != "water")
        assert st.samples[-1].solid_grams == pytest.approx(removed, rel=1e-6)
    finally:
        httpd.shutdown()


def test_reaction_reacts_a_magma_sample(sample):
    """Seawater and the Magma basalt (rock and glass) on Reaction's real engine."""
    from reaction.app import config
    from reaction.app.engine import Engine
    from reaction.app.scenario import Scenario

    if not (config.external_dir() / "OBIGT" / "inorganic_aq.csv").exists():
        pytest.skip("Reaction's reference data is not installed")
    card = card_for(sample, 10.0, "both")
    sc, problems = Scenario(t_start_c=25.0, t_end_c=25.0, steps=4).changed({"reactants": card.reactants})
    assert not problems, problems
    result = Engine().run(sc)
    run = result["modes"]["static"]
    assert all(v is not None for v in run["properties"]["pH"])
    assert run["elements"]["Si"][-1] > 1e-5                    # the rock and glass dissolve ...
    assert any(v[-1] > 0 for v in run["minerals"].values())    # ... and secondary minerals form
    assert run["elements"]["Ti"][-1] > 0                       # titanium reaches the fluid ...
    assert not any("Ti is left out" in n for n in result["notes"])
