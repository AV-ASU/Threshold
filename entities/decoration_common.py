"""Shared helpers, palettes and gating sets for the Decoration draw
mixins. Split out of decoration.py (2026-07) so the themed deco_*
siblings can share the lighting/compass helpers without importing the
Decoration class (which would be circular)."""
import time
import math
import random
import pygame
from constants import (
    SCREEN_W, SCREEN_H,
    C_BLACK, C_GOLD, C_RED,
)

# Compass-octant lookup. Index = 0..7 starting from EAST and walking
# clockwise (E, SE, S, SW, W, NW, N, NE). Each entry is a unit-circle
# offset; multiplied by per-axis travel inside _compass_offset.
_COMPASS_UNIT = (
    ( 1.0,  0.0),   # 0 E
    ( 0.7,  0.7),   # 1 SE
    ( 0.0,  1.0),   # 2 S
    (-0.7,  0.7),   # 3 SW
    (-1.0,  0.0),   # 4 W
    (-0.7, -0.7),   # 5 NW
    ( 0.0, -1.0),   # 6 N
    ( 0.7, -0.7),   # 7 NE
)


def _compass_offset(dx, dy, travel_x, travel_y):
    """Bucket a (dx, dy) world-vector into one of 8 compass directions
    (E, SE, S, SW, W, NW, N, NE) and return an integer (ox, oy) pixel
    offset capped to (travel_x, travel_y). Used by watching_eye and
    watching_wound to snap their tracking to discrete states instead
    of smooth analog drift -- the discrete shift is what the player's
    peripheral vision catches.

    `dx` is east-positive; `dy` is south-positive (screen coords).
    Player directly on top of the prop returns (0, 0). atan2 gives an
    angle in [-pi, pi]; we add pi/8 and divide by pi/4 so the
    quantisation lines up centred on each octant rather than on the
    octant boundary."""
    if abs(dx) < 1.0 and abs(dy) < 1.0:
        return (0, 0)
    ang = math.atan2(dy, dx)            # -pi..pi, 0=E, +pi/2=S
    # Shift so EAST sits at the centre of bucket 0, then floor.
    bucket = int(math.floor((ang + math.pi / 8) / (math.pi / 4))) % 8
    ux, uy = _COMPASS_UNIT[bucket]
    return (int(round(ux * travel_x)), int(round(uy * travel_y)))


# ---- Darkwood lighting helpers (mirror of scenes.base; kept local so
# entities/ doesn't import scenes/) ----
_DECO_SHADOW_CACHE = {}


def _ground_shadow(surf, cx, cy, rw, rh, alpha=80):
    key = (rw, rh, alpha)
    s = _DECO_SHADOW_CACHE.get(key)
    if s is None:
        s = pygame.Surface((rw * 2, rh * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, rw * 2, rh * 2))
        _DECO_SHADOW_CACHE[key] = s
    surf.blit(s, (int(cx - rw), int(cy - rh)))


_DECO_POOL_CACHE = {}


def _light_pool(surf, cx, cy, radius, color=(255, 170, 70), peak=70):
    key = (radius, color, peak)
    s = _DECO_POOL_CACHE.get(key)
    if s is None:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        steps = 10
        for k in range(steps, 0, -1):
            r = max(1, int(radius * k / steps))
            a = int(peak * (1 - k / steps) ** 1.4) + 4
            pygame.draw.circle(s, (color[0], color[1], color[2], a),
                               (radius, radius), r)
        _DECO_POOL_CACHE[key] = s
    surf.blit(s, (int(cx - radius), int(cy - radius)))


_GROUNDED_DECOS = frozenset((
    "well", "creepy_tree", "pickup_truck", "player_car",
    "rust_sedan", "rust_wagon", "rust_coupe", "rust_van",
    "burn_barrel", "news_rack",
    "gas_pump", "payphone", "pedestal", "pillar", "wheelbarrow",
    "headstone", "brazier", "town_sign", "flagpole", "bush",
    "corn_doll", "corn_altar", "stalk_marker", "standing_stone",
))

# Kinds that must NOT use the generic upscale path (they draw absolute
# light pools, track the player, animate ambiently, or are already large
# -- upscaling via a local canvas would misplace or clip them). The rug
# sizes itself via w/h kwargs instead, so it opts out too.
_NO_SCALE_DECOS = frozenset((
    "candle", "lantern", "brazier", "wall_torch", "swallow_hole",
    "smoke", "mist", "mote", "wisp",
    "flock", "leaves", "well", "steeple", "pickup_truck", "player_car",
    "rust_sedan", "rust_wagon", "rust_coupe", "rust_van",
    "burn_barrel", "news_rack",
    "watching_eye", "watching_wound", "passing_silhouette",
    "gas_pump", "payphone", "terminal", "computer", "mirror", "rug",
    "creepy_tree", "crow", "flock", "town_sign", "flagpole",
))


