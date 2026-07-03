"""The Moth -- the King's herald, the first flying entity (2026-07).

A dead thing drifting the wrong way up: a knot of too many jointed limbs
folded like a drowned spider, a gold gleam caged in its ribs. Near the
player it KINDLES (limbs easing open, the cage brightening: the
counterplay window), then FLARES: the limbs snap out wrong-jointed and
the cage burns while the ribs stay black against the light. Procedural,
drawn for the 3D tilt world (the caller projects and hovers it; this
draws a billboard at the given screen point).

`spread` 0..1 folds/opens the limbs; `glow` 0..1 drives the caged light
(idle ember ~0.12, kindle ramps, flare 1.0).
"""
import math
import pygame

_TAR = (20, 18, 24)
_TAR_HI = (46, 42, 54)
_DK = (30, 27, 34)
_VOID = (14, 13, 17)
_GOLD = (230, 186, 48)
_GOLD_HI = (255, 218, 96)

# eight limbs: unit directions around the knot (matched to the approved
# concept sheet), deliberately uneven
_LIMBS = ((-1.0, 0.5), (-0.6, 1.0), (-0.2, 0.7), (0.3, 1.0),
          (0.8, 0.6), (1.0, 0.2), (0.6, -0.4), (-0.8, -0.2))


def _soft_glow(surf, x, y, r, peak, col=_GOLD):
    """Layered falloff bloom (never a flat gold coin)."""
    if r < 2 or peak <= 0:
        return
    x, y, r = int(x), int(y), int(r)
    g = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    for i in range(r, 0, -2):
        a = int(peak * (1 - i / r) ** 1.7)
        if a > 0:
            pygame.draw.circle(g, (col[0], col[1], col[2], a),
                               (r + 1, r + 1), i)
    surf.blit(g, (x - r - 1, y - r - 1),
              special_flags=pygame.BLEND_RGBA_ADD)


def draw_moth(surf, x, y, t, spread=0.0, glow=0.12, seed=0):
    x, y = int(x), int(y)
    spread = max(0.0, min(1.0, spread))
    glow = max(0.0, min(1.0, glow))
    # the halo first, so the body silhouettes against its own light
    if glow > 0.2:
        _soft_glow(surf, x, y, int(8 + 22 * glow), int(40 + 130 * glow))
    # thorax knot, ribbed
    body = pygame.Rect(x - 8, y - 7, 17, 15)
    pygame.draw.ellipse(surf, _TAR, body)
    pygame.draw.ellipse(surf, _VOID, body, 1)
    for i in range(3):
        pygame.draw.arc(surf, _DK, (x - 7 + i, y - 6, 14 - 2 * i, 12),
                        math.radians(235), math.radians(305), 1)
    # the limbs: folded knuckles-up at rest, snapping out with spread
    for li, (ax, ay) in enumerate(_LIMBS):
        wig = math.sin(t * 2.1 + li * 1.7 + seed) * (1.5 - spread)
        # joint eases outward and DOWNWRONG as it opens
        jx = x + ax * (10 + 8 * spread) + wig
        jy = y + ay * (9 + 7 * spread) - 3 * (1 - spread)
        # tip: folded back in at rest; flung wrong-jointed when open
        ex = x + ax * (4 + 16 * spread) - ay * 4 * spread + wig
        ey = y + ay * (3 + 15 * spread) + ax * 4 * spread + 7 * (1 - spread)
        pygame.draw.line(surf, _DK, (x, y), (int(jx), int(jy)),
                         3 if spread > 0.5 else 2)
        pygame.draw.line(surf, _TAR_HI if spread < 0.5 else _DK,
                         (int(jx), int(jy)), (int(ex), int(ey)),
                         2 if spread > 0.5 else 1)
    # the caged gleam; the ribs stay black over the burn
    if glow > 0.55:
        pygame.draw.circle(surf, _GOLD_HI, (x, y), 2)
        for i in range(3):
            pygame.draw.arc(surf, _VOID, (x - 7 + i, y - 6, 14 - 2 * i, 12),
                            math.radians(225), math.radians(315), 1)
    else:
        _soft_glow(surf, x, y, 4, int(60 + 60 * glow))
        pygame.draw.circle(surf, _GOLD, (x, y), 1)
