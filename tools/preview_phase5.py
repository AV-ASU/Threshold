"""Phase 5 verification: the LIVE oblique view of a furnished room, exercising
the per-actor occlusion + depth-correct interleave (walls/props/actors in one
depth-sorted list, walls fade for whichever VISIBLE actor they cover) and the
head-turn arc swinging the camera yaw.

Boots a real Game headless, tilts the camera to the locked ~55deg, drops a few
actors around the furniture + partition walls, and renders the scene across the
+/-45deg head-turn arc to a labelled strip (+ a sweeping gif).

    python tools/preview_phase5.py [scene]   -> /tmp/phase5.png (+ .gif)
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
import systems.game as gmod
from systems.game import TILT_PITCH_DEG, TILT_ZOOM


def _boot(key):
    g = gmod.Game()
    g.save.new()
    g._start_play()
    g.load_scene_now(key)
    # engage the oblique view (what F3 does), settled (no ease)
    g._cam_pitch_target = math.radians(TILT_PITCH_DEG)
    g.camera.pitch = math.radians(TILT_PITCH_DEG)
    g.camera.scale = TILT_ZOOM
    g._update_camera(snap=True)
    return g


def render(g, yaw_deg):
    g.look.cam_yaw = math.radians(yaw_deg)
    g.camera.yaw = g.look.cam_yaw
    # the look heading the sight cone keys to (face up-screen + the head lean)
    g.look.body = -math.pi / 2
    g.look.aim = g.look.body + math.radians(yaw_deg)
    if g.player:
        ax, ay = g.look.aim_vec()
        g.player.facing = (ax, ay)
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    g.draw_world()
    return surf.copy()


def main():
    key = (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-")
           else "sheriff_office")
    g = _boot(key)
    W, H = g.screen.get_width(), g.screen.get_height()
    font = pygame.font.SysFont("monospace", 14)
    yaws = [-45, -22, 0, 22, 45]
    strip = pygame.Surface((W * len(yaws), H + 20))
    strip.fill((6, 6, 8))
    for i, yd in enumerate(yaws):
        # re-boot per frame so simulated actors don't drift between captures
        gi = _boot(key)
        strip.blit(render(gi, yd), (i * W, 0))
        tag = "FORWARD" if yd == 0 else f"head {yd:+d}deg"
        strip.blit(font.render(tag, True, (190, 185, 150)), (i * W + 8, H + 2))
    pygame.image.save(strip, "/tmp/phase5.png")
    print("wrote /tmp/phase5.png")
    try:
        from PIL import Image
    except ImportError:
        print("PIL missing; no gif"); return
    frames = []
    N = 48
    for i in range(N):
        gi = _boot(key)
        yd = 45 * math.sin(i / N * 2 * math.pi)
        s = render(gi, yd)
        frames.append(Image.frombytes("RGB", (W, H),
                      pygame.image.tostring(s, "RGB")).convert(
                          "P", palette=Image.ADAPTIVE))
    frames[0].save("/tmp/phase5.gif", save_all=True, append_images=frames[1:],
                   duration=70, loop=0)
    print("wrote /tmp/phase5.gif")


if __name__ == "__main__":
    main()
