"""Protolith on Streamlit: the home page and every module's windows in one app.

The modules' own Streamlit pages (``magma.web.app``, ``reaction.web.app``) are mounted under
``/magma``, ``/magma-results``, ``/reaction``, ``/reaction-results`` and ``/sources``.  One private
workspace id in the address (``?w=...``) is shared by all of a visitor's windows, so Magma's
"Send to Reaction" puts a step straight on that visitor's Reaction card, as in Protolith.exe.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

import magma.web.app as magma_web
import reaction.web.app as reaction_web

from .. import __version__
from ..sample import SampleError

FEEDBACK_URL = "https://github.com/dougalien/protolith/issues"
STATIC = Path(__file__).resolve().parents[1] / "app" / "static"
ICON = str(STATIC / "protolith_512.png")
TAKE = {"rock": "The rock (its minerals)", "melt": "The melt (as a glass)", "both": "Rock and melt"}

magma_web.PATHS.update(input="./magma", results="./magma-results")
reaction_web.PATHS.update(input="./reaction", results="./reaction-results", sources="./sources")
magma_web.FEEDBACK_URL = reaction_web.FEEDBACK_URL = FEEDBACK_URL

PLANNED = [("Metamorphism", "Rocks re-equilibrating at new temperature and pressure, with the same Holland and "
                            "Powell data as Magma."),
           ("Surface", "Weathering, soils and diagenesis at low temperature, on Reaction's water chemistry.")]


def _svg(name: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode((STATIC / name).read_bytes()).decode()


def _wid() -> str:
    wid, _ = reaction_web.workspace()          # makes the id if the address has none
    return wid


def home_page() -> None:
    st.set_page_config(page_title="Protolith", page_icon=ICON, layout="wide")
    wid = _wid()
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:12px;padding:4px 0 10px">
<img src="{_svg('dougalien_mark.svg')}" width="34" height="34" alt="Dougalien Systems">
<img src="{_svg('protolith_mark.svg')}" width="30" height="30" alt="">
<span style="font-size:1.55rem;font-weight:600;color:#2B3134">Protolith</span>
<a href="https://dougalien.com" target="_blank" style="color:#5b6468;text-decoration:none">by Dougalien Systems</a>
<span style="color:#6f777a;font-size:0.9rem">· version {__version__}</span></div>
<div style="height:4px;border-radius:2px;background:{magma_web.STRIPE};margin:0 0 14px"></div>""",
        unsafe_allow_html=True)
    st.markdown("A geochemical calculator in modules. Each module opens in its own windows; a rock or melt from one "
                "module can be handed to the next.")
    mods = [("magma", "Magma", "Melting and crystallization of silicate melts (Holland and Powell, or MELTS)."),
            ("reaction", "Reaction", "Water and rock: speciation, mineral reactions and reaction paths in an aqueous fluid.")]
    cols = st.columns(len(mods) + len(PLANNED))
    for c, (key, name, about) in zip(cols, mods):
        with c.container(border=True):
            st.markdown(f"<img src='{_svg(key + '_mark.svg')}' width='30'> &nbsp;**{name}**", unsafe_allow_html=True)
            st.caption(about)
            st.link_button(f"Open {name}", f"./{key}?w={wid}", type="primary", use_container_width=True)
            st.link_button("Results window", f"./{key}-results?w={wid}", use_container_width=True,
                           help="The results in a window of its own, to drag to another screen")
    for c, (name, about) in zip(cols[len(mods):], PLANNED):
        with c.container(border=True):
            st.markdown(f"**{name}** · <span style='color:#6f777a'>planned</span>", unsafe_allow_html=True)
            st.caption(about)
    st.markdown("**Magma to Reaction:** in Magma's results window, pick a step and press **Send to Reaction**. Its "
                "rock goes on Reaction's card as minerals, its melt as a glass of its own oxides. **Save sample** "
                "writes the same thing to a file that Reaction's **Open sample** reads later.")
    st.divider()
    st.caption(f"Protolith {__version__} · alpha · [Report a problem]({FEEDBACK_URL})")


# ---- hand-offs ----------------------------------------------------------------------------------
def _stamp(smp):
    if not smp.written_at:
        smp.written_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return smp


def magma_handoff(state, snap) -> None:
    """Magma's Results window: Save sample and Send to Reaction, for any step of the run."""
    steps = snap["steps"]
    if not steps:
        return
    with st.container(border=True):
        st.markdown("**Pass the result on**")
        if getattr(state, "sample_error", ""):
            st.warning(f"Samples could not be made for this run: {state.sample_error}")
            return
        opts = [str(i) for i in range(len(steps) - 1, -1, -1)]
        labels = {str(i): f"{s['t']:.0f} °C · {s['melt_pct']:.1f}% melt" for i, s in enumerate(steps)}
        if snap.get("source"):
            opts.append("source")
            labels["source"] = "Mantle source (residue and melt)"
        a, b, c = st.columns(3)
        step = a.selectbox("Step", opts, format_func=labels.get, key="smp-step")
        part = b.selectbox("What to take", ["all", "rock"], key="smp-part",
                           format_func=lambda p: {"all": "Melt and rock", "rock": "The rock alone"}[p])
        smp = state.sample(step, part)
        if smp is None:
            st.caption("No sample for that step.")
            return
        smp = _stamp(smp)
        name = f"magma_{smp.conditions['t_c']:.0f}C{'_rock' if smp.melt is None else ''}.sample"
        c.download_button("Save sample", json.dumps(smp.to_dict(), indent=1), file_name=name,
                          mime="application/json", use_container_width=True)
        a, b, c = st.columns(3)
        take = a.selectbox("Put on Reaction's card", list(TAKE), format_func=TAKE.get, key="smp-take")
        grams = b.number_input("Grams per kg of water", min_value=0.001, value=100.0, step=10.0, key="smp-grams")
        if c.button("Send to Reaction", type="primary", use_container_width=True):
            wid, sess = reaction_web.workspace()
            from reaction.app.server import load_sample
            out = load_sample(sess, smp.to_dict(), grams, take)
            for p in out.get("problems") or []:
                st.error(p)
            if not out.get("problems"):
                st.success("On Reaction's card: " + ", ".join(out.get("reactants") or []) + ".")
            for n in out.get("notes") or []:
                st.caption(n)
            st.link_button("Open Reaction", f"./reaction?w={wid}")


def reaction_open_sample(sess) -> None:
    """Reaction's Input window: put a .sample file (from Magma, say) on the card."""
    with st.container(border=True):
        st.markdown("**Open sample**")
        st.caption("A .sample file from Magma: its rock goes on the card as minerals, its melt as a glass of its oxides.")
        a, b = st.columns(2)
        take = a.selectbox("Take", list(TAKE), format_func=TAKE.get, key="open-take")
        grams = b.number_input("Grams per kg of water", min_value=0.001, value=100.0, step=10.0, key="open-grams")
        f = st.file_uploader("Sample file", type=["sample", "json"], key="open-file")
        if f is not None and st.button("Put it on the card"):
            from reaction.app.server import load_sample
            try:
                sample = json.loads(f.getvalue().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                st.error(f"{f.name} is not a sample file (it is not JSON).")
                return
            try:
                out = load_sample(sess, sample, grams, take)
            except SampleError as exc:
                st.error(str(exc))
                return
            for p in out.get("problems") or []:
                st.error(p)
            for n in out.get("notes") or []:
                st.caption(n)
            if not out.get("problems"):
                st.success(f"{f.name} is on the card.")


magma_web.RESULTS_EXTRAS[:] = [magma_handoff]
reaction_web.INPUT_EXTRAS[:] = [reaction_open_sample]
