"""Fixed 55deg pitch + player-rotated yaw + skybox filling the void.

Renders the same demo room at a locked oblique angle while the CAMERA yaws,
with a procedural backdrop behind the scene. Proves the "rotate the world,
fill the black voids with a skybox" direction. Headless.

    python tools/preview_skybox.py   -> /tmp/skybox_demo.png (+ .gif)
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
from rendering.solids import draw_solid, draw_box
from rendering.skybox import draw_skybox

TILE = 32
COLS, ROWS = 11, 9
W, H = COLS * TILE, ROWS * TILE
CELL = (360, 320)
PITCH = 55

FLOOR_A = (40, 36, 33); FLOOR_B = (32, 29, 27)
WALL = {"top": (70, 60, 50), "side": (44, 38, 32), "dark": (28, 24, 20)}
COLUMN = {"body": (58, 54, 64), "lo": (30, 28, 36), "rim": (96, 96, 120)}
FIGURE = {"body": (26, 24, 30), "lo": (12, 11, 15), "rim": (60, 60, 80)}
PLAYER = {"body": (120, 96, 60), "lo": (70, 54, 34), "rim": (190, 160, 110)}
CRATE = {"top": (110, 86, 52), "side": (78, 60, 36), "dark": (50, 38, 22)}

FIG_SECT = [(0, 10, 11), (10, 8, 9), (24, 6, 6), (40, 5, 5), (52, 6, 6), (60, 4, 4)]
COL_SECT = [(0, 9, 9), (8, 8, 8), (40, 8, 8), (48, 10, 10)]
PLR_SECT = [(0, 7, 7), (18, 6, 6), (28, 7, 7), (34, 5, 5)]

COLUMNS = [(2, 2), (8, 2), (2, 6), (8, 6)]
CRATES = [(5, 3), (6, 3)]
FIGURES = [(7, 5)]
PLAYER_POS = (5, 5)


def make_cam(yaw):
    cam = Camera(pitch=math.radians(PITCH), yaw=yaw, scale=0.82)
    cam.cam_x, cam.cam_y = W / 2.0, H / 2.0
    cam.origin = (CELL[0] // 2, int(CELL[1] * 0.62))
    return cam


def draw_floor(surf, cam):
    for ty in range(ROWS):
        for tx in range(COLS):
            x0, y0 = tx * TILE, ty * TILE
            quad = [cam.project(x0, y0), cam.project(x0 + TILE, y0),
                    cam.project(x0 + TILE, y0 + TILE), cam.project(x0, y0 + TILE)]
            pygame.draw.polygon(surf, FLOOR_A if (tx + ty) % 2 == 0 else FLOOR_B, quad)


def drawables(cam, t):
    items = []
    # walls
    cells = [(tx, 0) for tx in range(COLS)] + [(tx, ROWS - 1) for tx in range(COLS)]
    cells += [(0, ty) for ty in range(1, ROWS - 1)] + [(COLS - 1, ty) for ty in range(1, ROWS - 1)]
    for (tx, ty) in cells:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        items.append((cam.depth(wx, wy, 15),
                      lambda s, wx=wx, wy=wy: draw_box(s, cam, wx, wy, TILE, TILE, 30, WALL)))
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


def render(yaw, t=1.4, kind="overcast"):
    surf = pygame.Surface(CELL)
    draw_skybox(surf, (0, 0, CELL[0], CELL[1]), yaw=yaw, kind=kind, horizon_frac=0.40)
    cam = make_cam(yaw)
    draw_floor(surf, cam)
    for _d, fn in sorted(drawables(cam, t), key=lambda p: p[0]):
        fn(surf)
    return surf


def strip():
    font = pygame.font.SysFont("monospace", 12)
    yaws = [0, 45, 90, 135]
    out = pygame.Surface((CELL[0] * len(yaws), CELL[1] + 18))
    out.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        out.blit(render(math.radians(yd)), (i * CELL[0], 0))
        out.blit(font.render(f"yaw {yd}deg  (pitch {PITCH})", True, (170, 170, 180)),
                 (i * CELL[0] + 8, CELL[1] + 2))
    pygame.image.save(out, "/tmp/skybox_demo.png")
    print("wrote /tmp/skybox_demo.png")


def gif():
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; skipping gif"); return
    frames = []
    N = 72
    for i in range(N):
        yaw = i / N * 2 * math.pi
        s = render(yaw, t=i * 0.12)
        raw = pygame.image.tostring(s, "RGB")
        frames.append(Image.frombytes("RGB", CELL, raw).convert("P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/skybox_demo.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/skybox_demo.gif")


if __name__ == "__main__":
    strip()
    gif()
