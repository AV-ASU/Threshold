"""PROTOTYPE -- the SEE-THROUGH DOOR (mundane portal-door).

The idea (design spike): stop treating a door as a fade-to-black transition.
A door is a real aperture standing on the wall seam; through the opening you
see the ACTUAL room beyond, rendered with the same tilt camera as your own
view -- the floor past the threshold recedes the way yours does. A wooden leaf
hangs in the frame and physically swings; when it is shut it occludes the room,
when it swings open the room resolves into view. Walking across the sill is the
existing seamless `cross_fold` (no fade, stride/look preserved), so the door
looks like one continuous space you step through.

This reuses the King-rift / hidden-fold through-view core almost entirely --
`rendering.portal._render_through_full` already renders any target scene through
an aperture with the live camera. The ONLY differences from `draw_rift_door`:
  * keep the colour (no gray "liminal" crush -- this is a normal room, not the
    space between);
  * a WOODEN FRAME (jambs + lintel + sill) instead of the buzzing gold rim;
  * a real hinged LEAF quad that swings about the frame's near jamb and occludes
    the aperture -- the leaf IS the reveal, not an alpha ramp.

Everything is projected through `camera`, so the frame and the swinging leaf
foreshorten with the head-turn and with where the player stands, exactly like
the rift door and the walls. Pitch-0 has no meaningful see-through (you look at
the tops of things); this prototype targets the tilted view.

Not wired into the live game -- see tools/preview_seethrough_door.py.
"""
import math

import pygame

from constants import TILE, SCREEN_W, SCREEN_H

# Warm painted-wood palette for the frame + leaf (a Brimley interior door).
_WOOD_DARK = (46, 33, 24)
_WOOD_MID = (78, 56, 39)
_WOOD_LIT = (120, 92, 62)
_LEAF_FACE = (64, 47, 34)
_LEAF_EDGE = (150, 118, 82)

DOOR_H_TILES = 2.4          # door opening height, in world tiles
JAMB_W = 5                  # frame thickness on screen, px


def _lift(camera, world_h):
    """Screen pixels a world height projects straight UP (the wall/standee
    rule): world z rises by sin(pitch) * scale."""
    return int(world_h * camera.height_rise())


def _quad_up(base0, base1, up):
    """A wall parallelogram: base segment base0->base1, sides straight up
    `up` px (world height projects vertically on screen)."""
    return [base0, base1,
            (base1[0], base1[1] - up),
            (base0[0], base0[1] - up)]


def draw_seethrough_door(screen, target, anchor_px, fx, fy, camera, t,
                         seam_dir, swing=0.0, hinge="left", light=0.6):
    """Draw a mundane see-through door standing on the wall seam at world
    (fx, fy).

    target      -- the (already-built) Scene on the far side.
    anchor_px   -- world (x, y) in `target` that should sit centred in the
                   opening (normally the arrival spawn).
    seam_dir    -- unit WORLD vector along the wall the door sits in.
    swing       -- 0 (shut) .. 1 (flat open ~90deg). Drives the leaf angle.
    hinge       -- "left" or "right": which jamb the leaf is hinged on.
    light       -- 0..1 warmth of the spill pooled on the floor at the sill.
    """
    from rendering.portal import _render_through_full

    swing = max(0.0, min(1.0, swing))
    seam_world = DOOR_H_TILES * TILE * 0.75          # opening breadth (world)
    door_world_h = DOOR_H_TILES * TILE               # opening height (world)
    sdx, sdy = seam_dir
    half = seam_world * 0.5

    # The fixed opening: base endpoints of the frame on the ground seam.
    hw = (fx - sdx * half, fy - sdy * half)          # "left" jamb world pos
    fw = (fx + sdx * half, fy + sdy * half)          # "right" jamb world pos
    if hinge == "right":
        hw, fw = fw, hw                              # hinge on the other jamb
    p_hinge = camera.project(*hw)
    p_free = camera.project(*fw)
    up = _lift(camera, door_world_h)

    bx, by = camera.project(fx, fy)

    # -- warm floor spill at the sill (sells the door as a light source) -----
    if light > 0.01:
        seg = math.hypot(p_free[0] - p_hinge[0], p_free[1] - p_hinge[1])
        glow_w = max(16, int(seg) + 20)
        spill = pygame.Surface((glow_w, 22), pygame.SRCALPHA)
        a = int(90 * light * (0.25 + 0.75 * swing))
        pygame.draw.ellipse(spill, (150, 120, 70, a), spill.get_rect())
        ang = math.degrees(math.atan2(p_free[1] - p_hinge[1],
                                      p_free[0] - p_hinge[0]))
        if abs(ang) > 0.5:
            spill = pygame.transform.rotate(spill, -ang)
        screen.blit(spill, (int(bx - spill.get_width() / 2),
                            int(by - spill.get_height() / 2)),
                    special_flags=pygame.BLEND_RGBA_ADD)

    # -- the room beyond, rendered through the opening -----------------------
    aperture = _quad_up(p_hinge, p_free, up)
    left = int(min(q[0] for q in aperture))
    top = int(min(q[1] for q in aperture))
    right = int(max(q[0] for q in aperture))
    bot = int(max(q[1] for q in aperture))
    rect = pygame.Rect(left, top, right - left + 1,
                       bot - top + 1).clip(screen.get_rect())
    if rect.width > 2 and rect.height > 2:
        try:
            full = _render_through_full(target, anchor_px, camera,
                                        (bx, by - up / 2), 0.0, t)
            win = full.subsurface(rect).convert_alpha()
            # Mask to the aperture polygon. NO gray crush -- keep the colour;
            # a light interior gloom sells "another room" without the rift's
            # liminal desaturate.
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.polygon(mask, (255, 255, 255, 255),
                                [(qx - rect.left, qy - rect.top)
                                 for qx, qy in aperture])
            win.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            win.fill((205, 205, 210, 255), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(win, rect.topleft)
        except Exception:
            pygame.draw.polygon(screen, (10, 9, 12), aperture)

    # -- the hinged leaf, swinging about the near jamb -----------------------
    # World rotation of the free base point about the hinge base point, about
    # the vertical axis. swing=0 -> leaf fills the opening (shut); swing=1 ->
    # ~90deg, the leaf edge-on. Rotate toward the far room (into the target).
    ang = swing * (math.pi / 2.0) * 0.98
    nx, ny = -sdy, sdx                                # wall normal (into room)
    if hinge == "right":
        nx, ny = -nx, -ny
    hx, hy = hw
    vx, vy = (fw[0] - hx), (fw[1] - hy)              # hinge -> free, world
    ca, sa = math.cos(ang), math.sin(ang)
    # Rotate v toward the normal: v' = v*cos + (|v| * n) * sin
    vlen = math.hypot(vx, vy) or 1.0
    rvx = vx * ca + nx * vlen * sa
    rvy = vy * ca + ny * vlen * sa
    leaf_free_w = (hx + rvx, hy + rvy)
    lp0 = camera.project(hx, hy)
    lp1 = camera.project(*leaf_free_w)
    leaf = _quad_up(lp0, lp1, up)
    # Shade the leaf by how edge-on it is (more open = catches less light).
    shade = 0.55 + 0.45 * (1.0 - swing)
    face = tuple(int(c * shade) for c in _LEAF_FACE)
    pygame.draw.polygon(screen, face, leaf)
    pygame.draw.polygon(screen, _LEAF_EDGE, leaf, 2)
    # A rail + a simple panel line so the leaf reads as a door, not a slab.
    mid0 = ((leaf[0][0] + leaf[1][0]) // 2, (leaf[0][1] + leaf[1][1]) // 2)
    mid1 = ((leaf[3][0] + leaf[2][0]) // 2, (leaf[3][1] + leaf[2][1]) // 2)
    pygame.draw.line(screen, _WOOD_DARK, mid0, mid1, 1)
    # A little brass knob on the free stile.
    knob = (int(lp1[0] * 0.5 + leaf[2][0] * 0.5),
            int((lp1[1] + leaf[2][1]) / 2 - up * 0.12))
    pygame.draw.circle(screen, (198, 168, 96), knob, max(2, int(up * 0.02)))

    # -- the wooden frame (jambs + lintel + sill) ----------------------------
    hh = up
    # jambs
    for base in (p_hinge, p_free):
        jamb = [(base[0] - JAMB_W, base[1]),
                (base[0] + JAMB_W, base[1]),
                (base[0] + JAMB_W, base[1] - hh),
                (base[0] - JAMB_W, base[1] - hh)]
        pygame.draw.polygon(screen, _WOOD_MID, jamb)
        pygame.draw.polygon(screen, _WOOD_DARK, jamb, 1)
    # lintel across the top
    lintel = [(p_hinge[0] - JAMB_W, p_hinge[1] - hh),
              (p_free[0] + JAMB_W, p_free[1] - hh),
              (p_free[0] + JAMB_W, p_free[1] - hh - JAMB_W * 2),
              (p_hinge[0] - JAMB_W, p_hinge[1] - hh - JAMB_W * 2)]
    pygame.draw.polygon(screen, _WOOD_LIT, lintel)
    pygame.draw.polygon(screen, _WOOD_DARK, lintel, 1)
