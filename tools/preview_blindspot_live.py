"""Live blind-spot preview (DESIGN.md §10).

Boots the real Game headless, loads a populated outdoor scene, forces the
oblique tilt on, and renders draw_world() for a spread of LOOK HEADINGS so the
sight gate can be eyeballed: NPCs / items / rot are drawn only where the head
is pointed, hidden (and free to keep simulating) in the blind spot. Evidence is
bumped so the world rot rot is present to show its reveal-on-peek.

    python tools/preview_blindspot_live.py  -> /tmp/blindspot_live.png
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
from systems.game import Game, TILT_PITCH_DEG, TILT_ZOOM
from systems.look_control import LookController

SCENE = "brimley"
HEADINGS = [-90, -90 + 70, 0, 90, 150]   # up, up-right, right, down, down-left
LABELS = ["look UP", "look UP-RIGHT", "look RIGHT", "look DOWN", "look DOWN-LEFT"]


def _neutralize_grade(g):
    """Strip the darkening post passes so the sight gate is legible in the
    still (the film grade / vignette / haze bury the world in twilight)."""
    import scenes.base as sb
    sb.apply_grade = lambda *a, **k: None
    for name in ("_draw_brimley_haze", "_draw_outdoor_vignette", "_draw_dark",
                 "_draw_apex_overlay", "_draw_hidden_overlay"):
        setattr(g, name, lambda *a, **k: None)


def boot():
    g = Game()
    g.save.new()
    # bump evidence so world rot rot is scattered (reveal-on-peek target)
    g.save.arg("evidence")[:] = ["a", "b", "c"]
    g._start_play()
    g.load_scene_now(SCENE)
    _neutralize_grade(g)
    g._update_camera(snap=True)
    # force the tilt fully on
    g.camera.pitch = math.radians(TILT_PITCH_DEG)
    g.camera.scale = TILT_ZOOM
    return g


def render(g, head_deg):
    g.look = LookController(math.radians(head_deg))
    # settle the head/look so aim == heading (no easing lag for the still shot)
    g.look.body = math.radians(head_deg)
    g.look.aim = g.look.body
    g.look.cam_yaw = (g.look.body + math.pi / 2)
    g.camera.yaw = g.look.cam_yaw
    if g.player:
        g.player.facing = (math.cos(g.look.body), math.sin(g.look.body))
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    g._update_camera(snap=True)
    g.camera.pitch = math.radians(TILT_PITCH_DEG)
    g.camera.scale = TILT_ZOOM
    g.draw_world()
    _debug_overlay(g, surf)
    return surf.copy()


def _debug_overlay(g, surf):
    """Mark the sight DECISION for every NPC + draw the cone edges, so the gate
    is unmistakable: green ring = drawn (in sight), red x = hidden (blind spot,
    still simulating). Diagnostic only -- not part of the game."""
    from rendering.sight import visible_factor, SIGHT_HALF, SIGHT_RANGE
    p = g.player
    head = g.look.aim
    blk = g.scene.blocks_sight
    # cone edge rays projected onto the floor
    for edge in (-1, 1):
        ang = head + edge * SIGHT_HALF
        ex = p.x + math.cos(ang) * SIGHT_RANGE
        ey = p.y + math.sin(ang) * SIGHT_RANGE
        a = g.camera.project(p.x, p.y)
        b = g.camera.project(ex, ey)
        pygame.draw.line(surf, (230, 200, 110), a, b, 1)
    for npc in g.scene.npcs:
        if getattr(npc, "_inside", False):
            continue
        f = visible_factor(p.x, p.y, head, npc.x, npc.y, blk)
        sx, sy = g.camera.project(npc.x, npc.y)
        if f >= 0.5:
            pygame.draw.circle(surf, (90, 230, 120), (sx, sy - 18), 9, 2)
        else:
            pygame.draw.line(surf, (230, 80, 80), (sx - 6, sy - 24),
                             (sx + 6, sy - 12), 2)
            pygame.draw.line(surf, (230, 80, 80), (sx - 6, sy - 12),
                             (sx + 6, sy - 24), 2)


def main():
    g = boot()
    cell = render(g, HEADINGS[0])
    cw, ch = cell.get_width(), cell.get_height()
    font = pygame.font.SysFont("monospace", 16)
    cols = len(HEADINGS)
    out = pygame.Surface((cw * cols, ch + 24))
    out.fill((6, 6, 8))
    for i, (hd, lab) in enumerate(zip(HEADINGS, LABELS)):
        out.blit(render(g, hd), (i * cw, 0))
        out.blit(font.render(lab, True, (210, 200, 150)), (i * cw + 8, ch + 4))
    pygame.image.save(out, "/tmp/blindspot_live.png")
    print("wrote /tmp/blindspot_live.png  (%d scenes, tilt %ddeg)" % (cols, TILT_PITCH_DEG))


if __name__ == "__main__":
    main()
