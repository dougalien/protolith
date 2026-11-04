"""Protolith on Streamlit Community Cloud: ``streamlit run streamlit_app.py``.

Protolith is the metamorphism app: an Input window and a Results window, as in Protolith.exe, sharing
one visitor's run through the private ``?w=`` id in the address.
"""
import os
import sys
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")          # the solver's matrices are small; one numpy thread is fastest
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from metamorphism.web.app import input_page, results_page  # noqa: E402

page = st.navigation([st.Page(input_page, title="Input", url_path="input", default=True),
                      st.Page(results_page, title="Results", url_path="results")], position="hidden")
page.run()
