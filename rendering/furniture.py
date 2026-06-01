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
    "counter":   (34, 14, 14, _WOOD_MID, None),
    "firewood":  (20, 16, 9,  _WOOD_DK, _d_logs),
    "crate":     (18, 18, 16, _WOOD_MID, None),
    "barrel":    (16, 16, 18, _WOOD_MID, None),
}


def is_solid_furniture(kind):
    return kind in FURNITURE


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
