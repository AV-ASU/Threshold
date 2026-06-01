"""Stress-test the tilt against WRAP seams and FOLDS (headless).

The gate before scenes/base.py changes: under the oblique tilt, (a) a
wrap-around scene's floor must stay seamless across the wrap line, and (b)
fold peeks must still land on the right spot and read.

Approach = the LIVE-ready window warp:
  - render a flat WINDOW of the world around the player, big enough that the
    yaw rotation still covers the screen. draw_scene_terrain already wraps
    tile lookups past the map bounds, so the window is seamless across a
    wrap seam for free.
  - warp that window (yaw rotate + pitch squash) and center it on the player.
  - a FOLD is composited as a fog-masked peek panel placed via cam.project()
    (not raw cam subtraction) so it sits on the tilted floor at its seam.

    python tools/preview_wrap_fold_tilt.py        -> /tmp/wrap_fold_tilt.png
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import load_scene
from scenes.base import draw_scene_terrain, TILE, apply_grade
from rendering.camera import Camera
from rendering.skybox import draw_skybox
from rendering.sprites import draw_player_sprite, draw_npc_sprite

PITCH = 55
WIN_TILES = 34          # flat window span (tiles) -- > screen so yaw covers it


class _P:
    """Minimal stand-in player for draw_fold + placement."""
    def __init__(self, x, y, facing):
        self.x = x; self.y = y; self.facing = facing


def render_flat_window(scene, cx, cy, span_px):
    """Flat raster of the world window centered on world (cx, cy), span_px
    wide/tall, wrapping past map bounds (seamless across wrap seams)."""
    surf = pygame.Surface((span_px, span_px))
    surf.fill((10, 10, 14))
    wx0 = cx - span_px / 2.0
    wy0 = cy - span_px / 2.0
    x0 = int(math.floor(wx0 / TILE))
    y0 = int(math.floor(wy0 / TILE))
    x1 = int(math.ceil((wx0 + span_px) / TILE))
    y1 = int(math.ceil((wy0 + span_px) / TILE))
    draw_scene_terrain(surf, scene, wx0, wy0, x0, y0, x1, y1)
    return surf, wx0, wy0


def warp(flat, cam):
    rotated = pygame.transform.rotate(flat, math.degrees(cam.yaw))
    cp = max(0.05, math.cos(cam.pitch))
    w, h = rotated.get_size()
    return pygame.transform.smoothscale(
        rotated, (max(1, int(w * cam.scale)), max(1, int(h * cam.scale * cp))))


def make_cam(yaw_deg, px, py, S):
    cam = Camera(pitch=math.radians(PITCH), yaw=math.radians(yaw_deg),
                 scale=0.7)
    cam.cam_x, cam.cam_y = px, py
    cam.origin = S
    return cam


def draw_fold_tilted(out, cam, face, player):
    """A trimmed draw_fold: build the target peek, fog-mask it, place it on
    the tilted floor at cam.project(fold_px). Read-only proof of placement."""
    from rendering.folds import _fog_mask, SIGHT_DEPTH, SEAM_TILES
    nx, ny = face["normal"]
    if player.facing[0] * nx + player.facing[1] * ny < 0.2:
        return False
    target = face["target"]
    ax, ay = face["anchor_tile"]
    fold_x, fold_y = face["fold_px"]
    if nx != 0:
        w, h = SIGHT_DEPTH, SEAM_TILES * TILE
    else:
        w, h = SEAM_TILES * TILE, SIGHT_DEPTH
    cam_x = ax * TILE + 16 - w // 2
    cam_y = ay * TILE + 16 - h // 2
    big = pygame.Surface((w, h))
    big.fill((8, 8, 11))
    target.draw(big, cam_x, cam_y)
    apply_grade(big, 1.0)
    surf = big.convert_alpha()
    import numpy as np
    mask = _fog_mask(w, h, face["normal"])
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * 255).astype(np.uint8)
    del pa
    # placement: seam at cam.project(fold_px); panel faces camera (billboard),
    # rising off the floor so the tear stands like a doorway.
    sx, sy = cam.project(fold_x, fold_y)
    rise = int(h * (0.4 + 0.6 * cam.ground_squash()))
    if nx < 0:
        rx, ry = sx - w, sy - rise
    elif nx > 0:
        rx, ry = sx, sy - rise
    elif ny < 0:
        rx, ry = sx - w // 2, sy - rise
    else:
        rx, ry = sx - w // 2, sy - rise
    out.blit(surf, (rx, ry))
    pygame.draw.line(out, (210, 180, 70), (sx, sy - rise), (sx, sy), 2)
    return True


def render(scene, yaw_deg, px, py, facing, fold=None, cell=(440, 380)):
    S = (cell[0] // 2, int(cell[1] * 0.55))
    cam = make_cam(yaw_deg, px, py, S)
    out = pygame.Surface(cell)
    draw_skybox(out, (0, 0, cell[0], cell[1]), yaw=cam.yaw, kind="overcast",
                horizon_frac=0.40)
    span = WIN_TILES * TILE
    flat, wx0, wy0 = render_flat_window(scene, px, py, span)
    warped = warp(flat, cam)
    # the window is centered on the player -> blit centered on S
    out.blit(warped, (S[0] - warped.get_width() // 2,
                      S[1] - warped.get_height() // 2))
    player = _P(px, py, facing)
    if fold is not None:
        draw_fold_tilted(out, cam, fold, player)
    # player billboard at center
    spr = pygame.Surface((40, 52), pygame.SRCALPHA)
    draw_player_sprite(spr, 20, 34, facing, 0)
    pbx, pby = cam.project(px, py, 0)
    rise = 52 * (0.45 + 0.55 * cam.ground_squash())
    out.blit(spr, (int(pbx - 20), int(pby - rise)))
    return out


def main():
    scene = load_scene("brimley")
    font = pygame.font.SysFont("monospace", 12)
    cell = (440, 380)
    # Put the player ON the wrap seam (x near 0) so the window straddles it.
    seam_x = 2.0 * TILE          # just inside the west edge -> window crosses x=0
    py = 13 * TILE               # the road row
    px = seam_x
    # A synthetic fold a few tiles ahead (north), peeking into another scene.
    target = load_scene("sheriff_office")
    fold = {"normal": (0, -1), "target": target,
            "anchor_tile": (target.w // 2, target.h // 2),
            "fold_px": (px, py - 5 * TILE)}

    rows = []
    # Row 1: wrap-seam seamlessness across the head-turn arc (no fold)
    yaws = [-45, -20, 0, 20, 45]
    strip1 = pygame.Surface((cell[0] * len(yaws), cell[1] + 18))
    strip1.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        strip1.blit(render(scene, yd, px, py, (0, -1)), (i * cell[0], 0))
        tag = "WRAP SEAM  head %+d" % yd if yd else "WRAP SEAM  FORWARD"
        strip1.blit(font.render(tag, True, (170, 170, 180)),
                    (i * cell[0] + 8, cell[1] + 2))
    rows.append(strip1)
    # Row 2: a FOLD peek placed on the tilted floor across the arc
    strip2 = pygame.Surface((cell[0] * len(yaws), cell[1] + 18))
    strip2.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        strip2.blit(render(scene, yd, px, py, (0, -1), fold), (i * cell[0], 0))
        tag = "FOLD  head %+d" % yd if yd else "FOLD  FORWARD"
        strip2.blit(font.render(tag, True, (210, 180, 120)),
                    (i * cell[0] + 8, cell[1] + 2))
    rows.append(strip2)

    full = pygame.Surface((rows[0].get_width(), sum(r.get_height() for r in rows) + 6))
    full.fill((0, 0, 0))
    y = 0
    for r in rows:
        full.blit(r, (0, y)); y += r.get_height() + 6
    pygame.image.save(full, "/tmp/wrap_fold_tilt.png")
    print("wrote /tmp/wrap_fold_tilt.png")


if __name__ == "__main__":
    main()
