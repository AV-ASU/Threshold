"""Tilt a REAL scene — polished Phase 2 proof (headless).

On top of the floor-warp + wall-extrude proof this adds the whole stack so we
can judge the real look before it lands in scenes/base.py:
  - procedural FLOOR warped to the oblique plane (yaw rotate + pitch squash);
  - WALL tiles extruded as upright boxes with the game's wall palette + the
    real per-tile wall TOP texture (warped like the floor) and back-face cull;
  - the PLAYER standing on the floor as a billboard, depth-sorted WITH the
    walls so walls behind sit behind and walls in front fade (occlusion.py);
  - the procedural SKYBOX filling the void around the scene.

    python tools/preview_scene_tilt.py [scene_key]   -> /tmp/scene_tilt.png
    python tools/preview_scene_tilt.py [scene_key] --gif   (+ rotating gif)
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
from scenes.base import (draw_scene_terrain, draw_floor, TILE, _WALL_CHARS,
                         _WALL_BASE, _WALL_TOP, _WALL_FACE, _WALL_FOOT,
                         _draw_wall_mass)
from rendering.camera import Camera
from rendering.skybox import draw_skybox
from rendering.occlusion import occluder_alpha
from rendering.solids import draw_with_alpha
from rendering.sprites import draw_player_sprite

PITCH = 55
WALL_H = 24
SKY = "void"          # interiors/underground; "overcast" for daytime surface


def _is_wall(scene, tx, ty):
    if 0 <= ty < scene.h and 0 <= tx < scene.w:
        return scene.objects[ty][tx] in _WALL_CHARS
    return False


def render_flat_floor(scene):
    """Floor + ground objects flat, world space (the live top-down raster)."""
    surf = pygame.Surface((scene.w * TILE, scene.h * TILE))
    surf.fill((10, 10, 14))
    draw_scene_terrain(surf, scene, 0, 0, 0, 0, scene.w, scene.h)
    return surf


def warp_floor(flat, cam):
    """Affine warp matching cam.project() for z=0: world-rotate by yaw, then
    scale x by cam.scale, y by cam.scale*cos(pitch)."""
    rotated = pygame.transform.rotate(flat, math.degrees(cam.yaw))
    cp = max(0.05, math.cos(cam.pitch))
    w, h = rotated.get_size()
    return pygame.transform.smoothscale(
        rotated, (max(1, int(w * cam.scale)), max(1, int(h * cam.scale * cp))))


def _wall_top_tex(scene, tx, ty):
    """The real wall raster for one tile (used to texture the top face)."""
    tile = pygame.Surface((TILE, TILE)).convert()
    tile.fill(_WALL_BASE)
    _draw_wall_mass(tile, scene, -tx * TILE, -ty * TILE, tx, ty, tx + 1, ty + 1)
    return tile


def build_player(facing=(0, 1)):
    spr = pygame.Surface((40, 52), pygame.SRCALPHA)
    draw_player_sprite(spr, 20, 34, facing, 0)
    return spr


def render(scene, yaw_deg, player_tile, cell=(440, 380)):
    cam = Camera(pitch=math.radians(PITCH), yaw=math.radians(yaw_deg),
                 scale=0.62)
    cam.cam_x = scene.w * TILE / 2
    cam.cam_y = scene.h * TILE / 2
    S = (cell[0] // 2, int(cell[1] * 0.54))
    cam.origin = S
    out = pygame.Surface(cell)
    # 1. skybox in the void
    draw_skybox(out, (0, 0, cell[0], cell[1]), yaw=cam.yaw, kind=SKY,
                horizon_frac=0.40)
    # 2. floor plane, centered on the shared world-center anchor S
    warped = warp_floor(render_flat_floor(scene), cam)
    out.blit(warped, (S[0] - warped.get_width() // 2,
                      S[1] - warped.get_height() // 2))

    # 3. assemble depth-sorted standing drawables: walls + player
    px = player_tile[0] * TILE + TILE / 2
    py = player_tile[1] * TILE + TILE / 2
    player_spr = build_player()
    draws = []
    for ty in range(scene.h):
        for tx in range(scene.w):
            if scene.objects[ty][tx] in _WALL_CHARS:
                wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
                draws.append(("wall", cam.depth(wx, wy, WALL_H), tx, ty))
    draws.append(("player", cam.depth(px, py, 0), 0, 0))
    draws.sort(key=lambda d: d[1])

    for kind, _d, tx, ty in draws:
        if kind == "player":
            a = 255
            pbx, pby = cam.project(px, py, 0)
            sw, sh = player_spr.get_size()
            rise = sh * (0.45 + 0.55 * cam.ground_squash())
            out.blit(player_spr, (int(pbx - sw / 2), int(pby - rise)))
            continue
        wx, wy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
        # fade a wall that stands between the camera and the player
        a = occluder_alpha(cam, wx, wy, WALL_H, px, py, 30,
                           o_halfw=TILE * 0.5 * cam.scale)
        draw_with_alpha(out, a,
                        lambda s, tx=tx, ty=ty, wx=wx, wy=wy:
                        _draw_wall_box(s, cam, scene, tx, ty, wx, wy))
    return out


def _draw_wall_box(surf, cam, scene, tx, ty, wx, wy):
    hw = TILE / 2

    def P(dx, dy, dz):
        return cam.project(wx + dx, wy + dy, dz)
    g = [P(-hw, -hw, 0), P(hw, -hw, 0), P(hw, hw, 0), P(-hw, hw, 0)]
    t = [P(-hw, -hw, WALL_H), P(hw, -hw, WALL_H),
         P(hw, hw, WALL_H), P(-hw, hw, WALL_H)]
    # Only draw a side face where the neighbour tile is NOT a wall (cull
    # interior seams so a wall RUN reads as one mass, not a grid of boxes).
    near = _shade(_WALL_FACE, 0.5)
    side = _shade(_WALL_FACE, 0.7)
    if not _is_wall(scene, tx, ty + 1):
        pygame.draw.polygon(surf, near, [g[3], g[2], t[2], t[3]])
    if not _is_wall(scene, tx - 1, ty):
        pygame.draw.polygon(surf, side, [g[0], g[3], t[3], t[0]])
    if not _is_wall(scene, tx + 1, ty):
        pygame.draw.polygon(surf, side, [g[1], g[2], t[2], t[1]])
    # top: texture-map the real wall raster (a z=const plane warps affinely)
    tex = _wall_top_tex(scene, tx, ty)
    _blit_quad(surf, tex, t)
    pygame.draw.polygon(surf, _shade(_WALL_TOP, 0.5), t, 1)


def _blit_quad(surf, tex, quad):
    """Approximate texture-map a square surface into a screen quad via the
    quad's bounding box + the affine warp already implied. Cheap stand-in:
    scale the tile to the quad bbox (good enough for a near-parallel top)."""
    xs = [p[0] for p in quad]; ys = [p[1] for p in quad]
    x0, y0 = int(min(xs)), int(min(ys))
    w = max(1, int(max(xs) - x0)); h = max(1, int(max(ys) - y0))
    scaled = pygame.transform.smoothscale(tex, (w, h))
    surf.blit(scaled, (x0, y0))


def _shade(c, f):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def _player_start(scene):
    # a floor tile near center
    cx, cy = scene.w // 2, scene.h // 2
    for r in range(max(scene.w, scene.h)):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                tx, ty = cx + dx, cy + dy
                if (0 <= tx < scene.w and 0 <= ty < scene.h
                        and not _is_wall(scene, tx, ty)
                        and scene.objects[ty][tx] == "."):
                    return (tx, ty)
    return (cx, cy)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    key = args[0] if args else "sheriff_office"
    do_gif = "--gif" in sys.argv
    scene = load_scene(key)
    ptile = _player_start(scene)
    font = pygame.font.SysFont("monospace", 12)
    cell = (440, 380)
    yaws = [-45, -20, 0, 20, 45]
    out = pygame.Surface((cell[0] * len(yaws), cell[1] + 18))
    out.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        out.blit(render(scene, yd, ptile, cell), (i * cell[0], 0))
        tag = f"{key}  head {yd:+d}" if yd else f"{key}  FORWARD"
        out.blit(font.render(tag, True, (170, 170, 180)),
                 (i * cell[0] + 8, cell[1] + 2))
    pygame.image.save(out, "/tmp/scene_tilt.png")
    print(f"wrote /tmp/scene_tilt.png ({key})")
    if do_gif:
        try:
            from PIL import Image
        except ImportError:
            print("PIL missing; no gif"); return
        frames = []
        N = 60
        for i in range(N):
            yd = 45 * math.sin(i / N * 2 * math.pi)
            s = render(scene, yd, ptile, cell)
            frames.append(Image.frombytes(
                "RGB", cell, pygame.image.tostring(s, "RGB")).convert(
                "P", palette=Image.ADAPTIVE))
        frames[0].save("/tmp/scene_tilt.gif", save_all=True,
                       append_images=frames[1:], duration=70, loop=0)
        print("wrote /tmp/scene_tilt.gif")


if __name__ == "__main__":
    main()
