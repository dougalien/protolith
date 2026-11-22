"""The core stands alone: importing it loads none of the modules that use it."""
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"


def test_core_imports_no_module():
    code = ("import sys; import protolith.core.hp.minimize, protolith.core.hp.solutions, protolith.core.hp.endmembers; "
            "print(sorted({m.split('.')[0] for m in sys.modules} & {'metamorphism'}), "
            "'protolith.sample' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                         env={**os.environ, "PYTHONPATH": str(SRC)}).stdout.split()
    assert out == ["[]", "False"]


def test_dataset_loads_from_the_core():
    from protolith.core.hp.endmembers import DATA

    assert len(DATA) == 291
