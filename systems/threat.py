"""Threat layer.

THRESHOLD's threat is a single meter: VISIBILITY [0, 1] -- how
visible the player is to the King in Yellow right now. It is driven
by three things, all converging on the one number:

  * WATCHERS -- a cultist's curse (landed by lingering in its
                sightline) is a permanent status effect that spawns
                Watcher figures onto the player; each one nudges
                visibility up. This is the thing that raises it.
  * HIDING   -- the lever that pulls visibility back down. Cover is
                how the player survives a curse they cannot undo.
  * THE KING -- the lethal apex. The instant visibility hits 1.0 he
                materialises at the doorway the player entered from
                and hunts relentlessly; reaching the player is the
                closure ending. Claw visibility below 0.90 -- by
                hiding -- and he dissolves.

The live tick logic lives on the Game class (`_tick_visibility`,
`_tick_king`) so the wiring stays in one place. This module
documents the model and exposes the tier constants other modules
import without dragging in the full Game class.

NOTE: the Watcher / curse / cultist *input* side is being built in a
following pass. `_tick_visibility` currently carries a placeholder
raiser so the King is reachable and the lethal core is playable.
"""


# Visibility tier names used for content gating + dialogue
# escalation. Three buckets so writers don't have to think about
# float thresholds in every dialog beat.
PROX_TIER_LOW = "low"      # < 0.33
PROX_TIER_MID = "mid"      # < 0.66
PROX_TIER_HIGH = "high"    # >= 0.66


def proximity_tier(p):
    """Return one of PROX_TIER_LOW / MID / HIGH for a visibility
    value. Used by scenes/dialogue.py:escalate to pick which version
    of an NPC's line to show. Single source of truth for bucketing."""
    if p < 0.33:
        return PROX_TIER_LOW
    if p < 0.66:
        return PROX_TIER_MID
    return PROX_TIER_HIGH
