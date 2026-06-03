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


def _vbox(surf, cam, wx, wy, w, d, z0, z1, pal, yaw=0.0, outline=True):
    """A box from height z0 to z1 (footprint w x d), yaw-rotated about its
    centre -- used to stack a vehicle from a body + cabin + wheels."""
    hw, hd = w / 2.0, d / 2.0
    c, s = math.cos(yaw), math.sin(yaw)

    def P(sx, sy, sz):
        return cam.project(wx + sx * c - sy * s, wy + sx * s + sy * c, sz)
    fbl, fbr = P(-hw, hd, z0), P(hw, hd, z0)        # near bottom
    tbl, tbr = P(-hw, hd, z1), P(hw, hd, z1)        # near top
    bbl, bbr = P(-hw, -hd, z0), P(hw, -hd, z0)      # far bottom
    ttl, ttr = P(-hw, -hd, z1), P(hw, -hd, z1)      # far top
    pygame.draw.polygon(surf, pal["side"], [bbl, fbl, tbl, ttl])   # left
    pygame.draw.polygon(surf, pal["side"], [bbr, fbr, tbr, ttr])   # right
    pygame.draw.polygon(surf, pal["dark"], [fbl, fbr, tbr, tbl])   # near face
    pygame.draw.polygon(surf, pal["top"], [tbl, tbr, ttr, ttl])    # top
    if outline:
        pygame.draw.polygon(surf, _shade(pal["top"], 0.55),
                            [tbl, tbr, ttr, ttl], 1)


def _vehicle_shadow(surf, cam, wx, wy, bl, bw):
    shw = max(4, int(bl * 0.5 * cam.scale * 1.05))
    shh = max(2, int(bw * 0.5 * cam.ground_squash() * cam.scale * 1.05))
    bx, by = cam.project(wx, wy, 0)
    sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 100), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (bx - shw - 2, by - shh - 2))


_WHEEL = {"top": (26, 24, 26), "side": (16, 15, 17), "dark": (8, 8, 10)}


def _vehicle_wheels(surf, cam, wx, wy, bl, bw, yaw, r=5):
    c, s = math.cos(yaw), math.sin(yaw)
    for ex in (-bl * 0.30, bl * 0.30):
        for ey in (-bw * 0.48, bw * 0.48):
            wxr = wx + ex * c - ey * s
            wyr = wy + ex * s + ey * c
            _vbox(surf, cam, wxr, wyr, r * 1.6, r * 1.1, 0, r, _WHEEL,
                  yaw=yaw, outline=False)


def _draw_car_solid(surf, cam, deco):
    """A 1994 sedan as a real volume: a low body on four wheels with a glassed
    cabin set back on top, headlights at the nose. Faded, dead-paint palette."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    bl, bw, bh = 50 * s, 26 * s, 12 * s             # body (length along local x)
    body = {"top": (92, 100, 106), "side": (64, 72, 78), "dark": (40, 46, 52)}
    cab = {"top": (60, 70, 78), "side": (44, 52, 58), "dark": (26, 32, 38)}
    _vehicle_shadow(surf, cam, wx, wy, bl, bw)
    _vehicle_wheels(surf, cam, wx, wy, bl, bw, yaw)
    _vbox(surf, cam, wx, wy, bl, bw, 4 * s, bh, body, yaw=yaw)
    # cabin: shorter, set slightly back (-x), raised onto the body
    cx = -6 * s
    _vbox(surf, cam, wx + cx * math.cos(yaw), wy + cx * math.sin(yaw),
          24 * s, bw * 0.86, bh, bh + 11 * s, cab, yaw=yaw)
    # headlights at the nose (+x end)
    hx = bl * 0.5
    for ey in (-bw * 0.34, bw * 0.34):
        hp = cam.project(wx + hx * math.cos(yaw) - ey * math.sin(yaw),
                         wy + hx * math.sin(yaw) + ey * math.cos(yaw), 7 * s)
        pygame.draw.circle(surf, (214, 208, 172), (int(hp[0]), int(hp[1])),
                           max(1, int(2 * s)))


def _draw_pickup_truck_solid(surf, cam, deco):
    """A pickup: a cab at the front (+x) and an open bed behind, on four wheels.
    Faded farm-green paint, rust at the seams implied by the dark palette."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    bl, bw, bh = 54 * s, 26 * s, 11 * s
    body = {"top": (88, 96, 78), "side": (62, 70, 54), "dark": (38, 44, 32)}
    cab = {"top": (70, 78, 62), "side": (50, 56, 44), "dark": (30, 36, 26)}
    _vehicle_shadow(surf, cam, wx, wy, bl, bw)
    _vehicle_wheels(surf, cam, wx, wy, bl, bw, yaw)
    _vbox(surf, cam, wx, wy, bl, bw, 4 * s, bh, body, yaw=yaw)
    # cab at the front (+x), raised
    cx = bl * 0.26
    _vbox(surf, cam, wx + cx * math.cos(yaw), wy + cx * math.sin(yaw),
          18 * s, bw * 0.9, bh, bh + 12 * s, cab, yaw=yaw)
    # low bed rim at the back so it reads as an open bed
    rx = -bl * 0.28
    _vbox(surf, cam, wx + rx * math.cos(yaw), wy + rx * math.sin(yaw),
          22 * s, bw, bh, bh + 4 * s, body, yaw=yaw, outline=False)


SOLID_PROPS = {
    "well":          _draw_well_solid,
    "pillar":        _draw_pillar_solid,
    "cistern_basin": _draw_cistern_basin_solid,
    "grain_heap":    _draw_grain_heap_solid,
    "player_car":    _draw_car_solid,
    "pickup_truck":  _draw_pickup_truck_solid,
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
