"""Ground heightfield preview -- blind-spot hills (DESIGN.md §10).

Boots a real Game headlessly, attaches a ground heightfield (one rounded hill)
to the live scene, and renders the REAL tilt pipeline so you can see:

  * the ground SWELL -- the projected floor mesh (rendering.heightfield) rolling
    over the flat raster;
  * an actor RIDING the crest -- a standee lifted by Scene.ground_z sits on the
    surface, not floating over a flat floor;
  * the BLIND-SPOT over the hill -- a figure on the far slope is HIDDEN from a
    player at the base (the crest occludes line of sight, same as a wall) and
    RESOLVES as the player climbs to the top. This is the dread payoff: a hill
    you can't see over hides what is beyond it.

    python tools/preview_heightfield.py   -> /tmp/heightfield.png (+ .gif)

Prototype behind a preview, per the ticket -- the infra (Scene.ground_z, the
sight crest term, the mesh renderer) is wired but dormant until a scene opts in
via Scene.set_ground, so shipping scenes stay dead-flat and pitch-0 identical.
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
from systems.game import Game
from systems.config import TILT_ACTOR_STAND
from rendering.heightfield import build_heightfield
from rendering.sprites import draw_npc_sprite, view_from_facing
from rendering.sight import visible_factor, SIGHT_EYE_H

CROP_W, CROP_H = 360, 300

# The hill sits a few tiles north of where we drop the player. Peak height in
# world-z px -- tall enough that a standing eye (SIGHT_EYE_H) can't see over it
# from the base, so the far-slope figure hides.
HILL_PEAK = 78.0
HILL_RADIUS = 5.5


def _face(g, heading):
    g.look.body = heading
    g.look.aim = heading
    g.look.cam_yaw = heading + math.pi / 2
    g.player.facing = (math.cos(heading), math.sin(heading))
    g.camera.yaw = g.look.cam_yaw
    g._update_camera(snap=True)


def _standee(g, wx, wy, kind, facing):
    """Draw one NPC standee at world (wx, wy) through the live camera, lifted by
    the ground height so it stands ON the swell -- the actor-lift the live wiring
    would apply. Faded by the player's sight cone + the ground-crest LOS, so a
    figure the hill hides is dim/gone exactly as the game would cull it."""
    gz = g.scene.ground_z(wx, wy)
    sx, sy = g.camera.project(wx, wy, gz)
    sy -= int(TILT_ACTOR_STAND * math.sin(g.camera.pitch))
    f = visible_factor(g.player.x, g.player.y, g.look.aim, wx, wy,
                       g.scene.blocks_sight, ground=g.scene.ground_z,
                       eye=SIGHT_EYE_H)
    view = view_from_facing(facing[0], facing[1], g.camera.yaw)
    if f <= 0.04:
        return sx, sy, 0.0                     # hidden: the game draws nothing
    layer = pygame.Surface((220, 250), pygame.SRCALPHA)
    draw_npc_sprite(layer, 110, 160, kind, facing, view=view)
    if f < 0.99:
        layer.set_alpha(int(255 * f))
    g.screen.blit(layer, (sx - 110, sy - 160))
    return sx, sy, f


def _shot(g, label, font, out, extra_npcs):
    g.draw_world()
    marks = []
    for (wx, wy, kind, facing) in extra_npcs:
        marks.append((label,) + _standee(g, wx, wy, kind, facing))
    # 2x crop centred a little ahead of the player so the hill fills the panel.
    fx, fy = g.player.x, g.player.y - 2.0 * TILE
    bx, by = g.camera.project(fx, fy)
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2))
    crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * 2, CROP_H * 2))
    bar = pygame.Surface((CROP_W * 2, 24))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * 2, CROP_H * 2 + 24))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * 2))
    out.append(sheet)


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()
    g.load_scene_now("store_row", "default")
    # Isolate the demo: clear the town's own residents so the swell + the two
    # demo figures read clean (this is a spike, not the live scene).
    g.scene.npcs = []
    g.scene.enemies = []
    font = pygame.font.SysFont("monospace", 15)

    px, py = g.player.x, g.player.y
    # A hill centred ~4 tiles north of the player.
    hcx = px / TILE
    hcy = py / TILE - 4.0
    hf = build_heightfield(g.scene.w, g.scene.h,
                           [(hcx, hcy, HILL_RADIUS, HILL_PEAK)])
    g.scene.set_ground(hf)

    _face(g, -math.pi / 2)                       # look north, up the slope

    # A figure standing ON the crest, and one on the FAR slope beyond it.
    crest = (px, py - 4.0 * TILE)
    beyond = (px, py - 7.2 * TILE)
    facing_s = (0.0, 1.0)                        # facing the player (south)

    shots = []
    # 1. Player at the base: the crest figure rides the swell; the far figure
    #    is HIDDEN behind the hill.
    _shot(g, "1. at the base -- crest figure shows, far slope HIDDEN", font,
          shots, [(crest[0], crest[1], "townsman", facing_s),
                  (beyond[0], beyond[1], "cultist", facing_s)])

    # 2. Player climbs onto the crest: the far figure RESOLVES (you can now see
    #    over the hill).
    g.player.y = py - 4.0 * TILE
    _face(g, -math.pi / 2)
    _shot(g, "2. on the crest -- you see over: far figure RESOLVES", font,
          shots, [(beyond[0], beyond[1], "cultist", facing_s)])

    # 3. Look away from the hill: it re-hides (the swell is a blind spot too).
    g.player.y = py
    _face(g, math.pi / 2)                        # look south, away
    _shot(g, "3. look away -- the far slope re-hides", font, shots,
          [(beyond[0], beyond[1], "cultist", facing_s)])

    pw, ph = shots[0].get_size()
    sheet = pygame.Surface((pw, ph * len(shots)))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, (0, i * ph))
    pygame.image.save(sheet, "/tmp/heightfield.png")
    print("wrote /tmp/heightfield.png")


if __name__ == "__main__":
    main()
