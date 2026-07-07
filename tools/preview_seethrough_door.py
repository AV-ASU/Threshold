"""PROTOTYPE preview -- the SEE-THROUGH DOOR.

Boots a real Game headlessly, stands the player in a real interior looking at a
door, and composites the ACTUAL room beyond through the opening with the live
tilt camera. Captures the leaf swinging shut -> open so you can see the far room
resolve as the door opens, then a step across the sill.

    python tools/preview_seethrough_door.py      # -> /tmp/seethrough_door.png (+ .gif)

This is a design spike, not wired into the game. It proves the visual: a door
is an oriented hole you see the next room through, not a fade to black.
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
from scenes import load_scene
from rendering.seethrough_door import draw_seethrough_door

HOST = "lodge"              # the room you stand in
TARGET = "bedroom"          # the room beyond the door

CROP_W, CROP_H = 320, 250


def _face(g, heading):
    g.look.body = heading
    g.look.aim = heading
    g.look.cam_yaw = heading + math.pi / 2
    g.player.facing = (math.cos(heading), math.sin(heading))
    g.camera.yaw = g.look.cam_yaw
    g._update_camera(snap=True)


def _shot(g, label, font, out, focus, door):
    """Draw the host world, composite the door, keep a 2x crop near `focus`."""
    g.draw_world()
    draw_seethrough_door(g.screen, **door)
    bx, by = g.camera.project(*focus)
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2 - 40))
    crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * 2, CROP_H * 2))
    bar = pygame.Surface((CROP_W * 2, 26))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * 2, CROP_H * 2 + 26))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * 2))
    out.append(sheet)
    return panel


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()
    g.load_scene_now(HOST, "default")
    font = pygame.font.SysFont("monospace", 15)

    # Stand a door a couple tiles in front of the player, on an E-W wall seam
    # (so the leaf swings across the view). The far room is a real Scene.
    px, py = g.player.x, g.player.y
    fx, fy = px, py - 2.4 * TILE            # door ahead (north)
    target = load_scene(TARGET)
    anchor = target.spawns.get("default", (fx, fy))
    seam_dir = (1.0, 0.0)                   # wall runs E-W; door faces north

    _face(g, -math.pi / 2)                  # look north, at the door

    def door(swing):
        return dict(target=target, anchor_px=anchor, fx=fx, fy=fy,
                    camera=g.camera, t=1.0, seam_dir=seam_dir,
                    swing=swing, hinge="left", light=0.7)

    shots = []
    frames = []
    stages = [
        (0.0, "1. shut -- the leaf fills the frame, room hidden"),
        (0.30, "2. cracking -- the room past the sill resolves"),
        (0.62, "3. swinging open -- you see the actual bedroom beyond"),
        (1.0, "4. flat open -- one continuous space to step into"),
    ]
    for sw, label in stages:
        panel = _shot(g, label, font, shots, (fx, fy), door(sw))
        frames.append(panel)

    # 5. a step across the sill: move the camera forward, door swung open.
    g.player.y = fy + 0.2 * TILE
    _face(g, -math.pi / 2)
    _shot(g, "5. crossing the sill -- cross_fold, no fade", font, shots,
          (fx, fy - 0.6 * TILE), door(1.0))

    # Compose the still sheet (3 cols).
    pw, ph = shots[0].get_size()
    cols = 3
    rows = (len(shots) + cols - 1) // cols
    sheet = pygame.Surface((pw * cols, ph * rows))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, ((i % cols) * pw, (i // cols) * ph))
    pygame.image.save(sheet, "/tmp/seethrough_door.png")
    print("wrote /tmp/seethrough_door.png")

    # A smooth swing GIF if Pillow is around.
    try:
        from PIL import Image
        gif = []
        for k in range(24):
            sw = 0.5 - 0.5 * math.cos(math.pi * k / 23)   # ease 0->1
            g.draw_world()
            draw_seethrough_door(g.screen, **door(sw))
            bx, by = g.camera.project(fx, fy)
            cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
            cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2 - 40))
            crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
            raw = pygame.image.tostring(crop, "RGB")
            gif.append(Image.frombytes("RGB", (CROP_W, CROP_H), raw))
        gif = gif + gif[::-1]
        gif[0].save("/tmp/seethrough_door.gif", save_all=True,
                    append_images=gif[1:], duration=60, loop=0)
        print("wrote /tmp/seethrough_door.gif")
    except Exception as e:
        print("no gif:", e)


if __name__ == "__main__":
    main()
