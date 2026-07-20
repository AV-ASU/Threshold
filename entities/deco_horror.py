"""Horror decoration draw methods (split from decoration.py 2026-07).

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


class DecoHorrorMixin:
    def _draw_watching_wound(self, surf, x, y):
        """Vertical slit-cut on a stone or bark surface, with a wet
        glint at the edge that catches the player's facing. Reads as
        an open wound rather than an eye -- no iris, no pupil. The
        glint is what tracks; the wound itself is just a dark cut.

        Same `size` kwarg as `watching_eye` (small / large). Designed
        to be placed alongside watching_eye decorations so the cult
        marks read as a mix of literal eyes and abstract cuts. The
        gaze sensation comes from the moving glint, not from a pupil
        the player can see directly."""
        size = self.kwargs.get("size", "small")
        if size == "large":
            slit_w, slit_h = 6, 28
            glint_w = 4
        else:
            slit_w, slit_h = 3, 14
            glint_w = 2
        # The cut itself -- a dark vertical slot. Slight outer halo
        # of bruised tissue where the surface has parted.
        pygame.draw.ellipse(surf, (60, 30, 32),
                            (x - slit_w // 2 - 2, y - slit_h // 2 - 2,
                             slit_w + 4, slit_h + 4))
        pygame.draw.ellipse(surf, (8, 4, 8),
                            (x - slit_w // 2, y - slit_h // 2,
                             slit_w, slit_h))
        # A thin rim of dried-blood smear around the rim.
        pygame.draw.ellipse(surf, (90, 22, 28),
                            (x - slit_w // 2, y - slit_h // 2,
                             slit_w, slit_h), 1)
        # The wet glint -- a 1-2px streak inside the cut. Snaps to one
        # of 8 compass positions inside the slit based on where the
        # player is standing. The discrete shift is what catches
        # peripheral vision; the player notices the wound's eye dart
        # as they cross a diagonal.
        ox, oy = _compass_offset(
            self.player_world[0] - self.x,
            self.player_world[1] - self.y,
            travel_x=max(1, slit_w // 4),
            travel_y=max(1, slit_h // 3),
        )
        # A slow wet pulse so the glint doesn't sit static.
        pulse = 0.7 + 0.3 * math.sin(self.t * 1.4 + self.seed)
        glint_alpha = max(40, int(180 * pulse))
        layer = pygame.Surface((slit_w + 4, slit_h + 4),
                                pygame.SRCALPHA)
        pygame.draw.rect(layer, (220, 210, 200, glint_alpha),
                         (slit_w // 2 + 2 + ox - glint_w // 2,
                          slit_h // 2 + oy,
                          glint_w, 2))
        surf.blit(layer, (x - (slit_w + 4) // 2,
                          y - (slit_h + 4) // 2))

    def _draw_watching_eye(self, surf, x, y):
        """An eye that always looks at the player. The pupil rotates
        toward the player's world position each frame using the
        class-level self.player_world cache. Random blink every
        few seconds. Sized via self.kwargs.get('size', 'small') to
        either 'small' (sclera ~10px) or 'large' (~22px) so the same
        kind serves close embedded eyes and far peripheral ones.

        The eye is meant to be placed where the player will see it
        only out of the corner of their attention -- in tree lines,
        wall faces, water surfaces. The pupil following them is the
        beat that makes the player feel observed.

        Cosmetic upgrades: bloodshot vein lines etched into the sclera
        (deterministic per-seed so each eye has its own pattern), and
        a vertical-slit pupil variant when `slit=True` is passed via
        kwargs -- used in the late-game cult sites to push the gaze
        from human to inhuman."""
        # THRESHOLD redesign: drop the cartoon-eyeball palette. The eye
        # now reads as something *carved* or *sunken* into the surface
        # it sits on -- a narrow lid-slit framing a recessed iris that
        # tracks the player. No bright sclera, no catchlight, no
        # candy-coloured iris. Same kwargs (`size`, `slit`) so all
        # existing scene wiring keeps working.
        #
        # 8-WAY DIRECTIONAL TRACKING: instead of a continuous pupil
        # offset (which feels like a smooth analog stick), the iris
        # now snaps to ONE of eight compass positions (N / NE / E /
        # SE / S / SW / W / NW) based on the player's bearing from
        # this eye. The discrete jump catches peripheral vision
        # better -- the player notices the eye SHIFT when they
        # cross a diagonal, instead of an iris that just slowly
        # drifts. Reads as someone making a deliberate look.
        size = self.kwargs.get("size", "small")
        slit = self.kwargs.get("slit", False)
        if size == "large":
            socket_w, socket_h = 26, 12
            pupil_r = 5
            travel = 6
        else:
            socket_w, socket_h = 14, 7
            pupil_r = 2
            travel = 3
        # Blink schedule: every ~6s, the slit closes for 0.18s.
        cycle = 6.0
        local = (self.t + self.seed * 0.1) % cycle
        blinking = local > (cycle - 0.18)
        # Recessed socket -- a dark horizontal hollow carved into the
        # surface. Slight inner shadow to suggest depth.
        pygame.draw.ellipse(surf, (16, 12, 16),
                            (x - socket_w // 2, y - socket_h // 2,
                             socket_w, socket_h))
        pygame.draw.ellipse(surf, (4, 2, 6),
                            (x - socket_w // 2, y - socket_h // 2,
                             socket_w, socket_h), 1)
        if blinking:
            # Lid closed -- the slit goes opaque. No pupil this frame.
            pygame.draw.rect(surf, (24, 18, 22),
                             (x - socket_w // 2, y - 1,
                              socket_w, 2))
            return
        # Bucket the player bearing into one of 8 compass octants.
        # Vertical travel halved so the iris stays inside the
        # horizontal socket on N/S looks.
        ox, oy = _compass_offset(
            self.player_world[0] - self.x,
            self.player_world[1] - self.y,
            travel, max(1, travel // 2),
        )
        # Iris -- desaturated dried-blood ring rather than purple.
        # Smaller than before so the eye doesn't bulge out of the socket.
        if pupil_r >= 3:
            pygame.draw.circle(surf, (90, 30, 30),
                               (x + ox, y + oy), pupil_r)
        if slit:
            # Vertical-slit pupil -- inhuman, animal. Two pixels wide.
            slit_w = 1
            slit_h = max(2, pupil_r + 1)
            pygame.draw.ellipse(surf, (4, 2, 6),
                                (x + ox - slit_w, y + oy - slit_h // 2,
                                 slit_w * 2, slit_h))
        else:
            pygame.draw.circle(surf, (4, 2, 6),
                               (x + ox, y + oy), max(1, pupil_r - 1))
        # Faint wet glint at the socket's inner edge -- on the side
        # the iris is looking from, so the moisture catches with
        # the gaze direction.
        if ox > 0:
            glint_x = x - (socket_w // 2) + 2
        elif ox < 0:
            glint_x = x + (socket_w // 2) - 2
        else:
            # Pure N / S look -- glint sits centre.
            glint_x = x
        pygame.draw.rect(surf, (60, 50, 50),
                         (glint_x, y, 1, 1))

    def _draw_passing_silhouette(self, surf, x, y):
        # One-shot scripted silhouette: a dark vertical strip drifts
        # left-to-right across the window glass over `dur` seconds
        # starting at `t0`. Outside that window the decoration is
        # invisible; the scene removes it after dur+1.
        t0 = self.kwargs.get("t0", 0.0)
        dur = self.kwargs.get("dur", 1.8)
        if not t0:
            return
        elapsed = time.time() - t0
        if elapsed < 0.0 or elapsed > dur:
            return
        phase = elapsed / dur            # 0..1 across the glass
        # Window glass spans roughly +/-10px around (x, y). Strip is
        # 3px wide, 18px tall; soft edges via per-column alpha.
        fx = int(x - 12 + phase * 24)
        strip = pygame.Surface((4, 20), pygame.SRCALPHA)
        for col_x in range(4):
            edge = 1.0 - abs(col_x - 1.5) / 1.8
            a = max(0, int(170 * edge))
            pygame.draw.rect(strip, (8, 6, 14, a), (col_x, 0, 1, 20))
        surf.blit(strip, (fx, y - 10))

    def _draw_bloody_pile(self, surf, x, y):
        # Lumpy mound of meat / cloth scraps in a pool of blood. Used
        # in the barn after the doll is taken -- the room dirties
        # immediately, this deco appears next to the chest. Static
        # (no animation): the horror is in finding it, not watching it.
        pool = (90, 8, 14)
        dark = (50, 4, 10)
        flesh = (130, 50, 50)
        scrap = (160, 110, 100)
        # Pool of blood underneath
        pygame.draw.ellipse(surf, pool, (x - 14, y - 2, 28, 12))
        pygame.draw.ellipse(surf, dark, (x - 9, y + 2, 18, 6))
        # Mound (three lumps)
        pygame.draw.ellipse(surf, flesh, (x - 10, y - 8, 14, 10))
        pygame.draw.ellipse(surf, flesh, (x - 2, y - 10, 12, 9))
        pygame.draw.ellipse(surf, flesh, (x + 1, y - 5, 10, 8))
        pygame.draw.ellipse(surf, dark, (x - 10, y - 8, 14, 10), 1)
        pygame.draw.ellipse(surf, dark, (x - 2, y - 10, 12, 9), 1)
        # Scraps poking out
        pygame.draw.line(surf, scrap, (x - 6, y - 4), (x - 9, y - 8), 1)
        pygame.draw.line(surf, scrap, (x + 4, y - 6), (x + 8, y - 9), 1)

    def _draw_bloodstain(self, surf, x, y):
        # static blob
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 8, y - 3, 16, 8))
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 4, y, 8, 4))

    def _draw_bloody_handprint(self, surf, x, y):
        """A blood-red handprint pressed onto a surface, with three
        downward streaks where the fingers dragged on the way off.
        Palm sits darker than the fingertip pads -- the hand pushed
        off and smeared as it left."""
        palm = (140, 20, 28)
        drip = (80, 10, 18)
        bright = (180, 32, 36)
        # Palm
        pygame.draw.ellipse(surf, palm, (x - 5, y - 2, 10, 7))
        # Four finger pads + thumb
        pygame.draw.circle(surf, bright, (x - 4, y - 5), 1)
        pygame.draw.circle(surf, bright, (x - 1, y - 6), 1)
        pygame.draw.circle(surf, bright, (x + 2, y - 6), 1)
        pygame.draw.circle(surf, bright, (x + 5, y - 4), 1)
        pygame.draw.circle(surf, bright, (x - 6, y - 1), 1)
        # Downward drag streaks
        pygame.draw.line(surf, drip, (x - 3, y + 4), (x - 3, y + 12), 1)
        pygame.draw.line(surf, drip, (x, y + 4), (x, y + 14), 1)
        pygame.draw.line(surf, drip, (x + 3, y + 4), (x + 3, y + 11), 1)

    def _draw_body(self, surf, x, y):
        # A slumped, fallen body. The kit reads at a glance: helmet beside the
        # head, spear on the ground, blood pool. Static -- this is a
        # decoration, not an NPC. Disappears after 2 re-entries via the
        # scene's on_enter logic.
        # Blood pool
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 14, y + 2, 28, 8))
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 11, y + 1, 22, 6))
        # Slumped torso (tabard-grey)
        pygame.draw.rect(surf, (110, 110, 130), (x - 9, y - 6, 18, 10))
        pygame.draw.rect(surf, (50, 50, 70), (x - 9, y - 6, 18, 10), 1)
        # Helmet, fallen sideways to the left of the body
        pygame.draw.rect(surf, (140, 140, 160), (x - 16, y - 4, 10, 7))
        pygame.draw.rect(surf, (40, 40, 60), (x - 14, y - 2, 4, 2))
        # Spear, dropped diagonally to the right
        pygame.draw.line(surf, (60, 40, 25), (x + 6, y - 4), (x + 18, y + 6), 2)
        pygame.draw.polygon(surf, (200, 200, 220),
                            [(x + 18, y + 6), (x + 14, y + 4), (x + 19, y + 3)])

    def _draw_gore(self, surf, x, y):
        # A slumped, broken figure. Read as "could be a person"; not an
        # animated NPC. Wide blood pool around it. The crutch pickup sits
        # adjacent so the noun does the heavy lifting.
        # Pool of blood (large, irregular-feeling via two ellipses)
        pygame.draw.ellipse(surf, (60, 6, 10), (x - 18, y, 36, 14))
        pygame.draw.ellipse(surf, (90, 10, 14), (x - 14, y - 2, 28, 10))
        pygame.draw.ellipse(surf, (40, 4, 8), (x - 6, y + 2, 12, 6))
        # Slumped torso
        pygame.draw.rect(surf, (60, 30, 30), (x - 9, y - 12, 18, 14))
        pygame.draw.rect(surf, (40, 18, 22), (x - 9, y - 12, 18, 14), 1)
        # Splayed limb
        pygame.draw.rect(surf, (60, 30, 30), (x + 8, y - 4, 12, 5))
        # Head, turned away
        pygame.draw.circle(surf, (80, 50, 50), (x - 6, y - 14), 5)
        # A few darker smudges for texture
        pygame.draw.line(surf, (30, 4, 6), (x - 10, y + 4), (x + 12, y + 6), 1)
        pygame.draw.line(surf, (30, 4, 6), (x - 8, y + 8), (x + 10, y + 8), 1)

    def _draw_hanging_figure(self, surf, x, y):
        """Vague humanoid silhouette suspended from a rope going off-
        tile upward. Slumped, no facial detail, very small slow sway.
        Used in the deep tree band of brimley and the cornfield's
        far rows."""
        sway = math.sin(self.t * 0.45 + self.seed) * 2.6
        sx_ = int(sway)
        # Long rope going up out of frame
        pygame.draw.line(surf, (140, 110, 70),
                         (x, y - 32), (x + sx_, y - 14), 1)
        # Knot at neck
        pygame.draw.circle(surf, (90, 60, 30), (x + sx_, y - 14), 2)
        # Slumped head
        pygame.draw.circle(surf, (20, 16, 22), (x + sx_, y - 10), 4)
        # Body / robes (trapezoid hanging straight down)
        pygame.draw.polygon(surf, (16, 12, 18), [
            (x + sx_ - 5, y - 8), (x + sx_ + 5, y - 8),
            (x + sx_ + 7, y + 12), (x + sx_ - 7, y + 12),
        ])
        pygame.draw.polygon(surf, (4, 2, 6), [
            (x + sx_ - 5, y - 8), (x + sx_ + 5, y - 8),
            (x + sx_ + 7, y + 12), (x + sx_ - 7, y + 12),
        ], 1)
        # Limp arms drooping at sides
        pygame.draw.line(surf, (16, 12, 18),
                         (x + sx_ - 5, y - 6), (x + sx_ - 7, y + 4), 2)
        pygame.draw.line(surf, (16, 12, 18),
                         (x + sx_ + 5, y - 6), (x + sx_ + 7, y + 4), 2)
        # Limp feet
        pygame.draw.line(surf, (8, 6, 10),
                         (x + sx_ - 4, y + 12), (x + sx_ - 4, y + 14), 2)
        pygame.draw.line(surf, (8, 6, 10),
                         (x + sx_ + 4, y + 12), (x + sx_ + 4, y + 14), 2)

    def _draw_claw_marks(self, surf, x, y):
        """Five parallel deep gouges torn diagonally across a wall.
        Each gouge has a rawer outer band and a near-black floor so
        it reads as cut INTO the surface, not painted on. Stroke
        jitter is per-instance via self.seed."""
        rng = random.Random(self.seed)
        outer = (60, 30, 30)
        deep = (16, 6, 10)
        for i in range(5):
            ox = -10 + i * 5 + rng.randint(-1, 1)
            top = (x + ox, y - 8)
            bot = (x + ox + 4 + rng.randint(-1, 1), y + 8)
            pygame.draw.line(surf, outer, top, bot, 2)
            pygame.draw.line(surf, deep, top, bot, 1)

    def _draw_symbol(self, surf, x, y):
        # Pulsing arcane sigil on the floor. Two concentric circles + an
        # inner triangle, all in violet. Pulses size with a slow sine so
        # it reads as 'active' rather than painted.
        pulse = 1.0 + math.sin(self.t * 1.5 + self.seed) * 0.18
        col = (180, 80, 220)
        r1 = max(2, int(14 * pulse))
        r2 = max(2, int(8 * pulse))
        pygame.draw.circle(surf, col, (x, y), r1, 1)
        pygame.draw.circle(surf, col, (x, y), r2, 1)
        h = max(2, int(8 * pulse))
        pygame.draw.polygon(surf, col, [
            (x, y - h),
            (x - h, y + h // 2),
            (x + h, y + h // 2),
        ], 1)

    def _draw_binding_sigil(self, surf, x, y):
        # A golden triangle scratched into the stone, point up. Three
        # bright lines drift across it at three different slow periods
        # regardless of the player -- the sigil is doing its work
        # whether anyone watches it or not.
        gold      = (200, 170, 60)
        gold_lo   = (130, 100, 30)
        h = 18
        pts = [(x, y - h), (x - h, y + h - 4), (x + h, y + h - 4)]
        pygame.draw.polygon(surf, gold_lo, pts)
        pygame.draw.polygon(surf, gold, pts, 1)
        for i, period in enumerate((9.0, 13.0, 17.0)):
            f = ((self.t / period) + i * 0.31) % 1.0
            ly = int(y - h + f * (h * 2 - 4))
            tri_t = (ly - (y - h)) / float(h * 2 - 4)
            w = max(1, int(h * tri_t))
            pygame.draw.line(surf, gold, (x - w, ly), (x + w, ly), 1)

    def _draw_wall_sign(self, surf, x, y):
        """The Yellow Sign daubed on a WALL face rather than the floor: the same
        crude-mask glyph as `yellow_sign`, but registered in `_WALL_DECO_KINDS`
        so under tilt it hangs up the vertical apse wall (the Sign Chamber
        tableau shows the Sign breathing on the wall, not warped onto the
        floor). Draw is identical -- only the tilt-set membership differs."""
        self._draw_yellow_sign(surf, x, y)

    def _draw_altar_mask(self, surf, x, y):
        """Flat (pitch-0) fallback for the Pallid Mask on the altar; the tilt
        camera draws the real volume (rendering.props._draw_altar_mask_solid)."""
        pygame.draw.ellipse(surf, (204, 200, 192), (x - 5, y - 7, 10, 14))
        pygame.draw.ellipse(surf, (150, 148, 142), (x - 5, y - 7, 10, 14), 1)
        for ex in (-2, 2):
            pygame.draw.circle(surf, (10, 9, 11), (x + ex, y - 1), 1)
            pygame.draw.circle(surf, (180, 120, 40), (x + ex, y), 1)

    def _draw_yellow_sign(self, surf, x, y):
        """The Yellow Sign -- His face, daubed in paint. CANON (NARRATIVE
        §4 #5): the Sign IS the Pallid Mask, "His face made an object",
        so what the cult paints is a crude mask: a broken oval outline,
        two thumb-press sockets, NO mouth (the flashback-mask grammar),
        and paint runs where the hand hurried. Primitive yet put
        together. Seeded per instance -- every daub in the world is a
        different hand on a different night -- and it breathes on the
        same faint pulse + sickly light pool as the old glyph (this is
        still the cosmic-horror anchor; it repeats at scale across the
        Scriptorium and Sign Chamber). SLIGHTLY ANIMATED, all of it
        wrongness-quiet: the breath pulse; the chin runs creep like paint
        that never dried; and every few seconds one socket catches a
        faint gold fleck set toward the player (the watching_eye's
        player_world cache) -- the daub watches."""
        rng = random.Random(self.seed)
        pulse = 1.0 + math.sin(self.t * 1.1 + self.seed) * 0.08
        _light_pool(surf, int(x), int(y), int(30 * pulse), (206, 188, 84),
                    int(46 + 10 * math.sin(self.t * 1.1 + self.seed)))
        col = (196, 178, 72)
        dark = (92, 80, 28)
        # The sockets go DEEP black -- darker than any ground they're
        # painted on, so the empty stare reads as holes, not smudges.
        sock = (6, 5, 4)
        R = 13 * pulse
        rx = R * rng.uniform(0.66, 0.74)
        ry = R * rng.uniform(0.96, 1.06)
        # Broken outline: most strokes survive (put together), a few
        # gaps where the hand lifted (primitive).
        n = 16
        pts = []
        for i in range(n):
            a = i / n * math.tau
            w = rng.uniform(-2.4, 2.4)
            pts.append((x + math.cos(a) * (rx + w),
                        y + math.sin(a) * (ry + w)))
        for i in range(n):
            if rng.random() < 0.78:
                a, b = pts[i], pts[(i + 1) % n]
                pygame.draw.line(surf, dark, a, b, 5)
                pygame.draw.line(surf, col, a, b, 3)
        # Thumb-press sockets, mismatched, set off-centre. No mouth.
        sockets = []
        for fx, fy, fr in ((-0.40, -0.25, 0.20), (0.43, -0.18, 0.23)):
            sxp, syp = int(x + rx * fx), int(y + ry * fy)
            srr = max(2, int(R * fr))
            sockets.append((sxp, syp, srr))
            pygame.draw.circle(surf, sock, (sxp, syp), srr)
        # THE GLEAM: every few seconds (seeded period) one socket
        # catches a faint gold fleck, set toward wherever the player
        # stands (the same player_world cache the watching_eye uses).
        # In and out in under half a second -- seen mostly from the
        # corner of the eye; the daub watches.
        period = 7.0 + (self.seed % 7)
        ph = (self.t + self.seed * 0.37) % period
        if ph < 0.45:
            fade = 1.0 - abs(ph / 0.45 * 2.0 - 1.0)
            sxp, syp, srr = sockets[self.seed % 2]
            pwx, pwy = self.player_world
            dx, dy = pwx - x, pwy - y
            d = math.hypot(dx, dy) or 1.0
            off = max(1, srr - 2)
            gx = int(sxp + dx / d * off)
            gy = int(syp + dy / d * off)
            gleam = tuple(int(sc + (gc - sc) * fade)
                          for sc, gc in zip(sock, (188, 164, 70)))
            pygame.draw.circle(surf, gleam, (gx, gy), 1)
        # Two paint runs off the chin, one trailing thinner. They CREEP
        # -- a very slow lengthening drift, wet paint that never dried.
        creep = 1.0 + 0.30 * math.sin(self.t * 0.13 + self.seed * 0.7)
        for dx, fl in ((-R * 0.2, 1.0), (R * 0.12, 0.7)):
            rl = rng.randint(int(R * 0.4), int(R * 0.9)) * fl * creep
            y0 = y + ry * 0.9
            pygame.draw.line(surf, dark, (x + dx, y0),
                             (x + dx, y0 + rl), 2)
            pygame.draw.line(surf, col, (x + dx, y0),
                             (x + dx, y0 + rl * 0.7), 1)

    def _draw_phantom_mark(self, surf, x, y):
        # A small chalk symbol. Registered as a floor decal
        # (_FLOOR_DECAL_KINDS), so under the tilt it warps flat onto the
        # floorboards (NOT a wall mark, despite reading like a scratched
        # sigil). Static (no anim). Shape is suggestive but doesn't match
        # any other game mark.
        pygame.draw.line(surf, (220, 220, 230), (x - 6, y - 4), (x + 6, y - 4), 1)
        pygame.draw.line(surf, (220, 220, 230), (x, y - 6), (x, y + 4), 1)
        pygame.draw.line(surf, (220, 220, 230), (x - 4, y + 4), (x + 4, y + 4), 1)
        pygame.draw.circle(surf, (220, 220, 230), (x, y), 1)

    def _draw_chalk_door(self, surf, x, y):
        """A door drawn in chalk where no door is -- the cult's compulsion
        (the door's dream made into a crude life-size drawing). A floor decal
        (see _FLOOR_DECAL_KINDS): a faint 'step-down' interior, jambs, lintel,
        a knob it cannot open. 2026-07 rework: DIMMER and SMALLER -- worn
        chalk with skips where the stick lifted, not bright doubled strokes
        (the old draw read as glowing white rectangles), and sized to stay
        inside its tile's open floor."""
        rng = random.Random(self.seed * 7 + 3)
        chalk = (196, 192, 180)
        faint = (134, 131, 121)
        w, h = 24, 38
        L, R, T, B = x - w // 2, x + w // 2, y - h // 2, y + h // 2
        # a faint dark wash inside the frame -- the "down through it" void
        void = pygame.Surface((w - 4, h - 4), pygame.SRCALPHA)
        void.fill((6, 6, 9, 60))
        surf.blit(void, (L + 2, T + 2))

        def hand(x0, y0, x1, y1, col, wdt=1):
            # a hand stroke in 3 segments, one skipped where the chalk
            # lifted -- worn, not stamped
            skip = rng.randint(0, 2)
            for i in range(3):
                if i == skip and rng.random() < 0.7:
                    continue
                fx0 = x0 + (x1 - x0) * i / 3.0
                fy0 = y0 + (y1 - y0) * i / 3.0
                fx1 = x0 + (x1 - x0) * (i + 1) / 3.0
                fy1 = y0 + (y1 - y0) * (i + 1) / 3.0
                pygame.draw.line(surf, col,
                                 (fx0 + rng.randint(-1, 1), fy0 + rng.randint(-1, 1)),
                                 (fx1 + rng.randint(-1, 1), fy1 + rng.randint(-1, 1)),
                                 wdt)
        hand(L, B, L, T, chalk, 2)           # left jamb
        hand(R, B, R, T, chalk, 2)           # right jamb
        hand(L, T, R, T, chalk, 2)           # lintel
        hand(L, B, R, B, faint, 1)           # threshold line
        # the knob -- the cruel detail; there is nothing to open
        pygame.draw.circle(surf, chalk, (R - 4, y + 3), 1)
        # a little chalk dust where the drawer knelt
        for _ in range(5):
            px = max(0, min(surf.get_width() - 1, x + rng.randint(-w // 2, w // 2)))
            py = max(0, min(surf.get_height() - 1, y + rng.randint(-h // 2, h // 2)))
            surf.set_at((px, py), faint)

    def _draw_chalk_door_wall(self, surf, x, y):
        """The chalk door drawn on a WALL instead of the floor (the same cult
        compulsion, hung as a life-size doorway on a `_WALL_DECO` billboard).
        Taller than the floor decal ('a door is tall, not a small plaque',
        scenes/terrain.py); worn chalk strokes with skips, a faint dark mouth,
        a knob that opens nothing. (Was missing, so it rendered as the magenta
        _draw_unknown square, 2026-07.)"""
        rng = random.Random(self.seed * 7 + 11)
        chalk = (196, 192, 180)
        faint = (134, 131, 121)
        w, h = 26, 48
        L, R, T, B = x - w // 2, x + w // 2, y - h // 2, y + h // 2
        # the faint dark "way through" behind the drawn frame
        mouth = pygame.Surface((w - 4, h - 4), pygame.SRCALPHA)
        mouth.fill((6, 6, 9, 70))
        surf.blit(mouth, (L + 2, T + 2))

        def hand(x0, y0, x1, y1, col, wdt=1):
            skip = rng.randint(0, 2)
            for i in range(3):
                if i == skip and rng.random() < 0.7:
                    continue
                fx0 = x0 + (x1 - x0) * i / 3.0
                fy0 = y0 + (y1 - y0) * i / 3.0
                fx1 = x0 + (x1 - x0) * (i + 1) / 3.0
                fy1 = y0 + (y1 - y0) * (i + 1) / 3.0
                pygame.draw.line(surf, col,
                                 (fx0 + rng.randint(-1, 1), fy0 + rng.randint(-1, 1)),
                                 (fx1 + rng.randint(-1, 1), fy1 + rng.randint(-1, 1)),
                                 wdt)
        hand(L, B, L, T, chalk, 2)           # left jamb
        hand(R, B, R, T, chalk, 2)           # right jamb
        hand(L, T, R, T, chalk, 2)           # lintel
        hand(L + 3, y, R - 3, y, faint, 1)   # a cross-rail, panelled door
        pygame.draw.circle(surf, chalk, (R - 4, y + 4), 1)   # the knob
        for _ in range(5):                                   # chalk dust
            px = max(0, min(surf.get_width() - 1, x + rng.randint(-w // 2, w // 2)))
            py = max(0, min(surf.get_height() - 1, y + rng.randint(-h // 2, h // 2)))
            surf.set_at((px, py), faint)

    def _draw_chalkboard(self, surf, x, y):
        """A WIDE schoolroom chalkboard on the wall (spans 4-5 tiles): the
        children's faded lesson ghosted under the cult's compulsion -- a doorway
        chalked over and over, smaller and smaller, marching off into a corner.
        Wall-mounted; draw_wall_deco stretches it along the wall span."""
        HW, HH = 52, 15                                                    # half size
        pygame.draw.rect(surf, (96, 66, 38), (x - HW, y - HH, HW * 2, HH * 2))      # frame
        pygame.draw.rect(surf, (60, 40, 22), (x - HW, y - HH, HW * 2, HH * 2), 2)
        pygame.draw.rect(surf, (28, 36, 32),
                         (x - HW + 4, y - HH + 4, HW * 2 - 8, HH * 2 - 8))  # slate
        for i in range(9):                                                 # ghost lesson
            pygame.draw.rect(surf, (96, 110, 100),
                             (x - HW + 10 + i * 7, y - HH + 7, 4, 5), 1)
        cx, cy, s = x - HW + 13, y + 3.0, 15.0                             # the door, shrinking
        for k in range(8):
            col = (214, 218, 210) if k == 0 else (150, 162, 150)
            pygame.draw.rect(surf, col, (int(cx), int(cy - s),
                                         max(2, int(s * 0.62)), int(s)), 1)
            cx += s * 0.55 + 3; cy += 1.0; s = max(3.0, s * 0.82)
        for tx in (x - HW + 24, x - HW + 34, x - HW + 44):                 # tally scratches
            pygame.draw.line(surf, (120, 132, 122), (tx, y + HH - 9),
                             (tx, y + HH - 5), 1)
        pygame.draw.rect(surf, (70, 50, 30), (x - HW + 4, y + HH - 4, HW * 2 - 8, 3))  # tray
        pygame.draw.rect(surf, (186, 192, 184), (x - HW + 14, y + HH - 3, 12, 1))      # dust

    def _draw_child_drawing(self, surf, x, y):
        """A child's crayon drawing dropped on the floor. Most are ordinary (a
        house, a sun, little figures); some are wrong -- a black doorway and a
        tall yellow figure beside it. Varies by seed. A floor decal."""
        pygame.draw.rect(surf, (226, 222, 208), (x - 8, y - 10, 16, 20))    # paper
        pygame.draw.rect(surf, (182, 178, 164), (x - 8, y - 10, 16, 20), 1)
        v = self.seed % 3
        if v == 0:                                                         # house + sun + kid
            pygame.draw.rect(surf, (150, 80, 60), (x - 5, y, 7, 6))
            pygame.draw.polygon(surf, (120, 60, 50), [(x - 6, y), (x - 1, y - 4), (x + 3, y)])
            pygame.draw.circle(surf, (218, 188, 60), (x + 5, y - 6), 2)
            for r in range(4):
                a = r * 1.571
                pygame.draw.line(surf, (218, 188, 60), (x + 5, y - 6),
                                 (int(x + 5 + math.cos(a) * 4), int(y - 6 + math.sin(a) * 4)), 1)
            pygame.draw.circle(surf, (60, 80, 140), (x - 4, y - 5), 1)
            pygame.draw.line(surf, (60, 80, 140), (x - 4, y - 4), (x - 4, y - 1), 1)
        elif v == 1:                                                       # a row of figures
            for i in range(4):
                fx = x - 6 + i * 4
                pygame.draw.circle(surf, (40, 40, 50), (fx, y - 2), 1)
                pygame.draw.line(surf, (40, 40, 50), (fx, y - 1), (fx, y + 3), 1)
        else:                                                              # the wrong one
            pygame.draw.rect(surf, (18, 16, 20), (x - 4, y - 6, 6, 12))    # black door
            pygame.draw.circle(surf, (210, 180, 40), (x + 4, y - 8), 2)    # yellow figure
            pygame.draw.line(surf, (210, 180, 40), (x + 4, y - 7), (x + 4, y + 6), 2)

    def _draw_apology_wall(self, surf, x, y):
        """A patch of wall covered in scratched 'I'M SORRY' text,
        repeated overlapping rows in cramped uneven handwriting.
        The lines are deterministic per-instance via self.seed so
        adjacent placements don't share identical patterns. Drawn
        as short white scratches so the text reads as carved/etched
        rather than written. Static -- no animation."""
        rng = random.Random(self.seed)
        col = (210, 210, 220)
        # 4 stacked rows of "I'M SORRY" using simple stroke shapes
        # for each letter. Each row jittered slightly horizontally
        # so the text feels written by hand, not typeset.
        word = "IM SORRY"
        for row in range(4):
            ry = y - 14 + row * 8
            rx = x - 22 + rng.randint(-2, 2)
            for ch in word:
                if ch == " ":
                    rx += 3
                    continue
                self._draw_etched_char(surf, ch, rx, ry, col, rng)
                rx += 5
        # Outer scratches around the patch suggest more text just
        # off the visible area.
        for _ in range(6):
            sx = x + rng.randint(-22, 22)
            sy = y + rng.randint(-14, 14)
            ex = sx + rng.randint(-3, 3)
            ey = sy + rng.randint(-2, 2)
            pygame.draw.line(surf, col, (sx, sy), (ex, ey), 1)

    def _draw_polaroid_wall(self, surf, x, y):
        """The polaroid family pinned to the bedroom wall above the bed
        after polaroid_taken flips. Reads as a photo frame containing
        the four-figure family from the polaroid item -- tall man,
        blonde woman, small boy, small girl. The frame is intact;
        the figures all face out, looking at the bed."""
        # Frame
        pygame.draw.rect(surf, (90, 60, 40), (x - 9, y - 12, 18, 16))
        pygame.draw.rect(surf, (40, 25, 15), (x - 9, y - 12, 18, 16), 1)
        # Photo paper
        pygame.draw.rect(surf, (210, 200, 180), (x - 7, y - 10, 14, 12))
        # Tall man (centre)
        pygame.draw.rect(surf, (60, 50, 70), (x - 1, y - 8, 2, 7))
        pygame.draw.circle(surf, (200, 180, 160), (x, y - 9), 1)
        # Blonde woman (right of man, leans on him)
        pygame.draw.rect(surf, (160, 80, 100), (x + 2, y - 7, 2, 6))
        pygame.draw.circle(surf, (220, 200, 140), (x + 3, y - 8), 1)
        # Boy (front of man, on crutches)
        pygame.draw.rect(surf, (200, 180, 80), (x - 3, y - 4, 1, 4))
        pygame.draw.circle(surf, (200, 180, 160), (x - 3, y - 5), 1)
        pygame.draw.line(surf, (90, 60, 30), (x - 4, y - 4),
                         (x - 4, y), 1)
        # Girl (next to boy)
        pygame.draw.rect(surf, (200, 100, 130), (x - 5, y - 4, 1, 4))
        pygame.draw.circle(surf, (200, 180, 160), (x - 5, y - 5), 1)
        # All four faces have black-dot eyes that point AT the viewer.
        for ex, ey in [(x, y - 9), (x + 3, y - 8),
                       (x - 3, y - 5), (x - 5, y - 5)]:
            pygame.draw.circle(surf, (10, 10, 14), (ex, ey), 1)

    def _draw_missing_flyer(self, surf, x, y):
        # Pinned paper flyer -- beige sheet with a small portrait sketch
        # at the top, MISSING bar in red, and three text lines below.
        # Two corner tacks sell the "pinned to wood" read; the bottom-
        # right corner curls slightly so it doesn't look freshly
        # printed.
        # Paper body
        pygame.draw.rect(surf, (220, 200, 160), (x - 7, y - 12, 14, 24))
        pygame.draw.rect(surf, (60, 40, 25), (x - 7, y - 12, 14, 24), 1)
        # Corner curl (bottom-right)
        pygame.draw.polygon(surf, (180, 160, 130),
                            [(x + 7, y + 8), (x + 7, y + 12), (x + 3, y + 12)])
        pygame.draw.line(surf, (60, 40, 25), (x + 7, y + 8),
                         (x + 3, y + 12), 1)
        # MISSING bar (red) at top
        pygame.draw.rect(surf, (160, 30, 30), (x - 5, y - 11, 10, 2))
        # Portrait circle
        pygame.draw.circle(surf, (40, 28, 22), (x, y - 6), 3, 1)
        # Text lines
        for i in range(3):
            pygame.draw.line(surf, (60, 40, 25),
                             (x - 5, y + i * 3),
                             (x + 5, y + i * 3), 1)
        # Tacks
        pygame.draw.circle(surf, (200, 60, 60), (x - 5, y - 11), 1)
        pygame.draw.circle(surf, (200, 60, 60), (x + 5, y - 11), 1)

    def _draw_banner(self, surf, x, y):
        col = self.kwargs.get("color", (140, 60, 70))
        for i in range(8):
            wy = math.sin(self.t * 3 + i * 0.5 + self.seed) * 1.5
            pygame.draw.line(surf, col, (x - 6, y + i * 2 + wy), (x + 6, y + i * 2 + wy), 2)

    def _draw_oil_portrait(self, surf, x, y):
        # A framed oil portrait gone varnish-dark: a pale collar and two
        # folded hands still float in the murk, but the face has sunk
        # where the varnish pooled. Whoever it was, the room forgot.
        pygame.draw.rect(surf, (74, 56, 30), (x - 9, y - 13, 19, 25))   # frame
        pygame.draw.rect(surf, (108, 86, 48), (x - 9, y - 13, 19, 25), 1)
        pygame.draw.rect(surf, (46, 36, 20), (x - 7, y - 11, 15, 21), 1)  # inner lip
        pygame.draw.rect(surf, (26, 24, 22), (x - 6, y - 10, 13, 19))   # the dark field
        rng = random.Random(self.seed if self.seed is not None else 3)
        # the sitter, almost gone: shoulders, collar, folded hands
        pygame.draw.ellipse(surf, (38, 34, 30), (x - 5, y - 4, 11, 12))  # shoulders
        pygame.draw.rect(surf, (118, 112, 98), (x - 2, y - 2, 5, 2))    # pale collar
        pygame.draw.ellipse(surf, (96, 88, 74), (x - 2, y + 5, 5, 3))   # folded hands
        # where the face should be, only pooled varnish
        pygame.draw.ellipse(surf, (20, 18, 17), (x - 3, y - 9, 7, 8))
        if rng.random() < 0.5:
            pygame.draw.line(surf, (60, 52, 40), (x - 5, y - 10 + rng.randint(0, 14)),
                             (x + 6, y - 9 + rng.randint(0, 14)), 1)    # varnish crack

    def _draw_wrong_photo(self, surf, x, y):
        """A framed photograph whose subjects degrade between visits.
        First visit: a family of three. Subsequent visits: faces
        progressively erased -- eyes go first, then mouths, then the
        whole face. Driven by `stage` kwarg (0..3). When stage>=2,
        a single fresh red dot appears in the corner of the frame
        as if someone marked it."""
        stage = self.kwargs.get("stage", 0)
        # Frame
        pygame.draw.rect(surf, (140, 110, 70), (x - 10, y - 8, 20, 16))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 8, 20, 16), 1)
        # Photo paper
        pygame.draw.rect(surf, (200, 190, 170), (x - 8, y - 6, 16, 12))
        # Three figures
        skin = (220, 190, 160)
        clothes_a = (160, 80, 100)
        clothes_b = (80, 100, 140)
        clothes_c = (180, 160, 80)
        # Adult man (centre)
        pygame.draw.rect(surf, clothes_b, (x - 1, y - 2, 2, 6))
        pygame.draw.circle(surf, skin, (x, y - 3), 1)
        # Adult woman (right)
        pygame.draw.rect(surf, clothes_a, (x + 2, y - 2, 2, 6))
        pygame.draw.circle(surf, skin, (x + 3, y - 3), 1)
        # Child (left)
        pygame.draw.rect(surf, clothes_c, (x - 4, y, 2, 4))
        pygame.draw.circle(surf, skin, (x - 3, y - 1), 1)
        # Eye dots -- present at stage 0, gone by stage 1+.
        if stage < 1:
            pygame.draw.circle(surf, (10, 10, 14), (x, y - 3), 1)
            pygame.draw.circle(surf, (10, 10, 14), (x + 3, y - 3), 1)
            pygame.draw.circle(surf, (10, 10, 14), (x - 3, y - 1), 1)
        # Mouth lines -- gone by stage 2+.
        if stage < 2:
            pygame.draw.line(surf, (90, 60, 70),
                             (x - 1, y - 2), (x + 1, y - 2), 1)
        # Face-erase scratches -- appear at stage 2+, oblitering each
        # face entirely.
        if stage >= 2:
            for ex, ey in [(x, y - 3), (x + 3, y - 3), (x - 3, y - 1)]:
                pygame.draw.line(surf, (200, 190, 170),
                                 (ex - 1, ey), (ex + 1, ey), 1)
        # Red corner dot
        if stage >= 2:
            pygame.draw.circle(surf, (200, 40, 40),
                               (x + 8, y - 6), 1)

    def _draw_photo(self, surf, x, y):
        pygame.draw.rect(surf, (140, 110, 70), (x - 10, y - 8, 20, 16))
        pygame.draw.rect(surf, (60, 40, 25), (x - 10, y - 8, 20, 16), 1)
        pygame.draw.rect(surf, (180, 180, 200), (x - 8, y - 6, 16, 12))
        pygame.draw.circle(surf, (220, 190, 160), (x - 4, y - 2), 1)
        pygame.draw.circle(surf, (220, 190, 160), (x, y - 2), 1)
        pygame.draw.circle(surf, (220, 190, 160), (x + 4, y - 2), 1)

    def _draw_sampler(self, surf, x, y):
        # A framed cross-stitch sampler: rows of little stitched motifs
        # on old linen, a stitched house at the foot. The bottom rows are
        # unraveling; a red thread hangs loose below the frame.
        rng = random.Random(self.seed if self.seed is not None else 5)
        pygame.draw.rect(surf, (66, 50, 32), (x - 10, y - 11, 21, 21))  # frame
        pygame.draw.rect(surf, (42, 32, 20), (x - 10, y - 11, 21, 21), 1)
        pygame.draw.rect(surf, (186, 178, 156), (x - 8, y - 9, 17, 17))  # linen
        pygame.draw.rect(surf, (124, 60, 56), (x - 7, y - 8, 15, 15), 1)  # stitched border
        # rows of stitch motifs (an alphabet the eye can't quite read)
        for row, ry in enumerate((y - 6, y - 3)):
            for i in range(5):
                if rng.random() < 0.85:
                    c = (96, 84, 110) if (i + row) % 2 else (124, 60, 56)
                    pygame.draw.rect(surf, c, (x - 6 + i * 3, ry, 2, 2))
        # the little stitched house
        pygame.draw.rect(surf, (96, 84, 110), (x - 2, y + 2, 5, 4))
        pygame.draw.polygon(surf, (124, 60, 56), [(x - 3, y + 2), (x + 3, y + 2), (x, y - 1)])
        # the bottom row come undone
        pygame.draw.line(surf, (124, 60, 56), (x - 6, y + 4), (x - 4, y + 6), 1)
        pygame.draw.line(surf, (124, 60, 56), (x + 4, y + 7), (x + 7, y + 5), 1)
        # the loose red thread, hanging out of the frame
        pygame.draw.line(surf, (124, 60, 56), (x + 5, y + 10), (x + 4, y + 15), 1)
        pygame.draw.line(surf, (124, 60, 56), (x + 4, y + 15), (x + 6, y + 17), 1)

    def _draw_doll(self, surf, x, y):
        """A small bound effigy -- cloth body, twine waist, stick arms,
        two dark X-marks for eyes. The cult's watching-charm, set on the
        charred edges around the burn clearing. ~14px tall."""
        # Drop shadow.
        sh = pygame.Surface((12, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, 12, 5))
        surf.blit(sh, (x - 6, y + 5))
        cloth = (122, 96, 70)
        cloth_dk = (84, 64, 46)
        twine = (70, 48, 28)
        # Body wedge (skirt wider at the base).
        pygame.draw.polygon(surf, cloth_dk,
                            [(x - 4, y + 5), (x + 4, y + 5),
                             (x + 3, y - 4), (x - 3, y - 4)])
        pygame.draw.polygon(surf, cloth,
                            [(x - 3, y + 4), (x + 3, y + 4),
                             (x + 2, y - 3), (x - 2, y - 3)])
        # Stick arms + twine waist.
        pygame.draw.line(surf, twine, (x - 3, y - 1), (x - 6, y + 1), 1)
        pygame.draw.line(surf, twine, (x + 3, y - 1), (x + 6, y + 1), 1)
        pygame.draw.line(surf, twine, (x - 3, y + 1), (x + 3, y + 1), 1)
        # Head + two tiny X eyes.
        pygame.draw.circle(surf, cloth, (x, y - 6), 3)
        pygame.draw.circle(surf, cloth_dk, (x, y - 6), 3, 1)
        for ex in (x - 1, x + 2):
            pygame.draw.line(surf, (20, 16, 14), (ex - 1, y - 7), (ex, y - 6), 1)
            pygame.draw.line(surf, (20, 16, 14), (ex - 1, y - 6), (ex, y - 7), 1)

    def _draw_wrong_taxidermy(self, surf, x, y):
        # A mounted... thing -- a stoat or grouse, but the eyes are wrong:
        # too many, sickly-yellow, catching the light. Underground only.
        # `wall` rotates it to face into the room.
        lay = pygame.Surface((22, 20), pygame.SRCALPHA)
        cx, cy = 11, 10
        pygame.draw.rect(lay, (58, 42, 26), (cx - 10, cy - 9, 20, 18), border_radius=2)
        pygame.draw.rect(lay, (34, 24, 14), (cx - 10, cy - 9, 20, 18), 1)
        pygame.draw.ellipse(lay, (70, 56, 40), (cx - 7, cy - 6, 14, 12))
        pygame.draw.ellipse(lay, (48, 36, 24), (cx - 7, cy - 6, 14, 12), 1)
        rng = random.Random(self.seed)
        for _ in range(6):
            ex = cx - 5 + rng.randint(0, 10)
            ey = cy - 4 + rng.randint(0, 8)
            pygame.draw.circle(lay, (208, 196, 64), (ex, ey), 1)
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_buck_head(self, surf, x, y):
        # Mounted buck on a wood plaque. Drawn canonically facing DOWN
        # (mounted on a north wall, antlers toward the wall); `wall`
        # (N/E/S/W) rotates it to face into the room off any wall.
        lay = pygame.Surface((46, 48), pygame.SRCALPHA)
        cx, cy = 23, 27
        plaque = [(cx - 11, cy - 11), (cx + 11, cy - 11), (cx + 13, cy + 8),
                  (cx, cy + 13), (cx - 13, cy + 8)]
        pygame.draw.polygon(lay, (58, 42, 26), plaque)
        pygame.draw.polygon(lay, (34, 24, 14), plaque, 1)
        for s in (-1, 1):
            bx = cx + s * 5
            pygame.draw.line(lay, (118, 106, 82), (bx, cy - 7), (bx + s * 8, cy - 18), 2)
            pygame.draw.line(lay, (118, 106, 82), (bx + s * 3, cy - 11), (bx + s * 9, cy - 14), 1)
            pygame.draw.line(lay, (118, 106, 82), (bx + s * 5, cy - 14), (bx + s * 7, cy - 21), 1)
        pygame.draw.ellipse(lay, (72, 52, 36), (cx - 7, cy - 8, 14, 18))
        pygame.draw.ellipse(lay, (50, 36, 24), (cx - 7, cy - 8, 14, 18), 1)
        pygame.draw.ellipse(lay, (38, 27, 19), (cx - 4, cy + 4, 8, 6))
        pygame.draw.circle(lay, (18, 14, 10), (cx - 3, cy - 1), 2)
        pygame.draw.circle(lay, (18, 14, 10), (cx + 3, cy - 1), 2)
        pygame.draw.circle(lay, (130, 118, 96), (cx - 3, cy - 2), 1)
        ang = {"N": 0, "E": -90, "S": 180, "W": 90}.get(self.kwargs.get("wall", "N"), 0)
        if ang:
            lay = pygame.transform.rotate(lay, ang)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_mounted_fish(self, surf, x, y):
        # A trophy walleye on a varnished board (always horizontal on the
        # wall). `flip` points the head the other way.
        lay = pygame.Surface((34, 16), pygame.SRCALPHA)
        cx, cy = 16, 8
        pygame.draw.rect(lay, (66, 48, 30), (0, cy - 7, 32, 14), border_radius=3)
        pygame.draw.rect(lay, (36, 26, 15), (0, cy - 7, 32, 14), 1)
        pygame.draw.ellipse(lay, (96, 104, 86), (cx - 12, cy - 4, 22, 8))
        pygame.draw.ellipse(lay, (70, 78, 62), (cx - 12, cy - 4, 22, 8), 1)
        pygame.draw.polygon(lay, (96, 104, 86), [(cx + 9, cy), (cx + 15, cy - 4), (cx + 15, cy + 4)])
        pygame.draw.polygon(lay, (80, 88, 70), [(cx - 2, cy - 4), (cx + 2, cy - 8), (cx + 4, cy - 4)])
        pygame.draw.line(lay, (60, 68, 54), (cx - 10, cy), (cx + 8, cy), 1)
        pygame.draw.circle(lay, (216, 206, 176), (cx - 9, cy - 1), 2)
        pygame.draw.circle(lay, (10, 10, 12), (cx - 9, cy - 1), 1)
        if self.kwargs.get("flip", False):
            lay = pygame.transform.flip(lay, True, False)
        surf.blit(lay, (x - lay.get_width() // 2, y - lay.get_height() // 2))

    def _draw_meat(self, surf, x, y):
        # A haunch of meat hung on a hook: a rounded red slab with fat
        # marbling and a pale bone nub at the base, swaying slightly,
        # the occasional drip. Reads clearly as hung meat / a larder.
        sway = math.sin(self.t * 0.8 + self.seed) * 1.5
        cx = int(x + sway)
        # Hook + the line it hangs from.
        pygame.draw.line(surf, (150, 150, 162), (x, y - 18), (x, y - 9), 2)
        pygame.draw.line(surf, (150, 150, 162), (x, y - 9), (cx - 3, y - 7), 2)
        # Haunch body on its own layer so the shape reads cleanly.
        body = pygame.Surface((24, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (118, 26, 34), (3, 0, 18, 22))      # meat
        pygame.draw.ellipse(body, (150, 44, 52), (6, 3, 11, 12))      # lit side
        pygame.draw.ellipse(body, (86, 16, 24), (3, 0, 18, 22), 1)    # rim
        pygame.draw.line(body, (196, 152, 150), (7, 9), (16, 13), 1)  # fat
        pygame.draw.line(body, (196, 152, 150), (6, 14), (14, 17), 1)
        pygame.draw.rect(body, (222, 216, 198), (10, 19, 4, 6))       # bone nub
        pygame.draw.circle(body, (236, 232, 216), (12, 25), 3)
        surf.blit(body, (cx - 12, y - 7))
        drip = (self.t * 0.3 + self.seed * 0.07) % 3.0
        if drip < 1.0:
            pygame.draw.rect(surf, (88, 16, 24),
                             (cx, y + 19 + int(drip * 8), 1, 2))

    def _draw_effects_pile(self, surf, x, y):
        """A sorted heap of the vanished's belongings -- a folded coat, a shoe, a
        hat, spectacles, a child's toy -- catalogued in the Sorting Hall (the
        lives the claimed shed). Muted, dead colours. A floor decal; varies by
        seed."""
        seed = self.seed
        def dk(c, f=0.55):
            return (int(c[0] * f), int(c[1] * f), int(c[2] * f))
        pygame.draw.ellipse(surf, (26, 22, 24), (x - 13, y - 1, 26, 11))   # heap shadow
        cols = [(86, 72, 90), (74, 84, 72), (96, 80, 58), (70, 70, 84)]
        c = cols[seed % 4]
        pygame.draw.rect(surf, c, (x - 10, y - 3, 13, 8))                  # folded cloth
        pygame.draw.rect(surf, dk(c), (x - 10, y - 3, 13, 8), 1)
        pygame.draw.line(surf, dk(c, 0.75), (x - 10, y + 1), (x + 3, y + 1), 1)
        pygame.draw.ellipse(surf, (60, 44, 32), (x + 2, y + 2, 9, 5))      # a shoe
        pygame.draw.ellipse(surf, (40, 28, 20), (x + 2, y + 2, 9, 5), 1)
        pygame.draw.ellipse(surf, (52, 48, 54), (x - 5, y - 6, 11, 5))     # a hat brim
        pygame.draw.ellipse(surf, (66, 62, 68), (x - 1, y - 8, 5, 4))      # hat crown
        if seed % 2:                                                       # spectacles
            pygame.draw.circle(surf, (150, 150, 160), (x + 6, y - 2), 1)
            pygame.draw.circle(surf, (150, 150, 160), (x + 9, y - 2), 1)
        pygame.draw.circle(surf, (182, 170, 150), (x - 7, y + 4), 2)       # a child's toy
        pygame.draw.circle(surf, (120, 108, 92), (x - 7, y + 4), 2, 1)

    def _draw_papers(self, surf, x, y):
        """An open notebook + a loose sheet fanned under it: pale pages with
        a few lines of ink and a curled corner. A seated tabletop prop -- the
        PI's case notes on the writing desk, the visible object the [E]
        read-prompt hovers over (scenes/house.py build_bedroom)."""
        seed = int(getattr(self, "seed", 0) or 0)
        PAGE = (222, 216, 198); PAGE_HI = (238, 233, 219)
        EDGE = (120, 112, 92); INK = (60, 54, 48)
        # a loose sheet fanned out under the notebook (nudged by the seed)
        ox = -6 + (seed % 3)
        pygame.draw.polygon(surf, (206, 200, 182),
                            [(x - 9 + ox, y - 2), (x + 7 + ox, y - 4),
                             (x + 9 + ox, y + 8), (x - 7 + ox, y + 10)])
        # the open notebook: two facing pages over a dark cover edge
        pygame.draw.rect(surf, EDGE, (x - 10, y - 7, 20, 14))
        pygame.draw.rect(surf, PAGE, (x - 9, y - 6, 9, 12))       # left page
        pygame.draw.rect(surf, PAGE_HI, (x + 1, y - 6, 8, 12))    # right page
        pygame.draw.line(surf, EDGE, (x, y - 6), (x, y + 6), 1)   # spine
        # a few lines of ink on both pages
        for i in range(4):
            ly = y - 4 + i * 3
            pygame.draw.line(surf, INK, (x - 8, ly),
                             (x - 2 - (seed + i) % 2, ly), 1)
            pygame.draw.line(surf, INK, (x + 2, ly),
                             (x + 7 - (seed + i) % 3, ly), 1)
        # curled corner catches the candlelight
        pygame.draw.polygon(surf, PAGE_HI,
                            [(x + 7, y + 6), (x + 9, y + 4), (x + 9, y + 6)])

    def _draw_ledger(self, surf, x, y):
        """The guest register open on the front desk: a leather-bound ledger,
        two cream pages with ruled lines + signature scrawls, a faint gold gleam
        on the names (the Ledger, a case note -- the guests who never checked out)."""
        cover = (74, 52, 36); cover_lo = (52, 36, 24)
        page = (224, 214, 188); spine = (150, 138, 112)
        line = (158, 148, 126); ink = (44, 36, 30)
        # leather cover, a touch wider than the pages
        pygame.draw.polygon(surf, cover,
                            [(x - 11, y - 7), (x + 11, y - 7),
                             (x + 12, y + 7), (x - 12, y + 7)])
        pygame.draw.polygon(surf, cover_lo,
                            [(x - 11, y - 7), (x + 11, y - 7),
                             (x + 12, y + 7), (x - 12, y + 7)], 1)
        # the two open pages + a shadowed spine down the middle
        pygame.draw.polygon(surf, page,
                            [(x - 10, y - 6), (x - 1, y - 6),
                             (x - 1, y + 6), (x - 10, y + 6)])
        pygame.draw.polygon(surf, page,
                            [(x + 1, y - 6), (x + 10, y - 6),
                             (x + 11, y + 6), (x + 1, y + 6)])
        pygame.draw.line(surf, spine, (x, y - 6), (x, y + 6), 1)
        # ruled lines, with a few inked signatures over them
        rng = random.Random(self.seed)
        for i in range(4):
            ly = y - 4 + i * 3
            pygame.draw.line(surf, line, (x - 9, ly), (x - 2, ly), 1)
            pygame.draw.line(surf, line, (x + 2, ly), (x + 9, ly), 1)
            for x0 in (x - 9, x + 2):
                sx = x0 + rng.randint(0, 2)
                pygame.draw.line(surf, ink, (sx, ly - 1),
                                 (sx + rng.randint(3, 6), ly - 1), 1)
        # faint gold gleam on the page -- the Sign in the names
        _light_pool(surf, x, y - 1, 13, (220, 190, 90), 24)

    def _draw_calendar(self, surf, x, y):
        """Stripped-down wall calendar. Just the month abbreviation
        and the day number on a small paper card -- no grid, no X
        marks, no week-day headers. Reads kwargs:
          today_d -- 1-based day-of-month shown on the card
          month   -- numeric month (10, 11, 12, or 1)
        `month_days` is still accepted for compatibility but ignored.

        CANON (NARRATIVE §1 setting note 3): every calendar in town
        stopped at the mid-January seal, so the default card reads
        JAN 15 -- the last day anyone marked, three months before the
        PI's mid-April arrival. (The old day-cycle that advanced this
        on sleep is removed; the stopped date IS the prop now.)
        Cached SysFont surface so we don't re-rasterise every frame."""
        today_d = self.kwargs.get("today_d", 15)
        month = self.kwargs.get("month", 1)
        # Paper. Smaller now that the grid is gone -- a tear-off
        # day-card pinned to the wall.
        paper_w, paper_h = 26, 26
        px = x - paper_w // 2
        py = y - paper_h // 2
        pygame.draw.rect(surf, (224, 218, 200), (px, py, paper_w, paper_h))
        pygame.draw.rect(surf, (50, 40, 30), (px, py, paper_w, paper_h), 1)
        # Header band carries the month abbreviation.
        pygame.draw.rect(surf, (40, 30, 24), (px, py, paper_w, 8))
        name = {10: "OCT", 11: "NOV", 12: "DEC", 1: "JAN"}.get(month, "JAN")
        # The day number, big and centred on the lower portion.
        day_str = str(today_d)
        try:
            cache = self.kwargs.get("_label_cache")
            cache_key = self.kwargs.get("_label_cache_key")
            target_key = (name, day_str)
            if cache is None or cache_key != target_key:
                month_font = pygame.font.SysFont(None, 10)
                day_font = pygame.font.SysFont(None, 18)
                month_surf = month_font.render(
                    name, False, (224, 218, 200))
                day_surf = day_font.render(
                    day_str, False, (40, 30, 24))
                cache = (month_surf, day_surf)
                self.kwargs["_label_cache"] = cache
                self.kwargs["_label_cache_key"] = target_key
            month_surf, day_surf = cache
            surf.blit(month_surf,
                      (px + (paper_w - month_surf.get_width()) // 2,
                       py + 1))
            surf.blit(day_surf,
                      (px + (paper_w - day_surf.get_width()) // 2,
                       py + 9))
        except Exception:
            pass

    def _draw_mud_footprint(self, surf, x, y):
        # A single BOOT print -- one connected sole (rounded toe/ball, a
        # narrow arch, a heel) with a faint tread, NOT separate toe dabs
        # (which read as an animal paw). `dir` (0..3) rotates it so a
        # trail suggests direction; `alpha` fades it.
        d = self.kwargs.get("dir", 0)
        a = max(20, min(220, int(self.kwargs.get("alpha", 180))))
        layer = pygame.Surface((16, 22), pygame.SRCALPHA)
        col = (32, 22, 14, a)
        tread = (22, 15, 9, a)
        # Ball of the foot (front), wide and rounded.
        pygame.draw.ellipse(layer, col, (3, 1, 10, 12))
        # Arch / instep -- a narrow waist linking the ball to the heel.
        pygame.draw.rect(layer, col, (5, 9, 6, 8))
        # Heel -- rounded, a touch narrower than the ball.
        pygame.draw.ellipse(layer, col, (4, 14, 8, 8))
        # Tread bars: two across the ball, one across the heel.
        pygame.draw.line(layer, tread, (4, 5), (11, 5), 1)
        pygame.draw.line(layer, tread, (4, 8), (11, 8), 1)
        pygame.draw.line(layer, tread, (5, 18), (10, 18), 1)
        # rotate per direction (0=up, 1=right, 2=down, 3=left)
        if d:
            layer = pygame.transform.rotate(layer, -90 * d)
        surf.blit(layer, (x - layer.get_width() // 2,
                          y - layer.get_height() // 2))

    def _draw_tin_cans(self, surf, x, y):
        """Strewn tins on the ground -- the cans noise trap. Three
        dull cans, one tipped with its lid sprung, seeded scatter."""
        rng = random.Random(self.seed)
        dull = (118, 116, 108)
        dark = (66, 64, 58)
        rust = (110, 70, 44)
        for i in range(3):
            cx = x + rng.randint(-9, 9)
            cy = y + rng.randint(-5, 5)
            if i == 0:              # tipped: seen side-on
                pygame.draw.rect(surf, dull, (cx - 5, cy - 2, 10, 5))
                pygame.draw.rect(surf, dark, (cx - 5, cy - 2, 10, 5), 1)
                pygame.draw.ellipse(surf, dark, (cx + 3, cy - 3, 4, 7))
            else:                   # standing: a small ring from above
                pygame.draw.circle(surf, dull, (cx, cy), 3)
                pygame.draw.circle(surf, dark, (cx, cy), 3, 1)
                pygame.draw.circle(surf, dark, (cx, cy), 1)
            if rng.random() < 0.7:
                surf.set_at((cx + rng.randint(-2, 2),
                             cy + rng.randint(-2, 2)), rust)
        # the sprung lid, glinting a little off to one side
        pygame.draw.ellipse(surf, (150, 148, 140), (x + 6, y + 4, 5, 3))

    def _draw_glass_litter(self, surf, x, y):
        """Broken glass across the ground -- the glass noise trap.
        A seeded scatter of pale glints and two larger shards."""
        rng = random.Random(self.seed * 3 + 1)
        glint = (188, 198, 204)
        dim = (120, 130, 138)
        for _ in range(9):
            gx = x + rng.randint(-11, 11)
            gy = y + rng.randint(-7, 7)
            col = glint if rng.random() < 0.4 else dim
            if rng.random() < 0.5:
                surf.set_at((gx, gy), col)
            else:
                pygame.draw.line(surf, col, (gx, gy),
                                 (gx + rng.randint(1, 2), gy), 1)
        for sx, sy, flip in ((x - 4, y - 1, 1), (x + 5, y + 3, -1)):
            pygame.draw.polygon(surf, dim,
                                [(sx, sy), (sx + 4 * flip, sy + 1),
                                 (sx + 1 * flip, sy - 3)])
            pygame.draw.line(surf, glint, (sx, sy),
                             (sx + 1 * flip, sy - 3), 1)

    def _draw_item_drop(self, surf, x, y):
        # generic loot bob: small box that bobs gently with subtle glow.
        # A faint ground-contact shadow sits under the bobbing icon so the
        # pickup reads as ON the floor, not floating;
        # the icon bobs, the shadow stays put.
        _ground_shadow(surf, x, y + 5, 7, 3, 90)
        bob = int(math.sin(self.t * 2) * 1)
        col = self.kwargs.get("color", C_GOLD)
        pygame.draw.rect(surf, col, (x - 4, y - 4 + bob, 8, 8))
        pygame.draw.rect(surf, C_BLACK, (x - 4, y - 4 + bob, 8, 8), 1)
        if int(self.t * 4) % 4 == 0:
            pygame.draw.line(surf, (255, 255, 200), (x - 6, y - 6 + bob), (x - 4, y - 4 + bob), 1)

    def _draw_etched_char(self, surf, ch, x, y, col, rng):
        """Skeletal stroke renderer for a single letter inside an
        apology-wall patch. Tiny 4x6 characters drawn with short
        line strokes -- only the letters used by I'M SORRY are
        defined."""
        if ch == "I":
            pygame.draw.line(surf, col, (x + 1, y), (x + 1, y + 5), 1)
        elif ch == "M":
            pygame.draw.line(surf, col, (x, y + 5), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 2, y + 2), (x + 4, y), 1)
            pygame.draw.line(surf, col, (x + 4, y), (x + 4, y + 5), 1)
        elif ch == "S":
            pygame.draw.line(surf, col, (x + 3, y), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x, y + 2), 1)
            pygame.draw.line(surf, col, (x, y + 2), (x + 3, y + 3), 1)
            pygame.draw.line(surf, col, (x + 3, y + 3), (x + 3, y + 5), 1)
            pygame.draw.line(surf, col, (x + 3, y + 5), (x, y + 5), 1)
        elif ch == "O":
            pygame.draw.rect(surf, col, (x, y, 4, 6), 1)
        elif ch == "R":
            pygame.draw.line(surf, col, (x, y + 5), (x, y), 1)
            pygame.draw.line(surf, col, (x, y), (x + 3, y), 1)
            pygame.draw.line(surf, col, (x + 3, y), (x + 3, y + 2), 1)
            pygame.draw.line(surf, col, (x + 3, y + 2), (x, y + 2), 1)
            pygame.draw.line(surf, col, (x, y + 2), (x + 3, y + 5), 1)
        elif ch == "Y":
            pygame.draw.line(surf, col, (x, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 4, y), (x + 2, y + 2), 1)
            pygame.draw.line(surf, col, (x + 2, y + 2), (x + 2, y + 5), 1)
