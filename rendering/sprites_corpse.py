"""Downed-NPC corpse sprites + fold-claim / rot infection overlays."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_wound import _gold_in_wound


# Dominant garment tint per local sprite kind, so a downed local still
# reads as *who* they were (the Sheriff's navy, Hettie's plum) rather
# than an anonymous heap. Falls back to a drab brown.
_CORPSE_TINT = {
    "sheriff":      (32, 50, 100),
    "royce":        (118, 92, 60),
    "hettie":       (118, 70, 92),
    "townswoman":   (150, 56, 70),
    "toby":  (172, 156, 70),
    "old_townsman": (78, 60, 42),
    "preacher":     (34, 32, 40),
    "clerk":        (60, 54, 60),
    "cultist":      (150, 140, 120),
}


def _corpse_echo_toby(surf, hx, hy, x, y, mold):
    """The lying boy's mouth never stopped -- dropped, his head still hangs
    open as one big gaping maw. At corpse scale this has to be a BOLD shape,
    not teeth: the head end is overdrawn as an oversized dark open mouth with
    a pale jaw rim and gold burning in the throat, gaping wider as the fold
    works him. Distinct at a glance from Hettie's reach."""
    w = 4 + mold                                # the gape widens with the mold
    pygame.draw.ellipse(surf, (236, 230, 220),
                        (hx - w, hy - w // 2 - 1, w * 2, w + 2))   # pale jaw rim
    pygame.draw.ellipse(surf, (6, 3, 4),
                        (hx - w + 1, hy - w // 2, w * 2 - 2, w))   # the dark gape
    pygame.draw.line(surf, (210, 158, 44), (hx, hy - 1), (hx, hy + 1), 1)  # gold throat
    if mold >= 2:                               # a few bold teeth bridge the gape
        for tx in (-w + 2, 0, w - 2):
            pygame.draw.line(surf, (236, 230, 220),
                             (hx + tx, hy - w // 2), (hx + tx, hy + w // 2 - 1), 1)


def _corpse_echo_hettie(surf, hx, hy, x, y, mold):
    """Hettie kept the lights on. Dropped, the arm is still flung out too
    far -- reaching, fingers grown long, an unmistakable silhouette
    stretched toward a switch that isn't there."""
    sgn = -1 if hx < x else 1                   # reach AWAY from the head
    ax = x + sgn * 16
    pygame.draw.line(surf, (198, 170, 146), (x + sgn * 4, y + 5),
                     (ax, y + 9), 2)            # too-long arm, brighter than body
    for fdy in (-4, -1, 2, 5):                   # splayed clutching fingers
        pygame.draw.line(surf, (198, 170, 146),
                         (ax, y + 9), (ax + sgn * 5, y + 9 + fdy), 1)


_CORPSE_ECHO = {
    "toby": _corpse_echo_toby,
    "hettie": _corpse_echo_hettie,
}


# ---- Corpse infection overlays ----------------------------------------
# When the fold claims a corpse (mold >= 1) it spreads INFECTION through the
# flesh -- gold rot welling up from INSIDE the body, sickly discolour, the
# Yellow Sign branded at full claim. The corruption is warm gold light from
# within (the body still reads as a body); it is NEVER a black void. Each
# overlay is drawn OVER the already-drawn slumped body. NAMED resisters get
# the wound shaped like their living mutation (a gold maw for Toby, a peeled
# Sign-seam for Hettie, gold faces for Garrick); unnamed kinds get the
# generic gold rot. mold is the intensity (1..3).

def _corpse_rot(surf, x, y, mold):
    """Sickly discoloured patches creeping over the flesh -- the meat going
    wrong before the gold breaks through."""
    rot = (92, 96, 44)
    pygame.draw.rect(surf, rot, (x - 9, y + 4, 6, 3))
    if mold >= 2:
        pygame.draw.rect(surf, rot, (x + 3, y - 1, 6, 2))
        pygame.draw.rect(surf, rot, (x - 4, y - 2, 4, 2))


def _corpse_sign(surf, x, y):
    """The Yellow Sign branded into the body at full claim."""
    pygame.draw.line(surf, (252, 222, 112), (x - 3, y + 2), (x + 3, y + 2), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y - 1), (x, y + 5), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y + 2), (x - 2, y), 1)
    pygame.draw.line(surf, (252, 222, 112), (x, y + 2), (x + 2, y), 1)


def _corpse_infect_generic(surf, x, y, body, body_lo, mold):
    _corpse_rot(surf, x, y, mold)
    _gold_in_wound(surf, x, y + 2, 3 + mold, 48 + 20 * mold)     # gold welling up a wound
    for vx in (-8, -4, 5, 9)[:1 + mold]:                        # gold veins branching out
        pygame.draw.line(surf, (208, 166, 58),
                         (x, y + 2), (x + vx, y + 2 + (vx % 3) - 1), 1)
    if mold >= 3:
        _corpse_sign(surf, x, y)


def _corpse_claim_toby(surf, x, y, body, body_lo, mold):
    # Toby's wound is the maw he became -- but it GLOWS: the fold's gold burns
    # up out of the split flesh, dark meat lips and a few pale teeth framing
    # it. An infected mouth opening down the body, not a black hole.
    _corpse_rot(surf, x, y, mold)
    h = 1 + mold
    _gold_in_wound(surf, x, y + 2, 4 + mold, 78 + 18 * mold)     # gold up the throat
    pygame.draw.rect(surf, (96, 30, 26), (x - 11, y + 1 - h, 23, 1))   # upper meat lip
    pygame.draw.rect(surf, (96, 30, 26), (x - 11, y + 2 + h, 23, 1))   # lower meat lip
    for tx in range(-9, 11, 4):                                  # pale teeth along the lips
        pygame.draw.line(surf, (230, 222, 202),
                         (x + tx, y + 1 - h), (x + tx, y + 2 + h), 1)


def _corpse_claim_hettie(surf, x, y, body, body_lo, mold):
    # Hettie peels open down her length: skin-flaps curl back off a seam that
    # wells gold, the Yellow Sign branded in it. Her reaching-arm echo still
    # lays over the top. Infected glow, not a slit.
    _corpse_rot(surf, x, y, mold)
    _gold_in_wound(surf, x, y + 2, 4 + mold, 60 + 16 * mold)     # gold up the seam
    skin = (212, 182, 156)
    for px in range(-9, 11, 6):                                  # skin-flaps peeling back
        d = 1 + mold
        pygame.draw.polygon(surf, skin, [(x + px, y - 1), (x + px + 4, y - 1),
                                         (x + px + 2, y - 1 - d)])
        pygame.draw.polygon(surf, skin, [(x + px, y + 6), (x + px + 4, y + 6),
                                         (x + px + 2, y + 6 + d)])
    if mold >= 2:
        _corpse_sign(surf, x, y)
    else:
        pygame.draw.line(surf, (250, 210, 92), (x - 7, y + 2), (x + 8, y + 2), 1)


def _corpse_claim_old_townsman(surf, x, y, body, body_lo, mold):
    # Faces strain up through Garrick's flesh, each lit GOLD from within --
    # gold faces surfacing across the body with dark sunken features, more of
    # them as the fold works him. Not black pits.
    _corpse_rot(surf, x, y, mold)
    spots = [(-7, 1), (0, 4), (6, 0), (10, 3), (3, 6), (-4, -1)][:1 + mold * 2]
    for fx, fy in spots:
        cx, cy = x + fx, y + 1 + fy
        _gold_in_wound(surf, cx, cy, 3, 66)                     # the face glows gold
        pygame.draw.circle(surf, (74, 26, 22), (cx - 1, cy - 1), 1)   # sunken eyes
        pygame.draw.circle(surf, (74, 26, 22), (cx + 1, cy - 1), 1)
        pygame.draw.line(surf, (44, 16, 14), (cx - 1, cy + 1), (cx + 1, cy + 1), 1)  # mouth


_CORPSE_CLAIM = {
    "toby": _corpse_claim_toby,
    "hettie": _corpse_claim_hettie,
    "old_townsman": _corpse_claim_old_townsman,
}


def draw_npc_corpse(surf, x, y, kind, seed=0, mold=0):
    """A local, put down. A horizontal slumped body over a dark blood
    pool -- read as a person on the floor, not a sprite standing. Tinted
    off the kind so the corpse still says who it was. Orientation is
    seeded so a row of bodies doesn't all face the same way.

    `mold` (0..3) is the world rot stage -- the fold claiming the dead.
    The body stays a recognisable body; the fold's INFECTION spreads over
    it as warm gold rot welling up from inside the flesh (never a black
    void): stage 1 a gold wound and sickly discolour, escalating through
    stage 3 where the Yellow Sign is branded into it. Named resisters are
    infected in the shape of their living mutation (`_CORPSE_CLAIM`); others
    get the generic gold rot. Where a character's compulsion should outlast
    them (`_CORPSE_ECHO`) that lays over the top -- their dying act still
    happening on the floor."""
    rng = random.Random(seed)
    body = _CORPSE_TINT.get(kind, (70, 64, 60))
    body_lo = tuple(int(c * 0.65) for c in body)
    skin = (172, 146, 126)
    head_left = rng.random() < 0.5
    hx = x - 13 if head_left else x + 13
    # Blood pool, drawn first so the body lies in it. Offset slightly
    # toward the head end (the wound that dropped them).
    pool = pygame.Surface((44, 26), pygame.SRCALPHA)
    pygame.draw.ellipse(pool, (84, 12, 14, 140), (0, 0, 44, 26))
    pygame.draw.ellipse(pool, (58, 6, 8, 185), (10, 7, 24, 12))
    surf.blit(pool, (x - 22 + (4 if head_left else -4), y - 2))
    # The body always reads as a BODY first -- a slumped flesh torso with an
    # outflung arm. mold 0 is a clean fresh kill. Then, once the fold claims
    # it (mold >= 1), INFECTION spreads OVER the body: gold rot welling up
    # from within the flesh, the Sign branded at full claim -- warm light, not
    # a black void. NAMED resisters get a wound shaped like their living
    # mutation (gold maw / peeled Sign-seam / gold faces); others get the
    # generic gold rot. The dying-compulsion echo lays over the top.
    pygame.draw.rect(surf, body, (x - 11, y - 2, 24, 9))
    pygame.draw.rect(surf, body_lo, (x - 11, y - 2, 24, 9), 1)
    pygame.draw.rect(surf, body_lo, (x - 3, y + 6, 9, 3))   # outflung arm
    if mold >= 1:
        infect = _CORPSE_CLAIM.get(kind, _corpse_infect_generic)
        infect(surf, x, y, body, body_lo, mold)
    # Head lolled to one end.
    pygame.draw.circle(surf, skin, (hx, y + 2), 4)
    pygame.draw.circle(surf, body_lo, (hx, y - 1), 4, 1)   # hair/hat smudge
    # A character's dying compulsion, still acting on the floor.
    echo = _CORPSE_ECHO.get(kind)
    if echo is not None:
        echo(surf, hx, y + 2, x, y, mold)
