"""VISION MOCKUP -- the 4D "floating pieces" look as the language of the FOLD.

Not wired into the game. A throwaway preview that reuses the REAL pipeline:
  * rendering.camera.Camera  -- the same tilt projection the live world uses
  * the King's 4D helpers (_rot / _to3d) -- the same 4D->3D evert math

Idea: near a fold seam, the world's near geometry (fence posts, cornstalks, a
stretch of road) lifts off the ground and everts through 4D -- solid chunks
separate, tumble, pass through each other, and recombine on the FAR side of the
seam. The drift is localized to the seam (it falls off with distance) so the
rest of the world stays grounded + readable: a threshold effect, not the default
look.

    python tools/preview_fold_shards.py     # -> /tmp/fold_shards.png (+ .gif if PIL)
"""
import os
import sys
import math
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()

from rendering.camera import Camera
from rendering.king_unfold import _rot, _to3d   # the real 4D evert math

PANEL_W, PANEL_H = 384, 480
SEAM_X = 0.0                 # world x of the fold seam
SEAM_RANGE = 4.2            # how far from the seam the lift reaches
PITCH = math.radians(52.0)
SCALE = 42.0

# --- palette (Brimley daytime, sallow -- what the town SHOULD read as) -------
SKY_TOP = (158, 158, 146)
SKY_BOT = (104, 104, 98)
GRASS = (78, 86, 58)
GRASS_DK = (62, 68, 46)
DIRT = (104, 90, 66)
DIRT_DK = (84, 72, 54)
WOOD = (120, 96, 66)
CORN = (168, 158, 84)
GOLD = (210, 170, 70)
GOLD_HI = (248, 224, 138)

LIGHT = (0.4, -0.5, 0.78)
_lm = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _lm for c in LIGHT)


def _cam():
    return Camera(cam_x=0.0, cam_y=0.0, pitch=PITCH, yaw=0.0,
                  scale=SCALE, origin=(PANEL_W // 2, int(PANEL_H * 0.66)))


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _clip(c):
    return (max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))),
            max(0, min(255, int(c[2]))))


def _rot3(v, ax, ay, az):
    x, y, z = v
    cx, sx = math.cos(ax), math.sin(ax)
    y, z = y * cx - z * sx, y * sx + z * cx
    cy, sy = math.cos(ay), math.sin(ay)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cz, sz = math.cos(az), math.sin(az)
    x, y = x * cz - y * sz, x * sz + y * cz
    return (x, y, z)


# box corner offsets and faces (as corner-index quads + outward normal)
_CORNERS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
_FACES = [((0, 1, 2, 3), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)),
          ((0, 1, 5, 4), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
          ((1, 2, 6, 5), (1, 0, 0)), ((0, 3, 7, 4), (-1, 0, 0))]


class Shard:
    __slots__ = ("hx", "hy", "hz", "ex", "ey", "ez", "col", "ph", "seed")

    def __init__(self, hx, hy, hz, ex, ey, ez, col, seed):
        self.hx = hx; self.hy = hy; self.hz = hz        # home center (world)
        self.ex = ex; self.ey = ey; self.ez = ez        # half extents (world)
        self.col = col
        self.seed = seed
        self.ph = (seed * 1.7) % math.tau

    def _state(self, lift, t):
        """Return (center_world, (ax,ay,az) tumble, gold) for the given lift."""
        if lift <= 0.001:
            return (self.hx, self.hy, self.hz), (0.0, 0.0, 0.0), 0.0
        rng = random.Random(self.seed)
        spread = 1.4 + rng.random() * 1.3
        d = [rng.uniform(-1, 1) * spread,
             rng.uniform(-1, 1) * spread,
             0.5 + rng.random() * 1.6,            # bias up off the ground
             lift * (1.0 + rng.random())]         # W: out of the 3D world
        ang = lift * (2.0 + rng.random() * 2.2) + self.ph + t * 0.5
        d = _rot(d, 0, 3, ang * 0.9)
        d = _rot(d, 1, 3, ang * 0.7)
        d = _rot(d, 2, 3, ang * 1.1)
        dx, dy, dz = _to3d(d)
        scl = lift * 2.0
        cx = self.hx + dx * scl
        cy = self.hy + dy * scl
        cz = self.hz + dz * scl + lift * 1.2
        tumble = (ang * 0.8, ang * 0.5 + self.ph, ang * 0.6)
        return (cx, cy, cz), tumble, lift

    def faces(self, cam, lift, t):
        (cx, cy, cz), (ax, ay, az), gold = self._state(lift, t)
        # rotated world corners
        wc = []
        for ox, oy, oz in _CORNERS:
            rx, ry, rz = _rot3((ox * self.ex, oy * self.ey, oz * self.ez), ax, ay, az)
            wc.append((cx + rx, cy + ry, cz + rz))
        out = []
        for idx, n in _FACES:
            nx, ny, nz = _rot3(n, ax, ay, az)
            shade = 0.45 + 0.55 * max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
            col = _clip([self.col[i] * shade for i in range(3)])
            if gold > 0.02:
                col = _lerp(col, GOLD, min(0.55, gold * 0.6))
            pts = [cam.project(*wc[i]) for i in idx]
            dep = sum(cam.depth(*wc[i]) for i in idx) / 4.0
            edge = _lerp(col, GOLD_HI, 0.5) if gold > 0.25 else _clip([col[i] * 1.25 for i in range(3)])
            out.append((dep, pts, col, edge))
        return out


# --------------------------------------------------------------------------- #
# props -> bags of shards
# --------------------------------------------------------------------------- #
def _fence_post(x, y, seed):
    s = []
    for i in range(4):
        z = 0.32 + i * 0.55
        s.append(Shard(x, y, z, 0.13, 0.13, 0.30, _clip([WOOD[k] * (1 - i * 0.05) for k in range(3)]), seed + i))
    s.append(Shard(x, y, 1.9, 0.5, 0.10, 0.10, _clip([WOOD[k] * 0.85 for k in range(3)]), seed + 7))  # rail
    return s


def _corn(x, y, seed):
    rng = random.Random(seed)
    s = []
    for i in range(5):
        z = 0.4 + i * 0.5
        s.append(Shard(x + rng.uniform(-0.08, 0.08), y, z, 0.16, 0.16, 0.30,
                       _clip([CORN[k] * (1 - i * 0.05) for k in range(3)]), seed * 7 + i))
    return s


def build_scene():
    s = []
    sd = 1
    # dirt road band across the front
    for gx in range(-5, 6):
        for gy in range(2, 5):
            c = DIRT if (gx + gy) % 2 else DIRT_DK
            s.append(Shard(gx, gy, 0.06, 0.5, 0.5, 0.06, c, sd)); sd += 1
    # a fence line crossing the seam (back to front)
    for gy in range(-3, 5):
        s += _fence_post(SEAM_X, gy * 1.05, sd); sd += 20
    # corn clusters either side
    for (cx, cy) in [(-2.6, -1.4), (-3.6, 0.8), (2.5, -1.2), (3.6, 1.0),
                     (-1.7, 2.4), (1.9, 2.2), (-3.9, -2.4), (3.9, -2.2)]:
        s += _corn(cx, cy, sd); sd += 40
    return s


def _lift_for(shard, L):
    w = max(0.0, 1.0 - abs(shard.hx - SEAM_X) / SEAM_RANGE)
    return L * (w ** 1.3)


def draw_sky(surf):
    for y in range(PANEL_H):
        surf.fill(_lerp(SKY_TOP, SKY_BOT, y / PANEL_H), (0, y, PANEL_W, 1))


def draw_ground(surf, cam):
    for gy in range(-5, 8):
        for gx in range(-8, 9):
            c = GRASS if (gx + gy) % 2 else GRASS_DK
            quad = [cam.project(gx - 0.5, gy - 0.5), cam.project(gx + 0.5, gy - 0.5),
                    cam.project(gx + 0.5, gy + 0.5), cam.project(gx - 0.5, gy + 0.5)]
            pygame.draw.polygon(surf, c, quad)


def _soft_disc(r, col, peak):
    """A radial additive glow disc (alpha^2 falloff), cached by (r, peak)."""
    key = (r, peak, col)
    d = _soft_disc._c.get(key)
    if d is None:
        d = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -1):
            a = int(peak * (1 - i / r) ** 2)
            pygame.draw.circle(d, (*col, a), (r, r), i)
        _soft_disc._c[key] = d
    return d
_soft_disc._c = {}


def draw_seam(surf, cam, intensity, t):
    """The gold fold-seam at SEAM_X, drawn as a plume of soft glows climbing
    from the ground up (radius + alpha fall off with height) -- a seam of light,
    no hard edges, no sky streaks. A few brighter cores sit near the base."""
    if intensity <= 0.01:
        return
    lay = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    cxs, _ = cam.project(SEAM_X, 0.0, 0.0)
    base_y = cam.project(SEAM_X, 0.0, 0.0)[1]
    lay.blit(_soft_disc(90, GOLD, int(46 * intensity)),       # wide base haze
             (cxs - 90, base_y - 90), special_flags=pygame.BLEND_RGB_ADD)
    for i in range(30):
        f = i / 29.0                                 # 0 = ground, 1 = top of plume
        sy = cam.project(SEAM_X, 0.0, f * 3.4)[1]
        wob = int(math.sin(f * 5 + t * 1.7) * 8 * intensity)
        r = int((34 - f * 22) * (0.6 + 0.4 * intensity))
        peak = int(120 * intensity * (1 - f * 0.6))
        col = GOLD_HI if f < 0.30 else GOLD
        d = _soft_disc(max(3, r), col, max(6, peak))
        lay.blit(d, (cxs + wob - d.get_width() // 2, sy - d.get_height() // 2),
                 special_flags=pygame.BLEND_RGB_ADD)
    surf.blit(lay, (0, 0))


def render_panel(L, seam_i, t, label):
    surf = pygame.Surface((PANEL_W, PANEL_H))
    draw_sky(surf)
    cam = _cam()
    draw_ground(surf, cam)
    draw_seam(surf, cam, seam_i * 0.5, t)
    faces = []
    for sh in build_scene():
        faces.extend(sh.faces(cam, _lift_for(sh, L), t))
    faces.sort(key=lambda f: f[0])
    for _, pts, col, edge in faces:
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, edge, pts, 1)
    draw_seam(surf, cam, seam_i, t)
    font = pygame.font.SysFont("monospace", 15)
    surf.blit(font.render(label, True, (228, 228, 218)), (10, PANEL_H - 24))
    return surf


def main():
    panels = [
        (0.00, 0.18, "Brimley -- intact"),
        (0.20, 0.70, "the seam wakes"),
        (0.55, 1.00, "geometry lifts"),
        (0.95, 1.00, "it everts (4D)"),
        (0.42, 0.80, "reforms -- far side"),
    ]
    strip = pygame.Surface((PANEL_W * len(panels), PANEL_H))
    for i, (L, seam, label) in enumerate(panels):
        strip.blit(render_panel(L, seam, t=i * 1.3, label=label), (i * PANEL_W, 0))
    pygame.image.save(strip, "/tmp/fold_shards.png")
    print("wrote /tmp/fold_shards.png")

    try:
        from PIL import Image
    except ImportError:
        print("(PIL not installed -- skipping GIF)")
        return
    frames = []
    N = 56
    for k in range(N):
        u = k / N
        L = 0.5 - 0.5 * math.cos(u * math.tau)        # 0..1..0
        seam = min(1.0, L * 1.5 + 0.16)
        surf = render_panel(L, seam, t=u * 7.0, label="the fold breathes")
        raw = pygame.image.tostring(surf, "RGB")
        frames.append(Image.frombytes("RGB", (PANEL_W, PANEL_H), raw))
    frames[0].save("/tmp/fold_shards.gif", save_all=True,
                   append_images=frames[1:], duration=70, loop=0)
    print("wrote /tmp/fold_shards.gif")


if __name__ == "__main__":
    main()
