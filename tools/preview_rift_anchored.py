"""LIVE preview -- the ANCHORED rift frame, through the real game renderer.

Boots a real Game headlessly, stands the player in front of an actual
direction-gated fold (the cornfield maze's effigy-grove fold) and captures
draw_world() frames that prove the frame is an object IN the world:

  1. head-on        -- full pane: oriented base, ground pool, through-view
  2. oblique        -- the approach-angle falloff: it thins and dims
  3. circled        -- a different standpoint: the base edge foreshortens
                       with the view, like a wall (not a billboard)
  4. king forming   -- the King's rift mid-charge (the violent loud version)
  5. king formed    -- torn through: the one-way juke standing in the room

    python tools/preview_rift_anchored.py    # -> /tmp/rift_anchored.png
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


def _face(g, heading):
    """Point body, aim, camera and player facing at `heading` (radians)."""
    g.look.body = heading
    g.look.aim = heading
    g.look.cam_yaw = heading + math.pi / 2
    g.player.facing = (math.cos(heading), math.sin(heading))
    g.camera.yaw = g.look.cam_yaw
    g._update_camera(snap=True)


def _fold_face(g):
    """The first cross-scene fold in the loaded scene (skip relocations)."""
    for f in g._folds:
        if f["target"].key != g.scene.key:
            return f
    raise SystemExit("no visible fold in scene")


CROP_W, CROP_H = 300, 240          # world-window around the rift, 2x zoomed


def _shot(g, label, font, out, focus):
    """Draw the world and keep a 2x crop centred near `focus` (world px)."""
    g.draw_world()
    bx, by = g.camera.project(focus[0], focus[1])
    cx = max(0, min(SCREEN_W - CROP_W, bx - CROP_W // 2))
    cy = max(0, min(SCREEN_H - CROP_H, by - CROP_H // 2 - 30))
    crop = g.screen.subsurface((cx, cy, CROP_W, CROP_H)).copy()
    panel = pygame.transform.scale(crop, (CROP_W * 2, CROP_H * 2))
    bar = pygame.Surface((CROP_W * 2, 26))
    bar.fill((0, 0, 0))
    bar.blit(font.render(label, True, (228, 228, 218)), (8, 4))
    sheet = pygame.Surface((CROP_W * 2, CROP_H * 2 + 26))
    sheet.blit(panel, (0, 0))
    sheet.blit(bar, (0, CROP_H * 2))
    out.append(sheet)


def main():
    g = Game()
    g.save.new()
    g.audio.music_muted = True
    g._start_play()
    g.load_scene_now("cornfield_maze", "default")
    font = pygame.font.SysFont("monospace", 16)
    shots = []

    face = _fold_face(g)
    fx, fy = face["fold_px"]
    nx, ny = face["normal"]
    into = math.atan2(ny, nx)              # heading INTO the fold

    # 1. head-on, 2.5 tiles back along the normal.
    g.player.x = fx - nx * 2.5 * TILE
    g.player.y = fy - ny * 2.5 * TILE
    _face(g, into)
    _shot(g, "1. fold head-on -- the pane stands on its world seam", font,
          shots, (fx, fy))

    # 2. oblique approach: same spot, facing ~55 degrees off the normal.
    _face(g, into + math.radians(55))
    _shot(g, "2. oblique -- the pane dims toward nothing (no back)", font,
          shots, (fx, fy))

    # 3. circled: stand off-axis along the seam and look back at it. The
    # projected base edge foreshortens -- the object holds its place.
    g.player.x = fx - nx * 1.2 * TILE - ny * 2.2 * TILE
    g.player.y = fy - ny * 1.2 * TILE + nx * 2.2 * TILE
    to_fold = math.atan2(fy - g.player.y, fx - g.player.x)
    _face(g, to_fold)
    _shot(g, "3. circled -- the base edge foreshortens like a wall", font,
          shots, (fx, fy))

    # 4 + 5. The King's rift, forming then formed, in brimley.
    from scenes import load_scene
    g.load_scene_now("brimley", "default")
    px, py = g.player.x, g.player.y
    spot = (px + 3.0 * TILE, py - 1.5 * TILE)
    tgt = load_scene("cornfield_path")
    tp = tgt.spawns.get("default")
    dxp, dyp = px - spot[0], py - spot[1]
    ln = math.hypot(dxp, dyp) or 1.0
    portal = {
        "x": spot[0], "y": spot[1],
        "target": "cornfield_path", "spawn": "default", "target_pos": tp,
        "_scene": tgt, "anchor": (int(tp[0] // TILE), int(tp[1] // TILE)),
        "charge": 0.55, "formed": False,
        "seam_dir": (-dyp / ln, dxp / ln),
    }
    g._portal = portal
    _face(g, math.atan2(spot[1] - py, spot[0] - px))
    _shot(g, "4. the King's rift FORMING (charge 0.55) -- he looms through",
          font, shots, spot)

    portal["charge"] = 1.0
    portal["formed"] = True
    _shot(g, "5. FORMED -- the one-way juke, same frame torn loud", font,
          shots, spot)

    pw, ph = shots[0].get_size()
    cols = 3
    rows = (len(shots) + cols - 1) // cols
    sheet = pygame.Surface((pw * cols, ph * rows))
    sheet.fill((12, 12, 14))
    for i, s in enumerate(shots):
        sheet.blit(s, ((i % cols) * pw, (i // cols) * ph))
    pygame.image.save(sheet, "/tmp/rift_anchored.png")
    print("wrote /tmp/rift_anchored.png")


if __name__ == "__main__":
    main()
