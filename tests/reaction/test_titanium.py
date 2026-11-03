"""Dissolved titanium from rutile solubility (reaction/thermo/titanium.py)."""
import math

import pytest

from reaction.constants import LN10, R
from reaction.thermo import titanium


@pytest.mark.parametrize("key", ["Ks3", "Ks4", "Ks5"])
def test_fits_reproduce_knauss_table_3(key):
    """Each fitted log K is within the paper's 2-sigma (or 0.15) of every measured value at 200 bar."""
    for t_c, (value, err) in titanium._KS[key].items():
        assert titanium.log_k(key, t_c + 273.15, 200.0) == pytest.approx(value, abs=max(2 * err, 0.15)), t_c


@pytest.mark.parametrize("key, dg, tol", [("Ks3", 33.3e3, 0.4), ("Ks4", 43.5e3, 0.25), ("Ks5", 112.0e3, 0.25)])
def test_25c_matches_knauss_table_5(key, dg, tol):
    """Table 5's 25 C value is the authors' own regression, not a measurement, so the fit weighs it
    lightly; for Ks3 the tight 100 C point (sigma 0.03) pulls the fit 0.37 above it."""
    assert titanium.log_k(key, 298.15, 200.0) == pytest.approx(-dg / (R * 298.15 * LN10), abs=tol)


@pytest.mark.parametrize("t_c, p_gpa", [(800, 0.7), (800, 1.0), (900, 1.0), (1000, 0.7)])
def test_high_temperature_follows_antignano_and_manning(t_c, p_gpa):
    t = t_c + 273.15
    ppm = 10 ** (6.173 - 5425 / t + 178.4 * p_gpa / t)            # their Eq. 10
    assert titanium.log_k("Ks4", t, p_gpa * 1e4) == pytest.approx(math.log10(ppm / 47.867e3), abs=1e-9)


def test_bridge_is_continuous_and_flagged():
    lo, hi = titanium.T_MEASURED[1], titanium.AM08_T
    for t, p in ((lo, 5000.0), (hi, 5000.0)):
        assert titanium.log_k("Ks4", t - 1e-6, p) == pytest.approx(titanium.log_k("Ks4", t + 1e-6, p), abs=1e-4)
    assert not titanium.measured("Ks4", 773.15, 5000.0)
    assert titanium.measured("Ks4", 473.15, 200.0) and titanium.measured("Ks4", 1073.15, 1e4)


def test_pressure_follows_the_measured_volume():
    t = 473.15
    d = titanium.log_k("Ks4", t, 1200.0) - titanium.log_k("Ks4", t, 200.0)
    assert d == pytest.approx(3.4 * 0.1 * 1000 / (R * t * LN10))      # Delta V = -3.4 cm3: more soluble


def test_titanium_minerals_join_the_database(eos_db_current):
    db = eos_db_current
    for name in ("Ti(OH)4", "Ti(OH)3+", "Ti(OH)5-", "rutile", "ilmenite", "sphene"):
        assert name in db.species, name
    rut = db.species["rutile"]
    assert rut.reaction == {"rutile": -1.0, "Ti(OH)4": 1.0, "H2O": -2.0}
    for t_c in (25.0, 100.0, 250.0):                 # rutile = Ti(OH)4 - 2 H2O: log K is log Ks4
        assert rut.logk(t_c, 200.0) == pytest.approx(titanium.log_k("Ks4", t_c + 273.15, 200.0), abs=1e-6)


@pytest.fixture(scope="module")
def eos_db_current():
    from reaction.app import config
    from reaction.database import load_data0
    from reaction.thermo.eosdb import load_eos_database

    ext = config.external_dir()
    if not (ext / "OBIGT" / "inorganic_aq.csv").exists():
        pytest.skip("thermodynamic data not found; set REACTION_DATA_DIR")
    eq36 = ext / "EQ36_DB" / "data0.cmp"
    return load_eos_database(ext / "OBIGT", "current", eq36_database=load_data0(eq36) if eq36.exists() else None)


def test_rutile_in_fresh_water_reaches_its_solubility():
    """A little rutile in fresh water at 100 C and 200 bar: dissolved Ti is the measured solubility."""
    from reaction.app import config
    from reaction.app.engine import Engine
    from reaction.app.scenario import Scenario

    if not (config.external_dir() / "OBIGT" / "inorganic_aq.csv").exists():
        pytest.skip("thermodynamic data not found; set REACTION_DATA_DIR")
    sc, problems = Scenario(fluid="freshwater", t_start_c=100.0, t_end_c=100.0, p_start_bar=200.0,
                            p_end_bar=200.0, steps=3).changed({"reactants": "0.01 g rutile"})
    assert not problems, problems
    run = Engine().run(sc)["modes"]["static"]
    ti = run["elements"]["Ti"][-1]
    assert run["minerals"]["rutile"][-1] > 0                     # saturated: most of it stays
    assert math.log10(ti) == pytest.approx(-7.72, abs=0.3)        # Knauss et al. (2001), near-neutral pH
