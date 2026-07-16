"""Furniture decoration draw methods (split from decoration.py 2026-07).

Mixed into Decoration; each method is dispatched by
getattr(self, f"_draw_{kind}") from Decoration.draw."""
import math
import random
import time
import pygame
from constants import (
    SCREEN_W, SCREEN_H, C_BLACK, C_GOLD, C_RED,
)
from entities.decoration_common import (
    _compass_offset, _ground_shadow, _light_pool,
)


class DecoFurnitureMixin:
    def _draw_cistern_basin(self, surf, x, y):
        pygame.draw.ellipse(surf, (92, 96, 98), (x - 13, y - 9, 26, 18))
        pygame.draw.ellipse(surf, (50, 54, 56), (x - 13, y - 9, 26, 18), 1)
        pygame.draw.ellipse(surf, (14, 22, 26), (x - 9, y - 6, 18, 12))

    def _draw_cot(self, surf, x, y):
        pygame.draw.rect(surf, (94, 65, 41), (x - 14, y - 7, 28, 14))
        pygame.draw.rect(surf, (52, 35, 22), (x - 14, y - 7, 28, 14), 1)
        pygame.draw.rect(surf, (150, 142, 128), (x - 12, y - 5, 24, 7))

    def _draw_plank_bench(self, surf, x, y):
        # top-down: a rough backless plank on two trestle feet
        pygame.draw.rect(surf, (72, 49, 31), (x - 19, y - 4, 38, 8))
        pygame.draw.rect(surf, (46, 32, 20), (x - 19, y - 4, 38, 8), 1)
        pygame.draw.rect(surf, (40, 28, 18), (x - 15, y - 2, 3, 4))
        pygame.draw.rect(surf, (40, 28, 18), (x + 12, y - 2, 3, 4))

    def _draw_pew(self, surf, x, y):
        pygame.draw.rect(surf, (72, 49, 31), (x - 20, y - 5, 40, 10))
        pygame.draw.rect(surf, (52, 35, 22), (x - 20, y - 5, 40, 10), 1)

    def _draw_bed(self, surf, x, y):
        w = int(self.kwargs.get("w", 56)); h = int(self.kwargs.get("h", 64))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 29, 19), (rx, ry, w, h))             # frame
        pygame.draw.rect(surf, (22, 15, 9), (rx, ry, w, h), 1)
        ix, iy, iw, ih = rx + 3, ry + 3, w - 6, h - 6
        pygame.draw.rect(surf, (112, 104, 96), (ix, iy, iw, ih))         # mattress
        pygame.draw.rect(surf, (132, 124, 116), (ix, iy, iw, 2))         # lit top
        pygame.draw.rect(surf, (146, 138, 130), (ix + 3, iy + 3, iw - 6, h // 5))  # pillow
        pygame.draw.rect(surf, (118, 110, 102), (ix + 3, iy + 3 + h // 5, iw - 6, 1))
        by = iy + ih * 2 // 5
        pygame.draw.rect(surf, (86, 44, 48), (ix, by, iw, iy + ih - by)) # blanket
        pygame.draw.rect(surf, (108, 58, 62), (ix, by, iw, 2))           # lit edge
        pygame.draw.line(surf, (62, 32, 36), (x, by + 2), (x, iy + ih - 2), 1)  # fold
        pygame.draw.rect(surf, (58, 38, 30), (ix + iw // 2, by + ih // 4, 7, 6))  # stain

    def _draw_sheeted_bed(self, surf, x, y):
        """Flat (pitch-0) fallback for the sheeted_bed volume: the guest bed
        shut up under a pale dust sheet, fold lines where it drapes."""
        w = int(self.kwargs.get("w", 56)); h = int(self.kwargs.get("h", 64))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 29, 19), (rx, ry, w, h))              # frame
        pygame.draw.rect(surf, (22, 15, 9), (rx, ry, w, h), 1)
        ix, iy, iw, ih = rx + 2, ry + 2, w - 4, h - 4
        pygame.draw.rect(surf, (168, 164, 152), (ix, iy, iw, ih))         # the sheet
        pygame.draw.rect(surf, (188, 184, 172), (ix, iy, iw, 2))          # lit top
        for fy in (iy + ih // 4, iy + ih // 2, iy + 3 * ih // 4):         # folds
            pygame.draw.line(surf, (140, 136, 124), (ix + 2, fy),
                             (ix + iw - 2, fy + 3), 1)
        pygame.draw.line(surf, (108, 104, 94), (ix + iw // 3, iy + 2),
                         (ix + iw // 3 - 3, iy + ih - 2), 1)              # hang line

    def _draw_table(self, surf, x, y):
        w = int(self.kwargs.get("w", 54)); h = int(self.kwargs.get("h", 38))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 27, 16), (rx + 3, ry + h - 8, 5, 8))     # legs
        pygame.draw.rect(surf, (40, 27, 16), (rx + w - 8, ry + h - 8, 5, 8))
        th = h - 8
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, th))                # top
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))                 # lit back
        pygame.draw.rect(surf, (40, 27, 16), (rx, ry + th - 3, w, 3))        # front lip
        for gx in range(rx + 8, rx + w - 4, 11):
            pygame.draw.line(surf, (56, 38, 22), (gx, ry + 4), (gx, ry + th - 5), 1)

    def _draw_writing_desk(self, surf, x, y):
        """Flat (pitch-0) fallback for the writing_desk furniture box.
        A table with a drawer line + knob across the front."""
        w = int(self.kwargs.get("w", 58)); h = int(self.kwargs.get("h", 42))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (40, 27, 16), (rx + 3, ry + h - 8, 5, 8))     # legs
        pygame.draw.rect(surf, (40, 27, 16), (rx + w - 8, ry + h - 8, 5, 8))
        th = h - 8
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, th))                # top
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))                 # lit back
        pygame.draw.rect(surf, (52, 36, 22), (rx + 6, ry + th - 12, w - 12, 8))  # drawer
        pygame.draw.circle(surf, (34, 26, 16),
                           (rx + w // 2, ry + th - 8), 2)                    # knob
        pygame.draw.rect(surf, (40, 27, 16), (rx, ry + th - 3, w, 3))        # front lip
        # the open case file on the top (flat, top-down for pitch 0)
        bx, by, bw, bh = rx + w // 2 - 9, ry + 5, 18, 13
        pygame.draw.rect(surf, (206, 200, 182), (bx, by, bw, bh))
        pygame.draw.rect(surf, (120, 112, 92), (bx, by, bw, bh), 1)
        pygame.draw.line(surf, (120, 112, 92), (bx + bw // 2, by),
                         (bx + bw // 2, by + bh), 1)
        for iy in range(by + 3, by + bh - 1, 3):
            pygame.draw.line(surf, (78, 70, 60), (bx + 2, iy), (bx + bw // 2 - 2, iy), 1)
            pygame.draw.line(surf, (78, 70, 60), (bx + bw // 2 + 2, iy), (bx + bw - 2, iy), 1)
        # the revolver on the top, until taken
        if getattr(self, "gun_present", False):
            gx = rx + 8
            pygame.draw.line(surf, (66, 46, 30), (gx, ry + 14), (gx + 4, ry + 10), 3)
            pygame.draw.line(surf, (32, 34, 38), (gx + 4, ry + 10), (gx + 13, ry + 6), 3)
            pygame.draw.line(surf, (120, 124, 132), (gx + 4, ry + 10), (gx + 13, ry + 6), 1)

    def _draw_nightstand(self, surf, x, y):
        """Flat (pitch-0) fallback for the nightstand box: a small bedside
        end table, a drawer with a brass knob over an open shelf recess."""
        w = int(self.kwargs.get("w", 26)); h = int(self.kwargs.get("h", 28))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (44, 30, 18), (rx + 2, ry + h - 7, 4, 7))     # legs
        pygame.draw.rect(surf, (44, 30, 18), (rx + w - 6, ry + h - 7, 4, 7))
        th = h - 7
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, th))                # body/top
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))                 # lit back
        pygame.draw.rect(surf, (52, 36, 22), (rx + 4, ry + 4, w - 8, 7))     # drawer
        pygame.draw.circle(surf, (206, 182, 118), (rx + w // 2, ry + 7), 2)  # brass knob
        pygame.draw.rect(surf, (30, 21, 12), (rx + 5, ry + 13, w - 10, th - 15))  # shelf recess
        pygame.draw.rect(surf, (40, 27, 16), (rx, ry + th - 3, w, 3))        # front lip

    def _draw_chair(self, surf, x, y):
        w = int(self.kwargs.get("w", 22)); h = int(self.kwargs.get("h", 28))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (44, 30, 18), (rx + 3, ry + h - 6, 3, 6))     # legs
        pygame.draw.rect(surf, (44, 30, 18), (rx + w - 6, ry + h - 6, 3, 6))
        pygame.draw.rect(surf, (64, 44, 26), (rx + 2, ry, w - 4, h // 3))    # back
        pygame.draw.rect(surf, (78, 56, 34), (rx + 2, ry + h // 3, w - 4, h // 3 + 2))  # seat
        pygame.draw.rect(surf, (98, 72, 44), (rx + 2, ry + h // 3, w - 4, 2))

    def _draw_small_chair(self, surf, x, y):
        """A child-sized chair pulled out from the writing table after
        crutch_taken. Wood-toned, smaller proportions than the regular
        chair object tile. Sits diagonally as if just stood up from."""
        pygame.draw.rect(surf, (110, 80, 60), (x - 6, y - 4, 12, 10))
        pygame.draw.rect(surf, (90, 60, 40), (x - 6, y - 8, 12, 6))
        pygame.draw.rect(surf, (60, 40, 25), (x - 6, y - 8, 12, 14), 1)
        pygame.draw.rect(surf, (70, 50, 32), (x - 5, y + 6, 2, 4))
        pygame.draw.rect(surf, (70, 50, 32), (x + 3, y + 6, 2, 4))

    def _draw_overturned_chair(self, surf, x, y):
        pygame.draw.rect(surf, (110, 80, 60), (x - 10, y - 2, 18, 6))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 2, 18, 6), 1)
        pygame.draw.rect(surf, (70, 50, 32), (x + 8, y - 8, 4, 6))
        pygame.draw.rect(surf, (70, 50, 32), (x + 8, y, 4, 6))
        pygame.draw.rect(surf, (90, 60, 40), (x - 10, y - 8, 6, 14))

    def _draw_wardrobe(self, surf, x, y):
        # Tall + narrow: a standing cabinet against a wall, twin doors.
        w = int(self.kwargs.get("w", 26)); h = int(self.kwargs.get("h", 52))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (60, 44, 27), (rx, ry, w, h))                 # carcass
        pygame.draw.rect(surf, (30, 22, 12), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (82, 60, 38), (rx, ry, w, 2))                 # lit top
        pygame.draw.rect(surf, (24, 17, 9), (rx, ry + h - 3, w, 3))          # base shadow
        pygame.draw.line(surf, (32, 23, 13), (x, ry + 2), (x, ry + h - 2), 1)  # door split
        for hy in (ry + h // 2 - 4, ry + h // 2 + 2):                        # handles
            pygame.draw.rect(surf, (38, 27, 16), (x - 3, hy, 2, 4))
            pygame.draw.rect(surf, (38, 27, 16), (x + 2, hy, 2, 4))

    def _draw_stove(self, surf, x, y):
        # Cast-iron range drawn canonically facing DOWN (cooktop at top,
        # oven door + ember toward the bottom = the front). `wall` (N/E/S/W
        # = the wall it stands against) rotates it so the oven door faces
        # INTO the room off any wall -- e.g. wall="W" turns the front to
        # the east. Default "N" keeps the original south-facing look.
        w = int(self.kwargs.get("w", 34)); h = int(self.kwargs.get("h", 40))
        lay = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(lay, (42, 42, 48), (0, 0, w, h))                    # body
        pygame.draw.rect(lay, (60, 60, 68), (0, 0, w, 2))                    # lit top
        pygame.draw.rect(lay, (22, 22, 28), (0, h - 3, w, 3))                # base shadow
        pygame.draw.rect(lay, (28, 28, 34), (0, 0, w, h), 1)
        for cxk in (w // 3, 2 * w // 3):                                     # burners
            pygame.draw.circle(lay, (18, 18, 24), (cxk, 9), 4)
            pygame.draw.circle(lay, (10, 10, 14), (cxk, 9), 2)
        pygame.draw.rect(lay, (16, 16, 20), (4, h - 16, w - 8, 11))          # oven door
        pygame.draw.rect(lay, (70, 70, 78), (7, h - 17, w - 14, 2))          # handle
        pygame.draw.rect(lay, (200, 90, 30), (w // 2 - 5, h - 7, 10, 2))     # ember
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(
            self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_counter(self, surf, x, y):
        # Flat fallback for the counter slab (same gap): a long worktop,
        # like the table top but with a solid front lip and no legs.
        w = int(self.kwargs.get("w", 60)); h = int(self.kwargs.get("h", 26))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, h))
        pygame.draw.rect(surf, (34, 23, 13), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))             # lit back
        pygame.draw.rect(surf, (40, 27, 16), (rx, ry + h - 4, w, 4))     # front lip
        for gx in range(rx + 8, rx + w - 4, 12):                         # grain
            pygame.draw.line(surf, (56, 38, 22), (gx, ry + 3), (gx, ry + h - 5), 1)

    def _draw_butcher_counter(self, surf, x, y):
        # Flat fallback: the shop's butcher counter shares the plain
        # counter slab top-down (the butcher detail is a tilt near-face
        # read; see rendering/furniture.py _d_butcher).
        self._draw_counter(surf, x, y)

    def _draw_washstand(self, surf, x, y):
        # A bedroom washstand: a small dark stand with a towel rail, a
        # porcelain basin sunk in the top and a ewer jug beside it. The
        # water in the basin is a shade too dark.
        pygame.draw.ellipse(surf, (0, 0, 0), (x - 11, y + 12, 24, 6))   # shadow
        pygame.draw.rect(surf, (56, 42, 30), (x - 9, y - 2, 19, 14))    # stand body
        pygame.draw.rect(surf, (38, 28, 20), (x - 9, y - 2, 19, 14), 1)
        pygame.draw.rect(surf, (70, 54, 38), (x - 9, y - 2, 19, 3))     # top edge
        pygame.draw.rect(surf, (30, 22, 16), (x - 8, y + 12, 3, 3))     # feet
        pygame.draw.rect(surf, (30, 22, 16), (x + 6, y + 12, 3, 3))
        pygame.draw.line(surf, (38, 28, 20), (x - 12, y + 1), (x - 12, y + 9), 1)  # towel rail
        pygame.draw.rect(surf, (168, 160, 144), (x - 14, y + 1, 4, 8))  # limp towel
        pygame.draw.rect(surf, (132, 124, 110), (x - 14, y + 5, 4, 1))
        pygame.draw.ellipse(surf, (208, 202, 188), (x - 7, y - 6, 12, 7))   # basin
        pygame.draw.ellipse(surf, (148, 142, 130), (x - 7, y - 6, 12, 7), 1)
        pygame.draw.ellipse(surf, (44, 48, 50), (x - 5, y - 5, 8, 4))   # too-dark water
        pygame.draw.ellipse(surf, (208, 202, 188), (x + 5, y - 9, 6, 9))    # ewer jug
        pygame.draw.ellipse(surf, (148, 142, 130), (x + 5, y - 9, 6, 9), 1)
        pygame.draw.arc(surf, (148, 142, 130), (x + 9, y - 8, 4, 6), -1.6, 1.6, 1)  # handle
        pygame.draw.rect(surf, (208, 202, 188), (x + 6, y - 11, 3, 3))  # spout neck

    def _draw_preserve_shelf(self, surf, x, y):
        # A larder shelf of preserve jars. Most hold what they should;
        # the contents have all gone the same murky shade, and one jar
        # near the end holds something the light doesn't explain.
        rng = random.Random(self.seed if self.seed is not None else 7)
        pygame.draw.rect(surf, (52, 40, 28), (x - 16, y + 4, 33, 3))    # shelf board
        pygame.draw.rect(surf, (34, 26, 18), (x - 16, y + 4, 33, 3), 1)
        pygame.draw.rect(surf, (34, 26, 18), (x - 15, y + 7, 2, 3))     # brackets
        pygame.draw.rect(surf, (34, 26, 18), (x + 13, y + 7, 2, 3))
        murks = [(96, 82, 40), (88, 56, 34), (72, 70, 38), (90, 44, 38)]
        jx = x - 13
        wrong = rng.randint(2, 4)                       # which jar is wrong
        for i in range(5):
            jw = rng.choice((5, 6)); jh = rng.choice((8, 9, 10))
            if jx + jw > x + 16:
                break
            jy = y + 4 - jh
            body = rng.choice(murks)
            if i == wrong:
                body = (24, 22, 26)                     # the one that's wrong
            pygame.draw.rect(surf, body, (jx, jy, jw, jh))
            pygame.draw.rect(surf, (140, 134, 118), (jx, jy - 2, jw, 2))   # wax/lid
            pygame.draw.rect(surf, tuple(c // 2 for c in body), (jx, jy, jw, jh), 1)
            pygame.draw.line(surf, (200, 196, 180), (jx + 1, jy + 1),
                             (jx + 1, jy + jh - 2), 1)                     # glass glint
            if i == wrong:
                # a pale curve pressed against the inside of the glass
                pygame.draw.arc(surf, (150, 142, 124),
                                (jx + 1, jy + 2, jw - 2, jh - 4), 0.6, 2.6, 1)
            jx += jw + 1

    def _draw_birdcage(self, surf, x, y):
        # A domed wire birdcage on a floor stand. The little door hangs
        # open. The perch still swings, just barely. Nothing is on it.
        pygame.draw.ellipse(surf, (0, 0, 0), (x - 7, y + 14, 15, 4))    # shadow
        pygame.draw.line(surf, (70, 66, 60), (x, y + 4), (x, y + 14), 2)    # stand post
        pygame.draw.rect(surf, (70, 66, 60), (x - 5, y + 14, 11, 2))    # foot
        cage = pygame.Rect(x - 7, y - 14, 15, 19)
        pygame.draw.ellipse(surf, (96, 90, 78), (cage.x, cage.y - 4, 15, 10))   # dome
        pygame.draw.ellipse(surf, (60, 56, 48), (cage.x, cage.y - 4, 15, 10), 1)
        pygame.draw.rect(surf, (96, 90, 78), (cage.x, cage.y, 15, 2))   # collar
        for i in range(5):                                              # bars
            bx = cage.x + 1 + i * 3
            pygame.draw.line(surf, (96, 90, 78), (bx, cage.y + 1), (bx, cage.bottom - 1), 1)
        pygame.draw.rect(surf, (96, 90, 78), (cage.x, cage.bottom - 2, 15, 2))  # base ring
        pygame.draw.line(surf, (60, 56, 48), (x, cage.y - 8), (x, cage.y - 4), 1)  # finial
        # the door, swung open on its hinge
        pygame.draw.rect(surf, (10, 9, 12), (x + 1, y - 8, 5, 7))       # the gap it left
        pygame.draw.rect(surf, (96, 90, 78), (x + 6, y - 10, 5, 7), 1)  # door ajar
        # the perch, swaying empty
        sway = math.sin(self.t * 0.9 + (self.seed or 0)) * 1.0
        pygame.draw.line(surf, (84, 62, 40),
                         (x - 4 + sway, y - 5), (x + 2 + sway, y - 5), 1)
        # a few down-feathers under the cage
        for fx, fy in ((-4, 17), (2, 18), (-1, 19)):
            pygame.draw.line(surf, (170, 164, 150), (x + fx, y + fy), (x + fx + 2, y + fy), 1)

    def _draw_butter_churn(self, surf, x, y):
        # A barrel butter churn: tapered staves, two hoops, the plunger
        # staff leaning out of the lid. Nobody has churned in a while.
        pygame.draw.ellipse(surf, (0, 0, 0), (x - 7, y + 12, 16, 5))    # shadow
        pygame.draw.polygon(surf, (92, 66, 40),                          # tapered body
                            [(x - 7, y + 14), (x + 8, y + 14), (x + 6, y - 4), (x - 5, y - 4)])
        pygame.draw.polygon(surf, (56, 40, 24),
                            [(x - 7, y + 14), (x + 8, y + 14), (x + 6, y - 4), (x - 5, y - 4)], 1)
        for sxo in (-3, 0, 3):                                           # stave seams
            pygame.draw.line(surf, (66, 47, 28), (x + sxo, y - 3), (x + sxo, y + 13), 1)
        pygame.draw.rect(surf, (50, 48, 52), (x - 6, y - 1, 13, 2))     # iron hoops
        pygame.draw.rect(surf, (50, 48, 52), (x - 7, y + 8, 15, 2))
        pygame.draw.ellipse(surf, (70, 50, 30), (x - 5, y - 6, 11, 4))  # lid
        pygame.draw.ellipse(surf, (44, 32, 20), (x - 5, y - 6, 11, 4), 1)
        pygame.draw.line(surf, (84, 62, 40), (x, y - 5), (x + 4, y - 18), 2)   # plunger staff
        pygame.draw.rect(surf, (84, 62, 40), (x + 2, y - 20, 5, 3))     # handle

    def _draw_bookshelf(self, surf, x, y):
        # Long + shallow: sits flush to a wall, books leaning along it.
        w = int(self.kwargs.get("w", 58)); h = int(self.kwargs.get("h", 18))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (56, 41, 25), (rx, ry, w, h))             # case
        pygame.draw.rect(surf, (30, 22, 12), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (78, 58, 36), (rx, ry, w, 2))             # lit top rail
        pygame.draw.rect(surf, (24, 17, 9), (rx, ry + h - 2, w, 2))      # base shadow
        cols = [(92, 46, 42), (48, 58, 74), (56, 72, 48), (104, 86, 46), (74, 52, 78)]
        bx, i = rx + 3, 0
        while bx < rx + w - 3:
            bw = 3 + ((self.seed + i * 7) % 3)
            bh = (h - 6) - ((self.seed + i * 5) % 3)
            col = cols[i % len(cols)]
            pygame.draw.rect(surf, col, (bx, ry + h - 3 - bh, bw, bh))
            pygame.draw.rect(surf, (col[0] // 2, col[1] // 2, col[2] // 2),
                             (bx, ry + h - 3 - bh, bw, 1))
            bx += bw + 1; i += 1

    def _draw_bare_shelf(self, surf, x, y):
        # The general store's emptied goods shelf (food scarcity, NARRATIVE
        # 8): the bookshelf case with nothing standing on the runs -- pale
        # dust-ghost outlines where stock stood, and one tin nobody wanted.
        w = int(self.kwargs.get("w", 58)); h = int(self.kwargs.get("h", 18))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (56, 41, 25), (rx, ry, w, h))             # case
        pygame.draw.rect(surf, (30, 22, 12), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (78, 58, 36), (rx, ry, w, 2))             # lit top rail
        pygame.draw.rect(surf, (24, 17, 9), (rx, ry + h - 2, w, 2))      # base shadow
        for i in range(3):                                               # dust ghosts
            gx = rx + 5 + ((self.seed + i * 13) % max(1, w - 18))
            pygame.draw.rect(surf, (70, 54, 34),
                             (gx, ry + 4, 6 + (i % 2) * 3, h - 9), 1)
        tx = rx + w - 9                                                  # the lone tin
        pygame.draw.rect(surf, (118, 112, 96), (tx, ry + 5, 4, h - 10))
        pygame.draw.line(surf, (86, 82, 70), (tx, ry + 5), (tx + 3, ry + 5), 1)

    def _draw_place_setting(self, surf, x, y):
        """A single place setting on the writing table after the player
        carries the reservation slip back into the bedroom: one plate,
        one chair, one candle. The other three settings the slip
        listed are conspicuously absent."""
        # Plate
        pygame.draw.ellipse(surf, (220, 220, 230), (x - 7, y - 4, 14, 8))
        pygame.draw.ellipse(surf, (60, 60, 70), (x - 7, y - 4, 14, 8), 1)
        pygame.draw.ellipse(surf, (240, 240, 250), (x - 5, y - 3, 10, 6))
        # Fork to the left
        pygame.draw.line(surf, (180, 180, 200), (x - 10, y - 2),
                         (x - 10, y + 4), 1)
        pygame.draw.line(surf, (180, 180, 200), (x - 11, y - 2),
                         (x - 9, y - 2), 1)
        # Knife to the right
        pygame.draw.line(surf, (180, 180, 200), (x + 10, y - 2),
                         (x + 10, y + 4), 1)
        # Tiny candle
        pygame.draw.rect(surf, (220, 200, 160), (x - 1, y - 12, 2, 7))
        glow = 0.7 + math.sin(self.t * 4 + self.seed) * 0.3
        pygame.draw.circle(surf, (240, 200, 100),
                           (x, y - 13), max(2, int(3 * glow)))

    def _draw_clock(self, surf, x, y):
        pygame.draw.rect(surf, (90, 60, 40), (x - 8, y - 16, 16, 28))
        pygame.draw.rect(surf, (40, 25, 15), (x - 8, y - 16, 16, 28), 1)
        pygame.draw.circle(surf, (240, 230, 210), (x, y - 8), 6)
        pygame.draw.circle(surf, (40, 25, 15), (x, y - 8), 6, 1)
        pygame.draw.line(surf, C_BLACK, (x, y - 13), (x, y - 12), 1)
        pygame.draw.line(surf, C_BLACK, (x, y - 4), (x, y - 3), 1)
        minute = self.t * 0.05
        second = math.floor(self.t * 1.0) * (math.pi / 30)
        mx = x + math.cos(minute - math.pi / 2) * 4
        my = (y - 8) + math.sin(minute - math.pi / 2) * 4
        pygame.draw.line(surf, C_BLACK, (x, y - 8), (mx, my), 1)
        sx2 = x + math.cos(second - math.pi / 2) * 5
        sy2 = (y - 8) + math.sin(second - math.pi / 2) * 5
        pygame.draw.line(surf, C_RED, (x, y - 8), (sx2, sy2), 1)
        sw = math.sin(self.t * 2) * 3
        pygame.draw.line(surf, (40, 25, 15), (x, y - 4), (x + sw, y + 8), 1)
        pygame.draw.circle(surf, (200, 180, 60), (int(x + sw), y + 8), 2)

    def _draw_radio(self, surf, x, y):
        pygame.draw.rect(surf, (90, 60, 40), (x - 10, y - 4, 20, 12))
        pygame.draw.rect(surf, (40, 25, 15), (x - 10, y - 4, 20, 12), 1)
        pygame.draw.rect(surf, (20, 18, 22), (x - 8, y - 2, 12, 6))
        nx = x - 8 + int((math.sin(self.t * 0.6) + 1) * 6)
        pygame.draw.line(surf, (220, 60, 60), (nx, y - 2), (nx, y + 4), 1)

    def _draw_wrong_radio(self, surf, x, y):
        """A 1990s portable transistor radio sitting on a surface.
        Brown plastic body, chrome tuning dial, leather carry strap
        slumped beside it. The dial creeps clockwise on a slow cycle
        -- nobody is touching it. Visible static lines crawl across
        the speaker grille. Replaces or layers on top of the
        existing 'radio' deco when the wrongness should be visible."""
        body = (90, 60, 40)
        edge = (50, 32, 18)
        chrome = (180, 180, 200)
        # Body
        pygame.draw.rect(surf, body, (x - 10, y - 5, 20, 12))
        pygame.draw.rect(surf, edge, (x - 10, y - 5, 20, 12), 1)
        # Speaker grille (left side) with crawling static lines
        pygame.draw.rect(surf, (20, 18, 22), (x - 9, y - 3, 8, 8))
        rng_t = self.t * 6
        for i in range(3):
            sy = int(y - 3 + (rng_t + i * 3) % 8)
            pygame.draw.line(surf, (110, 130, 110),
                             (x - 8, sy), (x - 2, sy), 1)
        # Tuning dial (right side) -- needle creeps
        pygame.draw.rect(surf, (20, 18, 22), (x, y - 3, 8, 6))
        pygame.draw.line(surf, edge, (x, y), (x + 8, y), 1)
        needle_x = x + int((math.sin(self.t * 0.4 + self.seed) + 1) * 4)
        pygame.draw.line(surf, (220, 60, 60),
                         (needle_x, y - 3), (needle_x, y + 3), 1)
        # Antenna
        pygame.draw.line(surf, chrome, (x + 8, y - 5), (x + 12, y - 12), 1)
        # Carry strap slumped
        pygame.draw.line(surf, (50, 32, 18), (x - 10, y - 5), (x - 14, y), 1)

    def _draw_computer(self, surf, x, y):
        # Beige 1990s-era CRT on a small desk. Power LED blinks. Screen
        # shows a slow pulsing cursor / scanlines -- nothing readable yet
        # (the ARG content lives behind this for later).
        # Desk
        pygame.draw.rect(surf, (110, 80, 50), (x - 14, y + 4, 28, 10))
        pygame.draw.rect(surf, (60, 40, 25), (x - 14, y + 4, 28, 10), 1)
        # CRT body
        pygame.draw.rect(surf, (200, 190, 170), (x - 12, y - 14, 24, 18))
        pygame.draw.rect(surf, (110, 100, 90), (x - 12, y - 14, 24, 18), 1)
        # Screen
        pygame.draw.rect(surf, (10, 14, 20), (x - 9, y - 12, 18, 14))
        # Scanlines (animated)
        for i in range(3):
            ly = y - 11 + ((int(self.t * 8) + i * 4) % 12)
            pygame.draw.line(surf, (40, 80, 60), (x - 8, ly), (x + 8, ly), 1)
        # Cursor blink
        if int(self.t * 2) % 2 == 0:
            pygame.draw.rect(surf, (120, 220, 140), (x - 8, y - 4, 3, 2))
        # Power LED
        led = (220, 80, 60) if int(self.t * 3) % 2 == 0 else (120, 40, 30)
        pygame.draw.rect(surf, led, (x + 9, y + 5, 2, 2))

    def _draw_terminal(self, surf, x, y):
        pygame.draw.rect(surf, (10, 12, 14), (x - 12, y - 10, 24, 20))
        pygame.draw.rect(surf, (40, 40, 50), (x - 12, y - 10, 24, 20), 1)
        for i in range(5):
            ly = (y - 8 + i * 4 + int(self.t * 8)) % 16 + (y - 10)
            w = (self.seed + i * 31) % 12 + 4
            pygame.draw.line(surf, (50, 200, 80), (x - 10, ly), (x - 10 + w, ly), 1)

    def _draw_mirror(self, surf, x, y):
        """Wall-mounted mirror with a slim wood frame. The reflection
        shows a faint grey humanoid silhouette that doesn't match the
        room (no player, no NPC -- just an extra figure). On a slow
        per-seed cycle, the silhouette's position shifts by a pixel
        as if it stepped sideways while you weren't looking. The
        wrongness is small enough that the player questions whether
        they imagined it."""
        frame = (90, 60, 40)
        edge = (50, 32, 18)
        glass = (60, 70, 90)
        glass_hl = (110, 130, 160)
        # Frame
        pygame.draw.rect(surf, frame, (x - 7, y - 12, 14, 22))
        pygame.draw.rect(surf, edge, (x - 7, y - 12, 14, 22), 1)
        # Glass
        pygame.draw.rect(surf, glass, (x - 5, y - 10, 10, 18))
        # Reflection highlights (diagonal gleam)
        pygame.draw.line(surf, glass_hl,
                         (x - 4, y - 9), (x + 1, y - 4), 1)
        pygame.draw.line(surf, glass_hl,
                         (x + 1, y + 5), (x + 4, y + 2), 1)
        # The wrong silhouette inside the glass. Position shifts by 1
        # pixel on a slow cycle keyed to seed so each mirror has its
        # own anomaly schedule.
        cycle = 11.0
        local = (self.t + self.seed * 0.13) % cycle
        shift = -1 if local > (cycle / 2) else 1
        sil_col = (30, 28, 36)
        pygame.draw.rect(surf, sil_col,
                         (x - 2 + shift, y - 5, 3, 8))
        pygame.draw.circle(surf, sil_col,
                           (x - 1 + shift, y - 6), 1)
        # Eye-glints on the silhouette -- two pinprick whites that
        # only appear during the brief "wrong" window.
        if local < 0.4:
            try:
                surf.set_at((x - 2 + shift, y - 6), (240, 240, 240))
                surf.set_at((x + shift, y - 6), (240, 240, 240))
            except (IndexError, ValueError):
                pass

    def _draw_crate(self, surf, x, y):
        # Flat (pitch-0) fallback for the crate FURNITURE box -- it had
        # none and rendered as the magenta _draw_unknown square. A slatted
        # pine lid seen from above, cross-braced.
        w = int(self.kwargs.get("w", 30)); h = int(self.kwargs.get("h", 30))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (74, 52, 32), (rx, ry, w, h))             # lid
        pygame.draw.rect(surf, (34, 23, 13), (rx, ry, w, h), 1)
        pygame.draw.rect(surf, (96, 70, 44), (rx, ry, w, 2))             # lit back
        for gx in range(rx + 6, rx + w - 3, 7):                          # slats
            pygame.draw.line(surf, (56, 38, 22), (gx, ry + 2), (gx, ry + h - 3), 1)
        pygame.draw.line(surf, (46, 31, 18), (rx + 2, ry + 2),
                         (rx + w - 3, ry + h - 3), 1)                    # brace
        pygame.draw.line(surf, (46, 31, 18), (rx + w - 3, ry + 2),
                         (rx + 2, ry + h - 3), 1)

    def _draw_barrel(self, surf, x, y):
        # Flat fallback for the barrel FURNITURE volume (same magenta-square
        # gap): round top, iron hoop, sunken wet lid.
        r = max(8, int(self.kwargs.get("w", 26)) // 2)
        pygame.draw.circle(surf, (66, 46, 28), (x, y), r)                # staves
        pygame.draw.circle(surf, (30, 21, 12), (x, y), r, 1)
        pygame.draw.circle(surf, (96, 96, 104), (x, y), r - 2, 1)        # hoop
        pygame.draw.circle(surf, (44, 32, 20), (x, y), max(2, r - 4))    # sunken lid
        pygame.draw.circle(surf, (22, 17, 13), (x, y), max(1, r - 8))    # dark core
        pygame.draw.arc(surf, (104, 78, 50),
                        (x - r + 2, y - r + 2, (r - 2) * 2, (r - 2) * 2),
                        2.2, 3.4, 1)                                     # cold glint

    def _draw_bedroll(self, surf, x, y):
        # A laid-out bedroll at the cult camp: a worn wool mat, a folded
        # blanket, a rolled pillow at one end. A floor decal (warps flat onto
        # the ground under tilt) -- the newcomers rest here.
        pygame.draw.rect(surf, (78, 66, 52), (x - 15, y - 8, 30, 16),
                         border_radius=5)
        pygame.draw.rect(surf, (52, 43, 33), (x - 15, y - 8, 30, 16), 1,
                         border_radius=5)
        pygame.draw.rect(surf, (94, 42, 36), (x - 11, y - 5, 22, 10),
                         border_radius=4)          # the blanket
        pygame.draw.rect(surf, (58, 26, 23), (x - 11, y - 5, 22, 10), 1,
                         border_radius=4)
        pygame.draw.ellipse(surf, (112, 100, 84), (x - 15, y - 7, 9, 14))  # pillow roll
        pygame.draw.ellipse(surf, (70, 60, 48), (x - 15, y - 7, 9, 14), 1)

    def _draw_firewood(self, surf, x, y):
        # A stack of split logs -- pale ringed ends in a dark cradle.
        w = int(self.kwargs.get("w", 40)); h = int(self.kwargs.get("h", 24))
        rx, ry = x - w // 2, y - h // 2
        pygame.draw.rect(surf, (38, 27, 17), (rx, ry, w, h))
        pygame.draw.rect(surf, (24, 17, 10), (rx, ry, w, h), 1)
        r = 5
        row = 0
        oy = ry + r + 1
        while oy < ry + h - 1:
            cx = rx + r + 1 + (row % 2) * r
            while cx < rx + w - 1:
                pygame.draw.circle(surf, (92, 68, 44), (cx, oy), r)
                pygame.draw.circle(surf, (58, 40, 24), (cx, oy), r, 1)
                pygame.draw.circle(surf, (120, 92, 60), (cx, oy), max(1, r - 2), 1)
                cx += r * 2
            oy += r * 2 - 1
            row += 1

    def _draw_antler_rack(self, surf, x, y):
        # An antler/branch coat-rack: a post on a base, antler arms up
        # top, a dark wool coat hung from it.
        h = int(self.kwargs.get("h", 46))
        top = y - h // 2 + 6
        pygame.draw.ellipse(surf, (34, 24, 14), (x - 7, y + h // 2 - 8, 14, 7))  # base
        pygame.draw.rect(surf, (48, 34, 20), (x - 2, top, 4, h - 12))            # post
        for s in (-1, 1):
            pygame.draw.line(surf, (118, 106, 82), (x, top), (x + s * 9, top - 7), 2)
            pygame.draw.line(surf, (118, 106, 82), (x + s * 5, top - 3), (x + s * 8, top - 10), 1)
        coat = [(x - 7, top + 3), (x + 7, top + 3), (x + 5, y + 8), (x - 5, y + 8)]
        pygame.draw.polygon(surf, (46, 44, 50), coat)                           # hung coat
        pygame.draw.polygon(surf, (28, 26, 32), coat, 1)

    def _draw_chest(self, surf, x, y):
        # Wooden chest. Closed = lid down with a gold lock plate (and a
        # padlock if locked=True). Open = lid swung up and a dark
        # empty interior. State is driven by `open` (bool) and `locked`
        # (bool) kwargs; the scene's on_interact_fn flips `open` once
        # the chest has been emptied.
        open_state = self.kwargs.get("open", False)
        locked = self.kwargs.get("locked", False)
        # Body (lower half)
        pygame.draw.rect(surf, (110, 80, 50), (x - 9, y - 2, 18, 12))
        pygame.draw.rect(surf, (60, 40, 25), (x - 9, y - 2, 18, 12), 1)
        pygame.draw.line(surf, (40, 30, 20), (x - 9, y + 4),
                         (x + 9, y + 4), 1)
        if open_state:
            # Lid swung up, dark interior visible
            pygame.draw.polygon(surf, (130, 95, 60), [
                (x - 9, y - 2), (x - 9, y - 14),
                (x + 9, y - 14), (x + 9, y - 2),
            ])
            pygame.draw.polygon(surf, (60, 40, 25), [
                (x - 9, y - 2), (x - 9, y - 14),
                (x + 9, y - 14), (x + 9, y - 2),
            ], 1)
            pygame.draw.rect(surf, (10, 8, 6), (x - 6, y, 12, 6))
        else:
            # Lid closed
            pygame.draw.rect(surf, (130, 95, 60), (x - 9, y - 6, 18, 5))
            pygame.draw.rect(surf, (60, 40, 25), (x - 9, y - 6, 18, 5), 1)
            # Gold lock plate
            pygame.draw.rect(surf, (200, 180, 60), (x - 2, y - 3, 4, 5))
            pygame.draw.rect(surf, (40, 30, 20), (x - 2, y - 3, 4, 5), 1)
            if locked:
                # Iron padlock hanging from the plate
                pygame.draw.rect(surf, (60, 60, 70), (x - 1, y - 8, 2, 3))
                pygame.draw.circle(surf, (90, 90, 100), (x, y - 6), 2, 1)

    def _draw_rug(self, surf, x, y):
        """A worn area rug -- a multi-tile floor covering (w x h px via
        kwargs) that breaks up the plank grid. Faded field, a woven
        border, a centre motif, fringe at the ends, and a few worn
        patches. Drawn flat on the floor, under furniture/props."""
        w = int(self.kwargs.get("w", 88))
        h = int(self.kwargs.get("h", 60))
        base = self.kwargs.get("color", (96, 44, 46))
        border = tuple(min(255, int(c * 1.5) + 18) for c in base)
        dark = tuple(int(c * 0.6) for c in base)
        rx, ry = x - w // 2, y - h // 2
        sh = pygame.Surface((w + 10, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), (0, 0, w + 10, 16))
        surf.blit(sh, (rx - 5, ry + h - 8))
        pygame.draw.rect(surf, base, (rx, ry, w, h), border_radius=3)
        pygame.draw.rect(surf, dark, (rx, ry, w, h), 1, border_radius=3)
        pygame.draw.rect(surf, border, (rx + 3, ry + 3, w - 6, h - 6), 2)
        pygame.draw.polygon(surf, border, [
            (x, ry + 8), (rx + w - 8, y), (x, ry + h - 8), (rx + 8, y)], 1)
        pygame.draw.circle(surf, border, (x, y), 3, 1)
        for fxp in range(rx + 4, rx + w - 3, 5):       # fringe at the ends
            pygame.draw.line(surf, border, (fxp, ry - 2), (fxp, ry), 1)
            pygame.draw.line(surf, border, (fxp, ry + h), (fxp, ry + h + 2), 1)
        for i in range(3):                             # worn patches
            wx = rx + 6 + (self.seed * (i + 1)) % max(1, w - 12)
            wy = ry + 6 + (self.seed * (i + 3)) % max(1, h - 12)
            pygame.draw.rect(surf, dark, (wx, wy, 4, 3))

    def _draw_bowl(self, surf, x, y):
        # ceramic bowl on table — empty by default; if "filled" kwarg is True, contains an egg
        pygame.draw.ellipse(surf, (180, 170, 155), (x - 10, y - 4, 20, 10))
        pygame.draw.ellipse(surf, (130, 120, 110), (x - 10, y - 4, 20, 10), 1)
        pygame.draw.ellipse(surf, (60, 50, 45), (x - 8, y - 3, 16, 6))
        if self.kwargs.get("filled"):
            # painted egg in bowl
            cols = [(220, 80, 80), (80, 180, 220), (220, 200, 80)]
            pygame.draw.ellipse(surf, (240, 220, 200), (x - 5, y - 8, 10, 12))
            pygame.draw.ellipse(surf, cols[0], (x - 4, y - 6, 4, 2))
            pygame.draw.ellipse(surf, cols[1], (x, y - 4, 4, 2))
            pygame.draw.ellipse(surf, cols[2], (x - 3, y - 2, 4, 2))
