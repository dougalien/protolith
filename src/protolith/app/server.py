"""Protolith's shell: one program that runs every module and a home window that opens them.

Each module keeps its own local server and windows (Magma on 8766, Reaction on 8790, as when they run
alone), so nothing in a module changes to live inside the shell.  The shell adds:

* a home window (port 8800) that lists the modules and opens their windows;
* hand-offs between modules in the same process: Magma's "Send to Reaction" puts a step of a Magma run
  on Reaction's card without a file in between.

Like the modules, the home server listens on the loopback address only and refuses requests whose Host
or Origin is not its own, so a web page you happen to have open cannot drive it.
"""
from __future__ import annotations

import json
import mimetypes
import threading
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .. import __version__

STATIC = Path(__file__).resolve().parent / "static"
DEFAULT_PORT = 8800
MAX_BODY = 100_000

# Modules to come: shown on the home window so the plan is visible, not openable yet.
PLANNED = (
    {"key": "metamorphism", "name": "Metamorphism",
     "about": "Rocks re-equilibrating at new temperature and pressure, with the same Holland and Powell data as Magma."},
    {"key": "surface", "name": "Surface",
     "about": "Weathering, soils and diagenesis at low temperature, on Reaction's water chemistry."},
)


def _url(httpd) -> str:
    return f"http://127.0.0.1:{httpd.server_address[1]}"


@dataclass
class Shell:
    """The running modules.  ``start`` binds every server; ``serve`` runs them until ``stop``."""
    home: ThreadingHTTPServer | None = None
    magma: ThreadingHTTPServer | None = None
    reaction: ThreadingHTTPServer | None = None
    threads: list = field(default_factory=list)
    stopped: threading.Event = field(default_factory=threading.Event)

    def start(self, port: int = DEFAULT_PORT, magma_port: int | None = None, reaction_port: int | None = None,
              reaction_kw: dict | None = None) -> "Shell":
        from magma.app import server as magma_server
        from reaction.app import server as reaction_server

        self.magma = magma_server.make_server(magma_server.DEFAULT_PORT if magma_port is None else magma_port)
        self.reaction = reaction_server.make_server(reaction_server.DEFAULT_PORT if reaction_port is None
                                                    else reaction_port, **(reaction_kw or {}))
        self.magma.state.send_sample = self.send_to_reaction          # type: ignore[attr-defined]
        self.home = _bind(port)
        self.home.shell = self                                         # type: ignore[attr-defined]
        return self

    # ---- hand-offs ------------------------------------------------------------------------------
    def send_to_reaction(self, sample: dict, take: str = "rock", grams: float = 100.0) -> dict:
        """A sample (as written in a .sample file) onto Reaction's card; the reply says where to look."""
        from reaction.app.server import load_sample

        out = load_sample(self.reaction.session, sample, grams, take)    # type: ignore[union-attr]
        out["open"] = f"{_url(self.reaction)}/control"
        return out

    # ---- what the home window shows --------------------------------------------------------------
    def modules(self) -> dict:
        from magma import __version__ as magma_version
        from reaction.app import config

        has_data = (config.external_dir() / "OBIGT" / "inorganic_aq.csv").exists()
        mods = [
            {"key": "magma", "name": "Magma", "ready": True, "version": magma_version,
             "about": "Melting and crystallization of silicate melts (Holland and Powell, or MELTS).",
             "control": f"{_url(self.magma)}/control", "results": f"{_url(self.magma)}/results"},
            {"key": "reaction", "name": "Reaction", "ready": True,
             "about": "Water and rock: speciation, mineral reactions and reaction paths in an aqueous fluid.",
             "control": f"{_url(self.reaction)}/control", "results": f"{_url(self.reaction)}/results",
             "note": "" if has_data else ("Reaction's thermodynamic data is not installed yet; its window "
                                          "says how to get it.")},
        ]
        mods += [dict(m, ready=False) for m in PLANNED]
        return {"version": __version__, "modules": mods}

    # ---- running ---------------------------------------------------------------------------------
    def serve(self) -> None:
        """Serve every module in the background and the home window here, until ``stop``."""
        for httpd in (self.magma, self.reaction):
            t = threading.Thread(target=httpd.serve_forever, daemon=True)   # type: ignore[union-attr]
            t.start()
            self.threads.append(t)
        try:
            self.home.serve_forever()                                       # type: ignore[union-attr]
        finally:
            self.close()

    def stop(self) -> None:
        if self.stopped.is_set():
            return
        self.stopped.set()
        # shutdown() waits for serve_forever to return, so never call it from a request on that server
        threading.Thread(target=self._shutdown, daemon=True).start()

    def _shutdown(self) -> None:
        for httpd in (self.magma, self.reaction, self.home):
            if httpd is not None:
                httpd.shutdown()

    def close(self) -> None:
        for httpd in (self.magma, self.reaction, self.home):
            if httpd is not None:
                httpd.server_close()

    @property
    def url(self) -> str:
        return _url(self.home)


class Handler(BaseHTTPRequestHandler):
    server_version = "Protolith"
    protocol_version = "HTTP/1.1"

    @property
    def shell(self) -> Shell:
        return self.server.shell                 # type: ignore[attr-defined]

    def log_message(self, fmt, *args):
        pass

    def _allowed(self) -> bool:
        port = self.server.server_address[1]
        ok_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        if self.headers.get("Host", "") not in ok_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in ok_hosts}

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        self._send(status, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def _file(self, p: Path) -> None:
        p = p.resolve()
        if STATIC not in p.parents or not p.is_file():
            return self._json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self._send(200, p.read_bytes(), ctype)

    def do_GET(self) -> None:
        if not self._allowed():
            return self._json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
        path = urlparse(self.path).path
        if path in ("/", "/home"):
            return self._file(STATIC / "home.html")
        if path == "/favicon.ico":
            return self._file(STATIC / "protolith.ico")
        if path.startswith("/static/"):
            return self._file(STATIC / path[len("/static/"):])
        if path == "/api/modules":
            return self._json(self.shell.modules())
        return self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if not self._allowed():
            return self._json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self._json({"error": "request too large"}, 413)
        self.rfile.read(n)
        if urlparse(self.path).path == "/api/quit":
            self._json({"ok": True})
            self.shell.stop()
            return
        return self._json({"error": "not found"}, 404)


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False      # as in Reaction: on Windows a shared port silently loses requests


def _bind(port: int) -> ThreadingHTTPServer:
    """The home server on ``port``, or the next free one; ``port=0`` asks the system for any."""
    last: OSError | None = None
    for p in ([0] if port == 0 else range(port, port + 20)):
        try:
            return _Server(("127.0.0.1", p), Handler)
        except OSError as exc:
            last = exc
    raise OSError(f"no free port from {port} to {port + 19}: {last}")
