"""Reaction is OBIGT only (Douglas, 2026-11-03): no Holland & Powell data may reach its calculations."""
import os
import subprocess
import sys

from reaction.app import config


def test_only_obigt_is_offered():
    assert list(config.DATABASES) == ["current"] and config.database() == "current"


def test_reaction_never_loads_the_hp_core():
    code = ("import sys, reaction.app.server, reaction.app.engine, reaction.thermo.eosdb, protolith.reaction_link;"
            "bad=[m for m in sys.modules if m.startswith(('protolith.core', 'magma', 'metamorphism'))];"
            "print(bad); sys.exit(1 if bad else 0)")
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
