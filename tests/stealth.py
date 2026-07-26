"""Stealth-rework guard (DESIGN.md §12): graded suspicion, cover
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
# SDL converts SIGTERM into a quit event instead of dying, so `timeout`
# and CI cancellation cannot stop a harness (it runs to completion while
# the wrapper reports 124). Keep the default kill behavior in tests.
os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")
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
        # A stray reach-grab (CULT_GRAB_REACH) can open THE TALK -- the
        # one-time first-contact tableau, a world-freeze. Page it through
        # the way a player would (Escape pages, never aborts; the release
        # and stand-down run on the last page) so fixtures that are not
        # about the grab keep running.
        for _pg in range(14):
            tb = getattr(g, "_tableau", None)
            if tb is None or tb.get("kind") != "talk":
                break
            g._tableau_input(pygame.event.Event(pygame.KEYDOWN,
                                                key=pygame.K_ESCAPE))
        g.step(dt)


def clear_cult(g):
    g.scene.npcs = [x for x in g.scene.npcs
                    if not str(getattr(x, "tag", "")).startswith("cult_")]


def open_field(g):
    """A verified-open patch of brimley grass (the west-central glade,
    kept clear of corn/marsh/trees in the 60x60 redesign) so the
    measurements aren't at the mercy of spawn-side tree clutter."""
    g.player.x, g.player.y = 14 * TILE + 16, 34 * TILE + 16
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
    n = plant(g, 34)
    locked = False
    for _ in range(300):
        aim(g, n)
        tick(g, 1)
        # Pinned just OUTSIDE the arm's reach (CULT_GRAB_REACH), inside
        # the SUS_NEAR field: point-blank for the fill, no grab noise.
        n.x, n.y = g.player.x + 34, g.player.y
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
    # The FIRST grab of a run is always the Talk (the grip close-up now),
    # struggle losses included -- so spend the freebie to test the real
    # CAPTURED end of an ignored window, not the one-time warning.
    g.save.set_flag("cult_talk_given", True)
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

    # (2026-07: the Sign Chamber congregation are set-piece NPCs now --
    # no cult tag, so no noise reaction, no gaze, no grab; their wake is
    # the scripted calling-out. The east patrol stays the live threat.)
    g = underground("works_sign")
    _rank = [n for n in g.scene.npcs if getattr(n, "pose", "") == "kneel"]
    check(len(_rank) >= 4,
          "deaf: the congregation kneels as set-piece NPCs")
    check(all(not str(getattr(n, "tag", "")).startswith("cult_")
              for n in _rank),
          "deaf: the rank carries no cult tag (its wake is scripted)")
    check(any(e.kind == "cultist" and e.alive for e in g.scene.enemies),
          "deaf: the east patrol is still the room's live threat")

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
    g.player.x, g.player.y = 48 * TILE + 16, 42 * TILE + 16   # by the kid's house
    g.player.hidden = None
    n = g._spawn_cultist("cult_regular", "cultist",
                         at=(46 * TILE + 16, 42 * TILE + 16))
    n.x, n.y = 46 * TILE + 16, 42 * TILE + 16
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
    g.load_scene_now("works_cistern", "default")
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
    g.load_scene_now("works_cistern", "default")
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
    g.player.x, g.player.y = 8 * TILE + 16, 24 * TILE + 16   # south of the shop wall
    n.x, n.y = 8 * TILE + 16, 15 * TILE + 16                 # north, wall between
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

    # --- 8. darkness is NOT concealment + the hide-exit beat --------------
    # Maintainer ruling, 2026-07: "darkness shouldn't hide you AT ALL." The
    # dark belongs to Him -- it is the condition His things need to open, so
    # hiding in it was hiding inside the threat. Cover is what you put BETWEEN
    # yourself and an eye: corn, a hide, a wall. The old SUS_CONCEAL_DARK
    # shadow-cover pass is CUT, and this locks it staying cut in the darkest
    # room in the game. Leaving an enclosed hide still takes HIDE_EXIT_BEAT of
    # rooted vulnerability (the deferred exit-takes-a-beat window).
    from systems.stealth import concealment_factor as _cf
    from systems.config import HIDE_EXIT_BEAT, SUS_CONCEAL_CORN
    import systems.config as _cfg
    check(not hasattr(_cfg, "SUS_CONCEAL_DARK"),
          "dark: SUS_CONCEAL_DARK is gone from config (no shadow cover)")
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
    assert not g.scene.lit_at(p.x, p.y) and not g._flashlight_lit()
    check(_cf(p) == 1.0,
          "dark: standing unlit in the deepest dark conceals NOTHING")
    # ...and no stray _in_dark stamp survives to be read by a future eye.
    check(not getattr(p, "_in_dark", False),
          "dark: nothing stamps player._in_dark anymore")
    p.hidden = "corn"
    check(abs(_cf(p) - SUS_CONCEAL_CORN) < 1e-9,
          "dark: real cover still works in the dark (corn is unaffected)")
    p.hidden = "under"
    check(_cf(p) == 0.0, "dark: an enclosed hide still zeroes the score")
    p.hidden = None

    g = new_game()
    g.load_scene_now("works_cistern", "default")
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

    # --- 10. the cult WAKES at 1 evidence (CULT_WAKE_EV) -----------------
    # Below the first find the surface spawns NO patrol: the town is
    # only wrong, not yet hostile. The first evidence raises the hoods.
    g = new_game()
    g.load_scene_now("brimley", "default")
    tick(g, 10)
    check(not any(str(getattr(n, "tag", "")).startswith("cult_")
                  for n in g.scene.npcs),
          "wake: zero evidence, zero cult on the surface")
    ev = g.save.arg("evidence", [])
    ev.append({"name": "maras_room", "lines": [], "weight": 0.1})
    g.save.set_arg("evidence", ev)
    tick(g, 40)
    check(any(str(getattr(n, "tag", "")).startswith("cult_")
              for n in g.scene.npcs),
          "wake: the first find raises the hooded ones")

    # --- 10. deep-water WADE (TODO #8) -----------------------------------
    # The flooded deep works slow the player and throw a loud splash the
    # searchers converge on. Scoped to WADE_SCENES; the Brimley river is
    # NOT one, so its `~` keeps its own set-piece rules.
    from systems.config import (WADE_SCENES, WADE_SPEED_MULT,
                                 WADE_SPLASH_LOUD, NOISE_SEARCH_PULL)
    check(WADE_SPEED_MULT < 1.0, "wade: wading slows the player")
    check(WADE_SPLASH_LOUD > NOISE_SEARCH_PULL,
          "wade: a splash out-shouts the searcher-pull threshold")

    def _find_water(g):
        for ty, row in enumerate(g.scene.floor):
            if "~" in row:                 # row may be a str or a list
                return list(row).index("~"), ty
        return None

    for key in ("works_cistern", "the_sump", "depths_threshing"):
        g = new_game()
        g.load_scene_now(key, "default")
        wt = _find_water(g)
        check(wt is not None, f"wade: {key} is flooded (has `~` water)")
        if wt:
            g.player.x, g.player.y = wt[0] * TILE + 16, wt[1] * TILE + 16
            check(g._wading(), f"wade: standing in {key} water reads as wading")

    g = new_game()
    g.load_scene_now("works_cistern", "default")
    g.player.x, g.player.y = 6 * TILE + 16, 5 * TILE + 16   # dry crossing
    check(not g._wading(), "wade: the dry central crossing is not wading")

    # the Brimley river is EXCLUDED (its own set-piece, not a WADE scene)
    g = new_game()
    g.load_scene_now("brimley", "default")
    check("brimley" not in WADE_SCENES, "wade: Brimley is not a WADE scene")
    river = _find_water(g)
    if river:
        g.player.x, g.player.y = river[0] * TILE + 16, river[1] * TILE + 16
        check(not g._wading(), "wade: the Brimley river never reads as wading")

    # the real step path throws a SPLASH: drive movement across the flood
    g = new_game()
    # The tilt is the only camera, so movement is body-relative. Pin the
    # look east and hold FORWARD to drive the real step path east across the
    # flooded N arm; stub _update_look so the (dummy) mouse can't drag the
    # heading off east mid-walk.
    g._update_look = lambda dt: None
    g.look.body = 0.0
    g.load_scene_now("works_cistern", "default")
    g.player.x, g.player.y = 4 * TILE + 16, 2 * TILE + 16   # W end of N arm
    g.player.step_timer = 0.0

    class _Held:
        def __init__(self, ks): self.ks = set(ks)
        def __getitem__(self, k): return 1 if k in self.ks else 0
    _orig_gp = pygame.key.get_pressed
    pygame.key.get_pressed = lambda: _Held({pygame.K_w})
    splashed = False
    try:
        for _ in range(20):
            tick(g, 1)
            if any(e[4] == "splash" for e in g.scene._noise_events):
                splashed = True
                break
    finally:
        pygame.key.get_pressed = _orig_gp
    check(splashed, "wade: a wet footfall throws a splash noise event")

    # --- 11. "no light = danger" (TODO #21): the gaze opens under the open
    # sky, in the deep, AND in a DARK non-refuge interior -- but there a light
    # POOL / the flashlight is the cover, and BURNS them. The true refuges
    # (SAFE_SCENES) stay gaze-free. -------------------------------------------
    from systems.config import (WATCHER_OPEN_SCENES, WATCHER_WAKE_EV,
                                 WATCHER_GRACE, WATCHER_SPAWN_BASE,
                                 WATCHER_GAZE_DISPEL, WATCHER_LIGHT_BURN,
                                 DIM_INTERIOR_SCENES, KING_FREE_SCENES)
    check(DIM_INTERIOR_SCENES <= WATCHER_OPEN_SCENES,
          "watchers: the dark non-refuge interiors are now in the gaze's reach")
    check("bedroom" not in WATCHER_OPEN_SCENES
          and "toby_house" not in WATCHER_OPEN_SCENES,
          "watchers: the true refuges (SAFE_SCENES) stay outside the gaze")
    check("brimley" in WATCHER_OPEN_SCENES
          and "effigy_grove" in WATCHER_OPEN_SCENES
          and "works_sign" in WATCHER_OPEN_SCENES,
          "watchers: the open sky and the deep stay in it")
    # Inside the shop, out of cover: the gaze opens. (The player stands at a
    # dark spot because the SPAWN rule needs one in view -- not because being
    # unlit is what exposes you. Being out of cover is.)
    g = new_game()
    g.load_scene_now("shop", "default")
    tick(g, 30)
    g.save.set_arg("evidence", [{"name": f"w{i}"}
                                for i in range(WATCHER_WAKE_EV)])
    # A mech-dark spot on the OPEN shop floor (the spawn rule needs a dark
    # spot WITH line of sight to the player, so the exposure test stands
    # in the open, not the sealed pantry).
    dark_x, dark_y = 6 * TILE + 16, 5 * TILE + 16
    assert not g.scene.lit_at(dark_x, dark_y)
    for _ in range(int((WATCHER_GRACE + WATCHER_SPAWN_BASE + 4) * 30)):
        g.player.x, g.player.y = dark_x, dark_y
        g.player.hidden = None
        g._tick_watchers(1 / 30.0)
        if g._watchers:
            break
    check(bool(g._watchers),
          "watchers: standing in the dark of a non-refuge interior opens one")
    # The spawn rules themselves (maintainer, 2026-07): every opened
    # Watcher stands in the DARK with LINE OF SIGHT to the player...
    check(all((not g.scene.lit_at(w.x, w.y))
              and g.scene.clear_sight_line(w.x, w.y, dark_x, dark_y)
              for w in g._watchers),
          "watchers: every spawn is dark AND holds line of sight")
    # ...and the sealed pantry (shut doors, no dark spot in view) can
    # open NOTHING: no unanswerable accumulation, and a fully lit or
    # sealed room is secured.
    g.player.x, g.player.y = 2 * TILE + 16, 1 * TILE + 16
    n0 = len(g._watchers)
    g._spawn_watcher()
    check(len(g._watchers) == n0,
          "watchers: no dark spot with sight of you = nothing opens "
          "(the sealed pantry)")
    # Step into a light POOL: it changes NOTHING about the hold (maintainer
    # ruling, 2026-07 -- "Watchers should be able to gaze at you while you're
    # standing in the light, that's the whole point of them"). A lamp is not a
    # safe square; the gaze holds you in it. This is the check that fails if
    # anyone re-adds light-as-cover.
    lit_x, lit_y = 12 * TILE + 16, 9 * TILE + 16   # inside the hooded fan
    assert g.scene.lit_at(lit_x, lit_y)
    g.player.x, g.player.y = lit_x, lit_y
    g.player.hidden = None
    g._tick_watchers(1 / 30.0)
    check(g._watcher_gaze == float(len(g._watchers)) and g._watcher_gaze > 0.0,
          "watchers: a light pool does NOT drop the gaze hold (it sees you)")
    # And the wave keeps BUILDING while you stand in the light: the timer runs.
    t_before = g._watcher_clone_t
    g._tick_watchers(1 / 30.0)
    check(g._watcher_clone_t < t_before,
          "watchers: the spawn timer keeps running while you stand in light")
    # Real cover is the only thing that stops it.
    g.player.hidden = "under"
    g._tick_watchers(1 / 30.0)
    check(g._watcher_gaze == 0.0,
          "watchers: an enclosed hide (real cover) drops the hold")
    g.player.hidden = None
    # Light BURNS a Watcher: one caught IN a pool dissolves fast.
    g._cursed = True
    g._spawn_watcher()
    if g._watchers:
        w = g._watchers[-1]
        w.x, w.y = lit_x, lit_y
        burned = False
        for _ in range(int((WATCHER_GAZE_DISPEL / (1 + WATCHER_LIGHT_BURN)
                            + 0.6) * 30)):
            w.x, w.y = lit_x, lit_y
            g._tick_watcher_gaze(1 / 30.0)
            if w not in g._watchers:
                burned = True
                break
        check(burned, "watchers: a Watcher caught in a light pool burns out")
    # The true refuge stays gaze-free: inside toby_house, no Watcher ever opens.
    gr = new_game()
    gr.load_scene_now("toby_house", "default")
    tick(gr, 30)
    gr.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(WATCHER_WAKE_EV)])
    for _ in range(int((WATCHER_GRACE + WATCHER_SPAWN_BASE + 4) * 30)):
        gr.player.hidden = None
        gr._tick_watchers(1 / 30.0)
    check(not gr._watchers and not gr._cursed,
          "watchers: the true refuge never manifests one")
    # Same clock in the open: the wave DOES open (the mechanic still works).
    g2 = new_game()
    g2.load_scene_now("brimley", "default")
    tick(g2, 30)
    clear_cult(g2)
    g2.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(WATCHER_WAKE_EV)])
    assert "brimley" not in KING_FREE_SCENES
    for _ in range(int((WATCHER_GRACE + 2) * 30)):
        g2.player.hidden = None
        g2._tick_watchers(1 / 30.0)
        if g2._watchers:
            break
    check(bool(g2._watchers),
          "watchers: the same exposure in the open still opens the wave")

    # ---- §12: cult liveness stays OUT of the threat path (TODO #23a) ----
    # The synchrony beat and the hand-off are scout-only dressing; a frozen
    # scout still detects, and no threat state ever pauses.
    print("[12] cult liveness: synchrony + hand-off never touch the threat")
    from types import SimpleNamespace
    from systems.stealth import sync_pause, handoff_step
    from systems.config import (CULT_SYNC_PERIOD, CULT_SYNC_HOLD,
                                CULT_HANDOFF_RANGE, CULT_HANDOFF_HOLD)
    from entities.npc import NPC
    gl = new_game()
    gl.load_scene_now("brimley", "default")
    clear_cult(gl)
    scn = gl.scene
    real_ticks = pygame.time.get_ticks
    try:
        # (a) the shared clock: a scout freezes inside the window, not outside.
        frame_ms = [int(CULT_SYNC_PERIOD * 1000) + 100]   # inside the hold
        pygame.time.get_ticks = lambda: frame_ms[0]
        sc_actor = SimpleNamespace(_cult_state="scout", lock_facing=False,
                                   aggro=1)
        check(sync_pause(sc_actor) is True,
              "sync: a scout holds during the shared beat")
        frame_ms[0] = int((CULT_SYNC_PERIOD + CULT_SYNC_HOLD) * 1000) + 500
        check(sync_pause(sc_actor) is False,
              "sync: the beat releases after the hold")
        # (b) threat states never pause, even inside the window.
        frame_ms[0] = int(CULT_SYNC_PERIOD * 1000) + 100
        held = [sync_pause(SimpleNamespace(_cult_state=st, lock_facing=False,
                                           aggro=1))
                for st in ("chase", "search", "investigate")]
        check(not any(held),
              "sync: chase/search/investigate never pause")
        check(sync_pause(SimpleNamespace(_cult_state="scout",
                                         lock_facing=True, aggro=0)) is False,
              "sync: set-piece kneelers keep their scripted stillness")
        # (c) detection scores straight through the freeze: a real cultist
        # in the open, player in view, gains suspicion while standing still.
        open_field(gl)
        cx = gl.player.x
        cy = gl.player.y - 3 * TILE
        cult = NPC(cx, cy, "A cultist", "cultist", movement="chaser",
                   tag="cult_test")
        cult.facing = (0, 1)                      # looking at the player
        for _ in range(6):
            cult._cult_tick(1 / 30.0, scn, gl.player)
        check(cult._suspicion > 0.0,
              "sync: a frozen scout still fills suspicion")
        check((cult.x, cult.y) == (cx, cy),
              "sync: and has not moved while the beat holds")
        # (d) the hand-off: two crossing scouts freeze, face, and part on
        # a cooldown; a chasing peer is never met.
        frame_ms[0] = int((CULT_SYNC_PERIOD + CULT_SYNC_HOLD) * 1000) + 500
        a = NPC(cx, cy, "A", "cultist", movement="chaser", tag="cult_test")
        b = NPC(cx + CULT_HANDOFF_RANGE - 4, cy, "B", "cultist",
                movement="chaser", tag="cult_test")
        met = handoff_step(a, [a, b], scn, 1 / 30.0)
        check(met and a._handoff_t > 0 and b._handoff_t > 0,
              "hand-off: crossing scouts stop together")
        check(abs(a.facing[0] - 1.0) < 0.01,
              "hand-off: and face each other")
        for _ in range(int(CULT_HANDOFF_HOLD * 30) + 2):
            handoff_step(a, [a, b], scn, 1 / 30.0)
            handoff_step(b, [a, b], scn, 1 / 30.0)
        check(a._handoff_t <= 0 and a._handoff_cd > 0,
              "hand-off: the meeting ends and the cooldown holds")
        check(handoff_step(a, [a, b], scn, 1 / 30.0) is False,
              "hand-off: no immediate second meeting")
        c = NPC(cx, cy, "C", "cultist", movement="chaser", tag="cult_test")
        d = NPC(cx + 10, cy, "D", "cultist", movement="chaser",
                tag="cult_test")
        d._cult_state = "chase"
        check(handoff_step(c, [c, d], scn, 1 / 30.0) is False,
              "hand-off: a chasing peer is never met")
    finally:
        pygame.time.get_ticks = real_ticks

    # ---- §13: the stealth economy (TODO #5, 2026-07 playtest tuning) ----
    # Running past the cult must not dominate hiding: the speed ladder
    # holds (King > sprint > chase > walk > scout), sprint is conspicuous,
    # and an awake cultist grabs at arm's reach.
    print("[13] stealth economy: the ladder, sprint tell, arm's reach")
    from systems.config import (CULT_CHASE_MULT, CULT_GRAB_REACH,
                                SUS_SPRINT_MULT, PLAYER_SPRINT_MULT)
    from systems.stealth import detection_score
    ge = new_game()
    ge.load_scene_now("brimley", "default")
    tick(ge, 10)
    clear_cult(ge)
    open_field(ge)
    walk = ge.player.speed
    sprint = walk * PLAYER_SPRINT_MULT
    chase = 0.95 * 60 * CULT_CHASE_MULT          # the surface regular
    scout = 0.95 * 60
    check(scout < walk < chase < sprint,
          f"ladder: scout {scout:.0f} < walk {walk:.0f} < chase "
          f"{chase:.1f} < sprint {sprint:.0f}")
    check(1.0 * 60 * CULT_CHASE_MULT < sprint,
          "ladder: the fastest underground chaser stays under sprint")
    check(CULT_GRAB_REACH > 22,
          "reach: the grab reaches past the old bare contact")
    # Sprint is conspicuous: same geometry, higher score while sprinting.
    ge.player.hidden = None
    ge.player.sprint_active = False
    n = plant(ge, 100)
    n.facing = (1.0, 0.0)
    ge.player.x, ge.player.y = n.x + 100, n.y
    s_walk = detection_score(ge.scene, n.x, n.y, n.facing, ge.player, 180.0)
    ge.player.sprint_active = True
    s_run = detection_score(ge.scene, n.x, n.y, n.facing, ge.player, 180.0)
    ge.player.sprint_active = False
    check(s_walk > 0 and abs(s_run - min(1.0, s_walk * SUS_SPRINT_MULT))
          < 1e-6, f"sprint tell: score {s_walk:.2f} -> {s_run:.2f} in LOS")
    # An awake SCOUT at arm's reach grabs in the open: the first grab of
    # the run is THE TALK (the tick helper pages it), which proves the
    # reach fired without ending the run.
    check(not ge.save.flag("cult_talk_given"), "reach: fresh run, no talk yet")
    n._cult_state = "scout"
    n._suspicion = 0.0
    n.x, n.y = ge.player.x + 26, ge.player.y
    for _ in range(6):
        tick(ge, 1)
        n.x, n.y = ge.player.x + 26, ge.player.y
        if ge.save.flag("cult_talk_given"):
            break
    check(ge.save.flag("cult_talk_given"),
          "reach: brushing an awake scout at 26px fires the grab (the Talk)")

    # ---- §14: river stones (TODO #5, the distraction verb) --------------
    # A thrown stone is a placed noise event: it spends from the pocket,
    # flies, lands, and its clatter turns an idle scout -- but it can
    # never divert a sighting-born search (loud sits under the pull), and
    # a rooted enclosed hide cannot throw at all.
    print("[14] river stones: the clatter routes a scout, never a search")
    from systems.config import NOISE_SEARCH_PULL
    gs = new_game()
    gs.load_scene_now("brimley", "default")
    tick(gs, 10)
    clear_cult(gs)
    open_field(gs)
    gs.player.inventory.add("stone", 2)
    n = plant(gs, 150)
    n._cult_state = "scout"
    n._suspicion = 0.0
    pin = (gs.player.x + 150, gs.player.y)      # earshot, out of reach
    n.x, n.y = pin
    gs.look.aim = 0.0                            # throw east, toward him
    gs._throw_stone()
    check(gs.player.inventory.count("stone") == 1,
          "stones: the throw spends one")
    check(len(gs._stones) == 1, "stones: it flies")
    for _ in range(90):
        tick(gs, 1)
        n.x, n.y = pin
        if n._cult_state == "investigate":
            break
    check(not gs._stones, "stones: it lands inside the range budget")
    check(n._cult_state == "investigate",
          "stones: the clatter turns the idle scout")
    # A sighting-born search holds through a stone.
    n._cult_state = "search"
    n._cult_state_t = 8.0
    n._last_seen_pos = pin
    n._noise_loud = NOISE_SEARCH_PULL
    n._sweep_list = []
    gs._throw_stone()
    for _ in range(60):
        tick(gs, 1)
        if not gs._stones:
            break
    tick(gs, 3)
    check(n._cult_state == "search",
          "stones: a sighting-born search is never diverted")
    # A rooted enclosed hide cannot throw.
    gs.player.hidden = "under"
    gs.player.inventory.add("stone", 1)
    k0 = gs.player.inventory.count("stone")
    gs._throw_stone()
    check(gs.player.inventory.count("stone") == k0 and not gs._stones,
          "stones: a rooted enclosed hide cannot throw")
    gs.player.hidden = None
    # A stone THROUGH A WINDOW: the loud tier. Two claims, each on its own
    # FRESH game so a carried cultist can never scramble the beat.
    # (1) the throw smashes the pane -> the run ledger + the broken set.
    from scenes.base import _WINDOW_CHARS
    gg = new_game()
    gg.load_scene_now("brimley", "default")
    tick(gg, 10)
    # Clear ALL npcs, not just the cult: a wandering homebody local is a
    # solid body that can step into the throw's path and stop the stone
    # short of the pane (is_solid_at counts solid NPCs) -- realistic, but
    # it makes a mechanic test flaky. The throw mechanic needs no NPCs.
    gg.scene.npcs = []
    win = None
    for wy_ in range(gg.scene.h):
        for wx_ in range(gg.scene.w):
            if gg.scene.objects[wy_][wx_] not in _WINDOW_CHARS:
                continue
            bx_ = wx_ * TILE + 16
            by_ = (wy_ + 2) * TILE + 16      # 2 south: the throw approach
            if not gg.scene.is_solid_at(bx_, by_):
                win = (wx_, wy_, bx_, by_)
                break
        if win:
            break
    check(win is not None, "glass: brimley offers a window with a clear approach")
    wx_, wy_, bx_, by_ = win
    gg.player.x, gg.player.y = bx_, by_
    gg.player.hidden = None
    gg.look.aim = -math.pi / 2               # throw north, at the pane
    gg.player.inventory.add("stone", 1)
    gg._throw_stone()
    for _ in range(60):
        tick(gg, 1)
        if not gg._stones:
            break
    check((wx_, wy_) in getattr(gg.scene, "_broken_windows", set()),
          "glass: the pane breaks and joins the scene's broken set")
    led = gg.save.arg("broken_windows", {}) or {}
    check([wx_, wy_] in led.get("brimley", []),
          "glass: the break is written to the run ledger")
    # (2) the loudness claim, tested straight on the noise bus (no throw,
    # so no chase/grab in play): a GLASS_LOUD event over the searcher
    # pull re-tasks a searcher that an ordinary stone (STONE_LOUD) could
    # not divert.
    from systems.config import GLASS_LOUD, GLASS_REACH, STONE_LOUD
    check(STONE_LOUD <= NOISE_SEARCH_PULL < GLASS_LOUD,
          "glass: only the glass tier clears the searcher-pull bar")
    gg2 = new_game()
    gg2.load_scene_now("brimley", "default")
    tick(gg2, 10)
    clear_cult(gg2)
    open_field(gg2)
    ng = plant(gg2, 90)
    ng._cult_state = "search"
    ng._cult_state_t = 20.0
    src = (gg2.player.x + 120, gg2.player.y)
    ng._last_seen_pos = src
    ng._noise_loud = NOISE_SEARCH_PULL
    ng._sweep_list = []
    ng._sweep_i = 0
    ng.x, ng.y = src
    gg2.scene.emit_noise(src[0], src[1], STONE_LOUD, kind="stone")
    for _ in range(4):
        ng.x, ng.y = src
        tick(gg2, 1)
    check(ng._cult_state == "search",
          "glass: an ordinary stone cannot divert the search")
    gg2.scene.emit_noise(src[0], src[1], GLASS_LOUD, kind="glass",
                         reach=GLASS_REACH)
    for _ in range(4):
        ng.x, ng.y = src
        tick(gg2, 1)
    check(ng._cult_state == "investigate",
          "glass: the smash diverts even a sighting-born search")
    # The dead well: a stone over the lip spends one and the shaft's
    # rattle turns a scout across the square. No landing ever sounds.
    gw = new_game()
    gw.load_scene_now("brimley", "default")
    tick(gw, 10)
    clear_cult(gw)
    gw.save.set_flag("well_examined", True)
    wpx, wpy = gw.scene._well_pos
    gw.player.x, gw.player.y = wpx, wpy + 20
    gw.player.hidden = None
    gw.player.inventory.add("stone", 1)
    m = plant(gw, 200)
    m._cult_state = "scout"
    m._suspicion = 0.0
    mpin = (wpx + 200, wpy)
    m.x, m.y = mpin
    press_e(gw)
    check(gw.player.inventory.count("stone") == 0,
          "well: the drop spends the stone")
    for _ in range(60):
        tick(gw, 1)
        m.x, m.y = mpin
        if m._cult_state == "investigate":
            break
    check(m._cult_state == "investigate",
          "well: the shaft's rattle turns a scout across the square")

    # The under-bridge hide: a real enclosed hide, and a cultist crossing
    # the deck overhead knocks (dressing only -- it must NEVER route the
    # searcher to the player below).
    gb = new_game()
    gb.load_scene_now("brimley", "default")
    tick(gb, 10)
    clear_cult(gb)
    check(getattr(gb.scene, "_bridge_hide_px", None) is not None
          and gb.scene._bridge_hide_px in [(h[0], h[1])
                                           for h in gb.scene.hide_spots],
          "bridge: the under-bridge hide is a registered enclosed hide")
    bhx, bhy = gb.scene._bridge_hide_px
    gb.player.x, gb.player.y = bhx, bhy
    gb.player.hidden = "under"
    x0, x1, y0, y1 = gb.scene._bridge_deck_px
    b = plant(gb, 40)
    b._cult_state = "scout"
    b._suspicion = 0.0
    b.x, b.y = (x0 + x1) / 2, (y0 + y1) / 2          # up on the deck
    gb._bridge_dust = 0.0
    for _ in range(40):
        tick(gb, 1)
        b.x, b.y = (x0 + x1) / 2, (y0 + y1) / 2
    check(gb._bridge_dust > 0.0,
          "bridge: a tread on the deck raises the dust/knock tell")
    check(b._cult_state == "scout",
          "bridge: the crosser never routes to the hidden player below")

    # ---- §15: interior doors (2026-07) ---------------------------------
    print("[15] interior doors: shut blocks body+sight, open sees through, "
          "a shut door breaks the chase")
    from scenes.base import Scene
    # a wall dividing a top room from a bottom room, two door gaps in it
    o = ["WWWWWW", "W....W", "W....W", "WW.W.W",
         "W....W", "W....W", "WWWWWW"]
    sd = Scene("doortest", ["=" * 6] * 7, o)
    sd.add_inner_door(2, 3, "plank")
    sd.add_inner_door(4, 3, "bars")
    dx, dy = 2 * TILE + 16, 3 * TILE + 16
    check(sd.is_solid_at(dx, dy) and sd.blocks_sight(dx, dy)
          and not sd._nav_solid_at(dx, dy),
          "doors: a shut plank door is solid + blocks sight, nav routes through")
    sd._inner_doors[(2, 3)]["open"] = True
    check(not sd.is_solid_at(dx, dy) and not sd.blocks_sight(dx, dy),
          "doors: an open door passes the body and the sight cone")
    check(sd.is_solid_at(4 * TILE + 16, 3 * TILE + 16)
          and not sd.blocks_sight(4 * TILE + 16, 3 * TILE + 16),
          "doors: a shut BARS door blocks the body but you see through it")
    # the stealth payoff: shutting the plank door breaks the LOS across it
    a0 = (2 * TILE + 16, 1 * TILE + 16)          # top room
    a1 = (2 * TILE + 16, 5 * TILE + 16)          # bottom room, past the door
    sd._inner_doors[(2, 3)]["open"] = True
    open_los = sd.clear_sight_line(a0[0], a0[1], a1[0], a1[1])
    sd._inner_doors[(2, 3)]["open"] = False
    shut_los = sd.clear_sight_line(a0[0], a0[1], a1[0], a1[1])
    check(open_los and not shut_los,
          "doors: shutting the door breaks the line of sight across it")
    was = sd._inner_doors[(2, 3)]["open"]
    sd.toggle_nearest_inner_door(dx, dy)
    check(sd._inner_doors[(2, 3)]["open"] != was,
          "doors: the player E-toggle flips the nearest door")

    # ---- §16: thin-slab walls (2026-07) --------------------------------
    print("[16] thin-slab walls: bands thin two-sided partitions AND the shell, "
          "connect flush at junctions, and collision+sight+nav agree")
    import scenes.terrain as _terr
    from scenes import load_scene
    # synthetic scene: a vertical partition (col 2) between two rooms + a shell.
    so = ["WWWWW", "W.W.W", "W.W.W", "W.W.W", "WWWWW"]
    ss = Scene("slabtest", ["=" * 5] * 5, so)
    _saved_slab = _terr._SLAB_SCENES
    _terr._SLAB_SCENES = frozenset(_saved_slab | {"slabtest"})
    try:
        foot = _terr._wall_slab(ss, 2, 2)     # floor E+W, wall N+S -> centre X
        check(isinstance(foot, list) and len(foot) == 1
              and foot[0][1] == 0.0 and foot[0][3] == TILE
              and 0.0 < foot[0][0] and foot[0][2] < TILE,
              "slab: a two-sided vertical partition is one centred band (thin X)")
        core = (2 * TILE + TILE // 2, 2 * TILE + TILE // 2)
        gap = (2 * TILE + 2, 2 * TILE + TILE // 2)      # lx=2, in the W gap
        check(ss.is_solid_at(*core) and ss.blocks_sight(*core),
              "slab: the band core is solid + blocks sight")
        check(not ss.is_solid_at(*gap) and not ss.blocks_sight(*gap),
              "slab: the thinned strip passes the body AND the sight cone")
        check(not ss.nav_grid()[2][2],
              "slab: the nav grid marks a slab tile solid (routes around)")
        # the SHELL now thins too, hugging the EXTERIOR edge (outer face stays
        # on the building silhouette, no floor lip; the wall thins inward): the
        # void-side edge is solid, the interior side passes.
        sfoot = _terr._wall_slab(ss, 0, 2)              # W shell, exterior is W
        check(isinstance(sfoot, list)
              and ss.is_solid_at(0 * TILE + 2, 2 * TILE + TILE // 2)
              and not ss.is_solid_at(0 * TILE + TILE - 2, 2 * TILE + TILE // 2),
              "slab: the shell hugs the exterior edge, thinning inward")
        # a junction (col-2 partition meets the bottom shell) connects FLUSH to
        # the run above -- the shared centreline pixel is solid on both sides.
        yb = 4 * TILE                                   # boundary row3|row4
        check(ss.is_solid_at(2 * TILE + TILE // 2, yb - 1)
              and ss.is_solid_at(2 * TILE + TILE // 2, yb + 1),
              "slab: a run connects flush across a junction (no notch)")
        # MATERIAL styles (Phase 1): thickness/round/rough come from _WALL_STYLES
        # per scene. A rough material roughens the DRAWN outline but leaves the
        # collision bands identical to a smooth material of the same thickness
        # (rough is draw-only; collision/sight/nav read the square bands).
        _terr._WALL_STYLES["_rufftest"] = {"thick": 0.5, "round": 0.5, "rough": 2.5}
        _terr._SLAB_STYLE["slabtest"] = "_rufftest"
        _terr._ROUND_POLY_CACHE.clear()
        r_bands, r_poly = _terr._wall_slab(ss, 2, 2), _terr._rounded_wall_poly(ss, 2, 2)
        _terr._SLAB_STYLE["slabtest"] = "plank"
        _terr._ROUND_POLY_CACHE.clear()
        s_bands, s_poly = _terr._wall_slab(ss, 2, 2), _terr._rounded_wall_poly(ss, 2, 2)
        check(r_bands == s_bands,
              "slab: a rough material leaves the collision bands unchanged (draw-only)")
        check(len(r_poly[0]) > len(s_poly[0]),
              "slab: a rough material jitters the drawn outline (more points)")
    finally:
        _terr._SLAB_SCENES = _saved_slab
        _terr._SLAB_STYLE.pop("slabtest", None)
        _terr._WALL_STYLES.pop("_rufftest", None)
        _terr._ROUND_POLY_CACHE.clear()
    check(any(_terr._wall_slab(load_scene("shop"), tx, ty)
              for ty in range(13) for tx in range(16)),
          "slab: the shipped shop pilot thins its walls (wired e2e)")
    check(_terr._wall_slab(sd, 0, 0) is None,
          "slab: a non-_SLAB_SCENES scene returns None (byte-identical)")

    # ---- ROCK (Phase 3, the mine): full-THICK draw, UNCHANGED tile collision --
    # A rock scene is styled for the DRAW (roughened outline) but stays FULL
    # thickness: it is deliberately NOT in _SLAB_SCENES, so collision/sight/nav
    # read the tile grid, unchanged. The point a THIN slab would thin away is
    # STILL solid here. Guards the "full-thick, draw-only rough" contract.
    rr = Scene("rocktest", ["=" * 5] * 5,
               ["WWWWW", "W.W.W", "W.W.W", "W.W.W", "WWWWW"])
    _saved_rock = _terr._ROCK_STYLE
    _terr._ROCK_STYLE = dict(_saved_rock)
    _terr._ROCK_STYLE["rocktest"] = "rock"
    _terr._ROUND_POLY_CACHE.clear()
    try:
        rfoot = _terr._wall_slab(rr, 2, 2)          # thick 1.0 -> the whole tile
        check(isinstance(rfoot, list) and any(
                  r[0] <= 0.0 and r[2] >= TILE and r[1] <= 0.0 and r[3] >= TILE
                  for r in rfoot),
              "rock: a rock wall band fills the whole tile (full-thick)")
        rpoly = _terr._rounded_wall_poly(rr, 2, 2)  # roughened DRAW outline
        check(rpoly is not None and len(rpoly[0]) > 4,
              "rock: the wall gets a roughened DRAW outline")
        gap = (2 * TILE + 2, 2 * TILE + TILE // 2)   # a slab would thin this away
        check(rr.is_solid_at(*gap) and rr.blocks_sight(*gap),
              "rock: the wall stays full-thick to collision + sight (tile grid)")
        check("rocktest" not in _terr._SLAB_SCENES,
              "rock: a rock scene is NOT a thin _SLAB_SCENES scene")
    finally:
        _terr._ROCK_STYLE = _saved_rock
        _terr._ROUND_POLY_CACHE.clear()
    check(_terr._wall_style(load_scene("well_passage"))
          is _terr._WALL_STYLES["rock"],
          "rock: the shipped mine (well_passage) renders the rock style")

    # ---- §17: the genset power link (TODO #21 first slice) --------------
    # A blackout kills the ELECTRIC fixtures in every layer at once: the
    # mechanical lit_at gate goes dark at the lamp, fire keeps burning,
    # and power comes back on its own when the timer drains.
    print("[17] power link: blackout kills electric light, fire survives, "
          "power returns")
    g = new_game()
    g.load_scene_now("shop")
    tick(g, 3)
    sc = g.scene
    lamp = next(d for d in sc.decorations if d.kind == "drop_bulb")
    wlamp = next(d for d in sc.decorations if d.kind == "wall_lamp")
    cand = next(d for d in sc.decorations if d.kind == "candle")
    # a spot only the hooded east wall_lamp reaches (inside its west fan,
    # clear of the counter's kerosene flame and the stockroom candle)
    fan_x, fan_y = wlamp.x - 40, wlamp.y
    check(sc.power_on and sc.lit_at(fan_x, fan_y),
          "power on: the wall lamp lights its fan")
    g._genset_down[sc.key] = 5.0
    tick(g, 2)
    check(not sc.power_on, "blackout: the scene's power_on drops")
    check(not sc.lit_at(fan_x, fan_y),
          "blackout: the electric lamp's fan goes mechanically dark")
    check(sc.lit_at(lamp.x, lamp.y),
          "blackout: the counter spot stays lit by the kerosene FLAME "
          "(fire is exempt)")
    check(sc.lit_at(cand.x, cand.y),
          "blackout: the stockroom candle still lights (fire is exempt)")
    check(getattr(lamp, "_powered", True) is False,
          "blackout: the fixture art reads unpowered (_powered False)")
    g._genset_down[sc.key] = 0.5
    tick(g, 60)
    check(sc.power_on and sc.lit_at(fan_x, fan_y),
          "recovery: the timer drains and the lamp lights again")
    # A BROKEN fixture (the 1-2 per room rule) never lights, even with
    # the genset running: the shop's dead mid-floor pendant.
    check(any(getattr(d, "kwargs", {}).get("broken")
              for d in sc.decorations if d.kind == "drop_bulb"),
          "broken: the shop carries its burned-out pendants")
    check(sc.power_on and not sc.lit_at(12 * TILE + 16, 6 * TILE + 16),
          "broken: a burned-out pendant's spot stays dark on full power")

    # ---- §18: the storm's STAGE -- ev-driven surface darkening (TODO #25) --
    # The daytime invariant: stage 0 is FULL DAY (no darkening, byte-identical),
    # and the gloom only ever deepens with the rot stage -- never a day cycle.
    from systems.config import STORM_DARK_GLOOM, STORM_STAGE_SCENES
    print("[18] storm stage: ev0 full day, gloom monotonic, Brimley staged")
    check(STORM_DARK_GLOOM[0] == 0,
          "storm stage: gloom is 0 at ev0 (full day, _draw_dark early-outs)")
    check(all(STORM_DARK_GLOOM[i] <= STORM_DARK_GLOOM[i + 1]
              for i in range(len(STORM_DARK_GLOOM) - 1)),
          "storm stage: gloom monotonic non-decreasing with the stage")
    check(len(STORM_DARK_GLOOM) == 4 and STORM_DARK_GLOOM[3] > 0,
          "storm stage: four stages, night by stage 3")
    check("brimley" in STORM_STAGE_SCENES,
          "storm stage: Brimley is a staged surface scene")

    # The storm dark is not a mechanic the PLAYER gets to use (maintainer
    # ruling, 2026-07: "darkness shouldn't hide you AT ALL"). It sets the
    # stage the storm will fill; it never conceals, and standing in a lamp
    # pool out here does not buy safety from the gaze either.
    from systems.stealth import concealment_factor
    g = new_game()
    g.load_scene_now("country_lane", "default")
    tick(g, 30)
    g.save.set_arg("evidence", [{"name": f"w{i}"} for i in range(3)])
    check(g.scene_gloom() > 0,
          "storm dark: by stage 3 the lane is genuinely dark")
    sc = g.scene
    spots = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(sc.h) for tx in range(sc.w)
             if not sc.is_solid_at(tx * TILE + 16, ty * TILE + 16)]
    lit_x, lit_y = next(p for p in spots if sc.lit_at(*p))
    dark_x, dark_y = next(p for p in spots if not sc.lit_at(*p))
    # NOT COVER: full night, unlit, flashlight off -- conceals nothing.
    g.player.x, g.player.y = dark_x, dark_y
    g.player.hidden = None
    g.flashlight_on = False
    tick(g, 2)
    check(concealment_factor(g.player) == 1.0,
          "storm dark: the outdoor night conceals nothing from the cult")
    # NOT A REFUGE EITHER: a yard-light pool does not stop the gaze.
    for _ in range(int((WATCHER_GRACE + WATCHER_SPAWN_BASE + 4) * 30)):
        g.player.x, g.player.y = lit_x, lit_y
        g.player.hidden = None
        g._tick_watchers(1 / 30.0)
        if g._watchers:
            break
    check(bool(g._watchers),
          "storm dark: Watchers open on you while you stand in a lamp pool")
    check(g._watcher_gaze > 0.0,
          "storm dark: and they HOLD you there (light is not cover)")

    # ---- §19: THE STORM as a MODE of the Watcher wave (TODO #25) ----------
    # Locks the maintainer's spec: Watchers do NOT stop at the gate, they BECOME
    # the storm; the cap lifts; units WALK at the player; light is the only
    # thing that stops them; they cannot touch or kill; and every dispel still
    # works. Out of storm, nothing changes.
    from systems.config import (STORM_MAX, STORM_GATE_EVIDENCE, STORM_UNIT_SPEED,
                                AMALGAM_CHANCE, WATCHER_MAX)
    print("[19] storm: one wave, two modes -- cap, approach, light, dispel")
    check(AMALGAM_CHANCE >= 0.85,
          "storm: the amalgam is the default skin now, the shroud is rare")
    g = new_game()
    g.load_scene_now("well_passage", "default")
    tick(g, 20)
    # Below the gate: the ordinary wave, capped, standing still.
    g.save.set_arg("evidence", [{"name": f"w{i}"}
                                for i in range(STORM_GATE_EVIDENCE - 1)])
    check(not g._storm_active(),
          "storm: below the gate there is no storm")
    # At the gate, in a dark room: the storm is up.
    g.save.set_arg("evidence", [{"name": f"w{i}"}
                               for i in range(STORM_GATE_EVIDENCE)])
    check(g._storm_active() and g.scene_gloom() > 0,
          "storm: at the gate, in the dark, a storm is up")
    check(STORM_MAX > WATCHER_MAX,
          "storm: the cap lifts above the Watcher max")
    # ...and the wave ACTUALLY uses it. The constant comparison above cannot
    # fail on a regression -- pinning `cap = WATCHER_MAX` in _tick_watchers left
    # it green -- so drive the real wave past the old ceiling.
    gc = new_game()
    gc.load_scene_now("well_passage", "default")
    tick(gc, 20)
    gc.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    csc = gc.scene
    cdark = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(2, csc.h - 2) for tx in range(2, csc.w - 2)
             if not csc.is_solid_at(tx * TILE + 16, ty * TILE + 16)
             and not csc.lit_at(tx * TILE + 16, ty * TILE + 16)]
    gc.player.x, gc.player.y = cdark[len(cdark) // 2]
    for _ in range(int(90 * 30)):
        gc.player.hidden = None
        gc._tick_watchers(1 / 30.0)
        if len(gc._watchers) > WATCHER_MAX:
            break
    check(len(gc._watchers) > WATCHER_MAX,
          f"storm: the live wave passes the Watcher cap "
          f"({len(gc._watchers)} units > {WATCHER_MAX})")
    # A safe room has no storm even at the gate (the refuge is load-bearing).
    g2 = new_game()
    g2.load_scene_now("bedroom", "default")
    tick(g2, 10)
    g2.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    check(not g2._storm_active(),
          "storm: a lit refuge never storms (gloom 0)")
    # --- the APPROACH. A unit walks at the player...
    sc = g.scene
    spots = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(2, sc.h - 2) for tx in range(2, sc.w - 2)
             if not sc.is_solid_at(tx * TILE + 16, ty * TILE + 16)]
    dark = [p for p in spots if not sc.lit_at(*p)]
    g.player.x, g.player.y = dark[0]
    g.player.hidden = None
    u = g._spawn_watcher() or (g._watchers[-1] if g._watchers else None)
    if u is None:                       # spawn geometry can miss; force one
        from entities.npc import NPC
        u = NPC(dark[-1][0], dark[-1][1], "", "amalgam", movement="storm",
                speed=STORM_UNIT_SPEED, no_prompt=True, solid=False)
        u.tag = "watcher"
        u.sprite_seed = 3
        sc.add_npc(u)
        g._watchers.append(u)
    g._sync_storm_mode(True)
    check(u.movement == "storm" and u.speed > 0,
          "storm: a live unit switches to the walking mode")
    # place it a way off, in the dark, and let it walk
    far = max(dark, key=lambda p: (p[0] - g.player.x) ** 2
              + (p[1] - g.player.y) ** 2)
    u.x, u.y = far
    d0 = math.hypot(u.x - g.player.x, u.y - g.player.y)
    for _ in range(240):
        u.update(1 / 30.0, sc, g.player)
    d1 = math.hypot(u.x - g.player.x, u.y - g.player.y)
    check(d1 < d0 - 8,
          f"storm: the unit closes on the player ({d0:.0f}px -> {d1:.0f}px)")
    # ...and STOPS at the light. Standing in a pool is the only safety.
    lit = [p for p in spots if sc.lit_at(*p)]
    if lit:
        g.player.x, g.player.y = lit[0]
        # put the unit just outside the pool, aimed in
        import math as _m
        for ang in range(0, 360, 15):
            ux = g.player.x + _m.cos(_m.radians(ang)) * 70
            uy = g.player.y + _m.sin(_m.radians(ang)) * 70
            if (not sc.is_solid_at(ux, uy) and not sc.lit_at(ux, uy)):
                u.x, u.y = ux, uy
                break
        held0 = math.hypot(u.x - g.player.x, u.y - g.player.y)
        for _ in range(240):
            u.update(1 / 30.0, sc, g.player)
        held1 = math.hypot(u.x - g.player.x, u.y - g.player.y)
        check(not sc.lit_at(u.x, u.y),
              "storm: the unit never steps into the light")
        check(held1 > 8.0,
              f"storm: light holds it off the player ({held1:.0f}px away)")
    # --- it cannot TOUCH you. Sit it on top of the player and tick the world.
    g.player.x, g.player.y = dark[0]
    u.x, u.y = g.player.x, g.player.y
    hp0 = g.player.hp
    dead0 = g.death_kind if hasattr(g, "death_kind") else None
    tick(g, 60)
    check(g.player.hp >= hp0 and g.state == "playing",
          "storm: a unit standing ON the player deals nothing (a scare)")
    # --- every DISPEL still works in a storm: light burns one caught in a pool.
    if lit:
        # a FRESH unit: the world ticks above may have swept or dispelled the
        # earlier one, and reusing it made this check depend on that.
        from entities.npc import NPC as _NPC
        w2 = _NPC(lit[0][0], lit[0][1], "", "amalgam", movement="storm",
                  speed=STORM_UNIT_SPEED, no_prompt=True, solid=False)
        w2.tag = "watcher"
        w2.sprite_seed = 5
        sc.add_npc(w2)
        g._watchers.append(w2)
        g._cursed = True
        w2.x, w2.y = lit[0]
        burned = False
        for _ in range(int((WATCHER_GAZE_DISPEL / (1 + WATCHER_LIGHT_BURN)
                            + 1.0) * 30)):
            w2.x, w2.y = lit[0]
            g._tick_watcher_gaze(1 / 30.0)
            if w2 not in g._watchers:
                burned = True
                break
        check(burned,
              "storm: light still BURNS a unit caught in a pool")
    # --- THE BEAM is a real barrier. Scene.lit_at only knows scene FIXTURES, so
    # testing against it alone left every lamp-less room (most of the mine, the
    # lost spaces, an unpowered building) with no safety in it at all -- while
    # the ruling is that during a storm light is the ONLY safety.
    gb = new_game()
    gb.load_scene_now("well_passage", "default")
    tick(gb, 20)
    gb.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    bsc = gb.scene
    bdark = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(2, bsc.h - 2) for tx in range(2, bsc.w - 2)
             if not bsc.is_solid_at(tx * TILE + 16, ty * TILE + 16)
             and not bsc.lit_at(tx * TILE + 16, ty * TILE + 16)]
    # Pick a player spot with a DARK, WALKABLE neighbour due south -- an earlier
    # version only checked the unit's spot was unlit and dropped it inside rock,
    # so the control ("it closes with the beam off") moved 0px and failed.
    home = None
    for px_, py_ in bdark:
        cand = (px_, py_ + 90)
        if (not bsc.is_solid_at(*cand) and not bsc.lit_at(*cand)
                and bsc.clear_sight_line(cand[0], cand[1], px_, py_)):
            home = ((px_, py_), cand)
            break
    assert home, "need a dark walkable pair for the beam check"
    (gb.player.x, gb.player.y), start = home
    gb.player.facing = (0, 1)
    gb.player.inventory.add("flashlight", 1)
    from entities.npc import NPC as _NPC3
    bu = _NPC3(start[0], start[1], "", "amalgam", movement="storm",
               speed=STORM_UNIT_SPEED, no_prompt=True, solid=False)
    bu.tag = "watcher"; bu.sprite_seed = 7
    bsc.add_npc(bu); gb._watchers.append(bu)
    # beam OFF: it closes (the spot is dark, nothing holds it)
    gb.flashlight_on = False
    gb._stamp_beam()
    d0 = math.hypot(bu.x - gb.player.x, bu.y - gb.player.y)
    for _ in range(120):
        bu.update(1 / 30.0, bsc, gb.player)
    closed = d0 - math.hypot(bu.x - gb.player.x, bu.y - gb.player.y)
    check(closed > 4.0,
          f"beam: with the light off a unit closes in the dark ({closed:.0f}px)")
    # beam ON, aimed at it: it is held, with no fixture anywhere near
    bu.x, bu.y = start
    gb.flashlight_on = True
    gb._stamp_beam()
    assert gb._flashlight_lit(), "the beam must actually be lit for this check"
    d1 = math.hypot(bu.x - gb.player.x, bu.y - gb.player.y)
    for _ in range(120):
        bu.update(1 / 30.0, bsc, gb.player)
    d2 = math.hypot(bu.x - gb.player.x, bu.y - gb.player.y)
    check(abs(d2 - d1) < 2.0,
          f"beam: the flashlight alone holds a unit off ({d1:.0f}px -> {d2:.0f}px)")

    # --- UNCAPPING THE POPULATION MUST NOT UNCAP THE THREAT. The gaze term and
    # the visibility FLOOR are both per-live-unit, so a lifted cap silently made
    # the storm the deadliest thing in the game: 22 units climbed the meter at
    # 1.1/s and pinned the floor at VIS_FLOOR_TOTAL_CAP, just under the King,
    # unclearably -- while the ruling is that regular units cannot touch or kill.
    from systems.config import (STORM_PRESS_UNITS, WATCHER_GAZE, WATCHER_FLOOR,
                                VIS_FLOOR_TOTAL_CAP)
    gp = new_game()
    gp.load_scene_now("well_passage", "default")
    tick(gp, 20)
    gp.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    psc = gp.scene
    pdark = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(2, psc.h - 2) for tx in range(2, psc.w - 2)
             if not psc.is_solid_at(tx * TILE + 16, ty * TILE + 16)
             and not psc.lit_at(tx * TILE + 16, ty * TILE + 16)]
    gp.player.x, gp.player.y = pdark[len(pdark) // 2]
    for i in range(STORM_MAX):
        pu = _NPC3(gp.player.x + 40 + i * 3, gp.player.y + 40, "", "amalgam",
                   movement="storm", speed=STORM_UNIT_SPEED,
                   no_prompt=True, solid=False)
        pu.tag = "watcher"; pu.sprite_seed = 20 + i
        psc.add_npc(pu); gp._watchers.append(pu)
    gp.player.hidden = None
    gp.visibility = 0.0
    gp._tick_watchers(1 / 30.0)
    check(gp._watcher_gaze <= STORM_PRESS_UNITS,
          f"press: at most {STORM_PRESS_UNITS} units press the meter "
          f"(gaze {gp._watcher_gaze:.0f} with {len(gp._watchers)} units)")
    gp._tick_visibility(1 / 30.0)
    check(gp._vis_floor < VIS_FLOOR_TOTAL_CAP - 0.05,
          f"press: a full storm does not pin the floor under the King "
          f"(floor {gp._vis_floor:.2f} vs cap {VIS_FLOOR_TOTAL_CAP})")

    # --- the flood must be SEEN. Storm units do not obey the sight cone: a
    # live 22-unit storm had 0 units pass it, so the whole thing was invisible.
    # Build the probe outright rather than reusing a live unit -- the earlier
    # version read g._watchers[-1] and SILENTLY SKIPPED both checks whenever the
    # wave happened to be empty, which is the one thing a guard must never do.
    from systems.config import STORM_SEE_RANGE
    from entities.npc import NPC as _NPC2
    su = _NPC2(0, 0, "", "amalgam", movement="storm", speed=STORM_UNIT_SPEED,
               no_prompt=True, solid=False)
    check(g.actor_smear_range(su) == STORM_SEE_RANGE,
          "storm: a storm unit stays sensed outside the sight cone")
    su.movement = "watch"
    check(g.actor_smear_range(su) == 0.0,
          "storm: a standing Watcher still obeys the cone outright")

    # --- and out of storm the wave is exactly as it was.
    g.save.set_arg("evidence", [{"name": "w0"}])
    check(not g._storm_active(), "storm: dropping below the gate ends it")
    g._sync_storm_mode(False)
    check(all(w.movement == "watch" and w.speed == 0.0 for w in g._watchers),
          "storm: units revert to standing still when it ends")

    # ---- §20: THE APEX -- the Mask that wears a unit (TODO #25) -----------
    # The maintainer's spec, end to end: it floats in, BECOMES an amalgam
    # (reusing its exact parts plus 2-3), pierces and ignores light, the axe/gun
    # destroy the HOST but not the Mask, it re-hosts and continues, and it leaves
    # when the player drops below the visibility threshold.
    from systems.config import (APEX_VIS_GATE, APEX_SPEED, APEX_CATCH_DIST,
                                APEX_EXTRA_LO, APEX_EXTRA_HI, APEX_MIGRATE_CD,
                                KING_ROAM_SPEED, PLAYER_SPRINT_MULT)
    from rendering.amalgam import assemble
    print("[20] apex: floats in, wears a host, survives the axe, leaves on vis")
    # It IS the King, so it moves at his speed -- above player sprint, the locked
    # ratio (error class 9): the apex cannot be outrun.
    check(APEX_SPEED == KING_ROAM_SPEED,
          "apex: moves at the King's own speed (it is Him)")
    check(APEX_SPEED * 60 > 84 * PLAYER_SPRINT_MULT,
          f"apex: faster than player sprint ({APEX_SPEED*60:.0f} vs "
          f"{84*PLAYER_SPRINT_MULT:.0f} px/s) -- cannot be outrun")
    # the host's deal is reused VERBATIM with parts appended
    base = assemble(4321)
    for ex in (APEX_EXTRA_LO, APEX_EXTRA_HI):
        grown = assemble(4321, extra=ex)
        check(grown[:len(base)] == base and len(grown) == len(base) + ex,
              f"apex: wears the host's exact deal plus {ex} more parts")
    ga = new_game()
    ga.load_scene_now("well_passage", "default")
    tick(ga, 20)
    ga.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    asc = ga.scene
    adark = [(tx * TILE + 16, ty * TILE + 16)
             for ty in range(2, asc.h - 2) for tx in range(2, asc.w - 2)
             if not asc.is_solid_at(tx * TILE + 16, ty * TILE + 16)
             and not asc.lit_at(tx * TILE + 16, ty * TILE + 16)]
    ga.player.x, ga.player.y = adark[len(adark) // 2]
    ga.player.hidden = None
    # BELOW the gate it does not come.
    ga.visibility = APEX_VIS_GATE - 0.2
    ga._tick_apex(1 / 30.0)
    check(getattr(ga, "_apex", None) is None,
          "apex: below the visibility gate the Mask does not come")
    # AT the gate it arrives, seeking.
    ga.visibility = min(0.95, APEX_VIS_GATE + 0.2)
    ga._tick_apex(1 / 30.0)
    check(ga._apex is not None and ga._apex["state"] == "seeking",
          "apex: at the gate it arrives, floating and seeking")
    # give it a unit to wear, and let it reach it
    from entities.npc import NPC as _NPC4
    prey = _NPC4(ga.player.x + 60, ga.player.y, "", "amalgam",
                 movement="storm", speed=STORM_UNIT_SPEED,
                 no_prompt=True, solid=False)
    prey.tag = "watcher"; prey.sprite_seed = 8181
    asc.add_npc(prey); ga._watchers.append(prey)
    for _ in range(600):
        ga._tick_apex(1 / 30.0)
        if ga._apex and ga._apex["state"] == "borne":
            break
    check(ga._apex is not None and ga._apex["state"] == "borne",
          "apex: it reaches a unit and BECOMES it")
    host = ga.apex_host()
    check(host is not None and getattr(host, "_apex", False),
          "apex: a host exists and is flagged as the bearer")
    check(prey not in asc.npcs,
          "apex: the amalgam it took is DELETED, not stacked on")
    check(host.sprite_seed == 8181,
          "apex: the host keeps the taken unit's own seed (its exact parts)")
    check(APEX_EXTRA_LO <= getattr(host, "_apex_extra", 0) <= APEX_EXTRA_HI,
          "apex: it adds 2-3 parts of its own")
    # LIGHT DOES NOT STOP IT. Sit it in a lit pool, aim the beam at it, and it
    # still closes -- unlike a regular unit, which both of those hold off.
    alit = [(tx * TILE + 16, ty * TILE + 16)
            for ty in range(2, asc.h - 2) for tx in range(2, asc.w - 2)
            if asc.lit_at(tx * TILE + 16, ty * TILE + 16)
            and not asc.is_solid_at(tx * TILE + 16, ty * TILE + 16)]
    # Needs a LIT player spot with a CLEAR walkable line to stand the apex on --
    # dropping it 100px south blind put it against rock and it slid 20px of a
    # possible 350, which reads as "the light held it" and is not the same thing.
    apair = None
    for lx, ly in alit:
        for off in (100.0, 84.0, 120.0):
            cand = (lx, ly + off)
            if (not asc.is_solid_at(*cand)
                    and asc.clear_sight_line(cand[0], cand[1], lx, ly)):
                apair = ((lx, ly), cand, off)
                break
        if apair:
            break
    if apair:
        (ga.player.x, ga.player.y), astart, d0 = apair
        ga.player.facing = (0, 1)
        ga.player.inventory.add("flashlight", 1)
        ga.flashlight_on = True
        ga._stamp_beam()
        assert ga._flashlight_lit(), "beam must be lit for this check"
        assert asc.lit_at(ga.player.x, ga.player.y), "player must stand in light"
        host.x, host.y = astart
        for _ in range(90):
            host.update(1 / 30.0, asc, ga.player)
        d1 = math.hypot(host.x - ga.player.x, host.y - ga.player.y)
        # Must reach CONTACT range, not merely "closer": a d0-40 threshold
        # passed even with a light probe bolted on, because the apex simply
        # stopped at the pool's edge, which is well inside that margin.
        check(d1 <= APEX_CATCH_DIST,
              f"apex: light and the beam do NOT hold it off -- reaches contact "
              f"({d0:.0f} -> {d1:.0f}px, catch at {APEX_CATCH_DIST:.0f})")
        # the contrast that gives it meaning: a REGULAR unit is held by the same
        # light the apex walks through.
        reg = _NPC4(astart[0], astart[1], "", "amalgam", movement="storm",
                    speed=STORM_UNIT_SPEED, no_prompt=True, solid=False)
        for _ in range(90):
            reg.update(1 / 30.0, asc, ga.player)
        dreg = math.hypot(reg.x - ga.player.x, reg.y - ga.player.y)
        check(dreg > d1 + 20,
              f"apex: a regular unit IS held by that same light "
              f"(unit {dreg:.0f}px vs apex {d1:.0f}px)")
    # THE AXE KILLS THE HOST, NOT THE MASK.
    ga._dispel_watcher(host, reason="axe")
    check(ga._apex is not None and ga._apex["state"] == "seeking",
          "apex: killing the host does not kill the Mask -- it seeks again")
    check(host not in asc.npcs, "apex: the host body is gone")
    check(ga._apex["cd"] > 0.0,
          "apex: re-hosting is on a cooldown (driving it off must cost it time)")
    # it CONTINUES: give it another unit and it takes that one too
    prey2 = _NPC4(ga.player.x + 70, ga.player.y, "", "amalgam",
                  movement="storm", speed=STORM_UNIT_SPEED,
                  no_prompt=True, solid=False)
    prey2.tag = "watcher"; prey2.sprite_seed = 9292
    asc.add_npc(prey2); ga._watchers.append(prey2)
    for _ in range(900):
        ga._tick_apex(1 / 30.0)
        if ga._apex and ga._apex["state"] == "borne":
            break
    check(ga._apex is not None and ga._apex["state"] == "borne",
          "apex: it re-hosts on another amalgam and continues the assault")
    # ONE IMPOSSIBLE THING AT A TIME: the roaming King does not also walk.
    # Put a King in the room FIRST -- asserting `_king is None` after a bare
    # tick was vacuous, since he does not spawn in a single tick anyway.
    kdummy = _NPC4(ga.player.x + 200, ga.player.y, "", "yellow_king",
                   movement="chaser", speed=KING_ROAM_SPEED,
                   no_prompt=True, solid=False)
    kdummy._birth = 1.0
    asc.add_npc(kdummy)
    ga._king = kdummy
    check(ga.apex_host() is not None, "apex: (a host is worn for this check)")
    ga._tick_king_roam(1 / 30.0)
    check(ga._king is None and kdummy not in asc.npcs,
          "apex: the roaming King stands down while the Mask is worn")
    # THE CATCH IS ITS OWN, NOT THE KING'S CARD. The apex used to fire
    # _trigger_death("king"), which played THE UNFOLDING's throat-swallow -- the
    # art of the very body the storm replaces. Maintainer: do not use the
    # existing death card. This asserts the apex death never reaches it.
    import rendering.king_unfold as _ku
    gd = new_game()
    gd.load_scene_now("well_passage", "default")
    tick(gd, 20)
    gd.save.set_arg("evidence", [{"name": f"w{i}"}
                                 for i in range(STORM_GATE_EVIDENCE)])
    dsc = gd.scene
    dspots = [(tx * TILE + 16, ty * TILE + 16)
              for ty in range(3, dsc.h - 3) for tx in range(3, dsc.w - 3)
              if not dsc.is_solid_at(tx * TILE + 16, ty * TILE + 16)]
    gd.player.x, gd.player.y = dspots[len(dspots) // 2]
    gd.player.hidden = None
    gd.visibility = min(0.95, APEX_VIS_GATE + 0.2)
    dprey = _NPC4(gd.player.x + 40, gd.player.y, "", "amalgam",
                  movement="storm", speed=STORM_UNIT_SPEED,
                  no_prompt=True, solid=False)
    dprey.tag = "watcher"; dprey.sprite_seed = 4242
    dsc.add_npc(dprey); gd._watchers.append(dprey)
    for _ in range(3000):
        gd._tick_apex(1 / 30.0)
        dh = gd.apex_host()
        if dh is not None:
            dh.update(1 / 30.0, dsc, gd.player)
        if gd._death_kind is not None:
            break
    check(gd._death_kind == "apex",
          f"apex: the catch fires its OWN death kind, not the King's "
          f"(got {gd._death_kind!r})")
    # ...and drawing that card must not touch the Unfolding art at all.
    calls = []
    _real = _ku.draw_unfold_catch
    _ku.draw_unfold_catch = lambda *a, **k: calls.append(1)
    import systems.render_mixin as _rm
    _real_rm = getattr(_rm, "draw_unfold_catch", None)
    if _real_rm is not None:
        _rm.draw_unfold_catch = lambda *a, **k: calls.append(1)
    try:
        for tstep in (0.1, 0.6, 1.4, 2.9):
            gd._death_t = tstep
            gd._draw_death_screen()
    finally:
        _ku.draw_unfold_catch = _real
        if _real_rm is not None:
            _rm.draw_unfold_catch = _real_rm
    check(not calls,
          f"apex: its death card never draws the Unfolding catch "
          f"({len(calls)} call(s))")

    # AND IT LEAVES when the player drops below the threshold.
    ga.visibility = APEX_VIS_GATE - 0.25
    ga._tick_apex(1 / 30.0)
    check(getattr(ga, "_apex", None) is None,
          "apex: below the vis threshold it withdraws entirely")
    check(not any(getattr(n, "_apex", False) for n in asc.npcs),
          "apex: and takes its host body with it")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES")
        return 1
    print("All stealth checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
