"""The player sprite, the facing->view helper, and small shared FX."""
import math
import random
import pygame
from constants import C_BLACK
from rendering.sprites_cultist import _darkwood_pass


def view_from_facing(fx, fy, yaw):
    """Camera-relative sprite view -- 'front' / 'back' / 'left' / 'right' -- for
    an actor facing world (fx, fy) under a camera yawed by `yaw` (Tier-2 / 2.5D
    sprites). The viewer sits below the screen, so an actor facing toward
    screen-bottom shows its FRONT, screen-top its BACK, the sides a profile.
    Four equal 90deg quadrants. At pitch 0 the live game never asks for a view
    (stays flat/front), so this only drives the oblique look mode."""
    th = math.degrees(math.atan2(fy, fx) - yaw)
    th = (th + 180) % 360 - 180
    if 45 <= th < 135:
        return "front"
    if -135 <= th < -45:
        return "back"
    if -45 <= th < 45:
        return "right"
    return "left"


def _blend_px(lay, x, y, col, a):
    """Alpha-blend `col` at alpha `a` (0..255) onto one pixel of an SRCALPHA
    layer -- soft glow/smoke specks without a per-pixel Surface."""
    if a <= 0 or not (0 <= x < lay.get_width() and 0 <= y < lay.get_height()):
        return
    bg = lay.get_at((x, y))
    f = a / 255.0
    lay.set_at((x, y), (int(bg[0] * (1 - f) + col[0] * f),
                        int(bg[1] * (1 - f) + col[1] * f),
                        int(bg[2] * (1 - f) + col[2] * f), 255))


def _cig_fx(lay, t, ex, ey, ember=True):
    """A breathing warm ember at (ex,ey) + an animated curl of smoke rising
    off it. The ember is the one point of colour on the monochrome PI; pass
    ember=False (the back view) for smoke only."""
    pulse = 0.55 + 0.45 * math.sin(t * 4.5)
    if ember:
        lay.set_at((ex, ey), (int(150 + 95 * pulse), int(72 + 52 * pulse),
                              int(30 + 20 * pulse)))
        glow = (int(118 + 60 * pulse), int(56 + 34 * pulse), 26)
        for gx, gy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            _blend_px(lay, ex + gx, ey + gy, glow, int(110 * pulse))
    for k in range(7):
        yy = int(round(ey - 1 - k * 2.0 - ((t * 5.0) % 2.0)))
        xx = int(round(ex + 1 + math.sin(t * 2.0 + k * 0.7) * (1.0 + k * 0.22)))
        _blend_px(lay, xx, yy, (120, 120, 124), max(0, 150 - k * 22))


def draw_player_sprite(surf, x, y, facing, walk_phase=0, armor=None,
                        prone=False, view="front"):
    """THRESHOLD: the private investigator, 1994 -- a worn, belted TAN TRENCH
    COAT (collar up, wide lapels over a pale shirt + dark tie, double-breast
    buttons, slash pockets, a back vent) over dark trousers and boots, a brown
    FEDORA, and a lit cigarette (glowing ember + animated smoke). Built at full
    detail front / back / both profiles, then brushed with the game's Darkwood
    grime so he sits in the cast. He keeps a LIVING gaze (a glint in the
    socket) -- the one unclaimed soul. A faint ground shadow roots him."""
    COAT = (140, 122, 90); CO_LO = (84, 72, 50); CO_HI = (168, 150, 114)
    HAT = (82, 62, 42); HAT_LO = (50, 38, 26)
    SKIN = (164, 136, 112); SK_LO = (90, 74, 58)
    SHIRT = (178, 172, 158); TIE = (70, 54, 48); INK = (14, 13, 13)
    PANTS = (40, 40, 38); BOOT = (26, 22, 20); GLINT = (220, 216, 202)
    if prone:
        bx = x - 12; by = y - 2
        pygame.draw.rect(surf, (84, 78, 62), (bx, by, 24, 9))            # blanket
        pygame.draw.rect(surf, (52, 48, 38), (bx, by, 24, 9), 1)
        pygame.draw.circle(surf, SKIN, (bx + 22, by + 4), 4)
        pygame.draw.ellipse(surf, HAT, (bx + 17, by - 1, 10, 4))         # fedora at rest
        pygame.draw.line(surf, INK, (bx + 21, by + 4), (bx + 24, by + 4), 1)
        pygame.draw.rect(surf, BOOT, (bx, by + 5, 4, 3))
        return
    shadow = pygame.Surface((24, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 95), (0, 0, 24, 8))
    surf.blit(shadow, (int(x) - 12, int(y) + 16))
    LX, LY = 22, 34
    lay = pygame.Surface((44, 60), pygame.SRCALPHA)
    cx, cy = LX, LY
    t = pygame.time.get_ticks() / 1000.0
    lo = int(math.sin(walk_phase) * 2)
    hemsway = int(abs(math.sin(walk_phase)))
    sh_y = cy - 11
    hcy = cy - 14
    by = cy + 1                                      # belt line
    prof = view in ("left", "right")
    s = 1 if view == "right" else -1
    # ---- legs + boots (mostly hidden by the long coat) ----
    if prof:
        pygame.draw.rect(lay, PANTS, (cx - 3, cy + 9, 6, 6))
        pygame.draw.rect(lay, BOOT, (cx - 2 + s * 3, cy + 14, 5, 5 + max(0, -lo)))
        pygame.draw.rect(lay, BOOT, (cx - 3 - s * 2, cy + 14, 5, 5 + max(0, lo)))
    else:
        pygame.draw.rect(lay, PANTS, (cx - 5, cy + 9, 10, 6))
        pygame.draw.rect(lay, BOOT, (cx - 5, cy + 14, 4, 5 + max(0, -lo)))
        pygame.draw.rect(lay, BOOT, (cx + 1, cy + 14, 4, 5 + max(0, lo)))
    # ---- the long belted trench (even neutral light; narrows edge-on) ----
    bw = 12 if prof else 14
    bl = cx - bw // 2
    jh = 22 + hemsway
    pygame.draw.rect(lay, COAT, (bl, sh_y, bw, jh))
    pygame.draw.rect(lay, CO_LO, (bl, sh_y, bw, jh), 1)
    pygame.draw.rect(lay, INK, (bl, by, bw, 2))                          # belt
    pygame.draw.rect(lay, CO_HI, (cx - 1, by, 2, 2))                     # buckle
    pygame.draw.rect(lay, INK, (bl, cy + 9, bw, 2))                      # hem shadow
    for hx in range(bl + 1, bl + bw, 3):                                # hem fall
        pygame.draw.line(lay, INK, (hx, cy + 11), (hx, cy + 11 + (hx % 2)), 1)
    pygame.draw.rect(lay, COAT, (bl - 1, sh_y, bw + 2, 3))              # shoulders
    pygame.draw.rect(lay, CO_LO, (bl - 1, sh_y, bw + 2, 1))            # shoulder seam
    if view == "back":
        # ---- BACK: collar up, yoke + epaulettes, centre seam, back vent ----
        pygame.draw.rect(lay, COAT, (cx - 5, sh_y - 5, 11, 6))          # tall collar
        pygame.draw.rect(lay, CO_LO, (cx - 5, sh_y - 2, 11, 2))
        pygame.draw.line(lay, CO_HI, (cx - 5, sh_y - 5), (cx + 5, sh_y - 5), 1)  # collar top edge
        pygame.draw.line(lay, CO_LO, (cx - 6, sh_y + 3), (cx + 6, sh_y + 3), 1)  # yoke seam
        pygame.draw.rect(lay, CO_LO, (cx - 6, sh_y, 4, 2)); lay.set_at((cx - 5, sh_y), CO_HI)  # epaulette L
        pygame.draw.rect(lay, CO_LO, (cx + 2, sh_y, 4, 2)); lay.set_at((cx + 4, sh_y), CO_HI)  # epaulette R
        pygame.draw.line(lay, CO_LO, (cx, sh_y + 4), (cx, by), 1)       # centre back seam
        pygame.draw.line(lay, INK, (cx, by + 2), (cx, cy + 9), 1)       # back vent
        pygame.draw.rect(lay, SK_LO, (cx - 1, hcy, 2, 1))             # thin neck sliver
        pygame.draw.ellipse(lay, HAT, (cx - 8, hcy - 3, 16, 3))       # fedora brim (back)
        pygame.draw.ellipse(lay, INK, (cx - 8, hcy - 2, 16, 2), 1)
        pygame.draw.rect(lay, HAT, (cx - 4, hcy - 9, 8, 6))          # crown
        pygame.draw.ellipse(lay, HAT, (cx - 4, hcy - 11, 8, 4))      # crown top
        pygame.draw.rect(lay, INK, (cx - 4, hcy - 4, 8, 1))         # band
        _cig_fx(lay, t, cx + 4, hcy - 2, ember=False)                # smoke past the head
    elif prof:
        # ---- PROFILE ----
        fxe = cx + (bw // 2 - 1) * s
        pygame.draw.rect(lay, CO_LO, (fxe, sh_y, 2, jh - 1))           # front closure edge
        pygame.draw.line(lay, CO_LO, (cx - (bw // 2) * s, sh_y + 3),
                         (cx - (bw // 2) * s, cy + 9), 1)             # back drape
        pygame.draw.rect(lay, CO_LO, (cx - 1, by + 3, 5, 4))          # slash pocket
        pygame.draw.rect(lay, COAT, (cx - 4 * s, sh_y - 4, 5, 5))     # collar up (nape)
        pygame.draw.rect(lay, CO_LO, (cx - 4 * s, sh_y - 1, 5, 2))
        # head -- SAME as front (10x13); nose pokes forward, features mirror it
        hx = cx
        pygame.draw.ellipse(lay, SKIN, (hx - 5, hcy - 2, 10, 13))
        pygame.draw.ellipse(lay, SK_LO, (hx - 5, hcy - 2, 10, 13), 1)
        pygame.draw.rect(lay, SK_LO, (hx - 4, hcy + 1, 8, 3))         # brim shadow band
        pygame.draw.rect(lay, SKIN, (hx + 5 * s, hcy + 1, 2, 2))      # nose
        pygame.draw.rect(lay, SK_LO, (hx + 6 * s, hcy + 3, 1, 1))     # under-nose
        pygame.draw.rect(lay, INK, (hx + 2 * s, hcy + 1, 2, 2)); lay.set_at((hx + 2 * s, hcy + 1), GLINT)  # eye
        pygame.draw.line(lay, SK_LO, (hx + s, hcy + 5), (hx + 4 * s, hcy + 5), 1)   # mouth
        pygame.draw.line(lay, SK_LO, (hx - 2 * s, hcy + 7), (hx + 4 * s, hcy + 7), 1)  # jaw
        pygame.draw.ellipse(lay, HAT, (hx - 7, hcy - 2, 15, 3))       # fedora brim
        pygame.draw.ellipse(lay, HAT, (hx + (2 if s > 0 else -9), hcy - 2, 9, 3))  # brim juts forward
        pygame.draw.rect(lay, HAT, (hx - 4, hcy - 7, 8, 5))         # crown
        pygame.draw.ellipse(lay, HAT, (hx - 4, hcy - 9, 8, 4))      # crown top
        pygame.draw.rect(lay, INK, (hx - 4, hcy - 3, 8, 1))        # band
        # near arm (sleeve) + cuff
        ax = cx + (1 if s > 0 else -4)
        pygame.draw.rect(lay, COAT, (ax, sh_y + 4, 3, 11)); pygame.draw.rect(lay, CO_LO, (ax, sh_y + 4, 3, 11), 1)
        pygame.draw.rect(lay, INK, (ax, sh_y + 13, 3, 2))           # cuff
        cxg = hx + 6 * s
        pygame.draw.line(lay, (208, 206, 200), (hx + 4 * s, hcy + 4), (cxg, hcy + 5), 1)  # cigarette
        _cig_fx(lay, t, cxg, hcy + 5)
    else:
        # ---- FRONT: collar wings, lapel V + shirt/tie, buttons, pockets ----
        pygame.draw.polygon(lay, CO_LO, [(cx - 6, sh_y - 3), (cx - 2, sh_y + 1), (cx - 6, sh_y + 2)])  # collar L
        pygame.draw.polygon(lay, CO_LO, [(cx + 6, sh_y - 3), (cx + 2, sh_y + 1), (cx + 6, sh_y + 2)])  # collar R
        pygame.draw.polygon(lay, CO_LO, [(cx - 6, sh_y), (cx - 1, sh_y + 6), (cx - 6, sh_y + 7)])      # lapel L
        pygame.draw.polygon(lay, CO_LO, [(cx + 6, sh_y), (cx + 1, sh_y + 6), (cx + 6, sh_y + 7)])      # lapel R
        pygame.draw.rect(lay, SHIRT, (cx - 1, sh_y, 3, 3))           # shirt
        pygame.draw.rect(lay, TIE, (cx, sh_y + 2, 1, 6))           # tie
        for row in (sh_y + 9, by - 2):                              # double-breast buttons
            pygame.draw.circle(lay, INK, (cx - 4, row), 1); pygame.draw.circle(lay, INK, (cx + 4, row), 1)
        pygame.draw.line(lay, CO_LO, (cx - 6, by + 4), (cx - 3, by + 3), 1)  # slash pocket L
        pygame.draw.line(lay, CO_LO, (cx + 6, by + 4), (cx + 3, by + 3), 1)  # slash pocket R
        pygame.draw.ellipse(lay, SKIN, (cx - 5, hcy - 2, 10, 13))    # face
        pygame.draw.ellipse(lay, SK_LO, (cx - 5, hcy - 2, 10, 13), 1)
        pygame.draw.rect(lay, SK_LO, (cx - 4, hcy + 1, 8, 3))       # brim shadow band
        for ex in (cx - 4, cx + 1):
            pygame.draw.rect(lay, INK, (ex, hcy + 1, 3, 2)); lay.set_at((ex + 1, hcy + 1), GLINT)
        pygame.draw.line(lay, SK_LO, (cx, hcy + 3), (cx, hcy + 5), 1)  # nose
        pygame.draw.ellipse(lay, HAT, (cx - 8, hcy - 2, 16, 3))      # fedora brim (wide)
        pygame.draw.ellipse(lay, INK, (cx - 8, hcy - 1, 16, 2), 1)
        pygame.draw.rect(lay, HAT, (cx - 4, hcy - 7, 8, 4))         # crown
        pygame.draw.line(lay, HAT_LO, (cx, hcy - 7), (cx, hcy - 4), 1)  # crease
        pygame.draw.rect(lay, INK, (cx - 4, hcy - 3, 8, 1))        # band
        pygame.draw.line(lay, (208, 206, 200), (cx + 1, hcy + 6), (cx + 5, hcy + 7), 1)  # cigarette
        _cig_fx(lay, t, cx + 5, hcy + 7)
    smudge = pygame.Surface((44, 60), pygame.SRCALPHA)
    for sxp, syp, rw, rh in ((cx - 3, cy, 5, 3), (cx + 2, sh_y + 5, 4, 3),
                             (cx - 1, by + 4, 6, 2)):
        pygame.draw.ellipse(smudge, (8, 8, 6, 70), (sxp - rw // 2, syp - rh // 2, rw, rh))
    lay.blit(smudge, (0, 0))
    _darkwood_pass(lay, 0x9151, strength=1.2)                         # the game's grime
    surf.blit(lay, (int(x) - LX, int(y) - LY))
