"""Structure decoration draw methods (split from decoration.py 2026-07).

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


class DecoStructureMixin:
    def _draw_well(self, surf, x, y):
        # A fuller, ominous wellhead -- a dead, dry town well, dread
        # set-dressing (NOT the way down; the descent is the cult's dug mine
        # out at the grove, reached by the rite). It goes nowhere the player
        # can follow. Mossy ring of fitted stones, a bottomless black shaft, a
        # winch frame, and a frayed stub where the bucket-rope used to hang.
        # Outer stone ring (3/4 top-down ellipse)
        pygame.draw.ellipse(surf, (78, 78, 88), (x - 18, y - 8, 36, 22))
        pygame.draw.ellipse(surf, (54, 54, 64), (x - 18, y - 8, 36, 22), 2)
        # Fitted stones around the rim
        for i in range(8):
            ang = i / 8 * math.tau
            sx = x + int(math.cos(ang) * 15)
            sy = y + 3 + int(math.sin(ang) * 8)
            pygame.draw.rect(surf, (96, 96, 106), (sx - 2, sy - 2, 4, 4))
            pygame.draw.rect(surf, (50, 50, 60), (sx - 2, sy - 2, 4, 4), 1)
        # Moss creeping the near rim
        pygame.draw.arc(surf, (54, 86, 54), (x - 16, y + 1, 32, 15), 3.5, 6.0, 2)
        # Bottomless shaft -- no water, just dark that keeps going
        pygame.draw.ellipse(surf, (10, 8, 14), (x - 12, y - 3, 24, 14))
        pygame.draw.ellipse(surf, (2, 2, 4), (x - 8, y - 1, 16, 9))
        # Winch frame: two posts + crossbar on the north side
        pygame.draw.line(surf, (84, 56, 36), (x - 13, y - 6), (x - 13, y - 22), 3)
        pygame.draw.line(surf, (84, 56, 36), (x + 13, y - 6), (x + 13, y - 22), 3)
        pygame.draw.line(surf, (70, 46, 28), (x - 15, y - 22), (x + 15, y - 22), 3)
        # Winch drum on the crossbar
        pygame.draw.rect(surf, (60, 40, 24), (x - 6, y - 24, 12, 4))
        # The frayed stub -- the rope is long gone; a hand's-width of it
        # still knotted to the drum, ending in loose threads.
        pygame.draw.line(surf, (150, 130, 90), (x, y - 22), (x, y - 16), 1)
        pygame.draw.line(surf, (120, 102, 70), (x, y - 16), (x - 1, y - 13), 1)
        pygame.draw.line(surf, (120, 102, 70), (x, y - 16), (x + 1, y - 14), 1)

    def _draw_town_sign(self, surf, x, y):
        """A wooden signpost with two crossbeams reading the town's
        name. Weathered, the paint mostly gone. The text is the
        decoration's `text` kwarg ('BRIMLEY' by default). Two posts
        with the boards nailed across them, edge highlights so the
        sign reads as raised."""
        text = self.kwargs.get("text", "BRIMLEY")
        post_col = (62, 44, 28)
        post_lit = (88, 64, 40)
        board_col = (96, 70, 44)
        board_lit = (124, 92, 58)
        board_dark = (60, 42, 22)
        # Two posts, 4px wide, 26px tall
        for px in (x - 10, x + 10):
            pygame.draw.rect(surf, post_col, (px - 2, y - 18, 4, 26))
            pygame.draw.line(surf, post_lit, (px - 2, y - 18),
                             (px - 2, y + 8), 1)
        # Board: 28px wide, 12px tall, centred at (x, y-10)
        bw, bh = 28, 14
        bx, by = x - bw // 2, y - 18
        pygame.draw.rect(surf, board_col, (bx, by, bw, bh))
        pygame.draw.rect(surf, board_dark, (bx, by, bw, bh), 1)
        pygame.draw.line(surf, board_lit, (bx + 1, by + 1),
                         (bx + bw - 1, by + 1), 1)
        # Text rendered tiny.
        font = pygame.font.SysFont(None, 12, bold=True)
        txt = font.render(text, True, (30, 20, 10))
        txt_x = bx + (bw - txt.get_width()) // 2
        txt_y = by + (bh - txt.get_height()) // 2
        surf.blit(txt, (txt_x, txt_y))

    def _draw_flagpole(self, surf, x, y):
        """A weathered metal flagpole with a tattered flag. The flag
        is half-mast; the rope is frayed. Used in front of the
        schoolhouse. Sway driven by self.t so the flag flutters."""
        pole_col = (130, 132, 138)
        pole_lit = (172, 174, 180)
        # Pole: 28px tall, 2px wide
        ph = 28
        pygame.draw.line(surf, pole_col, (x, y + 4), (x, y - ph), 2)
        pygame.draw.line(surf, pole_lit, (x - 1, y + 4), (x - 1, y - ph), 1)
        # Knob at top
        pygame.draw.circle(surf, (180, 180, 188), (x, y - ph), 2)
        # Half-mast flag -- a frayed strip 8x12. The trailing edge
        # ripples with self.t.
        sway = math.sin(self.t * 2.2 + self.seed * 0.1) * 1.4
        fy = y - ph + 8
        # Faded dark cloth (former colour, now near-black).
        cloth = (66, 50, 50)
        cloth_dark = (40, 28, 28)
        pts = [
            (x + 1, fy),
            (x + 12 + sway, fy + 1),
            (x + 11 + sway, fy + 10),
            (x + 1, fy + 9),
        ]
        pygame.draw.polygon(surf, cloth, pts)
        pygame.draw.line(surf, cloth_dark, (x + 1, fy), (x + 11 + sway, fy + 9), 1)
        # Frayed trailing edge
        for i in range(3):
            tx = int(x + 10 + sway - i)
            ty = fy + 2 + i * 3
            pygame.draw.line(surf, cloth_dark, (tx, ty), (tx + 3, ty + 1), 1)

    def _draw_steeple(self, surf, x, y):
        """A church bell-tower, near-top-down: a tall narrow spire rising
        up the screen from its base, a dark louvered belfry with a faint
        bell, a pointed cap + a crooked cross, and a long shadow thrown
        across the ground -- the one TALL thing for miles, the landmark
        you orient by."""
        H = 74
        topx = x + int(math.sin(self.seed) * 4)        # leans a touch
        top = y - H
        sh = pygame.Surface((64, 30), pygame.SRCALPHA)  # long cast shadow, down-right
        pygame.draw.polygon(sh, (0, 0, 0, 88), [(0, 26), (14, 26), (58, 4), (44, 0)])
        surf.blit(sh, (x - 6, y - 6))
        bw = 16
        body = [(x - bw // 2, y), (topx - bw // 2 + 3, top + 14),
                (topx + bw // 2 - 3, top + 14), (x + bw // 2, y)]
        pygame.draw.polygon(surf, (70, 64, 54), body)
        pygame.draw.polygon(surf, (38, 34, 28), body, 1)
        pygame.draw.line(surf, (98, 92, 80),
                         (x - bw // 2, y), (topx - bw // 2 + 3, top + 14), 2)
        pygame.draw.rect(surf, (15, 13, 17), (topx - 5, top + 14, 10, 12))  # belfry
        bell_dx = int(math.sin(self.t * 1.7 + self.seed) * 2)               # tolling
        pygame.draw.circle(surf, (66, 58, 42), (topx + bell_dx, top + 21), 3)
        pygame.draw.line(surf, (28, 24, 18), (topx + bell_dx, top + 18),
                         (topx + bell_dx, top + 24), 1)                      # clapper line
        spire = [(topx - bw // 2 + 2, top + 14), (topx, top - 8),
                 (topx + bw // 2 - 2, top + 14)]
        pygame.draw.polygon(surf, (54, 40, 30), spire)
        pygame.draw.polygon(surf, (32, 24, 18), spire, 1)
        pygame.draw.line(surf, (44, 40, 32), (topx, top - 8), (topx, top - 18), 2)
        pygame.draw.line(surf, (44, 40, 32), (topx - 4, top - 14), (topx + 4, top - 14), 2)

    def _draw_church_bell(self, surf, x, y):
        """The church bell, hung in its hoist frame: two grounded
        uprights, the yoke beam across them, the bell swung between.
        Aged bronze with a patina bloom and a worn-bright lip. While
        `ring_t` > 0 (set by Game._tick_bell when the peal is live) the
        whole bell swings on its pivot and the clapper lags behind it;
        at rest it hangs dead still. Anchor is the frame's FOOT, drawn
        ~38px upward."""
        pivot_x, pivot_y = x, y - 28
        ring = getattr(self, "ring_t", 0.0)
        a = 0.0
        if ring > 0.0:
            # full swing while the peal lives, easing off near the end
            env = min(1.0, ring / 2.0)
            a = math.sin(self.t * 5.4) * 0.42 * env
        ca, sa = math.cos(a), math.sin(a)

        def rot(px, py):
            return (int(pivot_x + px * ca - py * sa),
                    int(pivot_y + px * sa + py * ca))
        # the hoist frame: grounded uprights + the yoke beam across
        wood, wood_dk = (56, 44, 32), (34, 26, 20)
        for px_ in (x - 12, x + 10):
            pygame.draw.rect(surf, wood, (px_, y - 32, 3, 36))
            pygame.draw.rect(surf, wood_dk, (px_, y - 32, 3, 36), 1)
        pygame.draw.rect(surf, wood, (x - 13, y - 36, 26, 6))
        pygame.draw.rect(surf, wood_dk, (x - 13, y - 36, 26, 6), 1)
        bronze    = (118, 100, 62)
        bronze_dk = (78, 66, 42)
        patina    = (96, 110, 84)
        lip_hi    = (178, 160, 108)
        # crown loop on the pivot
        pygame.draw.circle(surf, bronze_dk, (int(pivot_x), int(pivot_y)), 3)
        # the bell profile, rotated about the pivot: shoulder -> waist
        # -> flared sound-bow -> lip
        prof = [(-4, 2), (4, 2), (5, 8), (6, 14), (10, 19), (10, 22),
                (-10, 22), (-10, 19), (-6, 14), (-5, 8)]
        pts = [rot(px, py) for px, py in prof]
        pygame.draw.polygon(surf, bronze, pts)
        pygame.draw.polygon(surf, bronze_dk, pts, 1)
        # patina bloom down one flank + the worn-bright lip edge
        pygame.draw.line(surf, patina, rot(-4, 6), rot(-6, 15), 2)
        pygame.draw.line(surf, lip_hi, rot(-9, 21), rot(9, 21), 1)
        # shoulder band (the founder's line)
        pygame.draw.line(surf, bronze_dk, rot(-4, 5), rot(4, 5), 1)
        # the clapper, lagging the swing
        cl = rot(-sa * 6, 24)
        pygame.draw.circle(surf, (40, 34, 26), cl, 3)

    def _draw_gas_pump(self, surf, x, y):
        """A 1990s rural gas pump. Beige body, red side panel, a
        rubber hose looping back into the pump. The dial wheel
        creeps slowly so the pump reads as plugged in but unused."""
        body = (200, 190, 170)
        edge = (60, 50, 40)
        red = (160, 40, 40)
        hose = (20, 18, 22)
        # Base
        pygame.draw.rect(surf, (90, 90, 100), (x - 6, y + 8, 12, 4))
        # Body column
        pygame.draw.rect(surf, body, (x - 6, y - 16, 12, 24))
        pygame.draw.rect(surf, edge, (x - 6, y - 16, 12, 24), 1)
        # Red side panel
        pygame.draw.rect(surf, red, (x - 6, y - 16, 12, 6))
        # Display window
        pygame.draw.rect(surf, (10, 14, 20), (x - 4, y - 8, 8, 5))
        # Slowly creeping dial digits
        digit = int(self.t * 0.7) % 10
        pygame.draw.rect(surf, (40, 200, 60),
                         (x - 3 + (digit % 4) * 2, y - 7, 1, 3))
        # Nozzle hook + hose looping back
        pygame.draw.line(surf, hose, (x + 6, y - 6), (x + 9, y - 4), 1)
        pygame.draw.line(surf, hose, (x + 9, y - 4), (x + 9, y + 4), 1)
        pygame.draw.line(surf, hose, (x + 9, y + 4), (x + 6, y + 6), 1)
        # Logo decal
        pygame.draw.rect(surf, (220, 200, 80), (x - 3, y - 14, 6, 2))

    def _draw_payphone(self, surf, x, y):
        """1990s glass-walled phone booth. Vertical box with metal
        framing, clear glass body, a black handset on a chrome cord,
        and a small red 'in use' light that blinks irregularly. The
        receiver sits slightly off the cradle on a per-seed schedule
        -- as if someone just hung up. The booth replaces a 'lantern'
        placeholder in village.py."""
        # Foundation slab
        pygame.draw.rect(surf, (60, 60, 70), (x - 9, y + 12, 18, 4))
        # Booth body (glass)
        pygame.draw.rect(surf, (140, 170, 200), (x - 8, y - 22, 16, 34))
        # Frame
        pygame.draw.rect(surf, (40, 40, 50), (x - 8, y - 22, 16, 34), 1)
        pygame.draw.line(surf, (40, 40, 50),
                         (x - 8, y - 6), (x + 8, y - 6), 1)
        # Roof cap
        pygame.draw.rect(surf, (50, 50, 60), (x - 10, y - 24, 20, 4))
        # Inner phone unit (metal box on the back wall)
        pygame.draw.rect(surf, (90, 90, 100), (x - 5, y - 16, 10, 8))
        pygame.draw.rect(surf, (40, 40, 50), (x - 5, y - 16, 10, 8), 1)
        # Handset hanging slightly off the hook (off-cradle anomaly)
        off_cradle = (self.t + self.seed * 0.07) % 8.0
        cord_y = y - 4 if off_cradle < 4.0 else y - 2
        # Cord (chromed line)
        pygame.draw.line(surf, (180, 180, 200),
                         (x - 4, y - 12), (x - 4, cord_y), 1)
        # Handset body
        pygame.draw.rect(surf, (10, 10, 14), (x - 6, cord_y, 4, 2))
        # Red "in use" light, blinks irregularly
        light_phase = (self.t * 1.7 + self.seed * 0.3) % 3.0
        if light_phase < 0.4:
            pygame.draw.rect(surf, (220, 60, 50), (x + 3, y - 18, 2, 2))
        else:
            pygame.draw.rect(surf, (90, 24, 20), (x + 3, y - 18, 2, 2))
        # Coin slot
        pygame.draw.line(surf, (10, 10, 14),
                         (x - 1, y - 10), (x + 1, y - 10), 1)

    def _draw_pickup_truck(self, surf, x, y):
        """A dead farm pickup, ~2.5 tiles long -- big, weathered, and
        long abandoned: faded muddy paint eaten through with rust,
        cracked-out windows, sagging on a flat tire, weeds growing up
        through the bed. The truck that drove for the county line and got
        handed back. Pair with solid 'X' tiles so the player can't walk
        through it. Faces right (nosed east, into the tree line)."""
        rng = random.Random(self.seed)
        # Sunk, oversized contact shadow under the whole hulk.
        sh = pygame.Surface((110, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 95), (0, 0, 110, 34))
        surf.blit(sh, (x - 52, y + 6))
        body = (96, 88, 66)          # faded, dirtied paint -- muddy tan/olive
        body_dark = (52, 48, 36)
        rust = (118, 60, 32)
        rust_dk = (78, 40, 22)
        glass = (60, 70, 70)         # dead, grimy glass
        tire = (24, 22, 26)
        # ---- Bed (rear/left), a big open rusted box ----
        pygame.draw.rect(surf, body, (x - 50, y - 16, 38, 30))
        pygame.draw.rect(surf, body_dark, (x - 50, y - 16, 38, 30), 2)
        pygame.draw.rect(surf, (40, 38, 30), (x - 46, y - 12, 30, 22))   # cavity
        # Weeds growing up through the bed and the wheel wells.
        for _ in range(9):
            wx = x - 44 + rng.randint(0, 28)
            wy = y - 10 + rng.randint(0, 18)
            g = 60 + rng.randint(0, 40)
            pygame.draw.line(surf, (44, g, 44), (wx, wy), (wx - 1, wy - 6), 1)
        # ---- Cab ----
        pygame.draw.rect(surf, body, (x - 12, y - 24, 34, 38))
        pygame.draw.rect(surf, body_dark, (x - 12, y - 24, 34, 38), 2)
        # Roof, sun-bleached + rust-blistered.
        pygame.draw.rect(surf, (108, 100, 78), (x - 10, y - 22, 30, 12))
        # Windshield -- cracked, mostly dark.
        pygame.draw.polygon(surf, glass, [
            (x - 6, y - 20), (x + 16, y - 20), (x + 19, y - 8), (x - 6, y - 8)])
        pygame.draw.line(surf, (150, 150, 140), (x - 2, y - 20), (x + 10, y - 9), 1)
        pygame.draw.line(surf, (150, 150, 140), (x + 10, y - 18), (x + 4, y - 8), 1)
        pygame.draw.rect(surf, body_dark, (x - 6, y - 20, 25, 12), 1)
        # Side window, glass gone -- just a dark hole.
        pygame.draw.rect(surf, (22, 22, 26), (x + 14, y - 6, 8, 12))
        # ---- Hood / front (right) ----
        pygame.draw.rect(surf, body, (x + 22, y - 8, 16, 22))
        pygame.draw.rect(surf, body_dark, (x + 22, y - 8, 16, 22), 2)
        pygame.draw.rect(surf, (150, 140, 90), (x + 37, y - 2, 3, 6))    # dead headlight
        # Bent front bumper, hanging.
        pygame.draw.line(surf, (96, 92, 96), (x + 38, y + 12), (x + 42, y + 16), 2)
        # ---- Rust eating the body (deterministic blotches) ----
        for _ in range(14):
            bx = x - 48 + rng.randint(0, 84)
            by = y - 22 + rng.randint(0, 34)
            r = rng.randint(2, 5)
            pygame.draw.circle(surf, rust if rng.random() < 0.6 else rust_dk,
                               (bx, by), r)
        # Long rust runs bleeding down from the seams.
        for sx0 in (x - 44, x - 30, x - 6, x + 16, x + 30):
            pygame.draw.line(surf, rust_dk, (sx0, y + 2), (sx0, y + 12), 1)
        # ---- Wheels: rear sound, front flat (the hulk sags forward) ----
        pygame.draw.circle(surf, tire, (x - 36, y + 13), 7)
        pygame.draw.circle(surf, (60, 58, 60), (x - 36, y + 13), 3)
        pygame.draw.ellipse(surf, tire, (x + 20, y + 13, 18, 8))         # flat tire
        pygame.draw.rect(surf, (60, 58, 60), (x + 27, y + 15, 4, 3))

    def _draw_news_rack(self, surf, x, y):
        """A coin-op newspaper vending box outside the shop, flat view.
        The window still shows the last issue it was ever fed; the
        examine in brimley.py carries the January 15 date."""
        pygame.draw.line(surf, (40, 40, 44), (x - 5, y + 6), (x - 5, y + 10), 2)
        pygame.draw.line(surf, (40, 40, 44), (x + 5, y + 6), (x + 5, y + 10), 2)
        pygame.draw.rect(surf, (102, 43, 37), (x - 7, y - 12, 14, 18))
        pygame.draw.rect(surf, (70, 30, 25), (x - 7, y - 12, 14, 18), 1)
        pygame.draw.rect(surf, (186, 180, 160), (x - 5, y - 10, 10, 9))
        pygame.draw.line(surf, (52, 50, 48), (x - 4, y - 8), (x + 4, y - 8), 2)
        pygame.draw.line(surf, (108, 104, 94), (x - 4, y - 5), (x + 4, y - 5), 1)
        pygame.draw.line(surf, (108, 104, 94), (x - 4, y - 3), (x, y - 3), 1)
        pygame.draw.rect(surf, (24, 24, 26), (x + 2, y + 2, 3, 2))   # coin slot

    # Faded period paints for the dead-lot cars. Keep in step with
    # rendering/props.py _RUST_BASES (the tilt volumes), which is the
    # authoritative copy; this one only feeds the dev-only flat view.
    _RUST_CAR_BASES = [
        (128, 62, 52), (86, 104, 122), (150, 142, 118),
        (98, 84, 60), (92, 102, 74), (146, 118, 62),
    ]

    def _rust_car_flat(self, surf, x, y, L, cab0, cab1, van=False,
                       rack=False):
        """Flat-view TOP-DOWN hulk shared by the rust_* car kinds: a
        weathered body pointing EAST, roof/glass from above, tyres
        poking out the sides (one blown), seeded rust and weeds. The
        real look is the tilt volume in rendering/props.py; this keeps
        the dev pitch-0 view honest. Pair with solid 'X' tiles."""
        rng = random.Random(self.seed)
        hL = L // 2
        base = self._RUST_CAR_BASES[rng.randrange(len(self._RUST_CAR_BASES))]
        fade = rng.uniform(0.72, 0.98)
        body = tuple(int(c * 0.9 * fade) for c in base)
        body_lit = tuple(min(255, int(c * 1.12 * fade)) for c in base)
        body_dark = tuple(int(c * 0.5 * fade) for c in base)
        glass = (16, 17, 19) if rng.random() < 0.45 else (52, 60, 58)
        tire, rust = (22, 20, 24), (110, 58, 30)
        hw = 15 if van else 11                    # half-width incl. flanks
        # Tyres at the corners; one blown flat (a wider smear).
        flat_i = rng.randrange(4)
        corners = ((x - hL + 8, y - hw - 2), (x + hL - 14, y - hw - 2),
                   (x - hL + 8, y + hw - 8), (x + hL - 14, y + hw - 8))
        for i, (wx, wy) in enumerate(corners):
            if i == flat_i:
                pygame.draw.rect(surf, tire, (wx - 2, wy + 2, 14, 6),
                                 border_radius=2)
            else:
                pygame.draw.rect(surf, tire, (wx, wy, 10, 6),
                                 border_radius=2)
        # Body seen from above, nose east.
        pygame.draw.rect(surf, body, (x - hL, y - hw + 2, L, 2 * hw - 4),
                         border_radius=5)
        pygame.draw.rect(surf, body_dark, (x - hL, y - hw + 2, L, 2 * hw - 4),
                         1, border_radius=5)
        if van:
            # one long roof slab with a windshield band at the nose
            pygame.draw.rect(surf, body_lit,
                             (x - hL + 3, y - hw + 5, L - 12, 2 * hw - 10))
            pygame.draw.rect(surf, glass,
                             (x + hL - 9, y - hw + 5, 5, 2 * hw - 10))
        else:
            # windshield (east) + rear glass (west) + roof between
            pygame.draw.rect(surf, glass, (x + cab1, y - hw + 5, 5,
                                           2 * hw - 10))
            pygame.draw.rect(surf, glass, (x + cab0, y - hw + 5, 4,
                                           2 * hw - 10))
            pygame.draw.rect(surf, body_lit, (x + cab0 + 5, y - hw + 5,
                                              cab1 - cab0 - 6, 2 * hw - 10))
            if rack:
                for ry in (y - hw + 6, y + hw - 8):
                    pygame.draw.line(surf, body_dark, (x + cab0 + 5, ry),
                                     (x + cab1 - 2, ry), 1)
        # Dead lamps.
        pygame.draw.rect(surf, (150, 142, 108), (x + hL - 2, y - hw + 4, 2, 3))
        pygame.draw.rect(surf, (150, 142, 108), (x + hL - 2, y + hw - 9, 2, 3))
        pygame.draw.rect(surf, (96, 30, 26), (x - hL, y - hw + 4, 2, 3))
        pygame.draw.rect(surf, (96, 30, 26), (x - hL, y + hw - 9, 2, 3))
        # Rust blotches + weeds along the flanks.
        for _ in range(10):
            pygame.draw.circle(
                surf, rust if rng.random() < 0.6 else (78, 40, 22),
                (x - hL + rng.randint(2, L - 2),
                 y - hw + rng.randint(2, 2 * hw - 2)), rng.randint(1, 3))
        for _ in range(7):
            wx = x - hL + rng.randint(0, L)
            wy = y + hw - rng.randint(0, 3)
            g = 58 + rng.randint(0, 42)
            pygame.draw.line(surf, (44, g, 44), (wx, wy),
                             (wx - rng.randint(0, 2), wy - rng.randint(4, 8)),
                             1)

    def _draw_rust_sedan(self, surf, x, y):
        """Dead-lot sedan, flat view (see _rust_car_flat)."""
        self._rust_car_flat(surf, x, y, 50, -17, 9)

    def _draw_rust_wagon(self, surf, x, y):
        """Dead-lot station wagon, flat view (long roof + rack)."""
        self._rust_car_flat(surf, x, y, 54, -25, 10, rack=True)

    def _draw_rust_coupe(self, surf, x, y):
        """Dead-lot coupe, flat view (short greenhouse set back)."""
        self._rust_car_flat(surf, x, y, 44, -15, 3)

    def _draw_rust_van(self, surf, x, y):
        """Dead-lot panel van, flat view (one tall slab)."""
        self._rust_car_flat(surf, x, y, 52, 0, 0, van=True)

    def _draw_player_car(self, surf, x, y):
        """The PI's pale grey-blue sedan, dead on the shoulder, drawn TOP-DOWN
        (the game's overhead read) pointing NORTH up the road into town -- roof,
        glass and all four tyres seen from above. ~1.5 tiles wide, ~3 long.
        Pair with a solid 'X' footprint so collision matches."""
        body = (112, 126, 142)
        body_dark = (60, 72, 90)
        body_lit = (146, 160, 176)
        glass = (60, 74, 92)
        tire = (22, 20, 24)
        rust = (96, 92, 80)
        # Four tyres at the corners, poking out the sides (top-down view).
        for wx, wy in ((x - 15, y - 17), (x + 10, y - 17),
                       (x - 15, y + 7), (x + 10, y + 7)):
            pygame.draw.rect(surf, tire, (wx, wy, 5, 10), border_radius=2)
        # Body, longer along Y because it points up the road.
        pygame.draw.rect(surf, body, (x - 13, y - 25, 26, 50), border_radius=6)
        pygame.draw.rect(surf, body_dark, (x - 13, y - 25, 26, 50), 1,
                         border_radius=6)
        # Hood seam (north) + a door seam down each side.
        pygame.draw.line(surf, body_dark, (x - 11, y - 22), (x + 11, y - 22), 1)
        pygame.draw.line(surf, body_dark, (x - 13, y + 1), (x + 13, y + 1), 1)
        # Windshield (front/north) + rear window (back/south).
        pygame.draw.rect(surf, glass, (x - 10, y - 10, 20, 7))
        pygame.draw.rect(surf, glass, (x - 10, y + 11, 20, 6))
        # Roof between the glass.
        pygame.draw.rect(surf, body_lit, (x - 10, y - 2, 20, 12))
        # Headlights (north) + tail lights (south).
        pygame.draw.rect(surf, (224, 222, 180), (x - 11, y - 25, 4, 3))
        pygame.draw.rect(surf, (224, 222, 180), (x + 7, y - 25, 4, 3))
        pygame.draw.rect(surf, (196, 40, 36), (x - 11, y + 22, 4, 3))
        pygame.draw.rect(surf, (196, 40, 36), (x + 7, y + 22, 4, 3))
        # Side mirrors + a rust scar on the roof -- it has sat a while.
        pygame.draw.rect(surf, body_dark, (x - 16, y - 7, 3, 3))
        pygame.draw.rect(surf, body_dark, (x + 13, y - 7, 3, 3))
        pygame.draw.rect(surf, rust, (x - 5, y + 2, 4, 7))

    def _draw_headstone(self, surf, x, y):
        """A weathered grave marker set crooked in the dirt -- a
        rounded slab or a cross, leaning, mossy, its inscription worn to
        illegible scratches. Per-instance variation (seed) so a row of
        them reads as graves, never a clean grid of identical rocks."""
        rng = random.Random(self.seed)
        h = rng.randint(18, 26)
        w = rng.randint(11, 15)
        lean = rng.randint(-4, 4)              # top shifted sideways = crooked
        cross = rng.random() < 0.30
        stone = (94, 92, 90)
        stone_dk = (56, 54, 54)
        moss = (58, 74, 50)
        # Sit the marker's foot down on its ground shadow (drawn at y+16).
        # Without this the stone's base rested at the tile centre while the
        # shadow sat a half-tile lower, so the graves read as floating.
        b = y + 14
        tx = x + lean
        top = b - h
        # Turned dirt at the foot.
        pygame.draw.ellipse(surf, (30, 26, 23), (x - w // 2 - 2, b, w + 4, 7))
        if cross:
            pygame.draw.line(surf, stone, (tx, top), (x, b), 5)
            pygame.draw.line(surf, stone, (tx - w // 2, top + h // 3),
                             (tx + w // 2, top + h // 3), 5)
            pygame.draw.line(surf, stone_dk, (tx, top), (x, b), 1)
        else:
            pts = [(x - w // 2, b), (x - w // 2 + lean, top + 5),
                   (tx - w // 4, top), (tx + w // 4, top),
                   (x + w // 2 + lean, top + 5), (x + w // 2, b)]
            pygame.draw.polygon(surf, stone, pts)
            pygame.draw.polygon(surf, stone_dk, pts, 1)
            for i in range(2):                 # illegible inscription
                ly = top + 9 + i * 5
                lx = x - w // 4 + int(lean * (1 - (ly - top) / h))
                pygame.draw.line(surf, stone_dk, (lx, ly), (lx + w // 2, ly), 1)
        pygame.draw.circle(surf, moss, (x - w // 4, b - 2), 2)

    def _draw_standing_stone(self, surf, x, y):
        """An ORGANIC standing stone -- a weathered monolith at the burn
        clearing: an irregular tapering slab with no tool marks, moss
        skirting the base, pale lichen blooming up one face, a hairline
        crack. Seeded per instance so the three in the grove read as
        siblings, never copies. Elevation art; under tilt it stands up
        as a grounded standee (rendering/props.py)."""
        rng = random.Random(self.seed)
        h = rng.randint(42, 56)
        wbase = rng.randint(15, 19)
        wtop = rng.randint(5, 9)
        lean = rng.randint(-3, 3)
        stone = (96, 94, 98)
        stone_dk = (52, 50, 56)
        stone_lt = (126, 124, 130)
        moss = (58, 74, 50)
        lichen = (134, 138, 118)
        # Foot seated on the ground shadow (same grounding as headstone).
        b = y + 14
        top = b - h
        # Jagged silhouette: walk both flanks with seeded wobble so no
        # edge is a ruled line.
        left, right = [], []
        steps = 5
        for i2 in range(steps + 1):
            f = i2 / steps
            yy = b - f * h
            half = (wbase * (1 - f) + wtop * f) / 2.0
            cx = x + lean * f
            left.append((cx - half + rng.uniform(-1.8, 1.8), yy))
            right.append((cx + half + rng.uniform(-1.8, 1.8), yy))
        pts = left + right[::-1]
        pygame.draw.polygon(surf, stone, pts)
        pygame.draw.polygon(surf, stone_dk, pts, 1)
        # One lit flank, one hairline crack wandering down from the crown.
        pygame.draw.line(surf, stone_lt, left[1], left[-2], 1)
        crack = [(x + rng.randint(-3, 3), top + rng.randint(3, 7))]
        for _ in range(3):
            crack.append((crack[-1][0] + rng.randint(-3, 3),
                          crack[-1][1] + h // 5))
        pygame.draw.lines(surf, stone_dk, False, crack, 1)
        # Lichen blooms up one face.
        for _ in range(rng.randint(3, 5)):
            lx = x + rng.randint(-(wbase // 2) + 2, (wbase // 2) - 2)
            ly = b - rng.randint(6, h - 8)
            pygame.draw.circle(surf, lichen, (lx, ly), rng.randint(1, 2))
        # Turned dirt + moss skirting the base.
        pygame.draw.ellipse(surf, (30, 26, 23),
                            (x - wbase // 2 - 2, b - 2, wbase + 4, 6))
        for _ in range(rng.randint(3, 5)):
            mx = x + rng.randint(-(wbase // 2), wbase // 2)
            pygame.draw.circle(surf, moss,
                               (mx, b - rng.randint(1, 4)), rng.randint(1, 2))

    def _draw_pedestal(self, surf, x, y):
        # Stone pedestal: a tapered grey block. Used at the end of the
        # abducted_hallway to stage the final diary page. Slow inner
        # glow when `lit=True` is passed via kwargs.
        body = (110, 110, 120)
        edge = (60, 60, 70)
        pygame.draw.rect(surf, body, (x - 9, y - 4, 18, 12))
        pygame.draw.rect(surf, edge, (x - 9, y - 4, 18, 12), 1)
        pygame.draw.rect(surf, body, (x - 11, y + 6, 22, 4))
        pygame.draw.rect(surf, edge, (x - 11, y + 6, 22, 4), 1)
        pygame.draw.rect(surf, (140, 140, 150), (x - 7, y - 6, 14, 3))
        if self.kwargs.get("lit", True):
            pulse = 0.6 + math.sin(self.t * 2.0 + self.seed) * 0.4
            glow = pygame.Surface((18, 8), pygame.SRCALPHA)
            alpha = int(120 * pulse)
            pygame.draw.ellipse(glow, (200, 180, 220, alpha), (0, 0, 18, 8))
            surf.blit(glow, (x - 9, y - 10))

    def _draw_pillar(self, surf, x, y):
        """Stone pillar. `large=True` draws a fat 32x44 column with a
        capital and base; default is a slim 18x36 supporting pillar.
        When `filled=True` the pillar shows its offering: the orb
        (large) or a big fish (small) sits on top of the capital with
        a soft glow."""
        large = self.kwargs.get("large", False)
        filled = self.kwargs.get("filled", False)
        if large:
            body = (130, 130, 140)
            edge = (70, 70, 80)
            cap = (160, 160, 170)
            pygame.draw.rect(surf, body, (x - 16, y - 30, 32, 44))
            pygame.draw.rect(surf, edge, (x - 16, y - 30, 32, 44), 1)
            pygame.draw.rect(surf, cap, (x - 18, y - 34, 36, 6))
            pygame.draw.rect(surf, edge, (x - 18, y - 34, 36, 6), 1)
            pygame.draw.rect(surf, cap, (x - 18, y + 12, 36, 6))
            pygame.draw.rect(surf, edge, (x - 18, y + 12, 36, 6), 1)
            pygame.draw.line(surf, edge, (x, y - 28), (x, y + 12), 1)
            if filled:
                # Orb resting on top of the capital. Soft purple glow,
                # subtle pulse via self.t.
                pulse = 0.7 + math.sin(self.t * 2.0 + self.seed) * 0.3
                glow = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow, (180, 80, 220, int(80 * pulse)),
                                   (20, 20), int(16 * pulse))
                surf.blit(glow, (x - 20, y - 56))
                pygame.draw.circle(surf, (60, 30, 80), (x, y - 40), 7)
                pygame.draw.circle(surf, (200, 120, 240), (x, y - 40), 6)
                pygame.draw.circle(surf, (255, 220, 255),
                                   (x - 2, y - 42), 2)
        else:
            body = (118, 118, 128)
            edge = (60, 60, 70)
            cap = (150, 150, 160)
            pygame.draw.rect(surf, body, (x - 9, y - 22, 18, 32))
            pygame.draw.rect(surf, edge, (x - 9, y - 22, 18, 32), 1)
            pygame.draw.rect(surf, cap, (x - 11, y - 26, 22, 5))
            pygame.draw.rect(surf, edge, (x - 11, y - 26, 22, 5), 1)
            pygame.draw.rect(surf, cap, (x - 11, y + 8, 22, 5))
            pygame.draw.rect(surf, edge, (x - 11, y + 8, 22, 5), 1)
            if filled:
                # Fish lying across the capital, head left. Static.
                fish_body = (90, 110, 140)
                fish_dark = (50, 60, 80)
                belly = (180, 190, 200)
                pygame.draw.ellipse(surf, fish_body,
                                    (x - 9, y - 33, 18, 7))
                pygame.draw.ellipse(surf, fish_dark,
                                    (x - 9, y - 33, 18, 7), 1)
                pygame.draw.ellipse(surf, belly,
                                    (x - 7, y - 31, 14, 4))
                pygame.draw.polygon(surf, fish_body,
                                    [(x + 8, y - 30), (x + 12, y - 33),
                                     (x + 12, y - 27)])
                pygame.draw.circle(surf, (20, 20, 30),
                                   (x - 6, y - 30), 1)

    def _draw_doorframe(self, surf, x, y):
        """The Threshold frame (flat pitch-0 fallback; the tilt view stands it up as
        real geometry via rendering/props.py). A plain pale frame around an EMPTY
        opening -- a door with no wall. Nothing fills the gap (you see through
        it); walking through it is the seal."""
        pal = (152, 150, 158)
        dk = (74, 72, 80)
        # opening: a hair darker than the apron so it reads as 'through to the
        # cave behind', with NO glow -- it is only a frame.
        pygame.draw.rect(surf, (24, 23, 28), (x - 10, y - 46, 20, 46))
        pygame.draw.rect(surf, pal, (x - 14, y - 48, 5, 48))            # left jamb
        pygame.draw.rect(surf, pal, (x + 9, y - 48, 5, 48))            # right jamb
        pygame.draw.rect(surf, pal, (x - 14, y - 48, 28, 5))           # lintel
        pygame.draw.rect(surf, dk, (x - 14, y - 48, 28, 48), 1)
        _ground_shadow(surf, x, y + 1, 14, 4, 80)

    def _draw_cellar_hatch(self, surf, x, y):
        """A floor hatch -- wood box flush to the ground, plank seams,
        iron pull-ring centred on top. Identical visual to the `L`
        ladder-down tile but drawn as a decoration so the scene can
        gate the trip down behind an E-press handler instead of an
        auto-transition. Used in the barn to replace the chest-as-
        trapdoor placeholder."""
        pygame.draw.rect(surf, (110, 80, 50), (x - 12, y - 12, 24, 24))
        pygame.draw.rect(surf, (60, 38, 24), (x - 12, y - 12, 24, 24), 2)
        pygame.draw.line(surf, (60, 38, 24),
                         (x - 12, y - 4), (x + 12, y - 4), 1)
        pygame.draw.line(surf, (60, 38, 24),
                         (x - 12, y + 4), (x + 12, y + 4), 1)
        pygame.draw.rect(surf, (50, 50, 60), (x - 4, y - 3, 8, 4))
        pygame.draw.rect(surf, (30, 30, 38), (x - 4, y - 3, 8, 4), 1)
        pygame.draw.circle(surf, (180, 180, 200), (x, y + 2), 4, 2)
        pygame.draw.circle(surf, (90, 90, 110), (x, y + 2), 4, 1)

    def _draw_shaft_ladder(self, surf, x, y):
        """The way up from the shaft floor: a single rope hanging from a hatch
        overhead (flat pitch-0 fallback; the tilt view draws it as a real 3D rope
        rising into the ceiling via rendering/props.py)."""
        # hatch frame + dark shaft at the top
        pygame.draw.rect(surf, (6, 6, 8), (x - 10, y - 50, 20, 9))
        pygame.draw.rect(surf, (88, 62, 36), (x - 12, y - 52, 24, 11), 2)
        pts = [(int(x + math.sin(f / 10.0 * 7 + 0.5) * 2.4), int(y + 10 - f / 10.0 * 54))
               for f in range(11)]
        pygame.draw.lines(surf, (92, 72, 44), False, pts, 4)      # rope body/edge
        pygame.draw.lines(surf, (150, 128, 88), False, pts, 2)    # rope mid
        for f in (0.34, 0.66):                                    # climbing knots
            pygame.draw.circle(surf, (120, 98, 60), pts[int(f * 10)], 3)
        pygame.draw.ellipse(surf, (120, 98, 60), (x - 6, y + 7, 12, 5), 2)  # frayed coil
        _ground_shadow(surf, x, y + 10, 8, 3, 80)

    def _draw_rope(self, surf, x, y):
        """A hanging cord -- a bell-pull / hoist line. A slightly kinked
        vertical rope with a frayed knot at the bottom; hangs from the
        prop placed above it. ~22px tall."""
        cord = (132, 110, 70)
        cord_dk = (92, 74, 44)
        top, bot = y - 11, y + 11
        midx = x + 1
        pygame.draw.line(surf, cord_dk, (x, top), (midx, y), 2)
        pygame.draw.line(surf, cord_dk, (midx, y), (x, bot), 2)
        pygame.draw.line(surf, cord, (x, top), (midx, y), 1)
        pygame.draw.line(surf, cord, (midx, y), (x, bot), 1)
        # Frayed knot.
        pygame.draw.circle(surf, cord_dk, (x, bot), 2)
        pygame.draw.line(surf, cord, (x - 2, bot + 2), (x, bot), 1)
        pygame.draw.line(surf, cord, (x + 2, bot + 3), (x, bot), 1)
