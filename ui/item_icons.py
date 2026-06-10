"""16x16 hand-drawn pygame icons for inventory items.

Centered into a 16x16 SRCALPHA box. Muted palette, no asset files.
"""
import pygame


# Shared palette (muted, slightly grimy).
_WOOD       = (90, 60, 40)
_WOOD_DARK  = (60, 40, 25)
_STEEL      = (140, 140, 150)
_STEEL_DARK = (70, 70, 80)
_PAPER      = (220, 210, 175)   # yellowed
_PAPER_DARK = (150, 135, 95)
_INK        = (40, 30, 25)
_BRUISE     = (70, 50, 90)
_BRUISE_HI  = (110, 70, 110)
_BRUISE_LO  = (40, 25, 55)
_GLASS      = (60, 80, 70)
_GLASS_HI   = (110, 130, 110)
_BLACK      = (20, 18, 22)
_BRASS      = (180, 150, 70)
_BRASS_DARK = (110, 85, 30)
_CLOTH      = (130, 105, 85)
_CLOTH_DARK = (80, 60, 45)
_ROBE       = (170, 155, 120)
_ROBE_DARK  = (95, 80, 55)
_BORDER     = (30, 25, 30)


def _axe(s):
    pygame.draw.line(s, _WOOD, (10, 14), (4, 4), 2)
    pygame.draw.polygon(s, _STEEL, [(3, 5), (8, 2), (9, 6), (4, 8)])
    pygame.draw.polygon(s, _STEEL_DARK, [(3, 5), (8, 2), (9, 6), (4, 8)], 1)


def _flashlight(s):
    # Steel barrel angled up-right, a pale lens at the head, and a short
    # warm beam spilling from it.
    pygame.draw.line(s, (250, 240, 180), (11, 5), (15, 1), 3)   # beam
    pygame.draw.line(s, (250, 240, 180), (11, 7), (15, 5), 2)
    pygame.draw.rect(s, _STEEL, (3, 8, 8, 4))                   # barrel
    pygame.draw.rect(s, _STEEL_DARK, (3, 8, 8, 4), 1)
    pygame.draw.rect(s, (235, 225, 170), (10, 7, 3, 6))         # lens
    pygame.draw.rect(s, _STEEL_DARK, (10, 7, 3, 6), 1)
    pygame.draw.rect(s, _STEEL_DARK, (2, 9, 1, 2))              # tail cap


def _sigil_rubbing(s):
    # The Pallid Mask: a pale half-face, black eyeholes, a centre seam.
    pygame.draw.ellipse(s, _PAPER, (4, 2, 9, 13))
    pygame.draw.ellipse(s, _PAPER_DARK, (4, 2, 9, 13), 1)
    pygame.draw.ellipse(s, _INK, (6, 6, 2, 3))    # left eyehole
    pygame.draw.ellipse(s, _INK, (10, 6, 2, 3))   # right eyehole
    pygame.draw.line(s, _PAPER_DARK, (8, 9), (8, 13), 1)  # seam


def _robe(s):
    pygame.draw.polygon(s, _ROBE,
                        [(8, 2), (12, 6), (13, 14), (3, 14), (4, 6)])
    pygame.draw.polygon(s, _ROBE_DARK,
                        [(8, 2), (12, 6), (13, 14), (3, 14), (4, 6)], 1)
    pygame.draw.line(s, _BLACK, (5, 13), (10, 13), 1)
    pygame.draw.line(s, (60, 30, 20), (4, 14), (12, 14), 1)


def _mom_notebook(s):
    pygame.draw.rect(s, (90, 60, 75), (4, 3, 9, 11))
    pygame.draw.rect(s, (50, 30, 40), (4, 3, 9, 11), 1)
    for yy in range(4, 14, 2):
        pygame.draw.line(s, _BRASS, (3, yy), (5, yy), 1)


def _testimony(s):
    # A loose leaf of the cult's testimony: a written page, a few lines of
    # script. Shared by the three fragments (Calling / Bargain / Digging).
    pygame.draw.rect(s, _PAPER, (4, 3, 9, 11))
    pygame.draw.rect(s, _PAPER_DARK, (4, 3, 9, 11), 1)
    for yy in (5, 7, 9, 11):
        pygame.draw.line(s, _PAPER_DARK, (6, yy), (11, yy), 1)


def _letter(s):
    # Mara's unsent letter: a folded sheet with an envelope crease.
    pygame.draw.rect(s, _PAPER, (3, 4, 11, 9))
    pygame.draw.rect(s, _PAPER_DARK, (3, 4, 11, 9), 1)
    pygame.draw.line(s, _PAPER_DARK, (3, 4), (8, 9), 1)
    pygame.draw.line(s, _PAPER_DARK, (14, 4), (8, 9), 1)


def _newspaper(s):
    # Yesterday's paper, folded in half: masthead band, column rules.
    pygame.draw.rect(s, _PAPER, (2, 4, 12, 9))
    pygame.draw.rect(s, _PAPER_DARK, (2, 4, 12, 9), 1)
    pygame.draw.line(s, _PAPER_DARK, (2, 8), (13, 8), 1)   # the fold
    pygame.draw.rect(s, _INK, (4, 5, 6, 1))                # masthead
    for ly in (10, 11):
        pygame.draw.line(s, _PAPER_DARK, (4, ly), (11, ly), 1)


def _unknown(s):
    pygame.draw.line(s, _PAPER_DARK, (6, 5), (10, 5), 1)
    pygame.draw.line(s, _PAPER_DARK, (10, 5), (10, 8), 1)
    pygame.draw.line(s, _PAPER_DARK, (8, 8), (10, 8), 1)
    pygame.draw.line(s, _PAPER_DARK, (8, 8), (8, 10), 1)
    pygame.draw.rect(s, _PAPER_DARK, (8, 12, 1, 1))


def _cross(s):
    # The Preacher's plain silver cross, with a faint drop-shadow.
    silver, shade = (185, 189, 196), (118, 122, 130)
    pygame.draw.rect(s, shade, (8, 3, 2, 11))
    pygame.draw.rect(s, shade, (5, 6, 7, 2))
    pygame.draw.rect(s, silver, (7, 2, 2, 11))
    pygame.draw.rect(s, silver, (4, 5, 7, 2))


_DISPATCH = {
    "lumber_axe":      _axe,
    "cross":           _cross,
    "flashlight":      _flashlight,
    "sigil_rubbing":   _sigil_rubbing,
    "robe":            _robe,
    "mom_notebook":    _mom_notebook,
    "unsent_letter":   _letter,
    "newspaper":       _newspaper,
    "cult_calling":    _testimony,
    "cult_bargain":    _testimony,
    "cult_digging":    _testimony,
}


def draw_item_icon(surf, x, y, key):
    box = pygame.Surface((16, 16), pygame.SRCALPHA)
    fn = _DISPATCH.get(key, _unknown)
    fn(box)
    surf.blit(box, (x, y))
