"""See-through door ACTOR sight-gating preview (PORTALS.md; TODO #2).

The see-through door already showed the ACTUAL room beyond through the opening,
rendered with the live tilt camera -- but the through-view showed that room
UNGATED, so a threat standing in it would leak through the door regardless of
where the player was looking. That breaks the restricted-sight thesis the game
rests on (unlike the King's rift, which shows all by design).

This boots a real Game, stands the player at a see-through interior door, plants
a figure in the room BEYOND it, and captures the same door while the player
looks AT the opening vs AWAY. With the gate wired, the figure reads through the
door only when it falls in the player's sight cone; look away and the room
beyond reads empty -- the far figure re-hides, same as the open world.

    python tools/preview_door_sight.py   -> /tmp/door_sight.png
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
from entities.npc import NPC

CROP_W, CROP_H = 150, 140
ZOOM = 4


def _frame_north(g):
    """Point the CAMERA north at the door once, so both panels share framing."""
    g.look.body = -math.pi / 2
    g.look.cam_yaw = 0.0
    g.player.facing = (0.0, -1.0)
    g.camera.yaw = 0.0
    g._update_camera(snap=True)


def _aim(g, heading):
    """Move only the SIGHT cone (look.aim) -- the camera stays put, so the door
    holds its screen position while the gaze sweeps on/off it."""
    g.look.aim = heading


def _shot(g, label, font, out, focus):
    g.draw_world()
    bx, by = g.camera.project(*focus)
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2))
    crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * ZOOM, CROP_H * ZOOM))
    bar = pygame.Surface((CROP_W * ZOOM, 24))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * ZOOM, CROP_H * ZOOM + 24))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * ZOOM))
    out.append(sheet)


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()
    g.load_scene_now("house", "default")
    font = pygame.font.SysFont("monospace", 15)

    # Door "B" -> bedroom sits at tile (13, 0) on the north wall. Plant a figure
    # in the bedroom's through-view, just past its arrival anchor so it stands
    # framed in the opening.
    door_tile = (13, 0)
    view = g.scene._door_views.get(door_tile)
    if view is None:
        print("no door view built; abort"); return
    target = view["target"]
    ax, ay = view["anchor_px"]
    lurker = NPC(ax, ay - 0.4 * TILE, "Figure", "cultist", movement="idle")
    lurker.facing = (0.0, 1.0)            # facing back toward the doorway
    target.npcs = [lurker]

    # Stand the player a couple tiles south of the door, looking north at it.
    g.player.x = door_tile[0] * TILE + TILE / 2
    g.player.y = door_tile[1] * TILE + 3.0 * TILE
    focus = (g.player.x, door_tile[1] * TILE + TILE / 2)

    shots = []
    _frame_north(g)                      # camera fixed on the door for both
    _aim(g, -math.pi / 2)                # gaze ON the door (north)
    _shot(g, "1. gaze on the door -- the figure beyond reads through it",
          font, shots, focus)
    _aim(g, -math.pi / 2 + math.radians(115))   # gaze swept off the door
    _shot(g, "2. gaze swept aside -- the room beyond reads EMPTY (figure hidden)",
          font, shots, focus)

    pw, ph = shots[0].get_size()
    sheet = pygame.Surface((pw, ph * len(shots)))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, (0, i * ph))
    pygame.image.save(sheet, "/tmp/door_sight.png")
    print("wrote /tmp/door_sight.png")


if __name__ == "__main__":
    main()
