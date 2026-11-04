"""Protolith (metamorphism) on Streamlit: an Input window and a Results window, as in Protolith.exe.

The run is the desktop app's ``State`` (``metamorphism.app.server``), unchanged: one equilibrium, a P-T
path, or a pseudosection, in a background thread.  Each user has a private workspace id in the address
(``?w=...``) shared by their two windows, so the Results window follows the run live on a second screen.
Nothing here computes thermodynamics.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import secrets
import threading
import time
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from .. import __version__
from .. import bulk as bulk_mod
from .. import facies
from ..app.server import CARDS, NOTES, OXIDES, SOURCES, SYSTEM_LABEL, State

FEEDBACK_URL = "https://github.com/dougalien/protolith/issues"
PATHS = {"input": "./", "results": "./results"}
WORKSPACE_TTL = 12 * 3600
STATIC = Path(__file__).resolve().parents[1] / "app" / "static"
ICON = str(STATIC / "protolith_512.png")
PALETTE = ["#3E5C6B", "#B4532A", "#C49A55", "#5E8C6A", "#8A6A9A", "#4F86A0", "#A8644A", "#6B6F45",
           "#7A8F99", "#C77B5A", "#9DA36A", "#5B4E7A"]
BG, GRID = "#F3F1EB", "#DDD8CC"
STRIPE = ("linear-gradient(90deg, #D6B27C 0 22%, #3E5C6B 22% 34%, #D6B27C 34% 62%, #B4532A 62% 70%, "
          "#D6B27C 70% 88%, #3E5C6B 88% 100%)")
KINDS = {"path": "A P-T path", "grid": "A pseudosection (T-P grid)", "point": "One temperature and pressure"}


# ---- workspaces: one State per user, shared by that user's two windows -------------------------------
@st.cache_resource
def _registry() -> dict:
    return {"lock": threading.Lock(), "ws": {}}


def workspace() -> tuple[str, State]:
    reg = _registry()
    wid = st.query_params.get("w")
    if not wid or len(wid) > 64:
        wid = secrets.token_urlsafe(16)
        st.query_params["w"] = wid
    now = time.time()
    with reg["lock"]:
        for k in [k for k, (_, t) in reg["ws"].items() if now - t > WORKSPACE_TTL and k != wid]:
            if reg["ws"][k][0].status != "running":
                del reg["ws"][k]
        state = reg["ws"][wid][0] if wid in reg["ws"] else State()
        reg["ws"][wid] = (state, now)
    return wid, state


def follow(state: State, key: str) -> None:
    seen = f"seen-{key}"
    st.session_state.setdefault(seen, state.version)

    @st.fragment(run_every=1.0 if state.status == "running" else 2.0)
    def _watch():
        if state.version != st.session_state[seen]:
            st.session_state[seen] = state.version
            st.rerun()
    _watch()
    st.session_state[seen] = state.version


def _svg(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((STATIC / name).read_bytes()).decode()


def header(subtitle: str) -> None:
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:12px;padding:4px 0 10px">
<img src="{_svg('dougalien_mark.svg')}" width="34" height="34" alt="Dougalien Systems">
<img src="{_svg('protolith_mark.svg')}" width="30" height="30" alt="">
<span style="font-size:1.55rem;font-weight:600;color:#2B3134">Protolith</span>
<a href="https://dougalien.com" target="_blank" style="color:#5b6468;text-decoration:none">by Dougalien Systems</a>
<span style="color:#6f777a;font-size:0.9rem">· {subtitle}</span></div>
<div style="height:4px;border-radius:2px;background:{STRIPE};margin:0 0 14px"></div>""",
        unsafe_allow_html=True)


def footer() -> None:
    st.divider()
    st.caption(f"Protolith {__version__} · alpha · [Report a problem]({FEEDBACK_URL}) · Metamorphism on the "
               "Holland and Powell data; every number comes from Protolith's own solver.")


# ---- the Input window ---------------------------------------------------------------------------
def _set_rock(name: str) -> None:
    ss = st.session_state
    wt = bulk_mod.PRESETS[name]
    for ox in OXIDES:
        ss[f"ox-{ox}"] = float(wt.get(ox, 0.0))
    ss["rock"], ss["name"] = name, name


def _apply_card(c: dict) -> None:
    ss = st.session_state
    _set_rock(c["rock"])
    ss["system"], ss["water"], ss["kind"] = c["system"], c["water"], c["kind"]
    if c["kind"] == "path":
        ss["path_text"] = "\n".join(f"{t:g}, {p:g}" for t, p in c["path"])
        ss["n"] = int(c["n"])
    elif c["kind"] == "grid":
        ss["t0"], ss["t1"], ss["ts"] = map(float, c["t"])
        ss["p0"], ss["p1"], ss["ps"] = map(float, c["p"])
    else:
        ss["t"], ss["p"] = float(c["t"]), float(c["p"])
    ss["card"] = c["key"]


def _defaults() -> None:
    ss = st.session_state
    if ss.get("_init"):
        return
    ss["_init"] = True
    ss.update(t=550.0, p=6.0, t0=450.0, t1=700.0, ts=50.0, p0=2.0, p1=10.0, ps=2.0, n=16,
              path_text="450, 4\n600, 7.5\n700, 8")
    _apply_card(CARDS[0])


def _inputs() -> dict:
    ss = st.session_state
    d = {"bulk": {ox: ss[f"ox-{ox}"] for ox in OXIDES if ss[f"ox-{ox}"]}, "name": ss.get("name") or "rock",
         "system": ss.get("system") or "metapelite", "water": ss.get("water") or "excess",
         "kind": ss.get("kind") or "path"}
    if d["kind"] == "path":
        way = []
        for line in ss["path_text"].splitlines():
            if line.strip():
                parts = line.replace(";", ",").split(",")
                if len(parts) != 2:
                    raise ValueError(f"'{line.strip()}' is not a temperature, pressure pair")
                way.append([parts[0].strip(), parts[1].strip()])
        d.update(path=way, n=int(ss["n"]))
    elif d["kind"] == "grid":
        d.update(t=[ss["t0"], ss["t1"], ss["ts"]], p=[ss["p0"], ss["p1"], ss["ps"]])
    else:
        d.update(t=ss["t"], p=ss["p"])
    return d


def input_page() -> None:
    st.set_page_config(page_title="Protolith · Input", page_icon=ICON, layout="wide")
    wid, state = workspace()
    _defaults()
    top_l, top_r = st.columns([4, 1])
    with top_l:
        header("metamorphism: stable assemblages, P-T paths and pseudosections")
    top_r.link_button("Open results window", f"{PATHS['results']}?w={wid}", width="stretch",
                      help="The results in a window of its own, to drag to another screen")
    snap = state.snapshot()
    running = snap["status"] == "running"

    with st.container(border=True):
        st.markdown("**Start from a card**")
        for group, title in (("path", "P-T paths"), ("grid", "Pseudosections"), ("point", "One point")):
            cards = [c for c in CARDS if c["group"] == group]
            st.caption(title)
            cols = st.columns(4)
            for k, c in enumerate(cards):
                if cols[k % 4].button(c["title"], key=f"card-{c['key']}", help=c["blurb"], width="stretch",
                                      disabled=running):
                    _apply_card(c)
                    st.rerun()
        card = next((c for c in CARDS if c["key"] == st.session_state.get("card")), None)
        if card:
            st.caption(card["blurb"])

    left, right = st.columns(2)
    with left.container(border=True):
        st.markdown("**The rock**")
        rocks = list(bulk_mod.PRESETS)
        a, b = st.columns([2, 1])
        pick = a.selectbox("Rock", rocks, index=rocks.index(st.session_state.get("rock", rocks[0])),
                           key="rock-pick", disabled=running)
        if pick != st.session_state.get("rock"):
            _set_rock(pick)
            st.rerun()
        b.text_input("Name", key="name", disabled=running)
        st.caption(SOURCES.get(st.session_state.get("rock"), ""))
        st.caption("Oxides, wt%")
        cols = st.columns(4)
        for k, ox in enumerate(OXIDES):
            cols[k % 4].number_input(ox, min_value=0.0, max_value=100.0, step=0.1, format="%.2f", key=f"ox-{ox}",
                                     disabled=running)
        total = sum(st.session_state[f"ox-{ox}"] for ox in OXIDES)
        st.caption(f"Total {total:.2f} wt% (normalized for the run). Left out by the "
                   f"{st.session_state.get('system') or 'metapelite'} set: {', '.join(bulk_mod.LEFT_OUT[st.session_state.get('system') or 'metapelite'])}.")

    with right.container(border=True):
        st.markdown("**Minerals and water**")
        st.segmented_control("Phase set", list(SYSTEM_LABEL), format_func=SYSTEM_LABEL.get, key="system",
                             disabled=running)
        st.segmented_control("Water", ["excess", "bulk"], key="water", disabled=running,
                             format_func={"excess": "In excess", "bulk": "The rock's own"}.get)
        st.caption("In excess: a free fluid at every point, as usual for prograde metamorphism. The rock's own: "
                   "only the H2O in the analysis, so the rock can be short of water.")
    with right.container(border=True):
        st.markdown("**The run**")
        st.segmented_control("Kind", list(KINDS), format_func=KINDS.get, key="kind", disabled=running)
        kind = st.session_state.get("kind") or "path"
        if kind == "path":
            st.text_area("Path: one temperature (°C), pressure (kbar) per line", key="path_text", height=110,
                         disabled=running)
            st.number_input("Points along the path", min_value=2, max_value=60, step=1, key="n", disabled=running)
        elif kind == "grid":
            a, b, c = st.columns(3)
            a.number_input("T from (°C)", key="t0", step=10.0, disabled=running)
            b.number_input("T to (°C)", key="t1", step=10.0, disabled=running)
            c.number_input("T step", key="ts", min_value=1.0, step=5.0, disabled=running)
            a.number_input("P from (kbar)", key="p0", step=0.5, disabled=running)
            b.number_input("P to (kbar)", key="p1", step=0.5, disabled=running)
            c.number_input("P step", key="ps", min_value=0.1, step=0.5, disabled=running)
            nt = int((st.session_state["t1"] - st.session_state["t0"]) // max(st.session_state["ts"], 1e-9)) + 1
            np_ = int((st.session_state["p1"] - st.session_state["p0"]) // max(st.session_state["ps"], 1e-9)) + 1
            st.caption(f"{nt} x {np_} = {nt * np_} points, a few seconds each.")
        else:
            a, b = st.columns(2)
            a.number_input("Temperature (°C)", key="t", step=10.0, disabled=running)
            b.number_input("Pressure (kbar)", key="p", step=0.5, disabled=running)

        a, b = st.columns(2)
        if a.button("Run", type="primary", width="stretch", disabled=running):
            try:
                state.start(_inputs())
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if b.button("Stop", width="stretch", disabled=not running):
            state.stop()
        done, n = snap["progress"]
        if running:
            st.progress(done / n if n else 0.0, text=f"Running: {done} of {n} · {snap['elapsed']:.0f} s")
        elif snap["status"] == "done":
            st.success(f"Run {snap['run_id']} done in {snap['elapsed']:.0f} s. The results window shows it.")
        elif snap["status"] in ("stopped", "error"):
            st.warning(snap["message"] or snap["status"])
    follow(state, "input")
    footer()


# ---- the Results window ---------------------------------------------------------------------------
def _fig(xlabel, ylabel, height=520) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), xaxis_title=xlabel, yaxis_title=ylabel,
                      legend=dict(orientation="h", y=-0.18), colorway=PALETTE, paper_bgcolor=BG, plot_bgcolor=BG,
                      font=dict(color="#2B3134"))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor="#CFC8B8")
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#CFC8B8")
    return fig


def _facies_plot(path: dict) -> go.Figure:
    d = facies.diagram()
    fig = _fig("temperature, °C", "pressure, kbar")
    for f in d["facies"]:
        xs, ys = [p[0] for p in f["points"]], [p[1] for p in f["points"]]
        fig.add_scatter(x=xs + xs[:1], y=ys + ys[:1], mode="lines", line=dict(color="#c9c1b0", width=1),
                        fill="toself", fillcolor="rgba(214,178,124,0.10)", hoverinfo="skip", showlegend=False)
        fig.add_annotation(x=sum(xs) / len(xs), y=sum(ys) / len(ys), text=f["name"], showarrow=False,
                           font=dict(size=10, color="#8a8370"))
    for ln in d["lines"]:
        fig.add_scatter(x=[p[0] for p in ln["points"]], y=[p[1] for p in ln["points"]], mode="lines",
                        line=dict(color="#7A8F99", width=1, dash="dot"), name=ln["label"], hoverinfo="name")
    pts = path["points"]
    fig.add_scatter(x=[p["t_c"] for p in pts], y=[p["p_kbar"] for p in pts], mode="lines+markers", name="Path",
                    line=dict(color="#B4532A", width=2.5),
                    marker=dict(size=8, color=["#B4532A" if p["state"] == "done" else "#cccccc" for p in pts]),
                    text=[p.get("label", p["state"]) for p in pts],
                    hovertemplate="%{x:.0f} °C, %{y:.2f} kbar<br>%{text}<extra></extra>")
    return fig


def _modes_plot(path: dict) -> go.Figure:
    pts = [p for p in path["points"] if p["state"] == "done"]
    fig = _fig("temperature along the path, °C", "wt% of the rock", height=440)
    for m in path["minerals"]:
        fig.add_scatter(x=[p["t_c"] for p in pts], y=[p["modes"].get(m, 0) for p in pts], name=m, mode="lines",
                        stackgroup="one", hovertemplate=m + " %{y:.1f}%<extra></extra>")
    return fig


def _in_out(path: dict) -> list[str]:
    out, prev = [], None
    for p in path["points"]:
        if p["state"] != "done":
            continue
        cur = set(p["assemblage"])
        if prev is not None:
            came, went = sorted(cur - prev), sorted(prev - cur)
            if came or went:
                bits = ([f"**{', '.join(came)}** in"] if came else []) + ([f"{', '.join(went)} out"] if went else [])
                out.append(f"{p['t_c']:.0f} °C, {p['p_kbar']:.1f} kbar: " + "; ".join(bits))
        prev = cur
    return out


def _grid_plot(grid: dict) -> go.Figure:
    t, p, cells = grid["t_c"], grid["p_kbar"], grid["cells"]
    var = {f["id"]: f["variance"] for f in grid["fields"]}
    lab = {f["id"]: f["label"] for f in grid["fields"]}
    z = [[(var.get(c) if c is not None and c >= 0 else None) for c in row] for row in cells]
    text = [[(lab.get(c, "failed") if c is not None else "running") for c in row] for row in cells]
    fig = _fig("temperature, °C", "pressure, kbar", height=600)
    fig.add_heatmap(x=t, y=p, z=z, text=text, colorscale=[[0, "#F3EBDD"], [1, "#9FB0B8"]], showscale=True,
                    colorbar=dict(title="variance"), hovertemplate="%{x:.0f} °C, %{y:.2f} kbar<br>%{text}<extra></extra>")
    for f in grid["fields"]:
        if f["n"] >= 2:
            fig.add_annotation(x=f["centre"][0], y=f["centre"][1], text=str(f["id"]), showarrow=False,
                               font=dict(size=11, color="#2B3134"))
    for (a, b), (c, d) in grid["boundaries"]:
        fig.add_scatter(x=[a, c], y=[b, d], mode="lines", line=dict(color="#3E5C6B", width=1.2),
                        hoverinfo="skip", showlegend=False)
    return fig


def _point_table(pt: dict) -> None:
    rows = [{"mineral": m["abbr"], "name": m["name"], "wt% of rock": round(m["mode"], 2),
             "formula": m["formula"]} for m in pt["minerals"]]
    st.dataframe(rows, hide_index=True, width="stretch")
    if pt.get("fluid"):
        st.caption(f"Free fluid: {pt['fluid']['grams']:.2f} g per 100 g of rock (not counted in the modes).")


def _csv(snap: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    if snap["path"]:
        ms = snap["path"]["minerals"]
        w.writerow(["T_C", "P_kbar", "assemblage"] + [f"{m}_wt_pct" for m in ms])
        for p in snap["path"]["points"]:
            w.writerow([p["t_c"], p["p_kbar"], p.get("label", p["state"])] + [p.get("modes", {}).get(m, "") for m in ms])
    elif snap["grid"]:
        g = snap["grid"]
        lab = {f["id"]: f["label"] for f in g["fields"]}
        w.writerow(["T_C", "P_kbar", "field", "assemblage"])
        for i, pr in enumerate(g["p_kbar"]):
            for j, tc in enumerate(g["t_c"]):
                c = g["cells"][i][j]
                w.writerow([tc, pr, c, lab.get(c, "")])
    elif snap["point"]:
        w.writerow(["mineral", "name", "wt_pct_of_rock", "formula"])
        for m in snap["point"]["minerals"]:
            w.writerow([m["abbr"], m["name"], m["mode"], m["formula"]])
    return buf.getvalue()


def results_page() -> None:
    st.set_page_config(page_title="Protolith · Results", page_icon=ICON, layout="wide")
    wid, state = workspace()
    top_l, top_r = st.columns([4, 1])
    with top_l:
        header("results")
    top_r.link_button("Back to the input window", f"{PATHS['input']}?w={wid}", width="stretch")
    snap = state.snapshot()
    follow(state, "results")
    if not snap["run"]:
        st.info("No run yet. Choose a card in the input window and press Run; the results appear here as they come in.")
        footer()
        return
    b = snap["bulk"]
    kind = snap["run"]["kind"]
    st.subheader(f"{b['name']}: {KINDS[kind].lower()}")
    st.caption(f"{b['system_label']} · water {'in excess' if b['water'] == 'excess' else 'from the rock'} · "
               f"{b['components']} components · run {snap['run_id']}"
               + (f" · left out: {', '.join(b['left_out'])}" if b["left_out"] else ""))
    done, n = snap["progress"]
    if snap["status"] == "running":
        st.progress(done / n if n else 0.0, text=f"Running: {done} of {n} · {snap['elapsed']:.0f} s")
    elif snap["status"] == "done":
        st.success(f"Run {snap['run_id']}: done in {snap['elapsed']:.0f} s.")
    elif snap["message"]:
        st.warning(snap["message"])

    if kind == "path" and snap["path"]:
        path = snap["path"]
        changes = _in_out(path)
        with st.container(border=True):
            st.markdown("**Minerals coming in and going out**")
            for c in changes or ["No change in the assemblage along the path so far."]:
                st.markdown(c)
        st.plotly_chart(_facies_plot(path), width="stretch")
        st.caption("Facies fields are schematic, after Spear (1993) and Winter (2010); the Al2SiO5 and muscovite + "
                   "quartz lines are worked out from ds6.2.")
        if path["minerals"]:
            st.markdown("**Modes along the path**")
            st.plotly_chart(_modes_plot(path), width="stretch")
        pick = [k for k, p in enumerate(path["points"]) if p["state"] == "done"]
    elif kind == "grid" and snap["grid"]:
        g = snap["grid"]
        st.plotly_chart(_grid_plot(g), width="stretch")
        st.caption("Each cell is one equilibrium; fields are shaded by variance (darker, more degrees of freedom).")
        st.dataframe([{"field": f["id"], "assemblage": f["label"], "variance": f["variance"], "cells": f["n"]}
                      for f in g["fields"]], hide_index=True, width="stretch")
        pick = []
    elif kind == "point" and snap["point"]:
        pt = snap["point"]
        st.markdown(f"**{pt['label']}** at {pt['t_c']:.0f} °C and {pt['p_kbar']:.2f} kbar · variance {pt['variance']}")
        _point_table(pt)
        pick = [0]
    else:
        pick = []

    if snap["status"] != "running":
        a, b2, c = st.columns(3)
        a.download_button("Download the table (CSV)", _csv(snap), file_name="protolith.csv", mime="text/csv",
                          width="stretch")
        if pick:
            labels = ({k: f"{snap['path']['points'][k]['t_c']:.0f} °C, {snap['path']['points'][k]['p_kbar']:.1f} kbar"
                       for k in pick} if kind == "path" else {0: "this point"})
            j = b2.selectbox("Sample from", pick, format_func=labels.get, key="smp-pt")
            smp = state.sample(0, j)
            if smp is not None:
                c.download_button("Save sample", json.dumps(smp.to_dict(), indent=1), width="stretch",
                                  file_name=f"protolith_{smp.conditions['t_c']:.0f}C.sample", mime="application/json")
    with st.expander("Notes on the models"):
        for t in snap["notes"]:
            st.markdown(f"- {t}")
    footer()
