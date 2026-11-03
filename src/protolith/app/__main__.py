"""``python -m protolith.app`` (or Protolith.exe) starts every module and opens the home window."""
from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import threading
import urllib.request
import webbrowser

# One thread for numpy's linear algebra, before numpy loads: Magma's matrices are small, and on Windows
# several threads fighting over them made each step many times slower (see magma.app.__main__).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

from .server import DEFAULT_PORT, Shell  # noqa: E402


def _check(shell: Shell) -> int:
    """Start, ask the home window for its module list, and stop: a quick test that the program works."""
    threading.Thread(target=shell.serve, daemon=True).start()
    try:
        with urllib.request.urlopen(f"{shell.url}/api/modules", timeout=30) as r:
            names = [m["name"] for m in __import__("json").loads(r.read())["modules"] if m["ready"]]
        for m in (shell.magma, shell.reaction):
            port = m.server_address[1]
            req = urllib.request.Request(f"http://127.0.0.1:{port}/control", headers={"Host": f"127.0.0.1:{port}"})
            with urllib.request.urlopen(req, timeout=30) as r:
                assert r.status == 200
        print("Protolith check passed: " + ", ".join(names) + " answer.")
        return 0
    except Exception as exc:                      # noqa: BLE001 - report any failure as a failed check
        print(f"Protolith check failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        shell.stop()


def main() -> None:
    multiprocessing.freeze_support()           # Protolith.exe: a spawned worker runs its task, not the app
    ap = argparse.ArgumentParser(description="Protolith: a geochemical calculator in modules, by Dougalien Systems")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help="port of the home window")
    ap.add_argument("--no-browser", action="store_true", help="do not open the home window")
    ap.add_argument("--check", action="store_true", help="start, check that every module answers, and stop")
    args = ap.parse_args()
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW("Protolith, by Dougalien Systems")
        from magma.app.__main__ import _no_quick_edit
        _no_quick_edit()                       # a click in the console must not freeze the app
    if args.check:
        sys.exit(_check(Shell().start(0, 0, 0)))
    shell = Shell().start(args.port)
    print("Protolith, by Dougalien Systems (dougalien.com)")
    print(f"Home window:  {shell.url}/")
    print(f"Magma:        http://127.0.0.1:{shell.magma.server_address[1]}/control")
    print(f"Reaction:     http://127.0.0.1:{shell.reaction.server_address[1]}/control")
    print("Close this window or press Ctrl+C to stop every module.")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(f"{shell.url}/")).start()
    try:
        shell.serve()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
