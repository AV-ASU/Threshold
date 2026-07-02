"""Stealth-rework guard (STEALTH_REWORK.md): graded suspicion, cover
classes, the hide-check struggle.

Locks the rules the rework replaced binary invisibility with:

  1. detection is GRADED -- suspicion climbs in the open, the NOTICE
     tell fires before the lock, and only a full bar locks the chase;
  2. corn is CONCEALMENT, not a blackout -- a staring cultist at range
     cannot lock through it in seconds, but point-blank it still fills
     (the sit-next-to-a-cultist exploit is dead);
  3. an enclosed hide breaks the chase into SEARCH, and the searcher
     SWEEPS the hide and CHECKS it -- the struggle fires;
  4. the struggle resolves both ways: enough presses is the burst-out
     (unhidden, checker staggered, panic burst armed, not captured);
     an expired window is the CAPTURED death;
  5. walls still occlude absolutely -- suspicion decays behind one;
  6. apex pursuers (_force_chase) bypass the whole machine.

Run from the project root:  python tests/stealth.py
SDL runs headless (dummy drivers); no display required.
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame
from systems.game import Game
from systems.config import SUS_NOTICE, STRUGGLE_PRESSES
from constants import TILE

FAILS = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


def new_game():
    g = Game()
    g.save.new()
    g._start_play()
    return g


def tick(g, n=1, dt=1 / 30.0):
    for _ in range(n):
        g.state = "playing"
        if g.dialog.active:
            g.dialog.active = False
        g.step(dt)


def clear_cult(g):
    g.scene.npcs = [x for x in g.scene.npcs
                    if not str(getattr(x, "tag", "")).startswith("cult_")]


def open_field(g):
    """A verified-open patch of brimley grass (east of the kid's house)
    so the measurements aren't at the mercy of spawn-side tree clutter."""
    g.player.x, g.player.y = 73 * TILE + 16, 68 * TILE
    g.player.hidden = None
    g.player.hide_origin = None


def plant(g, dist=90):
    """Plant a scout cultist `dist` px from the player at the first angle
    with a clear line of sight, looking at them."""
    px, py = g.player.x, g.player.y
    for i in range(16):
        a = i * math.tau / 16
        cx, cy = px + math.cos(a) * dist, py + math.sin(a) * dist
        if (not g.scene.is_solid_at(cx, cy)
                and g.scene.clear_sight_line(cx, cy, px, py)):
            n = g._spawn_cultist("cult_regular", "cultist", at=(cx, cy))
            n.x, n.y = cx, cy
            n._cult_state = "scout"
            n._suspicion = 0.0
            aim(g, n)
            return n
    raise AssertionError("no clear planting spot found")


def aim(g, n):
    dx, dy = g.player.x - n.x, g.player.y - n.y
    m = math.hypot(dx, dy) or 1
    n.facing = (dx / m, dy / m)


def press_e(g, times=1):
    for _ in range(times):
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))


def main():
    print("stealth: graded suspicion / cover classes / the struggle")

    # --- 1. open ground: climb -> NOTICE -> LOCK ------------------------
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)                     # past on-enter dialogs (world freezes)
    clear_cult(g)
    open_field(g)
    n = plant(g, 90)
    for _ in range(6):
        aim(g, n)
        tick(g, 1)
    check(0.0 < n._suspicion < 1.0,
          f"graded: suspicion climbs without an instant lock "
          f"({n._suspicion:.2f} after 0.2s)")
    saw_notice = False
    for _ in range(120):
        aim(g, n)
        tick(g, 1)
        if getattr(n, "_sus_alert", False):
            saw_notice = True
        if n._cult_state == "chase":
            break
    check(saw_notice, "graded: the NOTICE tell fired before the lock")
    check(n._cult_state == "chase", "graded: a full bar locks the chase")

    # --- 2. corn: leaky at range, fatal point-blank ---------------------
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)
    clear_cult(g)
    open_field(g)
    n = plant(g, 150)
    ex, ey = n.x, n.y
    peak = 0.0
    for _ in range(90):             # 3 s of a cultist STARING from 150 px
        aim(g, n)
        tick(g, 1)
        n.x, n.y = ex, ey
        g.player.hidden = "corn"
        peak = max(peak, n._suspicion)
    check(n._cult_state != "chase" and peak < 1.0,
          f"corn: concealment holds at range (peak sus {peak:.2f})")
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)
    clear_cult(g)
    open_field(g)
    n = plant(g, 30)
    locked = False
    for _ in range(300):
        aim(g, n)
        tick(g, 1)
        n.x, n.y = g.player.x + 30, g.player.y
        g.player.hidden = "corn"
        if n._cult_state == "chase":
            locked = True
            break
    check(locked, "corn: point-blank concealment still fills (no camping)")

    # --- 3+4. enclosed hide -> SEARCH -> CHECK -> the struggle ----------
    def hide_and_get_checked():
        g = new_game()
        g.load_scene_now("brimley", "default")
        tick(g, 30)
        clear_cult(g)
        open_field(g)
        n = plant(g, 60)
        n._cult_state = "chase"
        n._suspicion = 1.0
        n._last_seen_pos = (g.player.x, g.player.y)
        hx, hy = g.player.x, g.player.y
        g.scene.hide_spots = [(hx, hy, "under")]
        g.player.hidden = "under"
        g.player.hide_origin = (hx + 10, hy)
        for _ in range(600):
            tick(g, 1)
            if g._struggle is not None:
                return g, n, True
        return g, n, False

    g, n, struggled = hide_and_get_checked()
    check(struggled, "enclosed: a searcher sweeps and CHECKS the hide "
                     "(the struggle fires)")
    if struggled:
        press_e(g, STRUGGLE_PRESSES + 2)     # win it, with overshoot
        check(g._struggle is None and g.player.hidden is None,
              "struggle: winning the mash bursts the player OUT")
        check(getattr(n, "_stun_t", 0.0) > 0,
              "struggle: the checker staggers on a burst-out")
        check(getattr(g.player, "_burst_t", 0.0) > 0,
              "struggle: the panic burst arms")
        check(g._death_kind is None, "struggle: a won struggle is not a capture")
        check(g.player.hidden is None,
              "struggle: overshoot presses do not re-enter the hide")

    g, n, struggled = hide_and_get_checked()
    if struggled:
        for _ in range(120):                 # let the window expire
            tick(g, 1)
            if g._death_kind is not None:
                break
        check(g._death_kind == "cultist",
              "struggle: an ignored window is the CAPTURED end")
    else:
        check(False, "struggle: second check never fired")

    # --- 4b. the sight fringe cannot oscillate ---------------------------
    # A score below SUS_SCORE_HOLD must neither fill nor hold suspicion:
    # if it could pin the bar at 1.0, the machine would flip chase/search
    # every frame at the fringe and spam the lock/lose stings.
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)
    clear_cult(g)
    open_field(g)
    n = plant(g, 172)               # inside range, score < SUS_SCORE_HOLD
    ex, ey = n.x, n.y
    flips = 0
    prev = n._cult_state
    for _ in range(300):            # 10 s of staring from the fringe
        aim(g, n)
        tick(g, 1)
        n.x, n.y = ex, ey
        if n._cult_state != prev:
            flips += 1
            prev = n._cult_state
    check(n._cult_state != "chase" and n._suspicion < 1.0 and flips == 0,
          f"fringe: a sub-threshold glimpse never locks or oscillates "
          f"(sus={n._suspicion:.2f}, flips={flips})")

    # --- 4c. the noise core (2026-07 sound overhaul) ---------------------
    # One shared ear (stealth.hear_noise over Scene.emit_noise): scouts
    # turn on loud events with a face-the-sound telegraph; a dominant
    # MASK swallows quieter sounds; searchers hold their target unless
    # something strictly louder pulls them; set-piece kneelers are deaf.
    def underground(scene="works_sorting"):
        g = new_game()
        g.load_scene_now(scene, "default")
        tick(g, 10)
        return g

    g = underground()
    e = next(x for x in g.scene.enemies if x.kind == "cultist")
    e._cult_state = "scout"
    e._suspicion = 0.0
    g.scene.emit_noise(e.x + 100, e.y, 0.8, kind="test")
    x0, y0 = e.x, e.y
    tick(g, 1)
    check(e._cult_state == "investigate",
          "noise: a scout turns on a loud event")
    moved = False
    for _ in range(10):                 # inside NOISE_REACT_PAUSE
        tick(g, 1)
        if abs(e.x - x0) + abs(e.y - y0) > 2:
            moved = True
    check(not moved and e.facing[0] > 0.7,
          "noise: the telegraph faces the sound before walking")
    tick(g, 30)
    check(abs(e.x - x0) > 4, "noise: after the hold it walks to the source")

    g = underground()
    e = next(x for x in g.scene.enemies if x.kind == "cultist")
    e._cult_state = "scout"
    g.scene.set_noise_mask(e.x, e.y, 4000, 0.85, 10.0)
    r = g.scene.emit_noise(e.x + 80, e.y, 0.8, kind="test")
    tick(g, 1)
    check(r is None and e._cult_state == "scout",
          "mask: a sub-level sound is swallowed (loud hides small)")
    r2 = g.scene.emit_noise(e.x + 80, e.y, 1.0, kind="test")
    tick(g, 1)
    check(r2 is not None and e._cult_state == "investigate",
          "mask: a louder-than-the-mask sound still lands")

    g = underground()
    e = next(x for x in g.scene.enemies if x.kind == "cultist")
    from systems.stealth import enter_search
    e._last_seen_pos = (e.x + 60, e.y)
    enter_search(e, g.scene)
    g.scene.emit_noise(e.x - 100, e.y, 0.8, kind="test")
    tick(g, 1)
    check(e._cult_state == "search",
          "pull: an ordinary noise cannot divert a searcher")
    g.scene.emit_noise(e.x - 100, e.y, 0.95, kind="test")
    tick(g, 1)
    check(e._cult_state == "investigate" and e._last_seen_pos[0] < e.x,
          "pull: a LOUD noise re-tasks the searcher")

    g = underground("works_sign")
    kneeler = next(x for x in g.scene.enemies
                   if x.kind == "cultist" and getattr(x, "aggro", 1) == 0)
    g.scene.emit_noise(kneeler.x + 40, kneeler.y, 1.0, kind="test")
    tick(g, 1)
    check(kneeler._cult_state == "scout",
          "deaf: a set-piece kneeler ignores noise (its wake is scripted)")

    # --- 4d. the church bell (the town's dominant noise source) ---------
    # Rung from the tower pull (E, scenes/threshold_extras.py); Game.
    # _ring_bell/_tick_bell drive the peal across scene loads. While it
    # peals: the surface is MASKED (small noises drown), Brimley hears a
    # map-wide pull at the church door, and the first cult hunter to
    # reach the door stills the rope and sweeps the churchyard.
    g = new_game()
    g.load_scene_now("bell_tower", "default")
    tick(g, 40)
    g.player.x, g.player.y = 5 * TILE + 32, 6 * TILE + 30
    press_e(g)
    check(g._bell_t > 19.0 and g.save.flag("bell_rung"),
          "bell: E at the pull arms the peal")
    g.load_scene_now("brimley", "default")
    tick(g, 10)
    clear_cult(g)
    g.player.x, g.player.y = 73 * TILE + 16, 68 * TILE
    g.player.hidden = None
    n = g._spawn_cultist("cult_regular", "cultist",
                         at=(70 * TILE + 16, 66 * TILE))
    n.x, n.y = 70 * TILE + 16, 66 * TILE
    n._cult_state = "scout"
    n._suspicion = 0.0
    n.facing = (0.0, -1.0)
    bx, by = g.scene._bell_door
    d0 = g.scene.world_dist(n.x, n.y, bx, by)
    heard = False
    for _ in range(120):
        tick(g, 1)
        if n._cult_state == "investigate":
            heard = True
            break
    check(heard and getattr(n, "_last_seen_pos", None) == (bx, by),
          f"bell: the peal pulls a cultist {d0:.0f}px out, far past "
          f"his 180px ear, onto the church door")
    check(getattr(n, "_cult_state_t", 0) > 15.0,
          "bell: the walk budget scales to the trip")
    r = g.scene.emit_noise(g.player.x, g.player.y, 0.8, kind="probe")
    check(r is None,
          "bell: the peal MASKS the player's small noises scene-wide")
    n.x, n.y = bx + 30, by
    tick(g, 2)
    check(g._bell_t <= 0.0 and n._cult_state == "search",
          "bell: a hunter at the door stills the rope and sweeps")
    check(not g.scene.mask_active(),
          "bell: the mask drops with the bell")

    # --- 5. walls occlude absolutely ------------------------------------
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)
    clear_cult(g)
    n = plant(g, 90)
    n._suspicion = 0.6
    g.player.x, g.player.y = 7 * TILE, 12 * TILE    # south of the church wall
    n.x, n.y = 7 * TILE, 2 * TILE                   # north, wall between
    tick(g, 30)
    check(n._suspicion < 0.6, "walls: suspicion decays behind one")

    # --- 6. apex bypass ---------------------------------------------------
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 30)
    clear_cult(g)
    open_field(g)
    n = plant(g, 120)
    n._force_chase = True
    n._suspicion = 0.0
    g.player.hidden = "corn"                        # cover means nothing to it
    tick(g, 3)
    check(n._cult_state == "chase",
          "apex: _force_chase bypasses suspicion and cover entirely")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES")
        return 1
    print("All stealth checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
