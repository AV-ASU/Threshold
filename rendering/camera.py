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
        self.pitch = pitch        # 0 = top-down, ->pi/2 = looking along ground
        self.yaw = yaw            # rotation about the vertical axis
        self.scale = scale
        self.origin = origin      # screen pixel that world (cam_x, cam_y, 0) maps to

    # -- the seam ------------------------------------------------------------
    def project(self, wx, wy, wz=0.0):
        """World (x, y, z) -> integer screen (sx, sy)."""
        dx = (wx - self.cam_x)
        dy = (wy - self.cam_y)
        if self.yaw:
            c, s = math.cos(self.yaw), math.sin(self.yaw)
            dx, dy = dx * c + dy * s, -dx * s + dy * c
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        sx = self.origin[0] + dx * self.scale
        sy = self.origin[1] + dy * self.scale * cp - wz * self.scale * sp
        return int(sx), int(sy)

    def world_to_screen(self, wx, wy):
        """Back-compat alias for ground-plane points (z = 0)."""
        return self.project(wx, wy, 0.0)

    def depth(self, wx, wy, wz=0.0):
        """Painter's-algorithm key: bigger = nearer the camera (draw later).
        Uses ground depth primarily; height nudges so a tall thing on a tile
        sorts just behind/over its own base consistently."""
        dx = (wx - self.cam_x)
        dy = (wy - self.cam_y)
        if self.yaw:
            c, s = math.cos(self.yaw), math.sin(self.yaw)
            dy = -dx * s + dy * c
        return dy - wz * 0.001

    # -- pitch-aware footprint helpers (for volumetric draw) -----------------
    def ground_squash(self):
        """How much a flat-on-the-ground circle flattens vertically on screen
        (1 at top-down, ->0 as we tilt to the horizon)."""
        return math.cos(self.pitch)

    def height_rise(self):
        """Screen pixels up per world unit of height (0 top-down, ->1)."""
        return math.sin(self.pitch) * self.scale
