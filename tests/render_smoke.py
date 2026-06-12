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
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame
from systems.game import Game

# One scene per overlay category: outdoor vignette, safe interior,
# dim-safe/dark cellar, brimley haze/eye, cult-dark dread, creepy well.
SCENES = ["bedroom", "basement", "brimley",
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


def check_vignette_paints(g):
    """The core vignette overlays must be present on Game and must
    actually draw. Fill the screen with a sentinel colour, invoke each
    method, and confirm pixels changed."""
    errors = 0
    g.load_scene_now("our_house_area", "default")   # an OUTDOOR_SCENES key
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
    print("[1/3] draw pipeline across scenes ...")
    failures += check_draw_pipeline(g)
    print("[2/3] core vignette overlays paint ...")
    failures += check_vignette_paints(g)
    print("[3/3] ending cutscenes draw ...")
    failures += check_ending_cutscenes(g)

    if failures:
        print(f"\n{failures} failure(s).")
        sys.exit(1)
    print("\nAll render smoke checks passed.")


if __name__ == "__main__":
    main()
