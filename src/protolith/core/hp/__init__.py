"""The Holland & Powell thermodynamic system, shared by every Protolith module.

- ``endmembers``: G(T, P) of each end member in the ds6.36 and ds6.2 datasets (``protolith/core/data``).
- ``solutions``: the site-fraction solution models (olivine, feldspar, pyroxenes, spinel, garnet, melt,
  fluid and the rest of the igneous set).
- ``solutions_mp``: the metapelite set of White et al. (2014) on ds6.2, with MnO (ported from MAGEMin by
  scripts/port_magemin_mp.py).
- ``minimize``: the equilibrium solver (linear programming with column generation, then a Newton polish),
  with an optional oxygen buffer and warm starts.

Parameter values from the Holland & Powell end-member dataset and the igneous solution models
(Holland and Powell 2011; Green et al. 2016; Holland, Green and Powell 2018), numbers as distributed in
MAGEMin (Riel et al. 2022).  The code is written from the papers' equations.
"""
