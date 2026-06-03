"""Visualize the LookController on a real scene (headless) -- CAMERA.md Phase 3.

Scripts a mouse path through the control states and renders the world
responding, so the heading/rotation math + damping can be judged before live
wiring:
  1. cursor sweeps RIGHT a little  -> head leads (peek), world leans slightly
  2. cursor HELD far right         -> body comes around, world rotates to follow
  3. cursor returns centre         -> head re-centres
  4. RIGHT-MOUSE drag              -> free scene rotation (look around the room)

    python tools/preview_look_control.py [scene]  -> /tmp/look_control.png (+gif)
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
from scenes.base import (draw_terrain_tilted, _tilt_tile_box, TILE,
                         _TILT_WALL_RISE, _WALL_CHARS)
from rendering.camera import Camera
from rendering.skybox import draw_skybox
from rendering.sprites import draw_player_sprite
from systems.look_control import LookController, HEAD_MAX

PITCH = 55
CELL = (440, 380)


def _player_start(scene):
    cx, cy = scene.w // 2, scene.h // 2
    for r in range(max(scene.w, scene.h)):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                tx, ty = cx + dx, cy + dy
                if (0 <= tx < scene.w and 0 <= ty < scene.h
                        and scene.objects[ty][tx] == "."):
                    return (tx * TILE + TILE / 2, ty * TILE + TILE / 2)
    return (cx * TILE, cy * TILE)


def render(scene, lc, px, py, label, sub):
    cam = Camera(pitch=math.radians(PITCH), yaw=lc.cam_yaw, scale=0.72)
    cam.cam_x, cam.cam_y = px, py
    cam.origin = (CELL[0] // 2, int(CELL[1] * 0.55))
    out = pygame.Surface(CELL)
    draw_skybox(out, (0, 0, CELL[0], CELL[1]), yaw=cam.yaw, kind="void",
                horizon_frac=0.40)
    walls, _solids = draw_terrain_tilted(out, scene, cam)
    # walls behind the player first, player, then walls in front (Phase 5 the
    # game depth-sorts these per-actor; this preview keeps a simple player split)
    pdepth = cam.depth(px, py)
    behind = [w for w in walls
              if cam.depth(w[0] * TILE + TILE / 2, w[1] * TILE + TILE / 2,
                           _TILT_WALL_RISE) <= pdepth]
    front = [w for w in walls if w not in behind]
    for tx, ty in behind:
        _tilt_tile_box(out, cam, scene, tx, ty)
    # player at centre; the body faces "up" by construction, but show the head
    # lead by tilting the drawn facing a touch.
    spr = pygame.Surface((40, 52), pygame.SRCALPHA)
    draw_player_sprite(spr, 20, 34, (0, -1), 0)
    bx, by = cam.project(px, py, 0)
    out.blit(spr, (int(bx - 20), int(by - 30)))
    for tx, ty in front:
        _tilt_tile_box(out, cam, scene, tx, ty)
    # HUD: a reticle showing where the aim/head points (screen-relative)
    ang = -math.pi / 2 + lc.head_off          # up + head offset, screen space
    rx = bx + math.cos(ang) * 60
    ry = by + math.sin(ang) * 60
    pygame.draw.line(out, (210, 180, 80), (bx, by - 18), (rx, ry), 2)
    pygame.draw.circle(out, (230, 200, 90), (int(rx), int(ry)), 4, 1)
    f = pygame.font.SysFont("monospace", 13)
    f2 = pygame.font.SysFont("monospace", 11)
    out.blit(f.render(label, True, (210, 200, 150)), (8, 6))
    out.blit(f2.render(sub, True, (150, 150, 160)), (8, 22))
    deg = math.degrees(lc.head_off)
    out.blit(f2.render("head %+.0fdeg  body %3.0f  yaw %3.0f"
                       % (deg, math.degrees(lc.body) % 360,
                          math.degrees(lc.cam_yaw) % 360),
                       True, (130, 150, 130)), (8, CELL[1] - 16))
    return out


def script(scene, px, py):
    """Yield (label, sub, aim_heading|None, rmb_dx, rmb_held) per frame."""
    base = math.pi / 2          # facing 'south' in world == default
    # 1. peek right (aim leads within the 45 arc)
    for i in range(26):
        a = base + math.radians(35) * (i / 25)
        yield ("PEEK", "cursor drifts right -> head leads", a, 0, False)
    # 2. hold far right -> body catches up, world rotates
    for i in range(34):
        a = base + math.radians(80)
        yield ("BODY FOLLOWS", "held off-axis -> body comes around", a, 0, False)
    # 3. return to centre
    for i in range(24):
        a = base + math.radians(80) * (1 - i / 23)
        yield ("RE-CENTRE", "cursor back -> head relaxes", a, 0, False)
    # 4. RMB free-rotate the scene
    for i in range(40):
        yield ("RMB LOOK", "right-drag rotates the whole scene", None, 6, True)
    # 5. release -> relax
    for i in range(18):
        yield ("RELEASE", "free rotation eases back", base, 0, False)


def main():
    key = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "sheriff_office"
    scene = load_scene(key)
    px, py = _player_start(scene)
    lc = LookController(heading=math.pi / 2)

    # strip: one frame per phase
    phases = {}
    frames = []
    for label, sub, aim, dx, held in script(scene, px, py):
        lc.update(aim, dx, held)
        frames.append(render(scene, lc, px, py, label, sub))
        phases.setdefault(label, frames[-1])
    # contact strip of the 5 phases
    keys = ["PEEK", "BODY FOLLOWS", "RE-CENTRE", "RMB LOOK", "RELEASE"]
    strip = pygame.Surface((CELL[0] * len(keys), CELL[1]))
    strip.fill((6, 6, 8))
    for i, k in enumerate(keys):
        strip.blit(phases[k], (i * CELL[0], 0))
    pygame.image.save(strip, "/tmp/look_control.png")
    print("wrote /tmp/look_control.png")
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; no gif"); return
    gif = [Image.frombytes("RGB", CELL, pygame.image.tostring(f, "RGB")).convert(
        "P", palette=Image.ADAPTIVE) for f in frames]
    gif[0].save("/tmp/look_control.gif", save_all=True, append_images=gif[1:],
                duration=60, loop=0)
    print("wrote /tmp/look_control.gif")


if __name__ == "__main__":
    main()
