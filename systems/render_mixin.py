"""THRESHOLD rendering -- the draw layer, extracted from systems/game.py.

draw_world (the world->screen compositor: depth-sorted solids, blind-spot
sight gating, overlays) plus the vignette/dark/haze/apex overlays, the HUD,
interact prompt, notices, title/pause/settings screens, and the death card.
Moved verbatim into a RenderMixin -- call order is unchanged (draw_world still
invokes self._draw_hud() etc. in place). Scene-specific draw helpers stay
local imports inside the methods. No behavior change; verified byte-identical
via tools/capture_world.py. Tuning + colours live in systems.config/constants.
"""
import math
import random

import pygame

from constants import (TILE, SCREEN_W, SCREEN_H, RENDER_SCALE,
                       C_BG, C_BLACK, C_BLOOD, C_GOLD, C_WHITE)
from systems.items import ITEM_DEFS
from rendering.sprites import (draw_player_sprite, draw_npc_sprite,
                               draw_npc_corpse,
                               draw_axe_swing, draw_axe_held,
                               draw_revolver_held, draw_gun_fire,
                               draw_king_death, view_from_facing, KING_UNFOLD)
from rendering.king_unfold import draw_unfold_catch
from rendering.moth import draw_moth
from rendering.transform import draw_vessel_bloom
from systems.config import *        # noqa: F401,F403

# The "?" tell card, pre-rendered once per alpha bucket (8 buckets) --
# a fresh SRCALPHA surface + three vector draws per suspicious cultist
# per frame was pure GC churn at exactly the moment frame pacing matters.
_SUS_TELL_CACHE = {}


def _sus_tell_card(bucket):
    card = _SUS_TELL_CACHE.get(bucket)
    if card is None:
        a = int(110 + 130 * (bucket / 7.0))
        col = (222, 196, 120, a)
        card = pygame.Surface((12, 16), pygame.SRCALPHA)
        pygame.draw.arc(card, col, (2, 1, 8, 8),
                        -math.pi * 0.7, math.pi * 0.95, 2)
        pygame.draw.line(card, col, (6, 8), (6, 10), 2)
        pygame.draw.circle(card, col, (6, 14), 1)
        _SUS_TELL_CACHE[bucket] = card
    return card


def _draw_sus_tell(surf, x, y, actor):
    """The rising "?" tell (DESIGN.md §12 Pillar 1): drawn over a
    SCOUTING cultist whose suspicion is climbing -- the player's read on
    the "have they spotted me?" window. Procedural (no font glyph; the
    HUD stays diegetic-minimal): a pale-gold curl + dot that brightens
    and lifts as suspicion fills. Scout-only on purpose: a locked chase
    has its own sting, and a SEARCHING hunter wearing a full "?" would
    tell the player they are merely suspected one beat after the lock
    announced the opposite."""
    sus = getattr(actor, "_suspicion", 0.0)
    if sus < SUS_NOTICE or getattr(actor, "_cult_state", "") != "scout":
        return
    bucket = min(7, int(min(1.0, sus) * 8))
    lift = int(4 * min(1.0, sus))
    surf.blit(_sus_tell_card(bucket), (int(x) - 6, int(y) - 16 - lift))


# Solid-prop card cache (see _draw_solid_prop). Static props rendered once per
# (prop, camera angle) and blitted thereafter; FIFO-capped so roaming the town
# doesn't grow it without bound.
_PROP_CARD_CACHE = {}
_PROP_CARD_ORDER = []
_PROP_CARD_CAP = 1400
# Radially-symmetric props whose card is yaw-invariant (measured 0% pixel
# change across a full turn): grass/spires/cylinders read the same from every
# azimuth. These key WITHOUT yaw, so they build once and survive camera turns
# instead of rebuilding every frame the view rotates. Asymmetric props (signs,
# vehicles, the well, the flock) keep yaw in the key and reshape correctly.
_YAW_INVARIANT_PROPS = frozenset({
    "grass_tuft", "tall_grass", "pillar", "creepy_tree", "candle", "steeple",
})
# The yaw-invariant props get their OWN cache. Eviction is FIFO by insertion,
# and the yaw-keyed props churn a fresh entry per bucket as the camera turns;
# sharing one cache, that churn would evict the stable yaw-invariant entries
# (inserted once, so oldest in the queue) and force them to rebuild every few
# frames. A separate cache keeps the static cards out of that line of fire.
_PROP_STATIC_CACHE = {}
_PROP_STATIC_ORDER = []
_PROP_STATIC_CAP = 2000

# The VISIBLE light-pool twin of Scene._LIGHT_KINDS (which carries only the
# mechanical stealth radius). One row per light-emitting decoration kind, the
# pool the fixture punches into a DARK scene's gloom:
#   (visible_radius, color, peak_alpha, screen_z_lift,
#    flicker_amp, flicker_speed, ring_base, ring_step, ring_n)
# _draw_dark iterates EVERY scene emitter through this table -- not just
# wall_torch -- so any real fixture (a cult brazier, a candle, a town yard
# light) lights the dark it stands in. This is the shared light logic
# (DESIGN.md §6): one table drives the surface (if it ever darkens) and the
# underground, with no per-scene special-casing. wall_torch keeps its exact
# legacy numbers, so torch-only rooms stay byte-identical.
FIXTURE_POOLS = {
    #                radius  color            peak  lift  amp   spd   rb  rs  rn
    "wall_torch":   (118,  (255, 168, 78),   82,   12,   0.18, 7.0,  26, 12, 7),
    "brazier":      (110,  (255, 150, 56),   80,   6,    0.16, 6.0,  24, 12, 7),
    "burn_barrel":  (100,  (255, 150, 56),   74,   8,    0.16, 6.0,  22, 11, 7),
    "camp_fire":    (112,  (255, 158, 60),   80,   2,    0.18, 5.0,  24, 12, 7),
    "lantern":      (72,   (255, 176, 84),   64,   6,    0.10, 3.0,  16,  8, 7),
    "candle":       (46,   (255, 178, 92),   50,   2,    0.14, 9.0,  10,  5, 7),
    "yard_light":   (104,  (202, 224, 255),  70,   2,    0.05, 2.0,  22, 11, 7),
    "generator":    (52,   (255, 212, 152),  46,   4,    0.08, 5.0,  12,  6, 7),
}


class RenderMixin:
    def _draw_boot_screen(self):
        """A single quiet frame shown while Audio() synthesises the sound
        library at startup (a few seconds of blocking DSP). Keeps the window
        from reading as hung/black on launch. Drawn once, before the audio
        build -- no clock, no animation, just the title word and a hint."""
        self.screen.fill((4, 3, 7))
        word = self.fonts["title"].render("THRESHOLD", True, (60, 56, 70))
        self.screen.blit(word, (SCREEN_W // 2 - word.get_width() // 2,
                                SCREEN_H // 2 - word.get_height() // 2 - 10))
        sub = self.fonts["sm"].render("waking the dark .", True, (40, 38, 50))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2,
                               SCREEN_H // 2 + 26))
        pygame.display.flip()
        # Pump the event queue once so the OS marks the window as responsive
        # rather than "Not Responding" during the synth that follows.
        pygame.event.pump()

    # ---- TITLE ----
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
        title_font = self.fonts["serif_huge"]
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
            txt = self.fonts["serif_lg"].render(opt, True, color)
            tx2 = SCREEN_W // 2 - txt.get_width() // 2
            ty2 = 360 + i * 46
            if i == self.title_choice:
                # A single small bracket on the left only -- asymmetric,
                # never resolves to a neat selector.
                marker = self.fonts["serif_lg"].render("[", True, (220, 218, 226))
                self.screen.blit(marker, (tx2 - 24, ty2))
            self.screen.blit(txt, (tx2, ty2))
        hint = self.fonts["serif_sm"].render(
            "arrow keys . enter . F11", True, (60, 58, 68))
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                SCREEN_H - 28))

    def _draw_ashfall(self):
        """Blit the ash motes as one soft pale-yellow wash over the world."""
        parts = self._ashfall_parts
        if not parts:
            return
        layer = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        cr, cg, cb = ASHFALL_COLOR
        for p in parts:
            sz = p["sz"]
            layer.fill((cr, cg, cb, p["a"]),
                       (int(p["x"]), int(p["y"]), sz, sz))
        self.screen.blit(layer, (0, 0))

    def _draw_brimley_haze(self):
        """Atmospheric overlay. Brimley and alter_room always run the
        outdoor haze + vignette. EVERY OTHER SCENE also runs the
        outdoor haze + vignette while the player is carrying the Pallid
        Mask -- His face is the hostile object now (DESIGN.md §4: the Mask
        is the temptation and it draws Him), so the world dims around it."""
        if self.scene is None:
            return
        key = self.scene.key
        # Safe / dim-safe interiors break the Mask-haze. Walking back to the
        # Inn (or the cellar) with the Mask is meant to feel like a refuge
        # from the hostile dim, not a continuation of it.
        if key in SAFE_SCENES or key in DIM_SAFE_SCENES:
            return
        holds_mask = (self.player is not None
                     and self.player.inventory.has("pallid_mask"))
        if key == "brimley":
            # Daytime town: a LIGHT atmospheric haze, not the oppressive dim.
            # The "too dark" read was a flat black tint stacked on the
            # blind-spot fog, the film grade, AND the grade's own vignette.
            # Now that the sight fog is shadow-cast (off-cone reads as a shaped
            # shadow, not a flat gray wash), the flat tint can come almost all
            # the way down so the LIT cone reads as full day. Keep the drifting
            # fog patches + the encroaching vignette for mood.
            self._draw_haze(26, (40, 40, 50, 70), 14, 24, 0.3, 30)
            self._draw_vignette()
        elif holds_mask:
            # The Mask's presence is HOSTILE -- His face draws Him, the world
            # dims hard around it. This heavier dim is intentional.
            self._draw_haze(170, (40, 40, 50, 80), 14, 24, 0.3, 30)
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
        psx, psy = self._player_screen()
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))

    def _build_vignette_levels(self):
        """Four vignette surfaces at decreasing inner_r (the clear
        hole). Higher level = tighter hole = more encroachment.
        Floors raised from the prior pass -- locked-in stillness
        no longer blots the player out. Even level 3 keeps a
        ~2-tile clear radius so the player can read where they
        are while the haze closes in."""
        size = max(self.screen.get_size()) * 2
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
        psx, psy = self._player_screen()
        size = surf.get_width()
        self.screen.blit(surf, (psx - size // 2, psy - size // 2))

    def _build_outdoor_vignette(self):
        """Two outdoor vignette surfaces: wide hole (early game) and
        tightened hole (late game). Tuned so the player can read
        ~3-4 tiles in every direction comfortably; corners still
        press in but the cone of vision is wide enough to
        navigate. Late-game vignette tightens the hole and
        deepens the corner alpha as proximity climbs."""
        size = max(self.screen.get_size()) * 2
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

    def _draw_apex_overlay(self):
        """Max-visibility rendering, in TWO tiers keyed to WHO has you
        (2026-07 playtest fix: the apex wash was too intense when only
        cultists were chasing -- a human threat wearing the cosmic
        overlay).

        - **The King is the threat** (his roam is armed, or his body is
          in your room): the full APEX tier -- a heavy dried-blood red
          wash + a hard edge-crush tunnel vignette. The world is wrong
          and He is looking. Unchanged from before.
        - **Only the cult has you** (below the gate, no King body): a
          milder TOWN tier -- no red wash, just a cold desaturated
          tighten at the edges. Reads as "seen, cornered, the town has
          turned its head" rather than "the void is eating you." The
          cult is human; it does not get His colour.

        Fires at visibility >= 0.95; both pulse on a slow sine so the
        dread reads as active. Cheap: <=2 SRCALPHA blits per frame."""
        if self.scene is None or self.player is None:
            return
        if self.visibility < 0.95:
            return
        # Safe / dim-safe interiors break the wash entirely. The Inn is
        # the refuge; stepping inside lifts the pressure. Reads as a
        # deliberate sanctuary rather than a hole in the horror.
        if (self.scene.key in KING_FREE_SCENES
                or self.scene.key in DIM_SAFE_SCENES):
            return
        t = pygame.time.get_ticks() / 1000.0
        pulse = 0.85 + 0.15 * math.sin(t * 1.4)
        psx, psy = self._player_screen()
        king_threat = (self._roam_king["armed"] or self._king is not None)
        if king_threat:
            # APEX tier: the red wash + the hard tunnel crush (His gaze).
            wash_a = self._claim_dark(int(70 * pulse))
            wash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            wash.fill((C_BLOOD[0], C_BLOOD[1], C_BLOOD[2], wash_a))
            self.screen.blit(wash, (0, 0))
            edge_a = self._claim_dark(int(180 * pulse))
            edge = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            edge.fill((0, 0, 0, edge_a))
            clear_r = int(110 + 6 * math.sin(t * 1.4))
            pygame.draw.circle(edge, (0, 0, 0, 0), (psx, psy), clear_r)
            self.screen.blit(edge, (0, 0))
            return
        # TOWN tier: no red, a gentler cold tighten. A thin desaturated
        # slate wash + a soft, WIDER edge vignette (a bigger clear disc,
        # a lighter ring) so it reads as pressure, not suffocation.
        wash_a = self._claim_dark(int(24 * pulse))
        wash = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        wash.fill((30, 32, 40, wash_a))
        self.screen.blit(wash, (0, 0))
        edge_a = self._claim_dark(int(96 * pulse))
        edge = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        edge.fill((6, 7, 10, edge_a))
        clear_r = int(168 + 6 * math.sin(t * 1.4))
        pygame.draw.circle(edge, (0, 0, 0, 0), (psx, psy), clear_r)
        self.screen.blit(edge, (0, 0))

    def _draw_sight_fog(self):
        """Gray fog over the blind spot, with the clear region SHADOW-CAST
        against solids: each ray across the cone stops at the first wall it
        hits, so you see your sightline cut off where vision is interrupted
        (crisp tile-edged shadows behind walls). This makes the fog HONEST --
        it now matches the actor gate (visible_factor -> los_clear), which
        already hides things behind walls. The cone is keyed to look.aim
        (half-angle SIGHT_HALF, out to SIGHT_RANGE) with a clear near-bubble.
        Engaged whenever the player is present and playing."""
        if not (self.player is not None and self.state == "playing"):
            return
        from rendering.sight import (SIGHT_HALF, SIGHT_RANGE, SIGHT_NEAR,
                                     SIGHT_ANG_FEATHER, LOS_STEP)
        aim = self.look.aim
        # The fog layer is a pure function of the player's ground point, the
        # aim heading, the camera pose, and the scene. All of those hold still
        # whenever the player is settled (standing, reading, in dialogue) --
        # the common case -- so cache the built layer and re-blit it until one
        # of them moves. The raymarch + polygon rebuild only runs on change.
        # Positions quantize to 3px buckets and the aim to ~0.6 degrees: the
        # fog is a soft gray wash, so re-blitting a sub-bucket-stale layer is
        # imperceptible, and walking frames get cache hits too.
        cam = self.camera
        fkey = (self.screen.get_size(),
                int(self.player.x / 3), int(self.player.y / 3),
                int(aim * 100), int(cam.cam_x / 3), int(cam.cam_y / 3),
                round(cam.yaw, 3), round(cam.scale, 3))
        fc = self._sight_fog_cache
        # Identity-held scene ref (not id(): a freed scene's id can recycle).
        if (fc.get("key") == fkey and fc.get("scene") is self.scene
                and fc.get("surf") is not None):
            self.screen.blit(fc["surf"], (0, 0))
            return
        fog = fc.get("surf")
        if fog is None or fog.get_size() != self.screen.get_size():
            fog = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        fog.fill((58, 60, 66, SIGHT_FOG_ALPHA))         # cold, thin gray
        # The sight math is ground-plane WORLD space; the apex is the player's
        # ground point. Cast a fan of rays across the cone, marching each one
        # out until it crosses a solid (Scene.blocks_sight, the same predicate
        # the gate uses) or reaches SIGHT_RANGE, then project the clipped tip.
        px, py = self.player.x, self.player.y
        blocks = self.scene.blocks_sight
        gx, gy = self.camera.project(px, py)
        half = SIGHT_HALF + SIGHT_ANG_FEATHER
        steps = 48          # enough rays for clean, crisp wall shadows
        pts = [(gx, gy)]
        for i in range(steps + 1):
            a = aim - half + 2 * half * (i / steps)
            ca, sa = math.cos(a), math.sin(a)
            dist = SIGHT_RANGE
            d = SIGHT_NEAR
            while d < SIGHT_RANGE:
                if blocks(px + ca * d, py + sa * d):
                    dist = d            # sightline interrupted here
                    break
                d += LOS_STEP
            pts.append(self.camera.project(px + ca * dist, py + sa * dist))
        # pygame.draw writes the colour's alpha directly, so drawing (…,0)
        # punches the visibility polygon + bubbles fully transparent.
        pygame.draw.polygon(fog, (0, 0, 0, 0), pts)
        near_r = max(10, int(SIGHT_NEAR * self.camera.scale))
        pygame.draw.circle(fog, (0, 0, 0, 0), (gx, gy), near_r)
        # keep the player's own body clear (it's never sight-gated)
        psx, psy = self._player_screen()
        pygame.draw.circle(fog, (0, 0, 0, 0), (psx, psy), 26)
        fc["key"] = fkey
        fc["surf"] = fog
        fc["scene"] = self.scene
        self.screen.blit(fog, (0, 0))

    def _draw_bridge_dust(self):
        """A faint dust-fall from the deck overhead while the town crosses
        the bridge above the under-bridge hide (TODO #5). Screen-space,
        keyed to _bridge_dust (set by _tick_bridge_knocks) -- a few pale
        motes sifting down the middle of the frame, so the knocks have a
        visible partner. Pure dressing; nothing gameplay reads it."""
        d = getattr(self, "_bridge_dust", 0.0)
        if d <= 0.02:
            return
        t = pygame.time.get_ticks() / 1000.0
        w, h = self.screen.get_width(), self.screen.get_height()
        rng = random.Random(7)
        for _ in range(int(26 * d)):
            bx = rng.randint(int(w * 0.28), int(w * 0.72))
            fall = (t * 60 + rng.randint(0, 400)) % (h * 0.5)
            yy = int(h * 0.16 + fall)
            a = int(120 * d * (0.4 + 0.6 * rng.random()))
            self.screen.fill((150, 140, 120),
                             (bx, yy, 1, 2), special_flags=0)
            pygame.draw.circle(self.screen, (120, 112, 96), (bx, yy), 1)

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
        psx, psy = self._player_screen()
        # 60% wash (153 alpha) routed through the darkness cap so
        # hide stacked with apex/dip never blots the whole screen.
        wash_a = self._claim_dark(153)
        layer = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
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
        psx, psy = self._player_screen()
        lit = self._flashlight_lit()
        # Diegetic wall-torch light: each torch punches its own warm, flickering
        # pool into the gloom, so a torch-lit room reads without the flashlight.
        tnow = pygame.time.get_ticks() / 1000.0
        # Every light-emitting fixture in the room punches its own pool into
        # the gloom (FIXTURE_POOLS -- the shared light logic, DESIGN.md §6):
        # not just wall_torch, but any brazier / candle / lantern / yard light
        # / generator the scene stands. wall_torch keeps its exact legacy
        # numbers, so a torch-only room is byte-identical.
        fixtures = []
        for d in getattr(self.scene, "decorations", []):
            spec = FIXTURE_POOLS.get(getattr(d, "kind", None))
            if spec is None:
                continue
            fx, fy = self.camera.project(d.x, d.y)
            fl = (1.0 - spec[4]) + spec[4] * math.sin(tnow * spec[5] + d.x * 0.25)
            fixtures.append((int(fx), int(fy) - spec[3], spec, fl))
        # Build the beam cone geometry once (apex -> left -> tip -> right).
        # The far points are laid out in WORLD space around the player's feet
        # and projected through the camera, so the cone lies FLAT on the ground
        # -- under tilt it foreshortens with the floor instead of shooting off
        # the screen into the void. (At pitch 0, scale 1.0, this projects to the
        # same screen pixels the old screen-space math produced.)
        cone = None
        if lit:
            fx, fy = getattr(self.player, "facing", (0, 1)) or (0, 1)
            flen = math.hypot(fx, fy) or 1.0
            ang = math.atan2(fy / flen, fx / flen)
            reach, spread = 300, math.radians(30)
            pwx, pwy = self.player.x, self.player.y

            def _far(a):
                return self.camera.project(pwx + reach * math.cos(a),
                                           pwy + reach * math.sin(a))
            tip = _far(ang)
            left = _far(ang - spread)
            right = _far(ang + spread)
            cone = [(psx, psy), left, tip, right]
        if lit:
            # A warm held-light pool at the feet -- not eyes adjusting.
            _light_pool(self.screen, psx, psy, 96, (240, 226, 165), 72)
        else:
            _light_pool(self.screen, psx, psy, 112, (118, 124, 150), 96)
        for fx, fy, spec, fl in fixtures:
            _light_pool(self.screen, fx, fy, int(spec[0] * fl), spec[1],
                        int(spec[2] * fl))
        gloom = 130 if self.scene.key in CULT_DARK_SCENES else 100
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, gloom))
        rings = [(30 + i * 14, int(gloom * i / 8)) for i in range(8)]
        for rr, aa in sorted(rings, key=lambda p: -p[0]):
            pygame.draw.circle(overlay, (0, 0, 0, aa), (psx, psy), rr)
        for fx, fy, spec, fl in fixtures:
            rb, rs, rn = spec[6], spec[7], spec[8]
            frings = [(int((rb + i * rs) * fl), int(gloom * i / rn))
                      for i in range(rn)]
            for rr, aa in sorted(frings, key=lambda p: -p[0]):
                pygame.draw.circle(overlay, (0, 0, 0, aa), (fx, fy), rr)
        if cone:
            # Carve the beam clear of the gloom (alpha 0 inside the cone).
            pygame.draw.polygon(overlay, (0, 0, 0, 0), cone)
        self.screen.blit(overlay, (0, 0))
        if cone:
            # A faint warm wash inside the cone sells it as a light source.
            beam = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(beam, (250, 232, 170, 26), cone)
            self.screen.blit(beam, (0, 0))

    def _draw_haze(self, base_alpha, fog_rgba, fog_n, drift_x, sway_amp,
                   sway_y_amt):
        """Reusable haze helper: a flat black tint at `base_alpha` plus
        `fog_n` drifting translucent SQUARE patches tinted `fog_rgba`.
        Used by the brimley overlay with different parameters."""
        cache = self._haze_cache
        if base_alpha:
            dim = cache.get(("dim", self.screen.get_size()))
            if dim is None:
                dim = pygame.Surface(self.screen.get_size())
                dim.fill((0, 0, 0))
                cache[("dim", self.screen.get_size())] = dim
            dim.set_alpha(base_alpha)
            self.screen.blit(dim, (0, 0))
        t = pygame.time.get_ticks() / 1000.0
        size = 160
        _sw, _sh = self.screen.get_size()
        # One translucent patch per tint, built once -- allocating + filling
        # fog_n fresh SRCALPHA squares every frame was ~1.5ms of pure waste.
        fog = cache.get(("patch", fog_rgba))
        if fog is None:
            fog = pygame.Surface((size, size), pygame.SRCALPHA)
            fog.fill(fog_rgba)
            cache[("patch", fog_rgba)] = fog
        for i in range(fog_n):
            fx = ((i * 137 + int(t * drift_x + i * 50))
                  % (_sw + 240) - 120)
            fy = ((i * 73) % _sh
                  + int(math.sin(t * sway_amp + i * 0.7) * sway_y_amt))
            self.screen.blit(fog, (fx, fy))

    def _refresh_fold_charge(self, face):
        """Pull a state-driven fold's formation charge from the scene hook
        (Scene.fold_charge_fn(game, char) -> 0..1) before it draws. Scenes
        without the hook keep the default fully-formed pane."""
        fn = getattr(self.scene, "fold_charge_fn", None)
        if fn is not None:
            face["charge"] = fn(self, face.get("char"))

    def _draw_folds(self):
        """Composite every seen fold in the current scene -- a one-sided peek
        into its target, only visible when the player faces into it. Pitch-0
        path only; under tilt each fold is depth-sorted into the unified list
        so it interleaves with the player, NPCs, and walls (see draw_world)."""
        folds = getattr(self, "_folds", None)
        if not folds or self.player is None:
            return
        from rendering.folds import draw_fold
        t = pygame.time.get_ticks() / 1000.0
        for face in folds:
            self._refresh_fold_charge(face)
            draw_fold(self.screen, face, self.cam_x, self.cam_y,
                      self.player, t, self.camera)

    def _draw_one_fold(self, face):
        """Draw a single seen fold (used by the tilted depth-sort list)."""
        from rendering.folds import draw_fold
        t = pygame.time.get_ticks() / 1000.0
        self._refresh_fold_charge(face)
        draw_fold(self.screen, face, self.cam_x, self.cam_y,
                  self.player, t, self.camera)

    def _draw_portal(self):
        """Composite the King's torn rift (the roaming-King portal), if open."""
        p = getattr(self, "_portal", None)
        if not p:
            return
        from rendering.portal import draw_portal
        t = pygame.time.get_ticks() / 1000.0
        draw_portal(self.screen, p, self.cam_x, self.cam_y, self.camera, t)

    def _draw_idle_king(self):
        """The idle state: the King at full bloom far up THE road, indifferent.
        A receding horizon render (set by _tick_idle_king), never a scene entity
        -- you can't reach him. Drawn SOLID (not alpha-blended -- translucency
        washed out his gloss + maws) so he reads as the King, just distant; the
        night vignette is what keeps him from popping like a poster.

        Three grounding layers seat him in the 3D world (2026-07 pass):
        the ROAD MIRAGE (the air around him refracts -- horizontal screen
        strips displaced like heat-shimmer, the road bending around what
        stands on it), his softened UNLIGHT, and the WRONG-WAY SHADOW (a
        long stain smearing DOWN the road toward the player, against
        every light in the scene). His eversion churns at half tempo --
        indifferent, not hunting -- and refreshes every couple of frames
        so the warp reads as slow weather, not a stepped stutter."""
        ik = getattr(self, "_idle_king", None)
        if not ik or self.player is None:
            return
        from rendering.king_unfold import draw_king_unfold, eat_light_at
        sx, sy = self.camera.project(ik[0], ik[1])
        h = self.screen.get_height()
        w = self.screen.get_width()
        # Only when he's actually up the road in front of you: facing north he is
        # ahead at the vanishing point (glimpsed); turn away and he projects
        # off-screen and isn't drawn.
        if sy < -120 or sy > h + 120 or sx < -160 or sx > w + 160:
            return
        sy -= int(TILT_LIFT.get("yellow_king", TILT_ACTOR_STAND)
                  * math.sin(self.camera.pitch))
        sx, sy = int(sx), int(sy)
        t = pygame.time.get_ticks() / 1000.0
        # 1. The road mirage: displace thin horizontal strips of the
        # already-drawn scene around him, stronger toward his base --
        # the air over the tarmac refuses to hold still where he
        # stands. Drawn FIRST so his body and shadow stay crisp.
        band_w, band_h = 170, 100
        bx, by = sx - band_w // 2, sy - 4
        srect = self.screen.get_rect()
        for i in range(0, band_h, 3):
            off = int(round(math.sin(t * 2.6 + i * 0.33)
                            * (1.0 + 1.8 * (i / band_h))))
            if off == 0:
                continue
            r = pygame.Rect(bx, by + i, band_w, 3).clip(srect)
            if r.w <= 0 or r.h <= 0:
                continue
            strip = self.screen.subsurface(r).copy()
            self.screen.blit(strip, (r.x + off, r.y))
        # 2. The light-eating shadow, softened at idle (the full hunt
        # disc read as a hard black hole at the vanishing point). Live
        # every frame so the world keeps pulsing under him.
        eat_light_at(self.screen, sx, sy, IDLE_KING_SCALE * IDLE_KING_EAT,
                     IDLE_KING_THREAT * IDLE_KING_EAT)
        # 3. The BODY: a full UNFOLDING rendered to a small card, reused
        # for IDLE_KING_CARD_REFRESH frames, churning at half tempo.
        # Position still updates every frame (cheap blit).
        R = int(IDLE_KING_SCALE * 2.6) + 8
        card = getattr(self, "_idle_king_card", None)
        last = getattr(self, "_idle_king_card_frame", -999)
        if (card is None or card.get_width() != R * 2
                or self.frame_count - last >= IDLE_KING_CARD_REFRESH):
            card = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
            lean = (math.sin(t * 0.8) * 0.14, -0.18)
            draw_king_unfold(card, R, R, t * IDLE_KING_TEMPO,
                             threat=IDLE_KING_THREAT,
                             scale=IDLE_KING_SCALE, to_player=(0.0, 1.0),
                             birth=1.0, lean=lean, eat_light=False)
            card = card.convert_alpha()        # fast blits on a real display
            self._idle_king_card = card
            self._idle_king_card_frame = self.frame_count
        # 4. The wrong-way shadow: a tapering stain smeared down the
        # road TOWARD the player (he only exists on this north road, so
        # screen-down IS toward you), swaying slowly. No light in the
        # scene casts it.
        L = 260
        shs = pygame.Surface((110, L), pygame.SRCALPHA)
        for i in range(L):
            k = i / L
            wd = int(52 * (1.0 - 0.5 * k))
            a = int(95 * (1.0 - k) ** 1.5)
            wob = int(math.sin(t * 1.7 + i * 0.045) * 4 * k)
            pygame.draw.rect(shs, (4, 3, 8, a),
                             (55 - wd // 2 + wob, i, wd, 1))
        self.screen.blit(shs, (sx - 55, sy + int(R * 0.30)))
        self.screen.blit(card, (sx - R, sy - R))

    def _draw_death_screen(self):
        """Render the active death card over everything. King = the
        furnace of masks (sprites.draw_king_death), wordless;
        cultist = a stark CAPTURED card over a near-black wash."""
        if self._death_kind == "king":
            if KING_UNFOLD:
                # the Unfolding takes you DOWN THE THROAT (mouth iris -> tunnel
                # of teeth -> gold furnace); _death_t 0..3 maps to the catch 0..1.
                draw_unfold_catch(self.screen, min(1.0, self._death_t / 3.0))
            else:
                draw_king_death(self.screen, self._death_t)
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

    # ---- Draw ----
    def _skybox_kind(self):
        """The oblique-camera surround for the current scene (DESIGN.md §10).
        A scene may pin `skybox_kind` ("overcast"/"void") explicitly;
        otherwise every SURFACE scene gets the sallow daytime `overcast` sky and
        everything else (interiors, underground) keeps the near-black `void` so
        the horror keeps its dark. The surface set is `SEAMLESS_WORLD_SCENES`
        (OUTDOOR_SCENES + Brimley + the surface hidden-folds) -- using
        OUTDOOR_SCENES alone wrongly handed Brimley and the fold tableaux the
        near-black void, which is what made daytime Brimley read as night."""
        kind = getattr(self.scene, "skybox_kind", None)
        if kind:
            return kind
        return "overcast" if self.scene.key in SEAMLESS_WORLD_SCENES else "void"

    def _player_screen(self):
        """The player's projected SCREEN position, lifted to the sprite centre
        under tilt (sin pitch) so the player-centred overlays -- vignettes,
        flashlight cone apex, apex/hide discs -- align with the drawn body, not
        the ground point ~15px below it (DESIGN.md §10). At pitch 0 the lift
        is 0, so the flat view's overlays do not move a pixel."""
        psx, psy = self.camera.project(self.player.x, self.player.y)
        psy -= int(TILT_ACTOR_STAND * math.sin(self.camera.pitch))
        return psx, psy

    def _draw_solid_prop(self, d, ox=0.0, oy=0.0):
        """Draw one solid furniture/prop by blitting a cached card. Solid props
        (headstones, signs, the flagpole, lamps, furniture boxes) are STATIC --
        none animate -- and their shape relative to the ground point depends
        only on the camera angle, never on where the camera is panned to. So
        render the 3D prop once per (prop, angle) into a card and blit it at the
        projected base, exactly like the trees. The wrap offset (ox, oy) only
        moves the base, so every wrap-clone shares one card."""
        cam = self.camera
        bx, by = cam.project(d.x + ox, d.y + oy)
        # Yaw-invariant props build once (no yaw in the key) and live in their
        # own cache so the yaw-keyed props' per-turn churn can't evict them.
        if d.kind in _YAW_INVARIANT_PROPS:
            key = (id(d), round(cam.pitch, 2), round(cam.scale, 2))
            cache, order, cap = (_PROP_STATIC_CACHE, _PROP_STATIC_ORDER,
                                 _PROP_STATIC_CAP)
        else:
            # Yaw bucketed at 0.04 rad (like the wall cards): a
            # continuous head-turn used to rebuild every yaw-keyed prop
            # every frame; ~1px of in-bucket shape error is invisible
            # mid-swing.
            key = (id(d), int(cam.yaw / 0.04), round(cam.pitch, 2),
                   round(cam.scale, 2))
            cache, order, cap = (_PROP_CARD_CACHE, _PROP_CARD_ORDER,
                                 _PROP_CARD_CAP)
        entry = cache.get(key)
        if entry is None:
            entry = self._build_prop_card(d)
            cache[key] = entry
            order.append(key)
            if len(order) > cap:
                cache.pop(order.pop(0), None)
        card, ax, ay = entry
        if card is not None:
            self.screen.blit(card, (bx - ax, by - ay))

    def _invalidate_prop_card(self, deco):
        """Drop any cached solid-prop card for `deco` so its next draw rebuilds
        (the cards key on id(deco), so a prop whose look changed in place -- e.g.
        the desk once its revolver is taken -- would otherwise show a stale
        card until the scene reloads)."""
        did = id(deco)
        for cache, order in ((_PROP_CARD_CACHE, _PROP_CARD_ORDER),
                             (_PROP_STATIC_CACHE, _PROP_STATIC_ORDER)):
            for k in [k for k in cache if k[0] == did]:
                cache.pop(k, None)
                try:
                    order.remove(k)
                except ValueError:
                    pass

    def _build_prop_card(self, d):
        """Cache-miss path: render one solid prop to a tight SRCALPHA card via a
        throwaway camera at the same angle whose origin pins the prop's ground
        point to a fixed spot. Returns (surface, anchor_x, anchor_y)."""
        from rendering.camera import Camera
        from rendering.furniture import draw_furniture_solid
        from rendering.props import draw_prop_solid
        cam = self.camera
        # Scratch the prop is drawn into before the tight crop. get_bounding_rect
        # scans the WHOLE scratch every rebuild, so an oversized one is pure
        # cost. Sized from the measured worst-case extents across every scene
        # (steeple up=64, hanging_figure down=26, flock half-width=85) at the
        # full-tilt zoom, scaled to the transition's max zoom (scale->1.0 during
        # tilt-in, ~1.39x) and padded ~25%. Anything that fits is cropped to a
        # byte-identical card; this just stops scanning ~120k empty pixels.
        PADX, PADY, BASE = 150, 120, 55
        tmp = pygame.Surface((PADX * 2, PADY + BASE), pygame.SRCALPHA)
        anchor = (PADX, PADY)
        tcam = Camera(cam_x=d.x, cam_y=d.y, pitch=cam.pitch, yaw=cam.yaw,
                      scale=cam.scale, origin=anchor)
        if not draw_furniture_solid(tmp, tcam, d):
            draw_prop_solid(tmp, tcam, d)
        rect = tmp.get_bounding_rect()
        if rect.width == 0 or rect.height == 0:
            return (None, 0, 0)
        card = tmp.subsurface(rect).copy().convert_alpha()
        return (card, anchor[0] - rect.x, anchor[1] - rect.y)

    def _draw_fps_overlay(self):
        """Dev perf readout (F1): FPS, frame ms, and the live scene key, drawn
        top-left over everything. Diagnostic only -- used to measure render
        cost (e.g. the wrapped Brimley town) before/after tuning."""
        fps = self.clock.get_fps()
        ms = self._last_dt * 1000.0
        scene_key = getattr(self.scene, "key", "?") if self.scene else "?"
        lines = [f"{fps:4.1f} fps   {ms:5.1f} ms", f"scene: {scene_key}"]
        font = self.fonts["mono_sm"]
        pad = 4
        surfs = [font.render(t, True, (210, 230, 140)) for t in lines]
        w = max(s.get_width() for s in surfs) + pad * 2
        h = sum(s.get_height() for s in surfs) + pad * 2
        bg = pygame.Surface((w, h))
        bg.set_alpha(150)
        bg.fill((0, 0, 0))
        self.screen.blit(bg, (6, 6))
        y = 6 + pad
        for s in surfs:
            self.screen.blit(s, (6 + pad, y))
            y += s.get_height()

    def draw_world(self):
        if self.state == "opening":
            self._draw_opening()
            return
        # Internal render scale: draw the world layer (geometry + atmosphere +
        # grade) to a smaller buffer, then upscale once to the window before the
        # crisp HUD. The camera is scaled to match so framing is identical. Off
        # (s == 1.0) -> the world draws straight to the window, unchanged.
        self._win = self.screen
        _rs = getattr(self, "_render_scale", RENDER_SCALE)
        _s = (_rs if (_rs < 0.999 and self.scene and self._tilt_on()) else 1.0)
        if _s < 1.0:
            rw, rh = max(1, round(SCREEN_W * _s)), max(1, round(SCREEN_H * _s))
            if self._world_buf is None or self._world_buf.get_size() != (rw, rh):
                self._world_buf = pygame.Surface((rw, rh)).convert()
            self.screen = self._world_buf
        self._render_s = _s
        self.screen.fill(C_BG)
        if not self.scene:
            if _s < 1.0:
                self._win.fill(C_BG)
                self.screen = self._win
            return
        # Re-sync the projection to the live camera offset for this frame.
        # Pivot about the BUFFER centre (the view centre world point) so any
        # pitch/yaw rotates about the middle of the view, not the corner. At
        # pitch 0 + scale 1 this is arithmetically identical to the legacy view:
        #   project(x) = (SCREEN/2) + (x - (cam + SCREEN/2)) = x - cam.
        _rw, _rh = self.screen.get_size()
        self.camera.origin = (_rw // 2, _rh // 2)
        self.camera.cam_x = self.cam_x + SCREEN_W // 2
        self.camera.cam_y = self.cam_y + SCREEN_H // 2
        if _s < 1.0:
            self.camera.scale *= _s
        # Phase 4 blind-spot vision (DESIGN.md §10). Under tilt, gate WHAT
        # IS DRAWN to a forward sight cone keyed to the look heading + walls
        # (rendering/sight.py). The world keeps simulating off-camera (the
        # update path is untouched) -- only RENDERING is gated, so unseen
        # actors / items / rot simply aren't shown and re-hide when the head
        # turns away (the SCP-173 dread). The King is exempt (a relentless
        # apex you must be able to track) and the player is never gated. At
        # pitch 0 `_sight` stays None -> every alpha is 255 and the frame is
        # byte-identical to the shipping top-down view.
        _sight = None
        if self._tilt_on() and self.player:
            from rendering.sight import visible_factor, SIGHT_RENDER_STEP
            _spx, _spy, _shead = self.player.x, self.player.y, self.look.aim
            _blk = self.scene.blocks_sight
            # Ground-crest occlusion feeds the draw gate too, so a figure behind
            # a hill re-hides exactly like one behind a wall. None (no
            # heightfield) keeps the pure cone+wall gate -- byte-identical.
            _gz = (self.scene.ground_z
                   if getattr(self.scene, "_ground_hf", None) is not None
                   else None)
            def _sight(wx, wy):
                return visible_factor(_spx, _spy, _shead, wx, wy, _blk,
                                      step=SIGHT_RENDER_STEP, ground=_gz)
        # Hand the see-through doors the SAME sight gate so a threat in the room
        # beyond an opening is culled by the player's cone, like the open world
        # (DESIGN.md §7; the through-view showed the far room ungated before). Only
        # under tilt (the aperture is a tilt feature); cleared otherwise.
        self.scene._door_actor_sight = _sight
        from rendering.solids import draw_with_alpha

        def _vis_alpha(wx, wy, exempt=False, king=False):
            """0..255 alpha to draw a world thing at (wx, wy) under the sight
            gate, or None to skip it (fully in the blind spot). 255 when the
            gate is off (pitch 0) or the thing is exempt (pickups). The KING
            is never fully hidden (a trackable apex), but in the blind-spot
            fog he reads as a DIM SMEAR, not a crisp full-opacity figure:
            seeing him plainly in the fog killed the dread (play-notes). He
            resolves to solid as you look AT him (f high) or as he CLOSES
            (the near term), so trackability holds."""
            if _sight is None:
                return 255
            if king:
                f = _sight(wx, wy)
                if f >= 0.99:
                    return 255
                d = math.hypot(wx - self.player.x, wy - self.player.y)
                near = max(0.0, 1.0 - d / KING_SEE_RANGE)
                floor = int(55 + 175 * near * near)
                return max(floor, int(255 * f))
            if exempt:
                return 255
            f = _sight(wx, wy)
            if f <= 0.03:
                return None
            return 255 if f >= 0.99 else int(255 * f)

        _tilt = self.camera.pitch > 0.02
        _tilt_walls = _tilt_solid_decos = _tilt_wall_decos = None
        if _tilt:
            # DEBUG oblique view (DESIGN.md §10): skybox fills the void,
            # the floor warps to the tilted plane. The upright occluders -- wall
            # tiles + solid props -- are RETURNED (not drawn here) so they can be
            # depth-interleaved with the actors below and faded per-actor
            # (Phase 5). Actors already project through self.camera so they stand
            # on this floor.
            from scenes.base import draw_terrain_tilted
            from rendering.skybox import draw_skybox
            draw_skybox(self.screen, (0, 0, *self.screen.get_size()),
                        yaw=self.camera.yaw, kind=self._skybox_kind(),
                        horizon_frac=0.40)
            (_tilt_walls, _tilt_solid_decos, _tilt_wall_decos,
             _tilt_neighbor_solids) = draw_terrain_tilted(
                self.screen, self.scene, self.camera, sight=_sight)
            # Ground swell (DESIGN.md §10): a projected floor mesh over the
            # flat raster where a scene authored hills, so the terrain rolls and
            # actors sit on it. No-op if no heightfield / flat camera.
            if getattr(self.scene, "_ground_hf", None) is not None:
                from rendering.heightfield import draw_ground_mesh
                draw_ground_mesh(self.screen, self.camera, self.scene)
        else:
            self.scene.draw(self.screen, self.cam_x, self.cam_y, self.camera)
        self._draw_idle_king()
        # The unified scene-actor draw list (DESIGN.md §10). Each entry is
        # (depth, draw_callable). At pitch 0 it stays in INSERTION ORDER (==the
        # legacy item->npc->enemy->projectile->player order) and is drawn
        # straight through, so the flat view is byte-identical. Under tilt the
        # walls + solid props are appended and the whole list is sorted by
        # Camera.depth so actors, props, and walls interleave correctly. The
        # focus list collects every VISIBLE actor's ground footprint so an
        # occluding wall fades for whichever of them it actually covers.
        _entries = []
        _focus = []
        def _emit(depth, fn):
            _entries.append((depth, fn))
        _tilt_items = self._tilt_on()
        for it in self.scene.items:
            # Items are pickups, not threats: exempt from the blind-spot sight
            # cull so they always READ as existing in the world (gated + tiny,
            # they were easy to miss). Drawn as a clear floating gem.
            a = _vis_alpha(it["x"], it["y"], exempt=True)
            if a is None:
                continue
            sx, sy = self.camera.project(it["x"], it["y"])
            t = pygame.time.get_ticks() / 200.0
            bob = int(math.sin(t + (it["x"] + it["y"]) * 0.01))
            color = self._item_color(it["key"])

            def _draw_item(s, sx=sx, sy=sy, bob=bob, color=color,
                           tilt=_tilt_items):
                if tilt:
                    # A small ground shadow so the pickup sits ON the floor, then
                    # a plain icon just above it -- no glow halo. Items are exempt
                    # from the sight cull (drawn always), so they read in the
                    # world without needing to be big.
                    sh = pygame.Surface((12, 6), pygame.SRCALPHA)
                    pygame.draw.ellipse(sh, (0, 0, 0, 90), sh.get_rect())
                    s.blit(sh, (sx - 6, sy - 2))
                    iy = sy - 5 + bob
                    pygame.draw.rect(s, color, (sx - 4, iy - 4, 8, 8))
                    pygame.draw.rect(s, C_BLACK, (sx - 4, iy - 4, 8, 8), 1)
                    pygame.draw.rect(s, tuple(min(255, c + 60) for c in color),
                                     (sx - 3, iy - 3, 2, 2))
                else:
                    pygame.draw.rect(s, color, (sx - 4, sy - 4 + bob, 8, 8))
                    pygame.draw.rect(s, C_BLACK, (sx - 4, sy - 4 + bob, 8, 8), 1)
            _emit(self.camera.depth(it["x"], it["y"]),
                  lambda a=a, fn=_draw_item: draw_with_alpha(self.screen, a, fn))
            # A pickup is a "focus" too: an occluding wall/prop fades for it the
            # same way it does for an actor (below), so a gem tucked behind a
            # near wall or a tall prop still reads through instead of vanishing
            # under the tilt. Low height -- it sits on the floor.
            if _tilt_items:
                _focus.append((it["x"], it["y"], 14))
        # Pick at most one NPC to "blink" this frame -- their eye dots
        # will skip drawing for a single frame. Only fires while the
        # player is standing still, and only rarely. The villagers
        # don't blink, except, very rarely, one does.
        blink_idx = -1
        if self.stillness_t > 1.5 and random.random() < 1 / 300:
            human_kinds = ("townswoman", "toby", "old_townsman",
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
        _offsets = [(0, 0)]
        if sc.wrap_x:
            _ww = sc.w * TILE
            _offsets += [(-_ww, 0), (_ww, 0)]
        if sc.wrap_y:
            _wh = sc.h * TILE
            _offsets += [(0, -_wh), (0, _wh)]
        if sc.wrap_x and sc.wrap_y:
            _offsets += [(-_ww, -_wh), (-_ww, _wh), (_ww, -_wh), (_ww, _wh)]

        # Under tilt a sprite's centre rises so its feet sit on the floor
        # point; 0 at top-down so the shipping view is untouched.
        actor_lift = int(TILT_ACTOR_STAND * math.sin(self.camera.pitch))

        def _on_screen(sx, sy):
            return -64 <= sx <= SCREEN_W + 64 and -64 <= sy <= SCREEN_H + 64

        for i, npc in enumerate(self.scene.npcs):
            # A homebody currently inside their door: not drawn at all.
            if getattr(npc, "_inside", False):
                continue
            # A corpse: draw it prone in its blood and skip all the
            # living-NPC logic (morph, blink, king-threat, gaze). A fresh
            # kill (mold=0) -- corpses don't persist across loads anymore, so
            # there's no growing rot stage to track (NARRATIVE §4 / DESIGN.md §1).
            if not getattr(npc, "alive", True):
                for ox, oy in _offsets:
                    sx, sy = self.camera.project(npc.x + ox, npc.y + oy)
                    if not _on_screen(sx, sy):
                        continue
                    a = _vis_alpha(npc.x + ox, npc.y + oy)
                    if a is None:
                        continue
                    _emit(self.camera.depth(npc.x + ox, npc.y + oy),
                          lambda a=a, sx=sx, sy=sy, npc=npc:
                          draw_with_alpha(self.screen, a,
                                          lambda s: draw_npc_corpse(
                                              s, sx, sy, npc.sprite_kind,
                                              seed=getattr(npc, 'sprite_seed', 0), mold=0),
                                          rect=(sx - 90, sy - 90, 180, 170)))
                continue
            m = getattr(npc, "morph", 0.0)
            king_threat = None
            # The King is a SINGLE apex. In a toroidal scene (Brimley) the actor
            # wrap-clones below would draw him TWICE near a seam (you saw two by
            # the well). Collapse him to the ONE wrap image nearest the player and
            # compute his screen-space tells + proximity at that image.
            king_offset = (0.0, 0.0)
            if (npc.sprite_kind == "yellow_king" and self.player
                    and len(_offsets) > 1):
                king_offset = min(_offsets, key=lambda o:
                                  (npc.x + o[0] - self.player.x) ** 2
                                  + (npc.y + o[1] - self.player.y) ** 2)
            kx, ky = npc.x + king_offset[0], npc.y + king_offset[1]
            if npc.sprite_kind == "yellow_king" and self.player:
                d = math.hypot(kx - self.player.x, ky - self.player.y)
                span = KING_THREAT_FAR - KING_THREAT_NEAR
                # Existence is purely proximity: a far void that blooms only
                # as he closes. Visibility is NOT mixed in here -- it drives the
                # hunt + the portal (_tick_king_roam), not his on-screen bloom,
                # and reads too narrow a band near apex to gauge existence by.
                # The 0.15 floor keeps him a faint watching void, never fully
                # gone, until he nears.
                king_threat = max(0.15, min(1.0, 1.0 - (d - KING_THREAT_NEAR) / span))
            # The Unfolding's locomotion + perspective tells (screen-space, so
            # they read right under any camera yaw/pitch). to_player aims its
            # reaching limbs + eyes; lean everts the mass forward along its
            # heading scaled by the smoothed travel magnitude; scale_mul looms
            # him larger as he closes the view-depth gap (tilt only).
            king_to_player = None
            king_lean = None
            king_scale_mul = 1.0
            if npc.sprite_kind == "yellow_king" and self.player:
                kxs, kys = self.camera.project(kx, ky)
                pxs, pys = self.camera.project(self.player.x, self.player.y)
                king_to_player = (pxs - kxs, pys - kys)
                lean_mag = getattr(npc, "_yk_lean", 0.0)
                if lean_mag > 0.01:
                    fx, fy = npc.facing
                    axs, ays = self.camera.project(kx + fx * TILE,
                                                   ky + fy * TILE)
                    ldx, ldy = axs - kxs, ays - kys
                    dl = math.hypot(ldx, ldy) or 1.0
                    king_lean = (ldx / dl * lean_mag, ldy / dl * lean_mag)
                if self._tilt_on():
                    C = KING_TILT_DEPTH_CAM
                    dz = (self.camera.depth(kx, ky)
                          - self.camera.depth(self.player.x, self.player.y))
                    dz = max(-0.45 * C, min(0.45 * C, dz))
                    f = C / (C - dz)
                    pf = max(0.0, min(1.0,
                             self.camera.pitch / math.radians(TILT_PITCH_DEG)))
                    king_scale_mul = max(KING_TILT_DEPTH_MIN,
                                         min(KING_TILT_DEPTH_MAX,
                                             1.0 + (f - 1.0) * pf))
            npc_lift = int(TILT_LIFT.get(npc.sprite_kind, TILT_ACTOR_STAND)
                           * math.sin(self.camera.pitch))
            # The King is the relentless apex -- you must be able to track
            # him, but he is a DIM SMEAR in the blind-spot fog rather than a
            # crisp full-opacity figure (play-notes; the _vis_alpha king
            # branch), resolving solid as you look at him or as he closes.
            # Everyone else obeys the blind spot outright.
            exempt = npc.sprite_kind == "yellow_king"
            # One image for the singular King; the wrap-clone set for everyone
            # else (so a townsperson near the seam still reads on both sides).
            actor_offsets = [king_offset] if exempt else _offsets
            for ox, oy in actor_offsets:
                sx, sy = self.camera.project(npc.x + ox, npc.y + oy)
                if not _on_screen(sx, sy):
                    continue
                a = _vis_alpha(npc.x + ox, npc.y + oy, king=exempt)
                if a is None:
                    continue
                # A visible standing actor is a "focus": occluding walls fade for
                # whichever of these they cover (DESIGN.md §10 per-actor
                # occlusion), so a cultist seen behind a near wall reads through.
                # Invisible interact MARKERS are exempt: they draw nothing, so
                # fading a wall for one erases real architecture for a ghost
                # (the church vestry's back wall vanished for the records
                # terminal's marker; the room read as missing a wall).
                if npc.sprite_kind != "_invisible":
                    _focus.append((npc.x + ox, npc.y + oy, 28))
                sy -= npc_lift            # stand on the floor under tilt

                # Capture EVERY per-NPC value as a default arg: this closure
                # runs later (from the depth-sorted _entries), by which point the
                # loop variables (npc, m, i, the king_* tells) have advanced to
                # the LAST npc. Binding them here freezes each NPC's own data --
                # otherwise every NPC drew as the last one in the list (and the
                # King, materialised last, turned every visible NPC into a King).
                def _draw_npc(target, sx=sx, sy=sy, npc=npc, m=m, i=i,
                              king_threat=king_threat,
                              king_to_player=king_to_player,
                              king_lean=king_lean, king_scale_mul=king_scale_mul):
                    if m > 0.0:
                        draw_vessel_bloom(target, sx, sy, npc.sprite_kind,
                                          npc.facing, m, seed=getattr(npc, 'sprite_seed', 0))
                    else:
                        # (The curse is His own gaze now; NARRATIVE §4 / DESIGN.md §1.
                        # curse_v stays 0 for all normal NPCs.)
                        curse_v = 0.0
                        # A Watcher being stared down: its eyes go dark (gaze)
                        # and it fades as the dispel timer fills, so the cure
                        # reads.
                        w_gaze = (npc.sprite_kind == "watcher"
                                  and getattr(npc, "_gaze_dispel_t", 0.0) > 0.05)
                        nview = "front"
                        if self._tilt_on():
                            nview = view_from_facing(npc.facing[0],
                                                     npc.facing[1],
                                                     self.camera.yaw)
                        draw_npc_sprite(target, sx, sy, npc.sprite_kind,
                                        npc.facing, blink=(i == blink_idx),
                                        birth=getattr(npc, "_birth", None),
                                        gait=getattr(npc, "_gait", None),
                                        threat=king_threat,
                                        seed=getattr(npc, 'sprite_seed', 0),
                                        curse=curse_v, gaze=w_gaze, view=nview,
                                        to_player=king_to_player,
                                        lean=king_lean, scale_mul=king_scale_mul,
                                        pose=getattr(npc, "pose", None),
                                        gape=getattr(npc, "_gape", 0.0))
                    # The rising "?" tell (DESIGN.md §12 Pillar 1): a
                    # cultist whose suspicion is climbing but hasn't locked
                    # shows the half-seen hesitation over its head.
                    _draw_sus_tell(target, sx, sy - 32, npc)
                _emit(self.camera.depth(npc.x + ox, npc.y + oy),
                      lambda a=a, fn=_draw_npc, sx=sx, sy=sy:
                      draw_with_alpha(self.screen, a, fn,
                                      rect=(sx - 110, sy - 160, 220, 250)))
            # THRESHOLD: NPC name labels removed. They were the
            # last RPG-tell on screen -- the player should learn
            # who an NPC is by interacting with them, not by
            # reading a tag floating over their head. Strangers
            # on the road read as STRANGERS until they speak.
        for e in self.scene.enemies:
            eview = "front"
            if self._tilt_on():
                eview = view_from_facing(e.facing[0], e.facing[1],
                                         self.camera.yaw)
            for ox, oy in _offsets:
                sx, sy = self.camera.project(e.x + ox, e.y + oy)
                if not _on_screen(sx, sy):
                    continue
                a = _vis_alpha(e.x + ox, e.y + oy)
                if a is None:
                    continue
                _focus.append((e.x + ox, e.y + oy, 28))
                # Feed e.draw an offset that lands its internal `x - cam`
                # exactly on the (lifted) projected point. At pitch 0 this is
                # arithmetically the legacy (cam_x - ox) call -> identical.
                def _draw_enemy(s, e=e, sx=sx, sy=sy, eview=eview):
                    e.draw(s, e.x - sx, e.y - (sy - actor_lift), view=eview)
                    # The rising "?" tell for a suspicious-but-not-locked
                    # underground cultist (mirrors the NPC path).
                    _draw_sus_tell(s, sx, sy - 32, e)
                _emit(self.camera.depth(e.x + ox, e.y + oy),
                      lambda a=a, sx=sx, sy=sy, fn=_draw_enemy:
                      draw_with_alpha(self.screen, a, fn,
                                      rect=(sx - 110, sy - 160, 220, 250)))
        # The Moths -- the first flying entity: a hovering billboard with
        # a slow bob, sight-gated like every other actor. A faint cold
        # smudge marks the ground point (never an honest shadow).
        for m in (getattr(self.scene, "_moths", None) or []):
            for ox, oy in _offsets:
                sx, sy = self.camera.project(m["x"] + ox, m["y"] + oy)
                if not _on_screen(sx, sy):
                    continue
                a = _vis_alpha(m["x"] + ox, m["y"] + oy)
                if a is None:
                    continue
                # hover collapses to the ground as a burnt-out moth FALLS;
                # a newly ARRIVED seeker drops in from above while it
                # fades up (the "b" ramp)
                hf = m.get("h", 1.0)
                bm = m.get("b", 1.0)
                hover = ((34 + math.sin(m["t"] * 1.7 + m["seed"]) * 5.0)
                         * hf * (1.0 + 2.2 * (1.0 - bm)))

                def _draw_moth_e(s, m=m, sx=sx, sy=sy, hover=hover):
                    gy = sy - actor_lift
                    husk = m["state"] == "husk"
                    if not husk:
                        smw = 20 + int(6 * m["glow"])
                        smudge = pygame.Surface((smw * 2, 8),
                                                pygame.SRCALPHA)
                        pygame.draw.ellipse(smudge, (8, 7, 12, 80),
                                            (0, 0, smw * 2, 8))
                        s.blit(smudge, (sx - smw, gy - 4))
                    draw_moth(s, sx, gy - hover, m["t"],
                              spread=m["spread"], glow=m["glow"],
                              seed=m["seed"],
                              flap=(1.0 if m.get("fast") else 0.2),
                              husk=husk)
                _emit(self.camera.depth(m["x"] + ox, m["y"] + oy),
                      lambda a=a * bm, sx=sx, sy=sy, fn=_draw_moth_e:
                      draw_with_alpha(self.screen, a, fn,
                                      rect=(sx - 70, sy - 180, 140, 230)))
        for p in self.scene.projectiles:
            psx, psy = self.camera.project(p.x, p.y)
            _emit(self.camera.depth(p.x, p.y),
                  lambda p=p, psx=psx, psy=psy:
                  p.draw(self.screen, p.x - psx, p.y - (psy - actor_lift)))
        # Thrown river stones (TODO #5): a tiny pebble on a cosmetic arc
        # (sine of flight progress) over its ground shadow. The player's
        # own action, so never sight-gated -- like the pickups it must
        # always READ.
        for st in (getattr(self, "_stones", None) or []):
            z = 12.0 + 30.0 * math.sin(math.pi * min(1.0, st["p"]))
            ssx, ssy = self.camera.project(st["x"], st["y"], z)
            gsx, gsy = self.camera.project(st["x"], st["y"], 0)

            def _draw_stone(ssx=ssx, ssy=ssy, gsx=gsx, gsy=gsy):
                sh = pygame.Surface((10, 4), pygame.SRCALPHA)
                pygame.draw.ellipse(sh, (8, 7, 12, 70), (0, 0, 10, 4))
                self.screen.blit(sh, (gsx - 5, gsy - actor_lift - 2))
                pygame.draw.circle(self.screen, (112, 110, 104),
                                   (int(ssx), int(ssy - actor_lift)), 2)
                pygame.draw.circle(self.screen, (60, 58, 55),
                                   (int(ssx), int(ssy - actor_lift)), 2, 1)
            _emit(self.camera.depth(st["x"], st["y"]), _draw_stone)
        if self.player:
            psx, psy = self.camera.project(self.player.x, self.player.y)
            psy -= actor_lift             # stand on the floor under tilt
            _focus.append((self.player.x, self.player.y, 30))

            def _draw_player(psx=psx, psy=psy):
                if getattr(self, "_seal_warp", None) is not None:
                    return        # SEAL live warp: he has gone through
                # The camera-relative body view, computed once: it picks the
                # sprite face AND decides whether the held weapon is occluded
                # by the torso (see _draw_weapon below). Only meaningful under
                # tilt; at pitch 0 it stays "front" so the draw order is
                # byte-identical to before.
                pview = "front"
                if self._tilt_on() and self.player.hidden is None:
                    pview = view_from_facing(self.player.facing[0],
                                             self.player.facing[1],
                                             self.camera.yaw)

                # Held weapon + its use animation. The gun and axe share one
                # slot (_active_weapon); each gets its OWN art. The gun no
                # longer borrows the axe arc: it shows a held revolver, and a
                # muzzle flash + recoil when fired. melee_swing_t drives the
                # use animation for both (set by the swing / the shot).
                def _draw_weapon():
                    wpn = self._active_weapon()
                    firing = self.player.melee_swing_t > 0
                    prog = (1.0 - (self.player.melee_swing_t / AXE_SWING_DUR)
                            if firing else 0.0)
                    # The held weapon points where you AIM. facing/melee_dir are
                    # WORLD headings; under the yawed camera, rotate them into
                    # screen space (Camera.project's yaw rotation) so the gun/axe
                    # lines up with the on-screen crosshair. The body view is
                    # already yaw-aware via view_from_facing.
                    def _sf(v):
                        fx, fy = v
                        if self._tilt_on() and self.camera.yaw:
                            c, s = math.cos(self.camera.yaw), math.sin(self.camera.yaw)
                            return (fx * c + fy * s, -fx * s + fy * c)
                        return (fx, fy)
                    if wpn == "pistol":
                        if firing:
                            draw_gun_fire(self.screen, psx, psy,
                                          _sf(self.player.melee_dir), prog)
                        else:
                            draw_revolver_held(self.screen, psx, psy,
                                               _sf(self.player.facing))
                    elif wpn == "lumber_axe":
                        if firing:
                            draw_axe_swing(self.screen, psx, psy,
                                           _sf(self.player.melee_dir), prog)
                        else:
                            draw_axe_held(self.screen, psx, psy,
                                          _sf(self.player.facing))

                # When the player faces AWAY (the "back" view) the torso should
                # hide the held weapon, so draw it BEFORE the body. Otherwise the
                # weapon reads in front of the hands, so it goes after.
                weapon_behind = (pview == "back")
                if weapon_behind:
                    _draw_weapon()

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
                                       prone=getattr(self.player, "prone", False),
                                       view=pview)
                if not weapon_behind:
                    _draw_weapon()
            _emit(self.camera.depth(self.player.x, self.player.y), _draw_player)

        # Under tilt, fold the upright occluders -- wall tiles + solid props --
        # into the same list and depth-sort EVERYTHING so actors, props, and
        # walls interleave correctly (DESIGN.md §10). A wall fades for
        # whichever VISIBLE actor it actually covers (min over the focus set),
        # so the furnished rooms' partition walls + mid-floor props no longer
        # blanket an actor standing behind them. Solid props are wrap-cloned
        # through the projection too. At pitch 0 nothing is appended and the
        # list stays in legacy insertion order -> the flat view is byte-identical.
        if _tilt:
            from scenes.base import (_TILT_WALL_RISE, _COUNTER_RISE,
                                     _COUNTER_CHARS, _tilt_tile_box)
            from rendering.occlusion import (focus_occ_data,
                                              occluder_alpha_box, _screen_span)
            _whalf = TILE * 0.5 * self.camera.scale
            _sw, _sh = self.scene.w, self.scene.h
            # Precompute each focus actor's (depth, screen box) ONCE. The fade
            # test below runs for every wall x every actor; the actor side is
            # identical across all walls, so recomputing its projection per wall
            # (the old occluder_alpha did) was pure waste in the wall-dense town.
            _focus_pre = [focus_occ_data(self.camera, fx, fy, fh)
                          for (fx, fy, fh) in _focus]
            for (tx, ty) in (_tilt_walls or []):
                wcx, wcy = tx * TILE + TILE / 2, ty * TILE + TILE / 2
                # A counter is waist-high: occlude + depth-sort at its real
                # (short) rise so an NPC standing behind it shows OVER the top
                # instead of being blanketed like a full wall.
                _wtx = tx % _sw if self.scene.wrap_x else tx
                _wty = ty % _sh if self.scene.wrap_y else ty
                _ch = (self.scene.objects[_wty][_wtx]
                       if 0 <= _wty < _sh and 0 <= _wtx < _sw else "")
                rise = _COUNTER_RISE if _ch in _COUNTER_CHARS else _TILT_WALL_RISE
                wa = 255
                if _focus_pre:
                    _od = self.camera.depth(wcx, wcy)
                    _os = _screen_span(self.camera, wcx, wcy, rise, _whalf)
                    for _pd, _ps in _focus_pre:
                        wa = min(wa, occluder_alpha_box(_od, _os, _pd, _ps))
                        if wa <= 60:
                            break
                def _wall_fn(wa=wa, tx=tx, ty=ty, wcx=wcx, wcy=wcy):
                    rect = None
                    if wa < 255:
                        # Bound the scratch composite to the tile's card area
                        # (wall/tree cards are <=180px, anchored at the ground
                        # point) so the fade costs a small blit, not a
                        # full-screen one.
                        bx, by = self.camera.project(wcx, wcy)
                        rect = (bx - 100, by - 150, 200, 215)
                    draw_with_alpha(self.screen, wa,
                                    lambda s: _tilt_tile_box(
                                        s, self.camera, self.scene, tx, ty),
                                    rect=rect)
                _emit(self.camera.depth(wcx, wcy, rise), _wall_fn)
            # Phase 2+ of neighbor strips: emit the neighbor's wall-class
            # tiles through a satellite camera (shifted by the offset so
            # neighbor world coords project at the seam). Depth-sorted in
            # host frame against the host actors, so a neighbor tree in
            # front of the player sorts correctly.
            for (n_scene, ntx, nty, hwx, hwy, sat_cam) in (
                    _tilt_neighbor_solids or []):
                _emit(self.camera.depth(hwx, hwy, _TILT_WALL_RISE),
                      lambda n_scene=n_scene, ntx=ntx, nty=nty,
                      sat_cam=sat_cam:
                      _tilt_tile_box(self.screen, sat_cam, n_scene, ntx, nty))
            # Volumetric gabled roofs over each building region (tilt only --
            # the flat view paints the top-down roof art in draw_scene_terrain).
            # Each region emits one depth entry keyed at its NEAREST eave
            # corner (see emit_tilt_roofs): the roof overhangs its own walls,
            # so it must sort after ALL of them, while anything truly nearer
            # the camera still draws over it.
            from scenes.base import (emit_tilt_roofs, emit_tilt_water_reeds,
                                     _tilt_window_half as _twh)
            _rh = _twh(self.camera)
            _rx0 = int((self.camera.cam_x - _rh) // TILE) - 1
            _ry0 = int((self.camera.cam_y - _rh) // TILE) - 1
            _rx1 = int((self.camera.cam_x + _rh) // TILE) + 1
            _ry1 = int((self.camera.cam_y + _rh) // TILE) + 1
            emit_tilt_roofs(_emit, self.scene, self.camera, self.screen,
                            _rx0, _ry0, _rx1, _ry1)
            emit_tilt_water_reeds(_emit, self.scene, self.camera, self.screen,
                                  _rx0, _ry0, _rx1, _ry1)
            # Solid props (trees, headstones, lanterns -- the standees) wrap-
            # clone like decorations and used to emit one depth entry per
            # (prop x offset) pair. Brimley has ~420 such props x 9 wrap
            # offsets = ~3800 emits/frame, almost all of them off-screen.
            # Walk the SPATIAL CHUNK INDEX (Move 2 of the perf strategy: only
            # touch chunks the visible window overlaps), then per-prop project
            # + screen-pixel cull. Brimley typically projects ~50-200 instead
            # of 3800. The scene's _deco_index_cache is built by
            # draw_terrain_tilted above; both flat solid list AND chunk map
            # are populated there.
            from scenes.base import (_DECO_CHUNK_PX, _DECO_TALL_MARGIN,
                                     _tilt_window_half)
            _SOL_MX, _SOL_MTOP, _SOL_MBOT = 100, 100, 220
            _idx = getattr(self.scene, "_deco_index_cache", None) or {}
            _solid_chunks = _idx.get("solid_chunks") or {}
            _half = _tilt_window_half(self.camera) + _DECO_TALL_MARGIN
            _vx0 = self.camera.cam_x - _half
            _vy0 = self.camera.cam_y - _half
            _vx1 = self.camera.cam_x + _half
            _vy1 = self.camera.cam_y + _half
            for ox, oy in _offsets:
                _cx0 = int((_vx0 - ox) // _DECO_CHUNK_PX)
                _cy0 = int((_vy0 - oy) // _DECO_CHUNK_PX)
                _cx1 = int((_vx1 - ox) // _DECO_CHUNK_PX) + 1
                _cy1 = int((_vy1 - oy) // _DECO_CHUNK_PX) + 1
                for _cy in range(_cy0, _cy1):
                    for _cx in range(_cx0, _cx1):
                        _bucket = _solid_chunks.get((_cx, _cy))
                        if not _bucket:
                            continue
                        for d in _bucket:
                            if getattr(d, "_no_wrap", False) and (ox or oy):
                                continue   # stays at its true spot; no wrap
                            psx, psy = self.camera.project(d.x + ox, d.y + oy)
                            if not (-_SOL_MX <= psx <= SCREEN_W + _SOL_MX
                                    and -_SOL_MTOP <= psy <= SCREEN_H + _SOL_MBOT):
                                continue
                            # Optional per-prop depth bias: a prop whose visible
                            # mass sits ABOVE a nearer occluder can key itself
                            # later (e.g. a bell-tower spire that rises out of
                            # its own church roof, which otherwise sorts after
                            # and paints over the whole tower). Defaults to 0 --
                            # every other prop is unaffected.
                            _dbias = float(getattr(d, "kwargs", {})
                                           .get("depth_bias", 0.0))
                            _emit(self.camera.depth(d.x + ox, d.y + oy) + _dbias,
                                  lambda d=d, ox=ox, oy=oy:
                                  self._draw_solid_prop(d, ox, oy))
            # Surface props seated ON furniture (a ledger, plate, lamp on a
            # desk/table): lifted to the prop height (deco kwarg `z`) and
            # depth-sorted at the SOUTH EDGE of their host tile, not their own
            # anchor -- the host furniture box's anchor can sit deeper in the
            # tile than the prop's (a plate placed near the tile's north edge
            # sorted BEHIND its own table and the table top painted over it),
            # and the south edge is the deepest any single-tile host anchor can
            # be, so the prop always lands at-or-after its host. On a tie the
            # stable sort keeps these (emitted after the solids) on top. Flat-
            # lying kinds warp onto the surface; upright kinds stand on it as a
            # lifted billboard. (Ground depth, not the lifted height: depth
            # treats higher z as farther.)
            from scenes.base import (_SURFACE_DECAL_KINDS, _FLOOR_DECAL_KINDS,
                                     _draw_floor_decal)
            from rendering.props import is_solid_prop
            from rendering.furniture import is_solid_furniture
            for d in self.scene.decorations:
                _z = float(getattr(d, "kwargs", {}).get("z", 0.0))
                if _z <= 0 and d.kind not in _SURFACE_DECAL_KINDS:
                    continue
                # Solid props (e.g. a candle/lamp now drawn as a real volume)
                # bake `z` into their own draw, so the solid pass already
                # placed them on the surface. Re-emitting here would render
                # them twice.
                if is_solid_prop(d.kind) or is_solid_furniture(d.kind):
                    continue
                _dy = (int(d.y // TILE) + 1) * TILE if _z > 0 else d.y
                if d.kind in _SURFACE_DECAL_KINDS or d.kind in _FLOOR_DECAL_KINDS:
                    _emit(self.camera.depth(d.x, _dy),
                          lambda d=d: _draw_floor_decal(self.screen, self.camera, d))
                else:
                    _emit(self.camera.depth(d.x, _dy),
                          lambda d=d, z=_z: d.draw(self.screen, 0, 0, self.camera,
                                                   mount_z=z))
            # Wall-hung decorations: lift onto the wall face (_WALL_MOUNT_Z) as
            # camera-facing billboards, depth-sorted at the lifted depth so a
            # back-wall photo sorts in FRONT of its wall box, not under it. NOT
            # sight-gated -- they sit ON a wall, and that wall blocks LOS, so
            # gating would hide every wall decoration behind its own wall. They
            # are environmental like the walls + furniture (which also draw
            # regardless of the cone); the gray fog already greys off-cone.
            from scenes.base import _WALL_MOUNT_Z, draw_wall_deco
            # +4 depth bias (depth is in world px): a card on an E/W wall ties
            # with its own wall box at yaw ~0 (same camera distance) and the
            # box painted over it; the bias keeps the card just in front of
            # its own wall while staying far below the one-tile (32) gap to
            # any real occluder.
            for d in (_tilt_wall_decos or []):
                for ox, oy in _offsets:
                    _emit(self.camera.depth(d.x + ox, d.y + oy,
                                            _WALL_MOUNT_Z) + 4.0,
                          lambda d=d, ox=ox, oy=oy: draw_wall_deco(
                              self.screen, self.camera, self.scene, d,
                              _WALL_MOUNT_Z, woff=(ox, oy)))
            # The portal + folds depth-sort with the trees/walls/actors (so a
            # tree in front of one occludes it and it occludes what is behind)
            # instead of always drawing on top -- they are real upright things
            # in the scene. Without this, hidden folds drew under the player and
            # the room peek was hidden behind whatever stood in front of it.
            if getattr(self, "_portal", None):
                _emit(self.camera.depth(self._portal["x"], self._portal["y"],
                                        _TILT_WALL_RISE),
                      lambda: self._draw_portal())
            # FOLDS: a scene can ship several direction-gated portals (the
            # grove stands the descent pane and the school pane)
            # and a naive draw runs a full target-room render for each. Cull
            # to the ones IN THE PLAYER'S SIGHT CONE -- a portal that is behind
            # you, beside you, or behind a wall isn't drawn. The canon already
            # says each fold reads as floor from any other angle, so dropping
            # off-cone ones leaves no visible gap. Combined with the canonical
            # direction-into-normal check inside draw_fold, only the rifts the
            # player is actually looking AT pay the render cost.
            for face in (getattr(self, "_folds", None) or ()):
                fx, fy = face["fold_px"]
                if _sight is not None and _sight(fx, fy) <= 0.0:
                    continue                      # outside the sight cone
                _emit(self.camera.depth(fx, fy, _TILT_WALL_RISE),
                      lambda f=face: self._draw_one_fold(f))
            _entries.sort(key=lambda e: e[0])
        # Execute the (legacy-ordered at pitch 0, depth-sorted under tilt) list.
        for _depth, _fn in _entries:
            _fn()
        # Reset the per-frame full-screen darkness budget. Each
        # whole-screen black overlay below claims a slice via
        # _claim_dark() so the combined wash never exceeds
        # MAX_FULLSCREEN_DARK. The player's feet stay readable even
        # when hide + apex stack.
        self._overlay_dark_used = 0
        self._draw_brimley_haze()
        self._draw_dark()
        self._draw_sight_fog()
        self._draw_outdoor_vignette()
        self._draw_apex_overlay()
        self._draw_hidden_overlay()
        self._draw_bridge_dust()
        # Film grade over the whole world layer (desaturate, cool tint,
        # vignette, animated grain) -- fuses the frame into one grimy
        # image. Applied before the HUD so UI text stays crisp.
        from scenes.base import apply_grade
        apply_grade(self.screen, pygame.time.get_ticks() / 1000.0,
                    frame=self.frame_count)
        # World layer done. Upscale it to the window (one smoothscale) so the
        # HUD below draws at full resolution over a softened world. Restore the
        # full-res camera so next frame's input/unproject reads window pixels.
        if self._render_s < 1.0:
            pygame.transform.smoothscale(self.screen, (SCREEN_W, SCREEN_H),
                                         self._win)
            self.screen = self._win
            self.camera.origin = (SCREEN_W // 2, SCREEN_H // 2)
            self.camera.scale /= self._render_s
        # Cursor reticle in look mode (the mouse is otherwise hidden) -- shows
        # where the gun aims. Drawn on the window (crisp), at the window cursor.
        if self._tilt_on() and self.state == "playing":
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, (228, 198, 96), (mx, my), 7, 1)
            for ddx, ddy in ((10, 0), (-10, 0), (0, 10), (0, -10)):
                pygame.draw.line(self.screen, (228, 198, 96),
                                 (mx + ddx // 2, my + ddy // 2),
                                 (mx + ddx, my + ddy), 1)
        # SEAL live warp overlay: the doorframe ignites gold and the warped
        # dressing leaves streaks as it pours through (the motion itself is
        # driven by the threshold scene's on_update, scenes/depths.py).
        if getattr(self, "_seal_warp", None) is not None:
            self._draw_seal_warp_overlay()
        # Ashfall over the graded world (DESIGN.md §2) -- the pale-yellow drift
        # rides on top so the grade's desaturate/cool-tint can't wash it out.
        # Under the HUD: it's atmosphere, not interface.
        self._draw_ashfall()
        self._draw_interact_prompt()
        self._draw_hud()
        self._draw_notebook_toast()
        # Floating NPC speech (above the speaker's head, non-modal, not
        # sight-gated) sits under the modal dialog box -- the two are
        # mutually exclusive in practice, but a scripted modal always wins.
        self.float_speech.draw(self.screen, self)
        # Non-modal narration caption (lower third, frameless). Under the
        # modal box for the same reason as the floats.
        self.narration.draw(self.screen)
        self.dialog.draw(self.screen)
        self.journal_ui.draw(self.screen, self.player)
        # Text-input modal (LOGIN: terminal etc.) drawn over inventory so
        # it always wins focus.
        self.text_input.draw(self.screen)
        if self.notice_text and not self.journal_ui.open:
            self._draw_notice()
        if self.state == "transition":
            t = self.transition_t / 0.85
            alpha = int(t * 255) if self.transition_dir == "out" else int((1 - t) * 255)
            alpha = max(0, min(255, alpha))
            fade = pygame.Surface(self.screen.get_size())
            fade.fill(C_BLACK)
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
        # Flashback overlay -- preempts everything for the duration of
        # the witnessing sequence.
        self._draw_flashback()
        # Ending overlay -- preempts everything during the ending
        # sequences.
        self._draw_ending()
        # Close-up examine tableau -- a full-frame modal close-up over the
        # world + HUD (world is frozen while it is up).
        self._draw_tableau()
        # Death screen -- the King's mask furnace or the cultist KILLED
        # card. Drawn over EVERYTHING (HUD, dialog) so the catch takes
        # the whole frame.
        if self._death_kind is not None:
            self._draw_death_screen()

    def _item_color(self, key):
        d = ITEM_DEFS.get(key, {})
        return {
            "weapon": (200, 200, 220),
            "armor":  (140, 110, 80),
            "consumable": (220, 80, 80),
            "key": (220, 200, 80),
            "lore": (180, 180, 220),
        }.get(d.get("kind"), (220, 220, 220))

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
                        and self.scene.objects[ty][tx] in ("*", "q")):
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
                # Mirror try_interact's skips so the cue never points at an
                # NPC you can't talk to: no_prompt (the invisible-interact
                # pattern, where a decoration shows its own cue) and _inside
                # (a homebody gone behind its door -- not drawn, not talkable).
                if (getattr(npc, "no_prompt", False)
                        or getattr(npc, "_inside", False)):
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
        # Project through the camera so the cue tracks the target under tilt +
        # yaw (at pitch 0 this is byte-identical to the old `x - cam_x` form).
        # Lift it above the head: the base 40px gap plus the screen-space rise
        # the sprite itself gains under tilt (TILT_ACTOR_STAND * sin pitch), so
        # the [E] clears the risen body instead of sitting on it.
        sx, sy = self.camera.project(target[0], target[1], 0.0)
        sy -= 40 + int(TILT_ACTOR_STAND * math.sin(self.camera.pitch))
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
        s = self.fonts["serif_tiny"].render(scene_label, True, (74, 70, 84))
        self.screen.blit(s, (14, SCREEN_H - 24))
        # Ammo readout, lower-right -- only while carrying the pistol. Red
        # when empty. Dim, like the rest of the HUD.
        if self.player.inventory.has("pistol"):
            ammo = self.player.inventory.count("pistol_ammo")
            col = (200, 70, 60) if ammo <= 0 else (150, 144, 120)
            a = self.fonts["serif_tiny"].render(f"rounds  {ammo}", True, col)
            self.screen.blit(a, (SCREEN_W - a.get_width() - 14,
                                 SCREEN_H - 22))
        # Flashlight state -- only surfaces in the dark, and only once you
        # carry a light. Warm amber when the beam's actually burning (so
        # the cost it's adding to the meter is legible), cold and dim when
        # off, and a dead grey in cult-dark where the beam won't catch.
        if (self.scene.key in DARK_SCENES
                and self.player.inventory.has("flashlight")):
            if self._flashlight_lit():
                lbl, col = "light, lit  (f)", (210, 180, 90)
            elif self.scene.key in CULT_DARK_SCENES:
                lbl, col = "the light will not catch here", (70, 66, 78)
            else:
                lbl, col = "light, dark  (f)", (96, 92, 108)
            ls = self.fonts["serif_tiny"].render(lbl, True, col)
            self.screen.blit(ls, (14, SCREEN_H - 40))
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
        # more of the case you understand. (DESIGN.md §1, made legible.)
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
        # Being-seen readout -- a small NOTCHED rate bar just under the threat
        # meter: how hard human/cult eyes are on you THIS second (the King is
        # felt, not counted). Splits the faucet (rate) from the bathtub (the
        # visibility state above), teaching "unseen is good" in real time.
        seen = max(0.0, min(1.0, getattr(self, "_being_seen", 0.0)))
        n = BEING_SEEN_NOTCHES
        lit_n = int(round(seen * n))
        ng = 1
        nw = (bar_w - (n - 1) * ng) // n
        nb_y = ty + bar_h + 3
        for i in range(n):
            nx = tx + i * (nw + ng)
            if i < lit_n:                            # cool -> amber as eyes pile on
                f = (i + 1) / n
                c = (int(70 + 150 * f), int(82 + 86 * f), int(96 - 44 * f))
            else:
                c = (32, 30, 40)
            pygame.draw.rect(self.screen, c, (nx, nb_y, nw, bar_h))
        # The hidden-floor lesson: unseen (rate 0) but the meter won't drain
        # below the evidence floor -> "knowing dooms you". Pulse the locked floor
        # segment so the player SEES why hiding stopped saving them.
        if seen <= 0.001 and fw > 0 and pw <= fw + 1:
            t_now = pygame.time.get_ticks() / 1000.0
            fl = 0.5 + 0.5 * abs(math.sin(t_now * 4.0))
            pygame.draw.rect(self.screen, (int(150 * fl), int(42 * fl),
                                           int(36 * fl)), (tx, ty, fw, bar_h))
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
        # The hide-check struggle (DESIGN.md §12): a pulsing centre
        # prompt + press pips while the window runs. The prompt IS the
        # mechanic's legibility -- unmistakable, urgent, brief.
        st = getattr(self, "_struggle", None)
        if st is not None:
            t_now = pygame.time.get_ticks() / 1000.0
            pulse = 0.6 + 0.4 * abs(math.sin(t_now * 9.0))
            cx = SCREEN_W // 2
            cy = SCREEN_H // 2 + 70
            # Font.render is one of pygame's priciest per-frame calls --
            # quantize the pulse into 8 cached renders instead of
            # rasterizing the prompt fresh 60x/s inside the mash window.
            pb = min(7, int((pulse - 0.6) / 0.4 * 8))
            cache = getattr(self, "_struggle_txt_cache", None)
            if cache is None:
                cache = self._struggle_txt_cache = {}
            txt = cache.get(pb)
            if txt is None:
                pv = 0.6 + 0.4 * (pb / 7.0)
                txt = cache[pb] = self.fonts["serif"].render(
                    "FIGHT. Mash E.", True,
                    (int(230 * pv), int(70 + 40 * pv), int(50 * pv)))
            self.screen.blit(txt, (cx - txt.get_width() // 2, cy))
            need = max(1, STRUGGLE_PRESSES)
            got = min(need, st.get("presses", 0))
            pw2, ph2, pg = 16, 6, 4
            total = need * pw2 + (need - 1) * pg
            px0 = cx - total // 2
            py0 = cy + txt.get_height() + 8
            for i in range(need):
                c = ((236, 200, 120) if i < got else (60, 40, 40))
                pygame.draw.rect(self.screen, c,
                                 (px0 + i * (pw2 + pg), py0, pw2, ph2))
            # The window itself: a thin draining bar under the pips.
            frac = max(0.0, min(1.0, st.get("t", 0.0) / STRUGGLE_WINDOW))
            pygame.draw.rect(self.screen, (90, 30, 26),
                             (px0, py0 + ph2 + 4, total, 3))
            pygame.draw.rect(self.screen, (210, 60, 48),
                             (px0, py0 + ph2 + 4, int(total * frac), 3))

    def _draw_notebook_toast(self):
        """The corner card the PI scribbles a beat onto, then it fades -- the
        diegetic 'written to the case book' tell, fired by _flash_notebook on
        EVERY clue/note write. It NAMES the beat beside the scribble, so the
        player knows what got recorded and can open the book (I / N) to read
        it. Now the only per-write feedback: the world no longer narrates a
        conclusion at the player on every pickup, so this is how you know the
        PI set something down."""
        tt = getattr(self, "_notebook_toast_t", 0.0)
        if tt <= 0:
            return
        frac = max(0.0, min(1.0, (NOTEBOOK_TOAST_DUR - tt) / NOTEBOOK_TOAST_DUR))
        if frac < 0.10:
            a = frac / 0.10
        elif frac > 0.84:
            a = max(0.0, (1.0 - frac) / 0.16)
        else:
            a = 1.0
        if a <= 0.0:
            return
        ox, oy = 16, 16
        # --- the scribbled leaf ---
        W, H = 46, 56
        page = pygame.Surface((W, H), pygame.SRCALPHA)

        def C(r, g, b, al=255):
            return (r, g, b, int(al * a))
        pygame.draw.rect(page, C(226, 220, 204), (2, 3, W - 6, H - 6))
        pygame.draw.rect(page, C(150, 142, 120), (2, 3, W - 6, H - 6), 1)
        pygame.draw.polygon(page, C(198, 190, 172),
                            [(W - 10, 3), (W - 10, 11), (W - 4, 3)])
        # Ink lines write left-to-right over the toast's first stretch.
        write = max(0.0, min(1.0, (frac - 0.06) / 0.5))
        lx0, lx1 = 7, W - 10
        head = None
        for i in range(5):
            lp = max(0.0, min(1.0, write * 5 - i))
            if lp <= 0:
                break
            ly = 14 + i * 8
            x_end = lx0 + int((lx1 - lx0) * lp)
            pts, x = [], lx0
            while x <= x_end:
                pts.append((x, ly + (1 if (x // 3) % 2 == 0 else 0)))
                x += 3
            if len(pts) >= 2:
                pygame.draw.lines(page, C(38, 32, 42), False, pts, 1)
            head = (x_end, ly)
        if 0.06 < frac < 0.58 and head:
            px, py = head
            pygame.draw.polygon(page, C(26, 24, 32),
                                [(px, py - 1), (px + 3, py - 7), (px + 4, py - 1)])
        self.screen.blit(page, (ox, oy))
        # --- the beat's name beside the leaf, over a soft legibility wash ---
        from ui.case_titles import humanise
        name = getattr(self, "_notebook_toast_name", None)
        title_txt = humanise(name) if name else "Case book"
        lbl = self.fonts["serif_tiny"].render("Noted", True, (206, 178, 108))
        ttl = self.fonts["serif_sm"].render(title_txt, True, (216, 210, 196))
        tx = ox + W + 12
        wash_w = max(lbl.get_width(), ttl.get_width()) + 18
        wash_h = lbl.get_height() + ttl.get_height() + 14
        wash = pygame.Surface((wash_w, wash_h), pygame.SRCALPHA)
        wash.fill((8, 7, 12, int(150 * a)))
        self.screen.blit(wash, (tx - 8, oy + 4))
        lbl.set_alpha(int(255 * a))
        ttl.set_alpha(int(255 * a))
        self.screen.blit(lbl, (tx, oy + 8))
        self.screen.blit(ttl, (tx, oy + 8 + lbl.get_height() + 2))

    def _draw_notice(self):
        s = self.fonts["serif"].render(self.notice_text, True, C_WHITE)
        bg = pygame.Surface((s.get_width() + 24, s.get_height() + 14), pygame.SRCALPHA)
        bg.fill((10, 8, 14, 220))
        x = SCREEN_W // 2 - bg.get_width() // 2
        y = 90
        self.screen.blit(bg, (x, y))
        self.screen.blit(s, (x + 12, y + 7))

    def draw_pause(self):
        s = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        if self.pause_view == "controls":
            self._draw_controls_screen()
            return
        if self.pause_view == "settings":
            self._draw_settings_screen()
            return
        title = self.fonts["serif_title"].render("Paused", True, (200, 198, 206))
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 160))
        for i, opt in enumerate(self.pause_options):
            selected = (i == self.pause_choice)
            color = C_GOLD if selected else (120, 116, 132)
            txt = self.fonts["serif_lg"].render(opt, True, color)
            ox = SCREEN_W//2 - 80
            oy = 260 + i * 50
            # A thin gold margin tick marks the choice -- the same quiet
            # selection language as the inventory/notebook menus, no caret.
            if selected:
                pygame.draw.rect(self.screen, C_GOLD,
                                 (ox - 16, oy + 5, 3, txt.get_height() - 10))
            self.screen.blit(txt, (ox, oy))

    def _draw_controls_screen(self):
        title = self.fonts["serif_title"].render("Controls", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 90))
        x_label = SCREEN_W//2 - 230
        x_key = SCREEN_W//2 + 20
        y0 = 180
        for i, (action, keys) in enumerate(self.CONTROLS_REFERENCE):
            y = y0 + i * 34
            a = self.fonts["serif"].render(action, True, (200, 196, 210))
            k = self.fonts["serif"].render(keys, True, C_GOLD)
            self.screen.blit(a, (x_label, y))
            self.screen.blit(k, (x_key, y))
        hint = self.fonts["serif_sm"].render(
            "esc or enter . back", True, (120, 116, 132))
        self.screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 60))

    def _draw_settings_screen(self):
        title = self.fonts["serif_title"].render("Settings", True, C_WHITE)
        self.screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 130))
        rows = [
            ("Master volume", self.audio.master_vol),
            ("Music volume",  self.audio.music_vol),
            ("Sound volume",  self.audio.sfx_vol),
        ]
        x_label = SCREEN_W//2 - 200
        bar_x = SCREEN_W//2 + 10
        bar_w = 180
        for i, (name, val) in enumerate(rows):
            y = 240 + i * 56
            sel = (i == self.settings_choice)
            color = C_GOLD if sel else (170, 166, 178)
            txt = self.fonts["serif_lg"].render(name, True, color)
            if sel:
                pygame.draw.rect(self.screen, C_GOLD,
                                 (x_label - 16, y + 6, 2, txt.get_height() - 12))
            self.screen.blit(txt, (x_label, y))
            # Slider track + fill + percent.
            pygame.draw.rect(self.screen, (60, 56, 70),
                             (bar_x, y + 18, bar_w, 6), 1)
            pygame.draw.rect(self.screen, color,
                             (bar_x, y + 18, int(bar_w * val), 6))
            pct = self.fonts["serif_sm"].render(
                f"{int(round(val * 100))}%", True, color)
            self.screen.blit(pct, (bar_x + bar_w + 12, y + 12))
        hint = self.fonts["serif_sm"].render(
            "up and down . select     left and right . adjust     esc . back",
            True, (120, 116, 132))
        self.screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 60))
