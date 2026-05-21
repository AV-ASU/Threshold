"""Atmosphere render overlays extracted from systems.game.

GameRenderMixin holds presentation-only draw methods that operate on
Game instance state (self.*). They are mixed into Game rather than
rewritten as standalone functions so the split stays behaviour-
preserving; the goal is only to keep systems/game.py focused on
simulation instead of pixel-pushing. Further overlay families
(haze/eye, flashlight, watchers, dread) can move here the same way.
"""
import pygame
from constants import SCREEN_W, SCREEN_H, C_BLOOD

# Outdoor scenes -- everywhere the player is walking under sky.
# A soft always-on player-centred vignette darkens the world edges
# in these scenes so the world never feels safe between buildings.
# Mistlands runs its own (heavier) vignette via _draw_mistlands_haze
# and is intentionally NOT in this set so the two don't stack.
OUTDOOR_SCENES = {"our_house_area", "village", "forest_path",
                  "void_boss", "graveyard", "diner_gas_station",
                  "country_lane", "cornfield_maze",
                  "gravel_road_north", "river_crossing"}


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
