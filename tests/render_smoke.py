"""Render smoke test.

The scene/spawn smoke test (smoke.py) never touches draw code, so a
broken overlay would pass it. This test drives the full draw pipeline
across representative scene types and threat states and fails on any
exception. It also checks that the core vignette overlays are present
on Game and actually paint -- a regression guard for the render path.

Run from the project root with:

    python tests/render_smoke.py

SDL runs headless (dummy drivers), so no display is required.
"""
import os
import sys

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

# One scene per overlay category: outdoor vignette, safe interior,
# dim-safe/dark cellar, brimley haze/eye, cult-dark dread, creepy well.
SCENES = ["bedroom", "lodge_cellar", "brimley",
          "depths_hall", "well_bottom"]


def fail(msg):
    print(f"FAIL: {msg}")
    return 1


def check_draw_pipeline(g):
    """draw_world() across scenes x proximity tiers x flashlight, with
    no exceptions. draw_world is pure render, so repeated calls are
    safe and don't advance the simulation."""
    errors = 0
    for key in SCENES:
        try:
            g.load_scene_now(key, "default")
        except Exception as e:
            errors += fail(f"load {key}: {e!r}")
            continue
        for prox in (0.1, 0.5, 0.9):
            g.pursuer_proximity = prox
            g.dread_aperture = 1.0 - prox
            try:
                g.draw_world()
            except Exception as e:
                errors += fail(f"draw_world {key} prox={prox}: {e!r}")
    return errors


def check_phase6_and_doors(g):
    """Guards for the two DESIGN.md §10/§7 additions:

      * the ground HEIGHTFIELD (Phase 6, blind-spot hills): ground_z is 0 on a
        flat scene, rises on a hill, a crest occludes line of sight (but not
        from atop it), and the mesh renderer is a strict no-op at pitch 0;
      * the see-through door ACTOR sight-gating: a far-room figure draws through
        the aperture when it falls in the sight cone and is CULLED when it does
        not (so the empty room shows but a blind-spot lurker stays hidden)."""
    import math
    import numpy as np
    from rendering.heightfield import (build_heightfield, carve_channel,
                                       draw_ground_mesh)
    from rendering.camera import Camera
    from rendering.portal import _draw_aperture_actors
    from scenes.base import Scene
    from scenes import load_scene
    from entities.npc import NPC
    from constants import TILE
    errors = 0

    # -- heightfield: sampling + the crest sight primitive --------------------
    flat = Scene("hf_flat", ["." * 24] * 24)
    if flat.ground_z(160, 160) != 0.0:
        errors += fail("heightfield: a flat scene must read ground_z 0")
    if not flat.clear_sight_line(2 * TILE, 2 * TILE, 20 * TILE, 2 * TILE):
        errors += fail("heightfield: flat-scene LOS must stay clear (no-op)")
    hill = Scene("hf_hill", ["." * 24] * 24)
    hill.set_ground(build_heightfield(24, 24, [(12, 10, 5.5, 78.0)]))
    if hill.ground_z(12 * TILE + 16, 10 * TILE + 16) < 60.0:
        errors += fail("heightfield: the authored hill did not rise")
    if abs(hill.ground_z(2 * TILE, 2 * TILE)) > 0.01:
        errors += fail("heightfield: ground off the hill must stay flat")
    a = (4 * TILE + 16, 10 * TILE + 16)
    far = (20 * TILE + 16, 10 * TILE + 16)
    crest = (12 * TILE + 16, 10 * TILE + 16)
    if hill.clear_sight_line(a[0], a[1], far[0], far[1]):
        errors += fail("heightfield: a crest must block LOS across it")
    if not hill.clear_sight_line(crest[0], crest[1], far[0], far[1]):
        errors += fail("heightfield: from the crest you must see over")

    # -- carved river channel: a sunken bed + a bank crest that occludes -------
    chan = Scene("hf_chan", ["." * 24] * 24)
    banks = [(tx, 8.0, 2.0, 30.0) for tx in range(24)] + \
            [(tx, 15.0, 2.0, 30.0) for tx in range(24)]   # clear of the cut
    grid = build_heightfield(24, 24, banks)
    grid = carve_channel(24, 24, [(tx, 11.5) for tx in range(24)], 3.0, 60.0,
                         grid=grid)
    chan.set_ground(grid)
    if chan.ground_z(12 * TILE + 16, 11 * TILE + 16) > -20.0:
        errors += fail("channel: the river bed must sink below grade")
    if chan.ground_z(12 * TILE + 16, 8 * TILE + 16) < 10.0:
        errors += fail("channel: the banks must rise above grade")
    # a viewer up on the far bank cannot see a figure down on the channel bed
    bank = (12 * TILE + 16, 6 * TILE + 16)
    bed = (12 * TILE + 16, 11 * TILE + 16)
    if chan.clear_sight_line(bank[0], bank[1], bed[0], bed[1]):
        errors += fail("channel: the bank crest must hide the channel bed")

    # -- heightfield: the mesh renderer is a strict no-op at pitch 0 ----------
    surf0 = pygame.Surface((80, 80))
    surf0.fill((5, 6, 7))
    before = pygame.surfarray.array3d(surf0).copy()
    draw_ground_mesh(surf0, Camera(cam_x=12 * TILE, cam_y=16 * TILE,
                                   pitch=0.0, scale=1.6, origin=(40, 40)), hill)
    if not np.array_equal(before, pygame.surfarray.array3d(surf0)):
        errors += fail("heightfield: draw_ground_mesh must be a no-op at pitch 0")
    try:                                     # and it must draw under tilt w/o error
        draw_ground_mesh(pygame.Surface((640, 480)),
                         Camera(cam_x=12 * TILE, cam_y=16 * TILE,
                                pitch=math.radians(55), scale=1.6,
                                origin=(320, 300)), hill)
    except Exception as e:
        errors += fail(f"heightfield: draw_ground_mesh threw under tilt: {e!r}")

    # -- see-through door: the aperture actor pass is sight-gated -------------
    target = load_scene("bedroom")
    ax, ay = target.spawns.get("from_lodge", target.spawns["default"])
    lk = NPC(ax, ay - 0.4 * TILE, "F", "cultist", movement="idle")
    lk.facing = (0.0, 1.0)
    target.npcs = [lk]
    quad = [(360, 340), (440, 340), (440, 250), (360, 250)]
    pc = Camera(cam_x=ax, cam_y=ay + 96, pitch=math.radians(55), scale=1.6,
                origin=(400, 300))

    def _drawn(gate):
        s = pygame.Surface((800, 600), pygame.SRCALPHA)
        s.fill((0, 0, 0, 255))
        _draw_aperture_actors(s, target, (ax, ay), quad, (400, 295), pc,
                              (ax, ay), lambda x, y: gate, 1.0)
        arr = pygame.surfarray.array3d(s).astype(int)
        lit = arr.sum(axis=2) > 10
        outside = 0
        xs, ys = np.where(lit)
        for X, Y in zip(xs, ys):
            if not (360 <= X <= 440 and 250 <= Y <= 340):
                outside += 1
        return int(lit.sum()), outside

    seen, seen_out = _drawn(1.0)
    hidden, _ = _drawn(0.0)
    if seen < 100:
        errors += fail("door-gate: a seen far actor must draw through the aperture")
    if seen_out != 0:
        errors += fail("door-gate: the aperture figure must be clipped to the opening")
    if hidden != 0:
        errors += fail("door-gate: a blind-spot far actor must NOT draw through")
    return errors


def check_vignette_paints(g):
    """The core vignette overlays must be present on Game and must
    actually draw. Fill the screen with a sentinel colour, invoke each
    method, and confirm pixels changed."""
    errors = 0
    g.load_scene_now("lodge_yard", "default")   # an OUTDOOR_SCENES key
    g.visibility = 0.95                      # late-game -> tighter overlay fires
    g.stillness_t = 10.0                     # tightest vignette level
    sentinel = (123, 45, 67)
    for meth in ("_draw_vignette", "_draw_outdoor_vignette"):
        if not hasattr(g, meth):
            errors += fail(f"Game is missing {meth}")
            continue
        g.screen.fill(sentinel)
        before = pygame.image.tostring(g.screen, "RGB")
        getattr(g, meth)()
        after = pygame.image.tostring(g.screen, "RGB")
        if before == after:
            errors += fail(f"{meth} drew nothing")
    return errors


def check_ending_cutscenes(g):
    """_draw_ending across every authored ending at sampled timestamps.
    The endings are bespoke draw code (the SPREAD drive-out, the Carcosa
    tableau) that nothing else exercises; sample each at several points
    through its run and fail on any exception."""
    errors = 0
    for name in ("escape_alone", "seal_threshold", "rite_broken"):
        script = g._ENDING_SCRIPTS[name]
        total = sum(d for _, d in script)
        g._ending_active = name
        for frac in (0.02, 0.18, 0.34, 0.5, 0.66, 0.82, 0.97):
            t = total * frac
            ph, pt = len(script) - 1, max(0.0, script[-1][1] - 0.01)
            acc = t
            for i, (_, d) in enumerate(script):
                if acc < d:
                    ph, pt = i, acc
                    break
                acc -= d
            g._ending_phase, g._ending_phase_t = ph, pt
            try:
                g._draw_ending()
            except Exception as e:
                errors += fail(f"_draw_ending {name} t={t:.1f}: {e!r}")
    g._ending_active = None
    g._ending_phase = 0
    g._ending_phase_t = 0.0
    return errors


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()

    failures = 0
    print("[1/4] draw pipeline across scenes ...")
    failures += check_draw_pipeline(g)
    print("[2/4] core vignette overlays paint ...")
    failures += check_vignette_paints(g)
    print("[3/4] ending cutscenes draw ...")
    failures += check_ending_cutscenes(g)
    print("[4/4] heightfield + see-through door sight-gating ...")
    failures += check_phase6_and_doors(g)

    if failures:
        print(f"\n{failures} failure(s).")
        sys.exit(1)
    print("\nAll render smoke checks passed.")


if __name__ == "__main__":
    main()
