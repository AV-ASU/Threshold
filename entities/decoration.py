"""Animated decorative props (candles, smoke, the well, gore...).
Pure draw functions, no game logic.

The per-kind ``_draw_*`` methods were split by theme into the
``deco_*`` sibling mixins (2026-07); this file keeps the Decoration
shell (init/update/draw dispatch) and composes them. Shared
lighting/compass helpers live in ``decoration_common``. External code
still does ``from entities.decoration import Decoration`` unchanged."""
import random
import pygame
from constants import SCREEN_W, SCREEN_H
from entities.decoration_common import (
    _ground_shadow, _GROUNDED_DECOS, _NO_SCALE_DECOS,
)
from entities.deco_furniture import DecoFurnitureMixin
from entities.deco_lighting import DecoLightingMixin
from entities.deco_nature import DecoNatureMixin
from entities.deco_structure import DecoStructureMixin
from entities.deco_mine import DecoMineMixin
from entities.deco_horror import DecoHorrorMixin


class Decoration(
    DecoFurnitureMixin, DecoLightingMixin, DecoNatureMixin,
    DecoStructureMixin, DecoMineMixin, DecoHorrorMixin,
):
    # Class-level player position cache. Game updates this every step
    # so a Decoration draw can read the player's world coords without
    # the draw signature having to plumb them through. Used by the
    # watching_eye to point its pupil at the player and by any future
    # tracking decoration.
    player_world = (0, 0)

    def __init__(self, x, y, kind, scale=1.0, seed=None, **kwargs):
        self.x = x; self.y = y
        self.kind = kind
        self.scale = scale
        self.t = random.uniform(0, 100)
        self.seed = seed if seed is not None else random.randint(0, 9999)
        self.kwargs = kwargs

    def update(self, dt):
        self.t += dt

    def draw(self, surf, cam_x, cam_y, camera=None, wox=0.0, woy=0.0,
             mount_z=0.0):
        if getattr(self, "hidden", False):
            return                       # conditionally withheld (e.g. the
            #                              arrival-road car during the treadmill)
        # Route the point anchor through the shared projection when the live
        # game supplies a camera (DESIGN.md §10); fall back to the legacy
        # top-down conversion for headless tools that pass raw offsets. At
        # pitch 0 the two are arithmetically identical. `wox/woy` is the
        # wrap-clone world offset (0 for the primary draw), passed explicitly
        # so projection doesn't depend on the camera's pivot convention.
        # `mount_z` lifts the anchor off the ground (wall-hung decorations) so
        # the flat sprite reads as a card stood up the wall, not on the floor.
        if camera is not None:
            sx, sy = camera.project(self.x + wox, self.y + woy, mount_z)
        else:
            sx = int(self.x - cam_x)
            sy = int(self.y - cam_y)
        if sx < -64 or sx > SCREEN_W + 64 or sy < -64 or sy > SCREEN_H + 64:
            return
        if self.kind in _GROUNDED_DECOS:
            _ground_shadow(surf, sx, sy + 16, 13, 5, 75)
        drawfn = getattr(self, f"_draw_{self.kind}", self._draw_unknown)
        # Scale support: small static props/stains can be enlarged to
        # fill a room and break the tile grid. Opt-in (scale != 1.0), so
        # every existing 1.0 placement is byte-identical. Risky kinds
        # (lights, player-trackers, ambient, already-large) opt out.
        if self.scale != 1.0 and self.kind not in _NO_SCALE_DECOS:
            C = 48
            canvas = pygame.Surface((C * 2, C * 2), pygame.SRCALPHA)
            drawfn(canvas, C, C)
            side = max(1, int(C * 2 * self.scale))
            scaled = pygame.transform.scale(canvas, (side, side))
            surf.blit(scaled, (sx - side // 2, sy - side // 2))
        else:
            drawfn(surf, sx, sy)

    def _draw_unknown(self, surf, x, y):
        pygame.draw.rect(surf, (255, 0, 255), (x - 4, y - 4, 8, 8))
