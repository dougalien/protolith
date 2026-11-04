"""The background of the P-T path view: the metamorphic facies and a few reaction lines.

The facies fields are schematic, after Spear (1993) and Winter (2010, fig. 25.2): facies boundaries are
gradational and depend on the rock, so they are drawn as guides only.  The reaction lines are worked out
from the Holland and Powell data (ds6.2, the metapelite set's dataset), pure phases only:
the Al2SiO5 polymorphs (kyanite, andalusite, sillimanite) and muscovite + quartz = K-feldspar + Al2SiO5 + H2O.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.optimize import brentq

from protolith.core.hp.endmembers import gibbs

DATASET = "62"

# (name, [(T degC, P kbar), ...]) polygons sharing their edges
FACIES = [
    ("Zeolite", [(150, 0), (300, 0), (280, 4), (150, 5)]),
    ("Prehnite–pumpellyite", [(300, 0), (400, 0), (380, 6), (280, 4)]),
    ("Hornfels", [(400, 0), (1000, 0), (1000, 2), (393, 2)]),
    ("Greenschist", [(393, 2), (500, 2), (530, 9), (470, 11), (380, 8), (380, 6)]),
    ("Blueschist", [(150, 5), (280, 4), (380, 6), (380, 8), (470, 11), (520, 20), (150, 20)]),
    ("Amphibolite", [(500, 2), (700, 2), (750, 11), (600, 12), (530, 9)]),
    ("Granulite", [(700, 2), (1000, 2), (1000, 14), (750, 11)]),
    ("Eclogite", [(470, 11), (530, 9), (600, 12), (750, 11), (1000, 14), (1000, 20), (520, 20)]),
]

AL2SIO5 = {"ky": "Ky", "and": "And", "sill": "Sil"}


def _g(name: str, t_c: float, p: float) -> float:
    return gibbs(name, t_c + 273.15, p, dataset=DATASET)


def _stable_al2sio5(t_c: float, p: float) -> str:
    return min(AL2SIO5, key=lambda n: _g(n, t_c, p))


def _al2sio5_line(a: str, b: str, third: str) -> list:
    """Where a = b, along T, kept only where the third polymorph is not more stable."""
    out = []
    for t in np.arange(150.0, 1001.0, 10.0):
        f = lambda p: _g(a, t, p) - _g(b, t, p)
        lo, hi = 0.01, 25.0
        if f(lo) * f(hi) > 0:
            continue
        p = brentq(f, lo, hi)
        if _g(third, t, p) >= _g(a, t, p) - 1e-6:
            out.append((float(t), round(float(p), 3)))
    return out


def _muscovite_out() -> list:
    """Ms + Qz = Kfs + Al2SiO5 + H2O, along P (the line is steep), with whichever Al2SiO5 is stable."""
    out = []
    for p in np.arange(0.5, 15.01, 0.5):
        def f(t):
            als = _stable_al2sio5(t, p)
            return _g("mu", t, p) + _g("q", t, p) - _g("san", t, p) - _g(als, t, p) - _g("H2O", t, p)
        lo, hi = 300.0, 1000.0
        if f(lo) * f(hi) > 0:
            continue
        out.append((round(float(brentq(f, lo, hi)), 2), float(p)))
    return out


def _triple_point() -> tuple:
    def pk(a, b, t):
        return brentq(lambda p: _g(a, t, p) - _g(b, t, p), 0.01, 25.0)
    t = brentq(lambda t: pk("ky", "and", t) - pk("ky", "sill", t), 400.0, 700.0)
    return (round(float(t), 2), round(float(pk("ky", "and", t)), 3))


@lru_cache(maxsize=1)
def diagram() -> dict:
    """The facies polygons and the reaction lines, for the window."""
    tp = _triple_point()
    lines = [
        {"label": "Ky = And", "points": _al2sio5_line("ky", "and", "sill") + [tp]},
        {"label": "Ky = Sil", "points": [tp] + _al2sio5_line("ky", "sill", "and")},
        {"label": "And = Sil", "points": [tp] + _al2sio5_line("and", "sill", "ky")},
        {"label": "Ms + Qz = Kfs + Als + H2O", "points": _muscovite_out()},
    ]
    return {"facies": [{"name": n, "points": [list(q) for q in pts]} for n, pts in FACIES],
            "triple_point": list(tp), "lines": [ln for ln in lines if len(ln["points"]) >= 2]}


__all__ = ["FACIES", "diagram"]
