"""Shared enemy perception: can this pursuer actually SEE the player?

Before this module, "seeing" was a bare distance check (`d < range and not
hidden`) -- which let cultists see through walls, see behind their own
heads, and treated any hide spot as total invisibility. Perception now
gates on three things in sequence, cheapest first:

  1. RANGE   -- within the looker's sight radius.
  2. CONE    -- the player is within the looker's forward facing cone
               (dot-product against `facing`); you can slip behind a
               cultist that isn't looking your way.
  3. SIGHT   -- an unobstructed sight-line (scene.sight_blocked raycast);
               a wall or a sorting-table between you breaks it.

Cover (`player.hidden`) no longer hard-zeroes perception. Instead it
shrinks the effective sight range hard (HIDE_RANGE_MULT) and narrows the
cone, so a cultist far away or not looking won't spot a hidden player --
but one standing right over your hiding spot, staring, still can. Cover
breaks the *lock*, it is not an invisibility toggle. The caller (the cult
state machine) turns a broken sight-line into a SEARCH at the last-seen
position, which is the actual cat-and-mouse.
"""
import math

# Forward cone: the player must be within this half-angle of the looker's
# facing to be seen. cos(55 deg) ~= 0.574 -> a 110-degree total cone.
SIGHT_CONE_DOT = 0.574
# While the player is hidden (in cover), perception is throttled rather
# than disabled: the sight range is multiplied down so only a near,
# facing, line-of-sight looker can pin them.
# The multiplier depends on the KIND of cover (player.hidden's value), so
# the spot types are no longer cosmetic:
#   under / in -- full-body concealment ("hold your breath": tucked under a
#                 cot, inside a crate). Hardest to spot -- a looker must be
#                 almost on top of you. The trade is commitment: it's a
#                 hold, not a peek.
#   behind / corn -- partial cover you crouch behind / in. Looser: you're
#                 leaning on the geometry and the looker's facing as much as
#                 the cover itself.
# ~0.16 * 180px ~= 29px (a tile) for under/in; ~0.30 * 180 ~= 54px for
# behind/corn. Default (unknown kind) takes the looser value.
HIDE_RANGE_MULT = {
    "under": 0.16,
    "in":    0.16,
    "behind": 0.30,
    "corn":   0.30,
}
HIDE_RANGE_MULT_DEFAULT = 0.30
# Hidden players also demand a tighter cone (the looker must be staring
# more directly at the spot). Full-body cover tightens it further.
HIDE_CONE_DOT = {
    "under": 0.90,
    "in":    0.90,
    "behind": 0.77,
    "corn":   0.77,
}
HIDE_CONE_DOT_DEFAULT = 0.77


def perceives_player(looker, player, scene, sight_range):
    """True if `looker` can see `player` right now.

    `sight_range` is the looker's base sight radius in px (aggro /
    gaze_range). Range, then facing cone, then line-of-sight. Cover
    throttles range + cone instead of granting blanket invisibility.
    Wrap-aware via the scene's fold deltas.
    """
    dx = scene.world_dx(looker.x, player.x)
    dy = scene.world_dy(looker.y, player.y)
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return True                      # on top of each other

    hide_kind = getattr(player, "hidden", None)
    hidden = hide_kind is not None
    rng = sight_range
    if hidden:
        rng *= HIDE_RANGE_MULT.get(hide_kind, HIDE_RANGE_MULT_DEFAULT)
    if d > rng:
        return False

    # Facing cone. looker.facing points where the looker is looking;
    # (dx,dy)/d points looker->player. Dot >= threshold => in front.
    fx, fy = getattr(looker, "facing", (0.0, 1.0))
    fmag = math.hypot(fx, fy) or 1.0
    cone = (HIDE_CONE_DOT.get(hide_kind, HIDE_CONE_DOT_DEFAULT)
            if hidden else SIGHT_CONE_DOT)
    if ((fx * dx + fy * dy) / (fmag * d)) < cone:
        return False

    # Line of sight: a wall / table / solid prop between breaks it.
    if scene.sight_blocked(looker.x, looker.y, player.x, player.y):
        return False
    return True
