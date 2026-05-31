"""Portal proof-of-concept (NARRATIVE Sec.11 -- non-Euclidean folds).

Renders a STILL of the core effect: standing in the cornfield maze and
seeing THROUGH a gap into a different scene entirely, masked into the corn
with depth + an eldritch rim. No game-loop wiring yet -- this exists only
to judge whether 'a hole in space that shows somewhere else' reads on a
frame before we build movement/parallax.

Built on the face-list data model we agreed on: a Portal is a list of
PortalFaces; each face is one-sided (a normal it's seen/entered from), a
target scene, an anchor tile in that target centred in the window, and the
window opening on screen. This POC renders ONE face -- the four-sided case
is later just more faces in the list, no new code.

    python tools/portal_poc.py                 # default: maze -> works_sign
    python tools/portal_poc.py --target dark    # look into the hive instead
    python tools/portal_poc.py --out /tmp/p.png
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import sys, math

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from constants import SCREEN_W, SCREEN_H, TILE
from scenes import load_scene
from scenes.base import apply_grade


class PortalFace:
    """One one-sided window. normal = the side it's seen/entered from."""
    def __init__(self, normal, target_scene, anchor_tile, opening_rect):
        self.normal = normal
        self.target_scene = target_scene
        self.anchor_tile = anchor_tile
        self.opening_rect = opening_rect


class Portal:
    def __init__(self, faces):
        self.faces = faces


def render_view(scene, cam_x, cam_y, w, h):
    """An in-game viewport of `scene` (terrain + decorations) to a w x h
    surface at the given camera. Mirrors what the live draw_world shows."""
    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    scene.draw(surf, cam_x, cam_y)        # terrain + decorations (+ wrap clones)
    return surf


def _depth_shade(win):
    """Darken the window's edges so the far place reads as set BACK behind
    the corn plane -- a hole with depth, not a flat sticker."""
    w, h = win.get_size()
    shade = pygame.Surface((w, h), pygame.SRCALPHA)
    border = max(10, min(w, h) // 5)
    for i in range(border):
        a = int(200 * (1 - i / border) ** 1.6)
        pygame.draw.rect(shade, (0, 0, 0, a), (i, i, w - 2 * i, h - 2 * i), 1)
    win.blit(shade, (0, 0))


def _eldritch_rim(frame, r):
    """A faint, sickly-gold wrongness around the opening -- the Sign's
    colour bleeding from the seam where space doesn't meet itself."""
    glow = pygame.Surface((r.width + 40, r.height + 40), pygame.SRCALPHA)
    for i, a in ((10, 22), (6, 40), (2, 90)):
        pygame.draw.rect(glow, (210, 188, 70, a),
                         (20 - i, 20 - i, r.width + 2 * i, r.height + 2 * i),
                         max(1, i))
    frame.blit(glow, (r.x - 20, r.y - 20))


def _occluding_stalks(frame, r, seed=5):
    """A few corn stalks overlapping the window's vertical edges, so the
    gap reads as torn between real stalks in front of the far place."""
    import random
    rng = random.Random(seed)
    for edge_x in (r.left, r.right):
        for _ in range(7):
            sy = rng.randint(r.top - 6, r.bottom + 6)
            sx = edge_x + rng.randint(-7, 7)
            h = rng.randint(18, 34)
            col = (28 + rng.randint(0, 22), 34 + rng.randint(0, 26), 18)
            pygame.draw.line(frame, col, (sx, sy), (sx + rng.randint(-2, 2), sy - h), 2)


def composite_face(frame, face):
    """Render the neighbour scene through one face into the host frame."""
    target = load_scene(face.target_scene)
    r = face.opening_rect
    ax, ay = face.anchor_tile
    anchor_px, anchor_py = ax * TILE + 16, ay * TILE + 16
    tcam_x = anchor_px - r.width // 2
    tcam_y = anchor_py - r.height // 2
    win = render_view(target, tcam_x, tcam_y, r.width, r.height)
    apply_grade(win, t=1.0)
    _depth_shade(win)
    frame.blit(win, r.topleft)
    _eldritch_rim(frame, r)
    _occluding_stalks(frame, r)


def _draw_player(frame, x, y):
    """A small POV figure standing before the window, facing up into it."""
    pygame.draw.ellipse(frame, (0, 0, 0, 60), (x - 11, y + 12, 22, 8))
    pygame.draw.rect(frame, (38, 34, 30), (x - 6, y - 6, 12, 18))   # coat
    pygame.draw.circle(frame, (60, 52, 44), (x, y - 10), 6)          # head


def main():
    out = "/tmp/portal_poc.png"
    target = "works_sign"
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out = argv[i + 1]; i += 2
        elif argv[i] == "--target" and i + 1 < len(argv):
            target = argv[i + 1]; i += 2
        else:
            i += 1

    host = load_scene("cornfield_maze")
    # Stand the camera so corn fills the frame and a lane runs north ahead.
    px, py = 11 * TILE + 16, 14 * TILE + 16
    hcam_x = px - SCREEN_W // 2
    hcam_y = py - SCREEN_H // 2 - 40
    frame = pygame.Surface((SCREEN_W, SCREEN_H))
    frame.fill((8, 8, 11))
    host.draw(frame, hcam_x, hcam_y)
    apply_grade(frame, t=1.0)

    # One face: a window in the corn ahead, seen from the south (normal up),
    # looking into the target scene's middle.
    tgt = load_scene(target)
    opening = pygame.Rect(SCREEN_W // 2 - 115, 120, 230, 215)
    portal = Portal([PortalFace((0, -1), target,
                                 (tgt.w // 2, tgt.h // 2), opening)])
    for face in portal.faces:
        composite_face(frame, face)

    _draw_player(frame, SCREEN_W // 2, SCREEN_H // 2 + 150)

    font = pygame.font.Font(None, 28)
    label = f"PORTAL POC  cornfield_maze  -->  {target}  (one face, seen from south)"
    txt = font.render(label, True, (255, 235, 90))
    pygame.draw.rect(frame, (0, 0, 0), (0, 0, txt.get_width() + 14, txt.get_height() + 8))
    frame.blit(txt, (7, 4))
    pygame.image.save(frame, out)
    print(f"portal POC -> {out}  (host=cornfield_maze, target={target})")


if __name__ == "__main__":
    main()
