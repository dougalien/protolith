"""Protolith: one geochemical calculator for melting and crystallization (Magma), water-rock reaction
(Reaction), and later metamorphism and surface processes, on shared thermodynamic data.

This package holds what the modules share: the thermodynamic core (``core``, the Holland & Powell
dataset, solution models and solver), the sample file (``sample``), the links from Magma results
(``magma_link``) to Reaction's reactant card (``reaction_link``), and the shell (``app``).
"""
__version__ = "0.0.1"
