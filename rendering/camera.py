"""Camera + world->screen projection — the single seam every draw goes through.

Today the game converts world to screen ad-hoc everywhere as
    sx = x - cam_x ;  sy = y - cam_y
which hard-codes a top-down orthographic view. This module is the one place
that conversion is supposed to live, so that *tilting the camera* later is a
parameter change here, not a rewrite of 37 scenes.

Coordinate convention (kept compatible with the existing game):
  * world x -> screen right
  * world y -> ground "depth" (screen down when top-down)
  * world z -> height OFF the ground (0 = on the floor), screen up
At pitch 0 this is exactly the current top-down view (z has no effect, you
see the tops of things). As pitch increases toward ~pi/2 the ground
foreshortens (cos) and height rises on screen (sin) -- an oblique / "tilted"
camera. Optional yaw spins the world about the vertical axis.

Drop-in story: `Camera(cam_x, cam_y).world_to_screen(x, y)` returns the same
(sx, sy) the game computes today, so Phase 1 can swap call sites with no
visual change, then `pitch` can be dialed up later.
"""
import math


class Camera:
    def __init__(self, cam_x=0.0, cam_y=0.0, pitch=0.0, yaw=0.0,
                 scale=1.0, origin=(0, 0)):
        self.cam_x = cam_x
        self.cam_y = cam_y
        self.scale = scale
        self.origin = origin      # screen pixel that world (cam_x, cam_y, 0) maps to
        # pitch/yaw are PROPERTIES that cache their cos/sin. project()/depth()
        # run thousands of times per frame (every decoration x9 wrap clones,
        # every billboard, every depth-sort entry) but the angles only change
        # ONCE per frame, so recomputing the trig per call was pure waste. The
        # setters refresh the cache; the math below reads it. Values are
        # identical to the old per-call trig -- this is a speed change, not a
        # visual one.
        self._pitch = pitch       # 0 = top-down, ->pi/2 = looking along ground
        self._yaw = yaw           # rotation about the vertical axis
        self._cp, self._sp = math.cos(pitch), math.sin(pitch)
        self._cy, self._sy = math.cos(yaw), math.sin(yaw)

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, v):
        self._pitch = v
        self._cp, self._sp = math.cos(v), math.sin(v)

    @property
    def yaw(self):
        return self._yaw

    @yaw.setter
    def yaw(self, v):
        self._yaw = v
        self._cy, self._sy = math.cos(v), math.sin(v)

    # -- the seam ------------------------------------------------------------
    def project(self, wx, wy, wz=0.0):
        """World (x, y, z) -> integer screen (sx, sy)."""
        dx = (wx - self.cam_x)
        dy = (wy - self.cam_y)
        if self._yaw:
            c, s = self._cy, self._sy
            dx, dy = dx * c + dy * s, -dx * s + dy * c
        cp, sp = self._cp, self._sp
        sx = self.origin[0] + dx * self.scale
        sy = self.origin[1] + dy * self.scale * cp - wz * self.scale * sp
        return int(sx), int(sy)

    def world_to_screen(self, wx, wy):
        """Back-compat alias for ground-plane points (z = 0)."""
        return self.project(wx, wy, 0.0)

    def unproject(self, sx, sy):
        """Inverse of project() for the ground plane (z = 0): screen pixel ->
        world (wx, wy). The seam in the other direction -- needed to size the
        render window to exactly cover the tilted screen, and for mouse->world
        picking once the live view tilts."""
        rx = (sx - self.origin[0]) / self.scale
        cp = self._cp or 1e-6
        ry = (sy - self.origin[1]) / (self.scale * cp)
        if self._yaw:
            c, s = self._cy, self._sy
            # inverse of the forward rotation [[c, s], [-s, c]]
            rx, ry = rx * c - ry * s, rx * s + ry * c
        return self.cam_x + rx, self.cam_y + ry

    def depth(self, wx, wy, wz=0.0):
        """Painter's-algorithm key: bigger = nearer the camera (draw later).
        Uses ground depth primarily; height nudges so a tall thing on a tile
        sorts just behind/over its own base consistently."""
        dx = (wx - self.cam_x)
        dy = (wy - self.cam_y)
        if self._yaw:
            c, s = self._cy, self._sy
            dy = -dx * s + dy * c
        return dy - wz * 0.001

    # -- pitch-aware footprint helpers (for volumetric draw) -----------------
    def ground_squash(self):
        """How much a flat-on-the-ground circle flattens vertically on screen
        (1 at top-down, ->0 as we tilt to the horizon)."""
        return self._cp

    def height_rise(self):
        """Screen pixels up per world unit of height (0 top-down, ->1)."""
        return self._sp * self.scale
