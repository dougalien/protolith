"""``python -m metamorphism.app`` starts Metamorphism's local server on its own and opens the control window.
Inside Protolith (``python -m protolith.app``) the shell starts it with the other modules."""
from __future__ import annotations

import argparse
import multiprocessing
import os
import threading
import webbrowser

# One thread for numpy's linear algebra in this process and in the grid's worker processes (see
# magma.app.__main__).  Set before numpy loads.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

from .server import DEFAULT_PORT, make_server  # noqa: E402


def main() -> None:
    multiprocessing.freeze_support()          # a frozen exe: a spawned worker runs its row, not the app
    ap = argparse.ArgumentParser(description="Metamorphism: a rock at a new temperature and pressure, by Dougalien Systems")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no-browser", action="store_true", help="do not open the windows")
    args = ap.parse_args()
    httpd = make_server(args.port)
    url = f"http://127.0.0.1:{httpd.server_address[1]}"
    print("Metamorphism, by Dougalien Systems (dougalien.com)")
    print(f"Metamorphism is running at {url}/control  (results window: {url}/results)")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(f"{url}/control")).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
