"""Metamorphism: the stable mineral assemblage of a rock at a given temperature and pressure, one point
at a time or over a T-P grid (a pseudosection), on Protolith's Holland & Powell core.

- ``bulk``: oxide wt% to the core's components, with water fixed by the rock or kept in excess.
- ``point``: one equilibrium, reported as minerals with their modes and compositions.
- ``pseudosection``: a T-P grid of points, grouped into assemblage fields with their boundaries.

The bulk can come from a ``.sample`` file and any point can go back out as one
(``protolith.metamorphism_link``).  This package imports the core only, never Magma or Reaction.
"""
__version__ = "0.1.0"
