"""Infested resisters: bespoke body-horror overlays (NARRATIVE infestation)."""
import math
import random
import pygame
from constants import C_BLACK


# ---- Infested resisters (NARRATIVE infestation) -----------------------
# Each MUTATED resister has a bespoke body-horror form -- their flesh
# deforms AND the fold's gold/Sign shows in the wound ("both, fused").
# Authored as a discrete state (no crossfade), drawn OVER the base sprite
# so the person stays recognisable under the wrongness. The SAME
# transformation is authored at portrait scale in ui/dialog.py so the two
# always agree. Keyed by sprite_kind. A slow time throb keeps it alive.
_MEAT = (96, 22, 26); _MEAT_LO = (58, 12, 16); _MEAT_HI = (150, 44, 46)
_WBONE = (222, 214, 196); _WSKIN = (214, 182, 150)
_WGOLD = (236, 204, 64); _WGOLD_HI = (252, 232, 150)
# Garrick's cancer: sallow flayed flesh, engorged vessels, and black-gold
# tumors that BULGE out of the body (a shaded dome lit cold at the crown,
# gold molten light leaking from the fissures cracking it open).
_SALLOW = (170, 162, 130); _SALLOW_LO = (104, 98, 78)
_INFLAME = (150, 70, 62); _INFLAME_LO = (90, 42, 37); _VEIN = (120, 34, 36)
_TUMOR_DK = (9, 8, 12); _TUMOR_LIT = (60, 54, 66); _TUMOR_SPEC = (94, 88, 100)


def _lerp_rgb(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _gold_in_wound(surf, cx, cy, R, peak=64):
    """Additive gold glow welling up from inside an opened wound."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    for i in range(R, 0, -1):
        a = int(peak * (1 - i / R))
        if a > 0:
            pygame.draw.circle(g, (_WGOLD[0], _WGOLD[1], _WGOLD[2], a),
                               (R + 1, R + 1), i)
    surf.blit(g, (cx - R - 1, cy - R - 1), special_flags=pygame.BLEND_RGBA_ADD)


def _infest_tisdale_boy(surf, x, y, t, view="front"):
    # The lying boy's mouth won't stop -- and now his whole BODY is the
    # mouth. A vertical MAW splits him head to hem: raw-flesh lips bow open
    # around a deep dark throat (gold burning down in the gullet), and rows
    # of fangs interlock down both lips. His eyes are shoved to the corners
    # of the cloven head. (Child geometry: head ~y-8, body y..y+14.)
    # View-aware: the maw holds from every angle (it leans toward the lead in
    # profile); only the eyes change -- front shows the pair, a profile the
    # near eye, the back of the cloven head none.
    thr = 0.5 + 0.5 * math.sin(t * 2.6)
    hy = y - 8
    s = 1 if view == "right" else (-1 if view == "left" else 0)
    cx = x + s                                       # the maw leans toward the lead
    top = hy - 5; bot = y + 13; mid = (top + bot) // 2; half = (bot - top) / 2
    gap = 3 + int(1.5 * thr)                         # half-width at the widest (it flexes)

    def _edge(yy):                                   # maw half-width at row yy (a vertical lens)
        return gap * max(0.22, 1.0 - abs(yy - mid) / half)
    _gold_in_wound(surf, cx, mid, 4, 30 + int(16 * thr))         # glow deep in the throat
    pygame.draw.polygon(surf, _MEAT,                 # raw-flesh lips (outer lens)
                        [(cx, top), (cx + gap + 1, mid), (cx, bot), (cx - gap - 1, mid)])
    pygame.draw.polygon(surf, (14, 7, 9),            # the dark throat (a deep gullet, not flat red)
                        [(cx, top + 1), (cx + gap - 1, mid), (cx, bot - 1), (cx - gap + 1, mid)])
    pygame.draw.line(surf, _WGOLD, (cx, top + 2), (cx, bot - 2), 1)   # gold burning down the gullet
    for i, yy in enumerate(range(top + 1, bot, 2)):  # fangs interlocking down both lips
        w = _edge(yy)
        if w < 1:
            continue
        if i % 2 == 0:
            lx = int(cx - w)
            pygame.draw.polygon(surf, _WBONE, [(lx, yy - 1), (lx, yy + 2), (lx + 2, yy)])
        else:
            rx = int(cx + w)
            pygame.draw.polygon(surf, _WBONE, [(rx, yy - 1), (rx, yy + 2), (rx - 2, yy)])
    if view == "front":
        pygame.draw.circle(surf, (236, 232, 226), (cx - gap - 2, top + 1), 1)  # eyes shoved out
        pygame.draw.circle(surf, (236, 232, 226), (cx + gap + 2, top + 1), 1)
    elif s:                                          # profile -- only the near eye
        pygame.draw.circle(surf, (236, 232, 226), (cx + (gap + 2) * s, top + 1), 1)
    # back: the back of the cloven head -- no eyes.


def _infest_hettie(surf, x, y, t, view="front"):
    # Her face bloomed open -- and the bloom runs down her. The head splits
    # into a radial petal-star and the torso unzips into a vertical seam with
    # skin-petals curling out along both sides, gold burning up the opening:
    # a flayed flower the length of her. (Adult geometry: head ~y-11, body
    # y-2..y+16. Distinct from Toby's single slot -- this one SPLAYS.)
    # View-aware: the petal-star + body seam hold from every angle; the
    # face-front detail (raw socket + the carved Sign) follows the facing --
    # front-centred, shifted to the lead side in profile, and gone on the
    # back (just a dark hollow at the heart of the bloomed skull).
    thr = 0.5 + 0.5 * math.sin(t * 2.0)
    hy = y - 11
    s = 1 if view == "right" else (-1 if view == "left" else 0)
    _gold_in_wound(surf, x, hy, 3, 26 + int(14 * thr))        # glow under, a halo
    span = 5 + 2 * thr
    for k in range(5):                                        # head bloom: five petals
        a = -math.pi / 2 + k * (2 * math.pi / 5)
        tip = (int(x + math.cos(a) * span), int(hy + math.sin(a) * span))
        bx, by = -math.sin(a) * 2, math.cos(a) * 2
        pygame.draw.polygon(surf, _WSKIN,
                            [(int(x + bx), int(hy + by)),
                             (int(x - bx), int(hy - by)), tip])
    pygame.draw.polygon(surf, _MEAT,                          # the body seam unzips
                        [(x - 2, y - 1), (x + 2, y - 1), (x + 1, y + 14), (x - 1, y + 14)])
    for sy in range(2, 15, 4):                                # skin-petals peeling off both sides
        pygame.draw.polygon(surf, _WSKIN, [(x - 2, y + sy), (x - 2, y + sy + 3), (x - 6, y + sy + 1)])
        pygame.draw.polygon(surf, _WSKIN, [(x + 2, y + sy), (x + 2, y + sy + 3), (x + 6, y + sy + 1)])
    pygame.draw.line(surf, _WGOLD, (x, y - 1), (x, y + 13), 1)  # gold up the seam
    if view == "back":
        pygame.draw.circle(surf, (20, 12, 16), (x, hy), 2)    # dark hollow -- back of the bloom
    else:
        sx = x + 2 * s                                        # face detail leads in profile
        pygame.draw.circle(surf, _MEAT, (sx, hy), 3)          # raw flesh socket
        pygame.draw.line(surf, _WGOLD, (sx, hy - 2), (sx, hy + 2), 1)  # the Sign glint
        pygame.draw.line(surf, _WGOLD, (sx, hy), (sx - 2, hy - 1), 1)
        pygame.draw.line(surf, _WGOLD, (sx, hy), (sx + 2, hy - 1), 1)


def _tumor_veins(surf, cx, cy, n, length, rng, col=_VEIN):
    """Engorged vessels branching out from a feeder point across the flesh."""
    for _ in range(n):
        a = rng.uniform(0, 6.28); x0, y0 = float(cx), float(cy)
        steps = rng.randint(2, 4); seg = length / steps; pts = [(x0, y0)]
        for _ in range(steps):
            a += rng.uniform(-0.7, 0.7)
            x0 += math.cos(a) * seg; y0 += math.sin(a) * seg
            pts.append((x0, y0))
        for i in range(len(pts) - 1):
            pygame.draw.line(surf, col, pts[i], pts[i + 1], 1)


def _popout_tumor(surf, cx, cy, r, thr, rng):
    """A black-gold tumor BULGING out of the flesh -- not a flat disc drawn on
    it: a contact shadow grounds it, the raw skin puckers in a ring at its
    base, the silhouette is irregular (under-lobes), the mass is a shaded dome
    (dark base -> cold-lit crown, shifted up for volume), and molten gold
    light leaks from the fissures cracking it open."""
    R = r + int(thr * 1.5)
    sc = pygame.Surface((R * 3, R * 2), pygame.SRCALPHA)            # contact shadow
    pygame.draw.ellipse(sc, (0, 0, 0, 90), (0, 0, R * 3, R * 2))
    surf.blit(sc, (cx - R - 1, cy + R - 4))
    pygame.draw.circle(surf, _INFLAME, (cx, cy + 1), R + 2)        # puckered raw-skin ring
    pygame.draw.circle(surf, _INFLAME_LO, (cx, cy + 2), R + 2, 1)
    for _ in range(3):                                            # irregular under-lobes
        a = rng.uniform(0, 6.28); d = rng.uniform(0.5, 0.9) * R
        pygame.draw.circle(surf, _TUMOR_DK,
                           (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)),
                           max(1, int(rng.uniform(0.4, 0.6) * R)))
    for i in range(R, 0, -1):                                     # shaded bulging dome
        f = (R - i) / R; oy = -int((R - i) * 0.55)
        pygame.draw.circle(surf, _lerp_rgb(_TUMOR_DK, _TUMOR_LIT, f ** 1.4), (cx, cy + oy), i)
    pygame.draw.circle(surf, _TUMOR_SPEC, (cx - R // 3, cy - R // 2), max(1, R // 4))  # specular
    crown = (cx, cy - R // 2)                                     # gold molten fissures
    _gold_in_wound(surf, crown[0], crown[1], max(2, R // 2), 34 + int(20 * thr))
    rng2 = random.Random(cx * 7 + cy)
    for _ in range(3):
        a = rng2.uniform(-2.2, 2.2)
        ex = crown[0] + math.cos(a + 1.57) * R; ey = crown[1] + math.sin(a + 1.57) * R * 0.95
        mx = (crown[0] + ex) / 2 + rng2.uniform(-2, 2); my = (crown[1] + ey) / 2
        pygame.draw.lines(surf, _WGOLD, False, [crown, (mx, my), (ex, ey)], 1)
    pygame.draw.circle(surf, _WGOLD_HI, crown, 1)


def _infest_old_townsman(surf, x, y, t, view="front"):
    # (Garrick) skinned to sallow raw flesh, and a black-gold CANCER eats
    # him: engorged vessels CREEP all over the flayed skin (this carries the
    # spread) and erupt in SMALL tumors that bulge from the flesh -- shaded
    # black nodules lit cold at the crown with gold cracking from the bigger
    # ones. Kept small and within the silhouette so they read as growths
    # through him, not blobs stuck on. (Adult geometry: head ~y-12, body
    # y-1..y+16.)
    # View-aware AND asymmetric: front/right/left/back each get their own
    # nodule+vein layout and rng seed -- the profiles are NOT mirrors and the
    # back is its own sprite. The torso narrows in profile; the head leads a
    # socket in profile and loses its face on the back.
    thr = 0.5 + 0.5 * math.sin(t * 2.2)
    hy = y - 12
    profile = view in ("left", "right")
    s = 1 if view == "right" else (-1 if view == "left" else 0)
    hw = 4 if profile else 6
    hr = 5 if profile else 6
    hx = x + s                                                   # head leads toward the facing
    pygame.draw.circle(surf, _SALLOW, (hx, hy), hr)              # flayed raw-flesh head
    pygame.draw.circle(surf, _SALLOW_LO, (hx, hy), hr, 1)
    pygame.draw.rect(surf, _SALLOW, (x - hw, y - 1, hw * 2, 17))  # flayed raw-flesh torso
    pygame.draw.rect(surf, _SALLOW_LO, (x - hw, y - 1, hw * 2, 17), 1)
    # Per-view sunken sockets + a SMALL nodule layout (r 2-3), each unique.
    if view == "right":
        seed = 23; pits = [(hx + 1, hy - 1)]
        nodes = [(hx - 2, hy - 1, 2), (x + 1, y + 3, 3), (x - 1, y + 7, 2), (x + 1, y + 11, 2)]
    elif view == "left":
        seed = 37; pits = [(hx - 1, hy - 1)]
        nodes = [(hx + 2, hy, 2), (x - 2, y + 5, 3), (x + 1, y + 9, 2), (x - 1, y + 12, 2)]
    elif view == "back":
        seed = 51; pits = []
        nodes = [(x - 2, hy - 2, 2), (x + 2, y + 4, 2), (x - 3, y + 8, 3), (x + 1, y + 12, 2)]
    else:                                                        # front
        seed = 11; pits = [(x - 2, hy - 1), (x + 2, hy - 1)]
        nodes = [(x + 2, hy + 1, 2), (x - 3, y + 4, 3), (x + 2, y + 8, 2), (x - 1, y + 12, 3)]
    for ex, ey in pits:
        pygame.draw.circle(surf, (44, 30, 28), (ex, ey), 1)
    rng = random.Random(seed)
    vrng = random.Random(seed ^ 0x55)
    # The spread: a vein network creeping across the flayed flesh (feeders
    # spanning the torso + vessels off every nodule). This does the work.
    for fx, fy in [(x, y + 2), (x - hw + 1, y + 8), (x + hw - 1, y + 11)]:
        _tumor_veins(surf, fx, fy, 4, 10, vrng)
    for nx, ny, _r in nodes:
        _tumor_veins(surf, nx, ny, 3, 7, vrng)
    # Then the small pop-out nodules bulging from the flesh.
    for nx, ny, r in nodes:
        _popout_tumor(surf, nx, ny, r, thr, rng)


_INFEST_WORLD = {
    "tisdale_boy": _infest_tisdale_boy,
    "hettie": _infest_hettie,
    "old_townsman": _infest_old_townsman,
}


def draw_infested_overlay(surf, x, y, kind, view="front"):
    """Drawn OVER a mutated resister's base sprite: their bespoke flesh-
    horror form. `view` ('front'/'back'/'left'/'right') matches the base
    sprite's camera-relative facing so the horror reads from every angle
    (no face on the back of the head, profile in the sides). Falls back to a
    generic jaundice + eye-void wash for any kind without a dedicated
    incident."""
    fn = _INFEST_WORLD.get(kind)
    t = pygame.time.get_ticks() / 1000.0
    if fn is not None:
        fn(surf, x, y, t, view)
        return
    # Generic fallback (unchanged from the old overlay).
    wash = pygame.Surface((26, 36), pygame.SRCALPHA)
    wash.fill((168, 142, 56, 42))
    surf.blit(wash, (x - 13, y - 22))
    pygame.draw.rect(surf, (2, 0, 4), (x - 3, y - 13, 2, 2))
    pygame.draw.rect(surf, (2, 0, 4), (x + 1, y - 13, 2, 2))
