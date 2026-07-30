"""Shared fold-wound glow helper.

The per-local body-horror overlays that used to live here were cut
(the town reads normal, the wrongness is the *place*, not the people). What
remains is the one reusable primitive the corpse art still leans on: gold
welling up from inside an opened wound.
"""
import pygame

_WGOLD = (236, 204, 64)


def _gold_in_wound(surf, cx, cy, R, peak=64):
    """Additive gold glow welling up from inside an opened wound."""
    R = max(2, int(R))
    g = pygame.Surface((R * 2 + 2, R * 2 + 2), pygame.SRCALPHA)
    for i in range(R, 0, -1):
        a = int(peak * (1 - i / R))
        if a > 0:
            pygame.draw.circle(g, (_WGOLD[0], _WGOLD[1], _WGOLD[2], a),
                               (R + 1, R + 1), i)
    surf.blit(g, (cx - R - 1, cy - R - 1), special_flags=pygame.BLEND_RGBA_ADD)
