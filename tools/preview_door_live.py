"""LIVE verify -- see-through doors through the REAL game renderer.

Boots a Game in `house`, stands the player in front of each opted-in
see-through door, and captures draw_world() (which now renders the room beyond
through the doorway). Proves the feature works on real scene data, not a
standalone module.

    python tools/preview_door_live.py     # -> /tmp/door_live.png
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()

from constants import TILE, SCREEN_W, SCREEN_H
from systems.game import Game

CROP_W, CROP_H = 340, 260


def _face(g, heading):
    g.look.body = heading
    g.look.aim = heading
    g.look.cam_yaw = heading + math.pi / 2
    g.player.facing = (math.cos(heading), math.sin(heading))
    g.camera.yaw = g.look.cam_yaw
    g._update_camera(snap=True)


def _shot(g, label, font, out, focus):
    g.draw_world()
    bx, by = g.camera.project(*focus)
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2 - 30))
    crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * 2, CROP_H * 2))
    bar = pygame.Surface((CROP_W * 2, 26))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * 2, CROP_H * 2 + 26))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * 2))
    out.append(sheet)


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()
    g.load_scene_now("lodge", "default")
    font = pygame.font.SysFont("monospace", 15)
    shots = []

    for ch, name in (("B", "bedroom"), ("1", "clerk_room")):
        pos = g.scene.find_marker(ch)
        if pos is None:
            print("no marker", ch)
            continue
        tx, ty = pos
        fx, fy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        # Stand ~2 tiles on the room side of the door and look at it. The door
        # sits in a wall; figure which side is open floor.
        rdir = None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = fx + dx * 1.5 * TILE, fy + dy * 1.5 * TILE
            if not g.scene.is_solid_at(nx, ny):
                rdir = (dx, dy)
                break
        rdir = rdir or (0, 1)
        g.player.x = fx + rdir[0] * 1.8 * TILE
        g.player.y = fy + rdir[1] * 1.8 * TILE
        _face(g, math.atan2(-rdir[1], -rdir[0]))          # look back at the door
        _shot(g, f"door '{ch}' -> {name}: the room beyond, live", font,
              shots, (fx, fy))

        # Swing it wide via the real door-pulse anim + tick.
        g._pulse_door_at(fx, fy)
        for _ in range(8):
            g._tick_doors(0.05)
        _shot(g, f"door '{ch}' swung open ({name} resolves)", font,
              shots, (fx, fy))

    if not shots:
        print("no shots")
        return
    pw, ph = shots[0].get_size()
    cols = 2
    rows = (len(shots) + cols - 1) // cols
    sheet = pygame.Surface((pw * cols, ph * rows))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, ((i % cols) * pw, (i // cols) * ph))
    pygame.image.save(sheet, "/tmp/door_live.png")
    print("wrote /tmp/door_live.png")


if __name__ == "__main__":
    main()
