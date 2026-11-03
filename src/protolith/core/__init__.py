"""Protolith's shared thermodynamic core: what every module computes with, and no user interface.

Today it holds the Holland & Powell system (``protolith.core.hp``): the end-member dataset, the solid,
liquid and fluid solution models, and the Gibbs energy minimizer.  Magma runs on it; Reaction, and later
Metamorphism and Surface, move onto it one at a time (see the plan linked from the README).

Rules for this package: no module imports from here into the core (it never imports ``magma``,
``reaction`` or ``protolith.app``), every parameter is cited where it is defined, and the code is our own,
written from the papers' equations.
"""
