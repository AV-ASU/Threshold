"""Procedural skybox / distant backdrop — fills the void around a tilted scene.

Once the camera pitches to an oblique angle, the area beyond the playfield is
empty black. This fills it with a far backdrop that sits BEHIND the scene and
parallaxes as the camera yaws, giving the world depth without a real ceiling.
It is NOT drawn over the UI -- the game blits the scene + HUD on top.

Scene-type aware (the horror leans on darkness, so we don't flood interiors
with sky):
  * "overcast"  -- Brimley daytime: sallow overcast sky, a fogged horizon,
                   a near-black treeline/rooftop silhouette that wraps on yaw.
  * "void"      -- interiors / underground: near-black surround with a faint
                   cold gradient, so edges read as depth, not a hard cut.
All procedural, no assets.
"""
import math
import random
import pygame

_PALETTES = {
    "overcast": {
        "top": (30, 32, 38), "horizon": (78, 76, 64), "fog": (96, 94, 78),
        "sil": (10, 11, 13), "sign": (120, 104, 50),  # faint sallow band
    },
    "void": {
        "top": (6, 6, 9), "horizon": (16, 16, 22), "fog": (20, 20, 26),
        "sil": (4, 4, 6), "sign": (24, 22, 30),
    },
}

# cache the seeded silhouette profile so it doesn't boil frame to frame
_SIL_CACHE = {}


def _silhouette_profile(width, kind, seed=7):
    key = (width, kind, seed)
    if key in _SIL_CACHE:
        return _SIL_CACHE[key]
    rng = random.Random(seed)
    pts = []
    x = 0
    base = 0
    while x < width:
        # alternate broad treeline humps and the odd taller spike (a chimney,
        # a steeple, the works tower) so the wrap reads as a real far town.
        if rng.random() < 0.12:
            h = rng.randint(26, 46)
            w = rng.randint(3, 6)
        else:
            h = rng.randint(6, 18)
            w = rng.randint(6, 16)
        pts.append((x, -h))
        x += w
    _SIL_CACHE[key] = pts
    return pts


def draw_skybox(surf, rect, yaw=0.0, kind="overcast", horizon_frac=0.42):
    """Fill `rect` (x, y, w, h) with the backdrop, parallaxed by camera `yaw`.
    `horizon_frac` is where the horizon sits within the rect (fixed pitch ->
    fixed horizon)."""
    x0, y0, w, h = rect
    pal = _PALETTES.get(kind, _PALETTES["overcast"])
    horizon_y = y0 + int(h * horizon_frac)

    # Vertical gradient sky, top -> horizon.
    top, hor = pal["top"], pal["horizon"]
    band = max(1, horizon_y - y0)
    for i in range(band):
        f = i / band
        col = (int(top[0] + (hor[0] - top[0]) * f),
               int(top[1] + (hor[1] - top[1]) * f),
               int(top[2] + (hor[2] - top[2]) * f))
        pygame.draw.line(surf, col, (x0, y0 + i), (x0 + w, y0 + i))

    # A faint sallow Sign-band just above the horizon (the fold's pallor in
    # the sky) -- restrained, only on overcast.
    if kind == "overcast":
        sg = pal["sign"]
        for i in range(8):
            a = 30 - i * 3
            if a <= 0:
                break
            ln = pygame.Surface((w, 1), pygame.SRCALPHA)
            ln.fill((sg[0], sg[1], sg[2], a))
            surf.blit(ln, (x0, horizon_y - 10 + i))

    # Ground/fog below the horizon, fading down into where the scene sits.
    fog, fcol = pal["fog"], pal["horizon"]
    fband = max(1, (y0 + h) - horizon_y)
    for i in range(fband):
        f = i / fband
        col = (int(fog[0] + (0 - fog[0]) * f * 0.7),
               int(fog[1] + (0 - fog[1]) * f * 0.7),
               int(fog[2] + (0 - fog[2]) * f * 0.7))
        pygame.draw.line(surf, col, (x0, horizon_y + i), (x0 + w, horizon_y + i))

    # Wrapping distant silhouette, scrolled by yaw (parallax). Drawn twice so
    # it tiles seamlessly as the camera turns.
    prof_w = w * 2
    prof = _silhouette_profile(prof_w, kind)
    off = int((yaw / (2 * math.pi)) * prof_w) % prof_w
    sil = pal["sil"]
    for base in (-off, prof_w - off):
        poly = [(x0 + base + px, horizon_y + py) for (px, py) in prof]
        if not poly:
            continue
        poly = [(poly[0][0], horizon_y + 4)] + poly + [(poly[-1][0], horizon_y + 4)]
        pygame.draw.polygon(surf, sil, poly)
