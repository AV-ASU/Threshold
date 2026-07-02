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

    # --- 4e. placed noisemakers (traps underfoot + lure sources) --------
    # Scene.add_noise_trap: fires ON ENTRY, re-arms only after leaving;
    # Scene.add_noise_source: E toggles a periodic lure that the first
    # cult hunter to reach shuts off (then sweeps around it, like the
    # bell). Every placement must sit on walkable ground.
    from scenes import SCENE_BUILDERS, load_scene
    n_placed = 0
    for skey in SCENE_BUILDERS:
        _sc = load_scene(skey)
        for tr in getattr(_sc, "noise_traps", []) or []:
            n_placed += 1
            check(not _sc.is_solid_at(tr["x"], tr["y"]),
                  f"noisemakers: trap {tr['kind']} in {skey} on "
                  f"walkable ground")
        for s in getattr(_sc, "noise_sources", []) or []:
            n_placed += 1
            check(not _sc.is_solid_at(s["x"], s["y"]),
                  f"noisemakers: source {s['kind']} in {skey} on "
                  f"walkable ground")
    check(n_placed >= 9, f"noisemakers: placements present ({n_placed})")

    g = new_game()
    g.load_scene_now("works_sorting", "default")
    tick(g, 10)
    for e in g.scene.enemies:
        e._cult_state = "scout"
        e._suspicion = 0.0
        e.x, e.y = 13 * TILE + 16, 9 * TILE + 16
        e.facing = (0.0, 1.0)
    tr = g.scene.noise_traps[0]
    e = g.scene.enemies[0]
    e.x, e.y = tr["x"] + 120, tr["y"]
    e.facing = (0.0, -1.0)
    g.player.x, g.player.y = 1 * TILE + 16, 9 * TILE + 16
    g.player.hidden = None
    tick(g, 2)
    g.player.x, g.player.y = tr["x"], tr["y"]        # step into the litter
    tick(g, 2)
    check(e._cult_state == "investigate"
          and e._last_seen_pos == (tr["x"], tr["y"]),
          "noisemakers: stepping in the litter turns the nearest head")

    g = new_game()
    g.load_scene_now("works_vats", "default")
    tick(g, 10)
    src = next(s for s in g.scene.noise_sources if s["kind"] == "valve")
    for e in g.scene.enemies:
        e._cult_state = "scout"
        e._suspicion = 0.0
        e.x, e.y = 10 * TILE + 16, 5 * TILE + 16
        e.facing = (1.0, 0.0)
    g.player.x, g.player.y = src["x"], src["y"] + 20
    g.player.hidden = None
    press_e(g)
    check(src["on"], "noisemakers: E cracks the valve open")
    w = g.scene.enemies[0]
    heard = False
    for _ in range(60):
        tick(g, 1)
        if w._cult_state == "investigate":
            heard = True
            break
    check(heard and w._last_seen_pos == (src["x"], src["y"]),
          "noisemakers: the hiss lures a worker off the crossing")
    hx, hy, hkind = g.scene.hide_spots[0]
    g.player.x, g.player.y = hx, hy                  # vanish into the hide
    g.player.hidden = hkind
    silenced = False
    for _ in range(600):
        tick(g, 1)
        if not src["on"]:
            silenced = True
            break
    check(silenced, "noisemakers: a worker seats the valve shut")
    check(any(x._cult_state == "search" for x in g.scene.enemies),
          "noisemakers: the silencer sweeps around the dead lure")

    # --- 4f. errand stations (the cult's JOBS layer) ---------------------
    # Scene.add_cult_station + stealth.errand_step: scouts walk their
    # stations (leg planned once over the full grid, so cross-town legs
    # work), pose and dwell, and anything the ears or eyes raise peels
    # them off; they resume after. Every station must be REACHABLE from
    # the scene's default spawn -- a walkable-but-sealed pocket (the
    # burn clearing) once ate a station whole.
    n_st = 0
    for skey in SCENE_BUILDERS:
        _sc = load_scene(skey)
        _spx, _spy = _sc.spawns["default"]
        for _st in getattr(_sc, "cult_stations", []) or []:
            n_st += 1
            _p = _sc.nav_path(_spx, _spy, _st["x"], _st["y"],
                              max_visit=_sc.w * _sc.h + 8)
            check(_p is not None,
                  f"errands: station in {skey} at ({_st['x']},"
                  f"{_st['y']}) reachable from spawn")
    check(n_st >= 10, f"errands: stations present ({n_st})")

    g = new_game()
    g.load_scene_now("works_vats", "default")
    tick(g, 10)
    hx, hy, hkind = g.scene.hide_spots[0]
    g.player.x, g.player.y = hx, hy
    g.player.hidden = hkind
    w = g.scene.enemies[0]
    w._cult_state = "scout"
    w._suspicion = 0.0
    posed = False
    for _ in range(30 * 40):
        tick(g, 1)
        if getattr(w, "_errand_posing", False):
            posed = True
            break
    check(posed, "errands: a vats worker reaches a station and poses")
    check(getattr(w, "pose", None) == "chant",
          "errands: the station's task pose is taken")
    tr = g.scene.noise_traps[0]
    g.scene.emit_noise(tr["x"], tr["y"], 0.8, kind="probe")
    tick(g, 2)
    check(w._cult_state == "investigate"
          and getattr(w, "pose", None) is None,
          "errands: noise outranks the chore and drops the pose")
    resumed = False
    for _ in range(30 * 30):
        tick(g, 1)
        if (w._cult_state == "scout"
                and getattr(w, "_errand_posing", False)):
            resumed = True
            break
    check(resumed, "errands: he resumes his rounds after the noise dies")

    # --- 4g. one-hop noise bleed + animated doors ------------------------
    # A LOUD noise underground brings ONE transient cultist through the
    # nearest exit after a walk-time (the swinging leaf is the tell);
    # he looks the noise over and leaves; a long cooldown follows. The
    # surface never bleeds; quiet noises don't carry.
    g = new_game()
    g.load_scene_now("the_cells", "default")
    tick(g, 10)
    g.player.x, g.player.y = 2 * TILE + 16, 2 * TILE + 16
    g.player.hidden = "under"
    g.scene.emit_noise(4 * TILE + 16, 5 * TILE + 16, 1.0, kind="shot")
    tick(g, 2)
    check(g._bleed is not None and g._bleed["npc"] is None,
          "bleed: a LOUD noise underground arms a visit (walk-time first)")
    n0 = len(g.scene.enemies)
    for _ in range(30 * 7):
        tick(g, 1)
        if g._bleed and g._bleed["npc"] is not None:
            break
    check(g._bleed is not None and g._bleed["npc"] is not None
          and len(g.scene.enemies) == n0 + 1,
          "bleed: exactly one transient comes through the door")
    e = g._bleed["npc"]
    check(e._cult_state == "investigate"
          and e._last_seen_pos == (4 * TILE + 16, 5 * TILE + 16),
          "bleed: he walks to the noise")
    check(g.scene._door_anim.get(g._bleed["door"]) is not None,
          "doors: the leaf swings as the tell")
    g._bleed["linger"] = 999.0            # skip the look-around
    gone = False
    for _ in range(30 * 20):
        tick(g, 1)
        if g._bleed is None:
            gone = True
            break
    check(gone and e not in g.scene.enemies and g._bleed_cd > 0,
          "bleed: he leaves, despawns, and the cooldown arms")
    g.scene.emit_noise(4 * TILE + 16, 5 * TILE + 16, 1.0, kind="shot")
    tick(g, 3)
    check(g._bleed is None, "bleed: the cooldown blocks a second visit")

    g = new_game()
    g.load_scene_now("the_cells", "default")
    tick(g, 10)
    g.player.hidden = "under"
    g.scene.emit_noise(4 * TILE + 16, 5 * TILE + 16, 0.8, kind="probe")
    tick(g, 3)
    check(g._bleed is None, "bleed: a sub-LOUD noise does not carry")
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 10)
    g.player.hidden = "under"
    g.scene.emit_noise(g.player.x, g.player.y, 1.0, kind="shot")
    tick(g, 3)
    check(g._bleed is None, "bleed: the surface never bleeds")

    g = new_game()
    g.load_scene_now("works_sorting", "default")
    tick(g, 10)
    door = g._nearest_exit_tile(g.player.x, g.player.y)
    check(g.scene.door_pulse(door[0], door[1], hold=0.5),
          "doors: a pulse opens a resting leaf")
    tick(g, 10)
    st_ = g.scene._door_anim.get(door)
    check(st_ is not None and st_["open"] > 0.9,
          "doors: the leaf swings fully open")
    tick(g, 40)
    check(g.scene._door_anim.get(door) is None,
          "doors: the leaf seats shut and the state cleans up")

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

    # --- 8. darkness is concealment + the hide-exit beat -----------------
    # Pillar 2A's "shadow" cover: in a DARK scene an unlit player
    # (flashlight off, outside every light pool) reads at
    # SUS_CONCEAL_DARK -- leaky like corn, never stacking, ignored by
    # apex eyes. And leaving an enclosed hide takes HIDE_EXIT_BEAT of
    # rooted vulnerability (the deferred exit-takes-a-beat window).
    from systems.stealth import concealment_factor as _cf
    from systems.config import SUS_CONCEAL_DARK, HIDE_EXIT_BEAT
    g = new_game()
    g.load_scene_now("the_cells", "default")
    tick(g, 10)
    p = g.player
    p.hidden = None
    g.flashlight_on = False
    p.x, p.y = 2 * TILE + 16, 2 * TILE + 16
    if g.scene.lit_at(p.x, p.y):
        p.x, p.y = 4 * TILE + 16, 2 * TILE + 16
    tick(g, 2)
    check(getattr(p, "_in_dark", False)
          and abs(_cf(p) - SUS_CONCEAL_DARK) < 1e-9,
          "dark: the unlit gloom conceals at SUS_CONCEAL_DARK")
    p.inventory.add("flashlight", 1)
    g.flashlight_on = True
    tick(g, 2)
    check(not getattr(p, "_in_dark", False) and _cf(p) == 1.0,
          "dark: a lit flashlight burns the cover away")
    g.flashlight_on = False
    p.hidden = "under"
    check(_cf(p) == 0.0, "dark: an enclosed hide still zeroes the score")
    p.hidden = None
    g2 = new_game()
    g2.load_scene_now("brimley", "default")
    tick(g2, 10)
    check(not getattr(g2.player, "_in_dark", False),
          "dark: the daylit surface never grants it")

    g = new_game()
    g.load_scene_now("works_vats", "default")
    tick(g, 10)
    for e in g.scene.enemies:
        e.x, e.y = 10 * TILE + 16, 5 * TILE + 16
        e._cult_state = "scout"
        e._suspicion = 0.0
        e.facing = (1, 0)
    p = g.player
    hx, hy, hkind = g.scene.hide_spots[0]
    p.x, p.y = hx + 10, hy
    p.hidden = None
    press_e(g)
    check(p.hidden == hkind, "beat: E enters the enclosed hide")
    press_e(g)
    check(p.hidden is None
          and getattr(p, "emerge_t", 0.0) > 0.0,
          "beat: exiting arms the rooted emerge window")

    class _FK(dict):
        def __getitem__(self, k):
            return self.get(k, False)
    fk = _FK({pygame.K_w: True})
    x0, y0 = p.x, p.y
    g.update_player(1 / 30.0, fk)
    check((p.x, p.y) == (x0, y0), "beat: movement is rooted while emerging")
    for _ in range(int(HIDE_EXIT_BEAT * 30) + 2):
        g.update_player(1 / 30.0, fk)
    check((p.x, p.y) != (x0, y0), "beat: movement returns after the beat")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES")
        return 1
    print("All stealth checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
