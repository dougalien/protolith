"""Reaction on Protolith's shared Holland & Powell core (the "hp" database: thermo/hp_minerals.py)."""
import math

import pytest

from protolith.core.hp import endmembers as core
from reaction.app import config
from reaction.thermo import hp_minerals
from reaction.thermo.hkf import HKFSpecies


@pytest.fixture(scope="module")
def dbs(obigt_dir):
    from reaction.thermo.eosdb import load_eos_database
    return load_eos_database(obigt_dir, "current"), load_eos_database(obigt_dir, "hp")


def test_energy_scale_matches_the_apparent_gibbs_energy():
    """HP's G = H - TS moved onto the Benson-Helgeson scale: G at 25 C is dGf.  Against the ds62 values of
    the aq17 dataset (Miron et al. 2017), for minerals ds6.36 did not revise."""
    for name, em, dgf in (("albite", "ab", -3712.00), ("halite", "hlt", -384.25), ("diaspore", "dsp", -920.83),
                          ("quartz", "q", -856.43)):
        g = hp_minerals.HPMineral.of(name, em).gibbs(298.15, 1.0) / 1000.0
        assert g == pytest.approx(dgf, abs=0.2), name


def test_minerals_are_computed_by_the_core():
    m = hp_minerals.HPMineral.of("forsterite", "fo")
    for t, p in ((298.15, 1.0), (573.15, 85.9), (873.15, 2000.0)):
        assert m.gibbs(t, p) == pytest.approx(core.gibbs_j("fo", t, p) + 298.15 * m.s_elements)


def test_orthopyroxene_per_one_silicon():
    """HP writes enstatite as Mg2Si2O6, Reaction as MgSiO3: half the energy and volume."""
    en = hp_minerals.HPMineral.of("enstatite", "en", 0.5)
    assert en.gibbs(400.0, 10.0) == pytest.approx(0.5 * hp_minerals.HPMineral.of("x", "en").gibbs(400.0, 10.0))
    assert en.v0 == pytest.approx(31.31, abs=0.05)


def test_miron_species_reproduce_their_25c_values():
    sp = {s.name: s for s in hp_minerals.load_miron()}
    assert {"SiO2", "Al+3", "Ca+2", "Mg+2", "Na+", "K+", "Cl-", "HCO3-", "OH-"} <= set(sp)
    for s in sp.values():
        assert isinstance(s.eos, HKFSpecies)
        assert s.eos.gibbs(298.15, 1.0) == pytest.approx(s.eos.g0, abs=1e-6), s.name


def test_hp_database_takes_minerals_from_the_core(dbs):
    old, new = dbs
    for name in ("quartz", "calcite", "albite", "forsterite", "muscovite", "clinochlore", "rutile"):
        assert new.species[name].provenance.database == hp_minerals.SOURCE, name
    for name in ("SiO2", "Ca+2", "Al+3", "Na+"):
        assert new.species[name].provenance.database == hp_minerals.MIRON_SOURCE, name
    # what HP does not hold stays OBIGT's
    assert new.species["Fe+2"].provenance.database == "OBIGT"
    assert new.species["pyrite"].provenance.database == "OBIGT"
    assert "albite,low" not in new.species and "albite,high" in new.species        # one name, not a tie
    assert new.species["gibbsite"].provenance.database == "OBIGT"
    # and the minerals OBIGT lacks are there
    assert {"ulvospinel", "hercynite", "geikielite", "heulandite", "stilbite"} <= set(new.species)
    assert "ulvospinel" not in old.species
    assert any("Holland & Powell" in n for n in new.data_notes)


def test_hp_logk_close_to_obigt_where_both_are_good(dbs):
    """The two traditions agree to a few tenths of a log unit on quartz, calcite and albite; a bigger
    gap would mean a units or scale error, not a dataset difference."""
    old, new = dbs
    for name in ("quartz", "calcite", "albite", "muscovite", "corundum"):
        for t in (25.0, 150.0, 300.0):
            assert abs(new.species[name].logk(t) - old.species[name].logk(t)) < 0.5, (name, t)


def test_rutile_solubility_is_kept(dbs):
    """Dissolved Ti is defined from rutile solubility, so it follows the rutile it is given."""
    old, new = dbs
    for t in (25.0, 200.0, 300.0):
        assert new.species["rutile"].logk(t) == pytest.approx(old.species["rutile"].logk(t), abs=1e-9)


def test_engine_database_choice(monkeypatch):
    from reaction.app.engine import Engine
    monkeypatch.delenv("REACTION_DATABASE", raising=False)
    assert config.database() == "current" and Engine().database == "current"
    monkeypatch.setenv("REACTION_DATABASE", "HP")
    assert config.database() == "hp" and Engine().database == "hp"
    monkeypatch.setenv("REACTION_DATABASE", "nonsense")
    assert config.database() == "current"
    assert Engine(database="hp").database == "hp"


def test_hp_engine_runs_an_example(obigt_dir, monkeypatch):
    from reaction.app.engine import Engine
    from reaction.app.scenario import example_card
    monkeypatch.setenv("REACTION_DATA_DIR", str(obigt_dir.parent))
    run = next(iter(Engine(database="hp").run(example_card("serpentinization"))["modes"].values()))
    ph = [x for x in run["properties"]["pH"] if x is not None]
    assert ph and all(math.isfinite(x) for x in ph)


def test_obigt_species_keep_their_own_log_k(dbs):
    """The bridge: what stays OBIGT's is moved with its basis species, so its log K does not change, while
    the basis species themselves are Miron's (Na+ some 5.7 kJ above OBIGT's)."""
    old, new = dbs
    for name in ("NaSO4-", "CaSO4", "KSO4-", "halite", "sylvite", "gibbsite", "anhydrite", "CO2", "FeCl+"):
        for t in (25.0, 150.0, 300.0):
            assert new.species[name].logk(t) == pytest.approx(old.species[name].logk(t), abs=1e-6), (name, t)
    assert new.species["halite"].provenance.database == "OBIGT"
    assert new.species["halite"].logk(25.0) == pytest.approx(1.58, abs=0.02)   # halite solubility at 25 C


def test_iron_bridge_is_small_and_reported(dbs):
    _, new = dbs
    ov = new.hp_overlay
    assert set(ov.bridge) == {"Fe", "Mn"}
    assert all(abs(d) < 2000.0 for d in ov.bridge.values())                  # J per atom
    assert {"fayalite", "magnetite", "hematite"} <= {m for m, _ in ov.bridge_fit["Fe"]}
    assert any("bridge" in n for n in new.data_notes)


def test_switching_data_reloads_them(tmp_path):
    from reaction.app.engine import Engine
    e = Engine(data_dir=tmp_path, database="current")
    e._db = object()                                       # as if loaded
    assert e.set_database("hp") and e.database == "hp" and e._db is None
    assert not e.set_database("nonsense") and e.database == "hp"
    with e.run_lock:                                       # not in the middle of a run
        assert not e.set_database("current")
    assert e.database == "hp"


def test_control_window_offers_the_choice(tmp_path):
    from reaction.app.server import make_server
    from reaction.app.engine import Engine
    import json
    import threading
    import urllib.request
    httpd = make_server(0, workspace=tmp_path, engine=Engine(data_dir=tmp_path), model=None)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        def post(path, body):
            req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", json.dumps(body).encode(),
                                         {"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=10).read())
        state = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=10).read())
        assert state["database"]["name"] == "current"
        assert {c["key"] for c in state["database"]["choices"]} == {"current", "hp"}
        assert post("/api/database", {"name": "hp"}) == {"problems": []}
        assert httpd.session.engine.database == "hp"
        assert post("/api/database", {"name": "x"})["problems"]
        html = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10).read().decode()
        assert 'id="database"' in html
    finally:
        httpd.shutdown()
