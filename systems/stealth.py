"""Graded detection for the cult AI (STEALTH_REWORK.md, Pillar 1).

One source for the per-tick detection SCORE both cult machines read --
entities/npc.py (surface chasers) and entities/enemy.py (underground
cultists) mirror each other, so the scoring math lives here, pure and
headless-testable.

    score = los_clear * distance_falloff * facing_cone * concealment

- los_clear: the existing wall/solid-prop sight march (Scene.
  clear_sight_line). Corn does NOT block it -- corn is concealment,
  not architecture.
- distance_falloff: 1 up close, 0 at the enemy's gaze/aggro range.
- facing_cone: the enemy has eyes, not radar -- a soft cone around its
  facing (SUS_CONE_HALF, feathered). Inside SUS_NEAR the cone stops
  mattering: something crouched against your legs is felt, whichever
  way you face. This is what kills the sit-in-cover-beside-a-cultist
  exploit.
- concealment: 1.0 in the open; SUS_CONCEAL_CORN in corn (leaky, so a
  NEAR cultist still fills against a hidden player while a far one
  reads almost nothing); 0.0 in an enclosed hide ('under'/'in' -- the
  hard break; the CHECK is that cover's threat, not the gaze).

Suspicion itself (the [0,1] accumulator, fill/decay, state promotion)
stays in the two cult ticks; they call score() and share the same
constants (systems/config.py SUS_*).

Apex pursuers (_force_chase: the King via _yk_update, the hollow
Sheriff) never consult any of this.
"""
import math

from systems.config import (SUS_NEAR, SUS_CONE_HALF, SUS_CONE_FEATHER,
                            SUS_CONCEAL_CORN)

# The two enclosed hide kinds ('behind' was removed with the old model;
# kept out on purpose -- see CLAUDE.md).
ENCLOSED_KINDS = ("under", "in")


def concealment_factor(player):
    """How much the player's current cover scales the detection score.
    1.0 in the open, SUS_CONCEAL_CORN in corn, 0.0 in an enclosed hide."""
    hidden = getattr(player, "hidden", None)
    if hidden is None:
        return 1.0
    if hidden == "corn":
        return SUS_CONCEAL_CORN
    if hidden in ENCLOSED_KINDS:
        return 0.0
    return SUS_CONCEAL_CORN      # any future cover kind defaults leaky


def is_enclosed(player):
    """True while the player is inside a rooted enclosed hide."""
    return getattr(player, "hidden", None) in ENCLOSED_KINDS


def _facing_factor(dx, dy, d, facing):
    """Soft cone membership of the player (at enemy-relative dx, dy,
    distance d) in the enemy's facing cone. 1 inside, 0 outside, eased
    across SUS_CONE_FEATHER at the lip. Inside SUS_NEAR it is 1
    regardless of facing."""
    if d <= SUS_NEAR:
        return 1.0
    fx, fy = facing
    fmag = math.hypot(fx, fy)
    if fmag < 1e-6:
        return 1.0               # a facing-less watcher sees all ways
    heading = math.atan2(fy, fx)
    off = math.atan2(dy, dx) - heading
    off = abs((off + math.pi) % (2 * math.pi) - math.pi)
    if off <= SUS_CONE_HALF:
        return 1.0
    if off >= SUS_CONE_HALF + SUS_CONE_FEATHER:
        return 0.0
    return (SUS_CONE_HALF + SUS_CONE_FEATHER - off) / SUS_CONE_FEATHER


def detection_score(scene, ex, ey, facing, player, sight_range,
                    ignore_conceal=False):
    """The per-tick detection score in [0, 1] for one enemy eye at
    (ex, ey) with `facing`, against the live player. Wrap-aware via the
    scene's world_dx/world_dy. Cheap gates first; the sight march is
    only paid when everything else passes. `ignore_conceal` is the
    respects_hide=False escape hatch: cover scales nothing for an eye
    that does not respect it (walls still occlude)."""
    conceal = 1.0 if ignore_conceal else concealment_factor(player)
    if conceal <= 0.0:
        return 0.0
    dx = scene.world_dx(ex, player.x)
    dy = scene.world_dy(ey, player.y)
    d = math.hypot(dx, dy)
    if d >= sight_range:
        return 0.0
    fall = 1.0 - d / sight_range
    face = _facing_factor(dx, dy, d, facing)
    if face <= 0.0:
        return 0.0
    if not scene.clear_sight_line(ex, ey, player.x, player.y):
        return 0.0
    return fall * face * conceal


def sweep_points(scene, cx, cy, radius):
    """The enclosed hide spots within `radius` of (cx, cy) -- what a
    SEARCHING cultist walks to and checks, nearest first. Returns
    [(x, y, kind), ...]."""
    spots = getattr(scene, "hide_spots", None) or []
    out = [(hx, hy, kind) for hx, hy, kind in spots
           if kind in ENCLOSED_KINDS
           and scene.world_dist(cx, cy, hx, hy) <= radius]
    out.sort(key=lambda s: scene.world_dist(cx, cy, s[0], s[1]))
    return out
