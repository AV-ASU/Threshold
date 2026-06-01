"""Wall-occlusion demo: player-locked 55deg camera, +/-45deg head-turn arc,
occluders fade when they swing between the camera and the player.

The player sits inside a ring of columns + a wall. As the camera's head-turn
sweeps the 90deg arc, any column/wall that comes between camera and player
fades so the player stays readable. Headless.

    python tools/preview_occlusion.py  -> /tmp/occlusion_demo.png (+ .gif)
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from rendering.camera import Camera
from rendering.solids import draw_solid, draw_box, draw_with_alpha
from rendering.skybox import draw_skybox
from rendering.occlusion import occluder_alpha

TILE = 32
COLS, ROWS = 11, 9
W, H = COLS * TILE, ROWS * TILE
CELL = (360, 320)
PITCH = 55

FLOOR_A = (40, 36, 33); FLOOR_B = (32, 29, 27)
WALL = {"top": (70, 60, 50), "side": (44, 38, 32), "dark": (28, 24, 20)}
COLUMN = {"body": (58, 54, 64), "lo": (30, 28, 36), "rim": (96, 96, 120)}
PLAYER = {"body": (150, 120, 70), "lo": (90, 70, 40), "rim": (210, 180, 120)}

COL_SECT = [(0, 9, 9), (8, 8, 8), (40, 8, 8), (48, 10, 10)]
PLR_SECT = [(0, 7, 7), (18, 6, 6), (28, 7, 7), (34, 5, 5)]

# player at room center; a ring of columns around them + a near wall
PLAYER_TILE = (5, 4)
COLUMNS = [(3, 3), (7, 3), (3, 5), (7, 5), (5, 2), (5, 6)]
COL_H = 48
PLR_H = 34

PX = PLAYER_TILE[0] * TILE + TILE / 2
PY = PLAYER_TILE[1] * TILE + TILE / 2


def make_cam(head_yaw):
    # camera locked to the player's facing (forward = "north"); head_yaw is the
    # +/-45deg peek. Orbit slightly so the peek reads as looking around them.
    cam = Camera(pitch=math.radians(PITCH), yaw=head_yaw, scale=0.92)
    cam.cam_x, cam.cam_y = PX, PY
    cam.origin = (CELL[0] // 2, int(CELL[1] * 0.60))
    return cam


def draw_floor(surf, cam):
    for ty in range(ROWS):
        for tx in range(COLS):
            x0, y0 = tx * TILE, ty * TILE
            quad = [cam.project(x0, y0), cam.project(x0 + TILE, y0),
                    cam.project(x0 + TILE, y0 + TILE), cam.project(x0, y0 + TILE)]
            pygame.draw.polygon(surf, FLOOR_A if (tx + ty) % 2 == 0 else FLOOR_B, quad)


def drawables(cam):
    items = []
    # perimeter wall
    cells = [(tx, 0) for tx in range(COLS)] + [(tx, ROWS - 1) for tx in range(COLS)]
    cells += [(0, ty) for ty in range(1, ROWS - 1)] + [(COLS - 1, ty) for ty in range(1, ROWS - 1)]
    for (tx, ty) in cells:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        a = occluder_alpha(cam, wx, wy, 30, PX, PY, PLR_H)
        items.append((cam.depth(wx, wy, 15), a,
                      lambda s, wx=wx, wy=wy: draw_box(s, cam, wx, wy, TILE, TILE, 30, WALL)))
    for (tx, ty) in COLUMNS:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        a = occluder_alpha(cam, wx, wy, COL_H, PX, PY, PLR_H)
        items.append((cam.depth(wx, wy, COL_H), a,
                      lambda s, wx=wx, wy=wy: draw_solid(s, cam, wx, wy, COL_SECT, COLUMN)))
    # the player (never faded; the focus actor)
    items.append((cam.depth(PX, PY, PLR_H), 255,
                  lambda s: draw_solid(s, cam, PX, PY, PLR_SECT, PLAYER)))
    return items


def render(head_yaw, kind="overcast"):
    surf = pygame.Surface(CELL)
    draw_skybox(surf, (0, 0, CELL[0], CELL[1]), yaw=head_yaw, kind=kind, horizon_frac=0.40)
    cam = make_cam(head_yaw)
    draw_floor(surf, cam)
    for _d, a, fn in sorted(drawables(cam), key=lambda p: p[0]):
        draw_with_alpha(surf, a, fn)
    return surf


def strip():
    font = pygame.font.SysFont("monospace", 12)
    # the 90deg arc: -45, -22, 0(forward/default), +22, +45
    yaws = [-45, -22, 0, 22, 45]
    out = pygame.Surface((CELL[0] * len(yaws), CELL[1] + 18))
    out.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        out.blit(render(math.radians(yd)), (i * CELL[0], 0))
        tag = "FORWARD" if yd == 0 else f"head {yd:+d}deg"
        out.blit(font.render(tag, True, (180, 180, 190)), (i * CELL[0] + 8, CELL[1] + 2))
    pygame.image.save(out, "/tmp/occlusion_demo.png")
    print("wrote /tmp/occlusion_demo.png")


def gif():
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; skipping gif"); return
    frames = []
    N = 64
    for i in range(N):
        # ease across the +/-45 arc and back (head turning side to side)
        head = math.radians(45 * math.sin(i / N * 2 * math.pi))
        s = render(head)
        raw = pygame.image.tostring(s, "RGB")
        frames.append(Image.frombytes("RGB", CELL, raw).convert("P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/occlusion_demo.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/occlusion_demo.gif")


if __name__ == "__main__":
    strip()
    gif()
