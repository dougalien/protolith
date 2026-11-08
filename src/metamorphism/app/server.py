"""A small local web server for Protolith, the Metamorphism module's two windows (control, results).

Standard library only, like Magma's and Reaction's.  Both windows follow one shared state through a
server-sent-event stream.  The server listens on the loopback address only and rejects requests whose
Host or Origin is not the loopback address, so a web page you happen to have open cannot drive it.

A run goes in a background thread: one equilibrium, or a pseudosection whose pressure rows run in
parallel processes (``metamorphism.pseudosection.compute``).  Each finished row is grouped into fields
at once, so the results window draws the diagram as it fills in, and Stop ends the rows still running.
"""
from __future__ import annotations

import json
import math
import mimetypes
import os
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

from .. import __version__
from .. import bulk as bulk_mod
from .. import facies, names, pseudosection
from .. import path as path_mod
from ..point import Point, components_present, equilibrium

STATIC = Path(__file__).resolve().parent / "static"
PAGES = {"/": "control.html", "/control": "control.html", "/results": "results.html"}
DEFAULT_PORT = 8810            # Magma 8766, Reaction 8790, Protolith's home window 8800
MAX_BODY = 200_000
MAX_FILE = 50_000_000          # an opened pseudosection file
MAX_POINTS = 1600
SECONDS_PER_POINT = 6.0        # a typical pelite point with a warm start, for the time estimate

OXIDES = ("SiO2", "TiO2", "Al2O3", "Cr2O3", "FeO", "Fe2O3", "MnO", "MgO", "CaO", "Na2O", "K2O", "H2O")
SOURCES = {
    "pelite": "A typical shale-derived pelite (rounded, not a published analysis).",
    "aluminous pelite": "An Al- and Fe-rich, Ca-poor mudstone (rounded), the kind that grows chloritoid and staurolite.",
    "world median pelite": "Forshaw and Pattison (2023), the default rock of MAGEMin's metapelite set.",
    "metabasite": "A MORB-like basalt with the water of a hydrated sea floor (rounded).",
}
SYSTEM_LABEL = {"metapelite": "Metapelite (White et al. 2014)", "igneous": "Igneous (Holland et al. 2018)"}

# Starting cards: each fills in a rock and a run that shows it well.
CARDS = [
    {"key": "barrovian-path", "title": "Barrovian pelite", "group": "path",
     "blurb": "A mudstone heated and buried on a clockwise path, greenschist to upper amphibolite: chlorite gives "
              "way to garnet, staurolite and then kyanite or sillimanite.",
     "rock": "pelite", "system": "metapelite", "water": "excess", "kind": "path",
     "path": [[450, 4], [600, 7.5], [700, 8]], "n": 16},
    {"key": "buchan-path", "title": "Low-pressure (Buchan) pelite", "group": "path",
     "blurb": "The same rock heated at shallow depth, as near an intrusion: andalusite, then sillimanite as muscovite "
              "breaks down, then the first melt with cordierite.",
     "rock": "pelite", "system": "metapelite", "water": "excess", "kind": "path",
     "path": [[450, 2.5], [700, 3.5]], "n": 16},
    {"key": "staurolite-path", "title": "Aluminous pelite", "group": "path",
     "blurb": "An Al-rich mudstone up a medium-pressure path: chloritoid, then garnet and staurolite, then biotite.",
     "rock": "aluminous pelite", "system": "metapelite", "water": "excess", "kind": "path",
     "path": [[450, 5], [650, 9]], "n": 16},
    {"key": "metabasite-path", "title": "Metabasite", "group": "path",
     "blurb": "A basalt from greenschist into amphibolite on the igneous set: amphibole and plagioclase take over.",
     "rock": "metabasite", "system": "igneous", "water": "excess", "kind": "path",
     "path": [[500, 4], [750, 8]], "n": 12},
    {"key": "barrovian", "title": "Barrovian pelite", "group": "grid",
     "blurb": "A mudstone through the greenschist and amphibolite facies: chlorite gives way to garnet, "
              "biotite and the aluminosilicates.",
     "rock": "pelite", "system": "metapelite", "water": "excess", "kind": "grid",
     "t": [450, 700, 50], "p": [2, 10, 2]},
    {"key": "median", "title": "World median pelite", "group": "grid",
     "blurb": "The rock of Forshaw and Pattison (2023) on MAGEMin's own test grid, for comparison.",
     "rock": "world median pelite", "system": "metapelite", "water": "excess", "kind": "grid",
     "t": [400, 800, 50], "p": [2, 8, 2]},
    {"key": "metabasite", "title": "Metabasite", "group": "grid",
     "blurb": "A basalt on the igneous set: plagioclase, amphibole and pyroxene; garnet at high pressure.",
     "rock": "metabasite", "system": "igneous", "water": "excess", "kind": "grid",
     "t": [500, 800, 50], "p": [2, 12, 2]},
    {"key": "chloritoid", "title": "Chloritoid schist", "group": "point",
     "blurb": "An aluminous pelite at 500 °C and 6 kbar: chloritoid with chlorite, muscovite and quartz.",
     "rock": "aluminous pelite", "system": "metapelite", "water": "excess", "kind": "point", "t": 500, "p": 6},
    {"key": "staurolite", "title": "Staurolite schist", "group": "point",
     "blurb": "The same rock at 600 °C and 8 kbar: almandine garnet and staurolite with biotite.",
     "rock": "aluminous pelite", "system": "metapelite", "water": "excess", "kind": "point", "t": 600, "p": 8},
    {"key": "sillimanite", "title": "Sillimanite gneiss", "group": "point",
     "blurb": "A pelite at 650 °C and 5 kbar, past muscovite's best: sillimanite with biotite.",
     "rock": "pelite", "system": "metapelite", "water": "excess", "kind": "point", "t": 650, "p": 5},
]

NOTES = [
    "Phases are found by Gibbs energy minimization on the Holland and Powell (2011) data, with the "
    "solution models of White et al. (2014) for metapelites (ds6.2) or Holland, Green and Powell (2018) for "
    "the igneous set (ds6.36).",
    "The metapelite set matches MAGEMin's own reference grid at all 48 of its points (assemblage and Gibbs energy).",
    "Each cell of the diagram is one equilibrium at its center. Boundaries are drawn along cell edges, so "
    "they are stepped; a finer grid moves them closer to the true reaction lines.",
    "Fields are shaded by variance, F = C - phases + 2: the darker the field, the more degrees of freedom.",
    "Modes are wt% of the rock without its free fluid. With water in excess, the amount of fluid means nothing.",
    "A P-T path solves points spaced evenly along its line. The facies fields behind it are schematic, after "
    "Spear (1993) and Winter (2010); the Al2SiO5 and muscovite + quartz lines are worked out from ds6.2.",
    "Oxides the phase set cannot use (Cr2O3 for metapelites, MnO for the igneous set, and NiO, CoO, P2O5 "
    "and CO2 for both) are left out and listed.",
]


def _num(v, what: str) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be a number") from None
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError(f"{what} must be a number")
    return x


def parse_inputs(d: dict) -> tuple[bulk_mod.Bulk, dict]:
    """The window's inputs as a Bulk and the run: {"kind": "point", "t", "p"} or {"kind": "grid", "t": [from,
    to, step], "p": [...]}, temperatures in degC and pressures in kbar."""
    wt = d.get("bulk")
    if not isinstance(wt, dict) or not wt:
        raise ValueError("give the rock's composition")
    wt = {str(k): _num(v, k) for k, v in wt.items() if v not in (None, "")}
    system = str(d.get("system", "metapelite"))
    water = str(d.get("water", "excess"))
    b = bulk_mod.from_wt_pct(wt, water=water, name=str(d.get("name", "") or "rock")[:80], system=system)
    kind = str(d.get("kind", "point"))
    if kind == "point":
        t, p = _num(d.get("t"), "temperature"), _num(d.get("p"), "pressure")
        if not 100 <= t <= 1500:
            raise ValueError("temperature must be between 100 and 1500 °C")
        if not 0 < p <= 60:
            raise ValueError("pressure must be above 0 and at most 60 kbar")
        return b, {"kind": "point", "t": t, "p": p}
    if kind == "path":
        way = d.get("path")
        if not isinstance(way, list) or len(way) < 2:
            raise ValueError("give the path as at least two temperature, pressure pairs")
        try:
            way = [(_num(a, "temperature"), _num(b, "pressure")) for a, b in way]
        except (TypeError, ValueError):
            raise ValueError("give each point of the path as a temperature and a pressure") from None
        for t, p in way:
            if not 100 <= t <= 1500:
                raise ValueError("temperatures must be between 100 and 1500 °C")
            if not 0 < p <= 60:
                raise ValueError("pressures must be above 0 and at most 60 kbar")
        n = int(_num(d.get("n", 16), "number of steps"))
        if not 2 <= n <= 60:
            raise ValueError("a path has 2 to 60 steps")
        return b, {"kind": "path", "path": [list(q) for q in way], "n": n, "tp": path_mod.points(way, n)}
    if kind != "grid":
        raise ValueError("kind must be point, path or grid")
    try:
        ts = pseudosection.axis(*[_num(v, "temperature") for v in d.get("t", [])])
        ps = pseudosection.axis(*[_num(v, "pressure") for v in d.get("p", [])])
    except TypeError:
        raise ValueError("give each axis as from, to and step") from None
    if ts[0] < 100 or ts[-1] > 1500:
        raise ValueError("temperatures must be between 100 and 1500 °C")
    if ps[0] <= 0 or ps[-1] > 60:
        raise ValueError("pressures must be above 0 and at most 60 kbar")
    if len(ts) * len(ps) > MAX_POINTS:
        raise ValueError(f"{len(ts)} x {len(ps)} = {len(ts) * len(ps)} points is too many (at most {MAX_POINTS}); "
                         "use a larger step")
    return b, {"kind": "grid", "t": ts, "p": ps}


def workers_for(rows: int) -> int:
    return max(1, min(rows, (os.cpu_count() or 2) - 1))


def mineral_json(m) -> dict:
    return {"abbr": m.abbr, "name": m.name, "hp": m.hp, "mode": m.mode, "grams": m.grams, "formula": m.formula,
            "numbers": m.numbers, "wt_pct": m.wt_pct, "end_members": m.end_members}


def point_json(pt: Point, c: int) -> dict:
    return {"t_c": pt.t_c, "p_kbar": pt.p_kbar, "label": pt.label, "assemblage": list(pt.assemblage),
            "variance": c - len(pt.assemblage) + 2, "converged": pt.converged,
            "max_driving_force": pt.max_driving_force,
            "minerals": [mineral_json(m) for m in pt.minerals],
            "fluid": None if pt.fluid is None else {"grams": pt.fluid.grams},
            "traces": [m.abbr for m in pt.traces]}


def _modes(pt) -> dict:
    """wt% by mineral; two coexisting phases with one name (two amphiboles, say) are added together."""
    out: dict[str, float] = {}
    for m in pt.minerals:
        out[m.abbr] = out.get(m.abbr, 0.0) + m.mode
    return {k: round(v, 2) for k, v in out.items()}


def grid_json(ps: pseudosection.Pseudosection, done: list) -> dict:
    """The diagram for the windows: cells by field (None where the row is still running, -1 where the
    solver failed), the fields, their boundaries, and each cell's modes for shading."""
    cells, modes = [], []
    for i, row in enumerate(ps.points):
        cells.append([ps.field_of[i][j] if done[i] else None for j in range(len(ps.t_c))])
        modes.append([_modes(pt) if pt is not None else None for pt in row])
    minerals = sorted({a for row in modes for c in row if c for a in c}, key=lambda a: names.ORDER.get(a, 99))
    return {"t_c": ps.t_c, "p_kbar": ps.p_kbar, "cells": cells, "modes": modes, "minerals": minerals,
            "fields": [{"id": f.id, "label": f.label, "variance": f.variance, "n": len(f.cells),
                        "centre": f.centre, "assemblage": list(f.assemblage)} for f in ps.fields],
            "boundaries": _partial_boundaries(ps, done),
            "failed": [[i, j, m] for i, j, m in ps.failed], "done": done}


def path_json(tp: list, pts: list, done: list, c: int) -> dict:
    """The path for the windows: every point's T, P and (once solved) its minerals' modes."""
    rows = []
    for (t, p), pt, ok in zip(tp, pts, done):
        if not ok:
            rows.append({"t_c": t, "p_kbar": p, "state": "running"})
        elif pt is None:
            rows.append({"t_c": t, "p_kbar": p, "state": "failed"})
        else:
            rows.append({"t_c": t, "p_kbar": p, "state": "done", "label": pt.label, "assemblage": list(pt.assemblage),
                         "variance": c - len(pt.assemblage) + 2,
                         "modes": _modes(pt)})
    minerals = sorted({a for r in rows for a in r.get("modes", {})}, key=lambda a: names.ORDER.get(a, 99))
    return {"points": rows, "minerals": minerals, "done": done}


def _partial_boundaries(ps, done):
    """Boundaries while rows are missing: only the edges between two finished cells."""
    te, pe = pseudosection._edges(np.asarray(ps.t_c, float)), pseudosection._edges(np.asarray(ps.p_kbar, float))
    f, segs = ps.field_of, []
    for i in range(len(ps.p_kbar)):
        if not done[i]:
            continue
        for j in range(len(ps.t_c)):
            if j + 1 < len(ps.t_c) and f[i][j + 1] != f[i][j]:
                segs.append(((te[j + 1], pe[i]), (te[j + 1], pe[i + 1])))
            if i + 1 < len(ps.p_kbar) and done[i + 1] and f[i + 1][j] != f[i][j]:
                segs.append(((te[j], pe[i + 1]), (te[j + 1], pe[i + 1])))
    return [((float(a), float(b)), (float(c), float(d))) for (a, b), (c, d) in segs]


class State:
    """What both windows show.  Every change bumps `version` and wakes the event streams."""

    def __init__(self):
        self.cond = threading.Condition()
        self.lock = threading.Lock()
        self.version = 0
        self.status = "idle"            # idle | running | done | stopped | error
        self.message = ""
        self.progress = [0, 0]
        self.inputs: dict = {}
        self.run: dict = {}
        self.run_id = 0
        self.started = 0.0
        self.elapsed = 0.0
        self.workers = 1
        self.bulk: bulk_mod.Bulk | None = None
        self.point: Point | None = None                      # a single equilibrium
        self.ps: pseudosection.Pseudosection | None = None   # a pseudosection, filled row by row
        self.done: list = []
        self.grid: dict | None = None
        self.path_pts: list = []                             # a P-T path's points, filled stretch by stretch
        self.path: dict | None = None
        self.source_sample = None        # the sample the rock came from, the parent of samples written here
        # Inside Protolith: a function(sample dict, take, grams) that puts a sample on Reaction's card
        # and returns {"problems", "notes", "open"}.  None when Metamorphism runs on its own.
        self.send_sample = None
        self._stop = threading.Event()

    def snapshot(self) -> dict:
        b = self.bulk
        c = components_present(b) if b is not None else 0
        return {"version": self.version, "status": self.status, "message": self.message,
                "progress": self.progress, "inputs": self.inputs, "run": self.run, "run_id": self.run_id,
                "elapsed": round(time.time() - self.started, 1) if self.status == "running" else self.elapsed,
                "workers": self.workers,
                "bulk": None if b is None else {"name": b.name, "wt_pct": b.wt_pct, "left_out": b.left_out,
                                                "water": b.water, "system": b.system,
                                                "system_label": SYSTEM_LABEL[b.system], "components": c},
                "point": None if self.point is None else point_json(self.point, c),
                "grid": self.grid, "path": self.path, "notes": NOTES, "app_version": __version__,
                "source": None if self.source_sample is None else _sample_summary(self.source_sample),
                "can_send": self.send_sample is not None}

    def changed(self):
        with self.cond:
            self.version += 1
            self.cond.notify_all()

    # ---- runs ----------------------------------------------------------------------------------
    def start(self, inputs: dict) -> None:
        if self.status == "running":
            raise ValueError("a run is already going; stop it first")
        b, run = parse_inputs(inputs)
        if not inputs.get("from_sample"):
            self.source_sample = None
        self._stop.clear()
        self.run_id += 1
        self.inputs, self.run, self.bulk = dict(inputs), run, b
        self.point, self.ps, self.grid, self.done = None, None, None, []
        self.path_pts, self.path = [], None
        self.status, self.message = "running", ""
        self.started, self.elapsed = time.time(), 0.0
        if run["kind"] == "point":
            self.workers, self.progress = 1, [0, 1]
            target = self._run_point
        elif run["kind"] == "path":
            n = len(run["tp"])
            self.workers = workers_for(math.ceil(n / 2))
            self.progress = [0, n]
            self.path_pts, self.done = [None] * n, [False] * n
            self.path = path_json(run["tp"], self.path_pts, self.done, components_present(b))
            target = self._run_path
        else:
            self.workers = workers_for(len(run["p"]))
            self.progress = [0, len(run["p"])]
            self.ps = pseudosection.Pseudosection(b, run["t"], run["p"], [[None] * len(run["t"]) for _ in run["p"]])
            self.done = [False] * len(run["p"])
            pseudosection.group(self.ps)
            self.grid = grid_json(self.ps, self.done)
            target = self._run_grid
        self.changed()
        threading.Thread(target=target, args=(b, run), daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def _finish(self, status: str, message: str = "") -> None:
        self.status, self.message = status, message
        self.elapsed = round(time.time() - self.started, 1)
        self.changed()

    def _run_point(self, b, run) -> None:
        try:
            pt = equilibrium(b, run["t"], run["p"])
        except Exception as exc:          # noqa: BLE001 - reported in the windows
            return self._finish("error", f"{type(exc).__name__}: {exc}")
        self.point = pt.light()
        self.progress = [1, 1]
        self._finish("stopped" if self._stop.is_set() else "done")

    def _run_grid(self, b, run) -> None:
        def on_result(i, pts, fails):
            with self.lock:
                self.ps.points[i] = pts
                self.ps.failed = [f for f in self.ps.failed if f[0] != i] + [(i, j, m) for j, m in fails]
                self.done[i] = True
                pseudosection.group(self.ps)
                self.grid = grid_json(self.ps, self.done)
                self.progress = [sum(self.done), len(self.done)]
            self.changed()

        try:
            res = pseudosection.compute(b, run["t"], run["p"], workers=self.workers, on_result=on_result,
                                        stop=self._stop)
        except pseudosection.Stopped:
            n = sum(self.done)
            return self._finish("stopped", f"Stopped with {n} of {len(self.done)} pressure rows done.")
        except Exception as exc:          # noqa: BLE001
            return self._finish("error", f"{type(exc).__name__}: {exc}")
        with self.lock:
            self.ps, self.done = res, [True] * len(res.p_kbar)
            self.grid = grid_json(res, self.done)
        self._finish("done")

    def _run_path(self, b, run) -> None:
        c = components_present(b)

        def on_result(start, pts, fails):
            with self.lock:
                for k, pt in enumerate(pts):
                    self.path_pts[start + k] = pt
                    self.done[start + k] = True
                self.path = path_json(run["tp"], self.path_pts, self.done, c)
                self.progress = [sum(self.done), len(self.done)]
            self.changed()

        try:
            path_mod.compute(b, run["tp"], workers=self.workers, on_result=on_result, stop=self._stop)
        except pseudosection.Stopped:
            return self._finish("stopped", f"Stopped with {sum(self.done)} of {len(self.done)} points done.")
        except Exception as exc:          # noqa: BLE001
            return self._finish("error", f"{type(exc).__name__}: {exc}")
        self._finish("done")

    # ---- points, samples, files -------------------------------------------------------------------
    def point_at(self, i: int, j: int) -> Point | None:
        if self.run.get("kind") == "point":
            return self.point
        if self.run.get("kind") == "path":
            return self.path_pts[j] if 0 <= j < len(self.path_pts) else None
        if self.ps is None or not (0 <= i < len(self.ps.p_kbar) and 0 <= j < len(self.ps.t_c)):
            return None
        return self.ps.points[i][j]

    def sample(self, i: int, j: int, keep_fluid: bool = False):
        from protolith.metamorphism_link import to_sample

        pt = self.point_at(i, j)
        if pt is None or self.bulk is None:
            return None
        parent = self.source_sample.id if self.source_sample is not None else None
        run = {"kind": self.run.get("kind"), "t_c": pt.t_c, "p_kbar": pt.p_kbar}
        smp = to_sample(pt, self.bulk, parent=parent, note=self.bulk.name, run=run, keep_fluid=keep_fluid)
        smp.written_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return smp

    def open_sample(self, d: dict) -> dict:
        """A .sample file as the rock to metamorphose: the oxide wt% of each part it has."""
        from protolith.metamorphism_link import bulk_from_sample
        from protolith.sample import Sample

        smp = Sample.from_dict(d)
        parts = {}
        for part in ("whole", "rock", "melt"):
            try:
                parts[part] = bulk_from_sample(smp, part, "bulk", "metapelite").wt_pct
            except ValueError:
                continue
        if not parts:
            raise ValueError("this sample has no composition to use")
        if self.status != "running":
            self.source_sample = smp
            self.changed()
        return {"summary": _sample_summary(smp), "parts": parts}

    def open_pseudosection(self, d: dict) -> None:
        if self.status == "running":
            raise ValueError("a run is going; stop it first")
        ps = pseudosection.Pseudosection.from_dict(d)
        self.run_id += 1
        self.bulk, self.ps, self.point = ps.bulk, ps, None
        self.path_pts, self.path = [], None
        self.done = [True] * len(ps.p_kbar)
        self.grid = grid_json(ps, self.done)
        self.run = {"kind": "grid", "t": ps.t_c, "p": ps.p_kbar}
        self.inputs = {"kind": "grid", "bulk": ps.bulk.wt_pct, "name": ps.bulk.name, "system": ps.bulk.system,
                       "water": ps.bulk.water, "opened": True}
        self.source_sample = None
        self.progress = [len(ps.p_kbar), len(ps.p_kbar)]
        self.started = time.time()
        self._finish("done", "Opened from a file.")


def _sample_summary(s) -> dict:
    return {"id": s.id, "note": s.note, "app": (s.written_by or {}).get("app", ""),
            "t_c": (s.conditions or {}).get("t_c"), "has_melt": bool(s.melt),
            "phases": [p.name for p in s.phases]}


class Handler(BaseHTTPRequestHandler):
    server_version = "Protolith"
    protocol_version = "HTTP/1.1"

    @property
    def state(self) -> State:
        return self.server.state            # type: ignore[attr-defined]

    def log_message(self, fmt, *args):
        pass

    def _allowed(self) -> bool:
        port = self.server.server_address[1]
        ok_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
        if self.headers.get("Host", "") not in ok_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in ok_hosts}

    def _send(self, status: int, body: bytes, ctype: str, filename: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200) -> None:
        self._send(status, json.dumps(obj).encode(), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)

    def _file(self, p: Path) -> None:
        p = p.resolve()
        if STATIC not in p.parents or not p.is_file():
            return self._error(404, "not found")
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        self._send(200, p.read_bytes(), ctype)

    def _cell(self, q) -> tuple[int, int]:
        try:
            return int(q.get("i", ["0"])[0]), int(q.get("j", ["0"])[0])
        except ValueError:
            raise ValueError("i and j must be whole numbers") from None

    def do_GET(self) -> None:
        if not self._allowed():
            return self._error(HTTPStatus.FORBIDDEN, "forbidden")
        url = urlparse(self.path)
        path, q = url.path, parse_qs(url.query)
        if path in PAGES:
            return self._file(STATIC / PAGES[path])
        if path.startswith("/static/"):
            return self._file(STATIC / path[len("/static/"):])
        if path == "/favicon.ico":
            return self._file(STATIC / "protolith.ico")
        if path == "/api/state":
            return self._json(self.state.snapshot())
        if path == "/api/presets":
            return self._json({"oxides": list(OXIDES),
                               "presets": {k: {"wt": v, "source": SOURCES.get(k, "")}
                                           for k, v in bulk_mod.PRESETS.items()},
                               "systems": SYSTEM_LABEL, "left_out": bulk_mod.LEFT_OUT, "cards": CARDS,
                               "cpus": workers_for(10_000), "seconds_per_point": SECONDS_PER_POINT,
                               "max_points": MAX_POINTS})
        if path == "/api/facies":
            return self._json(facies.diagram())
        if path == "/events":
            return self._events()
        try:
            if path == "/api/point":
                i, j = self._cell(q)
                pt = self.state.point_at(i, j)
                if pt is None:
                    return self._error(404, "no point there yet")
                return self._json(point_json(pt, components_present(self.state.bulk)))
            if path == "/api/sample":
                i, j = self._cell(q)
                smp = self.state.sample(i, j, q.get("fluid", ["0"])[0] == "1")
                if smp is None:
                    return self._error(404, "no point there yet")
                body = json.dumps(smp.to_dict(), indent=1).encode()
                name = f"metamorphism_{smp.conditions['t_c']:.0f}C_{smp.conditions['p_bar'] / 1000:g}kbar.sample"
                return self._send(200, body, "application/json; charset=utf-8", name)
            if path == "/api/pseudosection":
                ps = self.state.ps
                if ps is None or not all(self.state.done):
                    return self._error(404, "no finished pseudosection to save")
                body = json.dumps(ps.to_dict()).encode()
                stem = "".join(ch if ch.isalnum() else "_" for ch in (ps.bulk.name or "rock"))[:40]
                return self._send(200, body, "application/json; charset=utf-8", f"{stem}.pseudosection")
        except ValueError as exc:
            return self._error(400, str(exc))
        return self._error(404, "not found")

    def _events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        seen = -1
        st = self.state
        try:
            while True:
                with st.cond:
                    if st.version == seen:
                        st.cond.wait(timeout=5 if st.status == "running" else 15)
                if st.version == seen and st.status != "running":
                    self.wfile.write(b": keep-alive\n\n")
                else:                       # while running, every few seconds anyway: the clock moves
                    seen = st.version
                    self.wfile.write(b"data: " + json.dumps(st.snapshot()).encode() + b"\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_POST(self) -> None:
        if not self._allowed():
            return self._error(HTTPStatus.FORBIDDEN, "forbidden")
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length") or 0)
        if n > (MAX_FILE if path == "/api/open-pseudosection" else MAX_BODY):
            return self._error(413, "request too large")
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._error(400, "that is not a JSON file")
        if not isinstance(body, dict):
            return self._error(400, "expected a JSON object")
        try:
            if path == "/api/run":
                self.state.start(body)
                return self._json({"ok": True, "run_id": self.state.run_id})
            if path == "/api/stop":
                self.state.stop()
                return self._json({"ok": True})
            if path == "/api/open-sample":
                return self._json(self.state.open_sample(body))
            if path == "/api/open-pseudosection":
                self.state.open_pseudosection(body)
                return self._json({"ok": True})
            if path == "/api/send-sample":
                if self.state.send_sample is None:
                    return self._error(404, "Send to Reaction works inside Protolith only")
                smp = self.state.sample(int(body.get("i", 0)), int(body.get("j", 0)), False)
                if smp is None:
                    return self._error(404, "no point there yet")
                return self._json(self.state.send_sample(smp.to_dict(), "rock", float(body.get("grams", 100.0))))
        except (ValueError, TypeError, KeyError) as exc:
            return self._error(400, str(exc))
        return self._error(404, "not found")


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False      # as in Reaction: on Windows a shared port silently loses requests


def make_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    try:
        httpd = _Server(("127.0.0.1", port), Handler)
    except OSError:                      # port taken: let the system pick one
        httpd = _Server(("127.0.0.1", 0), Handler)
    httpd.state = State()                # type: ignore[attr-defined]
    return httpd
