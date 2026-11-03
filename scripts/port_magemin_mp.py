"""Write the metapelite solution models of White et al. (2014) as core code, from MAGEMin's sources.

    python scripts/port_magemin_mp.py <MAGEMin checkout> src/protolith/core/hp/solutions_mp.py

MAGEMin (github.com/ComputationalThermodynamics/MAGEMin) writes each model in terms of its own
compositional variables x: the end-member proportions p(x) (``px_mp_*``), the site fractions sf(x) and
the activities as products of site-fraction powers (``obj_mp_*``), and the end-member recipes, Margules
parameters W and van Laar sizes v (``G_SS_mp_*_function``).  The core writes the same models in terms of
p: site fractions linear in p (sf = A p), or a ratio of two linear forms where the model uses one (the
Fe/(Fe+Mg) of the melt).  This script finds A (and the ratios) by sampling x, checks that the fit is
exact, reads the activities and parameters, and writes Python.  It is run once; its output is
committed and the script kept here as the record of where every number came from.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import sympy as sp

MODELS = ("liq", "fsp", "bi", "g", "ep", "ma", "mu", "opx", "sa", "cd", "st", "chl", "ctd", "sp", "mt", "ilm",
          "ilmm")
T, P = sp.symbols("T P")


def _block(text: str, start_pat: str) -> str:
    m = re.search(start_pat, text)
    if not m:
        raise SystemExit(f"not found: {start_pat}")
    i = m.start()
    depth, j = 0, text.index("{", i)
    while True:
        c = text[j]
        depth += c == "{"
        depth -= c == "}"
        j += 1
        if depth == 0:
            return text[i:j]


def _c2py(expr: str) -> str:
    e = expr.strip().rstrip(";")
    e = e.replace("SS_ref_db.P", "P").replace("SS_ref_db.T", "T")
    e = re.sub(r"x\[(\d+)\]", r"x\1", e)
    e = re.sub(r"sf\[(\d+)\]", r"sf\1", e)
    e = re.sub(r"cpow\(", "pow(", e)
    e = re.sub(r"csqrt\(", "sqrt(", e)
    e = re.sub(r"(\d)\.(?!\d)", r"\1.0", e)          # 1./3. -> 1.0/3.0
    return e


def _sym(e: str, extra: dict | None = None):
    ns = {"pow": sp.Pow, "sqrt": sp.sqrt, "T": T, "P": P}
    ns.update(extra or {})
    return sp.sympify(e, locals=ns)


def parse(src: Path, name: str) -> dict:
    gss = (src / "tc_gss_function.c").read_text()
    obj = (src / "objective_functions.c").read_text()
    g = _block(gss, rf"SS_ref G_SS_mp_{name}_function\(")
    px = _block(obj, rf"void px_mp_{name}\(")
    of = _block(obj, rf"double obj_mp_{name}\(")

    ems = re.findall(r'"([^"]+)"', re.search(r"EM_tmp\[\]\s*=\s*\{([^}]*)\}", g).group(1))
    sites = re.findall(r'"([^"]+)"', re.search(r"SF_tmp\[\]\s*=\s*\{([^}]*)\}", g).group(1))
    w = {int(i): _sym(_c2py(e)) for i, e in re.findall(r"SS_ref_db\.W\[(\d+)\]\s*=\s*([^;]+);", g)}
    v = {int(i): float(_sym(_c2py(e))) for i, e in re.findall(r"SS_ref_db\.v\[(\d+)\]\s*=\s*([^;]+);", g)}
    eq = {}
    for var, args in re.findall(r"em_data\s+(\w+)\s*=\s*get_em_data\((.*?)\);", g, re.S):
        q = re.findall(r'"([^"]+)"', args)
        eq[var] = (q[-2], q[-1])
    gsyms = {f"{var}_gb": sp.Symbol(f"{var}_gb") for var in eq}
    gbase = {}
    for i, e in re.findall(r"SS_ref_db\.gbase\[(\d+)\]\s*=\s*([^;]+);", g):
        e = re.sub(r"(\w+)\.gb", r"\1_gb", _c2py(e))
        gbase[int(i)] = _sym(e, gsyms)

    p_expr = {int(i): _c2py(e) for i, e in re.findall(r"\bp\[(\d+)\]\s*=\s*([^;]+);", px)}
    sf_expr = {int(i): _c2py(e) for i, e in re.findall(r"\bsf\[(\d+)\]\s*=\s*([^;]+);", of)}
    defs = {}
    for var, e in re.findall(r"double complex (c[ps]_\w+)\s*=\s*([^;]+);", of):
        defs[var] = _c2py(e)
    acts = {}
    for i, e in re.findall(r"\bmu\[(\d+)\]\s*=\s*(?:gb\[\d+\]\s*\+\s*)?R\*T\*rlog\(\((.*?)\)\)\s*\+\s*(?:gb|mu_Gex)", of):
        e = re.sub(r"\+\s*d_em\[\d+\]", "", e)
        for var, d in defs.items():
            e = re.sub(rf"\b{var}\b", f"({d})", e)
        acts[int(i)] = _c2py(e)
    sym = "asym" if "mu_Gex_asym" in of else "sym"
    nx = 1 + max(int(k) for k in re.findall(r"x(\d+)", " ".join(p_expr.values())))
    return dict(name=name, ems=ems, sites=sites, w=w, v=v, eq=eq, gbase=gbase, p=p_expr, sf=sf_expr,
                acts=acts, sym=sym, nx=nx)


def _eval(exprs: dict, xs: np.ndarray, n: int) -> np.ndarray:
    out = np.zeros((len(xs), n))
    for k, x in enumerate(xs):
        env = {f"x{i}": v for i, v in enumerate(x)}
        env.update(pow=pow, sqrt=np.sqrt)
        for i in range(n):
            out[k, i] = eval(exprs[i], env)
    return out


def site_map(m: dict, rng) -> tuple:
    """sf = A p for linear sites; (num, den) linear forms for ratio sites."""
    n, ns = len(m["ems"]), len(m["sites"])
    xs = rng.uniform(0.05, 0.3, size=(60, m["nx"]))
    pm = _eval(m["p"], xs, n)
    sm = _eval(m["sf"], xs, ns)
    lin, ratio = {}, {}
    for j in range(ns):
        a, res, *_ = np.linalg.lstsq(pm, sm[:, j], rcond=None)
        if np.max(np.abs(pm @ a - sm[:, j])) < 1e-10:
            lin[j] = a
            continue
        # sf (b.p) - a.p = 0 for all samples: the null space of [ -p | sf p ]
        mat = np.hstack([-pm, sm[:, [j]] * pm])
        _, sv, vt = np.linalg.svd(mat)
        vec = vt[-1]
        a, b = vec[:n], vec[n:]
        scale = b.sum() if abs(b.sum()) > 1e-9 else np.max(np.abs(b))
        a, b = a / scale, b / scale
        if sv[-1] > 1e-9 or np.max(np.abs(pm @ a / (pm @ b) - sm[:, j])) > 1e-9:
            raise SystemExit(f"{m['name']}: site {m['sites'][j]} is neither linear nor a ratio in p")
        ratio[j] = (a, b)
    return lin, ratio


def activity(e: str, sites: list) -> tuple:
    syms = {f"sf{j}": sp.Symbol(s) for j, s in enumerate(sites)}
    ex = sp.expand_power_base(_sym(e, syms), force=True)
    k, powers = sp.Integer(1), {}
    for f in sp.Mul.make_args(ex):
        if f.is_number:
            k *= f
        else:
            base, exp = f.as_base_exp()
            powers[str(base)] = powers.get(str(base), 0) + float(exp)
    return float(k), powers


def _num(v: float) -> str:
    r = round(float(v), 12)
    if abs(r - round(r)) < 1e-12:
        return f"{round(r):.1f}"
    return repr(r)


def recipe(expr, eq: dict) -> tuple:
    """(terms [(coef, name, state)], dqf (a, b, c))."""
    expr = sp.expand(expr)
    terms = []
    for var, (nm, state) in eq.items():
        c = expr.coeff(sp.Symbol(f"{var}_gb"))
        if c != 0:
            terms.append((float(c), nm, state))
    rest = sp.expand(expr - sum(sp.Float(c) * sp.Symbol(f"{v}_gb") for v in eq
                                for c in [expr.coeff(sp.Symbol(f"{v}_gb"))] if c != 0))
    b, c = float(rest.coeff(T)), float(rest.coeff(P))
    a = float(rest.subs({T: 0, P: 0}))
    return terms, (a, b, c)


def emit(m: dict, rng) -> str:
    lin, ratio = site_map(m, rng)
    n = len(m["ems"])
    sites = m["sites"]
    var = m["name"].upper() + "_MP"
    lines = [f"{var} = HPSolution(", f'    "{m["name"]}",', "    ("]
    for i, e in enumerate(m["ems"]):
        terms, (a, b, c) = recipe(m["gbase"][i], m["eq"])
        tt = ", ".join(f'({_num(k)}, "{nm}"' + (f', "{st}")' if st != "equilibrium" else ")") for k, nm, st in terms)
        dqf = f", dqf=({_num(a)}, {_num(b)}, {_num(c)})" if (a, b, c) != (0, 0, 0) else ""
        lines.append(f'     em("{e}", {tt}{dqf}, dataset=DS),')
    lines.append("    ),")
    lin_sites = [sites[j] for j in sorted(lin)]
    lines.append(f"    {tuple(lin_sites)!r},")
    occ = []
    for i, e in enumerate(m["ems"]):
        d = {sites[j]: _num(lin[j][i]) for j in sorted(lin) if abs(lin[j][i]) > 1e-12}
        occ.append(f'     "{e}": {{' + ", ".join(f'"{k}": {v}' for k, v in d.items()) + "}")
    lines.append("    {\n" + ",\n".join(occ) + "},")
    act = []
    for i, e in enumerate(m["ems"]):
        k, pw = activity(m["acts"][i], sites)
        args = ", ".join(f"{s}={_num(x)}" for s, x in pw.items())
        kk = f"{_num(k)}, " if abs(k - 1) > 1e-12 else ""
        act.append(f'     "{e}": A({kk}{args})')
    lines.append("    {\n" + ",\n".join(act) + "},")
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    wv = []
    for k, _ in enumerate(pairs):
        ex = sp.expand(m["w"].get(k, sp.Integer(0)))
        a, b, c = float(ex.subs({T: 0, P: 0})), float(ex.coeff(T)), float(ex.coeff(P))
        wv.append(_num(a) if (b, c) == (0, 0) else f"({_num(a)}, {_num(b)}, {_num(c)})")
    lines.append(f"    _pairs({n}, [{', '.join(wv)}]),")
    if m["sym"] == "asym":
        lines.append(f"    v=({', '.join(_num(m['v'][i]) for i in range(n))}),")
    if ratio:
        rr = []
        for j, (a, b) in sorted(ratio.items()):
            an = "{" + ", ".join(f'"{m["ems"][i]}": {_num(a[i])}' for i in range(n) if abs(a[i]) > 1e-12) + "}"
            bn = "{" + ", ".join(f'"{m["ems"][i]}": {_num(b[i])}' for i in range(n) if abs(b[i]) > 1e-12) + "}"
            rr.append(f'"{sites[j]}": ({an}, {bn})')
        lines.append("    ratios={" + ", ".join(rr) + "},")
    lines.append(")")
    return "\n".join(lines)


HEAD = '''"""The metapelite set: the solution models of White, Powell, Holland, Johnson and Green (2014, J. Metamorphic
Geol. 32, 261-286), on the ds6.2 dataset (MnNCKFMASHTO).

Written by scripts/port_magemin_mp.py from MAGEMin's sources (the ``G_SS_mp_*`` functions of
src/TC_database/tc_gss_function.c and ``px_mp_*`` / ``obj_mp_*`` of objective_functions.c): the numbers
are MAGEMin's, taken at Douglas's request (2026-11-03), and the form is the core's (site fractions
linear in the end-member proportions, or a ratio of two linear forms).  Do not edit by hand; run the
script again.

Names are MAGEMin's: liq, fsp, bi, g, ep, ma (margarite-rich white mica), mu, opx, sa, cd, st, chl, ctd,
sp, mt, ilm (Mn- and Mg-free ilmenite-hematite) and ilmm (with geikielite and pyrophanite).
"""
from __future__ import annotations

from .solutions import A, HPSolution, _pairs, em

DS = "62"

'''


def main(magemin: str, out: str) -> None:
    src = Path(magemin) / "src" / "TC_database"
    rng = np.random.default_rng(1)
    parts = [HEAD]
    for name in MODELS:
        parts.append(emit(parse(src, name), rng))
        parts.append("")
    parts.append("SOLUTIONS_MP = {s.name: s for s in (" + ", ".join(f"{n.upper()}_MP" for n in MODELS) + ")}")
    Path(out).write_text("\n".join(parts) + "\n", encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
