"""Infested resisters: bespoke body-horror overlays (NARRATIVE infestation)."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_common import _breath_lift


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


def _infest_toby(surf, x, y, t, view="front"):
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
    # (Garrick) the cancer took the arm that would point. ONE great
    # black-gold mass swallows his shoulder and arm, bulging out past the
    # coat's silhouette in lobes; a single gold fissure splits its crown
    # (the thing that watches the road for him now); his eyes are sealed
    # over ("didn't need eyes for it"); a FEW thick engorged vessels anchor
    # the mass into his neck and chest. Fewer, larger features -- the man
    # stays recognisable under the wrongness, the horror has one centre.
    # (Adult geometry: head ~y-12 under the hat, body y-2..y+17. The mass
    # sits on his right side -- screen LEFT when he faces us, leading or
    # trailing the turn in profile, wrapping the shoulder from behind.)
    thr = 0.5 + 0.5 * math.sin(t * 2.2)
    hy = y - 12
    s = 1 if view == "right" else (-1 if view == "left" else 0)
    SEAL = (118, 106, 84)                                  # sick sealed-lid skin

    def vessel(pts, w=2):
        for i in range(len(pts) - 1):
            pygame.draw.line(surf, _VEIN, pts[i], pts[i + 1], w)

    def mass(mx, my, r, rng_seed):
        # the dome + its under-lobes; crown fissure + gold come from
        # _popout_tumor, lobes first so the dome reads as one grown thing
        rng = random.Random(rng_seed)
        for la, ld, lr in ((2.6, 0.9, 0.55), (3.6, 0.8, 0.45), (1.9, 1.0, 0.4)):
            pygame.draw.circle(surf, _TUMOR_DK,
                               (int(mx + math.cos(la) * ld * r),
                                int(my + math.sin(la) * ld * r)),
                               max(2, int(r * lr)))
        _popout_tumor(surf, mx, my, r, thr, rng)

    if view == "back":
        # the mass wraps the shoulder from behind -- a black moon rising
        # over the yoke; vessels cross the spine to feed it; no face
        mx, my = x + 4, y + 1
        vessel([(x - 5, y + 9), (x - 1, y + 5), (mx - 2, my + 2)])
        vessel([(x - 3, y + 14), (x + 1, y + 9), (mx - 1, my + 3)])
        mass(mx, my, 4, 53)
        pygame.draw.circle(surf, _TUMOR_DK, (mx + 2, my - 4), 2)   # cresting lobe
        return
    if s:
        # profile: his right side LEADS when he faces left (the mass comes
        # at you before the man) and TRAILS when he faces right (the man
        # first, the thing looming off his back). Both land screen-left.
        mx, my = x - 4, y + 2
        # sealed near eye (the far one is hidden by the head)
        pygame.draw.rect(surf, SEAL, (x + s * 2 - 1, hy - 1, 3, 2))
        pygame.draw.line(surf, (60, 48, 40), (x + s * 2 - 1, hy), (x + s * 2 + 1, hy), 1)
        vessel([(x + s, y - 1), (mx, my - 2)], w=1)
        vessel([(x + 3, y + 8), (mx + 1, my + 3)], w=1)
        mass(mx, my, 4, 23 if view == "right" else 37)
        # the arm it took: fused down his side to a half-clenched knot
        pygame.draw.line(surf, _TUMOR_DK, (mx, my + 3), (mx, y + 12), 3)
        pygame.draw.circle(surf, _TUMOR_DK, (mx, y + 13), 2)
        _gold_in_wound(surf, mx, y + 13, 2, 14 + int(8 * thr))
        return
    # FRONT -- his right shoulder/arm = screen left
    mx, my = x - 5, y + 1
    # both eyes sealed over: lids of sick skin, a dark healed seam
    for ex in (x - 3, x + 3):
        pygame.draw.rect(surf, SEAL, (ex - 1, hy - 1, 3, 2))
        pygame.draw.line(surf, (60, 48, 40), (ex - 1, hy), (ex + 1, hy), 1)
    # a few THICK vessels, hand-placed: up the neck to the jaw, across the
    # chest under the coat, down toward the hip -- anchors, not spaghetti
    vessel([(x - 2, hy + 5), (x - 4, y - 1), (mx + 1, my - 3)])
    vessel([(x + 4, y + 6), (x, y + 4), (mx + 2, my + 2)])
    vessel([(mx + 1, my + 4), (mx + 2, y + 10)])
    mass(mx, my, 5, 11)
    # the arm it took, fused to his side: a tar sleeve ending in a knot
    # that will never point again, gold seeping at the knuckles
    pygame.draw.line(surf, _TUMOR_DK, (mx - 1, my + 4), (mx - 1, y + 13), 3)
    pygame.draw.circle(surf, _TUMOR_DK, (mx - 1, y + 14), 2)
    pygame.draw.circle(surf, _TUMOR_LIT, (mx - 2, y + 13), 1)
    _gold_in_wound(surf, mx - 1, y + 14, 2, 16 + int(10 * thr))


def _infest_old_pell(surf, x, y, t, view="front"):
    # Old Pell stopped marking the calendar, so the calendar marks HIM.
    # Tally-scars carve themselves across his face and torso in fours with
    # the fifth slashed through; one eye is crossed off (a scar X over a
    # void socket); and over his heart sits the 14th, the day that was
    # "already crossed": a heavier re-cut stroke that never closed, the
    # fold's gold welling in the line. (Adult geometry: head ~y-12 under
    # the hat brim, body y-2..y+17. Distinct from Garrick's cancer -- Pell
    # is INSCRIBED, not overgrown.)
    thr = 0.5 + 0.5 * math.sin(t * 1.8)
    SCAR = (46, 22, 24)
    s = 1 if view == "right" else (-1 if view == "left" else 0)
    hy = y - 12

    def tally(tx, ty, n=4, slash=True, h=3):
        for i in range(n):
            pygame.draw.line(surf, SCAR, (tx + i * 2, ty), (tx + i * 2, ty + h - 1), 1)
        if slash:
            pygame.draw.line(surf, _MEAT, (tx - 1, ty + h - 1), (tx + n * 2 - 1, ty), 1)

    if view == "back":
        # the count continues where he can't see it: rows across the yoke,
        # and the heavy line re-cut straight down the spine seam
        tally(x - 6, y - 1); tally(x + 1, y - 1)
        tally(x - 5, y + 4); tally(x + 2, y + 4, slash=False)
        tally(x - 4, y + 9, n=3)
        pygame.draw.line(surf, _MEAT, (x, y + 2), (x, y + 13), 2)
        pygame.draw.line(surf, _WGOLD, (x, y + 4), (x, y + 11), 1)
        tally(x - 4, hy + 2, n=3, slash=False, h=2)        # up the nape
        return
    if s:
        # profile: the rows wrap the lead cheek and the narrowed torso;
        # the crossed-off eye leads
        tally(x + 2 * s - 3, hy + 1, n=3, h=2)
        ex = x + 3 * s
        pygame.draw.rect(surf, (6, 4, 6), (ex - 2, hy - 3, 4, 4))
        _gold_in_wound(surf, ex, hy - 1, 2, 16 + int(10 * thr))
        pygame.draw.line(surf, _MEAT, (ex - 2, hy - 3), (ex + 2, hy + 1), 1)
        pygame.draw.line(surf, _MEAT, (ex + 2, hy - 3), (ex - 2, hy + 1), 1)
        tally(x - 4, y + 1); tally(x - 3, y + 6, slash=False)
        hx = x + 2 * s
        _gold_in_wound(surf, hx, y + 9, 3, 22 + int(14 * thr))
        pygame.draw.line(surf, _MEAT, (hx, y + 4), (hx, y + 13), 3)
        pygame.draw.line(surf, _WGOLD, (hx, y + 5), (hx, y + 12), 1)
        return
    # front: rows under the hat brim, then the ledger of days down the body
    tally(x - 5, hy - 4, n=3, slash=False, h=2)
    tally(x - 4, hy + 2, n=4, h=2)
    ex = x - 3                                             # the crossed-off eye
    pygame.draw.rect(surf, (6, 4, 6), (ex - 2, hy - 3, 4, 4))
    _gold_in_wound(surf, ex, hy - 1, 2, 16 + int(10 * thr))
    pygame.draw.line(surf, _MEAT, (ex - 2, hy - 3), (ex + 2, hy + 1), 1)
    pygame.draw.line(surf, _MEAT, (ex + 2, hy - 3), (ex - 2, hy + 1), 1)
    tally(x - 6, y + 1); tally(x + 1, y + 1)
    tally(x + 1, y + 6); tally(x - 5, y + 11, n=3, slash=False)
    # the 14th, crossed twice: the heavier line over the heart, still open
    # ("mine's the heavier line; you can tell")
    hx = x - 3
    _gold_in_wound(surf, hx, y + 8, 4, 26 + int(16 * thr))
    pygame.draw.line(surf, _MEAT, (hx, y + 4), (hx, y + 13), 3)
    pygame.draw.line(surf, _MEAT_LO, (hx - 2, y + 4), (hx - 2, y + 13), 1)
    pygame.draw.line(surf, _WGOLD, (hx, y + 5), (hx, y + 12), 1)
    pygame.draw.circle(surf, _WGOLD_HI, (hx, y + 8), 1)


_INFEST_WORLD = {
    "toby": _infest_toby,
    "hettie": _infest_hettie,
    "old_townsman": _infest_old_townsman,
}

# Mutated locals who SHARE a sprite kind resolve by name first (Old Pell
# wears the same old_townsman body as Garrick but carries his own horror).
_INFEST_NAMED = {
    "Old Pell": _infest_old_pell,
}


def draw_infested_overlay(surf, x, y, kind, view="front", name=None, seed=0):
    """Drawn OVER a mutated resister's base sprite: their bespoke flesh-
    horror form. `view` ('front'/'back'/'left'/'right') matches the base
    sprite's camera-relative facing so the horror reads from every angle
    (no face on the back of the head, profile in the sides). `name` picks a
    name-keyed incident over the kind-keyed one (sprite kinds are shared);
    `seed` rides the base sprite's idle breath so the wound moves with the
    flesh. Falls back to a generic jaundice + eye-void wash for anyone
    without a dedicated incident."""
    y -= _breath_lift(seed)
    fn = _INFEST_NAMED.get(name) or _INFEST_WORLD.get(kind)
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
