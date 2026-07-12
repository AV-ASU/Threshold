"""Visualize the LookController on a real scene (headless) -- DESIGN.md §10.

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
from systems.look_control import LookController, wrap

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
    walls, _solids, _walldecos = draw_terrain_tilted(out, scene, cam)
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
    # HUD: a free-aim reticle. The camera-up is the body, so the aim's screen
    # angle is up + (aim - body); the reticle moves with the cursor, not the cam.
    aim_off = wrap(lc.aim - lc.body)
    ang = -math.pi / 2 + aim_off
    rx = bx + math.cos(ang) * 60
    ry = by + math.sin(ang) * 60
    pygame.draw.line(out, (210, 180, 80), (bx, by - 18), (rx, ry), 2)
    pygame.draw.circle(out, (230, 200, 90), (int(rx), int(ry)), 4, 1)
    f = pygame.font.SysFont("monospace", 13)
    f2 = pygame.font.SysFont("monospace", 11)
    out.blit(f.render(label, True, (210, 200, 150)), (8, 6))
    out.blit(f2.render(sub, True, (150, 150, 160)), (8, 22))
    out.blit(f2.render("aim %+.0fdeg  body %3.0f  yaw %3.0f"
                       % (math.degrees(aim_off), math.degrees(lc.body) % 360,
                          math.degrees(lc.cam_yaw) % 360),
                       True, (130, 150, 130)), (8, CELL[1] - 16))
    return out


def script(scene, px, py):
    """Yield (label, sub, turn_delta, aim_heading|None) per frame -- tank model:
    turn_delta is A/D steering (radians this frame); aim is the free cursor."""
    base = math.pi / 2          # facing 'south' in world == default
    step = math.radians(2.5)    # per-frame turn while 'holding' A/D
    # 1. free aim: cursor swings right, the gun reticle follows, camera holds
    for i in range(26):
        a = base + math.radians(80) * (i / 25)
        yield ("FREE AIM", "cursor moves -> reticle only, camera holds", 0.0, a)
    # 2. hold D: the heading (and the camera behind it) turn right
    for i in range(34):
        yield ("TURN (D)", "A/D steer the heading + camera", step, base + math.radians(80))
    # 3. settle: stop turning, camera holds the new heading
    for i in range(20):
        yield ("SETTLED", "released -> camera holds the heading", 0.0, None)
    # 4. aim across the new heading (decoupled aim vs facing)
    for i in range(40):
        a = base + math.radians(80) - math.radians(150) * (i / 39)
        yield ("AIM != FACE", "aim left while facing right", 0.0, a)
    # 5. hold A: turn back the other way
    for i in range(18):
        yield ("TURN (A)", "steer back left", -step, base)


def main():
    key = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "sheriff_office"
    scene = load_scene(key)
    px, py = _player_start(scene)
    lc = LookController(heading=math.pi / 2)

    # strip: one frame per phase
    phases = {}
    frames = []
    for label, sub, turn_d, aim in script(scene, px, py):
        if turn_d:
            lc.turn(turn_d)
        lc.update(aim_heading=aim)
        frames.append(render(scene, lc, px, py, label, sub))
        phases.setdefault(label, frames[-1])
    # contact strip of the 5 phases
    keys = ["FREE AIM", "TURN (D)", "SETTLED", "AIM != FACE", "TURN (A)"]
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
