"""Protolith's shared thermodynamic core: what every module computes with, and no user interface.

It holds the Holland & Powell system (``protolith.core.hp``): the end-member datasets, the solid,
liquid and fluid solution models, and the Gibbs energy minimizer.

The core imports nothing from the modules that use it, every parameter is cited where it is defined,
and the code is written from the papers' equations.
"""
