"""Look / heading control for the oblique camera (CAMERA.md Phase 3).

The camera trails the player's MOVEMENT; the mouse is a free cursor that aims
the gun, and never rotates the view.

Model, updated per frame:
  * `body` -- the heading the player is travelling. Eases toward the walk
              direction, so the body (and the camera behind it) gently swing to
              face where you go. Standing still, it holds.
  * `aim`  -- the free look/aim heading: the world direction from the player to
              the cursor. The gun fires along it and the sprite faces it. It is
              independent of the body, so you can walk one way and aim another.
  * `cam_yaw` -- the world rotation fed to Camera.yaw. Sits directly behind the
              body (body + pi/2, so travel reads up the screen). Eased, never
              snaps. The mouse does NOT feed into it.

Pure + headless-testable: feed it a move heading + an aim heading, read back
cam_yaw / body / aim. The live game maps mouse -> aim via Camera.unproject.
"""
import math

# Tuning (eased per-frame fractions).
BODY_EASE = 0.09                # how fast the body swings toward the walk dir
YAW_EASE = 0.14                 # how gently cam_yaw trails behind the body


def wrap(a):
    """Wrap an angle to (-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class LookController:
    def __init__(self, heading=math.pi / 2):
        self.body = wrap(heading)        # travel facing (radians)
        self.aim = wrap(heading)         # free cursor aim heading (radians)
        # start the camera already settled behind the facing
        self.cam_yaw = wrap(self.body + math.pi / 2)

    def facing_vec(self):
        return (math.cos(self.body), math.sin(self.body))

    def aim_vec(self):
        return (math.cos(self.aim), math.sin(self.aim))

    def update(self, move_heading=None, aim_heading=None):
        """Advance one frame.

          move_heading -- world heading the player is WALKING this frame (None
              when standing). The body eases toward it and the camera trails
              behind, so the view swings to sit behind your travel. This is the
              ONLY thing that turns the camera.
          aim_heading  -- world heading to the cursor (the free gun aim). Set
              straight onto `aim`; it never moves the camera.

        Returns the eased cam_yaw."""
        if move_heading is not None:
            self.body = wrap(self.body
                             + wrap(move_heading - self.body) * BODY_EASE)
        if aim_heading is not None:
            self.aim = wrap(aim_heading)
        target = self.body + math.pi / 2
        self.cam_yaw = wrap(self.cam_yaw + wrap(target - self.cam_yaw) * YAW_EASE)
        return self.cam_yaw
