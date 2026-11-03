"""Reaction's database for the link tests: skipped where Reaction's reference data is not installed."""
import pytest

from reaction.app import config


@pytest.fixture(scope="session")
def eos_db_current():
    from reaction.database import load_data0
    from reaction.thermo.eosdb import load_eos_database

    ext = config.external_dir()
    obigt, eq36 = ext / "OBIGT", ext / "EQ36_DB" / "data0.cmp"
    if not (obigt / "inorganic_aq.csv").exists():
        pytest.skip(f"Reaction's reference data is not installed in {ext}")
    return load_eos_database(obigt, "current", eq36_database=load_data0(eq36) if eq36.exists() else None)
