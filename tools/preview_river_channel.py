"""River-channel preview -- a sunken river with real depth (CAMERA.md Phase 6).

A design spike for the "large outdoor area + a river that has depth" question.
It answers it as a DIRECT comparison: the same scene, same camera, same five
figures placed ACROSS the river (grade -> bank -> water -> bank -> grade),
rendered FLAT (no heightfield) vs CARVED (rendering.heightfield.carve_channel).
In the carved view the bank figures ride UP and the water figure drops DOWN into
the wet trough, and the near bank crest HIDES the figure in the bed -- the
sight-pit the WADE water routing wants.

    python tools/preview_river_channel.py   -> /tmp/river_channel.png

Self-contained: builds a small grass scene with a river and drives the tilt
draw + sight gate directly (no live scene opts in -- this is a prototype).
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
pygame.display.set_mode((SCREEN_W, SCREEN_H))
from systems.config import TILT_ACTOR_STAND
from rendering.camera import Camera
from rendering.skybox import draw_skybox
from rendering.heightfield import (build_heightfield, carve_channel,
                                   draw_ground_mesh)
from rendering.sprites import draw_npc_sprite, view_from_facing
from rendering.sight import visible_factor, SIGHT_EYE_H
from scenes.base import Scene, draw_terrain_tilted

W, H = 26, 26
RIVER_ROW = 13          # the river runs E-W across the middle
HALF = 3.2              # channel half-width, tiles
DEPTH = 82.0            # how far the bed sinks below grade, world-z px
BANK = 34.0             # how far the banks rise above grade, world-z px


def build_scene(carved):
    floor = [["." for _ in range(W)] for _ in range(H)]
    for tx in range(W):
        for ty in (RIVER_ROW, RIVER_ROW + 1):
            floor[ty][tx] = "~"
    sc = Scene("river_spike", ["".join(r) for r in floor], music="wind")
    sc.skybox_kind = "overcast"
    if carved:
        banks = []
        for tx in range(-1, W + 1):
            banks.append((tx, RIVER_ROW - HALF, 2.4, BANK))
            banks.append((tx, RIVER_ROW + 1 + HALF, 2.4, BANK))
        grid = build_heightfield(W, H, banks)
        centerline = [(tx, RIVER_ROW + 0.5) for tx in range(-1, W + 1)]
        sc.set_ground(carve_channel(W, H, centerline, HALF, DEPTH, grid=grid))
    return sc


# A row of identical stakes marching NORTH across the river on one column. Each
# is a fixed world height planted on the ground -- so their bases trace the
# terrain: flat they recede in a straight line; carved they plunge into the bed
# and climb the banks. That base profile IS the depth.
COL = W // 2
STAKE_H = 30.0                         # world-px height of each stake
STAKE_ROWS = [RIVER_ROW + 0.5 - i * 1.15 for i in range(-6, 7)]

# The viewer stands back on the south grade, looking north over the river.
VIEW_ROW = RIVER_ROW + 8.5


def _cam():
    px, py = COL * TILE + 16, VIEW_ROW * TILE
    return Camera(cam_x=px, cam_y=py, pitch=math.radians(55),
                  yaw=math.radians(22), scale=1.9,
                  origin=(SCREEN_W // 2, SCREEN_H // 2 + 90))


def _stakes(surf, sc, cam):
    for row in STAKE_ROWS:
        wx, wy = COL * TILE + 16, row * TILE
        gz = sc.ground_z(wx, wy)
        bx, by = cam.project(wx, wy, gz)
        tx, ty = cam.project(wx, wy, gz + STAKE_H)
        wet = sc.floor[int(row) % H][COL] == "~" if 0 <= int(row) < H else False
        col = (120, 180, 210) if wet else (232, 210, 120)
        pygame.draw.line(surf, (0, 0, 0), (bx, by + 2), (tx, ty), 6)
        pygame.draw.line(surf, col, (bx, by), (tx, ty), 4)
        pygame.draw.circle(surf, (255, 250, 235), (tx, ty), 5)
        pygame.draw.circle(surf, (0, 0, 0), (bx, by), 3)


def _draw(sc, cam, mode):
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_skybox(surf, (0, 0, SCREEN_W, SCREEN_H), yaw=cam.yaw,
                kind="overcast", horizon_frac=0.40)
    draw_terrain_tilted(surf, sc, cam)
    draw_ground_mesh(surf, cam, sc)
    if mode in ("flat", "carved"):
        _stakes(surf, sc, cam)
    else:                              # "sight": a figure standing in the bed
        # viewer at the near RIM (so the figure shows here); from the grade the
        # bank crest would hide it -- that asymmetry IS the sight-pit
        px, py = COL * TILE + 16, (RIVER_ROW + 1 + HALF) * TILE
        wx, wy = COL * TILE + 16, (RIVER_ROW + 0.5) * TILE
        f = visible_factor(px, py, -math.pi / 2, wx, wy, sc.blocks_sight,
                           ground=sc.ground_z, eye=SIGHT_EYE_H)
        if f > 0.04:
            gz = sc.ground_z(wx, wy)
            sx, sy = cam.project(wx, wy, gz)
            sy -= int(TILT_ACTOR_STAND * math.sin(cam.pitch))
            layer = pygame.Surface((220, 250), pygame.SRCALPHA)
            view = view_from_facing(0.0, -1.0, cam.yaw)
            draw_npc_sprite(layer, 110, 160, "cultist", (0.0, -1.0), view=view)
            if f < 0.99:
                layer.set_alpha(int(255 * f))
            surf.blit(layer, (sx - 110, sy - 160))
    return surf


def _panel(surf, label, font, sub):
    # crop to the middle where the action is, 1.6x up
    cw, ch = 460, 430
    cx = (SCREEN_W - cw) // 2
    cy = (SCREEN_H - ch) // 2 + 40
    crop = surf.subsurface((cx, cy, cw, ch)).copy()
    scaled = pygame.transform.scale(crop, (int(cw * 1.5), int(ch * 1.5)))
    bar = pygame.Surface((scaled.get_width(), 46))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (235, 233, 220)), (10, 4))
    bar.blit(pygame.font.SysFont("monospace", 13).render(
        sub, True, (150, 170, 180)), (10, 25))
    out = pygame.Surface((scaled.get_width(), scaled.get_height() + 46))
    out.blit(scaled, (0, 0))
    out.blit(bar, (0, scaled.get_height()))
    return out


def main():
    font = pygame.font.SysFont("monospace", 17)
    flat = _panel(_draw(build_scene(False), _cam(), "flat"),
                  "FLAT  (no heightfield)", font,
                  "a row of equal stakes -- their bases recede in a straight line")
    carved = _panel(_draw(build_scene(True), _cam(), "carved"),
                    "CARVED CHANNEL", font,
                    "same stakes -- their bases PLUNGE into the wet bed, climb the banks")
    gated = _panel(_draw(build_scene(True), _cam(), "sight"),
                   "CARVED + SIGHT", font,
                   "a figure stands down in the wet bed (from the grade the bank hides it)")

    gap = 16
    pw, ph = flat.get_size()
    sheet = pygame.Surface((pw * 3 + gap * 2, ph))
    sheet.fill((12, 12, 14))
    for i, p in enumerate((flat, carved, gated)):
        sheet.blit(p, (i * (pw + gap), 0))
    pygame.image.save(sheet, "/tmp/river_channel.png")
    print("wrote /tmp/river_channel.png")


if __name__ == "__main__":
    main()
