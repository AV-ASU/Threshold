"""VISION MOCKUP -- the PORTAL: a standing 4D pane with a dim black-gold electric
border and a readable peek into the real destination, shown under the tilt
camera and AT THREE VIEWING ANGLES so the one-directional rule reads:

  head-on  -> full pane, you see through it and can step in
  oblique  -> narrower, the peek shears, the border thins
  edge-on  -> a thin line, basically gone (you walk past it)

Not wired into the game. Reuses rendering.camera.Camera (the live tilt seam).
See PORTALS.md for the design.

    python tools/preview_portal.py     # -> /tmp/portal.png (+ .gif if PIL)
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

PANEL_W, PANEL_H = 420, 470
PITCH = math.radians(53.0)
SCALE = 44.0

# Brimley daytime (the "here")
SKY_TOP = (158, 158, 146); SKY_BOT = (104, 104, 98)
GRASS = (80, 88, 60); GRASS_DK = (64, 70, 48)
# the pane
GOLD = (196, 156, 58)            # the King's dim cursed gold rim (_GOLD_RIM)
GOLD_HI = (236, 200, 110)
CORE = (10, 8, 9)                # near-black mouth


def _cam():
    return Camera(cam_x=0.0, cam_y=0.0, pitch=PITCH, yaw=0.0,
                  scale=SCALE, origin=(PANEL_W // 2, int(PANEL_H * 0.64)))


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_sky(surf):
    for y in range(PANEL_H):
        surf.fill(_lerp(SKY_TOP, SKY_BOT, y / PANEL_H), (0, y, PANEL_W, 1))


def draw_ground(surf, cam):
    for gy in range(-5, 9):
        for gx in range(-8, 9):
            c = GRASS if (gx + gy) % 2 else GRASS_DK
            quad = [cam.project(gx - 0.5, gy - 0.5), cam.project(gx + 0.5, gy - 0.5),
                    cam.project(gx + 0.5, gy + 0.5), cam.project(gx - 0.5, gy + 0.5)]
            pygame.draw.polygon(surf, c, quad)


def render_destination():
    """The 'elsewhere' seen THROUGH the pane -- a dim, torch-lit grove. Drawn
    once; the peek samples columns from it. Deliberately a RECOGNISABLE place
    (ground, standing effigies, two braziers, a Sign on the dirt)."""
    w, h = 200, PANEL_H
    s = pygame.Surface((w, h))
    # darker, colder ground than Brimley -- clearly another room
    for y in range(h):
        f = y / h
        s.fill(_lerp((40, 44, 40), (20, 24, 22), f), (0, y, w, 1))
    horizon = int(h * 0.42)
    pygame.draw.rect(s, (16, 18, 16), (0, 0, w, horizon))      # void above
    # a faint yellow Sign scratched in the dirt
    cx = w // 2
    for a in range(3):
        ang = a * math.tau / 3 + 0.4
        ex = cx + int(math.cos(ang) * 34); ey = horizon + 70 + int(math.sin(ang) * 22)
        pygame.draw.line(s, (120, 100, 40), (cx, horizon + 70), (ex, ey), 3)
    # two braziers (warm glow) + effigy poles
    for bx, scale in ((46, 1.0), (150, 0.9)):
        glow = pygame.Surface((90, 90), pygame.SRCALPHA)
        for r in range(40, 0, -3):
            aa = int(70 * (1 - r / 40) ** 2)
            pygame.draw.circle(glow, (210, 120, 40, aa), (45, 45), r)
        s.blit(glow, (bx - 45, horizon + 20 - 45), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.line(s, (40, 30, 20), (bx, horizon + 24), (bx, horizon - 38), 5)
        pygame.draw.circle(s, (236, 150, 60), (bx, horizon - 40), 5)
    return s


_DEST = None


def _dest():
    global _DEST
    if _DEST is None:
        _DEST = render_destination()
    return _DEST


def _electric_edge(surf, p0, p1, t, intensity, seed):
    """A jagged 'living wound' arc hugging an edge from p0 to p1."""
    rng = random.Random(seed + int(t * 7))
    n = 9
    pts = []
    for i in range(n + 1):
        f = i / n
        x = p0[0] + (p1[0] - p0[0]) * f
        y = p0[1] + (p1[1] - p0[1]) * f
        j = (rng.uniform(-1, 1)) * 4 * intensity * math.sin(f * math.pi)
        pts.append((x + j, y))
    if len(pts) > 1:
        col = _lerp(GOLD, GOLD_HI, 0.5)
        pygame.draw.lines(surf, col, False, pts, 1)


def draw_portal(surf, cam, theta, t):
    """Standing pane at world origin. `theta` rotates its along-axis so we can
    show it head-on -> edge-on. Returns nothing; draws the peek + border."""
    cx, cy = 0.0, 0.0
    half_w = 0.72
    height = 3.25
    along = (math.cos(theta), math.sin(theta))
    # four world corners -> screen
    def corner(sgn, z):
        return cam.project(cx + along[0] * half_w * sgn,
                           cy + along[1] * half_w * sgn, z)
    bl = corner(-1, 0.0); br = corner(1, 0.0)
    tl = corner(-1, height); tr = corner(1, height)
    # how head-on it is: screen width vs the head-on max
    vis_w = abs(br[0] - bl[0])
    facing = min(1.0, vis_w / (2 * half_w * SCALE))     # 1 head-on, ->0 edge-on
    if facing < 0.04:
        # edge-on: just a faint line where the pane stands
        x = (bl[0] + br[0]) // 2
        pygame.draw.line(surf, _lerp(GRASS_DK, GOLD, 0.3),
                         (x, tl[1]), (x, bl[1]), 1)
        return facing
    dst = _dest()
    dh = dst.get_height()
    # ---- peek: vertical-column sample of the destination, fogged at edges ----
    steps = max(8, int(vis_w))
    peek = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    for i in range(steps + 1):
        f = i / steps
        x = bl[0] + (br[0] - bl[0]) * f
        ybot = bl[1] + (br[1] - bl[1]) * f
        ytop = tl[1] + (tr[1] - tl[1]) * f
        col_h = int(ybot - ytop)
        if col_h <= 1:
            continue
        src_x = int(f * (dst.get_width() - 1))
        col = dst.subsurface((src_x, 0, 1, dh))
        col = pygame.transform.scale(col, (2, col_h))
        # fog: dissolve toward the slit's left/right edges, and overall by facing
        edge_fog = (math.sin(f * math.pi)) ** 0.6
        a = int(255 * edge_fog * (0.35 + 0.65 * facing))
        col.set_alpha(a)
        peek.blit(col, (int(x), int(ytop)))
    surf.blit(peek, (0, 0))
    # ---- black core wash inside the slit (gives the gold rim contrast) ----
    quad = [bl, br, tr, tl]
    core = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    pygame.draw.polygon(core, (*CORE, int(120 * (1 - facing * 0.5))), quad)
    surf.blit(core, (0, 0))
    # ---- dim gold rim ----
    rim_a = int(200 * facing)
    rim = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    pygame.draw.polygon(rim, (*GOLD, rim_a), quad, 3)
    pygame.draw.polygon(rim, (*GOLD_HI, int(rim_a * 0.6)), quad, 1)
    surf.blit(rim, (0, 0))
    # ---- electric arcs along the two vertical edges ----
    arc = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    _electric_edge(arc, bl, tl, t, facing, seed=1)
    _electric_edge(arc, br, tr, t, facing, seed=2)
    if random.Random(int(t * 30)).random() < 0.5:    # occasional cross-flick
        _electric_edge(arc, (bl[0], (bl[1]+tl[1])//2), (br[0], (br[1]+tr[1])//2),
                       t, facing * 0.7, seed=3)
    surf.blit(arc, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    return facing


def draw_corn(surf, cam, wx, wy):
    """A foreground cornstalk to prove depth -- it stands BETWEEN camera and
    portal and overlaps it, so the pane reads as a thing in space."""
    bx, by = cam.project(wx, wy, 0.0)
    tx, ty = cam.project(wx, wy, 1.9)
    pygame.draw.line(surf, (60, 70, 40), (bx, by), (tx, ty), 6)
    for k in range(5):
        f = 0.25 + k * 0.16
        lx, ly = cam.project(wx, wy, f * 1.9)
        s = (-1) ** k
        pygame.draw.line(surf, (150, 150, 78), (lx, ly), (lx + s * 12, ly - 8), 3)


def render_panel(theta, t, label):
    surf = pygame.Surface((PANEL_W, PANEL_H))
    draw_sky(surf)
    cam = _cam()
    draw_ground(surf, cam)
    draw_portal(surf, cam, theta, t)
    draw_corn(surf, cam, 0.7, 2.2)        # nearer than the portal -> in front
    font = pygame.font.SysFont("monospace", 15)
    surf.blit(font.render(label, True, (228, 228, 218)), (10, PANEL_H - 24))
    return surf


def main():
    panels = [
        (math.radians(0),  "head-on -- step through"),
        (math.radians(62), "oblique -- it thins"),
        (math.radians(86), "edge-on -- gone"),
    ]
    strip = pygame.Surface((PANEL_W * len(panels), PANEL_H))
    for i, (th, label) in enumerate(panels):
        strip.blit(render_panel(th, t=2.0 + i, label=label), (i * PANEL_W, 0))
    pygame.image.save(strip, "/tmp/portal.png")
    print("wrote /tmp/portal.png")

    try:
        from PIL import Image
    except ImportError:
        print("(PIL not installed -- skipping GIF)")
        return
    frames = []
    N = 60
    for k in range(N):
        u = k / N
        # walk a half-circle around it: head-on -> edge-on -> head-on
        theta = abs(math.sin(u * math.tau)) * math.radians(90)
        surf = render_panel(theta, t=u * 8.0, label="walking around the pane")
        frames.append(Image.frombytes("RGB", (PANEL_W, PANEL_H),
                                      pygame.image.tostring(surf, "RGB")))
    frames[0].save("/tmp/portal.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/portal.gif")


if __name__ == "__main__":
    main()
