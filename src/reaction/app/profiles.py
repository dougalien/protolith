"""Which of Reaction's starting cards and examples a window offers, and what the window is called.

Reaction alone offers everything ("all").  Inside Protolith it runs twice, on the same engine code and
data: as **Reaction**, the hydrothermal module (hot water and rock: sea-floor alteration, boiling, vents,
serpentinization), and as **Weathering**, the low-temperature surface module (salt lakes, streams and soils,
calcite and forams dissolving).  Douglas asked for this split on 2026-11-03.  A profile changes only what
the window offers and its name; every card can still be edited into any run the engine can do.
"""
from __future__ import annotations

from dataclasses import dataclass

from .scenario import EXAMPLES, STARTING_CARDS


@dataclass(frozen=True)
class Profile:
    key: str
    name: str                     # the window's title
    tagline: str
    mark: str                     # the icon in static/
    cards: tuple                  # STARTING_CARDS keys, in order
    examples: tuple               # EXAMPLES keys, in order
    default: str                  # the starting card of a fresh session

    def starting_cards(self):
        return [STARTING_CARDS[k] for k in self.cards]

    def example_list(self):
        return [EXAMPLES[k] for k in self.examples]


PROFILES = {p.key: p for p in (
    Profile("all", "Reaction", "water and rock", "reaction_mark.svg", tuple(STARTING_CARDS), tuple(EXAMPLES),
            "seawater"),
    Profile("hydrothermal", "Reaction", "hot water and rock", "reaction_mark.svg",
            ("seawater", "freshwater", "hydrothermal"),
            ("solid_solutions", "serpentinization", "boiling", "phase_separation", "vent_energy"), "seawater"),
    Profile("surface", "Weathering", "water and rock at the surface", "weathering_mark.svg",
            ("brine", "stream"),
            ("kinetics", "forams", "weathering", "lake", "clays"), "brine"),
)}


def profile(key: str | None) -> Profile:
    try:
        return PROFILES[key or "all"]
    except KeyError:
        raise ValueError(f"unknown profile {key!r}; known: {', '.join(PROFILES)}") from None
