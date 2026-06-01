"""Tilt a REAL scene's floor + walls — Phase 2 proof (headless).

Strategy (orthographic oblique, so it stays cheap and keeps every procedural
floor detail):
  1. Render the scene's FLOOR flat into a world-space surface, exactly as the
     live game does today (z = 0 plane).
  2. Warp that flat image through the ground-plane projection. For a pure
     yaw + pitch about the view center this is affine: rotate by the yaw,
     then squash vertically by cos(pitch). pygame.transform.rotate + scale.
  3. Extrude WALL tiles as separate upright quads (top + side faces) on top,
     depth-sorted, so they stand rather than lie flat.

Proves the look on actual map data before the change lands in scenes/base.py.

    python tools/preview_scene_tilt.py [scene_key]   -> /tmp/scene_tilt.png
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
from scenes.base import draw_scene_terrain, TILE, _WALL_CHARS
from rendering.camera import Camera

PITCH = 55
WALL_H = 26
WALL_TOP = (70, 60, 50)
WALL_SIDE = (40, 35, 30)
WALL_DARK = (24, 21, 18)


def render_flat_floor(scene):
    """Floor + objects flat, in world space (the current top-down raster)."""
    W = scene.w * TILE
    H = scene.h * TILE
    surf = pygame.Surface((W, H))
    surf.fill((10, 10, 14))
    draw_scene_terrain(surf, scene, 0, 0, 0, 0, scene.w, scene.h)
    return surf


def warp_floor(flat, cam):
    """Affine warp of the flat floor plane to match cam.project() for z=0:
    world-rotate by yaw, then scale x by cam.scale and y by cam.scale*cos
    (pitch). Order matches the projection (rotate first, nonuniform scale
    after)."""
    yaw_deg = math.degrees(cam.yaw)
    rotated = pygame.transform.rotate(flat, yaw_deg)
    cp = max(0.05, math.cos(cam.pitch))
    w, h = rotated.get_size()
    squashed = pygame.transform.smoothscale(
        rotated, (max(1, int(w * cam.scale)),
                  max(1, int(h * cam.scale * cp))))
    return squashed


def extrude_walls(surf, scene, cam, ox, oy):
    """Draw wall tiles as upright quads on top of the warped floor, depth
    sorted. ox/oy place the scene's world origin on screen."""
    walls = []
    for ty in range(scene.h):
        for tx in range(scene.w):
            if scene.objects[ty][tx] in _WALL_CHARS:
                walls.append((tx, ty))
    walls.sort(key=lambda c: cam.depth(c[0] * TILE + TILE / 2,
                                       c[1] * TILE + TILE / 2))
    for (tx, ty) in walls:
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2

        def P(dx, dy, dz):
            sx, sy = cam.project(wx + dx, wy + dy, dz)
            return (sx + ox, sy + oy)
        hw = TILE / 2
        # four ground corners + their tops
        g = [P(-hw, -hw, 0), P(hw, -hw, 0), P(hw, hw, 0), P(-hw, hw, 0)]
        t = [P(-hw, -hw, WALL_H), P(hw, -hw, WALL_H),
             P(hw, hw, WALL_H), P(-hw, hw, WALL_H)]
        # near + side faces (simple, unculled is fine for the proof)
        pygame.draw.polygon(surf, WALL_DARK, [g[3], g[2], t[2], t[3]])
        pygame.draw.polygon(surf, WALL_SIDE, [g[0], g[3], t[3], t[0]])
        pygame.draw.polygon(surf, WALL_SIDE, [g[1], g[2], t[2], t[1]])
        pygame.draw.polygon(surf, WALL_TOP, [t[0], t[1], t[2], t[3]])
        pygame.draw.polygon(surf, (20, 18, 16), [t[0], t[1], t[2], t[3]], 1)


def render(scene, yaw_deg, cell=(420, 360)):
    cam = Camera(pitch=math.radians(PITCH), yaw=math.radians(yaw_deg),
                 scale=0.62)
    cam.cam_x = scene.w * TILE / 2
    cam.cam_y = scene.h * TILE / 2
    cam.origin = (0, 0)
    out = pygame.Surface(cell)
    out.fill((8, 8, 11))
    # The shared anchor: the screen point that the scene's world-center maps
    # to. The warped floor is centered on it; the walls use it as their
    # projection origin (cam.project(cam_x, cam_y) == (0,0) with origin 0).
    S = (cell[0] // 2, int(cell[1] * 0.52))
    flat = render_flat_floor(scene)
    warped = warp_floor(flat, cam)
    out.blit(warped, (S[0] - warped.get_width() // 2,
                      S[1] - warped.get_height() // 2))
    extrude_walls(out, scene, cam, S[0], S[1])
    return out


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "sheriff_office"
    scene = load_scene(key)
    font = pygame.font.SysFont("monospace", 12)
    yaws = [0, 30, 60, 90]
    cell = (420, 360)
    out = pygame.Surface((cell[0] * len(yaws), cell[1] + 18))
    out.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        out.blit(render(scene, yd, cell), (i * cell[0], 0))
        out.blit(font.render(f"{key}  yaw {yd}", True, (170, 170, 180)),
                 (i * cell[0] + 8, cell[1] + 2))
    pygame.image.save(out, "/tmp/scene_tilt.png")
    print(f"wrote /tmp/scene_tilt.png ({key})")


if __name__ == "__main__":
    main()
