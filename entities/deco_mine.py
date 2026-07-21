"""Mine decoration draw methods (split from decoration.py 2026-07).

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


class DecoMineMixin:
    def _draw_valve(self, surf, x, y):
        """The diggers' DEWATERING PUMP -- a hand pitcher pump on a
        driven well point, its hose run knocking when the arm swings
        loose. (2026-07 process audit: the old art was a pressure valve
        in an iron pipe run -- industrial plumbing that failed
        provenance in a hand dig. A farm town owns pitcher pumps, and a
        dig that broke into the river NEEDS one.) Kind name kept: the
        noise_source mechanic and its tests key on "valve"."""
        iron = (58, 60, 64)
        iron_dk = (34, 36, 40)
        wood = (76, 58, 38)
        # the driven pipe standing out of the ground + the pump body
        pygame.draw.rect(surf, iron_dk, (x - 2, y - 8, 4, 10))
        pygame.draw.rect(surf, iron, (x - 3, y - 18, 6, 11))
        pygame.draw.rect(surf, iron_dk, (x - 3, y - 18, 6, 11), 1)
        # the curved spout, mouth down
        pygame.draw.rect(surf, iron, (x + 3, y - 16, 5, 3))
        pygame.draw.rect(surf, iron, (x + 6, y - 14, 2, 4))
        # the long pump arm, raised (wood handle on an iron pin)
        pygame.draw.line(surf, iron_dk, (x - 2, y - 17), (x - 10, y - 25), 2)
        pygame.draw.line(surf, wood, (x - 8, y - 23), (x - 13, y - 28), 3)
        pygame.draw.circle(surf, (96, 92, 84), (x - 2, y - 17), 1)
        # the hose run slumping off toward the arm's basin
        pygame.draw.lines(surf, iron_dk, False,
                          [(x + 7, y - 11), (x + 10, y - 6), (x + 9, y - 1)], 2)

    def _draw_shoring_frame(self, surf, x, y):
        # top-down: the header beam along `ang` + the board ends at
        # both uprights (or one, for a broken span<=1 set)
        import math as _m
        ang = self.kwargs.get("ang", 0.0) or 0.0
        span = self.kwargs.get("span", 0.0) or 0.0
        ca, sa = _m.cos(ang), _m.sin(ang)
        half = self.kwargs.get("half")
        if half in ("a", "b"):
            # split frame (Scene.add_decoration): this deco is ONE
            # upright anchored on its post; the "b" twin draws the
            # beam for both (its frame centre sits -span/2 back)
            if half == "b":
                cx, cy = x - ca * span / 2, y - sa * span / 2
                hl = max(8, span / 2 + 5)
                pygame.draw.line(surf, (52, 39, 25),
                                 (int(cx - ca * hl), int(cy - sa * hl)),
                                 (int(cx + ca * hl), int(cy + sa * hl)), 4)
            pygame.draw.rect(surf, (98, 76, 50),
                             (int(x) - 3, int(y) - 2, 3, 4))
            pygame.draw.rect(surf, (86, 66, 43),
                             (int(x) + 1, int(y) - 2, 3, 4))
            return
        hl = max(8, span / 2 + 5)
        pygame.draw.line(surf, (52, 39, 25),
                         (int(x - ca * hl), int(y - sa * hl)),
                         (int(x + ca * hl), int(y + sa * hl)), 4)
        offs = [0.0] if span <= 1 else [-span / 2, span / 2]
        for o in offs:
            bx, by = x + ca * o, y + sa * o
            pygame.draw.rect(surf, (98, 76, 50),
                             (int(bx) - 3, int(by) - 2, 3, 4))
            pygame.draw.rect(surf, (86, 66, 43),
                             (int(bx) + 1, int(by) - 2, 3, 4))

    def _draw_descent_pit(self, surf, x, y):
        """Flat pitch-0 fallback for the mine mouth: a dark dug hole with a
        broken earth rim and the cut haul rope hanging into the dark. (The
        tilt view draws it as a real open shaft you look down into via
        rendering/props.py.)"""
        pygame.draw.ellipse(surf, (46, 34, 22), (x - 23, y - 16, 46, 32))   # dug rim
        pygame.draw.ellipse(surf, (7, 6, 10), (x - 18, y - 12, 36, 24))     # the hole
        pygame.draw.ellipse(surf, (2, 2, 4), (x - 12, y - 6, 24, 16))       # black throat
        pygame.draw.line(surf, (84, 65, 39), (x + 1, y - 10), (x + 2, y + 2), 2)
        pygame.draw.line(surf, (128, 106, 68), (x + 1, y - 10), (x + 2, y + 2), 1)
        for dx in (-2, 0, 2):                                               # frayed cut end
            pygame.draw.line(surf, (128, 106, 68), (x + 2, y + 2),
                             (x + 2 + dx, y + 5), 1)

    def _draw_ore_cart(self, surf, x, y):
        # top-down: the rusted tub, its dark mouth, four wheel hubs
        pygame.draw.rect(surf, (58, 40, 30), (x - 13, y - 8, 26, 16))
        pygame.draw.rect(surf, (96, 66, 48), (x - 11, y - 6, 22, 12))
        pygame.draw.rect(surf, (26, 22, 20), (x - 8, y - 4, 16, 8))
        for ox, oy in ((-10, -9), (10, -9), (-10, 9), (10, 9)):
            pygame.draw.circle(surf, (50, 42, 38), (x + ox, y + oy), 2)

    def _draw_tally_marks(self, surf, x, y):
        """Shift tallies scratched into the stone in fours with a
        cross-stroke -- the labor counted where it was done (the mine
        art pass; The Digging made visible, no words)."""
        rng = random.Random(self.seed)
        col = (142, 138, 128)
        gx = x - 20
        for g in range(3):
            n = 4 if g < 2 else 1 + rng.randint(0, 3)
            for i in range(n):
                sx = gx + i * 3
                pygame.draw.line(surf, col,
                                 (sx, y - 5 + rng.randint(-1, 1)),
                                 (sx + 1, y + 5), 1)
            if n >= 4:
                pygame.draw.line(surf, col, (gx - 1, y + 3),
                                 (gx + 10, y - 3), 1)
            gx += 14

    def _draw_mine_rail(self, surf, x, y):
        """A stub of old haul rail: two iron rails on rotten ties, run
        along `ang` (0 = east-west). The old workings' road; the
        procession's candle line walks it."""
        ang = self.kwargs.get("ang", 0.0) or 0.0
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca                       # across the rails
        L = 26
        for lat in (-4, 4):                    # the two rails
            x0 = x - ca * L + px * lat
            y0 = y - sa * L + py * lat
            x1 = x + ca * L + px * lat
            y1 = y + sa * L + py * lat
            pygame.draw.line(surf, (56, 52, 50), (int(x0), int(y0)),
                             (int(x1), int(y1)), 2)
            pygame.draw.line(surf, (84, 74, 66), (int(x0), int(y0)),
                             (int(x1), int(y1)), 1)
        rng = random.Random(self.seed)
        for k in (-18, -6, 6, 18):             # the ties, some gone
            if rng.random() < 0.25:
                continue
            tx0 = x + ca * k - px * 7
            ty0 = y + sa * k - py * 7
            tx1 = x + ca * k + px * 7
            ty1 = y + sa * k + py * 7
            pygame.draw.line(surf, (48, 38, 26), (int(tx0), int(ty0)),
                             (int(tx1), int(ty1)), 3)

    def _draw_waterfall(self, surf, x, y):
        """A sheet of water falling down the cave cliff into the river (flat pitch-0
        fallback; the tilt view draws it as a real falling sheet via
        rendering/props.py). Animated streaks scroll down + foam at the base."""
        H = 46
        top = y - H
        pygame.draw.rect(surf, (22, 28, 32), (x - 9, top, 18, H))       # wet rock
        cols = [(120, 168, 184), (92, 140, 158), (150, 196, 208)]
        for i in range(6):
            sx = x - 8 + i * 3
            col = cols[i % 3]
            off = int((self.t * 42 + i * 7) % 8)
            yy = top + off
            while yy < y:
                pygame.draw.line(surf, col, (sx, yy), (sx, min(y, yy + 4)), 1)
                yy += 8
        pygame.draw.line(surf, (188, 216, 226), (x - 8, top), (x + 8, top), 2)
        pygame.draw.ellipse(surf, (150, 188, 200), (x - 11, y - 3, 22, 7))
        pygame.draw.ellipse(surf, (210, 230, 236), (x - 5, y - 2, 10, 4))
        for i in range(5):
            fa = self.t * 3 + i * 1.3
            fx = x + int(math.cos(fa) * 7)
            fy = y - 1 - int(abs(math.sin(fa)) * 3)
            pygame.draw.circle(surf, (205, 226, 234), (fx, fy), 1)

    def _draw_water_channel(self, surf, x, y):
        """A SINGLE continuous fluid thread of the underground river on the cave
        floor (NARRATIVE §2): it leaves the channel, licks under the Threshold
        frame, and curves back into the river -- one unbroken ribbon, with a cold
        sheen that flows ALONG it. A FLOOR decal. `path` (kwarg) is a list of
        (dx, dy) world-px offsets from the anchor; joints are rounded so it reads
        as one line, never jointed segments."""
        path = self.kwargs.get("path")
        if not path or len(path) < 2:
            return
        raw = [(x + dx, y + dy) for dx, dy in path]
        # Chaikin corner-cutting: turn the routed waypoints into ONE smooth,
        # organic flowing curve (endpoints pinned to the south wall + the river).
        for _ in range(2):
            sm = [raw[0]]
            for i in range(len(raw) - 1):
                p, q = raw[i], raw[i + 1]
                sm.append((p[0] * 0.75 + q[0] * 0.25, p[1] * 0.75 + q[1] * 0.25))
                sm.append((p[0] * 0.25 + q[0] * 0.75, p[1] * 0.25 + q[1] * 0.75))
            sm.append(raw[-1])
            raw = sm
        pts = [(int(px), int(py)) for px, py in raw]
        Wd = 5
        # the SAME murky teal-green as the river floor (`~`), so the stream reads
        # as the same water, not a separate cyan thread
        pygame.draw.lines(surf, (22, 34, 34), False, pts, Wd + 6)   # soaked halo
        pygame.draw.lines(surf, (30, 48, 46), False, pts, Wd + 2)   # water body
        pygame.draw.lines(surf, (46, 68, 62), False, pts, Wd)
        for p in pts:                                               # round the joints
            pygame.draw.circle(surf, (30, 48, 46), p, (Wd + 2) // 2)
            pygame.draw.circle(surf, (46, 68, 62), p, Wd // 2)
        pygame.draw.lines(surf, (74, 98, 90), False, pts, 1)        # cold core
        # a few cold sheen glints chasing ALONG the line -- the current moving
        seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
               for i in range(len(pts) - 1)]
        total = sum(seg)
        if total > 0:
            for k in range(3):
                f = ((self.t * 0.16 + k / 3.0) % 1.0) * total
                acc = 0.0
                for i, d in enumerate(seg):
                    if acc + d >= f and d > 0:
                        u = (f - acc) / d
                        gx = int(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u)
                        gy = int(pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u)
                        pygame.draw.circle(surf, (150, 192, 204), (gx, gy), 2)
                        break
                    acc += d

    def _draw_water_trail(self, surf, x, y):
        """A thin thread of the underground river crossing a stone floor
        (NARRATIVE §2: the river is the artery; water finds the lowest place
        and the first thread reached the Threshold frame and crossed its plane).
        A FLOOR decal -- warped onto the tilted floor -- so it lies IN the stone
        and turns with the room. A dark wet rivulet pooled in a shallow seam,
        with a cold sheen that drifts along the flow (the current still moving)
        and faint ripple ticks. `ang` (radians) sets the flow axis (default down
        the +y screen toward the door); `pool=True` widens it into a standing
        pool where the thread reaches the frame."""
        ang = float(self.kwargs.get("ang", math.pi / 2))   # default: flows +y
        ca, sa = math.cos(ang), math.sin(ang)
        pool = self.kwargs.get("pool", False)
        L = 16 if not pool else 11                          # half-length along flow
        Wd = 4 if not pool else 9                           # half-width across flow

        def P(along, across):
            return (int(x + ca * along - sa * across),
                    int(y + sa * along + ca * across))
        # damp halo seeped into the surrounding stone (a touch wider than the
        # water, so the pool looks soaked-in, not painted on)
        for k in range(-L, L + 1, 4):
            f = 1.0 - abs(k) / (L + 4.0)
            pygame.draw.circle(surf, (22, 34, 34),
                               P(k, 0), max(1, int((Wd + 2) * f)))
        # the wet channel itself, in the SAME murky teal-green as the river (`~`)
        for k in range(-L, L + 1, 3):
            f = 1.0 - abs(k) / (L + 3.0)
            pygame.draw.circle(surf, (30, 48, 46), P(k, 0), max(1, int(Wd * f)))
            pygame.draw.circle(surf, (46, 68, 62), P(k, 0),
                               max(1, int(Wd * f * 0.6)))
        # a cold sheen that slides ALONG the flow -- the current moving
        drift = (self.t * 9.0) % (2 * L + 6) - (L + 3)
        gx, gy = P(drift, -Wd * 0.3)
        pygame.draw.circle(surf, (104, 128, 116), (gx, gy), 2)
        gx2, gy2 = P(drift * 0.6 + L * 0.4, Wd * 0.25)
        pygame.draw.circle(surf, (74, 98, 90), (gx2, gy2), 1)
        # a couple of faint ripple ticks across the thread
        for kk in (-L // 2, L // 3):
            a = P(kk, -Wd * 0.7); b = P(kk, Wd * 0.7)
            pygame.draw.line(surf, (60, 84, 76), a, b, 1)

    def _draw_loose_plank(self, surf, x, y):
        """A weathered board lying askew over a gap -- the plank noise
        trap. Grain lines, one nail head, dark shadow under the
        raised end."""
        sh = pygame.Surface((30, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 70), (0, 0, 30, 8))
        surf.blit(sh, (x - 15, y))
        pts = [(x - 14, y + 2), (x + 13, y - 3),
               (x + 14, y + 1), (x - 13, y + 6)]
        pygame.draw.polygon(surf, (104, 82, 56), pts)
        pygame.draw.polygon(surf, (58, 44, 30), pts, 1)
        pygame.draw.line(surf, (76, 58, 40),
                         (x - 10, y + 3), (x + 10, y - 1), 1)
        pygame.draw.circle(surf, (40, 36, 34), (x + 10, y - 1), 1)
