"""THE STORM -- the King as the shadow family's apex (TODO #25).

Not one body. His attention floods the flat plane, so the dark fills with
amalgam units (the same Watcher-family cuts). ONE of them bears the Pallid
Mask at a time -- the focal "Him" -- and it MIGRATES: the Mask sinks back
into its bearer's cut and rises from another unit elsewhere (THE UNFOLDING's
host/sink/rebond, translated to the storm).

Rules locked with the maintainer (TODO #25):
- LIGHT SLOWS a unit, never burns it (burning stays the Watchers'
  privilege); a unit also eases AWAY from a lit spot. He is survived,
  never dispelled.
- LUCK, NOT OMNISCIENCE: units drift toward His last SENSE of the player
  (a lagged point that only snaps to the player every `STORM_SENSE_INT`),
  not the live position. Reach light / break his sense and the flood
  blooms where you were, not where you are.
- The Mask stays SUB-PLAYER and CAMERA-FACING (rendering.amalgam).

This module is SIM + a draw helper only; it does not touch the live threat
loop yet. Integration (spawn geography off the darkening, the catch, the
retire of THE UNFOLDING) is TODO #25's later slices. Tuning lives here for
now and moves to systems.config on integration.
"""
import math
import random

from rendering.amalgam import draw_amalgam_sprite

# ---- tuning (moves to systems.config on integration) ----------------------
STORM_UNIT_SPEED = 22.0        # px/s a unit drifts toward His sense of you
STORM_STOP_DIST = 58.0        # it presses no closer than this (the grab is the catch)
STORM_LIGHT_SLOW = 0.22       # speed multiplier for a unit standing in light
STORM_LIGHT_SHY = 14.0        # px/s a lit unit eases back out of the light
STORM_SENSE_INT = 2.2         # s between snaps of His sense to the true player
STORM_DWELL_LO, STORM_DWELL_HI = 3.0, 5.5   # s the Mask is borne before it migrates
STORM_SINK_DUR = 0.6          # s to sink the Mask on the old bearer
STORM_RISE_DUR = 0.6          # s to rise it on the new bearer
STORM_BIRTH_DUR = 0.9         # s a unit takes to manifest
# The Mask at ~PLAYER SCALE: face height ~= player height (the maintainer's
# "the full 1", the preview's bottom row -- 2026-07, revising the earlier
# sub-player call). carved_pallid_surface face height ~= 2.1*r, so on
# integration r = player_sprite_height / 2.1 (~21 for the measured 45px).
STORM_MASK_R = 21


class _Unit:
    __slots__ = ("x", "y", "seed", "birth")

    def __init__(self, x, y, seed):
        self.x = float(x)
        self.y = float(y)
        self.seed = seed
        self.birth = 0.0


class Storm:
    """The storm over one scene. `anchors` are world (x, y) dark spots; the
    caller sizes them off the darkening (all dark, corn included). `lit_at`
    (optional) is a world (x, y) -> bool light test used for the slow rule."""

    def __init__(self, anchors, seed=0, mask_r=STORM_MASK_R, blend=0.5):
        rng = random.Random(seed)
        self.units = [_Unit(ax, ay, rng.randint(0, 99999)) for ax, ay in anchors]
        self.mask_r = mask_r
        self.blend = blend
        self._rng = rng
        # the migrating Mask
        self.bearer = rng.randrange(len(self.units)) if self.units else -1
        self.deploy = 1.0
        self.state = "borne"            # borne / sinking / rising
        self.dwell = rng.uniform(STORM_DWELL_LO, STORM_DWELL_HI)
        # His lagged sense of the player (luck, not omniscience)
        self.sense = None
        self._sense_t = 0.0

    # -- sim -----------------------------------------------------------------
    def update(self, dt, px, py, lit_at=None):
        if not self.units:
            return
        # His sense of you snaps to the truth only every so often
        self._sense_t -= dt
        if self.sense is None or self._sense_t <= 0.0:
            self.sense = (px, py)
            self._sense_t = STORM_SENSE_INT
        sx, sy = self.sense

        for u in self.units:
            if u.birth < 1.0:
                u.birth = min(1.0, u.birth + dt / STORM_BIRTH_DUR)
            dx, dy = sx - u.x, sy - u.y
            d = math.hypot(dx, dy) or 1.0
            spd = STORM_UNIT_SPEED
            lit = bool(lit_at and lit_at(u.x, u.y))
            if lit:
                spd *= STORM_LIGHT_SLOW
            if d > STORM_STOP_DIST:
                u.x += dx / d * spd * dt
                u.y += dy / d * spd * dt
            if lit:
                # a lit unit eases back the way it came (shy of the light)
                u.x -= dx / d * STORM_LIGHT_SHY * dt
                u.y -= dy / d * STORM_LIGHT_SHY * dt

        # the Mask's migration
        if self.state == "borne":
            self.dwell -= dt
            if self.dwell <= 0.0:
                self.state = "sinking"
        elif self.state == "sinking":
            self.deploy = max(0.0, self.deploy - dt / STORM_SINK_DUR)
            if self.deploy <= 0.0:
                self.bearer = self._pick_next(px, py)
                self.state = "rising"
        elif self.state == "rising":
            self.deploy = min(1.0, self.deploy + dt / STORM_RISE_DUR)
            if self.deploy >= 1.0:
                self.state = "borne"
                self.dwell = self._rng.uniform(STORM_DWELL_LO, STORM_DWELL_HI)

    def _pick_next(self, px, py):
        """The Mask rises near His sense of the player (so it hops toward
        you), but never on the unit it just left."""
        idx = [i for i in range(len(self.units)) if i != self.bearer]
        if not idx:
            return self.bearer
        idx.sort(key=lambda i: math.hypot(self.units[i].x - px,
                                          self.units[i].y - py))
        return self._rng.choice(idx[:min(3, len(idx))])

    def mask_world_pos(self):
        """Where the Mask is right now (the bearer's world position), or None
        while it is fully sunk between hosts."""
        if self.bearer < 0 or self.deploy <= 0.0:
            return None
        u = self.units[self.bearer]
        return (u.x, u.y)

    # -- draw ----------------------------------------------------------------
    def draw(self, surf, project, player_screen, actor_h=120):
        """`project(wx, wy) -> (sx, sy)` maps world to screen feet; drawn
        far-to-near. The bearer gets the Mask with its gaze aimed at the
        player's screen head."""
        order = sorted(range(len(self.units)), key=lambda i: self.units[i].y)
        phx, phy = player_screen[0], player_screen[1] - actor_h * 0.4
        for i in order:
            u = self.units[i]
            sx, sy = project(u.x, u.y)
            if i == self.bearer and self.deploy > 0.02:
                gx, gy = phx - sx, phy - (sy - actor_h * 0.5)
                gl = math.hypot(gx, gy) or 1.0
                draw_amalgam_sprite(
                    surf, sx, sy, seed=u.seed, birth=u.birth,
                    mask={"r": self.mask_r, "deploy": self.deploy,
                          "gaze": (gx / gl, gy / gl), "blend": self.blend,
                          "seed": 7})
            else:
                draw_amalgam_sprite(surf, sx, sy, seed=u.seed, birth=u.birth)
