"""Cutscene rendering for THRESHOLD: the journal door-dream flashback, the
endings, and the opening night-drive. Extracted from systems.game as a mixin
so these ~700 lines of pure-draw code live apart from the threat/loop
orchestrator. The methods are byte-for-byte the originals -- they still read
and write `self.*` (screen, fonts, the _flashback_*/_opening_*/_ending_*
state, the _ENDING_SCRIPTS table) on the Game instance they're mixed into.

This module OWNS the flashback/opening/rite tuning constants (the draw bodies
reference them by bare name, so they must resolve in this module's globals);
systems.game re-imports them so existing `systems.game.FLASHBACK_DUR` lookups
keep working."""
import math
import random

import pygame

from constants import SCREEN_W, SCREEN_H, TILE
from rendering.sprites import draw_carcosa, draw_mask_yank, draw_seal_tableau


# ---- Cutscene tuning constants (owned here; re-exported by systems.game) ----

FLASHBACK_DUR = 7.0            # seconds the FULL door-dream holds (the rite)
FLASHBACK_FLASH_DUR = 0.55     # the journal's intrusive MEMORY FLASH: two
                               # hard flickers of the door, in and gone
FLASHBACK_MASK_FRAMES = 3      # frames each individual mask holds on screen
# Mask SWARM: dark-wood faces flash all over the inside of the doorframe
# (some clipped by it), starting slow ~START s in and accelerating to a
# crowd that all stare back, then fading with the dream. RATE_* = masks/sec.
FLASHBACK_SWARM_START = 2.0
FLASHBACK_SWARM_PEAK = 5.5
FLASHBACK_RATE_MIN = 1.5
FLASHBACK_RATE_MAX = 420.0
FLASHBACK_FOCAL_Y = 0.80       # focal point: base of the doorway (slightly above)

# The opening drive -- a scripted, near-on-rails sequence (game state
# "opening"): the PI's car rolling into Brimley at night, hours from anyone
# in the northern dark, until the engine dies at the Arcadia Lodge. ESC skips
# it silently, with no on-screen tell.
OPENING_SCROLL_SPEED = 220.0  # px/sec the road scrolls -- the sense of speed
OPENING_ROLL_DUR = 2.6        # seconds rolling between stalls
OPENING_STALL_TIMEOUT = 4.5   # auto-restart if the player never taps (no softlock)
OPENING_DEAD_HOLD = 3.0       # the final dead beat before the hand-off
OPENING_STALLS = 2            # normal stalls; the one after is the fatal one

# rite_broken ending: the mask-yank act (the culpable beat), then a HARD CUT
# to the Carcosa blast.
RITE_YANK_DUR = 3.0
RITE_BLAST_DUR = 7.0



class CutsceneMixin:
    """Pure-draw cutscene methods mixed into Game. No state of its own."""


    def _draw_flashback(self):
        """Render the journal door-dream (NARRATIVE 1b): an OPEN doorway of
        dried, sun-bleached wood suspended in black. Light pours from
        INSIDE it -- a warm glow the frame's own jamb cuts off at the
        edges, so it reads as a door standing open onto somewhere too
        bright. Things move in that light: faint eyes that surface and blink,
        and -- accelerating from one face to a staring swarm (_spawn_flashback
        _masks) -- His dark-wood masks, all gazing back at you. All of it is
        CLIPPED to the opening; nothing ever crosses the threshold out into
        the dark. Wordless but for one opening line. The wind-and-falling
        audio bed (flashback_air) carries the fall."""
        if self._flashback_phase is None:
            return
        dur = getattr(self, "_flashback_dur", FLASHBACK_DUR)
        t = self._flashback_t / max(0.01, dur)   # 0..1 over the hold
        if getattr(self, "_flashback_mode", "rite") == "flash":
            # The journal's INTRUSIVE MEMORY: two hard flickers of the
            # door, forced in over half a second and gone. No swarm, no
            # audio bed; the full dream waits at the grove rite.
            if not (t < 0.28 or 0.48 < t < 0.86):
                return
            fade = 1.0
        # Whole-still fade: in over first 12%, out over last 18%.
        elif t < 0.12:
            fade = t / 0.12
        elif t > 0.82:
            fade = max(0.0, (1.0 - t) / 0.18)
        else:
            fade = 1.0
        fade = max(0.0, min(1.0, fade))

        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))

        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        now = self._flashback_t
        # The doorframe -- tall, the uprights a touch too slight to carry the
        # lintel (the wrongness, 1b). Fixed size: it never nears.
        dh = int(SCREEN_H * 0.52)
        dw = int(dh * 0.48)
        post = max(5, dw // 8)                  # the dried, too-slight jamb
        breathe = 1.0 + 0.009 * math.sin(now * 1.1)
        dh = int(dh * breathe)
        left = cx - dw // 2
        top = cy - dh // 2
        bot = top + dh
        # The doorway PULSES -- a slow heartbeat the glow rides on, so the
        # light visibly swells and ebbs (the thing inside, breathing).
        pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(now * 1.7))   # ~0.0..1.0
        ox, oy = left + post, top + post        # inside-jamb top-left
        ow, oh = dw - 2 * post, dh - post       # opening size (no sill)

        # Everything inside the doorway is drawn on one opening-sized surface
        # and blitted into the opening only -- so the glow is CONTAINED by the
        # frame and never leaks out past the wood into the black. The frame is
        # the black rectangle around it; the dream happens through the hole.
        if ow > 6 and oh > 6:
            inner = pygame.Surface((ow, oh), pygame.SRCALPHA)
            # Focal point: the BASE of the doorway (slightly above it), not
            # the geometric centre -- the perspective converges there, as if
            # looking down into the threshold.
            icx, icy = ow / 2, oh * FLASHBACK_FOCAL_Y

            # ---- Radiating, pulsing yellow glow ----
            # Radial yellow glow centred in the opening, breathing on the
            # pulse, falling to dark at the edges where the jamb cuts it off.
            steps = 38
            maxr = max(ow, oh) * 0.62
            for s in range(steps):
                f = s / (steps - 1)                 # 0 outer -> 1 inner
                rr = maxr * (1.0 - f)
                a = int((6 + 168 * f * f) * (0.40 + 0.60 * pulse) * fade)
                col = (246, 200 + int(38 * f), 70 + int(46 * f), min(255, a))
                rect = pygame.Rect(0, 0, int(rr * 1.5), int(rr * 1.62))
                rect.center = (int(icx), int(icy))
                pygame.draw.ellipse(inner, col, rect)

            # ---- Eyes peeking from the light ----
            # A few small, faint eye-pairs that surface, hold, blink under --
            # staggered so they don't pulse together. They peek; they never
            # resolve into faces.
            eyes = [(0.36, 0.40, 0.0), (0.62, 0.54, 1.9), (0.50, 0.30, 3.7)]
            for ex, ey, off in eyes:
                cyc = ((now + off) % 4.4) / 4.4
                pres = max(0.0, min(1.0, math.sin(math.pi * cyc) ** 2.0))
                if pres < 0.04:
                    continue
                openness = max(0.12, 0.5 + 0.5 * math.sin(now * 2.6 + off * 3))
                crackle = 0.62 + 0.38 * math.sin(now * 15 + off * 7)
                a = int(150 * pres * crackle * fade)
                if a <= 0:
                    continue
                exx = ex * ow + math.sin(now * 0.5 + off) * ow * 0.02
                eyy = ey * oh
                ew = max(2, int(0.045 * ow))
                eh = max(1, int(ew * 0.62 * openness))
                gap = ew * 1.5
                for sgn in (-1, 1):
                    er = pygame.Rect(0, 0, ew, eh)
                    er.center = (int(exx + sgn * gap), int(eyy))
                    pygame.draw.ellipse(inner, (230, 222, 190, a), er)
                    if eh >= 4:                     # a dark pupil when open
                        pygame.draw.ellipse(inner, (26, 18, 12, a),
                                            (er.centerx - 1, er.top + 1,
                                             2, max(1, eh - 2)))

            # ---- The mask swarm ----
            # Spawned (accelerating) in _tick_flashback. Each face lives a
            # few frames: blit its cached dark-wood mask (scaled to its size,
            # at its spot -- some overrun so the jamb CLIPS them) and age it.
            # Faces are OPAQUE (dark wood over the bright pulsing glow); their
            # gold gaze aims back at the player.
            pool = self._flashback_pool
            if pool:
                survivors = []
                for m in self._flashback_masks:
                    xf, yf, scale, gi, sd, life = m
                    surf = pool.get((gi, sd))
                    if surf is not None:
                        th = max(2, int(oh * scale))
                        tw = max(2, int(surf.get_width() * th
                                        / surf.get_height()))
                        scd = pygame.transform.smoothscale(surf, (tw, th))
                        inner.blit(scd, scd.get_rect(
                            center=(int(xf * ow), int(yf * oh))))
                    m[5] = life - 1
                    if m[5] > 0:
                        survivors.append(m)
                self._flashback_masks = survivors

            veil.blit(inner, (ox, oy))

        # ---- The dried wood frame, drawn ON TOP (occludes the glow/shapes
        # at the threshold -- that IS the 'cut off by the frame') ----
        def fc(c):
            return (int(c[0] * fade), int(c[1] * fade), int(c[2] * fade))
        base = (104, 74, 46)        # dried oak
        grain = (78, 52, 30)        # darker streak
        bleach = (138, 110, 74)     # sun-bleached highlight
        split = (44, 28, 16)        # a dry crack
        rng2 = random.Random(7)
        # two uprights + lintel (no sill -- it stands on level ground)
        for rx, rw, rh, ry in ((left, post, dh, top),
                               (left + dw - post, post, dh, top)):
            pygame.draw.rect(veil, fc(base), (rx, ry, rw, rh))
            # vertical grain streaks
            for gi in range(3):
                gx = rx + int((gi + 0.5) / 3 * rw) + rng2.randint(-1, 1)
                col = fc(grain if gi % 2 == 0 else bleach)
                pygame.draw.line(veil, col, (gx, ry + 2), (gx, ry + rh - 2), 1)
            # a couple of dry cracks
            for _ in range(2):
                cxx = rx + rng2.randint(1, max(1, rw - 1))
                y0 = ry + rng2.randint(4, max(5, rh // 2))
                y1 = min(ry + rh - 2, y0 + rng2.randint(rh // 5, rh // 2))
                pygame.draw.line(veil, fc(split), (cxx, y0),
                                 (cxx + rng2.randint(-1, 1), y1), 1)
        # lintel across the top
        pygame.draw.rect(veil, fc(base), (left, top, dw, post))
        for gi in range(int(dw / 14)):
            gx = left + gi * 14 + 6
            pygame.draw.line(veil, fc(grain), (gx, top + 2),
                             (gx, top + post - 2), 1)
        # warm lit rim where the inside light catches the jamb edges
        rim = (int(250 * pulse * fade), int(206 * pulse * fade),
               int(120 * pulse * fade))
        pygame.draw.line(veil, rim, (ox, oy), (ox, bot - 1), 1)
        pygame.draw.line(veil, rim, (ox + ow - 1, oy),
                         (ox + ow - 1, bot - 1), 1)
        pygame.draw.line(veil, rim, (ox, oy), (ox + ow - 1, oy), 1)

        # Opening narrator line -- names the dream, then fades and leaves the
        # image to carry it. Lives in the first ~2.2s only.
        intro = max(0.0, min(1.0, 1.0 - (now - 1.4) / 0.8))
        intro *= fade
        if intro > 0.01:
            txt = self.fonts["lg"].render("You dream of a doorway.", True,
                                          (210, 206, 214))
            txt.set_alpha(int(255 * intro))
            veil.blit(txt, (cx - txt.get_width() // 2, int(SCREEN_H * 0.15)))

        self.screen.blit(veil, (0, 0))


    def _draw_ending(self):
        """Render the active ending's current still. Same overlay
        treatment as the flashback -- except rite_broken, which is the
        wholly-visual Carcosa tableau (no text)."""
        if not self._ending_active:
            return
        if self._ending_active == "rite_broken":
            yt = self._ending_phase_t
            if yt < RITE_YANK_DUR:                # the culpable act...
                draw_mask_yank(self.screen, yt)
            else:                                 # ...HARD CUT to the blast
                draw_carcosa(self.screen, yt - RITE_YANK_DUR, "spread")
            return
        script = self._ENDING_SCRIPTS.get(self._ending_active, [])
        if self._ending_phase >= len(script):
            return
        line, dur = script[self._ending_phase]
        t = self._ending_phase_t / max(0.01, dur)
        if t < 0.15:
            alpha = int((t / 0.15) * 255)
        elif t > 0.85:
            alpha = int(((1.0 - t) / 0.15) * 255)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        if self._ending_active == "seal_threshold" and line == "":
            # The wordless close: the wide shot -- Brimley's acres
            # suspended in the void, the towering figure almost visible
            # behind them. No text by design (the approved lines all
            # played on black before this).
            draw_seal_tableau(self.screen, self._ending_phase_t)
            return
        rows = self._wrap_ending_line(line, int(SCREEN_W * 0.90))
        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))
        self.screen.blit(veil, (0, 0))
        surfs = [self.fonts["lg"].render(r, True, (220, 218, 226))
                 for r in rows]
        lh = surfs[0].get_height() if surfs else 0
        y0 = SCREEN_H // 2 - (lh * len(surfs)) // 2
        for i, s in enumerate(surfs):
            s.set_alpha(alpha)
            self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                                 y0 + i * lh))

    def _draw_seal_warp_overlay(self):
        """The SEAL live warp's screen dressing. The motion itself is the
        scene's (scenes/depths.py flies the real decorations through the
        frame); here the doorframe burns gold as it drinks, and each flight
        smears a streak into it. Drawn over the graded world, under the
        HUD (called from draw_world when game._seal_warp is active)."""
        sw = getattr(self, "_seal_warp", None)
        if sw is None:
            return
        t = sw["t"]
        dx, dy = sw["door"]
        sx, sy = self.camera.project(dx, dy, 0.0)
        lay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        # The frame's burn: swells in over the first beat, gutters like
        # the dream door's pulse.
        pulse = 0.55 + 0.45 * math.sin(t * 6.0)
        grow = min(1.0, t / 1.2)
        for rr in range(int(26 + 30 * grow), 2, -3):
            a = int((6 + 60 * (1 - rr / 60.0)) * grow * (0.6 + 0.4 * pulse))
            pygame.draw.circle(lay, (246, 206, 96, max(0, min(160, a))),
                               (int(sx), int(sy)), rr)
        # Streaks: every flying thing smears a gold line into the door,
        # brightening as the suck takes it.
        for f in sw["flights"]:
            p = max(0.0, min(1.0, (t - f["t0"]) / f["dur"]))
            fx, fy = self.camera.project(f["d"].x, f["d"].y, 0.0)
            a = int(40 + 130 * p)
            pygame.draw.line(lay, (235, 196, 110, a), (int(fx), int(fy)),
                             (int(sx), int(sy)), 1 + int(2 * p))
        self.screen.blit(lay, (0, 0))

    def _wrap_ending_line(self, line, max_w):
        """Greedy word-wrap for the ending stills; some authored lines run
        wider than the screen."""
        rows, cur = [], ""
        for wd in line.split():
            trial = (cur + " " + wd).strip()
            if cur and self.fonts["lg"].size(trial)[0] > max_w:
                rows.append(cur)
                cur = wd
            else:
                cur = trial
        if cur:
            rows.append(cur)
        return rows


    def _draw_car(self, s, cx, cy, light=1.0, exhaust=0.0, scale=1.3):
        """Top-down car, facing up the road (forward). `light` dims the
        headlights with the engine; the taillights stay (battery). `exhaust`
        (0..1) puffs idle smoke from the tail when the car stalls/dies.
        `scale` sizes the whole car (1.0 = the original footprint)."""
        k = scale

        def R(x, y, w, h):                       # rect in car-local units
            return pygame.Rect(int(cx + x * k), int(cy + y * k),
                               max(1, int(w * k)), max(1, int(h * k)))

        def P(x, y):                             # point in car-local units
            return (int(cx + x * k), int(cy + y * k))
        rad = lambda v: max(2, int(v * k))       # noqa: E731
        # Exhaust drifts back (down-screen) from the tail pipes.
        if exhaust > 0.01:
            t = pygame.time.get_ticks() / 1000.0
            pw = int(48 * k)
            puff = pygame.Surface((pw, pw), pygame.SRCALPHA)
            for i in range(3):
                pp = (t * 1.3 + i * 0.45) % 1.0
                pr = int((4 + pp * 9) * k)
                pa = int(70 * (1 - pp) * exhaust)
                if pa > 0:
                    pygame.draw.circle(
                        puff, (90, 92, 96, pa),
                        (pw // 2 + int(math.sin(t * 2 + i) * 3),
                         int((4 + pp * 28) * k)), pr)
            s.blit(puff, (int(cx - 24 * k), int(cy + 18 * k)))
        # Drop shadow on the road.
        shw, shh = int(46 * k), int(64 * k)
        sh = pygame.Surface((shw, shh), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 110), (0, 0, shw, shh))
        s.blit(sh, (int(cx - 23 * k), int(cy - 24 * k)))
        # Body: dark hull with a faint top sheen (headlight spill back-scatter).
        body = R(-13, -22, 26, 44)
        pygame.draw.rect(s, (26, 24, 30), body, border_radius=rad(5))
        pygame.draw.rect(s, (44, 42, 50), R(-13, -22, 26, 14), border_radius=rad(5))
        pygame.draw.rect(s, (9, 8, 11), body, 1, border_radius=rad(5))
        # Hood + windshield (front), roof, rear window.
        pygame.draw.rect(s, (30, 28, 34), R(-11, -20, 22, 7), border_radius=rad(2))
        wsh = (int(70 * light + 26), int(78 * light + 28), int(92 * light + 30))
        pygame.draw.polygon(s, wsh, [P(-9, -13), P(9, -13), P(7, -6), P(-7, -6)])
        pygame.draw.rect(s, (40, 42, 50), R(-8, -5, 16, 12), border_radius=rad(2))
        pygame.draw.rect(s, (24, 26, 32), R(-7, 8, 14, 5), border_radius=rad(2))
        # Side mirrors.
        pygame.draw.rect(s, (24, 22, 28), R(-15, -9, 3, 3))
        pygame.draw.rect(s, (24, 22, 28), R(12, -9, 3, 3))
        # Headlights + a tight hot core.
        hl = (int(235 * light), int(228 * light), int(190 * light))
        for hx in (-9, 9):
            pygame.draw.circle(s, hl, P(hx, -21), max(2, int(2 * k)))
            pygame.draw.circle(s, (255, 250, 230), P(hx, -21), max(1, int(k)))
        # Taillights (battery — stay lit even when the engine's dead).
        pygame.draw.rect(s, (150, 34, 26), R(-11, 18, 5, 3))
        pygame.draw.rect(s, (150, 34, 26), R(6, 18, 5, 3))
        pygame.draw.rect(s, (210, 70, 60), R(-10, 19, 2, 1))
        pygame.draw.rect(s, (210, 70, 60), R(7, 19, 2, 1))


    def _draw_case_card(self, header, lines, stamp, cx, cy, t_local, hold,
                        seed):
        """One case-file index card that FLASHES in: a white pop + a slight
        scale overshoot that settles, then holds, then fades. `t_local` is
        seconds since this card appeared; `hold` is how long before it fades.
        Aged paper, typed mono text, a coloured index tab, an optional red
        stamp. `seed` jitters the rotation so a stack reads as tossed down."""
        if t_local < 0 or t_local >= hold:
            return
        rng = random.Random(seed)
        ang = rng.uniform(-3.5, 3.5)
        appear, fade = 0.16, 0.5
        if t_local < appear:
            p = t_local / appear
            scale = 1.14 - 0.14 * p
            alpha = p
            flash = 1.0 - p
        elif t_local < hold - fade:
            scale, alpha, flash = 1.0, 1.0, 0.0
        else:
            scale, alpha, flash = 1.0, max(0.0, (hold - t_local) / fade), 0.0
        mono = self.fonts.get("mono", self.fonts["sm"])
        sm = self.fonts["sm"]
        pad = 11
        line_h = mono.get_height() + 3
        widths = [mono.size(ln)[0] for ln in lines]
        if header:
            widths.append(sm.size(header)[0])
        tw = max(widths) if widths else 40
        head_h = (sm.get_height() + 7) if header else 4
        # A stamp gets its own reserved column on the right so it never
        # lands on top of the typed text.
        stamp_surf = None
        if stamp:
            stamp_surf = pygame.transform.rotozoom(
                sm.render(stamp, True, (158, 42, 34)), 11, 1.0)
            stamp_surf.fill((255, 255, 255, 165),
                            special_flags=pygame.BLEND_RGBA_MULT)
        extra_r = (stamp_surf.get_width() + 10) if stamp_surf else 0
        w = tw + pad * 2 + 8 + extra_r
        h = head_h + len(lines) * line_h + pad
        card = pygame.Surface((w + 4, h + 5), pygame.SRCALPHA)
        # Drop shadow, then aged paper, then a thin border.
        pygame.draw.rect(card, (0, 0, 0, 95), (4, 5, w, h), border_radius=2)
        paper = (208, 200, 178)
        pygame.draw.rect(card, paper, (0, 0, w, h), border_radius=2)
        pygame.draw.rect(card, (150, 142, 120), (0, 0, w, h), 1, border_radius=2)
        # Foxing / age blotches.
        for _ in range(5):
            bx, by = rng.randint(4, w - 6), rng.randint(4, h - 6)
            pygame.draw.circle(card, (180, 168, 138, 70), (bx, by),
                               rng.randint(2, 5))
        # Coloured index tab down the left edge.
        tab_c = (150, 60, 48) if stamp else (74, 90, 74)
        pygame.draw.rect(card, tab_c, (0, 7, 5, h - 16))
        tx, ty = pad, 5
        if header:
            card.blit(sm.render(header, True, (58, 48, 42)), (tx, ty))
            ty += sm.get_height() + 1
            pygame.draw.line(card, (150, 142, 120), (tx, ty), (w - 8, ty), 1)
            ty += 4
        for ln in lines:
            card.blit(mono.render(ln, True, (38, 34, 32)), (tx, ty))
            ty += line_h
        # Red rubber stamp, angled, in its reserved right column.
        if stamp_surf:
            card.blit(stamp_surf,
                      (w - stamp_surf.get_width() - 7,
                       (h - stamp_surf.get_height()) // 2))
        comp = pygame.transform.rotozoom(card, ang, scale)
        rect = comp.get_rect(center=(int(cx), int(cy)))
        # Card-shaped white flash, taken before we fade the card. (set_alpha
        # is ignored on per-pixel-alpha surfaces, so scale the alpha channel
        # with a BLEND_RGBA_MULT fill instead.)
        if flash > 0.02:
            fl = comp.copy()
            fl.fill((255, 250, 235), special_flags=pygame.BLEND_RGB_ADD)
            fl.fill((255, 255, 255, int(200 * flash)),
                    special_flags=pygame.BLEND_RGBA_MULT)
        a = max(0.0, min(1.0, alpha))
        if a < 0.999:
            comp.fill((255, 255, 255, int(255 * a)),
                      special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(comp, rect)
        if flash > 0.02:
            self.screen.blit(fl, rect)


    def _draw_road_sign(self, s, x, y, light):
        """A weathered roadside sign reading BRIMLEY, the population struck
        through -- lit by the headlights as it passes. The struck-out count
        is the first wrong note: a town quietly subtracting itself."""
        def L(c):
            return (int(c[0] * light), int(c[1] * light), int(c[2] * light))
        pygame.draw.rect(s, L((58, 48, 36)), (x - 2, y, 4, 44))          # post
        bw, bh = 86, 38
        bx, by = x - bw // 2, y - bh
        pygame.draw.rect(s, L((52, 56, 50)), (bx, by, bw, bh), border_radius=3)
        pygame.draw.rect(s, L((28, 32, 28)), (bx, by, bw, bh), 2, border_radius=3)
        txt = self.fonts["sm"].render("BRIMLEY", True, L((202, 208, 198)))
        s.blit(txt, (x - txt.get_width() // 2, by + 4))
        pop = self.fonts["tiny"].render("POP. 412", True, L((150, 156, 148)))
        s.blit(pop, (x - pop.get_width() // 2, by + 21))
        pygame.draw.line(s, L((132, 44, 38)), (x - 26, by + 25), (x + 26, by + 27), 2)


    def _draw_lodge_sign(self, s, x, ground_y, f):
        """The Arcadia Lodge's roadside sign -- a lit motel sign the car
        pulls up to as the engine dies. Same family as the BRIMLEY sign, but
        SELF-LIT (warm, backlit, a flickering VACANCY) so it stays glowing as
        the headlights gutter -- the lodge beckoning from the dark. The
        building itself stays off the road (the Arcadia sits back in the
        Clerk's cornfields); a sign reads as 'you've arrived' without faking
        an exterior that contradicts the yard scene. `f` fades it in."""
        f = max(0.0, min(1.0, f))
        if f <= 0.0:
            return

        def C(c):
            return (int(c[0] * f), int(c[1] * f), int(c[2] * f))
        tt = pygame.time.get_ticks() / 1000.0
        neon = 1.0 if (tt * 3.0) % 5.0 > 0.3 else 0.4      # dying-neon flicker
        bw, bh = 96, 42
        bx, by = x - bw // 2, ground_y - 132
        # Post.
        pygame.draw.rect(s, C((50, 44, 38)),
                         (x - 2, by + bh, 4, ground_y - (by + bh)))
        # Warm backlight halo behind the board (additive).
        halo = pygame.Surface((s.get_width(), s.get_height()), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            ff = i / 10
            rw, rh = int(bw * 0.85 * ff), int(bh * 1.4 * ff)
            pygame.draw.ellipse(halo, (int(64 * (1 - ff) * f),
                                       int(48 * (1 - ff) * f),
                                       int(20 * (1 - ff) * f)),
                                (x - rw, by + bh // 2 - rh // 2, 2 * rw, rh))
        s.blit(halo, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        # Board.
        pygame.draw.rect(s, C((34, 30, 28)), (bx, by, bw, bh))
        pygame.draw.rect(s, C((96, 78, 46)), (bx, by, bw, bh), 2)
        warm = C((236, 200, 128))
        a = self.fonts["sm"].render("ARCADIA", True, warm)
        b = self.fonts["sm"].render("LODGE", True, warm)
        s.blit(a, (x - a.get_width() // 2, by + 3))
        s.blit(b, (x - b.get_width() // 2, by + 21))
        # VACANCY panel (the neon that flickers).
        vy = by + bh + 5
        pygame.draw.rect(s, C((28, 24, 22)), (x - 34, vy, 68, 18))
        pygame.draw.rect(s, C((70, 54, 30)), (x - 34, vy, 68, 18), 1)
        vac = self.fonts["tiny"].render(
            "VACANCY", True,
            C((int(212 * neon), int(150 * neon), int(70 * neon))))
        s.blit(vac, (x - vac.get_width() // 2, vy + 4))


    def _draw_opening(self):
        """The night drive into Brimley: a dark northern road scrolling past,
        layered pine walls, drifting ground mist, reflector posts, and the
        car's headlights as the only light for miles. The whole scene is lit
        by those headlights and dims as the engine stalls, guttering to
        near-black when it dies. Case-file cards flash in over it."""
        s = self.screen
        W, H = s.get_size()
        scroll = self._opening_scroll
        spd = getattr(self, "_opening_speed", OPENING_SCROLL_SPEED)
        sp_frac = max(0.0, min(1.0, spd / OPENING_SCROLL_SPEED))
        ph = getattr(self, "_opening_phase", "roll")
        t = self._opening_t
        # Headlight strength drives the whole scene's brightness.
        light = 0.30 + 0.70 * sp_frac
        if ph == "dead":
            light = 0.08 + 0.10 * abs(math.sin(t * 9.0))

        def L(c):
            return (int(c[0] * light), int(c[1] * light), int(c[2] * light))

        cx = W // 2
        cy = int(H * 0.78) + int(math.sin(t * 5.0) * 1.5 * sp_frac)
        road_w = int(W * 0.46)
        rx0 = cx - road_w // 2
        rx1 = rx0 + road_w

        # Night sky + a faint scatter of cold, twinkling stars at the top.
        s.fill((7, 8, 13))
        if getattr(self, "_opening_stars", None) is None:
            rs = random.Random(91)
            self._opening_stars = [
                (rs.randint(0, W), rs.randint(0, int(H * 0.25)),
                 rs.randint(1, 2), rs.uniform(0.3, 1.0)) for _ in range(44)]
        for sx, sy, sr, sb in self._opening_stars:
            tw = 0.6 + 0.4 * math.sin(t * 1.6 + sx * 0.05)
            c = int(140 * sb * tw)
            pygame.draw.circle(s, (c, c, int(c * 1.15)), (sx, sy), sr)

        # Off-road darkness either side (the forest floor between trunks).
        pygame.draw.rect(s, (6, 8, 8), (0, 0, rx0 - 9, H))
        pygame.draw.rect(s, (6, 8, 8), (rx1 + 9, 0, W - (rx1 + 9), H))

        # Gravel shoulders + asphalt, lit by the headlights.
        pygame.draw.rect(s, L((48, 45, 40)), (rx0 - 10, 0, 10, H))
        pygame.draw.rect(s, L((48, 45, 40)), (rx1, 0, 10, H))
        pygame.draw.rect(s, L((40, 38, 43)), (rx0, 0, road_w, H))
        # Faded painted edge lines + scrolling centre dashes (the sense of speed).
        pygame.draw.rect(s, L((118, 112, 90)), (rx0 + 4, 0, 2, H))
        pygame.draw.rect(s, L((118, 112, 90)), (rx1 - 6, 0, 2, H))
        y = -50 + int(scroll) % 50
        while y < H:
            pygame.draw.rect(s, L((170, 160, 110)), (cx - 2, y, 4, 26))
            y += 50
        # Dark asphalt patches scrolling by -- subtle road texture.
        patch_sp = 130
        pf = int(scroll // patch_sp)
        for ridx in range(pf - H // patch_sp - 2, pf + 2):
            py = int(scroll - ridx * patch_sp)
            if py < -20 or py > H + 20:
                continue
            r = random.Random(ridx * 53 + 9)
            pygame.draw.ellipse(s, L((30, 29, 33)),
                                (rx0 + r.randint(8, road_w - 26), py,
                                 r.randint(10, 26), r.randint(4, 8)))

        # Dense roadside forest -- the game's own canopy trees
        # (scenes.base._draw_tree), packed tight so each band reads as one
        # thick overhanging wall rather than a row of shapes. Indexed by a
        # stable physical row/column so the per-tree variation doesn't
        # shimmer as it scrolls; staggered rows + jitter break the grid.
        # Drawn to an offscreen layer, dimmed to a night shadow, then
        # blitted so the canopies spill out over the shoulders.
        from scenes.base import _draw_tree
        forest = pygame.Surface((W, H), pygame.SRCALPHA)
        f_sp = 28
        f_first = int(scroll // f_sp)
        f_rows = H // f_sp + 3
        f_cols = (list(range(-8, rx0 - 6, f_sp))
                  + list(range(rx1 + 6, W + 20, f_sp)))
        for ridx in range(f_first - f_rows, f_first + 2):
            yc = scroll - ridx * f_sp
            if yc < -TILE or yc > H + TILE:
                continue
            stagger = (f_sp // 2) if (ridx & 1) else 0
            for xc in f_cols:
                seed = ((ridx * 73856093) ^ ((xc + stagger) * 19349663)) \
                    & 0x7fffffff
                jx = xc + stagger + (seed % 9) - 4
                jy = int(yc) + ((seed >> 4) % 9) - 4
                _draw_tree(forest, jx - 16, jy - 16, seed)
        # Night shadow: a steady dim so the wall doesn't flicker with the
        # engine, lifting only a little when the headlights are strong.
        d = max(0, min(255, int(255 * (0.46 + 0.16 * light))))
        forest.fill((d, d, d, 255), special_flags=pygame.BLEND_RGB_MULT)
        s.blit(forest, (0, 0))

        # A lonely power line down the left shoulder: poles standing above the
        # canopy with a wire sagging from pole to pole. (The right shoulder
        # carries the BRIMLEY sign.) Draws over the trees so it reads as
        # roadside, not lost in the forest.
        pole_sp, pole_x, ph_h = 240, rx0 - 24, 58

        def _attach(idx):
            return (pole_x + 12, int(scroll - idx * pole_sp) - ph_h + 9)
        lo = int(scroll // pole_sp) - H // pole_sp - 2
        hi = int(scroll // pole_sp) + 2
        wire_c = L((48, 50, 54))
        for idx in range(lo, hi):
            ax, ay = _attach(idx)
            bx, by = _attach(idx + 1)
            if max(ay, by) < -60 or min(ay, by) > H + 60:
                continue
            pygame.draw.lines(s, wire_c, False,
                              [(ax, ay), ((ax + bx) // 2 + 7,
                                          (ay + by) // 2 + 9), (bx, by)], 1)
        for idx in range(lo, hi):
            yb = int(scroll - idx * pole_sp)
            tp = yb - ph_h
            if tp > H + 20 or yb < -20:
                continue
            flare = max(0.0, 1.0 - abs(yb - cy) / 200.0)
            pc = (int(40 + 42 * flare * light), int(36 + 34 * flare * light),
                  int(30 + 24 * flare * light))
            pygame.draw.rect(s, pc, (pole_x - 2, tp, 4, ph_h))      # post
            pygame.draw.rect(s, pc, (pole_x - 11, tp + 6, 23, 3))   # crossarm
            pygame.draw.rect(s, pc, (pole_x - 2, tp - 4, 4, 6))     # cap
            pygame.draw.circle(s, pc, (pole_x - 9, tp + 5), 1)      # insulators
            pygame.draw.circle(s, pc, (pole_x + 9, tp + 5), 1)

        # Reflector posts on the shoulders -- amber dots that flare as the
        # headlights sweep past them.
        post_sp = 150
        pf2 = int(scroll // post_sp)
        for ridx in range(pf2 - H // post_sp - 2, pf2 + 2):
            py = int(scroll - ridx * post_sp)
            if py < -10 or py > H + 10:
                continue
            flare = max(0.0, 1.0 - abs(py - cy) / 160.0)
            for postx in (rx0 - 13, rx1 + 13):
                pygame.draw.rect(s, L((58, 54, 46)), (postx - 1, py - 14, 2, 14))
                ac = (int(110 + 145 * flare * light),
                      int(74 + 96 * flare * light), int(18 + 30 * flare))
                pygame.draw.circle(s, ac, (postx, py - 13), 2)

        # The BRIMLEY sign passes once on the right shoulder.
        sign_y = int(scroll) - 140
        if 0 <= sign_y <= H + 60:
            self._draw_road_sign(s, rx1 + 28, sign_y, light)

        # The Arcadia Lodge's lit roadside sign on the right shoulder: in the
        # dead phase the car has pulled up to it as the engine dies. The
        # building stays off the road (the Arcadia sits back in the corn);
        # the sign gives "The Arcadia Lodge" caption a referent without
        # faking an exterior. Fades in over the start of the dead beat.
        if ph == "dead":
            self._draw_lodge_sign(s, rx1 + 36, cy + 8,
                                  min(1.0, self._opening_phase_t / 0.5))

        # Wet asphalt -- the road reads slick. A cool sheen reflecting the
        # night sky down the lane, a warm streak where the headlights mirror
        # back toward the car, and the taillights bleeding red onto the road
        # behind it. All additive over the dark asphalt.
        gy = cy - int(H * 0.20)
        wet = pygame.Surface((W, H), pygame.SRCALPHA)
        # Warm streak where the headlights mirror back toward the car.
        for i in range(7, 0, -1):
            f = i / 7
            rw = max(1, int(8 * f))
            a = int(20 * (1 - f) * light)
            if a > 0:
                pygame.draw.ellipse(wet, (150, 134, 90, a),
                                    (cx - rw, gy, 2 * rw,
                                     max(2, int((cy - gy) * 0.95))))
        # Taillights bleeding red onto the road behind the car (battery: they
        # stay lit even when the engine's dead, so this persists -- subtly).
        for txo in (-11, 11):
            for i in range(8, 0, -1):
                f = i / 8
                rw = max(1, int(5 * f))
                a = int(15 * (1 - f))
                if a > 0:
                    pygame.draw.ellipse(wet, (165, 40, 30, a),
                                        (cx + txo - rw, cy + 24, 2 * rw,
                                         int(50 * f)))
        s.blit(wet, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Drifting ground mist -- low cool bands the headlights catch. Each
        # band's alpha feathers to nothing at its top and bottom edges (a
        # triangular falloff) so there are no hard horizontal seams.
        mist = pygame.Surface((W, H), pygame.SRCALPHA)
        bh = 80
        for i in range(4):
            my = int(H * 0.30 + i * H * 0.16 + math.sin(t * 0.5 + i) * 12)
            peak = (10 + 7 * i) * (0.5 + 0.5 * light)
            band = pygame.Surface((W, bh), pygame.SRCALPHA)
            for row in range(bh):
                a = int(peak * math.sin(math.pi * row / bh))
                if a > 0:
                    pygame.draw.line(band, (150, 156, 168, a),
                                     (0, row), (W, row))
            mist.blit(band, (int(math.sin(t * 0.3 + i * 2) * 30), my))
        s.blit(mist, (0, 0))

        # The headlight beam itself: a warm cone thrown up the road from the
        # lamps -- hot and tight at the bumper, splaying wider and cooling to
        # amber as it fades into the dark ahead, with a bright hotspot pooling
        # on the asphalt just in front. Built from stacked soft ellipse slices
        # so the falloff is smooth and the sides are rounded -- not a hard
        # trapezoid or a floating disc. (The side-spill onto the trees was
        # dropped: top-down light on the treeline never read as anything but
        # pasted-on glows.)
        # NOTE: the glow layer is blitted with BLEND_RGBA_ADD, which adds the
        # full source RGB wherever a shape is drawn (it ignores the source
        # alpha). So the beam's falloff lives in the COLOUR brightness, scaled
        # by distance and headlight strength -- not in alpha.
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        top_y = int(H * 0.30)
        front = cy - 27                          # at the (1.3x) car's lamps
        reach = int(H * 0.20)                    # how far the beam throws
        span = max(1, front - reach)
        slices = 60
        eh = span // slices * 3 + 4              # tall slices -> heavy overlap
        for i in range(slices, -1, -1):          # far+dim first, near+bright last
            f = i / slices
            y = front - int(f * span)
            half = int(14 + f * f * road_w * 0.44)
            b = (1 - f) ** 1.8 * light            # hot at the lamps, fading up
            col = (min(255, int(176 * b)), min(255, int(150 * b)),
                   min(255, int(104 * b)))
            if col[0] + col[1] + col[2] > 3:
                pygame.draw.ellipse(glow, col,
                                    (cx - half, y - eh // 2, 2 * half, eh))
        for i in range(13, 0, -1):               # hotspot just ahead of bumper
            f = i / 13
            rw, rh = int(40 * f) + 3, int(56 * f) + 3
            hb = (1 - f) ** 1.3 * light
            col = (min(255, int(210 * hb)), min(255, int(196 * hb)),
                   min(255, int(150 * hb)))
            if col[0] + col[1] + col[2] > 3:
                pygame.draw.ellipse(glow, col,
                                    (cx - rw, (front - 38) - rh // 2,
                                     2 * rw, rh))
        s.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Dust / moths drifting up through the headlight beam -- a little
        # life in the only light for miles. They rise toward the beam's
        # reach and fade out, swaying side to side.
        for i in range(7):
            mt = (t * 0.55 + i * 0.37) % 1.0
            my = int(cy - 24 - mt * (cy - top_y - 24))
            mx = cx + int(math.sin(t * 1.3 + i * 2.1) * (16 + mt * 34))
            mc = int(210 * (1 - mt) * min(1.0, light + 0.1))
            if mc > 6:
                pygame.draw.circle(s, (mc, int(mc * 0.94), int(mc * 0.74)),
                                   (mx, my), 1)

        # The car. Exhaust puffs while it stalls and after it dies.
        exhaust = (1.0 - sp_frac) if ph in ("stall", "dead") else 0.0
        self._draw_car(s, cx, cy, light, exhaust=exhaust, scale=1.3)

        # --- Film grade: unify the drive with the cutscene look. Applied to the
        #     WORLD only -- the case cards stamp on top, crisp + legible. ---
        # Chunky downsample -> lo-fi film texture (kills the clean vector edges).
        ds = 1.5
        dw, dh = int(W / ds), int(H / ds)
        s.blit(pygame.transform.scale(
            pygame.transform.smoothscale(s, (dw, dh)), (W, H)), (0, 0))
        # Cold night grade: a cool multiply pulls the whole frame toward blue-
        # grey rot, so the only warmth left is the headlights.
        tint = pygame.Surface((W, H))
        tint.fill((202, 212, 230))
        s.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        # Film grain (animated), denser now for a proper emulsion crawl.
        if getattr(self, "_opening_grain", None) is None:
            g = pygame.Surface((W, H), pygame.SRCALPHA)
            rg = random.Random(7)
            for _ in range(int(W * H * 0.06)):
                if rg.random() < 0.6:
                    v = rg.randint(0, 30)
                    g.set_at((rg.randint(0, W - 1), rg.randint(0, H - 1)),
                             (v, v, v, rg.randint(30, 70)))
                else:
                    v = rg.randint(120, 190)
                    g.set_at((rg.randint(0, W - 1), rg.randint(0, H - 1)),
                             (v, v, int(v * 0.9), rg.randint(10, 28)))
            self._opening_grain = g
        s.blit(self._opening_grain,
               (random.randint(-3, 3), random.randint(-3, 3)))
        # Gate flicker -- the projector light stutters (Darkwood).
        if random.random() < 0.07:
            d = pygame.Surface((W, H))
            d.fill((7, 8, 11))
            s.blit(d, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

        # Heavy edge vignette -- the dark presses in from every edge.
        vig = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(64):
            a = int(175 * (1 - i / 64) ** 1.5)
            pygame.draw.rect(vig, (0, 0, 0, a), (i, i, W - 2 * i, H - 2 * i), 1)
        s.blit(vig, (0, 0))

        # --- Case-file cards flash in over the drive ---
        # Two beats: the case as you roll in (~first 4s), and the arrival as
        # the engine dies. Cards stamp down staggered, like building a file.
        ccx, ccy = int(W * 0.40), int(H * 0.26)
        if t < 4.4:
            self._draw_case_card("CASE FILE  \xb7  BLAINE",
                                 ["MISSING:  Mara Blaine, 26"],
                                 "OPEN", ccx, ccy, t - 0.2, 4.2, 11)
            self._draw_case_card(None, ["LAST SEEN:  Brimley"],
                                 None, ccx + 34, ccy + 44, t - 0.9, 3.5, 23)
            self._draw_case_card(None, ["JOB:  ask around, drive home by dawn"],
                                 None, ccx - 12, ccy + 86, t - 1.6, 2.8, 37)
        if ph == "dead":
            # Lower than the case beat so the cards sit between the lodge
            # (ahead) and the car, not on top of the building.
            dt_ = self._opening_phase_t
            dcy = int(H * 0.60)
            self._draw_case_card("ARRIVAL", ["The Arcadia Lodge."], None,
                                 ccx + 10, dcy, dt_ - 0.2,
                                 OPENING_DEAD_HOLD - 0.2, 41)
            self._draw_case_card(None, ["Engine won't turn over."], "STRANDED",
                                 ccx + 34, dcy + 46, dt_ - 0.8,
                                 OPENING_DEAD_HOLD - 0.8, 53)
