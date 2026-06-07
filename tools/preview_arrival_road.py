"""Headless preview of the arrival_road under the LIVE tilt camera.

Boots a real Game, loads arrival_road, and renders draw_world() from a few
player positions so we can confirm the infinite-corridor read:
  - on the BAND looking NORTH (should be endless forest + paved road, no car /
    sign / dirt path anywhere up the runway, idle King at the vanishing point);
  - in the southern ARRIVAL zone (the car, the BRIMLEY sign, the E-W crossing
    render ONCE here and never tile north).

    python tools/preview_arrival_road.py   -> /tmp/arrival_road.png
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
from scenes.base import TILE


def boot():
    from systems.game import Game
    g = Game()
    g.save.new()
    g._start_play()
    return g


def shot(g, tile_xy, label, aim=(0, -1)):
    g.load_scene_now("arrival_road")
    # arm the idle King: he shows on the band before the gate
    g.player.x = tile_xy[0] * TILE + TILE // 2
    g.player.y = tile_xy[1] * TILE + TILE // 2
    g.player.facing = aim
    try:
        g.look.aim = math.atan2(aim[1], aim[0])   # heading in radians
    except Exception:
        pass
    # idle-King tick so _idle_king populates if on the band
    try:
        g._tick_idle_king()
    except Exception:
        pass
    g._update_camera(snap=True)
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    g.draw_world()
    font = pygame.font.SysFont("monospace", 14)
    surf.blit(font.render(label, True, (240, 240, 120)), (8, 8))
    ik = getattr(g, "_idle_king", None)
    surf.blit(font.render(f"idle_king={ik is not None}", True, (240, 240, 120)),
              (8, 26))
    return surf.copy()


def main():
    g = boot()
    shots = [
        ((7, 20), "ON BAND row20, looking NORTH"),
        ((7, 12), "ON BAND row12, looking NORTH"),
        ((7, 50), "ARRIVAL zone row50, looking NORTH"),
        ((7, 60), "ARRIVAL zone row60 (by car/sign), NORTH"),
        ((7, 60), "ARRIVAL zone row60, looking SOUTH", (0, 1)),
    ]
    frames = [shot(g, t, lbl, *(rest or [])) for t, lbl, *rest in shots]
    for i, f in enumerate(frames):
        pygame.image.save(f, f"/tmp/arrival_{i}.png")
        print(f"wrote /tmp/arrival_{i}.png")


if __name__ == "__main__":
    main()
