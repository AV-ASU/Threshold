"""The Moth -- the King's herald, the first flying entity (2026-07).

A moth the size of a barn owl, wrong way up: two ragged membrane wing
pairs held TENTED over a knot of too many jointed limbs, a gold gleam
caged in its ribs. The wings are the read at rest; the limbs are the
horror when it opens. Near the player it KINDLES (wings rising, the
cage brightening: the counterplay window), then FLARES: wings and limbs
snap out wrong-jointed and the cage burns while the body stays black
against the light. It burns for a couple of seconds, then the husk
falls: crumpled wing scraps on a charred stain.

Procedural, drawn for the 3D tilt world (the caller projects and
hovers it; this draws a billboard at the given screen point).

`spread` 0..1 opens wings + limbs; `glow` 0..1 drives the caged light;
`flap` is the wingbeat energy (0.2 hover-fan, ~1.0 the King's fast
fliers); `husk=True` draws the fallen burn-out at the ground point.
"""
import math
import pygame

_TAR = (20, 18, 24)
_TAR_HI = (46, 42, 54)
_DK = (30, 27, 34)
_VOID = (14, 13, 17)
_WING = (38, 34, 46)
_WING_LO = (27, 24, 33)
_WING_EDGE = (64, 58, 74)
_VEIN = (56, 51, 64)
_CHAR = (24, 20, 18)
_GOLD = (230, 186, 48)
_GOLD_HI = (255, 218, 96)

# eight limbs: unit directions around the knot, deliberately uneven
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


def _wing(surf, x, y, side, spread, beat, glow, hind=False):
    """One ragged membrane wing. `side` is -1 (left) / +1 (right).
    At spread 0 it tents down over the back; at 1 it stands out level.
    `beat` is the live stroke offset (px, +down)."""
    ln = 15 if hind else 20                      # wing length
    # shoulder root, slightly behind the head
    rx = x + side * 2
    ry = y - (1 if hind else 3)
    # the tip swings from down-back (tented) to out-level (spread)
    tx = rx + side * (ln * (0.55 + 0.45 * spread))
    ty = ry + ln * (0.72 - 0.9 * spread) + beat
    # leading edge is taut; the trailing edge hangs and is RAGGED
    lead_mx = rx + side * (ln * 0.5 * (0.6 + 0.4 * spread))
    lead_my = ry + ln * (0.2 - 0.45 * spread) + beat * 0.6
    trail = []
    for i, f in enumerate((0.75, 0.5, 0.25)):
        jag = 2 if i % 2 == 0 else -1
        trail.append((rx + (tx - rx) * f + side * jag,
                      ry + (ty - ry) * f + 4 + jag + beat * 0.3 * f))
    pts = [(rx, ry), (lead_mx, lead_my), (tx, ty)] + trail
    pygame.draw.polygon(surf, _WING_LO if hind else _WING, pts)
    pygame.draw.polygon(surf, _VOID, pts, 1)
    # the taut leading edge catches what light there is -- the line
    # that makes the wing READ against a dark field
    pygame.draw.lines(surf, _WING_EDGE if not hind else _VEIN, False,
                      [(rx, ry), (int(lead_mx), int(lead_my)),
                       (int(tx), int(ty))], 1)
    if not hind:
        # two veins from the root toward the membrane
        for f in (0.55, 0.85):
            vx = rx + (tx - rx) * f
            vy = ry + (ty - ry) * f + 2
            pygame.draw.line(surf, _VEIN, (rx, ry),
                             (int(vx), int(vy)), 1)
        # at full burn the trailing edge kindles
        if glow > 0.7:
            for px_, py_ in trail:
                pygame.draw.line(surf, _GOLD, (int(px_), int(py_)),
                                 (int(px_) + side, int(py_) - 3), 1)


def draw_moth(surf, x, y, t, spread=0.0, glow=0.12, seed=0, flap=0.2,
              husk=False):
    x, y = int(x), int(y)
    spread = max(0.0, min(1.0, spread))
    glow = max(0.0, min(1.0, glow))
    if husk:
        # the burn-out on the ground: a charred stain, crumpled wing
        # scraps, the limb knot half-collapsed. No light left in it.
        pygame.draw.ellipse(surf, _CHAR, (x - 12, y - 4, 24, 9))
        pygame.draw.ellipse(surf, _VOID, (x - 12, y - 4, 24, 9), 1)
        for sx_, wpts in ((-1, ((-15, -2), (-7, -7), (-3, 0))),
                          (1, ((14, -3), (7, -8), (2, -1)))):
            pts = [(x + px_, y + py_) for px_, py_ in wpts]
            pygame.draw.polygon(surf, _WING_LO, pts)
            pygame.draw.polygon(surf, _VOID, pts, 1)
            pygame.draw.line(surf, _WING_EDGE, pts[0], pts[1], 1)
        pygame.draw.ellipse(surf, _TAR, (x - 5, y - 6, 11, 8))
        for ax, ay in _LIMBS[::3]:
            pygame.draw.line(surf, _DK, (x, y - 2),
                             (x + int(ax * 7), y + int(abs(ay) * 3)), 1)
        return
    # the halo first, so the body silhouettes against its own light
    if glow > 0.2:
        _soft_glow(surf, x, y, int(8 + 22 * glow), int(40 + 130 * glow))
    # live wingbeat: the stroke offset (px), faster + deeper with flap
    beat = math.sin(t * (5.0 + 13.0 * flap) + seed) * (1.5 + 5.0 * flap)
    # hind pair first (under), then the forewings
    for side in (-1, 1):
        _wing(surf, x, y, side, spread, beat * (0.7 if side < 0 else 1.0),
              glow, hind=True)
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
        jx = x + ax * (10 + 8 * spread) + wig
        jy = y + ay * (9 + 7 * spread) - 3 * (1 - spread)
        ex = x + ax * (4 + 16 * spread) - ay * 4 * spread + wig
        ey = y + ay * (3 + 15 * spread) + ax * 4 * spread + 7 * (1 - spread)
        pygame.draw.line(surf, _DK, (x, y), (int(jx), int(jy)),
                         3 if spread > 0.5 else 2)
        pygame.draw.line(surf, _TAR_HI if spread < 0.5 else _DK,
                         (int(jx), int(jy)), (int(ex), int(ey)),
                         2 if spread > 0.5 else 1)
    # forewings OVER the limbs: at rest they tent and hide most of the
    # knot (the moth read); open, they stand clear of the snap
    for side in (-1, 1):
        _wing(surf, x, y, side, spread, beat * (0.7 if side < 0 else 1.0),
              glow, hind=False)
    # the caged gleam; the ribs stay black over the burn
    if glow > 0.55:
        pygame.draw.circle(surf, _GOLD_HI, (x, y), 2)
        for i in range(3):
            pygame.draw.arc(surf, _VOID, (x - 7 + i, y - 6, 14 - 2 * i, 12),
                            math.radians(225), math.radians(315), 1)
    else:
        _soft_glow(surf, x, y, 4, int(60 + 60 * glow))
        pygame.draw.circle(surf, _GOLD, (x, y), 1)
