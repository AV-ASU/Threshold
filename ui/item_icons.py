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


def _charcoal(s):
    pygame.draw.line(s, _BLACK, (4, 12), (12, 4), 4)
    pygame.draw.line(s, (90, 90, 95), (5, 12), (12, 5), 1)


def _paper(s):
    pygame.draw.rect(s, _PAPER, (4, 3, 9, 11))
    pygame.draw.rect(s, _PAPER_DARK, (4, 3, 9, 11), 1)
    pygame.draw.line(s, _PAPER_DARK, (6, 7), (11, 7), 1)
    pygame.draw.line(s, _PAPER_DARK, (6, 10), (10, 10), 1)


def _sigil_rubbing(s):
    # The Pallid Mask: a pale half-face, black eyeholes, a centre seam.
    pygame.draw.ellipse(s, _PAPER, (4, 2, 9, 13))
    pygame.draw.ellipse(s, _PAPER_DARK, (4, 2, 9, 13), 1)
    pygame.draw.ellipse(s, _INK, (6, 6, 2, 3))    # left eyehole
    pygame.draw.ellipse(s, _INK, (10, 6, 2, 3))   # right eyehole
    pygame.draw.line(s, _PAPER_DARK, (8, 9), (8, 13), 1)  # seam


def _car_keys(s):
    pygame.draw.circle(s, _BRASS, (5, 8), 3, 1)
    pygame.draw.circle(s, _BRASS_DARK, (5, 8), 1)
    pygame.draw.line(s, _BRASS, (8, 8), (14, 8), 1)
    pygame.draw.line(s, _BRASS, (12, 8), (12, 11), 1)
    pygame.draw.line(s, _BRASS, (14, 8), (14, 10), 1)


def _kid_drawing(s):
    pygame.draw.rect(s, _PAPER, (3, 3, 11, 11))
    pygame.draw.rect(s, _PAPER_DARK, (3, 3, 11, 11), 1)
    pygame.draw.line(s, (130, 30, 40), (6, 7), (11, 7), 1)
    pygame.draw.line(s, (130, 30, 40), (5, 10), (12, 10), 1)
    pygame.draw.circle(s, (130, 30, 40), (8, 9), 1)


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


def _playscript(s):
    pygame.draw.circle(s, _BRUISE_LO, (8, 9), 6)
    pygame.draw.circle(s, _BRUISE, (8, 9), 5)
    pygame.draw.circle(s, _BRUISE_HI, (6, 7), 2)


def _polaroid(s):
    pygame.draw.rect(s, _PAPER, (3, 3, 11, 11))
    pygame.draw.rect(s, _PAPER_DARK, (3, 3, 11, 11), 1)
    pygame.draw.rect(s, (90, 80, 70), (5, 5, 7, 6))
    pygame.draw.line(s, _PAPER_DARK, (4, 12), (12, 12), 1)


def _cellar_bottle(s):
    pygame.draw.rect(s, _GLASS_HI, (7, 2, 2, 2))
    pygame.draw.rect(s, _GLASS, (6, 4, 4, 2))
    pygame.draw.rect(s, _GLASS, (5, 6, 6, 8))
    pygame.draw.rect(s, _BORDER, (5, 6, 6, 8), 1)
    pygame.draw.rect(s, _PAPER, (5, 8, 6, 4))
    pygame.draw.line(s, _INK, (6, 10), (9, 10), 1)


def _liquor_crate(s):
    # Wooden crate with three bottle necks poking out the top. Slat
    # seams + a darker shadow on the right side so it reads as a
    # 3D box rather than a flat rectangle.
    pygame.draw.rect(s, _WOOD,      (2, 6, 12, 8))
    pygame.draw.rect(s, _WOOD_DARK, (2, 6, 12, 8), 1)
    # Slat seams (two vertical lines)
    pygame.draw.line(s, _WOOD_DARK, (6, 6), (6, 13), 1)
    pygame.draw.line(s, _WOOD_DARK, (10, 6), (10, 13), 1)
    # Three bottle necks (dark green) sticking out of the crate top
    for nx in (4, 8, 12):
        pygame.draw.rect(s, _GLASS,    (nx - 1, 3, 2, 4))
        pygame.draw.rect(s, _BORDER,   (nx - 1, 3, 2, 4), 1)
        pygame.draw.rect(s, _GLASS_HI, (nx - 1, 3, 1, 1))
    # Right-side shadow
    pygame.draw.line(s, _WOOD_DARK, (13, 7), (13, 13), 1)


def _diary_page(s):
    pygame.draw.polygon(s, _PAPER,
                        [(3, 3), (12, 3), (13, 8), (12, 14), (4, 14), (3, 8)])
    pygame.draw.polygon(s, _PAPER_DARK,
                        [(3, 3), (12, 3), (13, 8), (12, 14), (4, 14), (3, 8)], 1)
    pygame.draw.line(s, _INK, (5, 7), (11, 7), 1)
    pygame.draw.line(s, _INK, (5, 10), (10, 10), 1)


def _old_doll(s):
    pygame.draw.circle(s, _CLOTH, (8, 5), 3)
    pygame.draw.circle(s, _CLOTH_DARK, (8, 5), 3, 1)
    pygame.draw.rect(s, _CLOTH, (5, 8, 6, 6))
    pygame.draw.rect(s, _CLOTH_DARK, (5, 8, 6, 6), 1)
    pygame.draw.line(s, _INK, (7, 5), (7, 5), 1)
    pygame.draw.line(s, _INK, (9, 5), (9, 5), 1)
    pygame.draw.line(s, _CLOTH_DARK, (5, 11), (10, 11), 1)


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
    "charcoal":        _charcoal,
    "paper":           _paper,
    "sigil_rubbing":   _sigil_rubbing,
    "car_keys":        _car_keys,
    "kid_drawing":     _kid_drawing,
    "robe":            _robe,
    "mom_notebook":    _mom_notebook,
    "playscript":             _playscript,
    "polaroid":        _polaroid,
    "cellar_bottle":   _cellar_bottle,
    "liquor_crate":    _liquor_crate,
    "diary_page_1":    _diary_page,
    "diary_page_2":    _diary_page,
    "old_doll":        _old_doll,
}


def draw_item_icon(surf, x, y, key):
    box = pygame.Surface((16, 16), pygame.SRCALPHA)
    fn = _DISPATCH.get(key, _unknown)
    fn(box)
    surf.blit(box, (x, y))
