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
WALL_RISE = 30          # world height that can poke into view above the floor


class _P:
    """Minimal stand-in player for draw_fold + placement."""
    def __init__(self, x, y, facing):
        self.x = x; self.y = y; self.facing = facing


def window_half_span(cam, cell):
    """Smallest centered (on cam_x/cam_y) square half-span, in world px, that
    still covers the whole tilted screen. Unproject the four screen corners
    (plus an upward margin so tall walls at the top edge are included) and
    take the farthest world offset from center."""
    W, H = cell
    corners = [(0, 0), (W, 0), (0, H), (W, H),
               (W // 2, -WALL_RISE)]   # top-edge wall headroom
    half = 0.0
    for sx, sy in corners:
        wx, wy = cam.unproject(sx, sy)
        half = max(half, abs(wx - cam.cam_x), abs(wy - cam.cam_y))
    return half + TILE                 # one tile of slack


def render_flat_window(scene, cx, cy, half_span):
    """Flat raster of the world window centered on world (cx, cy), wrapping
    past map bounds (seamless across wrap seams)."""
    span = int(half_span * 2)
    surf = pygame.Surface((span, span))
    surf.fill((10, 10, 14))
    wx0 = cx - half_span
    wy0 = cy - half_span
    x0 = int(math.floor(wx0 / TILE))
    y0 = int(math.floor(wy0 / TILE))
    x1 = int(math.ceil((wx0 + span) / TILE))
    y1 = int(math.ceil((wy0 + span) / TILE))
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
    """A trimmed draw_fold proving placement under tilt: build the target
    peek, fog-mask it, and stand it up as a tear whose BASE follows the
    projected floor seam (s0->s1) and whose sides rise straight up (world-z
    projects vertically). Anchored to the seam, not floating."""
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
    big = pygame.Surface((w, h))
    big.fill((8, 8, 11))
    target.draw(big, ax * TILE + 16 - w // 2, ay * TILE + 16 - h // 2)
    apply_grade(big, 1.0)
    peek = big.convert_alpha()
    import numpy as np
    mask = _fog_mask(w, h, face["normal"])
    pa = pygame.surfarray.pixels_alpha(peek)
    pa[:, :] = (mask * 255).astype(np.uint8)
    del pa

    # The seam is a short floor segment perpendicular to the normal at fold_px.
    seam_len = SEAM_TILES * TILE
    if nx != 0:                                   # vertical seam runs along y
        w0 = (fold_x, fold_y - seam_len / 2)
        w1 = (fold_x, fold_y + seam_len / 2)
    else:                                         # horizontal seam runs along x
        w0 = (fold_x - seam_len / 2, fold_y)
        w1 = (fold_x + seam_len / 2, fold_y)
    s0 = cam.project(*w0)
    s1 = cam.project(*w1)
    rise = int(seam_len * (0.5 + 0.7 * cam.ground_squash()))
    # Stand the (rotated-to-seam-direction) peek up from the seam base. The
    # base edge follows s0->s1; the height rises straight up the screen.
    _blit_tear(out, peek, s0, s1, rise)
    # the gold tear-seam, along the actual floor seam line
    pygame.draw.line(out, (214, 180, 74), s0, s1, 2)
    return True


def _blit_tear(out, peek, s0, s1, rise):
    """Stand `peek` up as a vertical panel whose base edge is the screen
    segment s0->s1 and whose top edge is that segment lifted `rise` px up
    the screen. Per-column vertical strips give the base its floor-seam slant
    while keeping the sides vertical (correct for projected world height)."""
    import pygame as pg
    pw, ph = peek.get_size()
    (x0, y0), (x1, y1) = s0, s1
    cols = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    for i in range(cols):
        f = i / (cols - 1)
        bx = x0 + (x1 - x0) * f
        by = y0 + (y1 - y0) * f
        src_x = min(pw - 1, int(f * pw))
        strip = peek.subsurface((src_x, 0, 1, ph))
        strip = pg.transform.scale(strip, (2, rise))
        out.blit(strip, (int(bx), int(by - rise)))


def render(scene, yaw_deg, px, py, facing, fold=None, cell=(440, 380)):
    S = (cell[0] // 2, int(cell[1] * 0.55))
    cam = make_cam(yaw_deg, px, py, S)
    out = pygame.Surface(cell)
    draw_skybox(out, (0, 0, cell[0], cell[1]), yaw=cam.yaw, kind="overcast",
                horizon_frac=0.40)
    half = window_half_span(cam, cell)
    flat, wx0, wy0 = render_flat_window(scene, px, py, half)
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
