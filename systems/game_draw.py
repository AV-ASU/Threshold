"""Drawing / HUD / cutscene rendering for the Game orchestrator.

Pure presentation code, extracted verbatim from systems/game.py as a
mixin to keep the Game class focused on the threat model and game loop.
`Game` inherits GameDrawMixin, so every ``self.*`` here resolves to the
live Game instance exactly as before -- this is a relocation, not a
behaviour change. Names below are imported from systems.game (resolved
after that module's constants/imports are defined, just before the Game
class is built).
"""

from systems.game import (
    AXE_SWING_DUR,
    CULT_DARK_SCENES,
    CURSE_RITUAL_TIME,
    C_BG,
    C_BLACK,
    C_BLOOD,
    C_GOLD,
    C_WHITE,
    DARK_SCENES,
    DIM_SAFE_SCENES,
    KING_FREE_SCENES,
    KING_THREAT_FAR,
    KING_THREAT_NEAR,
    NOTEBOOK_TOAST_DUR,
    OPENING_DEAD_HOLD,
    OPENING_SCROLL_SPEED,
    OUTDOOR_SCENES,
    RITE_YANK_DUR,
    SAFE_SCENES,
    SCREEN_H,
    SCREEN_W,
    TILE,
    draw_axe_swing,
    draw_carcosa,
    draw_infested_overlay,
    draw_king_death,
    draw_mask_yank,
    draw_npc_corpse,
    draw_npc_sprite,
    draw_player_sprite,
    draw_vessel_bloom,
    math,
    pygame,
    random,
)


class GameDrawMixin:
    def draw_title(self):
        """Stark title. Black field with a slow noise grain, the word
        THRESHOLD held still in the centre, options below in a quiet
        column. No music other than the wind drone -- if the player
        sits on this screen, all they hear is the wind. The title text
        breathes very slightly (1px vertical drift on a 6-second
        period) so the screen never feels frozen, but never feels
        alive either."""
        t = pygame.time.get_ticks() / 1000.0
        self.screen.fill((4, 3, 7))
        # Slow grain: a sparse field of single-pixel noise that drifts
        # imperceptibly. Just enough to keep the screen from looking
        # like a static frame.
        grain_seed = int(t * 6) & 0xFFFF
        for i in range(200):
            n = (i * 9931 + grain_seed * 17) & 0xFFFFFF
            sx = n % SCREEN_W
            sy = (n >> 8) % SCREEN_H
            v = 14 + ((n >> 16) & 0x1F)
            self.screen.set_at((sx, sy), (v, v, v + 4))
        # The title itself. Held dead centre, no shake, no colour
        # cycling. Letter-spacing widened so the word reads as a slab
        # rather than a friendly logo.
        title_text = "T H R E S H O L D"
        title_font = self.fonts["title"]
        title_surf = title_font.render(title_text, True, (170, 168, 174))
        # 1px vertical breath, very slow.
        breath = int(math.sin(t * 1.05) * 1)
        tx = SCREEN_W // 2 - title_surf.get_width() // 2
        ty = 180 + breath
        # A faint shadow, no offset bounce.
        shadow = title_font.render(title_text, True, (0, 0, 0))
        self.screen.blit(shadow, (tx + 2, ty + 2))
        self.screen.blit(title_surf, (tx, ty))
        # No subtitle. Negative space below the word.
        opts = self._title_menu_options()
        # Clamp the cursor in case the option list shrank (e.g. the
        # player hit Delete Save while highlighting it -- the slot
        # stays valid but the label flipped).
        if self.title_choice >= len(opts):
            self.title_choice = len(opts) - 1
        for i, opt in enumerate(opts):
            if i == self.title_choice:
                color = (220, 218, 226)
            else:
                color = (96, 92, 104)
            txt = self.fonts["lg"].render(opt, True, color)
            tx2 = SCREEN_W // 2 - txt.get_width() // 2
            ty2 = 360 + i * 44
            if i == self.title_choice:
                # A single small bracket on the left only -- asymmetric,
                # never resolves to a neat selector.
                marker = self.fonts["lg"].render("[", True, (220, 218, 226))
                self.screen.blit(marker, (tx2 - 24, ty2))
            self.screen.blit(txt, (tx2, ty2))
        hint = self.fonts["sm"].render(
            "arrow keys . enter . F11", True, (60, 58, 68))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                SCREEN_H - 28))
    def _draw_brimley_haze(self):
        """Atmospheric overlay. Brimley and alter_room always run the
        outdoor haze + vignette. EVERY OTHER SCENE also runs the
        outdoor haze + vignette while the player is carrying the
        playscript -- the playscript's presence is hostile, the world dims around
        it."""
        if self.scene is None:
            return
        key = self.scene.key
        # Safe / dim-safe interiors break the playscript-haze. Walking
        # back to the Inn (or the cellar) with the playscript is meant
        # to feel like a refuge from the hostile dim, not a
        # continuation of it.
        if key in SAFE_SCENES or key in DIM_SAFE_SCENES:
            return
        holds_playscript = (self.player is not None
                     and self.player.inventory.has("playscript"))
        if key == "brimley" or holds_playscript:
            # Lighter than the old crushing flat-170: the map should read as
            # a dim, lantern-lit town, not a blackout. Lights carve both the
            # haze (inside _draw_haze) and the stillness vignette below.
            self._draw_haze(96, (40, 40, 50, 64), 14, 24, 0.3, 30)
            self._draw_vignette()
    def _draw_vignette(self):
        """Player-centred radial darkness. Stillness ENCROACHES: the
        clear hole shrinks as `stillness_t` grows, so a player who
        stops moving in the haze feels the dark close on them. Walking
        opens the hole back up.

        Cached: 4 vignette surfaces at different inner radii built on
        first need; one of them is picked each frame based on the
        stillness phase. Costs a single alpha-blit."""
        if self.player is None:
            return
        if self._vignette_surf is None:
            self._vignette_surf = self._build_vignette_levels()
        # Stillness phase 0 = moving (widest hole), 3 = locked-in
        # (tightest). 1.5s, 4s, 8s thresholds.
        st = self.stillness_t
        if st < 1.5:
            level = 0
        elif st < 4.0:
            level = 1
        elif st < 8.0:
            level = 2
        else:
            level = 3
        surf = self._vignette_surf[level]
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))
    def _restamp_lights(self):
        """Re-assert world lights (lanterns, braziers, candles -- every pool
        that registered in decoration.LIGHT_SOURCES this frame) ON TOP of
        the haze + vignettes. Decorations draw before the dark-overlays, so
        without this the dim buries them; here the warm pools punch back
        through, reading as lit refuges in the gloom. A handful of cached
        blits -- no masks, no per-pixel work. Skipped under the King's apex
        (you can't out-glow Him) so the re-stamp runs BEFORE _draw_apex."""
        from entities.decoration import LIGHT_SOURCES, restamp_light
        for cx, cy, radius, color, peak in LIGHT_SOURCES:
            if (cx < -radius * 2 or cx > SCREEN_W + radius * 2
                    or cy < -radius * 2 or cy > SCREEN_H + radius * 2):
                continue
            # Two stamps: a wider, softer reach to lift the dim, then the
            # original tight pool to keep the warm hotspot.
            restamp_light(self.screen, cx, cy, radius, color, peak, boost=1.7)
            restamp_light(self.screen, cx, cy, radius, color, peak)
    def _draw_outdoor_vignette(self):
        """Soft, always-on player-centred vignette for OUTDOOR_SCENES.
        Wider clear hole and lower peak alpha than the brimley
        vignette -- doesn't oppress, just keeps the corners of the
        screen unsafe. Pursuer proximity tightens the hole over time:
        the world literally narrows as the threshold closes."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in OUTDOOR_SCENES:
            return
        if self._outdoor_vignette_surf is None:
            self._outdoor_vignette_surf = self._build_outdoor_vignette()
        # Pursuer proximity selects between two cached surfaces:
        # 0 = early game (wide), 1 = late (tighter). Avoids
        # rebuilding the gradient every frame.
        level = 1 if self.visibility > 0.55 else 0
        surf = self._outdoor_vignette_surf[level]
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))
    def _draw_apex_overlay(self):
        """Apex-tier rendering: when visibility hits >= 0.95,
        the world goes wrong. Heavy red wash across the whole screen
        (interiors and exteriors alike); the screen edges crush in
        with a hard black vignette so the player's view narrows;
        the overlay pulses on a slow sine so the dread reads as
        active, not static. Cheap: two SRCALPHA blits per frame."""
        if self.scene is None or self.player is None:
            return
        if self.visibility < 0.95:
            return
        # Safe / dim-safe interiors break the apex wash. The Inn is
        # the refuge. Standing inside it lifts the apex pressure --
        # only stepping out re-engages it. Reads as a deliberate
        # sanctuary mechanic rather than a hole in the horror.
        if (self.scene.key in KING_FREE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 1.4)
        # Red wash across the whole screen. Uses C_BLOOD (a desaturated
        # dried-blood red) rather than primary red so the apex tone
        # reads as "wrong" without going carnival-haunted. Wash alpha
        # routed through _claim_dark so the combined-darkness budget
        # caps stacked overlays.
        wash_a = self._claim_dark(int(70 * pulse))
        wash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        wash.fill((C_BLOOD[0], C_BLOOD[1], C_BLOOD[2], wash_a))
        self.screen.blit(wash, (0, 0))
        # Edge-crush vignette: heavy black ring around the screen
        # with a clear ~110-px disc around the player. Forces the
        # player to feel tunnel-vision. Inner radius pulses with
        # the wash so the disc breathes with the world.
        edge_a = self._claim_dark(int(180 * pulse))
        edge = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        edge.fill((0, 0, 0, edge_a))
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        clear_r = int(110 + 6 * math.sin(t * 1.4))
        pygame.draw.circle(edge, (0, 0, 0, 0), (psx, psy), clear_r)
        self.screen.blit(edge, (0, 0))
    def _draw_hidden_overlay(self):
        """While player.hidden is set, render a dark vignette
        around the player so the screen FEELS cramped -- the player
        is crouched in cover, vision narrow. Draws on top of every
        other overlay. Does not block gameplay; the camera still
        shows what's there, just dimmer at the edges. Softened
        from the prior pass: 60% wash with a wider clear disc so
        the cover read is "narrow" not "blind"."""
        if self.scene is None or self.player is None:
            return
        if getattr(self.player, "hidden", None) is None:
            return
        # Corn cover is walking-through-stalks, not crouched. The
        # player can still see forward; the vignette would lie
        # about that. Cultist sight cone IS still reduced (the
        # player.hidden flag handles that), so the mechanical
        # benefit stands.
        if self.player.hidden == "corn":
            return
        # Safe interiors: you're already safe, the hide-cramp read
        # is wrong here. Basement (DIM_SAFE) keeps the cramp -- its
        # hide spots are still meaningful cover.
        if self.scene.key in SAFE_SCENES:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        # 60% wash (153 alpha) routed through the darkness cap so
        # hide stacked with apex/dip never blots the whole screen.
        wash_a = self._claim_dark(153)
        layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        layer.fill((0, 0, 0, wash_a))
        clear_r = 95
        for r_step in range(8):
            r = max(8, clear_r + 16 - r_step * 4)
            pygame.draw.circle(layer, (0, 0, 0, 0), (psx, psy), r)
        self.screen.blit(layer, (0, 0))
    def _draw_dark(self):
        """Dark interiors/underground (DARK_SCENES) render as a navigable
        gloom: a moderate black tint over the whole scene so it reads
        dim-but-legible, with a clear pool around the player.

        With the flashlight LIT (`_flashlight_lit`) the near pool warms and
        a long beam cone is carved out of the gloom in the player's facing
        direction -- they can read the room far ahead. Without it, only a
        cold "eyes-adjusted" pool lifts the near floor out of pure black.
        Cult-dark rooms force the beam off (handled by `_flashlight_lit`)
        and sit a touch heavier."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in DARK_SCENES:
            return
        from scenes.base import _light_pool
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        lit = self._flashlight_lit()
        # Build the beam cone geometry once (apex -> left -> tip -> right).
        cone = None
        if lit:
            fx, fy = getattr(self.player, "facing", (0, 1)) or (0, 1)
            flen = math.hypot(fx, fy) or 1.0
            ang = math.atan2(fy / flen, fx / flen)
            reach, spread = 300, math.radians(30)
            tip = (psx + reach * math.cos(ang), psy + reach * math.sin(ang))
            left = (psx + reach * math.cos(ang - spread),
                    psy + reach * math.sin(ang - spread))
            right = (psx + reach * math.cos(ang + spread),
                     psy + reach * math.sin(ang + spread))
            cone = [(psx, psy), left, tip, right]
        if lit:
            # A warm held-light pool at the feet -- not eyes adjusting.
            _light_pool(self.screen, psx, psy, 96, (240, 226, 165), 72)
        else:
            _light_pool(self.screen, psx, psy, 112, (118, 124, 150), 96)
        gloom = 130 if self.scene.key in CULT_DARK_SCENES else 100
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, gloom))
        rings = [(30 + i * 14, int(gloom * i / 8)) for i in range(8)]
        for rr, aa in sorted(rings, key=lambda p: -p[0]):
            pygame.draw.circle(overlay, (0, 0, 0, aa), (psx, psy), rr)
        if cone:
            # Carve the beam clear of the gloom (alpha 0 inside the cone).
            pygame.draw.polygon(overlay, (0, 0, 0, 0), cone)
        self.screen.blit(overlay, (0, 0))
        if cone:
            # A faint warm wash inside the cone sells it as a light source.
            beam = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.polygon(beam, (250, 232, 170, 26), cone)
            self.screen.blit(beam, (0, 0))
    def _tinted_fog_blob(self, size, fog_rgba):
        """A cached soft fog patch tinted with `fog_rgba`, built in ONE
        numpy pass: the colour is constant and the alpha is the smooth
        radial falloff scaled by the tint's own alpha. Doing tint+falloff
        together at float precision avoids the double-quantization (uniform
        fill, then BLEND_MULT) that left faint concentric rings. The haze
        re-blits this single cached surface at drifting positions."""
        cache = getattr(self, "_tinted_fog_cache", None)
        if cache is None:
            cache = self._tinted_fog_cache = {}
        key = (size, fog_rgba)
        s = cache.get(key)
        if s is None:
            import numpy as np
            r = size / 2.0
            yy, xx = np.ogrid[0:size, 0:size]
            d = np.clip(np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r, 0.0, 1.0)
            falloff = 1.0 - (3 * d * d - 2 * d * d * d)      # smoothstep
            cr, cg, cb, ca = fog_rgba
            alpha = (falloff * ca).astype(np.uint8)
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            rgb = pygame.surfarray.pixels3d(s)
            rgb[:, :, 0] = cr
            rgb[:, :, 1] = cg
            rgb[:, :, 2] = cb
            del rgb
            a = pygame.surfarray.pixels_alpha(s)
            a[:, :] = alpha.T
            del a
            cache[key] = s
        return s

    def _draw_haze(self, base_alpha, fog_rgba, fog_n, drift_x, sway_amp,
                   sway_y_amt):
        """Reusable haze helper: a soft dim plus drifting SOFT fog blobs.
        World lights are re-stamped OVER this afterward (_restamp_lights),
        so lanterns/braziers read through it. Brimley is tuned lighter than
        the old crushing flat-170 with hard squares: the beautiful map
        should read as a dim lantern-lit town, the dark as mood not a
        blackout. The fog blobs are soft rounds now, not 160px squares."""
        if base_alpha:
            # Plain (non-SRCALPHA) surface + set_alpha is markedly faster to
            # blit than a full-screen SRCALPHA fill, and the result is
            # identical for a flat black dim.
            dim = self._haze_dim_surf
            if dim is None:
                dim = self._haze_dim_surf = pygame.Surface((SCREEN_W, SCREEN_H))
                dim.fill((0, 0, 0))
            dim.set_alpha(base_alpha)
            self.screen.blit(dim, (0, 0))
        t = pygame.time.get_ticks() / 1000.0
        # Scatter patches at VARIED sizes (cached per size) so they overlap
        # and merge into a continuous fog field instead of reading as a
        # regular grid of same-size polka-dots. Each patch keeps a stable
        # size from its index; positions drift/sway as before. Roughly
        # double the count so the field fills in. Larger patches are
        # blitted additively-soft (normal alpha) and just pile up where
        # they overlap, which is what makes it read as formless fog.
        sizes = (280, 360, 220, 320, 200, 300)
        n = fog_n * 2
        for i in range(n):
            size = sizes[i % len(sizes)]
            tinted = self._tinted_fog_blob(size, fog_rgba)
            half = size // 2
            fx = ((i * 167 + int(t * drift_x + i * 50))
                  % (SCREEN_W + size + 160) - (half + 80))
            fy = (((i * 233) % (SCREEN_H + size) - half)
                  + int(math.sin(t * sway_amp + i * 0.7) * sway_y_amt))
            self.screen.blit(tinted, (fx, fy))
    def _draw_flashback(self):
        """Render the flashback overlay if active. Black field, large
        white text in the centre, no other UI."""
        if self._flashback_phase is None:
            return
        line, dur = self._flashback_stills[self._flashback_phase]
        # Fade in over first 0.3s, hold, fade out over last 0.3s.
        t = self._flashback_t / max(0.01, dur)
        if t < 0.15:
            alpha = int((t / 0.15) * 255)
        elif t > 0.85:
            alpha = int(((1.0 - t) / 0.15) * 255)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        # Black field underneath.
        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))
        self.screen.blit(veil, (0, 0))
        # Text -- white, fading.
        s = self.fonts["lg"].render(line, True, (220, 218, 226))
        s.set_alpha(alpha)
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                             SCREEN_H // 2 - s.get_height() // 2))
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
        veil = pygame.Surface((SCREEN_W, SCREEN_H))
        veil.fill((0, 0, 0))
        self.screen.blit(veil, (0, 0))
        s = self.fonts["lg"].render(line, True, (220, 218, 226))
        s.set_alpha(alpha)
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2,
                             SCREEN_H // 2 - s.get_height() // 2))
    def _draw_death_screen(self):
        """Render the active death card over everything. King = the
        furnace of masks (sprites.draw_king_death) stamped CARCOSA;
        cultist = a stark CAPTURED card over a near-black wash."""
        if self._death_kind == "king":
            draw_king_death(self.screen, self._death_t)
            if self._death_t > 3.0:                  # the name surfaces over the descent
                w, h = self.screen.get_size()
                ta = min(235, int((self._death_t - 3.0) / 0.55 * 235))
                tt = self.fonts["title"].render("CARCOSA", True, (236, 204, 64))
                tt.set_alpha(ta)
                self.screen.blit(tt, (w // 2 - tt.get_width() // 2,
                                      h // 2 - tt.get_height() // 2))
            return
        # Cultist: the cult takes you (CAPTURED). Sheriff: the hollow
        # lawman takes you in (TAKEN INTO CUSTODY). Fade to near-black,
        # then the card. The Sheriff card is tinted his dull tin-star gold.
        w, h = self.screen.get_size()
        fade = min(255, int(self._death_t / 0.4 * 255))
        wash = pygame.Surface((w, h))
        wash.fill((6, 5, 7))
        wash.set_alpha(fade)
        self.screen.blit(wash, (0, 0))
        if self._death_kind == "sheriff":
            label, col, sub = ("TAKEN INTO CUSTODY", (188, 172, 96),
                               "The badge was just clothing. The hold is not.")
        else:
            label, col, sub = ("CAPTURED", (170, 150, 90), None)
        if self._death_t > 0.35:
            ta = min(255, int((self._death_t - 0.35) / 0.4 * 255))
            big = self.fonts["title"].render(label, True, col)
            big.set_alpha(ta)
            self.screen.blit(big, (w // 2 - big.get_width() // 2,
                                   h // 2 - big.get_height() // 2))
            if sub and self._death_t > 0.9:
                sa = min(210, int((self._death_t - 0.9) / 0.5 * 210))
                st = self.fonts["sm"].render(sub, True, (150, 140, 110))
                st.set_alpha(sa)
                self.screen.blit(st, (w // 2 - st.get_width() // 2,
                                      h // 2 + big.get_height()))
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
    def draw_world(self):
        if self.state == "opening":
            self._draw_opening()
            return
        self.screen.fill(C_BG)
        if not self.scene: return
        # Clear the per-frame world-light registry before any decoration
        # draws its pool -- the lanterns/braziers/candles repopulate it as
        # scene.draw runs, and the overlay pass reads it to carve the dark.
        from entities.decoration import reset_lights
        reset_lights()
        self.scene.draw(self.screen, self.cam_x, self.cam_y)
        # Fold reveals: the far side of any in-sight fold shows through,
        # drawn over terrain but under items/actors so the player walks
        # "in front of" the peek. Pure presentation.
        from systems.folds import draw_reveals
        draw_reveals(self, self.screen)
        for it in self.scene.items:
            sx = int(it["x"] - self.cam_x); sy = int(it["y"] - self.cam_y)
            t = pygame.time.get_ticks() / 200.0
            bob = int(math.sin(t + (it["x"] + it["y"]) * 0.01) * 1)
            color = self._item_color(it["key"])
            pygame.draw.rect(self.screen, color, (sx - 4, sy - 4 + bob, 8, 8))
            pygame.draw.rect(self.screen, C_BLACK, (sx - 4, sy - 4 + bob, 8, 8), 1)
        # Pick at most one NPC to "blink" this frame -- their eye dots
        # will skip drawing for a single frame. Only fires while the
        # player is standing still, and only rarely. The villagers
        # don't blink, except, very rarely, one does.
        blink_idx = -1
        if self.stillness_t > 1.5 and random.random() < 1 / 300:
            human_kinds = ("townswoman", "tisdale_boy", "old_townsman",
                           "hettie", "sheriff", "royce", "preacher", "clerk")
            human_npcs = [i for i, n in enumerate(self.scene.npcs)
                          if n.sprite_kind in human_kinds]
            if human_npcs:
                blink_idx = random.choice(human_npcs)
        # Wrap-clone offsets. In a toroidal scene an actor near one seam
        # must also be drawn at the opposite edge, or it pops out of
        # existence when the player straddles the fold (decorations are
        # already cloned this way in Scene.draw). For non-wrap scenes
        # this is exactly [(0, 0)] -- identical to the old single draw.
        sc = self.scene
        _offsets = sc.wrap_offsets()

        def _on_screen(sx, sy):
            return -64 <= sx <= SCREEN_W + 64 and -64 <= sy <= SCREEN_H + 64

        for i, npc in enumerate(self.scene.npcs):
            # A homebody currently inside their door: not drawn at all.
            if getattr(npc, "_inside", False):
                continue
            # A persisted corpse: draw it prone in its blood and skip all
            # the living-NPC logic (morph, blink, king-threat, gaze).
            if not getattr(npc, "alive", True):
                for ox, oy in _offsets:
                    sx = int(npc.x + ox - self.cam_x)
                    sy = int(npc.y + oy - self.cam_y)
                    if not _on_screen(sx, sy):
                        continue
                    draw_npc_corpse(self.screen, sx, sy, npc.sprite_kind,
                                    seed=id(npc) & 0xffff,
                                    mold=self._infest_stage())
                continue
            m = getattr(npc, "morph", 0.0)
            king_threat = None
            if npc.sprite_kind == "yellow_king" and self.player:
                d = math.hypot(npc.x - self.player.x, npc.y - self.player.y)
                span = KING_THREAT_FAR - KING_THREAT_NEAR
                # Existence is purely proximity: a far void that blooms only
                # as he closes. Visibility is NOT mixed in here -- it's the
                # spawn/despawn gate (_tick_king), and while he's present it
                # only ever sits in [0.90, 1.0], far too narrow a band to
                # read as existence (it would just pin him near-real the
                # whole time he's on screen). The 0.15 floor keeps him a
                # faint watching void, never fully gone, until he nears.
                king_threat = max(0.15, min(1.0, 1.0 - (d - KING_THREAT_NEAR) / span))
            for ox, oy in _offsets:
                sx = int(npc.x + ox - self.cam_x); sy = int(npc.y + oy - self.cam_y)
                if not _on_screen(sx, sy):
                    continue
                if m > 0.0:
                    draw_vessel_bloom(self.screen, sx, sy, npc.sprite_kind,
                                      npc.facing, m, seed=id(npc) & 0xffff)
                else:
                    # Curse-priest: bloom on the actual rite -- ramps as it
                    # holds you in its gaze, peaks/flashes as it binds you.
                    curse_v = 0.0
                    if npc.sprite_kind == "curse_priest":
                        rt = getattr(npc, "_ritual_t", 0.0)
                        cd = getattr(npc, "_curse_cd", 0.0)
                        ramp = min(1.0, rt / CURSE_RITUAL_TIME)
                        flash = max(0.0, (cd - (CURSE_RITUAL_TIME - 0.7)) / 0.7)
                        curse_v = max(ramp, flash)
                    # A Watcher being stared down: its eyes go dark (gaze) and
                    # it fades as the dispel timer fills, so the cure reads.
                    w_gaze = (npc.sprite_kind == "watcher"
                              and getattr(npc, "_gaze_dispel_t", 0.0) > 0.05)
                    draw_npc_sprite(self.screen, sx, sy, npc.sprite_kind,
                                    npc.facing, blink=(i == blink_idx),
                                    birth=getattr(npc, "_birth", None),
                                    gait=getattr(npc, "_gait", None),
                                    threat=king_threat, seed=id(npc) & 0xffff,
                                    curse=curse_v, gaze=w_gaze)
                    # A resister whose flesh has turned: their bespoke
                    # fold-horror form, laid over the person they were.
                    if getattr(npc, "_mutated", False):
                        draw_infested_overlay(self.screen, sx, sy,
                                              npc.sprite_kind)
            # THRESHOLD: NPC name labels removed. They were the
            # last RPG-tell on screen -- the player should learn
            # who an NPC is by interacting with them, not by
            # reading a tag floating over their head. Strangers
            # on the road read as STRANGERS until they speak.
        for e in self.scene.enemies:
            for ox, oy in _offsets:
                sx = int(e.x + ox - self.cam_x); sy = int(e.y + oy - self.cam_y)
                if not _on_screen(sx, sy):
                    continue
                e.draw(self.screen, self.cam_x - ox, self.cam_y - oy)
        for p in self.scene.projectiles:
            p.draw(self.screen, self.cam_x, self.cam_y)
        if self.player:
            psx = int(self.player.x - self.cam_x)
            psy = int(self.player.y - self.cam_y)
            if self.player.invuln > 0 and int(self.player.invuln * 12) % 2 == 0:
                pass
            elif self.player.hidden is not None:
                # THRESHOLD: hidden player draws on a low-alpha layer
                # so the silhouette is barely visible -- the cover
                # is reading as cover. Also draws a single faint
                # "[hidden]" tag above so the player knows the state
                # is on without needing a HUD widget.
                hide_layer = pygame.Surface((40, 60), pygame.SRCALPHA)
                draw_player_sprite(hide_layer, 20, 30, self.player.facing,
                                   0,
                                   armor=self.player.inventory.equipped["armor"],
                                   prone=getattr(self.player, "prone", False))
                hide_layer.set_alpha(80)
                self.screen.blit(hide_layer, (psx - 20, psy - 30))
                tag = self.fonts["tiny"].render("[hidden]", True,
                                                 (160, 158, 170))
                self.screen.blit(tag, (psx - tag.get_width() // 2,
                                       psy - 40))
            else:
                draw_player_sprite(self.screen, psx, psy, self.player.facing,
                                   self.player.walk_phase,
                                   armor=self.player.inventory.equipped["armor"],
                                   prone=getattr(self.player, "prone", False))
            # The axe swing: a wood haft + steel head arcing through the
            # facing hemisphere, with a brief motion smear so the chop
            # reads. Progress walks 0->1 as melee_swing_t bleeds down.
            if self.player.melee_swing_t > 0:
                prog = 1.0 - (self.player.melee_swing_t / AXE_SWING_DUR)
                draw_axe_swing(self.screen, psx, psy,
                               self.player.melee_dir, prog)
        # Reset the per-frame full-screen darkness budget. Each
        # whole-screen black overlay below claims a slice via
        # _claim_dark() so the combined wash never exceeds
        # MAX_FULLSCREEN_DARK. The player's feet stay readable even
        # when hide + apex stack.
        self._overlay_dark_used = 0
        self._draw_brimley_haze()
        self._draw_dark()
        self._draw_outdoor_vignette()
        # Re-stamp world lights (lanterns/braziers/candles) OVER the haze +
        # vignettes so they read through the dim -- but BEFORE the apex and
        # hide overlays, which fully override (you can't out-glow the King,
        # or light your way out of cover).
        self._restamp_lights()
        self._draw_apex_overlay()
        self._draw_hidden_overlay()
        # Film grade over the whole world layer (desaturate, cool tint,
        # vignette, animated grain) -- fuses the frame into one grimy
        # image. Applied before the HUD so UI text stays crisp.
        from scenes.base import apply_grade
        apply_grade(self.screen, pygame.time.get_ticks() / 1000.0)
        self._draw_interact_prompt()
        self._draw_hud()
        self._draw_notebook_toast()
        self.dialog.draw(self.screen)
        self.inv_ui.draw(self.screen, self.player)
        self.notebook_ui.draw(self.screen)
        # Text-input modal (LOGIN: terminal etc.) drawn over inventory so
        # it always wins focus.
        self.text_input.draw(self.screen)
        if self.notice_text:
            self._draw_notice()
        if self.state == "transition":
            t = self.transition_t / 0.85
            alpha = int(t * 255) if self.transition_dir == "out" else int((1 - t) * 255)
            alpha = max(0, min(255, alpha))
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill(C_BLACK)
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
        # Flashback overlay -- preempts everything for the duration of
        # the witnessing sequence.
        self._draw_flashback()
        # Ending overlay -- preempts everything during the ending
        # sequences.
        self._draw_ending()
        # Death screen -- the King's mask furnace or the cultist KILLED
        # card. Drawn over EVERYTHING (HUD, dialog) so the catch takes
        # the whole frame.
        if self._death_kind is not None:
            self._draw_death_screen()
    def _draw_interact_prompt(self):
        """Float an [E] over whatever pressing E would act on right now,
        mirroring try_interact's priority so the cue never lies: a
        hide-spot first (the core stealth affordance), then an adjacent
        axe-chop target, a chest, or an NPC to talk to. Drawn over the
        world, under the HUD."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        if self.player.hidden is not None:
            return
        px, py = self.player.x, self.player.y
        target = None
        # 1. Hide spot within reach -- the single most important cue in a
        # hide-or-die game: tell the player where cover is.
        for hx, hy, _k in (getattr(self.scene, "hide_spots", None) or []):
            if math.hypot(hx - px, hy - py) < 36:
                target = (hx, hy)
                break
        # 2. Axe-chop target on an adjacent tile (debris / boards).
        if target is None and self.player.inventory.has("lumber_axe"):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                tx = int((px + dx * TILE) // TILE)
                ty = int((py + dy * TILE) // TILE)
                if (0 <= ty < self.scene.h and 0 <= tx < self.scene.w
                        and self.scene.objects[ty][tx] in ("*", "q", "K")):
                    target = (tx * TILE + 16, ty * TILE + 16)
                    break
        # 3. A chest within reach -- but only if it's actually openable.
        # Decorative chests (e.g. the Sorting Hall's sealed cases) pass
        # interactive=False so they don't advertise a dead [E].
        if target is None:
            for d in self.scene.decorations:
                if (getattr(d, "kind", "") == "chest"
                        and d.kwargs.get("interactive", True)
                        and math.hypot(d.x - px, d.y - py) < 40):
                    target = (d.x, d.y - 8)
                    break
        # 4. An NPC to talk to.
        if target is None:
            for npc in self.scene.npcs:
                if getattr(npc, "no_prompt", False):
                    continue
                if math.hypot(npc.x - px, npc.y - py) < 40:
                    target = (npc.x, npc.y)
                    break
        # 5. A scene interactable (on_interact_fn readable/pickup -- the
        # case notebook, the cellar Ledger, the Mask altar). Last, to
        # mirror try_interact running on_interact_fn after NPCs.
        if target is None:
            for ix, iy, irad in getattr(self.scene, "interactables", ()):
                if math.hypot(ix - px, iy - py) < irad:
                    target = (ix, iy)
                    break
        if target is None:
            return
        sx = int(target[0] - self.cam_x)
        sy = int(target[1] - self.cam_y) - 40
        t = pygame.time.get_ticks() / 250.0
        yo = int(math.sin(t) * 2)
        txt = self.fonts["sm"].render("[E]", True, C_GOLD)
        self.screen.blit(txt, (sx - txt.get_width() // 2, sy + yo))
    def _draw_hud(self):
        """THRESHOLD HUD. No HP bar, no equipped-weapon label. The
        player has no health to track and no weapon they can use. All
        that's left is a small dim line in the corner that names the
        current threshold -- the only HUD element is an admission of
        where you've ended up."""
        if not self.player or not self.scene:
            return
        # Scene-name label, very small, very dim, lower-left.
        from scenes.base import scene_display_name
        scene_label = scene_display_name(self.scene)
        s = self.fonts["tiny"].render(scene_label, True, (60, 56, 70))
        self.screen.blit(s, (14, SCREEN_H - 22))
        # Ammo readout, lower-right -- only while carrying the pistol. Red
        # when empty. Dim, like the rest of the HUD.
        if self.player.inventory.has("pistol"):
            ammo = self.player.inventory.count("pistol_ammo")
            col = (200, 70, 60) if ammo <= 0 else (140, 136, 112)
            a = self.fonts["tiny"].render(f"rounds  {ammo}", True, col)
            self.screen.blit(a, (SCREEN_W - a.get_width() - 14,
                                 SCREEN_H - 22))
        # Flashlight state -- only surfaces in the dark, and only once you
        # carry a light. Warm amber when the beam's actually burning (so
        # the cost it's adding to the meter is legible), cold and dim when
        # off, and a dead grey in cult-dark where the beam won't catch.
        if (self.scene.key in DARK_SCENES
                and self.player.inventory.has("flashlight")):
            if self._flashlight_lit():
                lbl, col = "[F] light: on", (210, 180, 90)
            elif self.scene.key in CULT_DARK_SCENES:
                lbl, col = "[F] light: dead here", (70, 66, 78)
            else:
                lbl, col = "[F] light: off", (96, 92, 108)
            ls = self.fonts["tiny"].render(lbl, True, col)
            self.screen.blit(ls, (14, SCREEN_H - 36))
        # Threat meter -- thin bar upper-right. Tracks Pursuer
        # proximity (the threat fiction's spine). Stays dim and
        # quiet at low values; warms amber in the middle band; goes
        # bone-cold red and pulses at >= 0.95, where the Yellow King
        # avatar is loose. Player has no number, just a feel for
        # the line tightening.
        prox = max(0.0, min(1.0, self.visibility))
        bar_w = 80
        bar_h = 4
        tx = SCREEN_W - 14 - bar_w
        ty = 14
        # Color blends with proximity. Dim violet -> amber -> red.
        if prox < 0.5:
            t = prox / 0.5
            col = (int(60 + (200 - 60) * t),
                   int(60 + (170 - 60) * t),
                   int(80 + (60 - 80) * t))
        else:
            t = (prox - 0.5) / 0.5
            col = (int(200 + (220 - 200) * t),
                   int(170 + (40 - 170) * t),
                   int(60 + (40 - 60) * t))
        # At max threat, pulse the fill so the bar feels alive --
        # signals the apex state where hiding is the only option.
        if prox >= 0.95:
            t_now = pygame.time.get_ticks() / 1000.0
            pulse = 0.6 + 0.4 * abs(math.sin(t_now * 3.0))
            col = (int(col[0] * pulse), int(col[1] * pulse),
                   int(col[2] * pulse))
        # Frame
        pygame.draw.rect(self.screen, (40, 36, 50),
                         (tx - 1, ty - 1, bar_w + 2, bar_h + 2), 1)
        # The evidence FLOOR is seared in -- a dead, locked base the meter can
        # never bleed below. The bright live fill rides ABOVE it, so the
        # reclaimable headroom you can still hide back into visibly shrinks the
        # more of the case you understand. (NARRATIVE §3, made legible.)
        floor = max(0.0, min(1.0, getattr(self, "_vis_floor", 0.0)))
        fw = int(bar_w * floor)
        pw = int(bar_w * prox)
        if fw > 0:                                   # locked, seared base
            pygame.draw.rect(self.screen, (66, 30, 28), (tx, ty, fw, bar_h))
        if pw > fw:                                  # live reclaimable headroom
            pygame.draw.rect(self.screen, col, (tx + fw, ty, pw - fw, bar_h))
        if fw > 0:                                   # the locked watermark
            pygame.draw.line(self.screen, (122, 52, 44),
                             (tx + fw, ty), (tx + fw, ty + bar_h - 1))
        # Stamina (sprint wind) -- lower-left, just above the scene
        # label. Hidden while full + idle so the minimalist HUD stays
        # quiet; it surfaces the instant you spend wind. Cool blue while
        # you still have breath, red + refilling while you're blown and
        # locked out -- so a chase becomes a gamble: sprint now and risk
        # being caught winded, or keep something in reserve to break for
        # cover.
        p = self.player
        winded = p.sprint_cd > 0
        if p.sprint_active or winded or p.sprint_t < p.sprint_t_max - 0.01:
            sw, sh = 70, 4
            sx2, sy2 = 14, SCREEN_H - 32
            if winded:
                ratio = 1.0 - max(0.0, min(1.0, p.sprint_cd / p.sprint_cd_max))
                fill = (150, 60, 60)
            else:
                ratio = max(0.0, min(1.0, p.sprint_t / p.sprint_t_max))
                fill = (110, 150, 170)
            pygame.draw.rect(self.screen, (40, 36, 50),
                             (sx2 - 1, sy2 - 1, sw + 2, sh + 2), 1)
            pygame.draw.rect(self.screen, fill,
                             (sx2, sy2, int(sw * ratio), sh))
    def _draw_notebook_toast(self):
        """A small page in the upper-left that the PI scribbles a beat onto,
        then it fades -- the diegetic 'added to the notebook' tell, fired by
        _flash_notebook when _evidence logs a new entry."""
        tt = getattr(self, "_notebook_toast_t", 0.0)
        if tt <= 0:
            return
        frac = max(0.0, min(1.0, (NOTEBOOK_TOAST_DUR - tt) / NOTEBOOK_TOAST_DUR))
        if frac < 0.15:
            a = frac / 0.15
        elif frac > 0.75:
            a = max(0.0, (1.0 - frac) / 0.25)
        else:
            a = 1.0
        if a <= 0.0:
            return
        W, H = 34, 42
        surf = pygame.Surface((W, H), pygame.SRCALPHA)

        def C(r, g, b, al=255):
            return (r, g, b, int(al * a))
        # Page + edge + a dog-eared top-right corner.
        pygame.draw.rect(surf, C(224, 218, 202), (2, 3, W - 6, H - 6))
        pygame.draw.rect(surf, C(150, 142, 120), (2, 3, W - 6, H - 6), 1)
        pygame.draw.polygon(surf, C(198, 190, 172),
                            [(W - 8, 3), (W - 8, 9), (W - 4, 3)])
        # Ink lines write on left-to-right over frac ~0.12..0.78.
        write = max(0.0, min(1.0, (frac - 0.12) / 0.66))
        lx0, lx1 = 6, W - 9
        head = None
        for i in range(4):
            lp = max(0.0, min(1.0, write * 4 - i))
            if lp <= 0:
                break
            ly = 12 + i * 7
            x_end = lx0 + int((lx1 - lx0) * lp)
            pts, x = [], lx0
            while x <= x_end:
                pts.append((x, ly + (1 if (x // 3) % 2 == 0 else 0)))
                x += 3
            if len(pts) >= 2:
                pygame.draw.lines(surf, C(38, 32, 42), False, pts, 1)
            head = (x_end, ly)
        # Pen nib at the writing head while it's still scribbling.
        if 0.12 < frac < 0.8 and head:
            px, py = head
            pygame.draw.polygon(surf, C(26, 24, 32),
                                [(px, py - 1), (px + 3, py - 6), (px + 4, py - 1)])
        self.screen.blit(surf, (14, 14))
    def _draw_notice(self):
        s = self.fonts["sm"].render(self.notice_text, True, C_WHITE)
        bg = pygame.Surface((s.get_width() + 24, s.get_height() + 14), pygame.SRCALPHA)
        bg.fill((10, 8, 14, 220))
        x = SCREEN_W // 2 - bg.get_width() // 2
        y = 90
        self.screen.blit(bg, (x, y))
        self.screen.blit(s, (x + 12, y + 7))
    def draw_pause(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        title = self.fonts["xl"].render("PAUSED", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 160))
        for i, opt in enumerate(self.pause_options):
            color = C_GOLD if i == self.pause_choice else C_WHITE
            label = f"> {opt}" if i == self.pause_choice else f"  {opt}"
            txt = self.fonts["lg"].render(label, True, color)
            self.screen.blit(txt, (SCREEN_W//2 - 90, 260 + i * 50))
