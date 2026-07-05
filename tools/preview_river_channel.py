"""River-channel preview -- a sunken river with real depth (CAMERA.md Phase 6).

A design spike for the "large outdoor area + a river that has depth" question:
compose the shipped heightfield primitives into a CARVED river. The ground is
cut into a trough (rendering.heightfield.carve_channel), water chars sit on the
bed so the mesh shades it wet, and the bank crest occludes line of sight -- so a
figure down in the channel is HIDDEN from someone back on the grade until they
reach the rim (the sight-pit the WADE water routing wants).

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

W, H = 30, 24
RIVER_ROW = 12          # the river runs E-W across the middle
HALF = 3.2              # channel half-width, tiles
DEPTH = 66.0            # how far the bed sinks below grade, world-z px
CROP_W, CROP_H = 360, 300


def build_river_scene():
    floor = [["." for _ in range(W)] for _ in range(H)]
    # a two-tile-wide water ribbon on the channel axis
    for tx in range(W):
        for ty in (RIVER_ROW, RIVER_ROW + 1):
            floor[ty][tx] = "~"
    sc = Scene("river_spike", ["".join(r) for r in floor],
               music="wind")
    sc.skybox_kind = "overcast"
    # Raised BANKS (levees) either side of the cut, then carve the channel into
    # them: the profile becomes grade -> bank crest (+) -> wet bed (-) -> bank
    # -> grade, so there is real relief to read even over the flat floor raster.
    banks = []
    for tx in range(-1, W + 1):
        banks.append((tx, RIVER_ROW - HALF, 2.4, 30.0))
        banks.append((tx, RIVER_ROW + 1 + HALF, 2.4, 30.0))
    grid = build_heightfield(W, H, banks)
    centerline = [(tx, RIVER_ROW + 0.5) for tx in range(-1, W + 1)]
    sc.set_ground(carve_channel(W, H, centerline, HALF, DEPTH, grid=grid))
    return sc


def _cam(px, py, yaw=math.radians(28)):
    return Camera(cam_x=px, cam_y=py, pitch=math.radians(55), yaw=yaw,
                  scale=1.7, origin=(SCREEN_W // 2, SCREEN_H // 2 + 40))


def _standee(surf, cam, sc, px, py, aim, wx, wy, kind, facing):
    """Draw an actor standing on the (possibly sunken) ground, gated by the
    viewer's sight cone WITH the ground-crest term -- so the bank hides a figure
    in the channel from a viewer up on the grade."""
    gz = sc.ground_z(wx, wy)
    sx, sy = cam.project(wx, wy, gz)
    sy -= int(TILT_ACTOR_STAND * math.sin(cam.pitch))
    f = visible_factor(px, py, aim, wx, wy, sc.blocks_sight,
                       ground=sc.ground_z, eye=SIGHT_EYE_H)
    if f <= 0.04:
        return
    layer = pygame.Surface((220, 250), pygame.SRCALPHA)
    view = view_from_facing(facing[0], facing[1], cam.yaw)
    draw_npc_sprite(layer, 110, 160, kind, facing, view=view)
    if f < 0.99:
        layer.set_alpha(int(255 * f))
    surf.blit(layer, (sx - 110, sy - 160))


def _world(sc, cam):
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_skybox(surf, (0, 0, SCREEN_W, SCREEN_H), yaw=cam.yaw,
                kind="overcast", horizon_frac=0.40)
    draw_terrain_tilted(surf, sc, cam)
    draw_ground_mesh(surf, cam, sc)
    return surf


def _panel(surf, label, focus, cam, font):
    bx, by = cam.project(*focus)
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2))
    crop = surf.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * 2, CROP_H * 2))
    bar = pygame.Surface((CROP_W * 2, 24))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * 2, CROP_H * 2 + 24))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * 2))
    return sheet


def main():
    sc = build_river_scene()
    font = pygame.font.SysFont("monospace", 15)
    river_wy = (RIVER_ROW + 1) * TILE
    focus = (W / 2 * TILE, river_wy)

    # A figure standing IN the channel bed (on the water axis).
    fig = (W / 2 * TILE, river_wy)
    facing_n = (0.0, -1.0)

    shots = []

    # 1. The carved channel itself: banks sloping to a wet trough.
    px, py = W / 2 * TILE, river_wy + 6.0 * TILE     # stand back on the grade
    cam = _cam(px, py)
    surf = _world(sc, cam)
    shots.append(_panel(surf, "1. the carved channel -- banks cut to a wet trough",
                        focus, cam, font))

    # 2. A figure down in the channel, viewer back on the grade: the near bank
    #    crest HIDES it (below the line of sight over the rim).
    surf = _world(sc, cam)
    _standee(surf, cam, sc, px, py, -math.pi / 2, fig[0], fig[1],
             "cultist", facing_n)
    shots.append(_panel(surf, "2. viewer on the grade -- the figure in the channel is HIDDEN",
                        focus, cam, font))

    # 3. Viewer steps to the rim: the channel opens up and the figure RESOLVES.
    px3, py3 = W / 2 * TILE, river_wy + HALF * TILE + 0.4 * TILE
    cam3 = _cam(px3, py3)
    surf = _world(sc, cam3)
    _standee(surf, cam3, sc, px3, py3, -math.pi / 2, fig[0], fig[1],
             "cultist", facing_n)
    shots.append(_panel(surf, "3. step to the rim -- you see down into it, figure RESOLVES",
                        focus, cam3, font))

    pw, ph = shots[0].get_size()
    sheet = pygame.Surface((pw, ph * len(shots)))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, (0, i * ph))
    pygame.image.save(sheet, "/tmp/river_channel.png")
    print("wrote /tmp/river_channel.png")


if __name__ == "__main__":
    main()
