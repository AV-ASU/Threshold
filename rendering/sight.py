"""Line-of-sight / blind-spot sight model (DESIGN.md §10) — PROTOTYPE.

The "what the player can currently SEE" buffer that the tilt redesign exists
to pay off. A forward sight CONE from the player, keyed to the look heading
(where the head/eyes point), clipped by walls via a coarse ray march. This is
the gate the blind-spot horror hangs on: terrain reveals on a peek, but
NPCs / items / map-changes stay hidden until they actually fall inside the
cone AND are not behind a wall — so the world is free to rearrange in the
blind spot (SCP-173 / Weeping-Angel dread).

Pure math: no pygame, no assets. Headless-testable — feed positions + a
heading, read back a 0..1 visibility factor (0 = unseen, 1 = plainly in
view). The factor is soft at the cone edges so a thing eases into view rather
than popping; callers can threshold it for a hard seen/unseen decision or use
it directly as an alpha.

Conventions match the rest of the game: world angle in radians via
atan2(dy, dx), x -> screen right, y -> screen down. The cone is centred on the
look heading (LookController.aim — the head, not the body), half-angle
SIGHT_HALF, out to SIGHT_RANGE world px, with an always-seen SIGHT_NEAR bubble
right around the player (you feel what is on top of you regardless of facing).
"""
import math

# Tuning. These are the design knobs the look/feel hangs on (see DESIGN.md §10
# Phase 4). Kept here so the preview tool and the live game read one source.
SIGHT_HALF = math.radians(74)      # cone half-angle (~148 deg total field)
SIGHT_RANGE = 360.0                # px; how far the player can make things out
SIGHT_NEAR = 40.0                  # px; always-seen bubble around the player
SIGHT_ANG_FEATHER = math.radians(16)  # soft angular edge (eases in, no pop)
SIGHT_RANGE_FEATHER = 56.0         # px; soft far-edge fade band
# Eye height (world z, px) used by the ground-crest LOS term: the sight ray
# runs at this height above the ground under the viewer/target, so a hill that
# rises higher than the ray between them occludes what is beyond it -- the same
# dread primitive as a wall (DESIGN.md §10). Only consulted when a scene
# authors a heightfield; a flat scene passes ground=None and this is inert.
SIGHT_EYE_H = 22.0
LOS_STEP = 7.0                     # px ray-march step for the wall check (AI)
# The RENDER gate marches LOS for every visible actor/deco EVERY frame -- the
# dominant per-frame sight cost. Walls are a full TILE (32px), so a coarser
# step still lands inside every wall (no see-through) while ~halving the march
# iterations. Kept separate from LOS_STEP so the King's AI sight (king_roam)
# stays at the fine 7px step -- this only loosens the draw gate.
SIGHT_RENDER_STEP = 14.0


def _wrap(a):
    """Angle to (-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


def cone_factor(px, py, heading, tx, ty):
    """Angular + range membership of target (tx, ty) in the sight cone from
    (px, py) facing `heading`, IGNORING walls. 0 = outside, 1 = plainly in.

    Soft at the angular and far-range edges so things fade rather than pop.
    Inside SIGHT_NEAR the factor is 1 regardless of angle."""
    dx = tx - px
    dy = ty - py
    d = math.hypot(dx, dy)
    if d <= SIGHT_NEAR:
        return 1.0
    if d > SIGHT_RANGE:
        return 0.0
    # angular term, feathered at the cone lip
    off = abs(_wrap(math.atan2(dy, dx) - heading))
    if off > SIGHT_HALF + SIGHT_ANG_FEATHER:
        return 0.0
    ang_f = 1.0
    if off > SIGHT_HALF:
        ang_f = (SIGHT_HALF + SIGHT_ANG_FEATHER - off) / SIGHT_ANG_FEATHER
    # range term, feathered at the far lip
    range_f = 1.0
    if d > SIGHT_RANGE - SIGHT_RANGE_FEATHER:
        range_f = (SIGHT_RANGE - d) / SIGHT_RANGE_FEATHER
    return max(0.0, min(1.0, ang_f * range_f))


def los_clear(px, py, tx, ty, blocks, step=LOS_STEP, ground=None,
              eye=SIGHT_EYE_H):
    """True if no wall sits between (px, py) and (tx, ty). `blocks(x, y)` is a
    predicate returning True where sight is occluded (a wall tile). Coarse ray
    march; the endpoints themselves are not tested (the target may BE a wall-
    adjacent thing and the player may stand on an open tile by a wall).

    `ground(x, y)` (optional) samples the terrain height (world z) under a
    point. When given, a ground CREST between the eye and the target also
    occludes: the sight ray runs from `ground(px,py)+eye` to `ground(tx,ty)+eye`
    and any intermediate ground sample rising above it blocks the line, exactly
    like a wall. Default None keeps the pure wall behaviour (byte-identical for
    every flat scene) -- this term only ADDS occlusion, never removes it."""
    dx = tx - px
    dy = ty - py
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return True
    n = int(d / step)
    ez = tz = 0.0
    if ground is not None:
        ez = ground(px, py) + eye
        tz = ground(tx, ty) + eye
    for i in range(1, n + 1):
        f = i / (n + 1)
        sx, sy = px + dx * f, py + dy * f
        if blocks(sx, sy):
            return False
        if ground is not None and ground(sx, sy) > ez + (tz - ez) * f:
            return False
    return True


def visible_factor(px, py, heading, tx, ty, blocks=None, step=LOS_STEP,
                   ground=None, eye=SIGHT_EYE_H):
    """Combined sight: the cone factor, gated to 0 if a wall occludes the
    target. `blocks` may be None (open arena — cone only). Returns 0..1.

    `step` is the LOS ray-march granularity; callers in the per-frame draw
    gate pass the coarser SIGHT_RENDER_STEP. The cheap cone test runs first
    and short-circuits before any wall march.

    `ground` (optional) adds the terrain-crest occlusion term (see los_clear):
    a hill you can't see over hides what is beyond it. None = flat, no-op."""
    cf = cone_factor(px, py, heading, tx, ty)
    if cf <= 0.0 or blocks is None:
        return cf
    return cf if los_clear(px, py, tx, ty, blocks, step=step,
                           ground=ground, eye=eye) else 0.0


