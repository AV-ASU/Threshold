"""Hero preview of the LIVE tilted (oblique 55) view -- the DEFAULT player
experience. Boots a real Game, loads a scene, tilts to ~55, and frames a chosen
spot at the real game zoom so props/dressing can actually be judged the way the
player sees them (the contact-sheet flat view is the legacy pitch-0 fallback).

Two columns per row: the CLEAN judging view (blind-spot fog disabled, so every
prop is visible) and the true PLAYER POV (fog on, player dropped at the target
facing `aim`, so only the forward sight cone reveals -- what actually ships).

    python tools/preview_tilt_scene.py SCENE [col,row] [--aim 0,1] [--zoom 1.4]
    python tools/preview_tilt_scene.py clearing 13,6
    python tools/preview_tilt_scene.py cornfield_path            # centre of scene
"""
import os
import sys
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.time.get_ticks = lambda: 9000
from constants import TILE, SCREEN_W, SCREEN_H
from systems.game import Game


def _shot(key, center_tile, aim, zoom, fog):
    g = Game()
    g.save.new()
    g._start_play()
    g._cam_pitch_target = math.radians(55)
    g.camera.pitch = math.radians(55)
    random.seed(7)
    g.load_scene_now(key)
    sc = g.scene
    if center_tile is None:
        center_tile = (sc.w // 2, sc.h // 2)
    cx = center_tile[0] * TILE + TILE // 2
    cy = center_tile[1] * TILE + TILE // 2
    if g.player:
        g.player.x, g.player.y = cx, cy
        g.player.facing = aim
    # frame on the target; bump zoom so props read at print size
    g.cam_x = cx - SCREEN_W // 2
    g.cam_y = cy - SCREEN_H // 2
    try:
        g._update_camera(snap=True)
    except Exception:
        pass
    g.camera.scale *= zoom
    if hasattr(g, "look"):
        try:
            # look.aim is a HEADING (radians), not a vector
            g.look.aim = math.atan2(aim[1], aim[0])
        except Exception:
            pass
    if not fog:
        g._sight = None
    random.seed(7)
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    g.screen = surf
    g.draw_world()
    return surf.copy()


def main():
    args = [a for a in sys.argv[1:]]
    key = args[0] if args else "clearing"
    center = None
    aim = (0, 1)
    zoom = 1.4
    rest = args[1:]
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--aim" and i + 1 < len(rest):
            ax, ay = rest[i + 1].split(",")
            aim = (float(ax), float(ay)); i += 2
        elif a == "--zoom" and i + 1 < len(rest):
            zoom = float(rest[i + 1]); i += 2
        elif "," in a:
            tx, ty = a.split(","); center = (int(tx), int(ty)); i += 1
        else:
            i += 1
    pygame.init()
    pygame.display.set_mode((1, 1))
    font = pygame.font.SysFont("monospace", 14)
    clean = _shot(key, center, aim, zoom, fog=False)
    pov = _shot(key, center, aim, zoom, fog=True)
    out = pygame.Surface((SCREEN_W * 2 + 12, SCREEN_H + 20))
    out.fill((10, 10, 12))
    out.blit(clean, (0, 0)); out.blit(pov, (SCREEN_W + 12, 0))
    out.blit(font.render(f"{key}  TILT 55  (fog off -- judging)", True,
                         (235, 235, 120)), (6, SCREEN_H + 2))
    out.blit(font.render("PLAYER POV  (blind-spot fog on)", True,
                         (160, 200, 235)), (SCREEN_W + 18, SCREEN_H + 2))
    path = f"/tmp/tiltscene_{key}.png"
    pygame.image.save(out, path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
