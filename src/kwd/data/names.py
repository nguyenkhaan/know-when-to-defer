"""Synthetic display names and categories for LMRC stops, whose ids are opaque (spec 05 §4.8).

Categories are deliberately uneven. Spec 08 only allows an indirect reference such as "the
hospital" when exactly one hospital remains, so the rare categories must stay rare. Prefixes are
shared across names ("Oak Clinic", "Oak Pharmacy") to keep name confusions realistic.
"""

import random
from collections.abc import Collection

DEPOT_NAME = "Depot"
DEPOT_CATEGORY = "depot"

CATEGORY_WEIGHTS = {
    "residence": 0.70,
    "office": 0.09,
    "shop": 0.09,
    "restaurant": 0.06,
    "hospital": 0.01,
    "school": 0.01,
    "pharmacy": 0.01,
    "clinic": 0.01,
    "gym": 0.01,
    "warehouse": 0.01,
}

SUFFIXES = {
    "residence": ("Lane", "Court", "Way"),
    "office": ("Office", "Tower"),
    "shop": ("Shop", "Store", "Market"),
    "restaurant": ("Cafe", "Grill", "Diner"),
    "hospital": ("Hospital",),
    "school": ("School",),
    "pharmacy": ("Pharmacy",),
    "clinic": ("Clinic",),
    "gym": ("Gym",),
    "warehouse": ("Warehouse",),
}

PREFIXES = (
    "Alder",
    "Ash",
    "Aspen",
    "Beech",
    "Birch",
    "Cedar",
    "Chestnut",
    "Cypress",
    "Elm",
    "Fern",
    "Hazel",
    "Heather",
    "Hickory",
    "Holly",
    "Ivy",
    "Juniper",
    "Laurel",
    "Linden",
    "Maple",
    "Oak",
    "Pine",
    "Poplar",
    "Spruce",
    "Willow",
)


def normalize_name(name: str) -> str:
    """Canonical form for comparing stop names: casefolded, whitespace collapsed."""
    return " ".join(name.casefold().split())


def assign_names(stop_ids: Collection[str], seed: int) -> dict[str, tuple[str, str]]:
    """Return stop id -> (name, category) for the delivery stops of one route.

    Names are unique after `normalize_name`, also against the depot. Stops are visited in sorted
    order, so the result depends only on the set of ids and the seed.
    """
    rng = random.Random(seed)
    categories = list(CATEGORY_WEIGHTS)
    weights = list(CATEGORY_WEIGHTS.values())
    used = {normalize_name(DEPOT_NAME)}
    named = {}
    for stop_id in sorted(stop_ids):
        category = rng.choices(categories, weights)[0]
        base = f"{rng.choice(PREFIXES)} {rng.choice(SUFFIXES[category])}"
        # Residences always carry a house number; other names only when already taken.
        number = rng.randint(2, 199) if category == "residence" else 1
        name = base if number == 1 else f"{base} {number}"
        while normalize_name(name) in used:
            number += 1
            name = f"{base} {number}"
        used.add(normalize_name(name))
        named[stop_id] = (name, category)
    return named
