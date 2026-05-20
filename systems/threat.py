"""Threat layer.

THRESHOLD's threat fiction has three concentric rings:

  ring 1 -- WATCHERS    (almost-visible figures at the camera edges)
  ring 2 -- PURSUER     (audio-only pressure that ramps over time)
  ring 3 -- PATROLS     (real NPCs that can SEE, CHASE, and CATCH)

This module is intentionally thin -- the live tick logic still
lives on the Game class (`_tick_watchers`, `_tick_pursuer`,
`_tick_sheriff`) so the existing wiring keeps working. The job
of `systems/threat.py` is to:

  * Document the architecture in one place.
  * Expose constants other modules can import without dragging
    in the full Game class.
  * Provide expansion hooks so new threat types can be added
    without rewriting Game.

Adding a new threat:

  1. Append a patrol dict to `Game._patrols` in `__init__` with a
     unique `tag`, `kind` (sprite kind in rendering/sprites.py),
     `min_prox` (proximity threshold to activate), `scene` (always
     `None` at init -- the system rolls one when the patrol turns
     on), and `t` (initial countdown until first spawn).

  2. Add the `tag` to the reset map in `Game._reset_run_state`.

  3. If the new threat reacts to the flashlight, hide spots, the
     axe, or any other tool, gate the reaction inside
     `Game._tick_sheriff` (search for `patrol_hunter`).

  4. Add a capture line for the new threat in
     `Game._trigger_capture` (the dict at the top of that method).

The catch consequence is graduated by Pursuer proximity: at
`PROXIMITY_CLOSURE` (0.85+) any catch is the closure ending; below
that, a catch is a setback (wake-in-bedroom + day +1 + proximity
ratchets up by `CAPTURE_PROX_PUSH`).

The flashlight does not banish the Hunter at any tier. The cone
affects watchers: it banishes them outright below mid proximity,
pauses them in the mid band, and is inert at apex (the Yellow
King is past being held off by a 9V).
"""

# Tunables. Pulled out so future content can adjust the threat
# curve without grepping for magic numbers in game.py.
PROXIMITY_CLOSURE = 0.85       # catches above this end the run
CAPTURE_PROX_PUSH = 0.25       # how much a non-ending catch tightens the line
HUNTER_MIN_PROX = 0.30         # proximity at which the Hunter starts patrolling


# Proximity tier names used for content gating + dialogue
# escalation. Three buckets so writers don't have to think about
# float thresholds in every dialog beat.
PROX_TIER_LOW = "low"      # < 0.33
PROX_TIER_MID = "mid"      # < 0.66
PROX_TIER_HIGH = "high"    # >= 0.66


def proximity_tier(p):
    """Return one of PROX_TIER_LOW / MID / HIGH. Used by
    scenes/dialogue.py:escalate to pick which version of an NPC's
    line to show. Single source of truth for the bucketing."""
    if p < 0.33:
        return PROX_TIER_LOW
    if p < 0.66:
        return PROX_TIER_MID
    return PROX_TIER_HIGH
