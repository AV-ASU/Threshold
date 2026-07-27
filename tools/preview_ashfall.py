"""Headless preview of the ashfall overlay (DESIGN.md §2).

Boots a Game, forces an evidence count (-> infest stage), loads a scene,
fills the ash field, and renders draw_world to a PNG per case. Confirms the
gates too (Threshold stays clean). Run:

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python tools/preview_ashfall.py
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from systems.game import Game


def boot(evidence_n, scene_key):
    g = Game()
    g.save.new()
    g._start_play()
    g.save.set_arg("evidence", [f"ev{i}" for i in range(evidence_n)])
    g.load_scene_now(scene_key)
    g.state = "playing"
    return g


def fill_and_draw(g, frames=600, out="ash.png"):
    dt = 1 / 60.0
    for _ in range(frames):
        g._tick_ashfall(dt)
    g.draw_world()
    pygame.image.save(g.screen, out)
    return len(g._ashfall_parts)


CASES = [
    (1, "store_row", "ashfall_surface_stage1.png"),
    (3, "store_row", "ashfall_surface_stage3.png"),
    (3, "works_scriptorium", "ashfall_underground_stage3.png"),
    (3, "threshold", "ashfall_threshold_stage3.png"),
]

if __name__ == "__main__":
    os.makedirs("/tmp/ash", exist_ok=True)
    for ev, key, name in CASES:
        g = boot(ev, key)
        out = f"/tmp/ash/{name}"
        n = fill_and_draw(g, out=out)
        print(f"ev={ev} scene={key:18s} motes={n:4d} -> {out}")
