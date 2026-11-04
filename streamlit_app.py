"""Protolith on Streamlit Community Cloud: ``streamlit run streamlit_app.py``.

The home page, and each module's two windows (Input and Results) as in Protolith.exe, sharing one
visitor's work through the private ``?w=`` id in the address.
"""
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")          # Magma's matrices are small; one numpy thread is fastest
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

import magma.web.app as magma_web  # noqa: E402
import reaction.web.app as reaction_web  # noqa: E402
from protolith.web.app import home_page  # noqa: E402

page = st.navigation([
    st.Page(home_page, title="Protolith", url_path="home", default=True),
    st.Page(magma_web.input_page, title="Magma", url_path="magma"),
    st.Page(magma_web.results_page, title="Magma results", url_path="magma-results"),
    st.Page(reaction_web.input_page, title="Reaction", url_path="reaction"),
    st.Page(reaction_web.results_page, title="Reaction results", url_path="reaction-results"),
    st.Page(reaction_web.sources_page, title="Reaction sources", url_path="sources"),
], position="hidden")
page.run()
