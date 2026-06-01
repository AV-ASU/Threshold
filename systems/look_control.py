"""Look / heading control for the oblique camera (CAMERA.md Phase 3).

One input -- the mouse -- drives aim, head-turn, body-turn, and (with right
mouse held) free scene rotation. No extra keys.

Model, updated per frame:
  * `aim`  -- world heading from the player to the cursor (where the gun points)
  * `body` -- the player's facing; eases toward `aim` but the HEAD may lead it
              by up to +/-45deg. If the body lags more than that, it is forced
              to keep up so the head never exceeds the limit. Hold the cursor
              off to one side and the body slowly comes around (head re-centres).
  * `cam_yaw` -- the world rotation fed to Camera.yaw. Targets "body faces up
              the screen" (body + pi/2) plus a PARTIAL lean toward the head
              offset (so a peek swings the view a little, not fully) plus any
              free RMB rotation. Eased so the world never snaps.

Pure + headless-testable: feed it headings/deltas, read back cam_yaw / body /
head_off. The live game maps mouse -> aim via Camera.unproject and supplies the
RMB delta.
"""
import math

# Tuning (all eased per-frame fractions unless noted).
HEAD_MAX = math.radians(45)     # the head-turn arc limit off the body facing
BODY_EASE = 0.10                # how fast the body rotates toward the aim
YAW_EASE = 0.18                 # how fast cam_yaw eases to its target
LEAN_FRAC = 0.55                # camera lean per unit of head offset (<1 = partial)
RMB_SENS = math.radians(0.30)   # scene-rotate radians per pixel of mouse x
RMB_RELEASE = 0.85              # how fast free rotation relaxes when RMB released


def wrap(a):
    """Wrap an angle to (-pi, pi]."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class LookController:
    def __init__(self, heading=math.pi / 2):
        self.body = wrap(heading)        # world facing (radians)
        self.head_off = 0.0              # clamped head offset (radians)
        self.rmb_yaw = 0.0               # free scene rotation under RMB
        # start the camera already settled behind the facing
        self.cam_yaw = wrap(self.body + math.pi / 2)

    @property
    def aim(self):
        """World heading the gun points along (body + head lead)."""
        return wrap(self.body + self.head_off)

    def facing_vec(self):
        return (math.cos(self.body), math.sin(self.body))

    def aim_vec(self):
        a = self.aim
        return (math.cos(a), math.sin(a))

    def update(self, aim_heading=None, rmb_dx=0.0, rmb_held=False):
        """Advance one frame. `aim_heading` is the world angle to the cursor
        (ignored while RMB is held). Returns the eased cam_yaw."""
        if rmb_held:
            # deliberate look-around: drag rotates the whole scene
            self.rmb_yaw = wrap(self.rmb_yaw + rmb_dx * RMB_SENS)
        else:
            # relax the free rotation back toward neutral when released
            self.rmb_yaw *= RMB_RELEASE
            if aim_heading is not None:
                # body eases toward the aim...
                self.body = wrap(self.body + wrap(aim_heading - self.body) * BODY_EASE)
                # ...but the head may only lead by HEAD_MAX; force the body if not
                off = wrap(aim_heading - self.body)
                if off > HEAD_MAX:
                    self.body = wrap(aim_heading - HEAD_MAX); off = HEAD_MAX
                elif off < -HEAD_MAX:
                    self.body = wrap(aim_heading + HEAD_MAX); off = -HEAD_MAX
                self.head_off = off
        # camera target: body up the screen + partial head lean + free rotation
        target = self.body + math.pi / 2 + self.head_off * LEAN_FRAC + self.rmb_yaw
        self.cam_yaw = wrap(self.cam_yaw + wrap(target - self.cam_yaw) * YAW_EASE)
        return self.cam_yaw

    def move_basis(self):
        """Camera-relative movement basis in WORLD space: (forward, right)
        unit vectors. `forward` = the way the player faces (screen-up)."""
        fx, fy = math.cos(self.body), math.sin(self.body)
        return (fx, fy), (-fy, fx)
