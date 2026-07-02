"""Volumetric furniture for the oblique camera (CAMERA.md Tier-3 props).

Upright props become real BOXES projected through the camera, so they have
depth, rotate with the scene, and occlude correctly -- instead of the flat
"standee" sprite that never turns. Ground props (rugs, stains, blood) stay flat
decals; only the curated free-standing furniture in FURNITURE gets a volume.

Each spec is (footprint w, depth d, height h) in world units -- a wall rises 26,
a tile is 32 -- plus a palette {top, side, dark} (top is lit, the near face is
darkest) and an optional detail hook that paints recognisable features on the
near face (shelf lines, a mattress, a firebox glow). Tilt-only: the flat
top-down game never calls this, so it stays byte-identical.
"""
import pygame

# -- palettes ---------------------------------------------------------------
_WOOD_MID = {"top": (122, 88, 54), "side": (96, 67, 41), "dark": (70, 48, 30)}
_WOOD_DK = {"top": (94, 65, 41), "side": (72, 49, 31), "dark": (52, 35, 22)}
_STONE = {"top": (122, 120, 126), "side": (96, 94, 100), "dark": (70, 68, 74)}
_IRON = {"top": (86, 86, 94), "side": (64, 64, 72), "dark": (44, 44, 52)}
_CLOTH = {"top": (152, 62, 60), "side": (120, 47, 46), "dark": (90, 34, 34)}
_BONE = {"top": (196, 190, 170), "side": (150, 144, 126), "dark": (104, 99, 86)}


def _lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _shade(c, f):
    return (max(0, min(255, int(c[0] * f))),
            max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))))


def _hline(surf, fbl, fbr, tbl, tbr, f, col, w=1):
    """Draw a line across the near face at height fraction f (0 bottom..1 top)."""
    pygame.draw.line(surf, col, _lerp(fbl, tbl, f), _lerp(fbr, tbr, f), w)


# -- per-kind near-face detail ----------------------------------------------
def _d_shelves(surf, pal, c):
    for f in (0.18, 0.44, 0.70):
        _hline(surf, *c, f, _shade(pal["dark"], 0.6), 2)


def _d_mattress(surf, pal, c):
    # a paler blanket band near the top + a pillow block at one end
    _hline(surf, *c, 0.62, (176, 92, 88), 3)
    px = _lerp(c[0], c[1], 0.18)               # near-left toward near-right
    py = _lerp(_lerp(c[0], c[2], 0.55), _lerp(c[1], c[3], 0.55), 0.18)
    pygame.draw.circle(surf, (208, 198, 188), (int(py[0]), int(py[1])), 4)


def _d_firebox(surf, pal, c):
    # a dark mouth low-centre with an ember glow
    m = _lerp(_lerp(c[0], c[1], 0.5), _lerp(c[2], c[3], 0.5), 0.0)
    bx = int(_lerp(c[0], c[1], 0.5)[0]); by = int(_lerp(c[0], c[1], 0.5)[1])
    pygame.draw.ellipse(surf, (24, 18, 18), (bx - 6, by - 12, 12, 11))
    pygame.draw.ellipse(surf, (188, 96, 38), (bx - 4, by - 9, 8, 7))
    pygame.draw.ellipse(surf, (236, 168, 70), (bx - 2, by - 7, 4, 4))


def _d_door_seam(surf, pal, c):
    _hline(surf, c[0], c[0], c[2], c[2], 1.0, pal["dark"], 1)  # noop guard
    mid_b = _lerp(c[0], c[1], 0.5); mid_t = _lerp(c[2], c[3], 0.5)
    pygame.draw.line(surf, _shade(pal["dark"], 0.7), mid_b, mid_t, 1)
    for fx in (0.5,):
        h1 = _lerp(_lerp(c[0], c[1], fx - 0.06), _lerp(c[2], c[3], fx - 0.06), 1)
    # two small handles either side of the seam
    for off in (-0.07, 0.07):
        h = _lerp(_lerp(c[0], c[1], 0.5 + off), _lerp(c[2], c[3], 0.5 + off), 0.5)
        pygame.draw.circle(surf, (210, 190, 120), (int(h[0]), int(h[1])), 2)


def _d_logs(surf, pal, c):
    for f in (0.3, 0.6):
        p = _lerp(_lerp(c[0], c[1], f), _lerp(c[2], c[3], f), 0.4)
        pygame.draw.circle(surf, _shade(pal["top"], 1.15), (int(p[0]), int(p[1])), 3)
        pygame.draw.circle(surf, pal["dark"], (int(p[0]), int(p[1])), 3, 1)


def _d_cot_pallet(surf, pal, c):
    # a thin pale pallet band high on the near face + a folded blanket lump
    _hline(surf, *c, 0.72, (150, 142, 128), 3)
    p = _lerp(_lerp(c[0], c[1], 0.22), _lerp(c[2], c[3], 0.22), 0.5)
    pygame.draw.circle(surf, (96, 88, 78), (int(p[0]), int(p[1])), 3)


def _d_bones(surf, pal, c):
    # stacked pale rows with knobbly ends -- shelved bones
    for f in (0.22, 0.5, 0.78):
        _hline(surf, *c, f, _shade(pal["dark"], 0.7), 2)
        for fx in (0.28, 0.72):
            p = _lerp(_lerp(c[0], c[1], fx), _lerp(c[2], c[3], fx), f)
            pygame.draw.circle(surf, _shade(pal["top"], 1.05),
                               (int(p[0]), int(p[1])), 2)


def _d_pew_back(surf, pal, c):
    # a single rail across the top -- a bench back
    _hline(surf, *c, 0.86, _shade(pal["top"], 1.1), 2)


def _d_screen(surf, pal, c):
    # a dark glass screen set high on the near face, with a sick green CRT glow
    def fp(fx, fy):
        return _lerp(_lerp(c[0], c[1], fx), _lerp(c[2], c[3], fx), fy)
    pts = [fp(0.20, 0.40), fp(0.80, 0.40), fp(0.80, 0.84), fp(0.20, 0.84)]
    pts = [(int(x), int(y)) for x, y in pts]
    pygame.draw.polygon(surf, (16, 26, 24), pts)
    pygame.draw.polygon(surf, (62, 120, 94), pts, 1)
    g = fp(0.5, 0.62)
    pygame.draw.circle(surf, (70, 150, 112), (int(g[0]), int(g[1])), 2)


def _d_chest_lid(surf, pal, c):
    # a lid seam across the upper third + a small latch
    _hline(surf, *c, 0.62, _shade(pal["dark"], 0.7), 2)
    p = _lerp(_lerp(c[0], c[1], 0.5), _lerp(c[2], c[3], 0.5), 0.55)
    pygame.draw.circle(surf, (200, 178, 110), (int(p[0]), int(p[1])), 2)


def _fp(c, fx, fy):
    """A point on the near face at width-fraction fx, up-fraction fy."""
    return _lerp(_lerp(c[0], c[1], fx), _lerp(c[2], c[3], fx), fy)


def _d_gaspump(surf, pal, c):
    # a pale price display set high, a thin dark hose down one side
    p = [_fp(c, 0.24, 0.60), _fp(c, 0.76, 0.60), _fp(c, 0.76, 0.84), _fp(c, 0.24, 0.84)]
    pts = [(int(x), int(y)) for x, y in p]
    pygame.draw.polygon(surf, (148, 150, 120), pts)
    pygame.draw.polygon(surf, (54, 56, 44), pts, 1)
    a, b = _fp(c, 0.84, 0.52), _fp(c, 0.94, 0.18)
    pygame.draw.line(surf, (20, 20, 20), (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 2)


def _d_payphone(surf, pal, c):
    # a dark phone box face with a pale handset
    p = [_fp(c, 0.26, 0.48), _fp(c, 0.74, 0.48), _fp(c, 0.74, 0.88), _fp(c, 0.26, 0.88)]
    pts = [(int(x), int(y)) for x, y in p]
    pygame.draw.polygon(surf, (28, 32, 38), pts)
    pygame.draw.polygon(surf, (88, 94, 102), pts, 1)
    h = _fp(c, 0.42, 0.7)
    pygame.draw.circle(surf, (150, 156, 162), (int(h[0]), int(h[1])), 2)


def _d_headstone(surf, pal, c):
    # an incised cross
    col = _shade(pal["dark"], 0.7)
    t, b = _fp(c, 0.5, 0.82), _fp(c, 0.5, 0.42)
    l, r = _fp(c, 0.36, 0.66), _fp(c, 0.64, 0.66)
    pygame.draw.line(surf, col, (int(t[0]), int(t[1])), (int(b[0]), int(b[1])), 2)
    pygame.draw.line(surf, col, (int(l[0]), int(l[1])), (int(r[0]), int(r[1])), 2)


def _d_counter(surf, pal, c):
    # butcher-block front: plank seams, a worn pale lip along the top edge,
    # knife scores, and one old dark stain bleeding down from the lip
    seam = _shade(pal["dark"], 0.7)
    for fx in (0.34, 0.67):
        a, b = _fp(c, fx, 0.0), _fp(c, fx, 0.96)
        pygame.draw.line(surf, seam, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1)
    _hline(surf, *c, 0.88, _shade(pal["top"], 1.14), 2)     # the handled lip
    score = _shade(pal["dark"], 0.55)
    for fx, fy, ln in ((0.14, 0.64, 0.11), (0.48, 0.52, 0.09), (0.76, 0.68, 0.08)):
        a, b = _fp(c, fx, fy), _fp(c, fx + ln, fy - 0.09)
        pygame.draw.line(surf, score, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1)
    stain = (58, 34, 28)                                    # dried dark-red soak
    p = _fp(c, 0.55, 0.80)
    pygame.draw.ellipse(surf, stain, (int(p[0]) - 4, int(p[1]) - 2, 9, 5))
    d0, d1 = _fp(c, 0.57, 0.78), _fp(c, 0.57, 0.44)
    pygame.draw.line(surf, stain, (int(d0[0]), int(d0[1])), (int(d1[0]), int(d1[1])), 1)


# -- spec: kind -> (w, d, h, palette, detail) -------------------------------
FURNITURE = {
    "table":     (26, 20, 11, _WOOD_MID, None),
    "chair":     (13, 13, 16, _WOOD_DK, None),
    "bed":       (30, 46, 9,  _CLOTH,   _d_mattress),
    "bookshelf": (28, 13, 23, _WOOD_DK, _d_shelves),
    "shelf":     (26, 10, 22, _WOOD_DK, _d_shelves),
    "wardrobe":  (24, 15, 26, _WOOD_DK, _d_door_seam),
    "stove":     (22, 20, 18, _IRON,    _d_firebox),
    "fireplace": (30, 14, 24, _STONE,   _d_firebox),
    "counter":   (34, 14, 14, _WOOD_MID, _d_counter),
    "firewood":  (20, 16, 9,  _WOOD_DK, _d_logs),
    "crate":     (18, 18, 16, _WOOD_MID, None),
    "barrel":    (16, 16, 18, _WOOD_MID, None),
    "cot":       (28, 13, 8,  _WOOD_DK, _d_cot_pallet),
    "bone_rack": (26, 12, 24, _BONE,    _d_bones),
    "pew":       (40, 11, 11, _WOOD_DK, _d_pew_back),
    # Free-standing Tier-1 decorations promoted to real box volumes (they used
    # to float as flat top-down sprites under tilt).
    "chest":            (24, 18, 13, _WOOD_MID, _d_chest_lid),
    "small_chair":      (11, 11, 13, _WOOD_DK,  None),
    "overturned_chair": (16, 13, 8,  _WOOD_DK,  None),   # low box -> toppled
    "terminal":         (16, 15, 22, _IRON,     _d_screen),
    "computer":         (20, 17, 16, _IRON,     _d_screen),
    # Tier-2 roadside + graveyard uprights.
    "gas_pump":         (14, 12, 30, _IRON,     _d_gaspump),
    "payphone":         (11, 9,  24, _IRON,     _d_payphone),
    "headstone":        (16, 7,  19, _STONE,    _d_headstone),
}


def is_solid_furniture(kind):
    return kind in FURNITURE


# Furniture shorter than eye level can be seen (and shot/seen) over: it stays
# solid for collision but does not block line of sight. (A wall rises 26.)
SEE_OVER_MAX_H = 20


def is_see_over_furniture(kind):
    """True if this furniture is low enough to see over (a chair, table, bed,
    counter, crate...) vs a tall piece that blocks the view (bookshelf,
    wardrobe, fireplace)."""
    spec = FURNITURE.get(kind)
    return bool(spec and spec[2] < SEE_OVER_MAX_H)


def draw_furniture_solid(surf, cam, deco):
    """Draw one decoration as a projected box volume. Returns True if it was a
    furniture kind (and drawn), False if the caller should fall back to flat."""
    spec = FURNITURE.get(deco.kind)
    if spec is None:
        return False
    w, d, h, pal, detail = spec
    s = getattr(deco, "scale", 1.0) or 1.0
    w *= s; d *= s; h *= s
    wx, wy = deco.x, deco.y
    hw, hd = w / 2.0, d / 2.0

    def P(sx, sy, sz):
        return cam.project(wx + sx, wy + sy, sz)

    # soft contact shadow so the box seats on the floor instead of floating
    bx, by = cam.project(wx, wy, 0)
    shw = max(3, int(hw * cam.scale * 1.15))
    shh = max(2, int(hd * cam.scale * cam.ground_squash() * 1.15))
    sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 95), (2, 2, shw * 2, shh * 2))
    surf.blit(sh, (bx - shw - 2, by - shh - 2))

    # eight corners
    fbl, fbr = P(-hw, hd, 0), P(hw, hd, 0)      # near (bottom)
    tbl, tbr = P(-hw, hd, h), P(hw, hd, h)      # near (top)
    bbl, bbr = P(-hw, -hd, 0), P(hw, -hd, 0)    # far (bottom)
    ttl, ttr = P(-hw, -hd, h), P(hw, -hd, h)    # far (top)
    # faces: far-up sides first, near face, then top (painter order within box)
    pygame.draw.polygon(surf, pal["side"], [bbl, fbl, tbl, ttl])   # left
    pygame.draw.polygon(surf, pal["side"], [bbr, fbr, tbr, ttr])   # right
    pygame.draw.polygon(surf, pal["dark"], [fbl, fbr, tbr, tbl])   # near
    pygame.draw.polygon(surf, pal["top"], [ttl, ttr, tbr, tbl])    # top
    pygame.draw.polygon(surf, _shade(pal["top"], 0.55),
                        [ttl, ttr, tbr, tbl], 1)
    if detail:
        detail(surf, pal, (fbl, fbr, tbl, tbr))
    return True
