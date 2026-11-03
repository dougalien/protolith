"""A pseudosection: the stable assemblage of one rock over a grid of temperature and pressure.

Each row of the grid (one pressure) is solved from low to high temperature, each point starting from the
one before (``point.equilibrium(previous=...)``), which is several times faster than solving every point
from scratch.  Rows are independent, so they can run in parallel processes.

The points are then grouped into **fields**: connected cells (sharing an edge) with the same assemblage.
The same assemblage can make two fields if they do not touch.  Each field has its label, its variance
by the phase rule (F = C - phases + 2, with C the components the solver was given), its cells, and a
point to write its label at.  **Boundaries** are the cell edges between two different fields, as line
segments in (T, P), ready to draw.  On a grid this is a stepped outline; a finer grid moves it closer
to the true reaction lines.
"""
from __future__ import annotations

import json
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import names
from .bulk import Bulk
from .point import Point, components_present, equilibrium

FORMAT = "protolith-pseudosection"
VERSION = 1


@dataclass
class Field:
    id: int
    assemblage: tuple
    label: str
    variance: int
    cells: list                   # [(i, j)]: i the pressure row, j the temperature column
    centre: tuple                 # (t_c, p_kbar) of the cell that best stands for the field


@dataclass
class Pseudosection:
    bulk: Bulk
    t_c: list                     # column temperatures, degC, increasing
    p_kbar: list                  # row pressures, kbar, increasing
    points: list                  # points[i][j] at (t_c[j], p_kbar[i]); None where the solver failed
    fields: list = field(default_factory=list)
    field_of: list = field(default_factory=list)     # field_of[i][j]: the Field.id of a cell (-1: failed)
    failed: list = field(default_factory=list)       # [(i, j, message)]

    # ---- views -------------------------------------------------------------------------------
    def point_at(self, t_c: float, p_kbar: float) -> Point | None:
        """The grid point nearest to (t_c, p_kbar)."""
        j = int(np.argmin(np.abs(np.asarray(self.t_c) - t_c)))
        i = int(np.argmin(np.abs(np.asarray(self.p_kbar) - p_kbar)))
        return self.points[i][j]

    def field_at(self, t_c: float, p_kbar: float) -> Field | None:
        j = int(np.argmin(np.abs(np.asarray(self.t_c) - t_c)))
        i = int(np.argmin(np.abs(np.asarray(self.p_kbar) - p_kbar)))
        k = self.field_of[i][j]
        return self.fields[k] if k >= 0 else None

    def boundaries(self) -> list:
        """Line segments ((t1, p1), (t2, p2)) along every cell edge between two different fields."""
        t, p = np.asarray(self.t_c, float), np.asarray(self.p_kbar, float)
        te = _edges(t)
        pe = _edges(p)
        segs = []
        ni, nj = len(p), len(t)
        for i in range(ni):
            for j in range(nj):
                a = self.field_of[i][j]
                if j + 1 < nj and self.field_of[i][j + 1] != a:
                    segs.append(((te[j + 1], pe[i]), (te[j + 1], pe[i + 1])))
                if i + 1 < ni and self.field_of[i + 1][j] != a:
                    segs.append(((te[j], pe[i + 1]), (te[j + 1], pe[i + 1])))
        return [((float(a), float(b)), (float(c), float(d))) for (a, b), (c, d) in segs]

    def mode_grid(self, abbr: str) -> np.ndarray:
        """The mode (wt%) of one mineral at every grid point (rows: pressure), for contouring."""
        out = np.full((len(self.p_kbar), len(self.t_c)), np.nan)
        for i, row in enumerate(self.points):
            for j, pt in enumerate(row):
                if pt is not None:
                    out[i, j] = sum(m.mode for m in pt.minerals if m.abbr == abbr)
        return out

    # ---- file --------------------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "format": FORMAT, "version": VERSION,
            "bulk": {"wt_pct": self.bulk.wt_pct, "water": self.bulk.water, "name": self.bulk.name,
                     "left_out": self.bulk.left_out},
            "t_c": list(self.t_c), "p_kbar": list(self.p_kbar),
            "points": [[pt.to_dict() if pt is not None else None for pt in row] for row in self.points],
            "failed": [list(f) for f in self.failed],
        }

    def save(self, path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict()), encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, d: dict) -> "Pseudosection":
        from .bulk import from_wt_pct

        if d.get("format") != FORMAT:
            raise ValueError("this is not a Protolith pseudosection file")
        if d.get("version", 0) > VERSION:
            raise ValueError(f"pseudosection file version {d.get('version')} is newer than this app reads")
        b = d["bulk"]
        ps = cls(from_wt_pct(b["wt_pct"], b["water"], b.get("name", "")), d["t_c"], d["p_kbar"],
                 [[Point.from_dict(pt) if pt is not None else None for pt in row] for row in d["points"]],
                 failed=[tuple(f) for f in d.get("failed", [])])
        group(ps)
        return ps

    @classmethod
    def load(cls, path) -> "Pseudosection":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _edges(x: np.ndarray) -> np.ndarray:
    """Cell edges around grid values x: midpoints between them, and half a step past each end."""
    if len(x) == 1:
        return np.array([x[0] - 0.5, x[0] + 0.5])
    mid = (x[1:] + x[:-1]) / 2
    return np.concatenate([[x[0] - (mid[0] - x[0])], mid, [x[-1] + (x[-1] - mid[-1])]])


def axis(start: float, stop: float, step: float) -> list:
    """start, start + step, ... up to stop (included when it falls on the grid)."""
    if step <= 0 or stop < start:
        raise ValueError("an axis runs from a lower to a higher value with a positive step")
    n = int(np.floor((stop - start) / step + 1e-9)) + 1
    return [round(start + k * step, 9) for k in range(n)]


def solve_row(bulk: Bulk, t_c: list, p_kbar: float, phases=None) -> tuple:
    """One row: every temperature at one pressure, each starting from the one before.
    Returns ([Point or None], [(j, message)])."""
    out, failed, prev = [], [], None
    for j, t in enumerate(t_c):
        try:
            pt = equilibrium(bulk, t, p_kbar, previous=prev, phases=phases)
        except (RuntimeError, ValueError, np.linalg.LinAlgError) as e:
            if prev is None:
                out.append(None)
                failed.append((j, str(e)))
                continue
            try:                                    # a warm start can mislead: try once from scratch
                pt = equilibrium(bulk, t, p_kbar, phases=phases)
            except (RuntimeError, ValueError, np.linalg.LinAlgError) as e2:
                out.append(None)
                failed.append((j, str(e2)))
                prev = None
                continue
        out.append(pt.light())
        prev = pt
    return out, failed


def _row_job(args):
    bulk, t_c, p, phases = args
    return solve_row(bulk, t_c, p, phases)


def compute(bulk: Bulk, t_c: list, p_kbar: list, workers: int | None = None, phases=None,
            on_row=None) -> Pseudosection:
    """Solve the grid t_c x p_kbar (degC, kbar) for `bulk`.

    workers: processes to run rows in (default: the CPUs less one, at most the number of rows); 1 runs
    in this process.  on_row(done, total) is called as each row finishes."""
    t_c = sorted(float(t) for t in t_c)
    p_kbar = sorted(float(p) for p in p_kbar)
    if not t_c or not p_kbar:
        raise ValueError("the grid needs at least one temperature and one pressure")
    if workers is None:
        workers = max(1, min(len(p_kbar), (os.cpu_count() or 2) - 1))
    rows: list = [None] * len(p_kbar)
    failed = []
    jobs = [(bulk, t_c, p, phases) for p in p_kbar]
    if workers <= 1:
        for i, job in enumerate(jobs):
            rows[i] = _row_job(job)
            if on_row:
                on_row(i + 1, len(jobs))
    else:
        # spawn, as on Windows: the same behaviour everywhere, and no fork of a threaded process
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as ex:
            futs = {ex.submit(_row_job, job): i for i, job in enumerate(jobs)}
            done = 0
            for f in as_completed(futs):
                rows[futs[f]] = f.result()
                done += 1
                if on_row:
                    on_row(done, len(jobs))
    points = []
    for i, (row, fails) in enumerate(rows):
        points.append(row)
        failed += [(i, j, msg) for j, msg in fails]
    ps = Pseudosection(bulk, t_c, p_kbar, points, failed=failed)
    group(ps)
    return ps


def group(ps: Pseudosection) -> None:
    """Fill ps.fields and ps.field_of: connected cells of one assemblage make one field."""
    ni, nj = len(ps.p_kbar), len(ps.t_c)
    key = [[pt.assemblage if pt is not None else None for pt in row] for row in ps.points]
    fid = [[-1] * nj for _ in range(ni)]
    c = components_present(ps.bulk)
    cells_of = []
    for i in range(ni):
        for j in range(nj):
            if key[i][j] is None or fid[i][j] >= 0:
                continue
            k = len(cells_of)
            stack, cells = [(i, j)], []
            fid[i][j] = k
            while stack:
                a, b = stack.pop()
                cells.append((a, b))
                for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    x, y = a + da, b + db
                    if 0 <= x < ni and 0 <= y < nj and fid[x][y] < 0 and key[x][y] == key[i][j]:
                        fid[x][y] = k
                        stack.append((x, y))
            cells_of.append((key[i][j], sorted(cells)))
    fields = []
    for k, (asm, cells) in enumerate(cells_of):
        ci = np.mean([a for a, _ in cells])
        cj = np.mean([b for _, b in cells])
        a, b = min(cells, key=lambda ab: (ab[0] - ci) ** 2 + (ab[1] - cj) ** 2)
        fields.append(Field(k, asm, names.label(asm), c - len(asm) + 2, cells,
                            (float(ps.t_c[b]), float(ps.p_kbar[a]))))
    ps.fields, ps.field_of = fields, fid
