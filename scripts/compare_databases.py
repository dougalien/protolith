"""Reaction on OBIGT against Reaction on Protolith's Holland & Powell core: every difference, written down.

    python scripts/compare_databases.py [out.md]

Part 1 lists log K of each mineral that changed data (dissolution to Reaction's basis species) at 25-300 C
on both databases.  Part 2 runs every one-button example (columns left out: they take minutes) on both and
lists what forms, the final pH and the largest changes in saturation.  Needs Reaction's reference data
(scripts/fetch_references.ps1, or REACTION_DATA_DIR).
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reaction.app.engine import Engine  # noqa: E402
from reaction.app.scenario import EXAMPLES, example_card  # noqa: E402
from reaction.database.model import Kind  # noqa: E402
from reaction.thermo import hp_minerals  # noqa: E402

TEMPS = (25.0, 100.0, 200.0, 300.0)


def _logk(sp, t):
    try:
        v = sp.logk(t)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def _f(x, nd=2):
    return "" if x is None else f"{x:.{nd}f}"


def minerals_table(old, new) -> list[str]:
    rows = []
    for name, sp in sorted(new.species.items(), key=lambda kv: kv[0].lower()):
        if sp.kind != Kind.MINERAL or sp.provenance.database != hp_minerals.SOURCE:
            continue
        o = old.species.get(name)
        cells = []
        worst = 0.0
        for t in TEMPS:
            a, b = (_logk(o, t) if o else None), _logk(sp, t)
            cells += [_f(a), _f(b)]
            if a is not None and b is not None:
                worst = max(worst, abs(b - a))
        rows.append((name, cells, worst if o else None))
    head = "| mineral | " + " | ".join(f"{t:.0f} C OBIGT | {t:.0f} C HP" for t in TEMPS) + " | largest change |"
    out = [head, "|" + "---|" * (2 + 2 * len(TEMPS))]
    for name, cells, worst in rows:
        out.append(f"| {name} | " + " | ".join(cells) + f" | {'new' if worst is None else _f(worst)} |")
    return out


def _formed(run) -> set[str]:
    return {m for m, v in run["minerals"].items() if v and max((x or 0) for x in v) > 1e-12}


def _last(v):
    vals = [x for x in (v or []) if x is not None]
    return vals[-1] if vals else None


def examples(old_engine, new_engine) -> list[str]:
    out = []
    for key, ex in EXAMPLES.items():
        if ex.changes.get("kind") == "transport":
            continue
        res = {}
        for label, eng in (("OBIGT", old_engine), ("HP", new_engine)):
            t0 = time.time()
            try:
                res[label] = (next(iter(eng.run(example_card(key))["modes"].values())), time.time() - t0)
            except Exception as exc:                       # a run that fails is a difference too
                res[label] = (exc, time.time() - t0)
        out.append(f"### {getattr(ex, 'label', key)} (`{key}`)")
        out.append("")
        (a, ta), (b, tb) = res["OBIGT"], res["HP"]
        if isinstance(a, Exception) or isinstance(b, Exception):
            out += [f"- OBIGT: {a if isinstance(a, Exception) else 'ran'}",
                    f"- HP: {b if isinstance(b, Exception) else 'ran'}", ""]
            continue
        fa, fb = _formed(a), _formed(b)
        out.append(f"- Forms on both: {', '.join(sorted(fa & fb)) or 'nothing'}")
        if fa - fb:
            out.append(f"- Only on OBIGT: {', '.join(sorted(fa - fb))}")
        if fb - fa:
            out.append(f"- Only on HP: {', '.join(sorted(fb - fa))}")
        pa, pb = _last(a["properties"].get("pH")), _last(b["properties"].get("pH"))
        out.append(f"- Final pH: {_f(pa)} (OBIGT), {_f(pb)} (HP)")
        sat = []
        for m in set(a["saturation"]) & set(b["saturation"]):
            x, y = _last(a["saturation"][m]), _last(b["saturation"][m])
            if x is not None and y is not None:
                sat.append((abs(y - x), m, x, y))
        sat.sort(reverse=True)
        if sat:
            out.append("- Largest changes in final saturation index (log Q/K): "
                       + "; ".join(f"{m} {x:.2f} to {y:.2f}" for _, m, x, y in sat[:5]))
        out.append(f"- Run time: {ta:.0f} s (OBIGT), {tb:.0f} s (HP)")
        out.append("")
    return out


def main(path: str | None = None) -> None:
    old_engine, new_engine = Engine(database="current"), Engine(database="hp")
    old, new = old_engine.db, new_engine.db
    ov_notes = [n for n in new.data_notes]
    lines = ["# Reaction on the shared core: what changes", "",
             f"Written by `scripts/compare_databases.py` on {time.strftime('%Y-%m-%d')}. "
             f"Old: {old.title}. New: {new.title}.", ""]
    lines += [f"- {n}" for n in ov_notes] + [""]
    lines += ["## 1. log K of the minerals that changed data", "",
              "Dissolution to Reaction's basis species at water saturation (1 bar to 100 C). "
              "`new` marks a mineral OBIGT does not have.", ""]
    lines += minerals_table(old, new) + [""]
    ov = new.hp_overlay
    lines += ["## 2. The bridge", "",
              "OBIGT species of these elements are moved by one constant per atom, fitted on the HP minerals "
              "of the element (25-300 C). Residual: how far each mineral's HP energy still sits from OBIGT's "
              "after the bridge, kJ per formula (negative: HP more stable).", ""]
    for el, d in ov.bridge.items():
        lines.append(f"- **{el}**: {d / 1000:+.2f} kJ per atom. Residuals: "
                     + ", ".join(f"{m} {r:+.1f}" for m, r in sorted(ov.bridge_fit[el], key=lambda x: x[1])))
    if ov.mismatched:
        lines += ["", "Kept from OBIGT: " + "; ".join(ov.mismatched)]
    lines += ["", "## 3. The examples on both databases", ""]
    lines += examples(old_engine, new_engine)
    text = "\n".join(lines) + "\n"
    if path:
        Path(path).write_text(text, "utf-8")
        print(f"written to {path}")
    else:
        print(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
