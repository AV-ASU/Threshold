"""Render smoke test.

The scene/spawn smoke test (smoke.py) never touches draw code, so a
broken overlay would pass it. This test drives the full draw pipeline
across representative scene types and threat states and fails on any
exception. It also checks that the relocated vignette overlays
(rendering/overlays.py:GameRenderMixin) are wired into Game and
actually paint -- a regression guard for the overlay extraction.

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

# One scene per overlay category: outdoor vignette/dusk, safe interior,
# dim-safe/dark cellar, mistlands haze/eye, cult-dark dread, creepy well.
SCENES = ["village", "bedroom", "basement", "mistlands",
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
            for flashlight in (False, True):
                g.player.flashlight_on = flashlight
                g.player.battery_charge = 100.0
                try:
                    g.draw_world()
                except Exception as e:
                    errors += fail(
                        f"draw_world {key} prox={prox} "
                        f"light={flashlight}: {e!r}")
    return errors


def check_vignette_paints(g):
    """The relocated overlays must be present on Game (via the mixin)
    and must actually draw. Fill the screen with a sentinel colour,
    invoke each method, and confirm pixels changed."""
    errors = 0
    g.load_scene_now("village", "default")   # an OUTDOOR_SCENES key
    g.pursuer_proximity = 0.95               # ensures dusk tint fires
    g.stillness_t = 10.0                     # tightest vignette level
    sentinel = (123, 45, 67)
    for meth in ("_draw_vignette", "_draw_outdoor_vignette",
                 "_draw_dusk_tint"):
        if not hasattr(g, meth):
            errors += fail(f"Game is missing {meth} (mixin not wired?)")
            continue
        g.screen.fill(sentinel)
        before = pygame.image.tostring(g.screen, "RGB")
        getattr(g, meth)()
        after = pygame.image.tostring(g.screen, "RGB")
        if before == after:
            errors += fail(f"{meth} drew nothing")
    return errors


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()

    failures = 0
    print("[1/2] draw pipeline across scenes ...")
    failures += check_draw_pipeline(g)
    print("[2/2] relocated vignette overlays paint ...")
    failures += check_vignette_paints(g)

    if failures:
        print(f"\n{failures} failure(s).")
        sys.exit(1)
    print("\nAll render smoke checks passed.")


if __name__ == "__main__":
    main()
