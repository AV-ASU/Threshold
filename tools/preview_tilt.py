"""Render a small room through the Camera at increasing pitch -- the tilt demo.

Shows the SAME world (floor grid, perimeter walls, columns, a crate, a
figure, a player marker) projected at pitch 0 (today's top-down) -> oblique,
to prove the camera/projection + volumetric kit sell a tilted view. Headless.

    python tools/preview_tilt.py    -> /tmp/tilt_demo.png (+ .gif)
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
from rendering.solids import draw_solid, draw_box, draw_billboard

TILE = 32
COLS, ROWS = 11, 9
W, H = COLS * TILE, ROWS * TILE
CELL = (300, 260)

FLOOR_A = (40, 36, 33)
FLOOR_B = (32, 29, 27)
WALL = {"top": (70, 60, 50), "side": (44, 38, 32), "dark": (28, 24, 20)}
COLUMN = {"body": (58, 54, 64), "lo": (30, 28, 36), "rim": (96, 96, 120)}
FIGURE = {"body": (26, 24, 30), "lo": (12, 11, 15), "rim": (60, 60, 80)}
PLAYER = {"body": (120, 96, 60), "lo": (70, 54, 34), "rim": (190, 160, 110)}
CRATE = {"top": (110, 86, 52), "side": (78, 60, 36), "dark": (50, 38, 22)}

# figure (a Watcher-ish column that tapers to a head), in world-z heights
FIG_SECT = [(0, 10, 11), (10, 8, 9), (24, 6, 6), (40, 5, 5),
            (52, 6, 6), (60, 4, 4)]
COL_SECT = [(0, 9, 9), (8, 8, 8), (40, 8, 8), (48, 10, 10)]   # column w/ cap
PLR_SECT = [(0, 7, 7), (18, 6, 6), (28, 7, 7), (34, 5, 5)]    # squat figure

# scene contents in world coords (tile centers)
COLUMNS = [(2, 2), (8, 2), (2, 6), (8, 6)]
CRATES = [(5, 3), (6, 3)]
FIGURES = [(7, 5)]
PLAYER_POS = (5, 5)


def make_cam(pitch):
    cam = Camera(pitch=math.radians(pitch), scale=1.0)
    # center the room in the cell; lift origin so tilted room stays framed
    cx, cy = W / 2.0, H / 2.0
    cam.cam_x, cam.cam_y = cx, cy
    cam.origin = (CELL[0] // 2, int(CELL[1] * 0.60))
    return cam


def draw_floor(surf, cam):
    for ty in range(ROWS):
        for tx in range(COLS):
            x0, y0 = tx * TILE, ty * TILE
            quad = [cam.project(x0, y0), cam.project(x0 + TILE, y0),
                    cam.project(x0 + TILE, y0 + TILE), cam.project(x0, y0 + TILE)]
            col = FLOOR_A if (tx + ty) % 2 == 0 else FLOOR_B
            pygame.draw.polygon(surf, col, quad)


def draw_walls(surf, cam):
    # perimeter walls as boxes, depth-sorted back->front by world-y
    cells = []
    for tx in range(COLS):
        cells += [(tx, 0), (tx, ROWS - 1)]
    for ty in range(1, ROWS - 1):
        cells += [(0, ty), (COLS - 1, ty)]
    cells.sort(key=lambda c: cam.depth(c[0] * TILE, c[1] * TILE))
    for (tx, ty) in cells:
        draw_box(surf, cam, tx * TILE + TILE / 2, ty * TILE + TILE / 2,
                 TILE, TILE, 30, WALL)


def scene_drawables(cam, t):
    items = []
    for (tx, ty) in COLUMNS:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        items.append((cam.depth(wx, wy, 48),
                      lambda s, wx=wx, wy=wy: draw_solid(s, cam, wx, wy, COL_SECT, COLUMN)))
    for (tx, ty) in CRATES:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        items.append((cam.depth(wx, wy, 18),
                      lambda s, wx=wx, wy=wy: draw_box(s, cam, wx, wy, 26, 26, 18, CRATE, yaw=0.4)))
    for (tx, ty) in FIGURES:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        bob = math.sin(t * 1.3) * 1.5
        items.append((cam.depth(wx, wy, 60),
                      lambda s, wx=wx, wy=wy, b=bob: draw_solid(s, cam, wx, wy, FIG_SECT, FIGURE, t=t, yaw=t * 0.7, bob=b)))
    tx, ty = PLAYER_POS
    wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
    items.append((cam.depth(wx, wy, 34),
                  lambda s, wx=wx, wy=wy: draw_solid(s, cam, wx, wy, PLR_SECT, PLAYER)))
    return items


def render(pitch, t=1.4):
    surf = pygame.Surface(CELL)
    surf.fill((10, 9, 12))
    cam = make_cam(pitch)
    draw_floor(surf, cam)
    draw_walls(surf, cam)
    for _d, fn in sorted(scene_drawables(cam, t), key=lambda p: p[0]):
        fn(surf)
    return surf


def strip():
    font = pygame.font.SysFont("monospace", 12)
    pitches = [0, 20, 35, 55]
    out = pygame.Surface((CELL[0] * len(pitches), CELL[1] + 18))
    out.fill((6, 6, 8))
    for i, p in enumerate(pitches):
        out.blit(render(p), (i * CELL[0], 0))
        out.blit(font.render(f"pitch {p}deg", True, (170, 170, 180)),
                 (i * CELL[0] + 8, CELL[1] + 2))
    pygame.image.save(out, "/tmp/tilt_demo.png")
    print("wrote /tmp/tilt_demo.png")


def gif():
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; skipping gif"); return
    frames = []
    N = 60
    for i in range(N):
        # ease pitch 0->45 and back, with the figure spinning
        p = 22.5 * (1 - math.cos(i / N * 2 * math.pi))
        s = render(p, t=i * 0.13)
        raw = pygame.image.tostring(s, "RGB")
        frames.append(Image.frombytes("RGB", CELL, raw).convert("P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/tilt_demo.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/tilt_demo.gif")


if __name__ == "__main__":
    strip()
    gif()
