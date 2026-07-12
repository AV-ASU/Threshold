"""Look / heading control for the oblique camera (DESIGN.md §10).

Tank steering: A/D turn the heading (and the camera that rides behind it); W/S
drive forward/back along it. The mouse is a free cursor that aims the gun and
never rotates the view.

Model, updated per frame:
  * `body` -- the heading the player faces / travels. Turned by A/D (the game
              calls turn()); the camera sits behind it. W/S move along it.
  * `aim`  -- the free look/aim heading: the world direction from the player to
              the cursor. The gun fires along it and the sprite faces it. It is
              independent of the body, so you can drive one way and aim another.
  * `cam_yaw` -- the world rotation fed to Camera.yaw. Sits directly behind the
              body (body + pi/2, so the heading reads up the screen). Eased so a
              turn glides rather than snaps. The mouse does NOT feed into it.

Pure + headless-testable: turn() it / feed an aim heading, read back cam_yaw /
body / aim. The live game maps mouse -> aim via Camera.unproject.
"""
import math

# Tuning.
YAW_EASE = 0.25                 # how tightly cam_yaw tracks behind the heading


def wrap(a):
    """Wrap an angle to (-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class LookController:
    def __init__(self, heading=math.pi / 2):
        self.body = wrap(heading)        # heading / travel facing (radians)
        self.aim = wrap(heading)         # free cursor aim heading (radians)
        # start the camera already settled behind the facing
        self.cam_yaw = wrap(self.body + math.pi / 2)

    def facing_vec(self):
        return (math.cos(self.body), math.sin(self.body))

    def aim_vec(self):
        return (math.cos(self.aim), math.sin(self.aim))

    def turn(self, d):
        """Rotate the heading by `d` radians (A/D steering)."""
        self.body = wrap(self.body + d)

    def update(self, aim_heading=None):
        """Advance one frame: set the free aim and ease the camera to sit behind
        the heading. `aim_heading` is the world heading to the cursor (the gun
        aim); it does not directly move the camera (use chase_aim() to make the
        body chase aim with a dead-zone + rate cap). Returns the eased cam_yaw."""
        if aim_heading is not None:
            self.aim = wrap(aim_heading)
        target = self.body + math.pi / 2
        self.cam_yaw = wrap(self.cam_yaw + wrap(target - self.cam_yaw) * YAW_EASE)
        return self.cam_yaw

    def chase_by(self, delta, dt, rate, dead_zone=0.0):
        """Rotate body by `delta` radians, capped at `rate` rad/s and ignoring
        magnitudes below `dead_zone`. The caller supplies the angular delta in
        whatever frame is stable against the body's own rotation — typically a
        SCREEN-relative cursor offset, not a world-aim delta. Using a world-aim
        delta forms a feedback loop in tilt mode: the camera rides body, so
        yawing the camera also yaws the world point under the cursor, and the
        delta never closes (body spins indefinitely)."""
        delta = wrap(delta)
        if abs(delta) <= dead_zone:
            return
        excess = delta - dead_zone if delta > 0 else delta + dead_zone
        step = max(-rate * dt, min(rate * dt, excess))
        self.body = wrap(self.body + step)
