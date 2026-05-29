"""Body-horror transformation rendering.

The "vessel bloom": an ordinary human sprite tears open down the
sternum (ribcage bloom) into a Yellow-King vessel -- the torso splits
into two peeling rib-flaps, revealing a jaundiced vertical maw ringed
with teeth and packed with blinking eyes. Head and legs stay anchored
so the figure keeps a humanoid read the whole way: it is unmistakably a
*person* coming apart, not a sprite dissolving.

Driven by a single `morph` float in 0..1 so the entity layer only ramps
one value; all timing/easing/staging lives here.

  morph == 0          identical to draw_npc_sprite (no cost, no change).
  morph (0, ~0.2]     skin sickens (yellows), a dark sternum seam, a
                      tremble: the "something is wrong" tell.
  morph ~0.2..0.55    the seam tears, the two torso halves peel out,
                      the maw opens between them.
  morph ~0.55..1.0    the cavity deepens and fills with eyes + ichor,
                      the flaps splay like ribs, a sickly halo blooms.

All procedural primitives drawn onto a per-entity SRCALPHA cell, so the
whole figure trembles/peels as a unit without touching the hand-tuned
sprites in sprites.py.
"""
import math
import random
import pygame

from rendering.sprites import draw_npc_sprite

# --- Muddy, desaturated maw (matches the cult's body-horror register) ---
# His light is a faint seep, not a jaundiced lightbulb; gore is dark
# red-brown, not bright blood; bone/eyes stay muted.
_THROAT    = (20, 15, 12)       # deepest cavity
_FLESH     = (120, 98, 62)      # inner wall (muddy ochre flesh)
_FLESH_LO  = (74, 60, 40)       # wall shadow / outer rim
_TORN      = (96, 46, 38)       # torn-flesh edge (muddy, not bright)
_GORE      = (60, 30, 26)       # darker rip / drips
_TEETH     = (176, 168, 142)
_TEETH_LO  = (126, 120, 100)
_ICHOR     = (150, 128, 62)     # dim wet strands
_ICHOR_HI  = (190, 170, 96)
_EYE_WHITE = (182, 172, 132)
_EYE_PUPIL = (10, 7, 4)
_HALO      = (150, 128, 58)     # faint sick underglow
_SICK_TINT = (168, 148, 98)     # multiply target for sickening skin

# Local cell geometry. (lx, ly) is the local anchor that maps to the
# caller's (x, y), matching draw_npc_sprite's torso-ish origin.
_CW, _CH = 96, 116
_LX, _LY = 48, 64
# Torso band that peels (chest line .. hip line). Head sits above,
# legs below; only this band tears open.
_TOP = _LY - 8
_BOT = _LY + 15
_CCY = (_TOP + _BOT) // 2       # cavity centre


def _clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v


def _smooth(p):
    p = _clamp01(p)
    return p * p * (3.0 - 2.0 * p)


def _ease_out_back(p):
    """Overshoot ease -- the flaps fling open then settle (a lurch)."""
    p = _clamp01(p)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (p - 1.0) ** 3 + c1 * (p - 1.0) ** 2


def _lerp_col(a, b, t):
    t = _clamp01(t)
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _blit_hinged(dst, flap, hinge_local, anchor, deg, off):
    """Blit `flap` rotated `deg` (CCW) about its local `hinge_local`
    point, placing that hinge at world `anchor` + `off`. Used to swing
    the torso halves open about the sternum like cabinet doors."""
    rot = pygame.transform.rotate(flap, deg)
    w, h = flap.get_size()
    nw, nh = rot.get_size()
    relx = hinge_local[0] - w / 2.0
    rely = hinge_local[1] - h / 2.0
    th = math.radians(deg)
    # Screen space (y down): CCW rotation of the offset vector.
    rx = relx * math.cos(th) + rely * math.sin(th)
    ry = -relx * math.sin(th) + rely * math.cos(th)
    hx = nw / 2.0 + rx
    hy = nh / 2.0 + ry
    dst.blit(rot, (int(anchor[0] - hx + off[0]),
                   int(anchor[1] - hy + off[1])))


def draw_vessel_bloom(surf, x, y, base_kind, facing, morph, t=None, seed=0):
    """Render the human->vessel transformation at progress `morph`."""
    morph = _clamp01(morph)
    if morph <= 0.0:
        draw_npc_sprite(surf, x, y, base_kind, facing)
        return
    if t is None:
        t = pygame.time.get_ticks() / 1000.0

    sick    = _clamp01(morph / 0.30)
    open_p  = _clamp01((morph - 0.18) / 0.62)
    split   = _ease_out_back(open_p)
    eyemass = _smooth(_clamp01((morph - 0.42) / 0.58))

    cell = pygame.Surface((_CW, _CH), pygame.SRCALPHA)

    # A faint sick underglow behind the cavity (additive) -- a seep welling
    # from within, not a jaundiced lightbulb. Kept low and tight.
    if eyemass > 0.0:
        halo = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (_HALO[0], _HALO[1], _HALO[2],
                                   int(20 * eyemass)),
                            (_LX - 16, _CCY - 22, 32, 44))
        cell.blit(halo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # Base body, sickened.
    body = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
    draw_npc_sprite(body, _LX, _LY, base_kind, facing)
    if sick > 0.0:
        tint = pygame.Surface((_CW, _CH), pygame.SRCALPHA)
        tint.fill(_lerp_col((255, 255, 255), _SICK_TINT, sick) + (255,))
        body.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Cavity (behind the flaps so they reveal it as they peel).
    _draw_cavity(cell, _LX, _CCY, split, eyemass, facing, t, seed)

    # Head + upper body (above the torso band) -- anchored, drifts up
    # slightly as the vessel takes over.
    head = body.subsurface(pygame.Rect(0, 0, _CW, _TOP)).copy()
    cell.blit(head, (0, -int(eyemass * 3)))
    # Legs (below the band) -- anchored.
    legs = body.subsurface(pygame.Rect(0, _BOT, _CW, _CH - _BOT)).copy()
    cell.blit(legs, (0, 0))

    # Torso halves peel outward about the sternum.
    band_h = _BOT - _TOP
    left = body.subsurface(pygame.Rect(0, _TOP, _LX, band_h)).copy()
    right = body.subsurface(pygame.Rect(_LX, _TOP, _CW - _LX, band_h)).copy()
    deg = split * 26.0
    out = split * 9.0
    _blit_hinged(cell, left, (_LX, band_h / 2.0), (_LX, _CCY),
                 deg, (-out, 0))
    _blit_hinged(cell, right, (0, band_h / 2.0), (_LX, _CCY),
                 -deg, (out, 0))

    # Torn-flesh edges along the vertical tear.
    if split > 0.05:
        _draw_torn_seam(cell, _LX, _CCY, split, t, seed)

    # Eyes erupting across the peeled skin itself (drawn on top of the
    # flaps) -- the wrongness spreads beyond the maw.
    if eyemass > 0.35:
        _draw_skin_eyes(cell, _LX, _CCY, split, eyemass, facing, t, seed)

    # Tremble: small whole-figure shake, strongest mid-transform.
    shake = 2.2 * (1.0 - abs(2.0 * morph - 1.0))
    jx = int(math.sin(t * 41.0 + seed) * shake)
    jy = int(math.cos(t * 37.0 + seed * 1.7) * shake)
    surf.blit(cell, (x - _LX + jx, y - _LY + jy))


def _draw_cavity(cell, cx, cy, split, eyemass, facing, t, seed):
    """A vertical maw: irregular flesh rim, layered throat, side teeth,
    eyes, ichor."""
    rx = 4 + split * 9
    ry = 6 + split * 16
    rng = random.Random(seed * 17 + 1)

    # Irregular outer flesh rim (jagged polygon, not a clean disc).
    n = 16
    pts = []
    for i in range(n):
        a = i / n * math.tau
        jit = rng.uniform(0.80, 1.15)
        pts.append((cx + math.cos(a) * rx * 1.28 * jit,
                    cy + math.sin(a) * ry * 1.18 * jit))
    pygame.draw.polygon(cell, _FLESH_LO, pts)
    pygame.draw.ellipse(cell, _FLESH,
                        (cx - rx * 1.05, cy - ry, rx * 2.1, ry * 2))
    # Layered throat -> darker toward the centre for depth.
    for k, frac in enumerate((0.82, 0.58, 0.34)):
        col = _lerp_col(_FLESH, _THROAT, (k + 1) / 3.0)
        pygame.draw.ellipse(cell, col,
                            (cx - rx * frac, cy - ry * frac,
                             rx * 2 * frac, ry * 2 * frac))

    # Teeth down the left and right lips (a vertical mouth), irregular
    # in length and spacing so they read as fangs, not a zipper.
    rows = int(3 + split * 6)
    for i in range(rows):
        fr = (i + 0.5) / rows
        ty = cy - ry * 0.84 + fr * ry * 1.68 + rng.uniform(-1.4, 1.4)
        ln = (2.4 + rng.uniform(0, 2.6)) * (0.55 + split * 0.6)
        half = 1.2 + rng.uniform(0, 1.0)
        lx = cx - rx * 0.80
        pygame.draw.polygon(cell, _TEETH,
                            [(lx, ty - half), (lx, ty + half), (lx + ln, ty)])
        ln2 = (2.4 + rng.uniform(0, 2.6)) * (0.55 + split * 0.6)
        rxp = cx + rx * 0.80
        pygame.draw.polygon(cell, _TEETH,
                            [(rxp, ty - half), (rxp, ty + half), (rxp - ln2, ty)])

    # Eyes packed inside the throat, blinking on staggered phases. Each
    # sits in a dark socket so it reads against the cavity, with a wet
    # glint -- the Yellow-King "mass of eyes" signature.
    if eyemass > 0.0:
        ecount = int(3 + eyemass * 12)
        fx, fy = facing
        erng = random.Random(seed * 911 + 7)
        for i in range(ecount):
            u = v = 0.0
            for _ in range(8):
                u = erng.uniform(-1, 1)
                v = erng.uniform(-1, 1)
                if u * u + v * v <= 1.0:
                    break
            ex = cx + u * rx * 0.74
            ey = cy + v * ry * 0.80
            if 0.5 + 0.5 * math.sin(t * 1.7 + i * 0.9 + seed) < 0.26:
                continue
            r = erng.choice((2, 2, 3))
            pygame.draw.circle(cell, _THROAT, (int(ex), int(ey)), r + 1)
            pygame.draw.circle(cell, _EYE_WHITE, (int(ex), int(ey)), r)
            pygame.draw.circle(cell, _EYE_PUPIL,
                               (int(ex + fx), int(ey + fy)), 1)
            try:
                cell.set_at((int(ex - 1), int(ey - 1)), _ICHOR_HI)
            except (IndexError, ValueError):
                pass

    # Ichor: wet strands stretched down the maw, wobbling.
    if split > 0.4:
        strands = 2 + int(split * 2)
        for i in range(strands):
            sx = cx - rx * 0.5 + (i / max(1, strands - 1)) * rx
            wob = math.sin(t * 3.0 + i * 1.3 + seed) * 1.4
            pygame.draw.line(cell, _ICHOR,
                             (int(sx), int(cy - ry * 0.74)),
                             (int(sx + wob), int(cy + ry * 0.74)), 1)
        try:
            cell.set_at((int(cx), int(cy - ry * 0.3)), _ICHOR_HI)
        except (IndexError, ValueError):
            pass


def _draw_skin_eyes(cell, cx, cy, split, eyemass, facing, t, seed):
    """A scatter of eyes opening on the peeled flaps / shoulders, so the
    wrongness reads as spreading across the whole vessel, not just the
    maw. Most stay shut and open intermittently."""
    rng = random.Random(seed * 1303 + 11)
    fx, fy = facing
    for i in range(int(eyemass * 7)):
        ang = rng.uniform(0, math.tau)
        rad = rng.uniform(0.95, 1.4)
        ex = cx + math.cos(ang) * (7 + split * 9) * rad
        ey = cy + math.sin(ang) * (11 + split * 14) * rad * 0.72
        if 0.5 + 0.5 * math.sin(t * 1.4 + i * 1.3 + seed * 2.0) < 0.46:
            continue
        pygame.draw.circle(cell, _FLESH_LO, (int(ex), int(ey)), 3)
        pygame.draw.circle(cell, _EYE_WHITE, (int(ex), int(ey)), 2)
        pygame.draw.circle(cell, _EYE_PUPIL, (int(ex + fx), int(ey + fy)), 1)


def _draw_torn_seam(cell, cx, cy, split, t, seed):
    """Ragged dark-red flesh down the vertical tear + drips."""
    rng = random.Random(seed * 53 + 3)
    ry = 6 + split * 16
    steps = 7
    prev = (cx, cy - ry * 0.9)
    for i in range(1, steps + 1):
        fr = i / steps
        nx = cx + rng.uniform(-1.6, 1.6) * split
        ny = cy - ry * 0.9 + fr * ry * 1.8
        pygame.draw.line(cell, _TORN, (int(prev[0]), int(prev[1])),
                         (int(nx), int(ny)), 2)
        prev = (nx, ny)
    # Gore flecks flung from the tear.
    for _ in range(int(split * 5)):
        gx = cx + rng.uniform(-9, 9) * split
        gy = cy + rng.uniform(-ry, ry) * 0.8
        try:
            cell.set_at((int(gx), int(gy)), _GORE)
        except (IndexError, ValueError):
            pass
