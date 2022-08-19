"""
This local disnake leveling system uses the same levels and XP needed values as MEE6.
All credit goes towards the MEE6 developers for providing the "LEVELS_AND_XP" documentation.

MEE6 documentation can be found here: https://github.com/Mee6/Mee6-documentation
"""

from collections import namedtuple
from typing import NamedTuple

__all__ = ("_next_level_details", "_find_level")

from utils.CONSTANTS import LEVELS_AND_XP


def _next_level_details(current_level: int) -> NamedTuple:
    """Returns a `namedtuple`

    Attributes
    ----------
    - level (:class:`int`)
    - xp_needed (:class:`int`)

        .. changes
            v0.0.2
                Changed return type to a namedtuple instead of tuple
    """
    temp = current_level + 1
    if temp > 100:
        temp = 100
    key = str(temp)
    val = LEVELS_AND_XP[key]
    Details = namedtuple("Details", ["level", "xp_needed"])
    return Details(level=int(key), xp_needed=val)


def _find_level(current_total_xp: int) -> int:
    """Return the members current level based on their total XP"""
    if current_total_xp in LEVELS_AND_XP.values():
        for level, xp_needed in LEVELS_AND_XP.items():
            if current_total_xp == xp_needed:
                return int(level)
    else:
        for level, xp_needed in LEVELS_AND_XP.items():
            if 0 <= current_total_xp <= xp_needed:
                level = int(level)
                level -= 1
                if level < 0:
                    level = 0
                return level
