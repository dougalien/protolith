"""Metamorphism from the command line, until it has a window of its own.

    python -m metamorphism point --rock pelite --t 600 --p 6
    python -m metamorphism point --sample basalt.sample --part rock --water excess --t 550 --p 8 --save out.sample
    python -m metamorphism grid --rock metabasite --t 450 750 25 --p 2 12 1 --out mb.pseudosection

A rock is a preset (``--rock``: pelite, metabasite or "world median pelite"), a sample file (``--sample``, with ``--part``), or
oxide wt% (``--wt "SiO2=50 Al2O3=15 ..."``).
"""
from __future__ import annotations

import argparse
import sys
import time

from . import bulk as bulk_mod
from . import pseudosection
from .point import equilibrium


def _rock(a) -> bulk_mod.Bulk:
    if a.sample:
        from protolith.metamorphism_link import bulk_from_sample
        from protolith.sample import Sample

        return bulk_from_sample(Sample.load(a.sample), a.part, a.water, a.set)
    if a.wt:
        wt = {}
        for item in a.wt.replace(",", " ").split():
            ox, v = item.split("=")
            wt[ox.strip()] = float(v)
        return bulk_mod.from_wt_pct(wt, a.water, "typed", a.set)
    return bulk_mod.from_wt_pct(bulk_mod.PRESETS[a.rock], a.water, a.rock, a.set)


def _print_point(pt) -> None:
    print(f"{pt.t_c:g} C, {pt.p_kbar:g} kbar: {pt.label}" + ("" if pt.converged else "  (not converged)"))
    for m in pt.minerals:
        nums = ", ".join(f"{k} {v:.0f}" for k, v in m.numbers.items())
        print(f"  {m.abbr:4s} {m.mode:6.2f} wt%  {m.formula}  {nums}")
    if pt.traces:
        print("  traces: " + ", ".join(m.abbr for m in pt.traces))
    if pt.fluid is not None:
        print(f"  free water {pt.fluid.grams:.2f} g per 100 g")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m metamorphism", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("point", "grid"):
        s = sub.add_parser(name)
        s.add_argument("--rock", choices=sorted(bulk_mod.PRESETS), default="pelite")
        s.add_argument("--sample")
        s.add_argument("--part", choices=("whole", "rock", "melt"), default="whole")
        s.add_argument("--wt")
        s.add_argument("--water", choices=bulk_mod.WATER_MODES, default="excess")
        s.add_argument("--set", choices=bulk_mod.SYSTEMS, default="metapelite",
                       help="phase set: metapelite (White et al. 2014, with MnO) or igneous")
    pt = sub.choices["point"]
    pt.add_argument("--t", type=float, required=True, help="degC")
    pt.add_argument("--p", type=float, required=True, help="kbar")
    pt.add_argument("--save", help="write the point as a .sample")
    gr = sub.choices["grid"]
    gr.add_argument("--t", type=float, nargs=3, required=True, metavar=("FROM", "TO", "STEP"))
    gr.add_argument("--p", type=float, nargs=3, required=True, metavar=("FROM", "TO", "STEP"))
    gr.add_argument("--workers", type=int)
    gr.add_argument("--out", help="write the pseudosection (JSON)")
    a = ap.parse_args(argv)

    b = _rock(a)
    if b.left_out:
        print("left out (no solution model carries them): "
              + ", ".join(f"{ox} {v:.2f} wt%" for ox, v in b.left_out.items()))
    if a.cmd == "point":
        p = equilibrium(b, a.t, a.p)
        _print_point(p)
        if a.save:
            from protolith.metamorphism_link import to_sample

            print("saved", to_sample(p, b).save(a.save))
        return 0

    ts, ps = pseudosection.axis(*a.t), pseudosection.axis(*a.p)
    t0 = time.time()
    res = pseudosection.compute(b, ts, ps, workers=a.workers,
                                on_row=lambda d, n: print(f"  row {d}/{n}  {time.time() - t0:.0f} s",
                                                          file=sys.stderr))
    print(f"{len(ts)} x {len(ps)} points in {time.time() - t0:.0f} s, {len(res.fields)} fields")
    for f in sorted(res.fields, key=lambda f: -len(f.cells)):
        print(f"  {f.id:3d}  F={f.variance}  {len(f.cells):4d} cells  near {f.centre[0]:g} C {f.centre[1]:g} kbar"
              f"  {f.label}")
    for i, j, msg in res.failed:
        print(f"  failed at {ts[j]:g} C, {ps[i]:g} kbar: {msg}")
    if a.out:
        print("saved", res.save(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
