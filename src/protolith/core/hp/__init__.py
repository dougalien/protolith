"""The Holland & Powell thermodynamic system, shared by every Protolith module.

- ``endmembers``: G(T, P) of each end member in the ds6.36 dataset (``protolith/core/data/hp_ds636.tsv``).
- ``solutions``: the site-fraction solution models (olivine, feldspar, pyroxenes, spinel, garnet, melt,
  fluid and the rest of the igneous set).
- ``minimize``: the equilibrium solver (linear programming with column generation, then a Newton polish),
  with an optional oxygen buffer and warm starts.

Parameter values from the Holland & Powell end-member dataset and the igneous solution models
(Holland and Powell 2011; Green et al. 2016; Holland, Green and Powell 2018), numbers as distributed in
MAGEMin, taken with Douglas's approval (2026-11-02).  The code is our own, written from the papers' equations.

Moved here from Magma's ``magma/hp`` on 2026-11-03; Magma's adapter (``magma.hp.engine``) now calls it.
"""
