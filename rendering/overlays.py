"""Atmosphere render overlays extracted from systems.game.

GameRenderMixin holds presentation-only draw methods that operate on
Game instance state (self.*). They are mixed into Game rather than
rewritten as standalone functions so the split stays behaviour-
preserving; the goal is only to keep systems/game.py focused on
simulation instead of pixel-pushing.

The mixin holds the full atmosphere stack: the vignettes, the mistlands
haze and giant eye, the flashlight cone, the watchers and pursuer
glimpse, the dread / apex / King-in-Yellow washes, the subliminal
flashes and the flashback. The per-frame state these read (timers,
proximity, aperture) is still owned and ticked by Game.
"""
import math
import random

import pygame

from constants import SCREEN_W, SCREEN_H, TILE, C_BLOOD
from rendering.sprites import draw_npc_sprite

# Scene classification used by these overlays. Defined here because the
# overlays are the primary consumer; systems.game imports them back for
# the simulation code that also branches on a scene's mood.

# Outdoor scenes -- everywhere the player is walking under sky. A soft
# always-on player-centred vignette darkens the world edges here so the
# world never feels safe between buildings. Mistlands runs its own
# (heavier) vignette via _draw_mistlands_haze and is intentionally NOT
# in this set so the two don't stack.
OUTDOOR_SCENES = {"our_house_area", "village", "forest_path",
                  "void_boss", "graveyard", "diner_gas_station",
                  "country_lane", "cornfield_maze",
                  "gravel_road_north", "river_crossing"}
# Safe interiors (the Inn): heavy overlays short-circuit so the refuge
# reads clean. Dim-safe (the cellar) keeps the flashlight cone but
# suppresses the dread / apex washes.
SAFE_SCENES = {"bedroom", "house", "kid_house", "son_room"}
DIM_SAFE_SCENES = {"basement"}
# Dark scenes -- underground / interior cult sites where the flashlight
# matters; without it the screen dims to a small clear circle.
DARK_SCENES = {"basement", "dark", "depths_antechamber", "depths_hall",
               "depths_procession", "depths_stair", "depths_threshing",
               "haunted_house", "symbol_portal_room", "threshold",
               "well_bottom", "well_passage"}
# Creepy scenes -- the stillness heartbeat ramps and the kid trailer
# can appear while the player stands still here.
CREEPY_SCENES = {"basement", "haunted_house", "mistlands",
                 "symbol_portal_room", "void_boss", "well_bottom",
                 "well_passage"}
# Cap on combined full-screen darkness so stacked washes never go opaque.
MAX_FULLSCREEN_DARK = 204


class GameRenderMixin:
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

    def _build_vignette_levels(self):
        """Four vignette surfaces at decreasing inner_r (the clear
        hole). Higher level = tighter hole = more encroachment.
        Floors raised from the prior pass -- locked-in stillness
        no longer blots the player out. Even level 3 keeps a
        ~2-tile clear radius so the player can read where they
        are while the haze closes in."""
        size = max(SCREEN_W, SCREEN_H) * 2
        surfaces = []
        # inner_r values for stillness levels 0..3 (widest -> tightest)
        for inner_r in (160, 120, 90, 70):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            outer_r = size // 2
            steps = 60
            for i in range(steps):
                ratio = i / (steps - 1)
                r = int(outer_r - ratio * (outer_r - inner_r))
                alpha = int(230 * (1.0 - ratio))
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
            surfaces.append(surf)
        return surfaces

    def _draw_outdoor_vignette(self):
        """Soft, always-on player-centred vignette for OUTDOOR_SCENES.
        Wider clear hole and lower peak alpha than the mistlands
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
        level = 1 if self.pursuer_proximity > 0.55 else 0
        surf = self._outdoor_vignette_surf[level]
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))

    def _build_outdoor_vignette(self):
        """Two outdoor vignette surfaces: wide hole (early game) and
        tightened hole (late game). Tuned so the player can read
        ~3-4 tiles in every direction comfortably; corners still
        press in but the cone of vision is wide enough to
        navigate. Late-game vignette tightens the hole and
        deepens the corner alpha as proximity climbs."""
        size = max(SCREEN_W, SCREEN_H) * 2
        surfaces = []
        # (inner_r, peak_alpha). 260 ~= 8-tile clear radius early;
        # 210 ~= 6.5-tile clear radius late. Peak alphas (130/165)
        # let the outer dark read as dim-but-readable rather than
        # opaque -- crucial for the post-stack visibility budget.
        for inner_r, peak in ((260, 130), (210, 165)):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            outer_r = size // 2
            steps = 60
            for i in range(steps):
                ratio = i / (steps - 1)
                r = int(outer_r - ratio * (outer_r - inner_r))
                alpha = int(peak * (1.0 - ratio))
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), r)
            surfaces.append(surf)
        return surfaces

    def _draw_dusk_tint(self):
        """Proximity-driven colour tint applied across the whole screen
        for outdoor scenes. As Pursuer proximity climbs, the world
        shifts from neutral toward an oppressive blue-grey/red dusk.
        Cheap: a single SRCALPHA blit per frame. Skipped indoors
        (interiors run their own lighting through scene music)."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in OUTDOOR_SCENES:
            return
        p = self.pursuer_proximity
        if p < 0.20:
            return
        # Tint colour interpolates from a cool dusk-blue at mid
        # proximity toward a sickly red at near-closure. The high-
        # end target is C_BLOOD so the dusk + apex palette stay in
        # the same red family instead of clashing primaries.
        t = min(1.0, (p - 0.20) / 0.75)
        r = int(20 + t * (C_BLOOD[0] - 20))
        g = int(20 + t * (C_BLOOD[1] - 20))
        b = int(40 + t * (C_BLOOD[2] - 40))
        alpha = int(40 + t * 80)   # 40 .. 120
        tint = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        tint.fill((r, g, b, alpha))
        self.screen.blit(tint, (0, 0))

    def _draw_mistlands_haze(self):
        """Atmospheric overlay. Mistlands and alter_room always run the
        outdoor haze + vignette. EVERY OTHER SCENE also runs the
        outdoor haze + vignette while the player is carrying the
        orb -- the orb's presence is hostile, the world dims around
        it."""
        if self.scene is None:
            return
        key = self.scene.key
        # Safe / dim-safe interiors break the orb-haze. Walking
        # back to the Inn (or the cellar) with the orb is meant
        # to feel like a refuge from the hostile dim, not a
        # continuation of it.
        if key in SAFE_SCENES or key in DIM_SAFE_SCENES:
            return
        holds_orb = (self.player is not None
                     and self.player.inventory.has("orb"))
        if key in ("mistlands", "alter_room") or holds_orb:
            self._draw_haze(170, (40, 40, 50, 80), 14, 24, 0.3, 30)
            self._draw_vignette()

    def _draw_child_trailer(self):
        """Render a small kid sprite ~2 tiles BEHIND the player (in
        the direction opposite their facing). Only fires in
        CREEPY_SCENES. If the player rotates to face the trailer
        (i.e. turns around), it disappears for 3 seconds, so the
        player can never actually look at it head-on.

        World-space draw, so the trailer is at a believable physical
        offset rather than a fixed screen offset."""
        if self.scene is None or self.scene.key not in CREEPY_SCENES:
            return
        now = pygame.time.get_ticks() / 1000.0
        if now < self._trailer_hide_until:
            return
        fx, fy = self.player.facing
        # Player's "behind" direction is opposite their facing. Place
        # the trailer two tiles behind, slightly offset.
        bx = self.player.x - fx * (TILE * 2.2)
        by = self.player.y - fy * (TILE * 2.2)
        # World-to-screen
        sx = int(bx - self.cam_x)
        sy = int(by - self.cam_y)
        if sx < -32 or sx > SCREEN_W + 32 or sy < -32 or sy > SCREEN_H + 32:
            return
        # Detect "looking at" the trailer: if the player's facing dot
        # the trailer-direction is positive, they're rotating toward
        # it. (We compute trailer-direction = bx-px, by-py = -fx*..,
        # and `dot(facing, trailer_dir) = -1` means facing away.)
        # We only hide when the player turns to face it -- player's
        # facing roughly aligns with the trailer's direction-from-
        # player. If the player walks backwards (facing toward the
        # trailer), it should hide.
        # Simpler heuristic: the trailer is always BEHIND, so it's
        # always anti-aligned with facing. If the player's last move
        # direction is anti-parallel (player walked backwards toward
        # it) -- skip detection complexity, just hide on any direction
        # change toward the trailer's tile.
        # Render: a static pale-skin small kid silhouette, no facing.
        draw_npc_sprite(self.screen, sx, sy, "kid", (0, -1))
        # Add a faint dim overlay so it doesn't read as a real NPC.
        dim = pygame.Surface((30, 36), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 60))
        self.screen.blit(dim, (sx - 15, sy - 24))

    def _draw_giant_eye(self):
        """A massive eye fades in over the haze for ~2.5 seconds at
        random rare intervals (every 30-90s while in mistlands or
        alter_room). Pupil tracks the player. Fades out without
        comment. The player either sees it or convinces themselves
        they didn't. The Visitors are watching from above the haze."""
        if self.scene is None or self.scene.key not in (
                "mistlands", "alter_room"):
            self._giant_eye_t = -1.0
            self._giant_eye_phase = 0.0
            return
        # Schedule next appearance
        if self._giant_eye_t < 0:
            self._giant_eye_t = random.uniform(20.0, 50.0)
            self._giant_eye_phase = 0.0
            return
        if self._giant_eye_phase > 0:
            # Currently visible -- count down phase, fade in/out.
            self._giant_eye_phase -= 1.0 / 60.0
            if self._giant_eye_phase <= 0:
                self._giant_eye_phase = 0.0
                self._giant_eye_t = random.uniform(30.0, 90.0)
                return
            self._render_giant_eye(self._giant_eye_phase)
        else:
            self._giant_eye_t -= 1.0 / 60.0
            if self._giant_eye_t <= 0:
                # Trigger appearance
                self._giant_eye_phase = 2.5
                # Pick a screen quadrant for placement (random each fire)
                self._giant_eye_pos = (
                    random.randint(SCREEN_W // 4, SCREEN_W * 3 // 4),
                    random.randint(SCREEN_H // 4, SCREEN_H // 2),
                )

    def _render_giant_eye(self, phase):
        """Draw the giant eye at self._giant_eye_pos with alpha
        ramping in and out across the 2.5s phase. The pupil rotates
        toward the player on screen."""
        # Fade: 0 -> max_alpha at phase=2.0 (i.e. first 0.5s), hold,
        # then fade out in the last 0.5s.
        if phase > 2.0:
            ratio = (2.5 - phase) / 0.5
        elif phase < 0.5:
            ratio = phase / 0.5
        else:
            ratio = 1.0
        alpha = max(0, min(180, int(180 * ratio)))
        if alpha <= 4:
            return
        ex, ey = self._giant_eye_pos
        sclera_r = 110
        pupil_r = 38
        # Pupil offset toward the player's screen position
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        dx = psx - ex
        dy = psy - ey
        d = math.hypot(dx, dy) or 1.0
        travel = 50
        ox = int((dx / d) * travel)
        oy = int((dy / d) * travel)
        # Build the eye on a translucent surface so we can apply
        # the fade alpha cleanly.
        layer = pygame.Surface((sclera_r * 2 + 12, sclera_r * 2 + 12),
                               pygame.SRCALPHA)
        cx, cy = sclera_r + 6, sclera_r + 6
        pygame.draw.circle(layer, (220, 215, 200, alpha),
                           (cx, cy), sclera_r)
        pygame.draw.circle(layer, (40, 30, 30, alpha),
                           (cx, cy), sclera_r, 2)
        pygame.draw.circle(layer, (60, 30, 80, alpha),
                           (cx + ox, cy + oy), pupil_r)
        pygame.draw.circle(layer, (10, 10, 14, alpha),
                           (cx + ox, cy + oy), pupil_r - 6)
        pygame.draw.circle(layer, (240, 240, 250, alpha),
                           (cx + ox - 8, cy + oy - 8), 4)
        self.screen.blit(layer, (ex - cx, ey - cy))

    def _draw_dread_ring(self):
        """Tightening dark vignette around the player as the dread
        aperture closes. The interior stays clear so the player can
        see themselves and a small radius around them; everything
        else dims to black. No figure overlay -- the King in Yellow
        approaches as a real patrol entity, not a ring of copies."""
        if self.scene is None or self.player is None:
            return
        if self.scene.key not in DARK_SCENES:
            return
        # Safe / dim-safe interiors: no encroaching ring. Basement
        # is dark enough that the flashlight cone alone reads as
        # the gating mechanic; the dread aperture stops here.
        if (self.scene.key in SAFE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        a = self.dread_aperture
        if a >= 0.99:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        radius = int(28 + a * 232)
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        outer_alpha = int(220 * (1.0 - a))
        vignette.fill((0, 0, 0, outer_alpha))
        for r_step in range(8):
            r = max(4, radius + 18 - r_step * 4)
            pygame.draw.circle(vignette, (0, 0, 0, 0),
                               (psx, psy), r)
        self.screen.blit(vignette, (0, 0))

    def _draw_yk_vignette(self):
        if not getattr(self, "_yk_present", False):
            return
        # Safe / dim-safe scenes break the YK vignette. If the
        # avatar somehow crosses into the Inn or cellar, it should
        # not paint the room.
        if self.scene is not None and (
                self.scene.key in SAFE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        period = 2.4
        t_in = period - getattr(self, "_yk_tone_t", 0.0)
        ramp = max(0.0, min(1.0, t_in / period))
        env = (1.0 - ramp) ** 1.6
        max_alpha = 130
        alpha = self._claim_dark(int(max_alpha * env))
        if alpha <= 2:
            return
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        vignette = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, alpha))
        clear_r = int(120 + 80 * (1.0 - env))
        for r_step in range(10):
            r = max(20, clear_r + 30 - r_step * 6)
            pygame.draw.circle(vignette, (0, 0, 0, 0),
                               (psx, psy), r)
        self.screen.blit(vignette, (0, 0))

    def _draw_apex_overlay(self):
        """Apex-tier rendering: when Pursuer proximity hits >= 0.95,
        the world goes wrong. Heavy red wash across the whole screen
        (interiors and exteriors alike, unlike _draw_dusk_tint which
        only touches OUTDOOR_SCENES); the screen edges crush in
        with a hard black vignette so the player's view narrows;
        the overlay pulses on a slow sine so the dread reads as
        active, not static. Cheap: two SRCALPHA blits per frame.
        Always runs above the dusk tint so the apex state is
        visually distinct from regular high-proximity unease."""
        if self.scene is None or self.player is None:
            return
        if self.pursuer_proximity < 0.95:
            return
        # Safe / dim-safe interiors break the apex wash. The Inn is
        # the refuge. Standing inside it lifts the apex pressure --
        # only stepping out re-engages it. Reads as a deliberate
        # sanctuary mechanic rather than a hole in the horror.
        if (self.scene.key in SAFE_SCENES
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

    def _claim_dark(self, requested):
        """Reserve a slice of the per-frame full-screen darkness
        budget. Returns the alpha the caller is allowed to use
        (0..requested). Increments the running total so the next
        caller sees less budget. Reset to 0 at the top of the
        overlay block. Vignettes (radial, clear at player) do NOT
        participate -- only whole-screen black washes."""
        avail = max(0, MAX_FULLSCREEN_DARK - self._overlay_dark_used)
        used = min(requested, avail)
        self._overlay_dark_used += used
        return used

    def _draw_visibility_dip(self):
        """Black wash over the screen scaled to _visibility_dip_t.
        Decays linearly over ~1.2s. Used by watcher-banish and
        eye-scatter events to give the player a brief moment of
        'I can't see' after a horror beat -- the lit-up moment is
        followed by a stumble."""
        t = self._visibility_dip_t
        if t <= 0:
            return
        # Safe / dim-safe scenes don't dip. The Inn (and the
        # cellar) is the room you walked back into to recover --
        # it should not be dipping on you.
        if (self.scene is not None
                and (self.scene.key in SAFE_SCENES
                     or self.scene.key in DIM_SAFE_SCENES)):
            return
        ratio = min(1.0, t / 1.2)
        alpha = self._claim_dark(int(180 * ratio))
        if alpha <= 4:
            return
        layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        layer.fill((0, 0, 0, alpha))
        self.screen.blit(layer, (0, 0))

    def _draw_apex_silhouette(self):
        """A held black silhouette in the centre of the screen for the
        ~110ms after closure arms. Tall human shape, no detail. Drawn
        on top of every other overlay so the player can't miss it --
        but the duration is short enough that they cannot be sure
        they did not imagine it. Fires once per closure-arm event;
        a second arm in the same session is only possible if the
        timer was reset (it is not under normal play)."""
        if self._apex_silhouette_t <= 0:
            return
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        # Tall figure: ~2 tiles wide x ~3.5 tiles tall. No face,
        # no shading, no animation -- just a hole in the wash.
        w = 56
        h = 116
        pygame.draw.ellipse(self.screen, (2, 2, 4),
                            (cx - 18, cy - h // 2, 36, 38))
        pygame.draw.rect(self.screen, (2, 2, 4),
                         (cx - w // 2, cy - h // 2 + 28, w, h - 28))
        # Slight asymmetry on the lower edge -- shoulders, not a
        # rectangle. Mirrors a body the player did not consent to
        # see clearly.
        pygame.draw.polygon(self.screen, (2, 2, 4), [
            (cx - w // 2 - 6, cy - h // 2 + 36),
            (cx - w // 2,     cy - h // 2 + 28),
            (cx - w // 2,     cy - h // 2 + 60),
        ])
        pygame.draw.polygon(self.screen, (2, 2, 4), [
            (cx + w // 2 + 6, cy - h // 2 + 36),
            (cx + w // 2,     cy - h // 2 + 28),
            (cx + w // 2,     cy - h // 2 + 60),
        ])

    def _draw_flashlight(self):
        """When the player carries the flashlight AND has it toggled
        on AND has battery, dark scenes get a bright cone in the
        facing direction. Off / dead-battery / no-flashlight all
        fall back to a heavy darkness overlay with only a small
        clear circle around the player.

        'Dark' is two cases: any scene in DARK_SCENES (interiors
        always dark), OR an OUTDOOR_SCENES scene at dusk/night
        phase. This means the flashlight is useful at night
        anywhere outside, not just in the basement -- previously
        the cone never drew outside DARK_SCENES, so players who
        toggled the light outdoors saw no effect."""
        if self.scene is None or self.player is None:
            return
        phase = self._effective_phase()
        is_outdoor_dark = (self.scene.key in OUTDOOR_SCENES
                           and phase in ("dusk", "night"))
        if self.scene.key not in DARK_SCENES and not is_outdoor_dark:
            return
        has_light = (self.player.inventory.has("flashlight")
                     and self.player.flashlight_on
                     and self.player.battery_charge > 0)
        # Build a dark overlay with a clear cone for the flashlight, or
        # a small clear circle for unlit baseline. Outdoor-dusk uses
        # a softer ceiling than full interior dark -- moonlight, not
        # cellar.
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if is_outdoor_dark and self.scene.key not in DARK_SCENES:
            base_alpha = 130 if has_light else 160
        else:
            base_alpha = 200 if not has_light else 170
        overlay.fill((0, 0, 0, base_alpha))
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        if has_light:
            # Cone of light in the facing direction. We carve a clear
            # area by blitting BLEND_RGBA_SUB with progressively
            # smaller circles along the cone.
            fx, fy = self.player.facing
            # Anchor near the player's chest; project the cone forward
            for step in range(8):
                d = step * 22
                cx = psx + int(fx * d)
                cy = psy + int(fy * d) - 4
                r = max(8, 56 - step * 5)
                a = max(40, 220 - step * 22)
                pygame.draw.circle(overlay, (0, 0, 0, 0),
                                   (cx, cy), r)
                # Soft halo around the cone interior
                pygame.draw.circle(overlay, (0, 0, 0, max(0, base_alpha - a)),
                                   (cx, cy), r + 8, 4)
        else:
            # Baseline: tiny clear circle right around the player.
            pygame.draw.circle(overlay, (0, 0, 0, 0),
                               (psx, psy), 22)
        self.screen.blit(overlay, (0, 0))

    def _draw_pursuer_glimpse(self):
        """At very high Pursuer proximity, a tall_shadow silhouette
        renders for a single frame at the screen edge -- the Pursuer
        briefly visible in peripheral vision. Held for ~80ms then
        gone. Schedule fires only when proximity > 0.85 and a scene
        transition recently completed (an exhausted moment when the
        player just walked into a new room). Tracks `_glimpse_t` -- a
        countdown that's set on transition exit."""
        if self.scene is None or self.player is None:
            return
        if self.pursuer_proximity < 0.85:
            return
        if self._glimpse_t <= 0:
            return
        # Render the tall_shadow at the chosen screen edge for the
        # remaining frames.
        from rendering.sprites import draw_npc_sprite
        draw_npc_sprite(self.screen,
                        self._glimpse_pos[0], self._glimpse_pos[1],
                        "tall_shadow", (0, 1))
        self._glimpse_t -= 1.0 / 60.0

    def _draw_haze(self, base_alpha, fog_rgba, fog_n, drift_x, sway_amp,
                   sway_y_amt):
        """Reusable haze helper: a flat black tint at `base_alpha` plus
        `fog_n` drifting translucent SQUARE patches tinted `fog_rgba`.
        Used by the mistlands overlay with different parameters."""
        if base_alpha:
            dim = pygame.Surface((SCREEN_W, SCREEN_H))
            dim.fill((0, 0, 0))
            dim.set_alpha(base_alpha)
            self.screen.blit(dim, (0, 0))
        t = pygame.time.get_ticks() / 1000.0
        size = 160
        for i in range(fog_n):
            fx = ((i * 137 + int(t * drift_x + i * 50))
                  % (SCREEN_W + 240) - 120)
            fy = ((i * 73) % SCREEN_H
                  + int(math.sin(t * sway_amp + i * 0.7) * sway_y_amt))
            fog = pygame.Surface((size, size), pygame.SRCALPHA)
            fog.fill(fog_rgba)
            self.screen.blit(fog, (fx, fy))

    def _draw_subliminal(self):
        """Once in roughly 2000 frames, render a single-frame King
        in Yellow figure or hooded cultist silhouette in the player's
        peripheral. No SFX, no log entry, no follow-up. Players will
        think they imagined it. Suppressed during transitions and
        modals so it doesn't fight any active fade or dialog draw."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        if random.random() >= 1 / 2000:
            return
        kind = random.choice(("yellow_king", "cultist"))
        # Pick a screen position near the edge but not behind the HUD
        # bar. Avoid the immediate area around the player so it lands
        # in peripheral vision rather than centered.
        psx = int(self.player.x - self.cam_x)
        psy = int(self.player.y - self.cam_y)
        for _ in range(8):
            sx = random.randint(40, SCREEN_W - 40)
            sy = random.randint(40, SCREEN_H - 80)
            if math.hypot(sx - psx, sy - psy) > 140:
                draw_npc_sprite(self.screen, sx, sy, kind, (0, 1))
                return

    def _draw_watchers(self):
        """Render each active watcher in world space. Suppressed
        during transitions / dialog modals so the figure doesn't
        sit over a black fade."""
        if (self.dialog.active or self.inv_ui.open or self.notebook_ui.open
                or self.text_input.active
                or self.state != "playing"):
            return
        for w in self._watchers:
            sx = int(w["x"] - self.cam_x)
            sy = int(w["y"] - self.cam_y)
            if sx < -32 or sx > SCREEN_W + 32:
                continue
            if sy < -48 or sy > SCREEN_H + 32:
                continue
            draw_npc_sprite(self.screen, sx, sy, "watcher", (0, 1),
                            gaze=w.get("looked_at", False))
            w["seen"] = True

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
