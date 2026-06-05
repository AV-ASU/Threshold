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
from rendering.solids import draw_solid, draw_billboard, _shade


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


def _draw_stalagmite_solid(surf, cam, deco):
    """A wet limestone spike rising from the cave floor -- a tapered cone (body
    of revolution), so it stands oriented in the room and occludes/depth-sorts
    instead of facing the camera. Height + girth vary by seed; a damp sheen
    catches the dark near the tip."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    seed = getattr(deco, "seed", 0)
    R = (5 + (seed % 5)) * s
    H = (18 + (seed % 16)) * s
    lean = ((seed % 7) - 3) * 0.4 * s           # a slight off-vertical lean
    pal = {"body": (96, 94, 100), "lo": (48, 48, 54), "rim": (150, 150, 160)}
    # taper base -> point; the apex section is offset by `lean` so it isn't a
    # perfectly upright cone (caves don't grow them straight).
    draw_solid(surf, cam, wx, wy,
               [(0, R, R * 0.78), (H * 0.5, R * 0.55, R * 0.46),
                (H, R * 0.12, R * 0.12)], pal)
    tip = cam.project(wx + lean, wy, H * 0.86)
    pygame.draw.circle(surf, pal["rim"], (int(tip[0]), int(tip[1])),
                       max(1, int(1.6 * s)))
    wet = cam.project(wx - R * 0.3, wy + R * 0.2, H * 0.35)
    pygame.draw.circle(surf, (118, 122, 130), (int(wet[0]), int(wet[1])),
                       max(1, int(1.2 * s)))


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
    pygame.draw.ellipse(sh, (0, 0, 0, 105), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (bx - shw - 2, by - shh - 2))


def _vframe(cam, wx, wy, yaw):
    """A local->screen projector for a vehicle: local (lx along length, ly across
    width, lz height) rotated by yaw about the placement and projected."""
    c, s = math.cos(yaw), math.sin(yaw)

    def P(lx, ly, lz):
        return cam.project(wx + lx * c - ly * s, wy + lx * s + ly * c, lz)
    return P


def _qp(surf, P, locs, col, w=0):
    pygame.draw.polygon(surf, col,
                        [(int(x), int(y)) for x, y in (P(*p) for p in locs)], w)


def _lp(surf, P, a, b, col, w=1):
    pa, pb = P(*a), P(*b)
    pygame.draw.line(surf, col, (int(pa[0]), int(pa[1])),
                     (int(pb[0]), int(pb[1])), w)


def _round_wheel(surf, P, lx, ly, r):
    """A tyre as a real disc standing in the length/height plane at local
    (lx, ly): a 12-gon black tyre + a metal hubcap, projected through the
    camera so it reads as a round wheel at the oblique angle."""
    n = 12
    pts = [P(lx + math.cos(math.tau * i / n) * r, ly,
             r + math.sin(math.tau * i / n) * r) for i in range(n)]
    pts = [(int(x), int(y)) for x, y in pts]
    pygame.draw.polygon(surf, (20, 20, 22), pts)        # tyre
    pygame.draw.polygon(surf, (46, 46, 50), pts, 1)
    h = P(lx, ly, r)
    hr = max(2, int(r * 0.46))
    pygame.draw.circle(surf, (120, 122, 128), (int(h[0]), int(h[1])), hr)
    pygame.draw.circle(surf, (64, 66, 72), (int(h[0]), int(h[1])), hr, 1)
    pygame.draw.circle(surf, (170, 172, 178), (int(h[0]), int(h[1])), max(1, hr // 2))


def _draw_car_solid(surf, cam, deco):
    """A 1994 sedan as a real volume: a low body on four round wheels, a glassed
    cabin set back on top (side + windshield + rear glass with a B-pillar), a
    chrome grille + bumpers, headlights at the nose and red tail-lamps, a door
    seam + handle + side trim. Faded dead-paint palette."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    P = _vframe(cam, wx, wy, yaw)
    L, W = 52 * s, 26 * s
    hL, hW = L / 2, W / 2
    z0, z1 = 5 * s, 14 * s                        # body band
    cz1 = z1 + 11 * s                             # cabin top
    cf, cb = 9 * s, -17 * s                       # cabin front / back (local x)
    chW = W * 0.84 / 2
    r, wbx = 6 * s, hL * 0.60                      # wheel radius + wheelbase
    body = {"top": (96, 104, 110), "side": (66, 74, 80), "dark": (42, 48, 54)}
    cab = {"top": (58, 68, 76), "side": (42, 50, 56), "dark": (24, 30, 36)}
    glass, glass_hi, chrome = (46, 60, 64), (98, 118, 124), (172, 176, 184)
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    _round_wheel(surf, P, wbx, -hW, r)            # far wheels (behind body)
    _round_wheel(surf, P, -wbx, -hW, r)
    _vbox(surf, cam, wx, wy, L, W, z0, z1, body, yaw=yaw)
    ccx = (cf + cb) / 2
    _vbox(surf, cam, wx + ccx * math.cos(yaw), wy + ccx * math.sin(yaw),
          cf - cb, W * 0.84, z1, cz1, cab, yaw=yaw)
    ny = hW + 0.2                                  # near side plane
    # cabin glass: near-side band (with B-pillar + top highlight), windshield, rear
    _qp(surf, P, [(cb + 2, chW + 0.2, z1 + 1.5), (cf - 2, chW + 0.2, z1 + 1.5),
                  (cf - 2, chW + 0.2, cz1 - 1.5), (cb + 2, chW + 0.2, cz1 - 1.5)], glass)
    _lp(surf, P, (ccx, chW + 0.3, z1 + 1.5), (ccx, chW + 0.3, cz1 - 1.5), cab["dark"], 1)
    _lp(surf, P, (cb + 2, chW + 0.3, cz1 - 1.6), (cf - 2, chW + 0.3, cz1 - 1.6), glass_hi, 1)
    _qp(surf, P, [(cf, -chW, z1 + 1.5), (cf, chW, z1 + 1.5),
                  (cf, chW, cz1 - 1.5), (cf, -chW, cz1 - 1.5)], glass)
    _qp(surf, P, [(cb, -chW, z1 + 1.5), (cb, chW, z1 + 1.5),
                  (cb, chW, cz1 - 1.5), (cb, -chW, cz1 - 1.5)], glass)
    # near-side door seam + handle + chrome trim
    _lp(surf, P, (-2 * s, ny, z0 + 1), (-2 * s, ny, z1), _shade(body["dark"], 0.8), 1)
    _lp(surf, P, (-7 * s, ny, z1 - 3 * s), (-12 * s, ny, z1 - 3 * s), chrome, 1)
    _lp(surf, P, (-hL + 3, ny, z0 + 4 * s), (hL - 3, ny, z0 + 4 * s),
        _shade(body["side"], 1.3), 1)
    # bumpers (front bright, rear dim) + front grille bars
    _qp(surf, P, [(hL, -hW, z0), (hL, hW, z0), (hL, hW, z0 + 3 * s), (hL, -hW, z0 + 3 * s)], chrome)
    _qp(surf, P, [(-hL, -hW, z0), (-hL, hW, z0), (-hL, hW, z0 + 3 * s), (-hL, -hW, z0 + 3 * s)],
        _shade(chrome, 0.65))
    for ey in (-6 * s, -2 * s, 2 * s, 6 * s):
        _lp(surf, P, (hL, ey, z0 + 4 * s), (hL, ey, z1 - 2 * s), _shade(body["dark"], 0.7), 1)
    # head / tail lamps
    for ey in (-hW * 0.62, hW * 0.62):
        hp = P(hL, ey, z1 - 3 * s)
        pygame.draw.circle(surf, (230, 224, 188), (int(hp[0]), int(hp[1])), max(2, int(2.2 * s)))
        tp = P(-hL, ey, z1 - 3 * s)
        pygame.draw.circle(surf, (178, 42, 38), (int(tp[0]), int(tp[1])), max(2, int(2 * s)))
    _round_wheel(surf, P, wbx, hW, r)             # near wheels (exposed)
    _round_wheel(surf, P, -wbx, hW, r)
    _lp(surf, P, (-hL + 3, -hW + 2, z1), (hL - 3, -hW + 2, z1), _shade(body["top"], 1.15), 1)


def _draw_pickup_truck_solid(surf, cam, deco):
    """A pickup as a real volume: a cab at the front (glassed), an OPEN bed
    behind (recessed dark floor, side rails, a tailgate), four round wheels, a
    grille + bumper + lamps at the nose. Faded farm-green paint."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    yaw = float(deco.kwargs.get("yaw", 0.0))
    P = _vframe(cam, wx, wy, yaw)
    L, W = 56 * s, 27 * s
    hL, hW = L / 2, W / 2
    z0, z1 = 5 * s, 13 * s
    cf, cb = hL, 7 * s                             # cab spans nose -> x=7
    cz1 = z1 + 13 * s
    cW = W * 0.92
    chW = cW / 2
    r, wbx = 7 * s, hL * 0.62
    body = {"top": (92, 100, 82), "side": (64, 72, 56), "dark": (40, 46, 34)}
    cab = {"top": (74, 82, 66), "side": (52, 60, 46), "dark": (30, 36, 26)}
    glass, glass_hi, chrome = (46, 58, 60), (96, 114, 118), (166, 170, 176)
    _vehicle_shadow(surf, cam, wx, wy, L, W)
    _round_wheel(surf, P, wbx, -hW, r)
    _round_wheel(surf, P, -wbx, -hW, r)
    _vbox(surf, cam, wx, wy, L, W, z0, z1, body, yaw=yaw)
    ccx = (cf + cb) / 2
    _vbox(surf, cam, wx + ccx * math.cos(yaw), wy + ccx * math.sin(yaw),
          cf - cb, cW, z1, cz1, cab, yaw=yaw)
    # OPEN bed behind the cab: recessed dark floor + side rails + tailgate
    bf, bb = cb - 1 * s, -hL + 1
    railz = z1 + 5 * s
    _qp(surf, P, [(bb, -hW + 1, z1), (bf, -hW + 1, z1),
                  (bf, hW - 1, z1), (bb, hW - 1, z1)], (28, 30, 24))     # bed floor
    for ly in (-hW, hW):                                                 # side rails
        _qp(surf, P, [(bb, ly, z1), (bf, ly, z1), (bf, ly, railz), (bb, ly, railz)],
            body["side"] if ly > 0 else _shade(body["side"], 0.8))
    _qp(surf, P, [(bb, -hW, z1), (bb, hW, z1), (bb, hW, railz), (bb, -hW, railz)],
        body["dark"])                                                    # tailgate
    _lp(surf, P, (bb, hW + 0.2, railz), (bf, hW + 0.2, railz), _shade(body["top"], 1.1), 1)
    # cab glass: near side + windshield
    ny = hW + 0.2
    _qp(surf, P, [(cb + 2, chW + 0.2, z1 + 2), (cf - 3, chW + 0.2, z1 + 2),
                  (cf - 3, chW + 0.2, cz1 - 2), (cb + 2, chW + 0.2, cz1 - 2)], glass)
    _lp(surf, P, (cb + 2, chW + 0.3, cz1 - 2), (cf - 3, chW + 0.3, cz1 - 2), glass_hi, 1)
    _qp(surf, P, [(cf, -chW, z1 + 2), (cf, chW, z1 + 2),
                  (cf, chW, cz1 - 2), (cf, -chW, cz1 - 2)], glass)
    # door seam + trim on the cab near side
    _lp(surf, P, (cb + 3 * s, ny, z0 + 1), (cb + 3 * s, ny, z1), _shade(cab["dark"], 0.8), 1)
    _lp(surf, P, (cb + 1, ny, z0 + 4 * s), (hL - 3, ny, z0 + 4 * s), _shade(body["side"], 1.3), 1)
    # nose: bumper, grille, lamps
    _qp(surf, P, [(hL, -hW, z0), (hL, hW, z0), (hL, hW, z0 + 4 * s), (hL, -hW, z0 + 4 * s)], chrome)
    for ey in (-7 * s, -2.5 * s, 2.5 * s, 7 * s):
        _lp(surf, P, (hL, ey, z0 + 5 * s), (hL, ey, z1 - 1 * s), _shade(body["dark"], 0.7), 1)
    for ey in (-hW * 0.6, hW * 0.6):
        hp = P(hL, ey, z1 - 2 * s)
        pygame.draw.circle(surf, (230, 224, 188), (int(hp[0]), int(hp[1])), max(2, int(2.4 * s)))
        tp = P(-hL, ey, railz - 2 * s)
        pygame.draw.circle(surf, (178, 42, 38), (int(tp[0]), int(tp[1])), max(2, int(2 * s)))
    _round_wheel(surf, P, wbx, hW, r)
    _round_wheel(surf, P, -wbx, hW, r)


def _draw_waterfall_solid(surf, cam, deco):
    """A sheet of water cascading down the cave cliff into the river -- the
    visible mouth of the artery (NARRATIVE 1b). Drawn each frame through the
    camera (a real falling sheet, depth-sorted against the wall), with streaks
    scrolling DOWN and foam churning where it strikes the water. `ang` (radians)
    yaws the sheet so it can hang on any wall; default faces +y (south)."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    ang = float(deco.kwargs.get("ang", 0.0))
    ca, sn = math.cos(ang), math.sin(ang)
    H = 46 * s
    halfw = 9 * s
    t = deco.t

    def P(across, z):                       # across the sheet width, height z
        return cam.project(wx + across * ca, wy + across * sn, z)
    # the wet dark rock the sheet sheets over
    pygame.draw.polygon(surf, (22, 28, 32),
                        [P(-halfw, 0), P(halfw, 0), P(halfw, H), P(-halfw, H)])
    # falling streaks: dashed vertical runs that scroll downward over time
    cols = [(120, 168, 184), (92, 140, 158), (150, 196, 208)]
    n = 6
    for i in range(n):
        across = -halfw + (i + 0.5) * (2 * halfw / n)
        col = cols[i % 3]
        off = (t * 42 * s + i * 7) % (8 * s + 0.01)
        z = H - off
        while z > 0:
            pygame.draw.line(surf, col, P(across, z),
                             P(across, max(0, z - 4 * s)), 1)
            z -= 8 * s
    pygame.draw.line(surf, (188, 216, 226), P(-halfw, H), P(halfw, H), 2)  # crest
    # foam pool + spray where it strikes the river
    fb = cam.project(wx, wy, 0)
    fw = max(3, int(halfw * cam.scale * 1.25))
    fh = max(2, int(halfw * 0.5 * cam.ground_squash() * cam.scale))
    foam = pygame.Surface((fw * 2 + 4, fh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(foam, (150, 188, 200, 150), (2, 2, fw * 2, fh * 2))
    pygame.draw.ellipse(foam, (210, 230, 236, 180),
                        (fw - fw // 2 + 2, fh - fh // 2 + 2, fw, fh))
    surf.blit(foam, (int(fb[0]) - fw - 2, int(fb[1]) - fh - 2))
    for i in range(5):
        fa = t * 3.0 + i * 1.3
        p = P(math.cos(fa) * halfw * 0.7, abs(math.sin(fa)) * 4 * s)
        pygame.draw.circle(surf, (205, 226, 234), (int(p[0]), int(p[1])), 1)


def _draw_doorframe_solid(surf, cam, deco):
    """THE THRESHOLD (NARRATIVE 1b): a plain, blank, unmarked frame -- 'about the
    size of a car stood on its nose' -- standing DEAD STRAIGHT on the impossible
    apron. 'Too slight to hold itself upright, yet it stands.' It is ONLY a
    frame: nothing fills the opening, you see the cave straight through it (walk
    through and you stand in the same room; that walk-through is the seal). Two
    slight jambs + a lintel, pale bone-stone, unnaturally precise against the
    leaning cave around it -- geometry serving the door."""
    wx, wy = deco.x, deco.y
    s = (getattr(deco, "scale", 1.0) or 1.0)
    Wf, Hf, t, Df = 30 * s, 54 * s, 5 * s, 6 * s
    half = Wf / 2
    pal = {"top": (158, 156, 164), "side": (110, 108, 116), "dark": (74, 72, 80)}
    # cold ground-contact shadow so it seats on the apron
    bx, by = cam.project(wx, wy, 0)
    shw = max(4, int(half * cam.scale * 1.1))
    shh = max(2, int(Df * cam.ground_squash() * cam.scale))
    shsurf = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(shsurf, (0, 0, 0, 90), (2, 2, shw * 2, shh * 2))
    surf.blit(shsurf, (bx - shw - 2, by - shh - 2))
    # jambs + lintel as slight upright boxes, dead straight (no lean). The
    # opening is left EMPTY -- whatever the camera already drew behind it (the
    # cave, the far wall) shows through.
    _vbox(surf, cam, wx - half + t / 2, wy, t, Df, 0, Hf, pal)
    _vbox(surf, cam, wx + half - t / 2, wy, t, Df, 0, Hf, pal)
    _vbox(surf, cam, wx, wy, Wf, Df, Hf - t, Hf, pal)
    # a thin pale rule down each inner edge -- precise, machined
    for ex in (-half + t, half - t):
        a = cam.project(wx + ex, wy, t)
        b = cam.project(wx + ex, wy, Hf - t)
        pygame.draw.line(surf, pal["top"], a, b, 1)


SOLID_PROPS = {
    "doorframe":     _draw_doorframe_solid,
    "waterfall":     _draw_waterfall_solid,
    "well":          _draw_well_solid,
    "pillar":        _draw_pillar_solid,
    "cistern_basin": _draw_cistern_basin_solid,
    "grain_heap":    _draw_grain_heap_solid,
    "player_car":    _draw_car_solid,
    "pickup_truck":  _draw_pickup_truck_solid,
    "stalagmite":    _draw_stalagmite_solid,
}


# -- Standees: stand authored 2D elevation art UP on the floor -------------
# Props whose `_draw_<kind>` art in entities/decoration.py is a side-on
# ELEVATION (a thing seen standing, base at the anchor) -- trees, effigies,
# signs, a cauldron on its frame. Under tilt these used to blit FLAT at the
# projected point, reading as a top-down sticker lying in a tilted world. We
# now render that same authored art onto a card cropped to its silhouette and
# stand it up GROUNDED, depth-sorted + occluding alongside the walls (the same
# language as the object-map tree standees). The flat pitch-0 view still draws
# the 2D sprite via Scene.draw, so it stays byte-identical. `hanging_figure`
# hangs instead: its card is hung from a mount height so the body dangles.
_STANDEE_HANG = frozenset(("hanging_figure",))
_STANDEE_GROUND = frozenset((
    "creepy_tree", "corn_doll", "corn_altar", "cauldron",
    "wheelbarrow", "pedestal", "steeple", "town_sign", "flagpole",
    "tall_grass", "grass_tuft", "doll",
))
_STANDEE_KINDS = _STANDEE_GROUND | _STANDEE_HANG
_STANDEE_HANG_MOUNT = 34          # world height the hanging card is hung from
_STANDEE_CARD_CACHE = {}          # (kind, seed, scale) -> cropped card | False


def _standee_card(deco):
    """The decoration's own 2D elevation art rendered to a card cropped to its
    silhouette, cached per (kind, seed, scale). Animation is frozen at t=0 (a
    standee is a static occluder, like the cached tree cards). Returns the card
    Surface, or None if the art is empty / missing."""
    s = round(getattr(deco, "scale", 1.0) or 1.0, 2)
    key = (deco.kind, deco.seed, s)
    card = _STANDEE_CARD_CACHE.get(key)
    if card is None:
        fn = getattr(deco, f"_draw_{deco.kind}", None)
        if fn is None:
            _STANDEE_CARD_CACHE[key] = False
            return None
        C = 128
        big = pygame.Surface((C, C), pygame.SRCALPHA)
        t0 = deco.t
        deco.t = 0.0
        try:
            fn(big, C // 2, C // 2)
        except Exception:
            _STANDEE_CARD_CACHE[key] = False
            return None
        finally:
            deco.t = t0
        rect = big.get_bounding_rect()
        if not rect.width or not rect.height:
            _STANDEE_CARD_CACHE[key] = False
            return None
        card = big.subsurface(rect).copy()
        if s != 1.0:
            card = pygame.transform.smoothscale(
                card, (max(1, int(card.get_width() * s)),
                       max(1, int(card.get_height() * s))))
        _STANDEE_CARD_CACHE[key] = card
    return card or None


def draw_standee(surf, cam, deco):
    """Stand the decoration's elevation card up on the floor (or hang it).
    Returns True if it was a standee kind (and drawn)."""
    card = _standee_card(deco)
    if card is None:
        return False
    if deco.kind in _STANDEE_HANG:
        sw = card.get_width()
        tx, ty = cam.project(deco.x, deco.y, _STANDEE_HANG_MOUNT)
        surf.blit(card, (int(tx - sw / 2), int(ty)))
    else:
        draw_billboard(surf, cam, deco.x, deco.y, card, h_anchor=1.0)
    return True


def is_solid_prop(kind):
    """A decoration that, under tilt, draws as world-oriented geometry (a
    body-of-revolution solid OR a grounded standee) instead of a flat top-down
    sticker. Both route through draw_prop_solid + the unified depth pass."""
    return kind in SOLID_PROPS or kind in _STANDEE_KINDS


def draw_prop_solid(surf, cam, deco):
    """Draw one decoration as a volumetric body-of-revolution prop or a grounded
    standee. Returns True if it was a known solid/standee (and drawn), False
    otherwise so the caller can fall back."""
    fn = SOLID_PROPS.get(deco.kind)
    if fn is not None:
        fn(surf, cam, deco)
        return True
    if deco.kind in _STANDEE_KINDS:
        return draw_standee(surf, cam, deco)
    return False
