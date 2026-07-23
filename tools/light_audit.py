"""LIGHT AUDIT — the designer's coverage overlay (TODO #21).

Renders a scene under the tilt camera and overlays every light emitter's
two truths so darkness can be DESIGNED instead of discovered:

  * filled disc  = the MECHANICAL radius (`Scene._LIGHT_KINDS`, what the
                   stealth `lit_at` / shadow-cover gate reads),
  * bright ring  = the VISIBLE pool radius (`FIXTURE_POOLS`, what
                   `_draw_dark` casts), tinted the fixture's own colour,
  * cross-hatch  = everywhere NO mechanical radius reaches: the dark, as
                   a designed shape you can look at.

    python tools/light_audit.py <scene_key> [<scene_key> ...]

Output: /tmp/light_audit_<key>.png  (one sheet per scene, N facing)
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import random
import pygame


def _ground_ring(surf, cam, wx, wy, r, col, width=0, alpha=None):
    pts = [cam.project(wx + r * math.cos(a), wy + r * math.sin(a), 0)
           for a in [i * math.pi / 24.0 for i in range(48)]]
    if alpha is not None:
        tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(tmp, (*col, alpha), pts, width)
        surf.blit(tmp, (0, 0))
    else:
        pygame.draw.polygon(surf, col, pts, width)


def audit(g, key):
    from constants import TILE
    from scenes.base import Scene
    from systems.render_mixin import FIXTURE_POOLS
    random.seed(7)
    g.load_scene_now(key)
    g._update_camera(snap=True)
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    old = g.screen
    g.screen = surf
    import rendering.sight as sight
    sight.visible_factor = lambda *a, **k: 1.0
    try:
        g.draw_world()
    finally:
        g.screen = old
    cam = g.camera
    sc = g.scene
    kinds = getattr(Scene, "_LIGHT_KINDS", {})
    emitters = [(d, kinds.get(d.kind)) for d in sc.decorations
                if d.kind in kinds or d.kind in FIXTURE_POOLS]
    # the dark map: hatch every tile centre outside ALL mechanical radii
    hat = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for ty in range(sc.h):
        for tx in range(sc.w):
            cx, cy = tx * TILE + 16, ty * TILE + 16
            lit = False
            for d, mr in emitters:
                if mr and (d.x - cx) ** 2 + (d.y - cy) ** 2 <= mr * mr:
                    lit = True
                    break
            if lit:
                continue
            p = cam.project(cx, cy, 0)
            if 0 <= p[0] < surf.get_width() and 0 <= p[1] < surf.get_height():
                pygame.draw.line(hat, (60, 90, 200, 90),
                                 (p[0] - 4, p[1] + 3), (p[0] + 4, p[1] - 3), 1)
    surf.blit(hat, (0, 0))
    font = pygame.font.SysFont(None, 22)
    for d, mr in emitters:
        pool = FIXTURE_POOLS.get(d.kind)
        if mr:
            _ground_ring(surf, cam, d.x, d.y, mr, (250, 245, 200),
                         width=0, alpha=42)
            _ground_ring(surf, cam, d.x, d.y, mr, (250, 245, 200), width=1)
        if pool:
            _ground_ring(surf, cam, d.x, d.y, pool[0], pool[1], width=2)
        p = cam.project(d.x, d.y, 0)
        surf.blit(font.render(d.kind, True, (255, 255, 160)),
                  (int(p[0]) + 6, int(p[1]) - 18))
    lg = font.render(
        f"{key}: fill=lit_at radius, ring=visible pool, hatch=THE DARK",
        True, (240, 240, 240))
    pygame.draw.rect(surf, (10, 10, 14),
                     (10, surf.get_height() - 34, lg.get_width() + 12, 26))
    surf.blit(lg, (16, surf.get_height() - 30))
    out = f"/tmp/light_audit_{key}.png"
    pygame.image.save(surf, out)
    print("wrote", out)


def main():
    from systems.game import Game
    g = Game()
    g.save.new()
    g._start_play()
    for key in (sys.argv[1:] or ["lodge", "shop"]):
        audit(g, key)


if __name__ == "__main__":
    main()
