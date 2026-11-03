"""Magma's Holland & Powell engine: the adapter (``engine``) that runs cooling and melting paths on the
shared core in ``protolith.core.hp``, beside the MELTS engine in ``magma.thermo``.

The dataset, solution models and solver themselves live in the core, so other modules use the same
Gibbs energies.  See ``protolith.core.hp`` for their sources.
"""
