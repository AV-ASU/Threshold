"""Lighting decoration draw methods (split from decoration.py 2026-07).

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


class DecoLightingMixin:
    def _draw_wall_torch(self, surf, x, y):
        # A wall sconce: an iron bracket rising off the wall with a guttering
        # flame at the top. The ROOM lighting is punched by Game._draw_dark
        # (which finds wall_torch decos); this is the visible fixture + a tight
        # flame halo. Drawn tall and anchored at the wall base so the billboard
        # reads as mounted up the wall.
        _light_pool(surf, x, y - 16, 28, (255, 170, 80), 78)
        pygame.draw.line(surf, (38, 34, 36), (x, y), (x, y - 14), 3)          # iron post
        pygame.draw.line(surf, (62, 56, 50), (x - 3, y - 14), (x + 3, y - 14), 2)  # cup
        f = math.sin(self.t * 16) + (random.random() - 0.5)
        fh = 11 + f * 2.2
        bx = x + int(math.sin(self.t * 9) * 1.2)                             # waver
        top = int(y - 15 - fh)
        pygame.draw.ellipse(surf, (190, 70, 24), (bx - 4, top, 8, int(fh)))           # ember
        pygame.draw.ellipse(surf, (245, 165, 48),
                            (bx - 3, int(y - 14 - fh * 0.78), 6, int(fh * 0.78)))     # body
        pygame.draw.ellipse(surf, (255, 236, 175),
                            (bx - 1, int(y - 13 - fh * 0.45), 3, int(fh * 0.45)))     # core

    def _draw_candle(self, surf, x, y):
        _light_pool(surf, x, y - 2, 30, (255, 170, 80), 58)
        pygame.draw.rect(surf, (180, 180, 200), (x - 2, y, 4, 8))
        pygame.draw.rect(surf, (240, 230, 200), (x - 1, y - 4, 2, 4))
        f_h = 6 + math.sin(self.t * 18) * 1 + (random.random() - 0.5)
        f_w = 3 + math.sin(self.t * 13) * 0.5
        # Optional scripted dip: the flame nearly snuffs and re-grows
        # over ~0.7s when something passes the candle (the opening
        # watcher manifestation cue). Set kwargs["dip_t0"] = time.time()
        # to fire. Outside the dip window the candle is unchanged.
        dip_t0 = self.kwargs.get("dip_t0", 0.0)
        if dip_t0:
            elapsed = time.time() - dip_t0
            if 0.0 <= elapsed < 0.7:
                if elapsed < 0.15:
                    dim = 1.0 - (elapsed / 0.15) * 0.70
                else:
                    dim = 0.30 + 0.70 * ((elapsed - 0.15) / 0.55)
                f_h *= dim
                f_w *= dim
        pygame.draw.polygon(surf, (255, 200, 80), [(x, y - 4 - f_h), (x - f_w, y - 4), (x + f_w, y - 4)])
        pygame.draw.polygon(surf, (255, 240, 180),
                            [(x, y - 4 - f_h * 0.7), (x - f_w * 0.5, y - 4), (x + f_w * 0.5, y - 4)])

    def _draw_lantern(self, surf, x, y):
        # Lamppost: vertical iron pole grounded at y+18, cross-arm at the
        # top, lantern hangs from the arm tip. Earlier rounds drew only
        # the lantern + a stub of chain, which read as floating in the
        # corridor. The pole anchors it to the ground.
        _light_pool(surf, x + 8, y, 40, (255, 175, 80), 72)
        ground_y = y + 18
        top_y = y - 22
        # vertical pole
        pygame.draw.line(surf, (50, 50, 60), (x, ground_y), (x, top_y), 2)
        # base flare
        pygame.draw.rect(surf, (50, 50, 60), (x - 3, ground_y - 1, 7, 3))
        # cross-arm reaching right to where the lantern hangs
        pygame.draw.line(surf, (50, 50, 60), (x, top_y), (x + 8, top_y), 2)
        sway = math.sin(self.t * 1.2 + self.seed) * 1
        # short chain from arm tip down to lantern body
        pygame.draw.line(surf, (60, 60, 70),
                         (x + 8, top_y),
                         (x + 8 + sway, y - 6), 1)
        # lantern body
        pygame.draw.rect(surf, (80, 60, 30), (x + 3 + sway, y - 6, 10, 12))
        flick = (255, 200 + int(math.sin(self.t * 20) * 20), 80)
        pygame.draw.rect(surf, flick, (x + 5 + sway, y - 4, 6, 8))

    def _draw_kerosene_lamp(self, surf, x, y):
        # A brass oil lamp: warm pool, a fuel font, a glass chimney, flame.
        _light_pool(surf, x, y - 4, 30, (255, 168, 80), 60)
        pygame.draw.rect(surf, (96, 74, 40), (x - 5, y + 3, 10, 4))        # base
        pygame.draw.polygon(surf, (120, 96, 56),
                            [(x - 4, y + 3), (x + 4, y + 3), (x + 2, y - 3), (x - 2, y - 3)])  # font
        chim = pygame.Surface((10, 12), pygame.SRCALPHA)
        pygame.draw.polygon(chim, (210, 196, 150, 80), [(2, 11), (8, 11), (7, 0), (3, 0)])
        surf.blit(chim, (x - 5, y - 15))
        fh = 5 + math.sin(self.t * 16 + self.seed) * 1.2
        pygame.draw.polygon(surf, (255, 206, 96),
                            [(x, int(y - 4 - fh)), (x - 2, y - 4), (x + 2, y - 4)])

    def _draw_brazier(self, surf, x, y):
        """A cult fire-bowl on an iron tripod -- a warm focal light at a
        ritual site, the flame guttering. Pools of fire are the only
        warmth out here, and the eye goes straight to them."""
        _light_pool(surf, x, y - 6, 40, (255, 150, 56), 82)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x - 6, y + 11), 2)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x + 6, y + 11), 2)
        pygame.draw.line(surf, (28, 26, 30), (x, y - 2), (x, y + 12), 2)
        pygame.draw.ellipse(surf, (42, 40, 44), (x - 9, y - 5, 18, 8))
        pygame.draw.ellipse(surf, (18, 16, 20), (x - 7, y - 4, 14, 5))
        t = self.t * 6 + self.seed
        fh = 8 + int(math.sin(t) * 3)
        pygame.draw.polygon(surf, (208, 88, 28),
                            [(x, y - 5 - fh), (x - 5, y - 3), (x + 5, y - 3)])
        pygame.draw.polygon(surf, (250, 178, 68),
                            [(x, y - 4 - int(fh * 0.6)), (x - 3, y - 3), (x + 3, y - 3)])

    def _draw_campfire(self, surf, x, y):
        """The cold remnants of a campfire built INSIDE -- a scorch scar burned
        into the floorboards, grey ash, charred crossed logs, a ring of stones,
        long dead but for one last dull ember. A floor decal."""
        pygame.draw.ellipse(surf, (20, 16, 14), (x - 15, y - 12, 30, 24))   # scorch
        pygame.draw.ellipse(surf, (40, 34, 28), (x - 15, y - 12, 30, 24), 1)
        pygame.draw.ellipse(surf, (74, 70, 66), (x - 9, y - 7, 18, 14))     # ash bed
        pygame.draw.ellipse(surf, (96, 92, 88), (x - 5, y - 4, 9, 7))
        pygame.draw.line(surf, (30, 22, 18), (x - 8, y - 5), (x + 8, y + 5), 3)  # logs
        pygame.draw.line(surf, (30, 22, 18), (x + 8, y - 5), (x - 8, y + 5), 3)
        pygame.draw.line(surf, (54, 40, 30), (x - 8, y - 5), (x + 8, y + 5), 1)
        for i in range(8):                                                 # ring of stones
            a = i * 0.785
            sx = int(x + math.cos(a) * 13); sy = int(y + math.sin(a) * 10)
            pygame.draw.circle(surf, (112, 110, 114), (sx, sy), 2)
            pygame.draw.circle(surf, (70, 68, 72), (sx, sy), 2, 1)
        e = 0.5 + 0.5 * math.sin(self.t * 2.0)                             # last dull ember
        pygame.draw.circle(surf, (int(110 + 70 * e), 48, 22), (x, y), 1)

    def _draw_smoke(self, surf, x, y):
        for i in range(4):
            phase = (self.t * 0.6 + i * 0.4 + self.seed * 0.1) % 1.0
            ox = math.sin(phase * 6 + self.seed) * 3
            oy = -phase * 36
            r = int(4 + phase * 6)
            alpha = int((1 - phase) * 130)
            puff = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(puff, (160, 160, 170, alpha), (r + 1, r + 1), r)
            surf.blit(puff, (x + ox - r, y + oy - r))

    def _draw_mist(self, surf, x, y):
        """Low ground fog -- soft translucent pools that breathe and
        slide on the wind. Sized via kwargs w/h; laid over the water and
        the marsh so the fog clings to the wet ground."""
        ww = self.kwargs.get("w", 96)
        hh = self.kwargs.get("h", 48)
        drift = int(math.sin(self.t * 0.18 + self.seed) * 10)
        breath = 1.0 + math.sin(self.t * 0.25 + self.seed * 0.5) * 0.12
        pad = 30
        fog = pygame.Surface((ww + pad * 2, hh + pad * 2), pygame.SRCALPHA)
        rng = random.Random(self.seed)
        for _ in range(5):
            ew = int(rng.randint(ww // 2, ww) * breath)
            eh = int(rng.randint(hh // 2, hh) * breath)
            ox = pad + rng.randint(-ww // 4, ww // 4) + (ww - ew) // 2
            oy = pad + rng.randint(-hh // 4, hh // 4) + (hh - eh) // 2
            pygame.draw.ellipse(fog, (150, 156, 162, 22), (ox, oy, ew, eh))
        surf.blit(fog, (x - ww // 2 - pad + drift, y - hh // 2 - pad))

    def _draw_mote(self, surf, x, y):
        dx = math.sin(self.t * 0.4 + self.seed) * 8
        dy = math.cos(self.t * 0.3 + self.seed * 0.7) * 4
        col = (200, 200, 220)
        try:
            surf.set_at((int(x + dx), int(y + dy)), col)
            surf.set_at((int(x + dx + 1), int(y + dy)), col)
        except (IndexError, ValueError):
            pass

    def _draw_wisp(self, surf, x, y):
        """A will-o'-the-wisp -- a small cold pale glow drifting low over
        the bog. Marsh gas, or something out there carrying a light."""
        cx = int(x + math.sin(self.t * 0.5 + self.seed) * 14)
        cy = int(y + math.cos(self.t * 0.37 + self.seed * 0.6) * 8)
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(glow, (110, 168, 146, 38), (11, 11), 10)
        pygame.draw.circle(glow, (150, 200, 174, 70), (11, 11), 5)
        surf.blit(glow, (cx - 11, cy - 11))
        try:
            surf.set_at((cx, cy), (210, 235, 220))
        except (IndexError, ValueError):
            pass

    def _draw_leaves(self, surf, x, y):
        """Dead leaves and grit tumbling across the ground on the wind --
        a low, restless drift that loops near the anchor."""
        cols = [(86, 68, 40), (70, 56, 34), (54, 60, 36), (60, 48, 30)]
        for i in range(4 + (self.seed % 4)):
            ph = self.t * 0.6 + i * 0.9 + self.seed
            dx = math.sin(ph) * 16 + ((self.t * 9 + i * 19) % 74) - 37
            dy = math.cos(ph * 1.3) * 9 + math.sin(ph * 0.5) * 4
            sz = 1 + (i & 1)
            pygame.draw.rect(surf, cols[i % 4], (int(x + dx), int(y + dy), sz, sz))

    def _draw_flock(self, surf, x, y):
        """A few distant birds drifting across the grey, wings beating.
        Loops slowly so the sky is never quite still. `span`/`speed`
        kwargs tune the drift."""
        span = self.kwargs.get("span", 180)
        speed = self.kwargs.get("speed", 0.5)
        lead = ((self.t * speed * 16 + self.seed * 7) % (span + 60)) - 30
        n = 3 + (self.seed % 3)
        for i in range(n):
            bx = int(x + lead - i * (11 + (self.seed + i) % 8))
            by = int(y + (i % 3 - 1) * 8 + math.sin(self.t * 0.6 + i) * 3)
            flap = int(math.sin(self.t * 6 + i * 1.3) * 4)
            # ground shadow offset below -> reads as flying above the field
            pygame.draw.line(surf, (10, 12, 15), (bx - 4, by + 11),
                             (bx, by + 9), 1)
            pygame.draw.line(surf, (10, 12, 15), (bx + 4, by + 11),
                             (bx, by + 9), 1)
            col = (52, 52, 60)                            # lit-from-above silhouette
            pygame.draw.line(surf, col, (bx - 5, by + flap), (bx, by), 2)
            pygame.draw.line(surf, col, (bx + 5, by + flap), (bx, by), 2)

    def _draw_swallow_hole(self, surf, x, y):
        """A sink where the river spirals down into the earth and is gone --
        the underground river's mouth (NARRATIVE 1b: the river is the artery;
        water finds the lowest place and creeps to the door). Depth rings that
        darken to black at the centre + a slow draining swirl. Used on the
        surface (the river vanishes here) and in the Sump (the same artery,
        deeper). `scale` kwarg sizes it."""
        # wet stone rim, irregular
        pygame.draw.ellipse(surf, (40, 42, 40), (x - 17, y - 12, 34, 24))
        pygame.draw.ellipse(surf, (62, 64, 60), (x - 17, y - 12, 34, 24), 1)
        # depth rings: water -> near-black at the centre (it goes DOWN)
        rings = [(48, 56, 58), (34, 44, 48), (22, 32, 36), (13, 20, 24),
                 (6, 11, 14), (2, 4, 6)]
        for i, col in enumerate(rings):
            rw = max(2, 14 - i * 2)
            rh = max(1, 10 - i * 2)
            pygame.draw.ellipse(surf, col, (x - rw, y - rh, rw * 2, rh * 2))
        # draining swirl: spiral arms rotating with time (the current going down)
        for arm in range(3):
            base = self.t * 1.8 + arm * (2 * math.pi / 3)
            pts = []
            for k in range(11):
                r = 2.0 + k * 1.15
                a = base + k * 0.5
                pts.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.62))
            pygame.draw.lines(surf, (66, 80, 84), False, pts, 1)
        # a wet glint catching the light off the lip
        pygame.draw.line(surf, (104, 116, 118), (x - 10, y - 6), (x - 4, y - 8), 1)
