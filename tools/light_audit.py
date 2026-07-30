"""LIGHT AUDIT — the designer's coverage overlay.

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


def _ground_ring(surf, cam, wx, wy, r, col, width=0, alpha=None, cone=None):
    """Ground-projected outline of a pool: a full ring, or -- for a cone
    fixture -- the FAN (apex + arc), so a directional light audits as the
    fan it actually throws."""
    if cone is not None:
        nx, ny, half = cone
        a0 = math.atan2(ny, nx)
        pts = [cam.project(wx, wy, 0)]
        pts += [cam.project(wx + r * math.cos(a0 - half + 2 * half * i / 20),
                            wy + r * math.sin(a0 - half + 2 * half * i / 20),
                            0) for i in range(21)]
    else:
        pts = [cam.project(wx + r * math.cos(a), wy + r * math.sin(a), 0)
               for a in [i * math.pi / 24.0 for i in range(48)]]
    if alpha is not None:
        tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(tmp, (*col, alpha), pts, width)
        surf.blit(tmp, (0, 0))
    else:
        pygame.draw.polygon(surf, col, pts, width)


def _cone_of(d):
    raw = getattr(d, "kwargs", {}).get("cone")
    if not raw:
        return None
    dx, dy, half = raw
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n, math.radians(half))


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

    def _covered(d, cx, cy, r):
        if getattr(d, "kwargs", {}).get("broken"):
            return False                    # a burned-out bulb covers nothing
        if not r or (d.x - cx) ** 2 + (d.y - cy) ** 2 > r * r:
            return False
        cn = _cone_of(d)
        if cn is not None:
            dxv, dyv = cx - d.x, cy - d.y
            dist = math.hypot(dxv, dyv)
            if dist > 2.0:
                ca = math.acos(max(-1.0, min(
                    1.0, (dxv * cn[0] + dyv * cn[1]) / dist)))
                if ca > cn[2]:
                    return False
        return True

    # the dark map: hatch every WALKABLE tile centre outside ALL mechanical
    # radii, and tally COVERAGE over the walkable floor (the maintainer's
    # 90% rule: with every light on, >=90% of an indoor room's floor sits
    # inside a VISIBLE pool; the ~10% dark is chosen, not left over)
    hat = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    walk = mech_hits = pool_hits = 0
    for ty in range(sc.h):
        for tx in range(sc.w):
            cx, cy = tx * TILE + 16, ty * TILE + 16
            if sc.is_solid_at(cx, cy):
                continue
            walk += 1
            mech = any(_covered(d, cx, cy, mr) for d, mr in emitters)
            pool = any(_covered(d, cx, cy,
                                (FIXTURE_POOLS.get(d.kind) or (0,))[0])
                       for d, mr in emitters)
            mech_hits += mech
            pool_hits += pool
            if mech:
                continue
            p = cam.project(cx, cy, 0)
            if 0 <= p[0] < surf.get_width() and 0 <= p[1] < surf.get_height():
                pygame.draw.line(hat, (60, 90, 200, 90),
                                 (p[0] - 4, p[1] + 3), (p[0] + 4, p[1] - 3), 1)
    surf.blit(hat, (0, 0))
    cov_pool = 100.0 * pool_hits / max(1, walk)
    cov_mech = 100.0 * mech_hits / max(1, walk)
    font = pygame.font.SysFont(None, 22)
    # placed DARK SOURCES (the reverse light): a deep-blue ring, so the
    # authored blackness is as reviewable as the light
    for d in sc.decorations:
        if getattr(d, "kind", None) != "dark_pool":
            continue
        dr = int(getattr(d, "kwargs", {}).get("r", 90))
        _ground_ring(surf, cam, d.x, d.y, dr, (70, 60, 190), width=0, alpha=48)
        _ground_ring(surf, cam, d.x, d.y, dr, (110, 100, 235), width=2)
        p = cam.project(d.x, d.y, 0)
        surf.blit(font.render("dark_pool", True, (140, 130, 245)),
                  (int(p[0]) + 6, int(p[1]) - 18))
    for d, mr in emitters:
        p = cam.project(d.x, d.y, 0)
        if getattr(d, "kwargs", {}).get("broken"):
            # a broken fixture audits as a red X + tag, no rings: it is
            # sanctioned dark (the 1-2 per room rule), not missing coverage
            pygame.draw.line(surf, (235, 90, 80), (p[0] - 5, p[1] - 5),
                             (p[0] + 5, p[1] + 5), 2)
            pygame.draw.line(surf, (235, 90, 80), (p[0] - 5, p[1] + 5),
                             (p[0] + 5, p[1] - 5), 2)
            surf.blit(font.render(d.kind + " (broken)", True, (235, 120, 110)),
                      (int(p[0]) + 6, int(p[1]) - 18))
            continue
        pool = FIXTURE_POOLS.get(d.kind)
        cn = _cone_of(d)
        if mr:
            _ground_ring(surf, cam, d.x, d.y, mr, (250, 245, 200),
                         width=0, alpha=42, cone=cn)
            _ground_ring(surf, cam, d.x, d.y, mr, (250, 245, 200), width=1,
                         cone=cn)
        if pool:
            _ground_ring(surf, cam, d.x, d.y, pool[0], pool[1], width=2,
                         cone=cn)
        surf.blit(font.render(d.kind, True, (255, 255, 160)),
                  (int(p[0]) + 6, int(p[1]) - 18))
    lg = font.render(
        f"{key}: fill=lit_at radius, ring=visible pool, hatch=THE DARK   "
        f"coverage: pool {cov_pool:.0f}% / mech {cov_mech:.0f}% "
        f"(target: pool >= 90)",
        True, (240, 240, 240))
    pygame.draw.rect(surf, (10, 10, 14),
                     (10, surf.get_height() - 34, lg.get_width() + 12, 26))
    surf.blit(lg, (16, surf.get_height() - 30))
    out = f"/tmp/light_audit_{key}.png"
    pygame.image.save(surf, out)
    print(f"wrote {out}  pool={cov_pool:.0f}% mech={cov_mech:.0f}%")


def main():
    from systems.game import Game
    g = Game()
    g.save.new()
    g._start_play()
    for key in (sys.argv[1:] or ["lodge", "shop"]):
        audit(g, key)


if __name__ == "__main__":
    main()
