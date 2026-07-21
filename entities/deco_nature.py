"""Nature decoration draw methods (split from decoration.py 2026-07).

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


class DecoNatureMixin:
    def _draw_grain_heap(self, surf, x, y):
        pygame.draw.circle(surf, (150, 126, 70), (x, y), 13)
        pygame.draw.circle(surf, (80, 64, 35), (x, y), 13, 1)
        pygame.draw.circle(surf, (198, 174, 110), (x - 3, y - 3), 5)

    def _draw_garden_patch(self, surf, x, y):
        """A household vegetable plot dug into the lot -- the town feeding
        itself, unevenly (food scarcity, DESIGN.md §4). `tended=True` is a
        working bed: fresh-turned cold soil, straight furrows, a staked
        string line, the first pale hardy shoots. `tended=False` is the
        same plot let go: dried ridges gone to dashes, a stake fallen
        over, last year's weed stubble. Mid-April in the north; nothing
        here is ever lush."""
        rng = random.Random(self.seed)
        w = int(self.kwargs.get("w", 84)); h = int(self.kwargs.get("h", 56))
        tended = bool(self.kwargs.get("tended", True))
        rx, ry = x - w // 2, y - h // 2
        # value contrast does the work against the dark grass: turned earth
        # is near-black, every ridge catches a pale highlight
        soil = (30, 23, 16) if tended else (52, 45, 35)
        edge = (74, 58, 38) if tended else (66, 58, 45)
        pygame.draw.rect(surf, soil, (rx, ry, w, h), border_radius=6)   # the bed
        pygame.draw.rect(surf, edge, (rx, ry, w, h), 1, border_radius=6)
        rows = 4
        step_y = (h - 16) // (rows - 1)
        for i in range(rows):
            fy = ry + 8 + i * step_y
            if tended:
                pygame.draw.line(surf, (18, 13, 8),
                                 (rx + 6, fy), (rx + w - 6, fy), 2)     # furrow
                pygame.draw.line(surf, (88, 70, 46),
                                 (rx + 6, fy + 2), (rx + w - 6, fy + 2), 1)  # ridge light
            else:
                gx = rx + 6                     # collapsed furrow: broken dashes
                while gx < rx + w - 8:
                    seg = rng.randint(4, 10)
                    if rng.random() < 0.7:
                        pygame.draw.line(surf, (34, 28, 20), (gx, fy),
                                         (min(gx + seg, rx + w - 6), fy), 1)
                    gx += seg + rng.randint(2, 6)
        if tended:
            # stakes + a taut string along the first furrow, and the first
            # sparse cold-hardy shoots on the middle rows
            sy = ry + 8
            for sx in (rx + 8, rx + w - 8):
                pygame.draw.circle(surf, (112, 88, 56), (sx, sy), 2)
            pygame.draw.line(surf, (176, 164, 132),
                             (rx + 8, sy), (rx + w - 8, sy), 1)
            for i in (1, 2):
                fy = ry + 8 + i * step_y
                gx = rx + 8
                while gx < rx + w - 8:
                    if rng.random() < 0.55:
                        pygame.draw.line(surf, (108, 138, 82),
                                         (gx, fy - 1), (gx, fy - 4), 1)
                        pygame.draw.line(surf, (84, 112, 66),
                                         (gx + 1, fy - 1), (gx + 1, fy - 3), 1)
                    gx += rng.randint(4, 8)
        else:
            # a stake gone over, and last year's stubble through the beds
            pygame.draw.line(surf, (96, 76, 48),
                             (rx + w - 14, ry + 12), (rx + w - 5, ry + 6), 2)
            for _ in range(12):
                gx = rx + 6 + rng.randint(0, max(1, w - 12))
                gy = ry + 6 + rng.randint(0, max(1, h - 12))
                pygame.draw.line(surf, (118, 102, 66), (gx, gy),
                                 (gx + rng.randint(-2, 2),
                                  gy - rng.randint(2, 5)), 1)

    def _draw_log_seat(self, surf, x, y):
        """A felled log the cult camp sits on: bark-brown body, grooved bark,
        a pale ringed cut-end. A low floor decal (warps flat onto the ground
        under tilt)."""
        pygame.draw.rect(surf, (74, 56, 38), (x - 16, y - 6, 32, 12),
                         border_radius=5)
        pygame.draw.rect(surf, (42, 31, 21), (x - 16, y - 6, 32, 12), 1,
                         border_radius=5)
        for gx in range(-10, 12, 6):                      # bark grooves
            pygame.draw.line(surf, (52, 38, 26), (x + gx, y - 5),
                             (x + gx, y + 5), 1)
        pygame.draw.ellipse(surf, (150, 120, 82), (x + 11, y - 6, 8, 12))  # cut end
        pygame.draw.ellipse(surf, (96, 74, 48), (x + 11, y - 6, 8, 12), 1)
        pygame.draw.ellipse(surf, (120, 94, 62), (x + 13, y - 3, 4, 6), 1)  # rings

    def _draw_bush(self, surf, x, y):
        """A dense leafy bush -- walkable, but if the floor under it
        is corn-cover (':') the player hides in it. Used in the
        permeable forest band so the player can duck off a road and
        break sightlines. Rendered as a cluster of overlapping leafy
        blobs with edge highlights so it reads as foliage and not a
        small tree."""
        rng = random.Random(self.seed)
        # 4-7 overlapping ovals form the bush mass. Per-bush palette
        # variation so a band of these doesn't read as stamped.
        base_g = 70 + (rng.randint(-12, 12))
        leaf = (28, max(40, base_g - 12), 38)
        leaf_lit = (54, base_g + 10, 60)
        leaf_dark = (16, max(28, base_g - 24), 24)
        n = rng.randint(4, 7)
        # Drop shadow on the ground.
        shadow = pygame.Surface((28, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 28, 14))
        surf.blit(shadow, (x - 14, y + 4))
        # Leafy blobs, layered back-to-front.
        for i in range(n):
            ox = rng.randint(-9, 9)
            oy = rng.randint(-3, 1) - i // 2
            rx = rng.randint(7, 11)
            ry = rng.randint(5, 8)
            col = leaf_dark if i < n // 3 else leaf
            pygame.draw.ellipse(surf, col,
                                (x + ox - rx, y - 2 + oy - ry,
                                 rx * 2, ry * 2))
        # Upper-left highlights -- a few small lit ovals.
        for _ in range(2):
            ox = rng.randint(-6, 0)
            oy = rng.randint(-7, -3)
            pygame.draw.ellipse(surf, leaf_lit,
                                (x + ox - 4, y + oy - 2, 8, 4))

    def _draw_tall_grass(self, surf, x, y):
        """Knee-high grass clump -- decoration only, no gameplay effect.
        Five to seven stalks that sway out of phase, each ~14px tall.
        The clump's exact shape varies by `seed` so a meadow of these
        doesn't read as a stamped pattern."""
        rng = random.Random(self.seed)
        col_back = (38, 78, 46)
        col_front = (62, 118, 70)
        n = rng.randint(5, 8)
        base_sway = math.sin(self.t * 1.3 + self.seed) * 1.5
        for i in range(n):
            ox = rng.randint(-5, 5)
            height = rng.randint(10, 16)
            phase = self.seed * 0.13 + i * 0.7
            tip_sway = base_sway + math.sin(self.t * 1.8 + phase) * 1.2
            stalk_col = col_back if i < n // 2 else col_front
            pygame.draw.line(surf, stalk_col,
                             (x + ox, y + 4),
                             (x + ox + tip_sway, y + 4 - height), 1)

    def _draw_grass_tuft(self, surf, x, y):
        sway = math.sin(self.t * 2 + self.seed) * 1
        col = (50, 110, 60)
        for i in range(3):
            pygame.draw.line(surf, col,
                             (x - 2 + i * 2, y + 4),
                             (x - 2 + i * 2 + sway, y - 2 - i), 1)

    def _draw_hill_cap(self, surf, x, y):
        """Flat pitch-0 fallback for the unified grassy hilltop dome: a filled
        green ellipse with a lit crest. (The tilt view draws it as a real domed
        cap over the mound top via rendering/props.py.)"""
        rx = int(self.kwargs.get("rx", 100) * 0.7)
        ry = int(self.kwargs.get("ry", 88) * 0.5)
        pygame.draw.ellipse(surf, (40, 70, 33), (x - rx, y - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(surf, (72, 104, 54),
                            (x - rx // 2, y - ry // 2, rx, ry))

    def _draw_corn_doll(self, surf, x, y):
        """A small corn-husk effigy -- bundled stalks tied at the
        waist with twine, vaguely humanoid. The cult's curse-work
        tool. Specific to the cornfield maze; doesn't appear
        anywhere else. ~16px tall on the ground."""
        rng = random.Random(self.seed)
        # Drop shadow.
        sh = pygame.Surface((14, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 14, 6))
        surf.blit(sh, (x - 7, y + 4))
        husk = (162, 138, 84)
        husk_dark = (108, 86, 48)
        twine = (74, 50, 28)
        # Body: a wedge of husks, wider at the bottom (skirt).
        pygame.draw.polygon(surf, husk_dark, [
            (x - 5, y + 4), (x + 5, y + 4),
            (x + 3, y - 6), (x - 3, y - 6)])
        pygame.draw.polygon(surf, husk, [
            (x - 4, y + 4), (x + 4, y + 4),
            (x + 2, y - 5), (x - 2, y - 5)])
        # Husk strands at the base
        for i in (-3, 0, 3):
            pygame.draw.line(surf, husk_dark,
                             (x + i, y + 4), (x + i + rng.randint(-1, 1),
                                              y + 8), 1)
        # Waist twine
        pygame.draw.line(surf, twine,
                         (x - 4, y), (x + 4, y), 1)
        # Head -- a tied bundle, small.
        pygame.draw.circle(surf, husk_dark, (x, y - 8), 3)
        pygame.draw.circle(surf, husk, (x - 1, y - 9), 2)
        # Crooked stick arms
        pygame.draw.line(surf, husk_dark,
                         (x - 4, y - 3), (x - 7, y), 1)
        pygame.draw.line(surf, husk_dark,
                         (x + 4, y - 3), (x + 7, y - 2), 1)
        # Tiny dark eye -- not always present.
        if rng.random() < 0.6:
            ex = x + rng.choice((-1, 1))
            pygame.draw.line(surf, (10, 8, 4),
                             (ex, y - 8), (ex, y - 7), 1)

    def _draw_corn_altar(self, surf, x, y):
        """A small ritual mound -- cobs stacked on a base of crossed
        husk-stalks, with a half-burned candle stub on top. The
        cult's offering. Maze-specific."""
        # Drop shadow
        sh = pygame.Surface((22, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 100), (0, 0, 22, 8))
        surf.blit(sh, (x - 11, y + 4))
        stalk = (96, 80, 44)
        stalk_lit = (130, 110, 64)
        cob = (218, 192, 88)
        cob_dark = (160, 130, 56)
        kernel = (250, 226, 130)
        # Two crossed stalks at the base
        pygame.draw.line(surf, stalk, (x - 9, y + 6), (x + 9, y - 2), 2)
        pygame.draw.line(surf, stalk, (x + 9, y + 6), (x - 9, y - 2), 2)
        pygame.draw.line(surf, stalk_lit, (x - 9, y + 5),
                         (x + 9, y - 3), 1)
        # Three cobs stacked
        for i, (ox, oy, rx, ry) in enumerate(
                [(-3, 0, 4, 2), (3, -1, 4, 2), (0, -4, 4, 2)]):
            pygame.draw.ellipse(surf, cob_dark,
                                (x + ox - rx, y + oy - ry,
                                 rx * 2, ry * 2))
            pygame.draw.ellipse(surf, cob,
                                (x + ox - rx + 1, y + oy - ry,
                                 rx * 2 - 2, ry * 2 - 1))
            # Kernel highlights
            for kx in (-1, 1):
                pygame.draw.line(surf, kernel,
                                 (x + ox + kx, y + oy - 1),
                                 (x + ox + kx, y + oy), 1)
        # Candle stub on top with a tiny flame
        pygame.draw.rect(surf, (208, 200, 178),
                         (x - 1, y - 8, 2, 4))
        # Flame
        flick = math.sin(self.t * 6 + self.seed) * 0.5
        pygame.draw.line(surf, (240, 184, 80),
                         (x, y - 9), (x + int(flick), y - 11), 1)

    def _draw_stalk_marker(self, surf, x, y):
        """A single corn stalk standing taller than the rest with a
        strip of cloth tied around it and a small dark token hung
        from the cloth. The cult marks the next to be taken. Maze-
        specific. Sways slightly."""
        sway = math.sin(self.t * 1.4 + self.seed * 0.13) * 1.6
        # Drop shadow
        sh = pygame.Surface((10, 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), (0, 0, 10, 4))
        surf.blit(sh, (x - 5, y + 4))
        # Tall stalk
        stalk = (74, 102, 50)
        stalk_dark = (44, 64, 30)
        tip_x = x + int(sway)
        pygame.draw.line(surf, stalk_dark, (x, y + 4), (tip_x, y - 18), 2)
        pygame.draw.line(surf, stalk, (x - 1, y + 4),
                         (tip_x - 1, y - 18), 1)
        # A frayed husk leaf at mid-height
        leaf_x = x + int(sway * 0.5) - 4
        leaf_y = y - 6
        pygame.draw.line(surf, stalk_dark, (x - 1, y - 4),
                         (leaf_x, leaf_y), 1)
        pygame.draw.line(surf, stalk_dark, (x + 1, y - 4),
                         (leaf_x + 8, leaf_y - 1), 1)
        # Cloth strip around the upper third, sun-bleached red
        cloth = (164, 80, 60)
        cloth_dark = (100, 44, 36)
        pygame.draw.rect(surf, cloth_dark,
                         (tip_x - 4, y - 14, 8, 4))
        pygame.draw.rect(surf, cloth,
                         (tip_x - 3, y - 14, 7, 3))
        # A small dark token dangling from the cloth -- could be a
        # locket, a key, a tooth. Player fills in.
        pygame.draw.line(surf, (40, 32, 24),
                         (tip_x + 1, y - 10), (tip_x + 1, y - 6), 1)
        pygame.draw.circle(surf, (32, 26, 20),
                           (tip_x + 1, y - 5), 1)

    def _draw_creepy_tree(self, surf, x, y):
        """A leafless, gnarled tree. The trunk leans slightly off
        vertical so it never lines up with the regular trees on the
        same row -- a wrongness the player feels before they see it.
        Two darker oblong gouges in the bark sit where eyes would be,
        and a vertical gash beneath them suggests a pulled-open mouth.
        Branches splay outward like fingers, bare of all leaves."""
        trunk = (38, 28, 20)
        bark = (24, 16, 12)
        knot = (10, 6, 6)
        # Slow wind: the bare crown bends from a fixed base, branches
        # creaking sideways -- a dead tree working in the wind.
        sw = int(math.sin(self.t * 0.6 + self.seed) * 1.7)
        xt = x + sw
        # Leaning trunk -- base fixed at x, crown swayed to xt
        pygame.draw.polygon(surf, trunk, [
            (x - 4, y + 12), (xt - 5, y - 18),
            (xt + 4, y - 18), (x + 3, y + 12),
        ])
        pygame.draw.polygon(surf, bark, [
            (x - 4, y + 12), (xt - 5, y - 18),
            (xt + 4, y - 18), (x + 3, y + 12),
        ], 1)
        # Vertical bark cracks
        pygame.draw.line(surf, knot, (xt - 1, y - 16), (x - 2, y + 8), 1)
        pygame.draw.line(surf, knot, (xt + 1, y - 12), (x + 2, y + 4), 1)
        # Face in the bark -- eye gouges
        pygame.draw.ellipse(surf, knot, (xt - 3, y - 10, 2, 3))
        pygame.draw.ellipse(surf, knot, (xt + 1, y - 10, 2, 3))
        # Mouth gash (two stacked lines so it reads as torn-open)
        pygame.draw.line(surf, knot, (xt - 2, y - 4), (xt + 2, y - 4), 1)
        pygame.draw.line(surf, knot, (xt - 1, y - 3), (xt + 1, y - 3), 1)
        # Bare finger-branches
        for s, m, t in [
            ((xt, y - 16), (xt - 12, y - 22), (xt - 18, y - 18)),
            ((xt, y - 16), (xt + 12, y - 22), (xt + 18, y - 16)),
            ((xt, y - 18), (xt - 6, y - 28), (xt - 4, y - 36)),
            ((xt, y - 18), (xt + 6, y - 28), (xt + 4, y - 36)),
            ((xt, y - 18), (xt, y - 32), (xt + 2, y - 38)),
        ]:
            pygame.draw.line(surf, bark, s, m, 2)
            pygame.draw.line(surf, bark, m, t, 1)
        # Twigs at branch tips so they read as fingers, not sticks
        for tx_, ty_, dx_ in [(-18, -18, -1), (18, -16, 1),
                               (-4, -36, -1), (4, -36, 1), (2, -38, 1)]:
            pygame.draw.line(surf, bark,
                             (xt + tx_, y + ty_),
                             (xt + tx_ + dx_, y + ty_ - 3), 1)

    def _draw_crow(self, surf, x, y):
        # The noise-trap flush (Game._trip_noise_traps sets flushed_at):
        # the bird bursts up and away over ~0.9s, wings as alternating
        # chevrons, then the decoration hides -- the crow is gone for
        # the rest of the scene load.
        flushed = getattr(self, "flushed_at", None)
        if flushed is not None:
            el = self.t - flushed
            if el > 0.9:
                self.hidden = True
                return
            k = el / 0.9
            fx = x + int(k * k * 46) * (1 if (self.seed % 2) else -1)
            fy = y - int(k * 60)
            spread = 6 if math.sin(el * 22.0) > 0 else 2
            col = (10, 10, 14)
            pygame.draw.line(surf, col, (fx - spread, fy - 2), (fx, fy), 2)
            pygame.draw.line(surf, col, (fx + spread, fy - 2), (fx, fy), 2)
            pygame.draw.circle(surf, col, (fx, fy), 2)
            return
        hop = int(abs(math.sin(self.t * 0.8)) * 1)
        head_turn = int(math.sin(self.t * 0.5) * 2)
        # Body
        pygame.draw.ellipse(surf, (10, 10, 14), (x - 5, y - 2 - hop, 10, 6))
        # Anomaly: at a rare per-seed phase, the head is flipped to
        # the OPPOSITE side of the body -- the crow is looking
        # backwards. Held for ~120ms (~one stale frame) so the
        # player only catches it if they happen to look at this crow
        # during that window.
        anomaly_phase = (self.t + self.seed * 0.13) % 9.0
        looking_back = anomaly_phase > 8.88
        if looking_back:
            head_x = x - 4 - head_turn
            eye_x = x - 5 - head_turn
        else:
            head_x = x + 4 + head_turn
            eye_x = x + 5 + head_turn
        pygame.draw.circle(surf, (10, 10, 14), (head_x, y - 4 - hop), 2)
        pygame.draw.circle(surf, (220, 200, 50), (eye_x, y - 4 - hop), 1)

    def _draw_dead_crow(self, surf, x, y):
        """A crow lying on its side -- one stiff leg pointing up, wing
        splayed, glazed-film eye. A few loose feathers around it.
        Static. Read as a dead bird, not a sleeping one."""
        # Body
        pygame.draw.ellipse(surf, (8, 8, 12), (x - 6, y - 1, 12, 5))
        pygame.draw.ellipse(surf, (16, 16, 20), (x - 6, y - 1, 12, 5), 1)
        # Head turned away with film-eye
        pygame.draw.circle(surf, (8, 8, 12), (x - 7, y), 2)
        pygame.draw.circle(surf, (90, 90, 70), (x - 8, y), 1)
        # Stiff leg sticking up + foot
        pygame.draw.line(surf, (40, 30, 20), (x + 2, y - 1), (x + 2, y - 6), 1)
        pygame.draw.line(surf, (40, 30, 20), (x + 2, y - 6), (x + 4, y - 7), 1)
        # Splayed wing
        pygame.draw.polygon(surf, (4, 4, 8),
                            [(x + 1, y - 1), (x + 7, y - 4),
                             (x + 6, y), (x + 1, y + 1)])
        # Loose feathers
        for fx, fy in [(-9, 4), (8, 4), (-3, 5)]:
            pygame.draw.line(surf, (8, 8, 12),
                             (x + fx, y + fy),
                             (x + fx + 1, y + fy - 2), 1)

    def _draw_stalagmite(self, surf, x, y):
        """A wet limestone spike rising from the cave floor. Flat pitch-0 fallback
        -- the tilt view draws it as a real tapered cone via rendering/props.py.
        Girth + height vary by seed so a field of them never reads as a stamp."""
        R = 5 + (self.seed % 5)
        H = 18 + (self.seed % 16)
        lean = (self.seed % 7) - 3
        base = (92, 92, 98)
        lite = (140, 142, 150)
        dk = (52, 52, 58)
        tip = (x + lean // 2, y - H)
        pygame.draw.polygon(surf, base,
                            [(x - R, y + 6), (x + R, y + 6), tip])
        pygame.draw.polygon(surf, dk,
                            [(x - R, y + 6), (x + R, y + 6), tip], 1)
        pygame.draw.line(surf, lite, (x - 1, y + 4), tip, 1)
        _ground_shadow(surf, x, y + 6, R + 1, 3, 70)

    def _draw_husk_bundle(self, surf, x, y):
        """A tied sheaf of dried corn husks / reeds -- a STOOK: stalks
        rising from a spread base, cinched to a visible WAIST by twine,
        the tops splaying out and drooping past the tie. The waist is
        the read (2026-07: the old draw fanned every blade up from one
        point, and the resulting pale cone kept being mistaken for a
        stalagmite under the tilt)."""
        base = (140, 124, 80)
        blade = (166, 150, 104)
        dk = (100, 87, 52)
        twine = (114, 84, 46)
        wy = y - 8                                   # the waist height
        # lower body: stalks from a spread base gathering to the waist
        for dx in (-6, -3, 0, 3, 6):
            pygame.draw.line(surf, base if dx % 2 else dk,
                             (x + dx, y + 6), (x + dx // 3, wy), 2)
        # upper heads: splay OUT from the waist, outermost tips drooping
        for i, (ox, oy) in enumerate(((-9, -8), (-4, -12), (0, -13),
                                      (4, -12), (9, -8))):
            col = blade if i % 2 else base
            droop = 4 if abs(ox) > 6 else 1
            mid = (x + ox // 2, wy + oy // 2 - 2)
            tip = (x + ox, wy + oy + droop)
            pygame.draw.line(surf, col, (x, wy), mid, 2)
            pygame.draw.line(surf, col, mid, tip, 1)
        # the twine cinch -- the visible waist
        pygame.draw.line(surf, twine, (x - 4, wy), (x + 4, wy), 3)
        pygame.draw.line(surf, (66, 48, 28), (x - 4, wy + 2), (x + 4, wy + 2), 1)

    def _draw_spoil_heap(self, surf, x, y):
        # top-down: a shoveled earth mound with stones caught in it
        pygame.draw.circle(surf, (92, 80, 62), (x, y), 13)
        pygame.draw.circle(surf, (54, 46, 36), (x, y), 13, 1)
        pygame.draw.circle(surf, (120, 106, 84), (x - 3, y - 3), 5)
        for ox, oy in ((-6, 4), (5, -2), (2, 7)):
            pygame.draw.circle(surf, (120, 118, 122), (x + ox, y + oy), 1)

    def _draw_cobweb(self, surf, x, y):
        # A faint corner cobweb: radial threads + a few connecting arcs.
        # `ang` kwarg points it into the corner it hangs from.
        col = (118, 118, 130)
        base = self.kwargs.get("ang", 0.0)
        span = math.pi / 2
        n = 5
        R = int(self.kwargs.get("r", 17))
        for i in range(n):
            a = base + span * (i / (n - 1))
            pygame.draw.line(surf, col, (x, y),
                             (int(x + math.cos(a) * R), int(y + math.sin(a) * R)), 1)
        for ring in (R // 3, 2 * R // 3, R - 1):
            pts = [(int(x + math.cos(base + span * (i / (n - 1))) * ring),
                    int(y + math.sin(base + span * (i / (n - 1))) * ring))
                   for i in range(n)]
            pygame.draw.lines(surf, col, False, pts, 1)

    def _draw_wheelbarrow(self, surf, x, y):
        """Single-wheel wooden wheelbarrow seen from a 3/4 angle.
        Loaded with a small pile of rusted hand tools (claw hammer
        head, bent wrench, the tip of a saw). The tools are
        deliberately drawn looking dirty/old at distance, but the
        scene's interaction text ('these have been recently
        cleaned') contradicts what the player is seeing -- the
        horror is in the contradiction. Static, not animated."""
        # Tray (the bucket of the wheelbarrow). Trapezoid with a
        # darker rim. Brown weathered wood.
        tray_top_w = 26
        tray_bot_w = 18
        tray_h = 10
        tray_top_y = y - 4
        # Use polygon for the trapezoid silhouette.
        pygame.draw.polygon(surf, (110, 78, 50), [
            (x - tray_top_w // 2, tray_top_y),
            (x + tray_top_w // 2, tray_top_y),
            (x + tray_bot_w // 2, tray_top_y + tray_h),
            (x - tray_bot_w // 2, tray_top_y + tray_h),
        ])
        pygame.draw.polygon(surf, (60, 40, 24), [
            (x - tray_top_w // 2, tray_top_y),
            (x + tray_top_w // 2, tray_top_y),
            (x + tray_bot_w // 2, tray_top_y + tray_h),
            (x - tray_bot_w // 2, tray_top_y + tray_h),
        ], 1)
        # Plank seam across the tray.
        pygame.draw.line(surf, (60, 40, 24),
                         (x - tray_top_w // 2 + 2, tray_top_y + tray_h // 2),
                         (x + tray_top_w // 2 - 2, tray_top_y + tray_h // 2), 1)
        # Two front legs poking down past the tray.
        pygame.draw.rect(surf, (60, 40, 24), (x - 9, tray_top_y + tray_h, 2, 5))
        pygame.draw.rect(surf, (60, 40, 24), (x + 7, tray_top_y + tray_h, 2, 5))
        # Wheel out the front.
        pygame.draw.circle(surf, (40, 28, 20), (x - 12, y + 3), 4)
        pygame.draw.circle(surf, (16, 12, 10), (x - 12, y + 3), 4, 1)
        pygame.draw.line(surf, (90, 70, 50), (x - 16, y + 3),
                         (x - 8, y + 3), 1)
        # Long handle running back-right (the user's grip end).
        pygame.draw.line(surf, (90, 60, 36),
                         (x + 12, y), (x + 18, y + 5), 2)
        # Tools poking out of the tray. Rusty steel + dark wood.
        # Hammer head (rectangular block with a dark eye for the haft).
        pygame.draw.rect(surf, (130, 90, 70), (x - 4, tray_top_y - 4, 5, 4))
        pygame.draw.rect(surf, (60, 40, 30), (x - 4, tray_top_y - 4, 5, 4), 1)
        pygame.draw.rect(surf, (60, 40, 30), (x - 2, tray_top_y - 3, 1, 2))
        # Wrench at an angle (a bent steel rod with a notched head).
        pygame.draw.line(surf, (140, 110, 90),
                         (x + 2, tray_top_y - 2),
                         (x + 9, tray_top_y - 6), 2)
        pygame.draw.rect(surf, (140, 110, 90),
                         (x + 8, tray_top_y - 8, 3, 4))
        pygame.draw.rect(surf, (60, 40, 30),
                         (x + 8, tray_top_y - 8, 3, 4), 1)
        # Saw tip protruding (a small triangle of toothed steel).
        pygame.draw.polygon(surf, (170, 150, 140), [
            (x - 8, tray_top_y - 1),
            (x - 1, tray_top_y - 6),
            (x - 1, tray_top_y - 4),
        ])
        # Rust streaks down the tray face.
        pygame.draw.line(surf, (130, 60, 30),
                         (x - 6, tray_top_y + 2),
                         (x - 5, tray_top_y + tray_h - 1), 1)
        pygame.draw.line(surf, (130, 60, 30),
                         (x + 4, tray_top_y + 1),
                         (x + 4, tray_top_y + tray_h - 1), 1)
