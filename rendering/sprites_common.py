"""Shared sprite palettes + the King-render mode flags.

Internal to the rendering.sprites_* family; `rendering.sprites` re-exports the
public surface. Kept in one place so the cultist + NPC palettes and the
KING_UNFOLD toggle have a single home (no import cycle between siblings)."""

# THE UNFOLDING as the King (rendering/king_unfold.py): the non-humanoid 4D
# apex. When KING_UNFOLD is True the `yellow_king` sprite draws as the Unfolding
# (a real 4D everting mass); flip it False to fall back to the flat pallid-mask
# `_draw_king`. The death routes to `draw_unfold_catch` (Game._draw_death_screen).
KING_UNFOLD = True
KING_UNFOLD_SCALE = 48          # tuned down for the in-game ~tilt scale

# Vessel / pale palette, shared by the bare-human NPC kinds and the cultist.
_VP_HIDE = (58, 50, 42); _VP_LO = (30, 26, 23); _VP_HI = (92, 82, 64)
_VP_PALE = (222, 212, 186); _VP_PALE_LO = (150, 142, 120); _VP_PIT = (18, 14, 16)
_VP_GT = (196, 150, 42); _VP_GHI = (236, 204, 64)
# Muddy, desaturated -- gore is a dark red-brown (implied, never bright).
_VP_FLESH = (150, 134, 124); _VP_FLESH_LO = (104, 92, 84)
_VP_MOUTH = (28, 16, 16); _VP_TEETH = (150, 142, 124)
_VP_GOR = (84, 46, 40); _VP_GOR_LO = (54, 30, 28)
