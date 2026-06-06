"""Character sprites: NPCs, enemies, the player.

This module is a thin facade. The drawing code lives in themed siblings
(`rendering/sprites_*.py`); they are re-exported here so the long-standing
import surface `from rendering.sprites import <name>` keeps working. See
`sprites_common` for the shared palettes + the KING_UNFOLD render-mode flags.
"""
from rendering.sprites_common import KING_UNFOLD, KING_UNFOLD_SCALE
from rendering.sprites_king import door_mask_surface, reset_king_fx
from rendering.sprites_npc import draw_npc_sprite
from rendering.sprites_infested import draw_infested_overlay
from rendering.sprites_corpse import draw_npc_corpse
from rendering.sprites_player import (
    draw_player_sprite, view_from_facing,
)
from rendering.sprites_weapons import (
    draw_axe_swing, draw_axe_held, draw_revolver_held, draw_gun_fire,
)
from rendering.sprites_carcosa import draw_king_death, draw_mask_yank, draw_carcosa

__all__ = [
    "KING_UNFOLD", "KING_UNFOLD_SCALE",
    "draw_npc_sprite", "draw_npc_corpse", "draw_infested_overlay",
    "draw_player_sprite", "view_from_facing",
    "reset_king_fx", "door_mask_surface",
    "draw_axe_swing", "draw_axe_held", "draw_revolver_held", "draw_gun_fire",
    "draw_king_death", "draw_mask_yank", "draw_carcosa",
]
