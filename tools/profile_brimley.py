"""Headless render profiler for the wrapped Brimley town (FPS work).

Boots a real Game headless, loads a scene under the live OBLIQUE camera (the
actual in-game view, not the flat pitch-0 capture), and times draw_world() over
many frames. Two camera regimes are measured because they exercise different
costs:

  * settled  -- camera held still (player standing, dialogue, menus). The
                warped-floor cache (_TILT_FLOOR_CACHE) should hit every frame.
  * panning  -- camera nudged each frame (player walking). The floor is rebuilt
                every frame; this is the worst case.

    python tools/profile_brimley.py                 # time brimley, both regimes
    python tools/profile_brimley.py --scene bedroom # a different scene
    python tools/profile_brimley.py --frames 400
    python tools/profile_brimley.py --cprofile      # cProfile hot-function dump

Reports ms/frame + the implied FPS for each regime. Run it before and after a
change to read the win.
"""
import os
import sys
import time
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import math
import pygame


def _boot_game(scene_key):
    from systems.game import Game
    g = Game()
    g.save.new()
    g._start_play()
    g.load_scene_now(scene_key)
    # Live oblique view (the real in-game camera), snapped to target framing.
    g._update_camera(snap=True)
    # Draw onto an offscreen surface so no display is needed.
    g.screen = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    return g


def _time_regime(g, frames, pan):
    """Return mean ms/frame over `frames` draw_world calls. When `pan`, nudge
    the camera every frame (defeats the floor cache); otherwise hold it still."""
    base_x, base_y = g.cam_x, g.cam_y
    # Warm-up: first frame builds caches (deco index, floor, standee cards).
    g.draw_world()
    t0 = time.perf_counter()
    for i in range(frames):
        if pan:
            g.cam_x = base_x + (i % 40) * 2.0
            g.cam_y = base_y + (i % 23) * 1.5
        g.draw_world()
    dt = time.perf_counter() - t0
    g.cam_x, g.cam_y = base_x, base_y
    return dt / frames * 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="brimley")
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--cprofile", action="store_true")
    args = ap.parse_args()

    g = _boot_game(args.scene)
    print(f"scene: {args.scene}  ({g.scene.w}x{g.scene.h}, "
          f"wrap_x={g.scene.wrap_x} wrap_y={g.scene.wrap_y}, "
          f"{len(g.scene.decorations)} decorations)")

    if args.cprofile:
        import cProfile
        import pstats
        base_x, base_y = g.cam_x, g.cam_y
        # Warm up first (build the floor bake, cards, deco index) so the
        # profile shows the steady state, not one-time cache construction.
        for i in range(30):
            g.cam_x = base_x + (i % 40) * 2.0
            g.cam_y = base_y + (i % 23) * 1.5
            g.draw_world()
        def _run():
            for i in range(args.frames):
                g.cam_x = base_x + (i % 40) * 2.0
                g.cam_y = base_y + (i % 23) * 1.5
                g.draw_world()
        pr = cProfile.Profile()
        pr.enable(); _run(); pr.disable()
        st = pstats.Stats(pr).sort_stats("cumulative")
        st.print_stats(25)
        return

    for label, pan in (("settled (cache hits)", False),
                       ("panning (worst case)", True)):
        ms = _time_regime(g, args.frames, pan)
        fps = 1000.0 / ms if ms > 0 else float("inf")
        print(f"  {label:22s}  {ms:6.2f} ms/frame   ~{fps:6.1f} fps")


if __name__ == "__main__":
    main()
