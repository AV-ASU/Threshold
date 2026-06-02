"""Volumetric NON-box props for the oblique camera (CAMERA.md Phase 4 dress).

rendering/furniture.py turns upright furniture into axis-aligned BOXES. This is
its sibling for the shapes a box can't express -- bodies of revolution: the
**well** (a round stone drum with a winch gallows), stone **pillars**, cistern
**basins** brimming with black water, and raked **grain heaps**. Each is keyed
by decoration `kind`, drawn through the same Camera in the tilt path (depth
sorted alongside furniture). The flat top-down game (F3) never calls this -- it
falls back to the 2D `_draw_<kind>` sprites in entities/decoration.py.
"""
import math
import pygame
from rendering.solids import draw_solid, _shade


def _disc(surf, cam, wx, wy, hz, rx, ry, col, fill=True, width=2):
    """A pitch-squashed ellipse cap at world height hz (radii in world px)."""
    cx, cy = cam.project(wx, wy, hz)
    hw = int(rx * cam.scale)
    hd = int(ry * cam.ground_squash() * cam.scale)
    if hw < 1 or hd < 1:
        return
    pygame.draw.ellipse(surf, col, (cx - hw, cy - hd, hw * 2, hd * 2),
                        0 if fill else max(1, width))


def _draw_well_solid(surf, cam, deco):
    """The wellhead, as a real volume: a fitted-stone drum, a mossy cap, the
    black shaft mouth, a timber winch gallows (two posts + beam), and the rope
    descending into the dark. The ONLY way down into the Works -- now it reads
    like a thing you could lean over and fall into."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 17 * s
    drum = {"body": (96, 94, 100), "lo": (52, 50, 56), "rim": (152, 152, 164)}
    draw_solid(surf, cam, wx, wy,
               [(0, R, R), (11 * s, R, R), (15 * s, R * 0.94, R * 0.94)], drum)
    # mossy cap ring + the black shaft mouth on the rim
    _disc(surf, cam, wx, wy, 15 * s, R * 0.94, R * 0.94, (64, 82, 58),
          fill=False, width=2)
    _disc(surf, cam, wx, wy, 15 * s, R * 0.66, R * 0.66, (7, 7, 9))
    # timber winch gallows: two posts at the near rim + a cross-beam, drawn
    # at the front of the drum (wy + R*0.6) so they read as flanking timbers
    post = (120, 88, 52)
    beam_h = 30 * s
    py = wy + R * 0.6
    lw = max(2, int(3 * s))
    for ox in (-R * 0.9, R * 0.9):
        b = cam.project(wx + ox, py, 0)
        t = cam.project(wx + ox, py, beam_h)
        pygame.draw.line(surf, post, b, t, lw)
        pygame.draw.line(surf, _shade(post, 0.7), b, t, 1)
    bl = cam.project(wx - R * 0.9, py, beam_h)
    br = cam.project(wx + R * 0.9, py, beam_h)
    pygame.draw.line(surf, _shade(post, 1.2), bl, br, lw)
    # rope from the beam centre down into the shaft
    rt = cam.project(wx, py, beam_h - 1 * s)
    rb = cam.project(wx, wy, 11 * s)
    pygame.draw.line(surf, (152, 132, 94), rt, rb, max(1, int(2 * s)))


def _draw_pillar_solid(surf, cam, deco):
    """A round fitted-stone column with a flared base + capital, rising into
    the dark -- a colonnade upright + an occluder to round."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 9 * s
    H = 50 * s
    pal = {"body": (104, 101, 106), "lo": (56, 54, 58), "rim": (150, 148, 154)}
    draw_solid(surf, cam, wx, wy,
               [(0, R * 1.18, R * 1.18), (5 * s, R, R),
                (H - 5 * s, R, R), (H, R * 1.2, R * 1.2)], pal)
    # faint banded joints
    for hz in (18 * s, 33 * s):
        _disc(surf, cam, wx, wy, hz, R, R, _shade(pal["lo"], 1.05),
              fill=False, width=1)


def _draw_cistern_basin_solid(surf, cam, deco):
    """A low round stone basin brimming with black water, a cold sheen on it."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 13 * s
    H = 11 * s
    pal = {"body": (92, 96, 98), "lo": (50, 54, 56), "rim": (140, 146, 148)}
    draw_solid(surf, cam, wx, wy, [(0, R, R), (H, R, R)], pal)
    _disc(surf, cam, wx, wy, H, R * 0.82, R * 0.82, (14, 22, 26))
    _disc(surf, cam, wx, wy, H, R * 0.5, R * 0.5, (32, 52, 60),
          fill=False, width=1)


def _draw_grain_heap_solid(surf, cam, deco):
    """A raked cone of tithed grain, the dark of old blood pooled at its base."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    R = 15 * s
    H = 13 * s
    pal = {"body": (150, 126, 70), "lo": (80, 64, 35), "rim": (198, 174, 110)}
    draw_solid(surf, cam, wx, wy,
               [(0, R, R), (H * 0.6, R * 0.6, R * 0.6),
                (H, R * 0.12, R * 0.12)], pal)
    _disc(surf, cam, wx, wy, 0.5, R * 0.96, R * 0.96, (60, 30, 28),
          fill=False, width=2)


SOLID_PROPS = {
    "well":          _draw_well_solid,
    "pillar":        _draw_pillar_solid,
    "cistern_basin": _draw_cistern_basin_solid,
    "grain_heap":    _draw_grain_heap_solid,
}


def is_solid_prop(kind):
    return kind in SOLID_PROPS


def draw_prop_solid(surf, cam, deco):
    """Draw one decoration as a volumetric body-of-revolution prop. Returns
    True if it was a known solid prop (and drawn), False otherwise so the
    caller can fall back."""
    fn = SOLID_PROPS.get(deco.kind)
    if fn is None:
        return False
    fn(surf, cam, deco)
    return True
