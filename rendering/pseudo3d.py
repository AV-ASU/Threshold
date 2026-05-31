"""Procedural pseudo-3D — PROTOTYPE.

Proof-of-concept for rendering a creature as a *volumetric* form that is
projected to 2D every frame, instead of a flat drawing. Nothing here is an
image asset: the body is a stack of elliptical cross-sections (a body of
revolution, slightly squashed in depth) plus a handful of surface features
(the void cowl, the constellation of eyes, reaching arms) pinned to object
space at a 3D angle. We rotate the whole thing around its vertical axis by
`yaw`, project orthographically the way the rest of the game draws (x across,
y up the screen, z = depth used only for shading + feature occlusion), and
draw the result.

What that buys, for free, that a flat sprite can't fake:
  * the silhouette is broad side-on and thin head-on (elliptical section),
    so turning reads as real turning;
  * surface features slide *around* the body as it spins and occlude
    themselves on the far side (a feature whose outward normal points away
    from the camera fades out), so the cowl opening and the eyes wrap;
  * a fixed light (front-left) rakes the lit side, and the lit side travels
    as the body rotates.

This is the "option 2" recommendation: stays 100% procedural, slots into the
per-frame draw pattern `sprites.py` already uses. It is intentionally a
standalone module so it can be previewed and judged before touching the live
NPC path. Render a strip with:  python tools/preview_pseudo3d.py
"""
import math
import pygame

# ---- the form, authored in object space -------------------------------------
# Cross-sections up the body: (height_above_base, half_width_x, half_depth_z).
# Depth (z) is deliberately a touch larger than width low down so the thing is
# broad side-on and thin head-on -- a wrong, too-narrow silhouette from the
# front that fills out as it turns. Heights are in sprite pixels.
_SECTIONS = [
    (0.0, 7.5, 8.5),    # ragged hem, flared
    (8.0, 5.6, 6.4),
    (16.0, 4.4, 5.0),
    (26.0, 3.4, 3.8),
    (36.0, 3.0, 3.2),   # shoulders
    (44.0, 4.0, 4.0),   # the cowl swells back out into a head
    (50.0, 3.2, 3.2),   # crown
]
_BASE_Y = 64            # base of the figure within its layer, in layer pixels
_LAYER = (48, 78)       # layer size (w, h) -- generous; the form sways

# Shroud palette, lifted from the flat Watcher so the proto reads as the same
# creature: near-black, a cold rim, a deep void cowl, sick-gold gaze.
_SHROUD    = (24, 22, 28)
_SHROUD_LO = (12, 11, 15)
_RIM       = (52, 52, 70)
_VOID      = (5, 5, 8)
_GOLD      = (150, 122, 40)

# Light comes from front-left-ish: a direction in the camera's xz-plane the
# lit side is computed against.
_LIGHT = (-0.55, 0.83)   # (x, z), normalized-ish; z>0 = toward camera


def _rot_y(px, pz, yaw):
    """Rotate a point in the xz (ground) plane about the vertical axis."""
    c, s = math.cos(yaw), math.sin(yaw)
    return px * c + pz * s, -px * s + pz * c


def _section_edges(hw, hd, yaw):
    """Projected half-width of an elliptical section (semi-axes hw along x,
    hd along z) after a yaw rotation. A rotated ellipse projected onto the
    screen's x-axis spans +/- this -- broad when the deep axis turns to face
    us. Returns (half_width_on_screen, depth_of_nearest_point)."""
    c, s = math.cos(yaw), math.sin(yaw)
    half = math.hypot(hw * c, hd * s)
    # depth of the silhouette's near edge -- only used to bias shading.
    near = abs(hd * c) + abs(hw * s)
    return half, near


def draw_pseudo3d_watcher(surf, x, y, yaw=0.0, t=0.0, gaze=False):
    """Draw the volumetric Watcher centered at world (x, y), facing `yaw`
    radians, animated by time `t`. `gaze=True` (player looks straight at it)
    snuffs the eyes, same contract as the flat sprite."""
    layer = pygame.Surface(_LAYER, pygame.SRCALPHA)
    cx = _LAYER[0] // 2

    # Breathing / looming: a slow vertical bob + a tiny extra yaw wobble so it
    # never sits dead still. Sway shifts the whole stack laterally.
    bob = math.sin(t * 1.3) * 1.2
    loom = 0.5 + 0.5 * math.sin(t * 0.5)            # 0..1, creeps nearer
    sway = math.sin(t * 0.8) * 1.5
    yaw = yaw + math.sin(t * 0.6) * 0.12            # idle turn-search

    # Build the screen-space ribs (left edge, right edge) per section, plus a
    # per-section lit fraction. Lower sections first so we can fill bottom-up.
    ribs = []
    for (h, hw, hd) in _SECTIONS:
        half, _near = _section_edges(hw, hd, yaw)
        sx = cx + sway
        sy = _BASE_Y - h * (0.9 + 0.2 * loom) + bob   # looms taller as it nears
        ribs.append((sx - half, sx + half, sy))

    # Fill the body as a single tapered polygon (left edges down, right up),
    # then a darker inset and a cold rim down the lit side.
    left = [(lx, sy) for (lx, _rx, sy) in ribs]
    right = [(rx, sy) for (_lx, rx, sy) in ribs]
    body = right + left[::-1]
    pygame.draw.polygon(layer, _SHROUD, body)
    pygame.draw.polygon(layer, _SHROUD_LO, body, 1)

    # Which screen side is lit depends on yaw vs the light: rotate the light
    # into object space and see whether its x lands left or right.
    lx_obj, _lz = _rot_y(_LIGHT[0], _LIGHT[1], -yaw)
    lit_right = lx_obj > 0
    rim_pts = right if lit_right else left
    if len(rim_pts) >= 2:
        pygame.draw.lines(layer, _RIM, False, [(p[0], p[1]) for p in rim_pts], 1)

    # Torn hem: short strips trailing off the flared base, stirred by sway.
    base_l, base_r, base_y = ribs[0]
    for i in range(int(base_l), int(base_r), 2):
        ln = 3 + (i * 7 % 5)
        dr = sway * ((i - cx) / 9.0)
        pygame.draw.line(layer, _SHROUD, (i, base_y - 2),
                         (i + dr, base_y - 2 + ln), 2)

    # --- surface features, pinned in 3D so they wrap around on the turn ------
    def surface_pt(theta, h, push=1.0):
        """A point on the body surface at object-angle theta (0 = front) and
        height h. Returns (screen_x, screen_y, facing) where facing>0 means it
        points toward the camera (visible), <0 means it's around the back."""
        # interpolate section radius at this height
        hw, hd = 3.2, 3.4
        for j in range(len(_SECTIONS) - 1):
            h0 = _SECTIONS[j][0]
            h1 = _SECTIONS[j + 1][0]
            if h0 <= h <= h1:
                f = (h - h0) / (h1 - h0)
                hw = _SECTIONS[j][1] + f * (_SECTIONS[j + 1][1] - _SECTIONS[j][1])
                hd = _SECTIONS[j][2] + f * (_SECTIONS[j + 1][2] - _SECTIONS[j][2])
                break
        ox = math.sin(theta) * hw * push
        oz = math.cos(theta) * hd * push
        rx, rz = _rot_y(ox, oz, yaw)
        sx = cx + sway + rx
        sy = _BASE_Y - h * (0.9 + 0.2 * loom) + bob
        return sx, sy, rz       # rz>0 -> toward camera

    # The void cowl: a hollow that sits on the FRONT of the head (theta=0) and
    # so swings out of view as the figure turns its back. Drawn as a dark
    # ellipse whose visibility + width track its facing.
    hcx, hcy, hface = surface_pt(0.0, 45.0, push=0.85)
    if hface > -0.5:
        vis = max(0.0, min(1.0, (hface + 1.0) / 3.0))
        w = int(3 + 5 * vis)
        pygame.draw.ellipse(layer, _VOID,
                            (hcx - w // 2, hcy - 4, w, 11))
        pygame.draw.arc(layer, _SHROUD_LO,
                        (hcx - w // 2 - 1, hcy - 5, w + 2, 13), 0.2, 2.95, 1)
        # The constellation of sick eyes, deep in the cowl. Each pinned at its
        # own object-angle so they emerge and slide as it turns; staggered
        # blink; all snuffed if the player looks straight at it.
        if not gaze:
            for k in range(6):
                th = (k - 2.5) * 0.16
                eh = 44.0 + (k % 3 - 1) * 2.2
                ex, ey, ef = surface_pt(th, eh, push=0.7)
                if ef <= 0.1:
                    continue
                bl = 0.5 + 0.5 * math.sin(t * 1.7 + k * 1.5)
                if bl < 0.3:
                    continue
                evis = min(1.0, ef / 2.2) * bl
                g = int(70 + 60 * evis)
                pygame.draw.circle(layer, (g, int(g * 0.8), 30),
                                   (int(ex), int(ey)), 1)

    # Two long reaching arms, pinned to the shoulders at opposite sides so one
    # always leads and one trails as it turns -- hints of a hand swinging round.
    for side, hofs in ((-1, 0.0), (1, math.pi)):
        shx, shy, shf = surface_pt(side * 1.2 + hofs, 36.0, push=1.0)
        hnx, hny, hnf = surface_pt(side * 1.5 + hofs, 18.0, push=1.35)
        if (shf + hnf) > -1.2:
            pygame.draw.line(layer, _SHROUD_LO,
                             (int(shx), int(shy)), (int(hnx), int(hny)), 2)

    # Half-there apparition: a clear offset after-image, then the figure, both
    # translucent so the background bleeds through. Phase pulses it in and out.
    phase = 0.45 + 0.5 * (math.sin(t * 1.1) * 0.5 + 0.5)
    ox = int(x - cx)
    oy = int(y - _BASE_Y)
    layer.set_alpha(int(150 * phase))
    surf.blit(layer, (ox - int(sway * 3) - 1, oy - 2))
    layer.set_alpha(int(235 * phase))
    surf.blit(layer, (ox, oy))
