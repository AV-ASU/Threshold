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

import pygame

from systems.config import (SUS_NEAR, SUS_CONE_HALF, SUS_CONE_FEATHER,
                            SUS_CONCEAL_CORN, SUS_FILL_RATE, SUS_DECAY,
                            SUS_SCORE_HOLD, SUS_SWEEP_RADIUS,
                            SUS_CHECK_DIST, SUS_CHECK_PAUSE,
                            NOISE_HEAR_MIN, NOISE_FRESH,
                            NOISE_REACT_PAUSE, NOISE_SEARCH_PULL)

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
    keyed = [(scene.world_dist(cx, cy, hx, hy), hx, hy, kind)
             for hx, hy, kind in spots if kind in ENCLOSED_KINDS]
    keyed = [k for k in keyed if k[0] <= radius]
    keyed.sort()
    return [(hx, hy, kind) for _d, hx, hy, kind in keyed]


# ---- The shared suspicion/search machinery -------------------------------
# Both cult machines (entities/npc.py surface chasers, entities/enemy.py
# underground cultists) tick these, so fill/decay, the search budget, and
# the hide CHECK can never drift apart between the two files.

def update_suspicion(actor, score, dt):
    """Fill/decay the actor's suspicion bar from this tick's score, and
    return it. Scores below SUS_SCORE_HOLD neither fill nor hold: a
    glimpse too thin to sustain a chase must not be able to pin the bar
    at 1.0, or the machine flip-flops chase->search every frame at the
    sight fringe and spams the lock/lose stings."""
    sus = getattr(actor, "_suspicion", 0.0)
    if score >= SUS_SCORE_HOLD:
        sus = min(1.0, sus + score * SUS_FILL_RATE * dt)
    else:
        sus = max(0.0, sus - SUS_DECAY * dt)
    actor._suspicion = sus
    return sus


def enter_search(actor, scene):
    """Drop the actor into SEARCH at its last-seen point. The budget
    scales with the sweep: walking to and looking into each enclosed
    hide takes real time, and a flat window abandoned sweeps a few
    steps short of an occupied hide."""
    actor._cult_state = "search"
    actor._just_lost = True
    if actor._last_seen_pos is not None:
        lx, ly = actor._last_seen_pos
        actor._sweep_list = sweep_points(scene, lx, ly, SUS_SWEEP_RADIUS)
    else:
        actor._sweep_list = []
    actor._sweep_i = 0
    actor._check_t = 0.0
    actor._cult_state_t = 6.0 + 3.0 * len(actor._sweep_list)
    # A sighting-born search outranks ordinary noise: only something at
    # NOISE_SEARCH_PULL or louder (a shot, the burst, the bell) diverts.
    actor._noise_loud = NOISE_SEARCH_PULL


def sweep_check(actor, scene, player, dt, step_fn):
    """The SEARCH sweep tick once the actor stands at last-seen: walk
    to each enclosed hide and CHECK it (an occupied one is handed to
    the Game's struggle via scene._hide_check). Returns True while the
    sweep owns the actor's movement this tick; False once the list is
    spent (the caller falls back to its mill)."""
    sweep = getattr(actor, "_sweep_list", None) or []
    i = getattr(actor, "_sweep_i", 0)
    if i >= len(sweep):
        return False
    hx, hy, _kind = sweep[i]
    d_h = scene.world_dist(actor.x, actor.y, hx, hy)
    if d_h > SUS_CHECK_DIST:
        actor._check_t = 0.0
        step_fn(hx, hy)
        return True
    fdx = scene.world_dx(actor.x, hx)
    fdy = scene.world_dy(actor.y, hy)
    fm = math.hypot(fdx, fdy) or 1.0
    actor.facing = (fdx / fm, fdy / fm)
    actor._check_t = getattr(actor, "_check_t", 0.0) + dt
    if actor._check_t >= SUS_CHECK_PAUSE:
        if (is_enclosed(player)
                and scene.world_dist(player.x, player.y, hx, hy) < 24):
            scene._hide_check = (actor, hx, hy)
        actor._sweep_i = i + 1
        actor._check_t = 0.0
    return True


def hear_noise(actor, scene, hearing_range=180.0):
    """One shared ear for both cult machines: scan this frame's noise
    events (Scene.emit_noise) and re-target the actor onto the best
    audible one. SCOUTS turn on anything fresh, in range, at or over
    NOISE_HEAR_MIN. SEARCHERS/INVESTIGATORS already own a target and are
    only PULLED OFF it by something strictly louder than what they hold
    (actor._noise_loud; a sighting-born search holds NOISE_SEARCH_PULL,
    so only a gunshot/burst/bell diverts it). CHASE never diverts.
    Set-piece kneelers (lock_facing / aggro 0) are deaf: their wake is
    scripted. Returns True if the actor re-targeted this tick."""
    st = getattr(actor, "_cult_state", "scout")
    if st == "chase":
        return False
    if getattr(actor, "lock_facing", False) or getattr(actor, "aggro", 1) == 0:
        return False
    events = getattr(scene, "_noise_events", None)
    if not events:
        return False
    now = pygame.time.get_ticks() / 1000.0
    held = 0.0
    if st in ("search", "investigate"):
        held = getattr(actor, "_noise_loud", NOISE_SEARCH_PULL)
    best = None
    for (ex, ey, loud, et, _kind) in events:
        if now - et >= NOISE_FRESH or loud < NOISE_HEAR_MIN:
            continue
        if loud <= held:
            continue
        if scene.world_dist(actor.x, actor.y, ex, ey) > hearing_range:
            continue
        if best is None or loud > best[2]:
            best = (ex, ey, loud)
    if best is None:
        return False
    ex, ey, loud = best
    actor._cult_state = "investigate"
    actor._cult_state_t = 4.0
    actor._last_seen_pos = (ex, ey)
    actor._noise_loud = loud
    actor._react_t = NOISE_REACT_PAUSE
    actor.move_target = None
    if hasattr(actor, "_scout_target"):
        actor._scout_target = None
    return True


def react_hold(actor, scene, dt):
    """The turn-first telegraph: for NOISE_REACT_PAUSE after hearing
    something, the actor faces the source and holds still before it
    walks. Returns True while the hold owns this tick's movement."""
    t = getattr(actor, "_react_t", 0.0)
    if t <= 0.0:
        return False
    actor._react_t = t - dt
    pos = getattr(actor, "_last_seen_pos", None)
    if pos is not None:
        fdx = scene.world_dx(actor.x, pos[0])
        fdy = scene.world_dy(actor.y, pos[1])
        fm = math.hypot(fdx, fdy) or 1.0
        actor.facing = (fdx / fm, fdy / fm)
    return True


def grab_allowed(player, chasing):
    """The one contact-grab gate under the cover rules: open ground
    always grabs; CONCEALMENT (corn, and any future leaky kind) only
    yields to a pursuer that has LOCKED (cover is not armor); an
    enclosed hide never grabs directly (the struggle owns it)."""
    hidden = getattr(player, "hidden", None)
    if hidden is None:
        return True
    return bool(chasing) and not is_enclosed(player)
