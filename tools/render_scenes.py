"""Headless scene previewer for THRESHOLD.

Renders any registered scene (floor + walls + doors + decorations + any
built-in enemies/NPCs) to a labelled PNG, with the in-game film grade
applied, so the look can be eyeballed and shared in chat without a
display. This is the loop that drove the whole art pass -- keep it
working.

Usage (from the repo root):
    pip install pygame                  # if the env doesn't have it
    python tools/render_scenes.py                 # render every scene
    python tools/render_scenes.py village house   # only these keys
    python tools/render_scenes.py --out /tmp/x     # custom output dir

Output: <out>/<NN>_<key>.png  (default out: /tmp/threshold_renders)
NPCs/items that spawn on scene-entry (innkeeper, pickups, runtime
cultists/Watchers) are NOT shown -- only what the builder places.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys

# Make the repo root importable no matter where this is run from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import SCENE_BUILDERS, load_scene
from scenes.base import (draw_scene_terrain, draw_scene_doors, apply_grade,
                         TILE, scene_display_name)
try:
    from rendering.sprites import draw_npc_sprite
except Exception:
    draw_npc_sprite = None

TARGET = 820   # longest edge of the output image


def _parse_args(argv):
    out = "/tmp/threshold_renders"
    keys = []
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        else:
            keys.append(argv[i])
            i += 1
    return out, (keys or None)


def render_scene(key, font):
    sc = load_scene(key)
    W = max(1, sc.w * TILE)
    H = max(1, sc.h * TILE)
    surf = pygame.Surface((W, H))
    surf.fill((10, 10, 14))
    draw_scene_terrain(surf, sc, 0, 0, 0, 0, sc.w, sc.h)
    for d in sc.decorations:
        try:
            d.draw(surf, 0, 0)
        except Exception:
            pass
    draw_scene_doors(surf, sc, 0, 0, 0, 0, sc.w, sc.h)
    for e in sc.enemies:
        try:
            e.draw(surf, 0, 0)
        except Exception:
            pass
    if draw_npc_sprite:
        for n in sc.npcs:
            try:
                draw_npc_sprite(surf, int(n.x), int(n.y),
                                getattr(n, "sprite_kind", "old"),
                                getattr(n, "facing", (0, 1)))
            except Exception:
                pass
    scale = TARGET / max(W, H)
    big = pygame.transform.scale(
        surf, (max(1, int(W * scale)), max(1, int(H * scale))))
    apply_grade(big, t=1.0)
    label = f"{key}  -  {scene_display_name(sc)}  ({sc.w}x{sc.h})"
    txt = font.render(label, True, (255, 235, 90))
    pygame.draw.rect(big, (0, 0, 0),
                     (0, 0, txt.get_width() + 14, txt.get_height() + 8))
    big.blit(txt, (7, 4))
    return big


def main():
    out, keys = _parse_args(sys.argv[1:])
    os.makedirs(out, exist_ok=True)
    font = pygame.font.Font(None, 30)
    saved = []
    for i, key in enumerate(SCENE_BUILDERS):
        if keys is not None and key not in keys:
            continue
        try:
            img = render_scene(key, font)
        except Exception as exc:
            print(f"SKIP {key}: {exc}")
            continue
        path = os.path.join(out, f"{i:02d}_{key}.png")
        pygame.image.save(img, path)
        saved.append(path)
    print(f"rendered {len(saved)} scene(s) -> {out}")
    for p in saved:
        print(p)


if __name__ == "__main__":
    main()
