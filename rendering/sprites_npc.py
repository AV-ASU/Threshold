"""The NPC sprite core: `draw_npc_sprite` and its per-view body/head helpers."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_common import (
    KING_UNFOLD, KING_UNFOLD_SCALE,
    _VP_HIDE, _VP_LO, _VP_HI, _VP_PALE, _VP_PALE_LO, _VP_PIT,
    _VP_GT, _VP_GHI, _VP_FLESH, _VP_FLESH_LO, _VP_MOUTH, _VP_TEETH,
    _VP_GOR, _VP_GOR_LO, _breath_lift,
)
from rendering.sprites_cultist import _draw_cultist
from rendering.sprites_king import _draw_king


# Tier-2 (2.5D) head config for the bare human NPC kinds: the front body draws
# as authored, then _npc_view_overlay re-orients the HEAD to the camera view.
# kind -> (head y-offset from y, radius, rear cap/hair colour).
# Every human NPC kind is now HANDCRAFTED per camera view (front / back /
# profile) inside draw_npc_sprite -- the old head-cap post-pass is retired,
# so this stays empty (kept only so _npc_view_overlay no-ops cleanly).
_NPC_HEAD = {}

# Darkwood / Fear&Hunger grim-human base, shared by the local NPC kinds. The
# locals cast NO contact shadow -- canon: "the player is the only thing here
# that's properly *here*" -- so these helpers draw none. A dim, COLD socket
# glint (not gold) keeps baseline townsfolk unclaimed by the fold.
_GLINT_COLD = (118, 122, 126)

# The living human locals breathe at idle (_breath_lift): a slow desynced 1px
# rise. Masked/hooded/inhuman kinds stay deathly still on purpose.
_BREATH_KINDS = {"townswoman", "old_townsman", "hettie", "toby",
                 "sheriff", "royce", "preacher", "clerk"}


def _grim_body(surf, x, y, base, w=14, h=19, ragged=True, grime=True, view="front"):
    """A near-black clothed torso: a hard shadow side, a thin rim light, a
    frayed hem and a grime smudge -- the gaunt, oppressed-villager silhouette.

    Handcrafted per camera view (no head-cap trick): 'back' trades the front
    grime smudge for a spine seam + shoulder yoke; the profiles narrow the
    torso, lead with the near shoulder and carry the rim light on the leading
    edge."""
    drk = tuple(int(c * 0.42) for c in base)
    lit = tuple(min(255, int(c * 1.22)) for c in base)
    top = tuple(int(c * 0.7) for c in base)
    if view in ("left", "right"):
        s = 1 if view == "right" else -1
        nw = w - 4                                          # the body turned edge-on
        pygame.draw.rect(surf, base, (x - nw // 2, y - 2, nw, h))
        pygame.draw.rect(surf, drk, (x - nw // 2 - s, y - 2, nw, h), 1)
        pygame.draw.rect(surf, top, (x - nw // 2, y - 2, nw, 2))            # collar
        pygame.draw.rect(surf, drk, (x - (nw // 2) * s, y - 2, 3, h))       # trailing back in shadow
        pygame.draw.rect(surf, lit, (x + (nw // 2 - 1) * s, y - 1, 2, h - 1))  # lead-edge rim
        sh = x + (nw // 2 - 1) if s > 0 else x - (nw // 2 + 1)
        pygame.draw.rect(surf, base, (sh, y - 2, 3, 6))                     # lead shoulder
        pygame.draw.rect(surf, lit, (sh + (2 if s > 0 else 0), y - 2, 1, 6))
        if ragged:
            for i in range(-nw // 2, nw // 2 - 1, 3):
                pygame.draw.rect(surf, C_BLACK, (x + i + 1, y + h - 3, 2, 3))
        return
    if view == "back":
        pygame.draw.rect(surf, base, (x - w // 2, y - 2, w, h))
        pygame.draw.rect(surf, drk, (x - w // 2 + (w * 3) // 5, y - 2, (w * 2) // 5, h))
        pygame.draw.rect(surf, top, (x - w // 2, y - 2, w, 3))             # shoulder yoke
        pygame.draw.rect(surf, lit, (x - w // 2, y - 1, 2, h - 1))         # rim
        pygame.draw.line(surf, drk, (x, y + 1), (x, y + h - 2), 1)          # spine seam
        if ragged:
            for i in range(-w // 2, w // 2 - 1, 3):
                pygame.draw.rect(surf, C_BLACK, (x + i + 1, y + h - 3, 2, 3))
        return
    pygame.draw.rect(surf, base, (x - w // 2, y - 2, w, h))
    pygame.draw.rect(surf, drk, (x - w // 2 + (w * 3) // 5, y - 2, (w * 2) // 5, h))
    pygame.draw.rect(surf, tuple(int(c * 0.7) for c in base), (x - w // 2, y - 2, w, 2))
    pygame.draw.rect(surf, lit, (x - w // 2, y - 1, 2, h - 1))
    if grime:
        pygame.draw.rect(surf, drk, (x - 3, y + h - 7, 5, 4))
        pygame.draw.rect(surf, drk, (x + 2, y + 2, 2, 5))
    if ragged:
        for i in range(-w // 2, w // 2 - 1, 3):
            pygame.draw.rect(surf, C_BLACK, (x + i + 1, y + h - 3, 2, 3))


def _gaunt_head(surf, x, y, skin, hy=-12, narrow=5, tall=15, blink=False,
                glint=_GLINT_COLD, mouth=True, view="front",
                brows=None, creases=False, corners=False, kid_eyes=False):
    """A sallow, gaunt head: a tall narrow skull, cheek gouges, and the
    tableau eye grammar at pixel scale (2026-07, replacing the old hard
    full-width brow-shadow band): a soft shadow SOCKET around each eye,
    a heavy lid line, an under-eye bag, and the deep dark pit with its dim
    glint inside (oversized void pits on blink). Returns the head-centre y
    so callers can hang hats/hair off it.

    Per-kind touches ride optional params, each pulled from that
    character's tableau: `brows` ("heavy" for Vane, "thin" for Sable),
    `creases=True` (Crane's sermon creases between the brows),
    `corners=True` (mouth corners pinned down), `kid_eyes=True` (Toby's
    bigger worried eyes with a warmer glint).

    `view` poses the head for the oblique camera: 'front' is the full
    face; 'back' is the bare skull with no face (the hair/hat cap goes on
    over it); the profiles carry the same socket treatment on the one
    leading eye, plus the jaw gouge and nose bump."""
    cy = y + hy
    sk_lo = tuple(int(c * 0.42) for c in skin)
    sock = tuple(int(c * 0.30) for c in skin)
    lid = tuple(int(c * 0.50) for c in skin)
    bag = tuple(int(c * 0.55) for c in skin)
    pygame.draw.ellipse(surf, skin, (x - narrow, cy - 7, narrow * 2, tall))
    pygame.draw.ellipse(surf, sk_lo, (x - narrow, cy - 7, narrow * 2, tall), 1)
    if view == "back":
        # The back of the skull -- no features; a faint nape shadow + a centre
        # hair-part hint. Callers' hair/hat (and _npc_view_overlay) cap it.
        pygame.draw.rect(surf, tuple(int(c * 0.3) for c in skin),
                         (x - narrow + 1, cy + 4, narrow * 2 - 2, 3))
        pygame.draw.line(surf, sk_lo, (x, cy - 5), (x, cy + 4), 1)
        return cy
    if view in ("left", "right"):
        s = 1 if view == "right" else -1                 # leading direction
        pygame.draw.line(surf, sk_lo, (x - 2 * s, cy + 1), (x + 2 * s, cy + 5), 2)  # jaw
        ex = x + s * 2                                   # the leading eye
        pygame.draw.line(surf, sk_lo, (x + (narrow - 1) * s, cy - 1),   # nose bump
                         (x + (narrow + 1) * s, cy + 1), 1)
        if blink:
            pygame.draw.rect(surf, (4, 3, 5), (x + s - 2, cy - 2, 4, 4))
        else:
            pygame.draw.ellipse(surf, sock, (ex - 2, cy - 3, 5, 6))     # the socket
            pygame.draw.line(surf, lid, (ex - 2, cy - 2), (ex + 2, cy - 2), 1)  # heavy lid
            pygame.draw.line(surf, bag, (ex - 1, cy + 3), (ex + 1, cy + 3), 1)  # the bag
            if kid_eyes:
                pygame.draw.rect(surf, (8, 6, 8), (ex - 1, cy - 1, 4, 3))
                gl = (150, 150, 140)
            else:
                pygame.draw.rect(surf, (8, 6, 8), (ex - 1, cy - 1, 3, 3))
                gl = glint
            try:
                surf.set_at((ex, cy), gl)
            except (IndexError, ValueError):
                pass
            if brows == "heavy":
                pygame.draw.line(surf, (58, 50, 38), (ex - 2, cy - 4), (ex + 3, cy - 4), 2)
            elif brows == "thin":
                pygame.draw.line(surf, (52, 45, 40), (ex - 2, cy - 4), (ex + 3, cy - 4), 1)
        if mouth:
            pygame.draw.line(surf, tuple(int(c * 0.4) for c in skin),
                             (x + s, cy + 7), (x + s * 3, cy + 7), 1)
        return cy
    pygame.draw.line(surf, sk_lo, (x - narrow + 1, cy + 1), (x - 2, cy + 5), 2)
    pygame.draw.line(surf, sk_lo, (x + narrow - 1, cy + 1), (x + 2, cy + 5), 2)
    if blink:
        pygame.draw.rect(surf, (4, 3, 5), (x - 4, cy - 2, 4, 4))
        pygame.draw.rect(surf, (4, 3, 5), (x + 1, cy - 2, 4, 4))
    else:
        pygame.draw.ellipse(surf, sock, (x - 5, cy - 3, 5, 6))          # the sockets
        pygame.draw.ellipse(surf, sock, (x + 1, cy - 3, 5, 6))
        pygame.draw.line(surf, lid, (x - 5, cy - 2), (x - 2, cy - 2), 1)  # heavy lids
        pygame.draw.line(surf, lid, (x + 2, cy - 2), (x + 5, cy - 2), 1)
        pygame.draw.line(surf, bag, (x - 4, cy + 3), (x - 2, cy + 3), 1)  # under-eye bags
        pygame.draw.line(surf, bag, (x + 2, cy + 3), (x + 4, cy + 3), 1)
        if kid_eyes:
            pygame.draw.rect(surf, (8, 6, 8), (x - 5, cy - 1, 4, 3))
            pygame.draw.rect(surf, (8, 6, 8), (x + 2, cy - 1, 4, 3))
            gl = (150, 150, 140)
        else:
            pygame.draw.rect(surf, (8, 6, 8), (x - 4, cy - 1, 3, 3))
            pygame.draw.rect(surf, (8, 6, 8), (x + 2, cy - 1, 3, 3))
            gl = glint
        try:
            surf.set_at((x - 3, cy), gl); surf.set_at((x + 3, cy), gl)
        except (IndexError, ValueError):
            pass
        if brows == "heavy":
            pygame.draw.line(surf, (58, 50, 38), (x - 5, cy - 4), (x - 1, cy - 4), 2)
            pygame.draw.line(surf, (58, 50, 38), (x + 1, cy - 4), (x + 5, cy - 4), 2)
        elif brows == "thin":
            pygame.draw.line(surf, (52, 45, 40), (x - 5, cy - 4), (x - 2, cy - 4), 1)
            pygame.draw.line(surf, (52, 45, 40), (x + 2, cy - 4), (x + 5, cy - 4), 1)
        if creases:
            pygame.draw.line(surf, sk_lo, (x - 1, cy - 5), (x - 1, cy - 3), 1)  # sermon creases
            pygame.draw.line(surf, sk_lo, (x + 1, cy - 5), (x + 1, cy - 3), 1)
    if mouth:
        pygame.draw.line(surf, tuple(int(c * 0.4) for c in skin),
                         (x - 2, cy + 7), (x + 2, cy + 7), 1)   # thin grim set
        if corners and not blink:
            try:
                surf.set_at((x - 3, cy + 8), sk_lo)             # pinned corners
                surf.set_at((x + 3, cy + 8), sk_lo)
            except (IndexError, ValueError):
                pass
    return cy


def _npc_view_overlay(surf, x, y, kind, view):
    """Tier-2 post-pass over a human NPC's front body: 'back' covers the face
    (and eyes) with the rear cap so you see the back of the head; 'left'/'right'
    sweep the cap over the far half for a profile. Only kinds in _NPC_HEAD are
    touched -- masked/hooded/non-human kinds are left alone."""
    cfg = _NPC_HEAD.get(kind)
    if cfg is None:
        return
    hy, r, cap = cfg
    cy = y + hy
    if view == "back":
        pygame.draw.circle(surf, cap, (x, cy), r)
        cap_lo = tuple(int(c * 0.7) for c in cap)
        pygame.draw.rect(surf, cap_lo, (x - 2, cy + r - 2, 4, 2))   # nape
    elif view in ("left", "right"):
        s = 1 if view == "right" else -1
        pygame.draw.circle(surf, cap, (x - (r - 2) * s, cy), r - 1)  # rear covers far eye


def _oldhat(surf, x, y, crown, crown_lo, crown_hi, brim, brim_lo, s=0):
    """A battered slouch hat: a dented, rounded crown with a band over a
    DROOPING OVAL brim (not stacked rectangles). `s` (-1/0/+1) shifts the
    crown + brim forward for a profile view."""
    cx = x + s * 2                                       # crown leans to the face in profile
    if s > 0:
        brim_rect = (x - 6, y - 21, 21, 6)
    elif s < 0:
        brim_rect = (x - 15, y - 21, 21, 6)
    else:
        brim_rect = (x - 11, y - 21, 22, 6)
    pygame.draw.ellipse(surf, brim, brim_rect)                       # oval brim
    pygame.draw.ellipse(surf, brim_lo, brim_rect, 1)
    pygame.draw.arc(surf, brim_lo, (brim_rect[0], brim_rect[1],      # drooping front lip
                    brim_rect[2], brim_rect[3] + 3), 3.4, 6.0, 1)
    cw, ch = 12, 13                                                  # rounded crown dome
    pygame.draw.ellipse(surf, crown, (cx - cw // 2, y - 28, cw, ch))
    pygame.draw.ellipse(surf, crown_lo, (cx - cw // 2, y - 28, cw, ch), 1)
    pygame.draw.line(surf, crown_lo, (cx - 3, y - 26), (cx + 3, y - 26), 1)   # battered dent
    pygame.draw.line(surf, crown_hi, (cx - 4, y - 25), (cx - 4, y - 21), 1)   # top-left sheen
    pygame.draw.rect(surf, crown_lo, (cx - cw // 2 + 1, y - 21, cw - 2, 2))   # hat band


def _cap(surf, x, y, crown, crown_lo, bill, s=0):
    """A soft feed cap: a rounded crown over the head + a forward bill that
    shadows the brow. `s` (-1/0/+1) juts the bill forward for a profile."""
    cx = x + s
    pygame.draw.ellipse(surf, crown, (cx - 7, y - 25, 14, 11))               # rounded crown
    pygame.draw.ellipse(surf, crown_lo, (cx - 7, y - 25, 14, 11), 1)
    pygame.draw.line(surf, crown_lo, (cx - 5, y - 23), (cx + 5, y - 23), 1)  # seam
    if s == 0:
        pygame.draw.ellipse(surf, bill, (x - 8, y - 16, 16, 4))             # bill faces viewer
        pygame.draw.ellipse(surf, crown_lo, (x - 8, y - 16, 16, 4), 1)
    else:
        bx = x + 1 if s > 0 else x - 12
        pygame.draw.ellipse(surf, bill, (bx, y - 16, 12, 3))               # bill juts forward
        pygame.draw.ellipse(surf, crown_lo, (bx, y - 16, 12, 3), 1)


def draw_npc_sprite(surf, x, y, kind, facing, blink=False, gaze=False,
                    birth=None, gait=None, threat=None, seed=0, curse=0.0,
                    view="front", to_player=None, lean=None, scale_mul=1.0,
                    pose=None, gape=0.0, apex_mask=None, lamp=0.0):
    """`blink=True` suppresses eye dots for NPC kinds that have human
    eyes (the named locals -- townswoman, toby, sheriff, royce,
    preacher, clerk, hettie, old_townsman). Used by Game.draw to make a
    single NPC's eyes vanish for a single frame -- a subliminal wrongness.
    `gaze=True` lights the watcher's eyes (sees the player). Watchers
    only.
    while the player stands still."""
    if kind == "_invisible":
        return
    if kind in _BREATH_KINDS:
        y -= _breath_lift(seed)
    if kind == "townswoman":
        # Mrs. Calder & the Brimley women. F&H-gaunt: a crushed-dark red dress
        # over a grubby apron, lank dark hair in a bun, a sallow hollow-eyed
        # face. The welcome never reaches her eyes; void pits on blink.
        # HANDCRAFTED per camera view -- no head-cap trick.
        dress = (96, 44, 52); skin = (150, 148, 122); sk_lo = (63, 62, 51)
        hair = (38, 28, 24); hair_lo = (30, 22, 20); apron = (118, 112, 100)
        hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 13))      # hair sweep
            pygame.draw.line(surf, hair_lo, (x, hcy - 4), (x, hcy + 6), 1)      # part
            pygame.draw.circle(surf, hair, (x, hcy - 7), 3)                     # bun
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.rect(surf, apron, (x - 4, y + 2, 8, 13))               # apron edge-on
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 8))       # hair over crown
            pygame.draw.rect(surf, hair, (x - HN if s < 0 else x + HN - 3, hcy - 6, 3, 9))  # back fall
            pygame.draw.circle(surf, hair, (x - 4 * s, hcy - 6), 3)            # bun at back
            pygame.draw.line(surf, hair_lo, (x + 2 * s, hcy - 1), (x + 2 * s, hcy + 4), 1)  # strand
        else:
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.rect(surf, apron, (x - 5, y + 2, 10, 13))              # grubby apron
            pygame.draw.rect(surf, (70, 60, 52), (x - 5, y + 12, 10, 3))       # hem stain
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, y - 21, HN * 2, 7))       # dark hair sweep
            pygame.draw.circle(surf, hair, (x, y - 20), 3)                     # bun
            pygame.draw.line(surf, hair_lo, (x - 5, y - 14), (x - 6, y - 9), 2)  # lank strand
    elif kind == "old_townsman":
        # The interchangeable old-timers (Old Pell, Garrick, the road pilgrims).
        # A dark brown coat, a battered hat low over a sallow gaunt face, a
        # kept-too-long ash-yellow beard, a cane. Void pits on blink.
        # HANDCRAFTED per camera view (front / back / profile) -- no head-cap.
        coat = (66, 52, 36); skin = (146, 142, 116); sk_lo = (61, 59, 48)
        beard = (150, 148, 128); cane = (74, 50, 26)
        hatc = (30, 22, 14); hatc_lo = (16, 11, 7); hatc_hi = (52, 40, 26)
        hatb = (22, 16, 10); hatb_lo = (12, 9, 5)
        hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, coat, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))      # back of skull
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            # long ash hair covers the back of the head down the nape --
            # clearly HAIR (darker than the skin), only a neck strip below
            hair_bk = (114, 112, 92)
            pygame.draw.rect(surf, hair_bk, (x - HN, hcy - 4, HN * 2, 11))
            pygame.draw.line(surf, (88, 86, 70), (x, hcy - 3), (x, hcy + 6), 1)   # part
            pygame.draw.line(surf, (88, 86, 70), (x - 3, hcy - 2), (x - 4, hcy + 5), 1)  # strands
            pygame.draw.line(surf, (88, 86, 70), (x + 3, hcy - 2), (x + 4, hcy + 5), 1)
            _oldhat(surf, x, y, hatc, hatc_lo, hatc_hi, hatb, hatb_lo)         # hat (rings the head)
            pygame.draw.line(surf, cane, (x + 9, y - 4), (x + 9, y + 14), 2)   # cane
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, coat, view=view)
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.polygon(surf, beard,                                  # thin wispy beard off the jaw
                                [(x, hcy + 5), (x + 5 * s, hcy + 5),
                                 (x + 3 * s, hcy + 9), (x + s, hcy + 8)])
            _oldhat(surf, x, y, hatc, hatc_lo, hatc_hi, hatb, hatb_lo, s=s)
            pygame.draw.line(surf, cane, (x + 7 * s, y - 2), (x + 7 * s, y + 15), 2)  # near-side cane
        else:
            _grim_body(surf, x, y, coat, view=view)
            # Break up the flat coat front: an open seam down the middle, two
            # lapels off the collar, and a row of dull buttons.
            pygame.draw.line(surf, (40, 32, 22), (x, y + 1), (x, y + 15), 1)   # coat opening
            pygame.draw.line(surf, (88, 70, 48), (x - 1, y + 1), (x - 1, y + 15), 1)  # lit edge
            pygame.draw.line(surf, (52, 41, 28), (x - 5, y - 1), (x - 1, y + 4), 2)  # left lapel
            pygame.draw.line(surf, (52, 41, 28), (x + 5, y - 1), (x + 1, y + 4), 2)  # right lapel
            for by in (y + 6, y + 10, y + 14):
                pygame.draw.circle(surf, (94, 78, 52), (x + 1, by), 1)        # buttons
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            # scraggly thin ash beard tapering to a point -- a frail old-timer,
            # NOT a strong jaw
            bpts = [(x - 4, y - 6), (x + 4, y - 6), (x + 2, y - 1),
                    (x, y + 4), (x - 2, y - 1)]
            pygame.draw.polygon(surf, beard, bpts)
            pygame.draw.polygon(surf, (96, 94, 80), bpts, 1)
            pygame.draw.line(surf, (96, 94, 80), (x - 1, y - 4), (x, y + 2), 1)  # wispy strand
            _oldhat(surf, x, y, hatc, hatc_lo, hatc_hi, hatb, hatb_lo)        # hat
            pygame.draw.line(surf, cane, (x + 9, y - 4), (x + 9, y + 14), 2)  # cane
    elif kind == "hettie":
        # Hettie -- keeps the shop open, sweeping a step that won't get
        # dirty. A plum housedress under a worn white apron (bib straps, a
        # mended patch, matching ui/tableau._draw_hettie), grey hair pinned
        # in a bun under a kerchief. The uncanny tell is carried over from
        # the old shopkeeper: small wire-rim spectacles whose lenses are
        # FILLED black -- you can never quite find her eyes behind them --
        # with a reflection-glint on the WRONG (same) side of both lenses,
        # impossible under a single overhead light. Her blink is the
        # glints going out, nothing else moving (the tableau's lens-dark).
        # HANDCRAFTED per camera view -- no head-cap trick.
        dress = (84, 50, 64); skin = (146, 142, 118); sk_lo = (61, 60, 49)
        hair = (120, 118, 122); kerch = (96, 56, 70); apron = (124, 120, 108)
        hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 12))      # grey hair
            pygame.draw.circle(surf, hair, (x, hcy - 6), 3)                     # bun
            pygame.draw.ellipse(surf, kerch, (x - HN, hcy - 9, HN * 2, 5))      # kerchief crown
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.rect(surf, apron, (x - 4, y + 1, 8, 14))               # apron edge-on
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 7))       # hair crown
            pygame.draw.rect(surf, hair, (x - HN if s < 0 else x + HN - 3, hcy - 6, 3, 8))  # back fall
            pygame.draw.circle(surf, hair, (x - 4 * s, hcy - 6), 3)            # bun at back
            pygame.draw.rect(surf, kerch, (x - HN, hcy - 9, HN * 2, 3))         # kerchief band
            pygame.draw.rect(surf, (168, 160, 140), (x + s * 2 - 2, hcy - 3, 6, 5), 1)  # wire rim
            pygame.draw.rect(surf, (12, 12, 16), (x + s * 2 - 1, hcy - 2, 4, 3))  # lead lens
            if not blink:                              # the glint holds its wrong side
                try:
                    surf.set_at((x + s * 2, hcy - 2), (244, 238, 220))
                except (IndexError, ValueError):
                    pass
        else:
            _grim_body(surf, x, y, dress, view=view)
            pygame.draw.rect(surf, apron, (x - 5, y + 1, 10, 14))              # worn apron
            pygame.draw.rect(surf, (88, 78, 70), (x - 5, y + 12, 10, 2))       # apron hem
            pygame.draw.line(surf, (100, 96, 86), (x - 4, y + 1), (x - 3, y - 2), 1)  # bib straps
            pygame.draw.line(surf, (100, 96, 86), (x + 4, y + 1), (x + 3, y - 2), 1)
            pygame.draw.rect(surf, (92, 82, 74), (x - 2, y + 7, 4, 4), 1)      # mended patch
            pygame.draw.circle(surf, (188, 182, 164), (x, y - 1), 1)           # bone button
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, y - 21, HN * 2, 7))       # grey hair
            pygame.draw.circle(surf, hair, (x, y - 20), 3)                     # bun
            pygame.draw.rect(surf, kerch, (x - HN, y - 21, HN * 2, 3))         # kerchief band
            # Wire-rim black-lens spectacles over the sockets -- the tell.
            pygame.draw.rect(surf, (168, 160, 140), (x - 6, y - 15, 6, 5), 1)  # wire rims
            pygame.draw.rect(surf, (168, 160, 140), (x, y - 15, 6, 5), 1)
            pygame.draw.rect(surf, (12, 12, 16), (x - 5, y - 14, 4, 3))        # filled lenses
            pygame.draw.rect(surf, (12, 12, 16), (x + 1, y - 14, 4, 3))
            pygame.draw.line(surf, (40, 40, 50), (x - 1, y - 13), (x + 1, y - 13), 1)  # bridge
            if not blink:                              # her blink: the glints go out
                try:
                    surf.set_at((x - 4, y - 14), (244, 238, 220))
                    surf.set_at((x + 2, y - 14), (244, 238, 220))  # both upper-LEFT, the wrong side
                except (IndexError, ValueError):
                    pass
    elif kind == "toby":
        # Toby. Desaturated yellow tunic with a crew-neck band; the
        # original bright primary made the kid read as cheerful, which
        # fights the use. The mop hangs low over the brow in ragged tips,
        # with the cowlick off the crown (ui/tableau._draw_toby); the
        # cheek dots used to be freckles, now they sit slightly low and
        # asymmetric so they read as old tear-streaks when you look twice.
        # HANDCRAFTED per camera view (child proportions) -- no head-cap.
        tunic = (150, 138, 64); skin = (154, 150, 124); sk_lo = (64, 63, 52)
        hair = (58, 40, 24); hcy = y - 8; HN, HT = 6, 14
        if view == "back":
            _grim_body(surf, x, y + 2, tunic, w=13, h=14, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 10))      # mop from behind
            pygame.draw.line(surf, (40, 28, 16), (x, hcy - 3), (x, hcy + 3), 1)  # cowlick
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y + 2, tunic, w=13, h=14, view=view)
            _gaunt_head(surf, x, y, skin, hy=-8, narrow=HN, tall=HT, blink=blink,
                        kid_eyes=True, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 6))       # mop over crown
            pygame.draw.rect(surf, hair, (x - HN if s < 0 else x + HN - 3, hcy - 7, 3, 5))  # back fall
            pygame.draw.line(surf, (40, 28, 16), (x + s, hcy - 8), (x + 3 * s, hcy - 11), 2)  # cowlick
            pygame.draw.line(surf, (122, 118, 98), (x + 3 * s, hcy + 2), (x + 3 * s, hcy + 5), 1)  # tear
        else:
            _grim_body(surf, x, y + 2, tunic, w=13, h=14, view=view)
            pygame.draw.arc(surf, (104, 95, 42), (x - 4, y - 1, 8, 5), 3.3, 6.1, 2)  # crew-neck band
            _gaunt_head(surf, x, y, skin, hy=-8, narrow=HN, tall=HT, blink=blink,
                        kid_eyes=True, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 6))       # hair mop
            pygame.draw.rect(surf, hair, (x - 5, hcy - 3, 10, 2))              # low fringe over brow
            for fx2 in (x - 5, x, x + 5):                                      # ragged fringe tips
                pygame.draw.rect(surf, hair, (fx2, hcy - 1, 1, 1))
            pygame.draw.line(surf, (40, 28, 16), (x + 2, hcy - 8), (x + 4, hcy - 11), 2)  # cowlick
            pygame.draw.line(surf, (122, 118, 98), (x - 4, hcy + 2), (x - 4, hcy + 5), 1)  # tear-track
            pygame.draw.line(surf, (118, 112, 94), (x + 4, hcy + 3), (x + 4, hcy + 6), 1)
    elif kind == "sheriff":
        # Sheriff Hollis Vane -- a local, born here, broken. A tan duty
        # shirt, a brown brimmed hat (not a city cop's peaked cap), a tin
        # star going dull on the chest. Heavy tableau brows over sunken
        # sockets under the brim; stubble along the jaw; a man who hasn't
        # slept since the road stopped going anywhere. Void blink.
        # HANDCRAFTED per camera view -- no head-cap trick.
        shirt = (104, 90, 62); skin = (148, 142, 116); sk_lo = (62, 60, 49)
        hair = (74, 62, 44); hcy = y - 12; HN, HT = 6, 16
        hc = (60, 46, 32); hc_lo = (34, 26, 18); hc_hi = (92, 74, 50)
        hb = (48, 36, 24); hb_lo = (28, 21, 14)

        shirt_drk = (44, 38, 26)

        def _star(sx):
            # a real five-point tin star (the tableau's), not a blob
            pts = []
            for k in range(10):
                ang = -math.pi / 2 + k * math.pi / 5
                rr = 4 if k % 2 == 0 else 2
                pts.append((sx + rr * math.cos(ang), y + 2 + rr * math.sin(ang)))
            pygame.draw.polygon(surf, (150, 140, 84), pts)
            pygame.draw.polygon(surf, (96, 88, 50), pts, 1)

        def _delts():                                                         # broad deltoid shoulders
            pygame.draw.ellipse(surf, shirt, (x - 12, y - 2, 7, 8))
            pygame.draw.ellipse(surf, shirt, (x + 5, y - 2, 7, 8))
            pygame.draw.ellipse(surf, shirt_drk, (x - 12, y - 2, 7, 8), 1)
            pygame.draw.ellipse(surf, shirt_drk, (x + 5, y - 2, 7, 8), 1)
            pygame.draw.polygon(surf, shirt_drk, [(x - 9, y + 8), (x - 9, y + 17), (x - 6, y + 17)])
            pygame.draw.polygon(surf, shirt_drk, [(x + 9, y + 8), (x + 9, y + 17), (x + 6, y + 17)])
        if view == "back":
            _grim_body(surf, x, y, shirt, w=18, view=view)                    # GigaChad frame
            _delts()
            pygame.draw.rect(surf, (62, 54, 38), (x - 9, y + 10, 18, 4))       # belt
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.rect(surf, hair, (x - HN, hcy, HN * 2, 4))             # hair at nape
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo)
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, shirt, w=18, view=view)
            pygame.draw.ellipse(surf, shirt, (x - 4, y - 2, 9, 9))             # heavy shoulder/chest
            pygame.draw.ellipse(surf, shirt_drk, (x - 4, y - 2, 9, 9), 1)
            bulge = (x + 1, y + 2, 6, 7) if s > 0 else (x - 7, y + 2, 6, 7)
            pygame.draw.ellipse(surf, shirt, bulge)                            # forward chest bulge
            pygame.draw.rect(surf, (62, 54, 38), (x - 7, y + 10, 14, 4))       # belt
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink,
                        brows="heavy", view=view)
            # strong forward GigaChad jaw in profile -- the chin JUTS forward
            pygame.draw.polygon(surf, skin, [(x - 3 * s, y - 10), (x + 6 * s, y - 9),
                                             (x + 8 * s, y - 6), (x + 5 * s, y - 3),
                                             (x - 2 * s, y - 4)])
            pygame.draw.line(surf, sk_lo, (x + 6 * s, y - 9), (x + 8 * s, y - 6), 1)  # jaw front
            pygame.draw.line(surf, sk_lo, (x + 8 * s, y - 6), (x + 5 * s, y - 3), 1)  # jutting chin
            pygame.draw.circle(surf, (96, 92, 76), (x + 4 * s, y - 5), 1)      # stubble jaw
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo, s=s)
            _star(x + 3 * s)                                                   # star edge-on
        else:
            _grim_body(surf, x, y, shirt, w=18, view=view)
            _delts()
            pygame.draw.line(surf, shirt_drk, (x, y - 1), (x, y + 9), 1)       # shirt placket
            pygame.draw.rect(surf, (32, 28, 22), (x - 1, y - 2, 3, 2))         # open collar notch
            pygame.draw.rect(surf, (74, 64, 44), (x - 7, y + 1, 5, 4), 1)      # L breast pocket
            pygame.draw.rect(surf, (74, 64, 44), (x + 3, y + 1, 5, 4), 1)      # R breast pocket
            pygame.draw.rect(surf, shirt_drk, (x - 7, y + 1, 5, 2))            # pocket flaps
            pygame.draw.rect(surf, shirt_drk, (x + 3, y + 1, 5, 2))
            pygame.draw.rect(surf, (62, 54, 38), (x - 9, y + 10, 18, 4))       # belt
            pygame.draw.rect(surf, (96, 84, 52), (x - 2, y + 10, 4, 4), 1)     # buckle
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink,
                        brows="heavy", view=view)
            # heavy GigaChad jaw -- square the gaunt skull off into a broad,
            # cleft-chinned jaw
            jpts = [(x - 6, y - 10), (x + 6, y - 10), (x + 5, y - 5),
                    (x + 2, y - 2), (x - 2, y - 2), (x - 5, y - 5)]
            pygame.draw.polygon(surf, skin, jpts)
            pygame.draw.line(surf, sk_lo, (x - 6, y - 10), (x - 5, y - 5), 1)  # jaw angle L
            pygame.draw.line(surf, sk_lo, (x + 6, y - 10), (x + 5, y - 5), 1)  # jaw angle R
            pygame.draw.line(surf, sk_lo, (x, y - 4), (x, y - 2), 1)           # chin cleft
            pygame.draw.line(surf, sk_lo, (x - 2, y - 6), (x + 2, y - 6), 1)   # set mouth
            for sx2 in (-3, 1):
                pygame.draw.circle(surf, (96, 92, 76), (x + sx2, y - 4), 1)    # stubble on the jaw
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo)
            _star(x - 5)                                                       # star on the chest
    elif kind == "royce":
        # Royce -- drives the river road to the county line and gets handed
        # back into Brimley every time. A working man, no fisherman: a
        # quilted flannel jacket over a pale tee, a faded feed cap, three
        # days of stubble. Cap brim shadows the tired eyes; void blink.
        # HANDCRAFTED per camera view -- no head-cap trick.
        flannel = (84, 56, 46); skin = (146, 140, 114); sk_lo = (61, 59, 48)
        cap_c = (104, 44, 38); cap_lo = (62, 26, 22); cap_bill = (78, 32, 28)
        hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, flannel, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            # hair fills the gap between cap and collar -- only a thin strip
            # of neck shows, so the back never reads as a blank face
            pygame.draw.rect(surf, (60, 46, 34), (x - HN, hcy - 3, HN * 2, 9))
            pygame.draw.line(surf, (42, 32, 24), (x - 2, hcy - 1), (x - 2, hcy + 4), 1)
            pygame.draw.line(surf, (42, 32, 24), (x + 2, hcy - 1), (x + 2, hcy + 4), 1)
            _cap(surf, x, y, cap_c, cap_lo, cap_bill)
            pygame.draw.rect(surf, cap_lo, (x - 4, y - 23, 8, 2))             # adjuster strap
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, flannel, view=view)
            pygame.draw.rect(surf, (120, 116, 108), (x - 2, y - 2, 5, 7))      # tee collar edge
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.circle(surf, (104, 98, 82), (x + 3 * s, hcy + 6), 1)   # stubble
            _cap(surf, x, y, cap_c, cap_lo, cap_bill, s=s)
        else:
            _grim_body(surf, x, y, flannel, view=view)
            pygame.draw.rect(surf, (120, 116, 108), (x - 3, y - 2, 6, 7))      # tee at collar
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            for sx2 in (-3, 1):
                pygame.draw.circle(surf, (104, 98, 82), (x + sx2, y - 5), 1)   # stubble
            _cap(surf, x, y, cap_c, cap_lo, cap_bill)
    elif kind == "preacher":
        # Reverend Asa Crane -- gaunt, grey, the one who named them from
        # the pulpit. A black cassock with its button seam, a white
        # clerical collar (notched) at the throat, thin grey hair, deep
        # solemn hollows. He reads as already half a ghost. A small pale
        # cross hung centred on its cord (ui/tableau._draw_crane). Void
        # blink. HANDCRAFTED per camera view -- no head-cap trick.
        cassock = (28, 26, 32); skin = (156, 158, 140); sk_lo = (65, 66, 58)
        hair = (120, 120, 126); cross = (150, 144, 120); hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, cassock, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 8))       # thin grey hair
            pygame.draw.ellipse(surf, skin, (x - 3, hcy - 7, 6, 5))            # balding crown peeks
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, cassock, view=view)
            pygame.draw.rect(surf, (210, 210, 214), (x - 2, y - 2, 5, 3))      # collar edge
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 6))       # thin hair crown
            pygame.draw.rect(surf, hair, (x - HN if s < 0 else x + HN - 3, hcy - 6, 3, 6))  # back fall
            pygame.draw.line(surf, (96, 92, 78), (x, y - 1), (x + 2 * s, y + 5), 1)  # the cord
            pygame.draw.line(surf, cross, (x + 2 * s, y + 5), (x + 2 * s, y + 10), 1)  # cross edge-on
            pygame.draw.line(surf, cross, (x + s, y + 7), (x + 3 * s, y + 7), 1)
        else:
            _grim_body(surf, x, y, cassock, view=view)
            pygame.draw.line(surf, (16, 15, 19), (x, y + 1), (x, y + 15), 1)   # cassock button seam
            for by in (y + 12, y + 15):
                pygame.draw.circle(surf, (52, 49, 58), (x, by), 1)             # buttons below the cross
            pygame.draw.rect(surf, (210, 210, 214), (x - 3, y - 2, 6, 3))      # clerical collar
            pygame.draw.rect(surf, cassock, (x - 1, y - 2, 2, 3))              # the collar notch
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink,
                        creases=True, corners=True, view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, y - 21, HN * 2, 6))       # thin grey hair
            pygame.draw.ellipse(surf, skin, (x - 3, y - 21, 6, 4))            # high balding brow
            pygame.draw.line(surf, (96, 92, 78), (x - 3, y + 1), (x, y + 5), 1)  # the cord
            pygame.draw.line(surf, (96, 92, 78), (x + 3, y + 1), (x, y + 5), 1)
            pygame.draw.rect(surf, cross, (x - 1, y + 5, 2, 7))                # the pale cross, centred
            pygame.draw.rect(surf, cross, (x - 3, y + 7, 6, 2))
    elif kind == "clerk":
        # Mr. Sable, the Lodge Clerk -- the smiling host who never ages.
        # Matched to his tableau (ui/tableau._draw_sable): a dark coat
        # hanging OPEN around a wide white shirt-front, a short red tie,
        # neat side-parted dark hair going grey at the temples. The tell:
        # a level smile that never reaches the eyes, and on blink the
        # smile stays while the eyes drop to voids -- the host's face
        # running without him in it.
        # HANDCRAFTED per camera view -- no head-cap trick.
        vest = (40, 36, 44); skin = (160, 156, 142); sk_lo = (67, 65, 59)
        hair = (30, 26, 24); part = (54, 48, 44); grey = (110, 102, 92)
        hcy = y - 12; HN, HT = 6, 16
        if view == "back":
            _grim_body(surf, x, y, vest, view=view)
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 9))       # neat hair
            pygame.draw.line(surf, part, (x + 2, hcy - 7), (x + 2, hcy + 1), 1)  # part
            pygame.draw.line(surf, grey, (x - HN + 1, hcy - 3), (x - HN + 1, hcy), 1)  # grey temples
            pygame.draw.line(surf, grey, (x + HN - 2, hcy - 3), (x + HN - 2, hcy), 1)
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, vest, view=view)
            pygame.draw.rect(surf, (198, 196, 194), (x - 2, y - 2, 4, 16))     # shirt-front edge
            pygame.draw.line(surf, (120, 30, 36), (x + s, y - 2), (x + s, y + 4), 1)  # tie
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink,
                        mouth=False, brows="thin", view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, hcy - 8, HN * 2, 7))       # neat hair crown
            bfx = (x - HN) if s < 0 else (x + HN - 3)
            pygame.draw.rect(surf, hair, (bfx, hcy - 6, 3, 7))                  # back fall
            pygame.draw.line(surf, grey, (bfx + 1, hcy - 4), (bfx + 1, hcy), 1)  # grey temple
            pygame.draw.line(surf, (132, 98, 98), (x + s, hcy + 6), (x + 3 * s, hcy + 6), 1)  # smile
        else:
            _grim_body(surf, x, y, vest, view=view)
            # The shirt is a tapering V under the coat, not a full white
            # column (2026-07 playtest: head + wide shirt merged into one
            # pale blob behind the desk; the face must own the white).
            pygame.draw.polygon(surf, (188, 186, 184), [
                (x - 4, y - 2), (x + 4, y - 2), (x + 2, y + 8), (x - 2, y + 8)])
            pygame.draw.line(surf, (22, 20, 25), (x - 4, y - 2), (x - 2, y + 8), 2)  # coat lapels
            pygame.draw.line(surf, (22, 20, 25), (x + 4, y - 2), (x + 2, y + 8), 2)
            pygame.draw.rect(surf, (120, 30, 36), (x - 1, y - 1, 2, 6))        # short red tie
            pygame.draw.rect(surf, (94, 22, 28), (x - 1, y - 1, 2, 2))         # the knot
            # the host's watch chain, a gold glint across the vest
            pygame.draw.line(surf, (188, 160, 92), (x + 2, y + 9), (x + 5, y + 7), 1)
            _gaunt_head(surf, x, y, skin, narrow=HN, tall=HT, blink=blink,
                        mouth=False, brows="thin", view=view)
            pygame.draw.ellipse(surf, hair, (x - HN, y - 21, HN * 2, 7))       # neat dark hair
            pygame.draw.line(surf, part, (x + 1, y - 20), (x + 1, y - 16), 1)  # the part
            pygame.draw.line(surf, grey, (x - HN + 1, y - 16), (x - HN + 1, y - 13), 1)  # grey temples
            pygame.draw.line(surf, grey, (x + HN - 2, y - 16), (x + HN - 2, y - 13), 1)
            # the level smile that never reaches the eyes (the sides had
            # it; the front -- the desk view -- was blank-mouthed)
            pygame.draw.line(surf, (132, 98, 98), (x - 2, y - 9), (x + 2, y - 9), 1)
            pygame.draw.line(surf, part, (x + 2, y - 20), (x + 2, y - 15), 1)  # side part
            pygame.draw.line(surf, grey, (x - HN + 1, y - 16), (x - HN + 1, y - 15), 1)  # grey temples
            pygame.draw.line(surf, grey, (x + HN - 2, y - 16), (x + HN - 2, y - 15), 1)
            pygame.draw.line(surf, (132, 98, 98), (x - 3, y - 5), (x + 3, y - 5), 1)  # host smile
    elif kind == "sheriff_hollow":
        # Sheriff Vane, gone hollow -- the stage-3 unique threat. The
        # lawman's shape is still there (the sheriff's broad build, tan
        # shirt, brimmed hat) but the man isn't: his FACE HAS COLLAPSED
        # into a deep dark void -- a head-shaped cavity that sinks through
        # nested rings to true black -- and two dim gold eyes blink in and
        # out of existence somewhere down inside it. The tin star has
        # curdled into a small Yellow Sign. He doesn't stop.
        # HANDCRAFTED per camera view (front / back / profile): the void
        # face shows on front/profile; the back is a faceless hatted skull.
        # Jaundice is baked into the PALETTE (no bounding-box wash).
        t = pygame.time.get_ticks() / 1000.0
        shirt = (84, 78, 50); shirt_drk = (46, 42, 26)
        skin = (140, 142, 92); sk_lo = (60, 62, 38)    # sallow nape (back of head)
        hair = (62, 56, 36); hcy = y - 12; HN, HT = 6, 16
        rim = (74, 76, 48); rim_lo = (40, 42, 26)      # dim skull rim around the void
        VOID_RINGS = [(30, 30, 22), (17, 17, 13), (7, 7, 9), (2, 2, 4)]  # sinks to black
        hc = (54, 42, 28); hc_lo = (30, 23, 15); hc_hi = (84, 68, 44)
        hb = (42, 32, 21); hb_lo = (24, 18, 12)

        def _aura():
            # Soft sick halo leaking around the collapsed head -- concentric
            # fading rings, so it blends to nothing at the edge (no rectangle).
            halo = pygame.Surface((26, 26), pygame.SRCALPHA)
            for rr, aa in ((12, 14), (9, 24), (6, 36)):
                pygame.draw.circle(halo, (150, 132, 44, aa), (13, 13), rr)
            surf.blit(halo, (x - 13, hcy - 11))

        def _void_head(s=0):
            # The face collapsed inward: a dim head-rim around a cavity that
            # sinks ring by ring to true black. For a profile the cavity
            # shifts toward the lead side, so the back of the skull (rim)
            # trails behind -- reads as a head turned.
            pygame.draw.ellipse(surf, rim, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, rim_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            ox = s * 2
            for i, col in enumerate(VOID_RINGS):
                pygame.draw.ellipse(surf, col, (x - HN + 1 + i + ox, hcy - 6 + i,
                                                HN * 2 - 2 - 2 * i, HT - 2 - 2 * i))

        def _void_eyes(s):
            # The gold eyes pop up all over the void like the WATCHER's
            # mass-of-eyes: a seeded CONSTELLATION, each winking on its own
            # staggered phase (faint halo + bright dot, same colour as the
            # 'watcher' kind). Placed parametrically INSIDE the void ellipse
            # so every eye fits the cavity -- including the narrower,
            # lead-shifted profile void.
            cx = x + s * 2
            cy = hcy + 1
            ax = 2.0 if s else 3.2                # tighter in profile so they fit
            ay = 4.4 if s else 4.6
            erng = random.Random((int(x) * 7 + 5) & 0xffff)
            for i in range(7):
                ang = erng.uniform(0, math.tau)
                rad = math.sqrt(erng.uniform(0, 1))    # uniform over the ellipse
                ex = int(cx + math.cos(ang) * ax * rad)
                ey = int(cy + math.sin(ang) * ay * rad)
                bl = 0.5 + 0.5 * math.sin(t * 1.6 + i * 1.5 + x)
                if bl < 0.42:
                    continue                          # winked out (sparser now)
                gv = int(70 + 48 * bl)
                pygame.draw.circle(surf, (54, 46, 20), (ex, ey), 2)         # faint dark socket
                # The bright pupil sits toward the lead side, so in profile the
                # gaze reads as looking the way the body faces (centred front).
                pygame.draw.circle(surf, (gv, int(gv * 0.8), 28), (ex + s, ey), 1)

        def _delts():                                                     # broad deltoid shoulders
            pygame.draw.ellipse(surf, shirt, (x - 12, y - 2, 7, 8))
            pygame.draw.ellipse(surf, shirt, (x + 5, y - 2, 7, 8))
            pygame.draw.ellipse(surf, shirt_drk, (x - 12, y - 2, 7, 8), 1)
            pygame.draw.ellipse(surf, shirt_drk, (x + 5, y - 2, 7, 8), 1)
            pygame.draw.polygon(surf, shirt_drk, [(x - 9, y + 8), (x - 9, y + 17), (x - 6, y + 17)])
            pygame.draw.polygon(surf, shirt_drk, [(x + 9, y + 8), (x + 9, y + 17), (x + 6, y + 17)])

        def _sign(sx):                                                    # tin star, curdled to the Sign
            pygame.draw.line(surf, (210, 188, 70), (sx, y), (sx, y + 4), 1)
            pygame.draw.line(surf, (210, 188, 70), (sx, y + 1), (sx - 2, y), 1)
            pygame.draw.line(surf, (210, 188, 70), (sx, y + 1), (sx + 2, y), 1)
        if view == "back":
            _grim_body(surf, x, y, shirt, w=18, view=view)
            _delts()
            pygame.draw.rect(surf, (54, 48, 32), (x - 9, y + 10, 18, 4))   # belt
            pygame.draw.ellipse(surf, skin, (x - HN, hcy - 7, HN * 2, HT))
            pygame.draw.ellipse(surf, sk_lo, (x - HN, hcy - 7, HN * 2, HT), 1)
            pygame.draw.rect(surf, hair, (x - HN, hcy, HN * 2, 4))         # hair at nape
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo)
        elif view in ("left", "right"):
            s = 1 if view == "right" else -1
            _grim_body(surf, x, y, shirt, w=18, view=view)
            pygame.draw.ellipse(surf, shirt, (x - 4, y - 2, 9, 9))         # heavy shoulder/chest
            pygame.draw.ellipse(surf, shirt_drk, (x - 4, y - 2, 9, 9), 1)
            bulge = (x + 1, y + 2, 6, 7) if s > 0 else (x - 7, y + 2, 6, 7)
            pygame.draw.ellipse(surf, shirt, bulge)                        # forward chest bulge
            pygame.draw.rect(surf, (54, 48, 32), (x - 7, y + 10, 14, 4))   # belt
            _aura()
            _void_head(s)                                                  # collapsed-face cavity (turned)
            _void_eyes(s)                                                  # eyes pop up all over the void
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo, s=s)
            _sign(x + 3 * s)                                               # Sign edge-on
        else:
            _grim_body(surf, x, y, shirt, w=18, view=view)
            _delts()
            pygame.draw.line(surf, shirt_drk, (x, y - 1), (x, y + 9), 1)   # placket
            pygame.draw.rect(surf, (54, 48, 32), (x - 9, y + 10, 18, 4))   # belt
            _aura()
            _void_head()                                                   # the face, collapsed to a cavity
            _void_eyes(0)                                                  # gold eyes pop up all over the void
            _oldhat(surf, x, y, hc, hc_lo, hc_hi, hb, hb_lo)
            _sign(x - 5)                                                   # Sign on the chest
    elif kind == "yellow_king":
        # The King in Yellow -- a floating tear-in-space: a churning clot of
        # gold light packed with the cult's fused faces, arms reaching out to
        # grasp, trailing a wake of glowing soul-orbs. The full drawing, rift
        # birth, and motion live in _draw_king. `birth` (0..1) and `gait` come
        # from the live NPC; when absent (a preview) they loop off the clock so
        # the eruption still shows.
        import pygame as _pg
        t = _pg.time.get_ticks() / 1000.0
        if birth is None:
            cyc = t % 7.0
            b = min(1.0, cyc / 1.6)            # erupt over ~1.6s
            g = max(0.0, cyc - 1.6) * 7.0      # then drift the rest
        else:
            b = birth
            g = gait if gait is not None else t * 7.0
        if KING_UNFOLD:
            from rendering.king_unfold import draw_king_unfold
            tp = to_player if to_player is not None else (0.0, 1.0)
            ln = lean if lean is not None else (0.0, 0.0)
            draw_king_unfold(surf, x, y, t,
                             threat=(0.5 if threat is None else threat),
                             scale=KING_UNFOLD_SCALE * scale_mul,
                             to_player=tp, birth=b, lean=ln, gape=gape)
        else:
            _draw_king(surf, x, y, facing, t, b, g, threat)
    elif kind == "cultist":
        # Stitched animal-hide coat + a carved wooden mask (one of six,
        # chosen per individual by `seed`). Directional: mask front/side,
        # bare fur hood + Sign from behind so you can read its gaze. See
        # _draw_cultist + the mask helpers at the top of this module.
        t = pygame.time.get_ticks() / 1000.0
        _draw_cultist(surf, x, y, facing, seed, t, pose)
    elif kind == "amalgam":
        # A Watcher-family shadow assembled from parts, each emerging from
        # its own cut (rendering/amalgam.py; DESIGN.md §1). `seed` picks the
        # assembly, `birth` drives the staggered build-out on manifest, and
        # `gait` carries the gaze-dispel fraction (the peeling) -- both are
        # presentation-only attrs the watcher ticks maintain.
        from rendering.amalgam import draw_amalgam_sprite
        # THE APEX wears the Mask and its host's deal plus 2-3 parts.
        # `apex_mask` is stamped by Game._tick_apex on the host it created; an
        # ordinary unit passes None and its draw is untouched.
        draw_amalgam_sprite(surf, x, y, seed=seed, gaze=gaze,
                            birth=birth, dispel=gait, mask=apex_mask,
                            lamp=lamp)
    else:
        # generic placeholder
        pygame.draw.rect(surf, (200, 200, 200), (x - 8, y - 8, 16, 16))
    # Tier-2: re-orient the head to the camera view (no-op for front + for any
    # kind not in _NPC_HEAD; flat top-down never passes a view).
    if view != "front":
        _npc_view_overlay(surf, x, y, kind, view)
