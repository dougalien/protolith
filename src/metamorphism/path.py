"""A P-T path: the stable minerals at points spaced evenly along a line through a few waypoints.

Much quicker than a pseudosection (a path of 16 points against a grid of a hundred or more), and the result
reads like Magma's crystallization path: what grows and what goes as the rock heats and is buried.
The path is cut into stretches that run in parallel processes; inside each stretch every point starts from
the one before.
"""
from __future__ import annotations

import math
import multiprocessing
import os
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait

from .bulk import Bulk
from .pseudosection import Stopped, _end, solve_points

T_SCALE = 100.0     # degC that count as far as 1 kbar, for spacing the points along the path


def points(waypoints: list, n: int) -> list:
    """n (t_c, p_kbar) spaced evenly along the waypoints (in T/100 + P), the first and last included."""
    w = [(float(t), float(p)) for t, p in waypoints]
    if len(w) < 2:
        raise ValueError("a path needs at least two points")
    if n < 2:
        raise ValueError("a path needs at least two steps")
    seg = [math.hypot((b[0] - a[0]) / T_SCALE, b[1] - a[1]) for a, b in zip(w, w[1:])]
    total = sum(seg)
    if total <= 0:
        raise ValueError("the path's points are all the same")
    out = []
    for k in range(n):
        s, i = total * k / (n - 1), 0
        while i < len(seg) - 1 and s > seg[i]:
            s -= seg[i]
            i += 1
        f = 0.0 if seg[i] == 0 else min(1.0, s / seg[i])
        (t0, p0), (t1, p1) = w[i], w[i + 1]
        out.append((round(t0 + f * (t1 - t0), 3), round(p0 + f * (p1 - p0), 4)))
    return out


def _job(args):
    bulk, tp, phases = args
    return solve_points(bulk, tp, phases)


def compute(bulk: Bulk, tp: list, workers: int | None = None, phases=None, on_result=None, stop=None) -> tuple:
    """Solve every point of the path.  on_result(start, points, failed) as each stretch finishes (start: the
    index of its first point).  Returns ([Point or None], [(index, message)])."""
    n = len(tp)
    if workers is None:
        workers = max(1, (os.cpu_count() or 2) - 1)
    size = max(2, math.ceil(n / max(1, workers)))
    jobs = [(k, tp[k:k + size]) for k in range(0, n, size)]
    pts: list = [None] * n
    failed: list = []

    def finished(start, res):
        row, fails = res
        pts[start:start + len(row)] = row
        failed.extend((start + j, m) for j, m in fails)
        if on_result:
            on_result(start, row, fails)

    if workers <= 1 or len(jobs) == 1:
        for start, chunk in jobs:
            if stop is not None and stop.is_set():
                raise Stopped()
            finished(start, solve_points(bulk, chunk, phases))
    else:
        ex = ProcessPoolExecutor(max_workers=min(workers, len(jobs)), mp_context=multiprocessing.get_context("spawn"))
        try:
            futs = {ex.submit(_job, (bulk, chunk, phases)): start for start, chunk in jobs}
            pending = set(futs)
            while pending:
                if stop is not None and stop.is_set():
                    _end(ex)
                    raise Stopped()
                ready, pending = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
                for f in ready:
                    finished(futs[f], f.result())
        finally:
            ex.shutdown(wait=True, cancel_futures=True)
    return pts, sorted(failed)


__all__ = ["points", "compute"]
