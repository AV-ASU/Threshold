"""The King's portal -- the visible 4D rift (KING_PROMPT M2 + the look passes).

When the player pins visibility at 100%, the King tears a rift connecting their
room to the room he stands in, and folds through. The rift wears the SAME
gold-on-black electric motif as the hidden folds (rendering.folds) -- NOT the
Threshold doorframe, which by canon never screams.

PSEUDO-3D (KING_PROMPT decision): the rift is never a flat screen-space decal.
Two parts, both camera-respecting:
  - THE FRAME is a light in the scene -- a gold light-pool spills on the ground
    at the rift's base, an additive glow climbs the tear, and the jittered gold
    cut sits on the base seam.
  - THE VIEW THROUGH IT is the target room rendered with the SAME tilt camera
    (same pitch / yaw / scale), aimed so the room you'd emerge into sits in the
    aperture, then masked to the rift's standing-tear hole. So looking through
    flows continuously with the player's own 3D view -- a real oriented hole in
    space, the floor beyond receding the same way yours does -- DESATURATED
    toward gray (the spaces between are colourless; your room keeps the colour).

Reuses the live tilt pipeline (scenes.base.draw_terrain_tilted + _tilt_tile_box,
rendering.skybox) so the far side is the same renderer as the near side, plus
the folds gold seam so the two rift kinds read as one family.
"""
import math
import random

import pygame
import numpy as np

from constants import TILE, SCREEN_W, SCREEN_H
from scenes.base import apply_grade
from rendering.folds import _fog_mask, _draw_seam, _blit_tear, _draw_rim

PORTAL_W = 3 * TILE          # peek depth (flat fallback only)
PORTAL_H = 3 * TILE          # breadth of the slit

_POOL_CACHE = {}
_GLOW_CACHE = {}

# ---- the camera-respecting view through the rift -----------------------------

_THROUGH_CACHE = {}              # cache the expensive scene composite per fold

# How many frames between full re-renders of the through-view. The target room
# is STATIC (no actors walking around in it for the hidden folds), and the
# translation-safe cache shift handles the player walking past, so a real
# rebuild is only needed when pitch/yaw/scale change OR the cached crop falls
# off the edge of the buf. We bumped this from 4 to 30 (~half a second at 60
# fps) -- the eye can't see content updates that aren't there to update, but
# you do see the rebuild stalls. The forming King's portal still rebuilds per
# loom step since loom changes invalidate the cache.
_REFRESH_FRAMES = 30


def clear_through_cache():
    """Drop the cached through-view buffers. Called on scene load (fold/portal
    object identities change) so stale buffers don't linger forever."""
    _THROUGH_CACHE.clear()


def _render_through_full(target, anchor_px, camera, door_origin, loom, t):
    """Build the full-screen tilted render of `target` aimed so anchor_px lands
    at door_origin. Returns the SCREEN-sized Surface (so caller can crop).
    This is the expensive call we want to cache between frames."""
    from rendering.camera import Camera
    from rendering.skybox import draw_skybox
    from scenes.base import draw_terrain_tilted, _tilt_tile_box, _TILT_WALL_RISE
    ax, ay = anchor_px
    pcam = Camera(cam_x=ax, cam_y=ay, pitch=camera.pitch, yaw=camera.yaw,
                  scale=camera.scale, origin=(int(door_origin[0]),
                                              int(door_origin[1])))
    buf = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_skybox(buf, (0, 0, SCREEN_W, SCREEN_H), yaw=pcam.yaw,
                kind="void", horizon_frac=0.40)
    walls, solid_decos, _wall_decos = draw_terrain_tilted(buf, target, pcam)
    walls = sorted(walls, key=lambda w: pcam.depth(
        w[0] * TILE + TILE / 2, w[1] * TILE + TILE / 2, _TILT_WALL_RISE))
    for tx, ty in walls:
        _tilt_tile_box(buf, pcam, target, tx, ty)
    for d in solid_decos:
        try:
            from rendering.furniture import draw_furniture_solid
            from rendering.props import draw_prop_solid
            if not draw_furniture_solid(buf, pcam, d):
                draw_prop_solid(buf, pcam, d)
        except Exception:
            pass
    if loom > 0.01:
        # He looms on the far side while the rift forms, before he steps through.
        from rendering.king_unfold import draw_king_unfold
        ox, oy = int(door_origin[0]), int(door_origin[1])
        lift = int(18 * math.sin(camera.pitch))
        draw_king_unfold(buf, ox, oy - lift, t, threat=0.45,
                         scale=max(26.0, camera.scale * 40.0),
                         to_player=(0.0, 1.0), birth=1.0,
                         lean=(math.sin(t * 0.8) * 0.12, -0.12))
    return buf


# Mouselook eases camera.yaw by tiny amounts every frame (~0.004 rad / frame),
# so a fine-rounded yaw signature invalidated the cache on every frame the
# player moved -- the actual lag the player feels. We tolerate a small yaw
# delta and only force a real rebuild past this threshold. Inside the band the
# cached buf is used as-is, so the destination room's projection is mildly
# off-axis from the rim by up to _YAW_THRESH radians. Hard to spot under the
# liminal desaturate; preserves smooth mouselook performance.
_YAW_THRESH = 0.14               # ~8 deg of yaw drift tolerated before rebuild


def _wrap_pi(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _render_through(target, anchor_px, camera, rect, door_origin,
                    loom=0.0, t=0.0, cache_key=None):
    """Return a `rect`-sized Surface showing `target` through the rift, with the
    same tilt camera as the host. CACHED per `cache_key` (id of the fold/portal).

    The cached buf is anchored to the door's screen origin at build time. When
    the player walks, the host camera translates and the door moves on screen,
    but the cached buf's content stays valid -- we just CROP at a shifted
    position equal to (current door_origin minus the door_origin at build).
    This lets the cache survive camera translation, which is the hot case
    (walking past the fold). A real rebuild only fires every
    `_REFRESH_FRAMES` frames OR when pitch/scale change OR the camera yaw has
    drifted past `_YAW_THRESH` since the build (so the smooth mouselook ease
    doesn't thrash the cache every frame).

    `loom` (0..1) draws the King at the anchor -- him looming through the rift
    while it forms, before he comes (canon: you see him on the far side first).
    """
    pitch_b = round(camera.pitch, 3)
    scale_b = round(camera.scale, 3)
    loom_b = round(loom, 2)
    refresh = True
    entry = None
    if cache_key is not None:
        entry = _THROUGH_CACHE.get(cache_key)
        if entry is not None:
            yaw_drift = abs(_wrap_pi(camera.yaw - entry["yaw"]))
            refresh = (entry["frame"] >= _REFRESH_FRAMES
                       or yaw_drift > _YAW_THRESH
                       or entry["pitch"] != pitch_b
                       or entry["scale"] != scale_b
                       or entry["loom"] != loom_b)
    if refresh:
        full = _render_through_full(target, anchor_px, camera, door_origin,
                                    loom, t)
        arr = pygame.surfarray.pixels3d(full)
        gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
        for c in range(3):
            arr[..., c] = np.clip(arr[..., c] * 0.55 + gray * 0.30,
                                  0, 255).astype(arr.dtype)
        del arr
        entry = {"buf": full, "frame": 0,
                 "yaw": camera.yaw, "pitch": pitch_b, "scale": scale_b,
                 "origin": (int(door_origin[0]), int(door_origin[1])),
                 "loom": loom_b}
        if cache_key is not None:
            _THROUGH_CACHE[cache_key] = entry
    else:
        entry["frame"] += 1
    # Crop at a shifted position so a cache hit still aligns with the door's
    # new screen position. The cached buf has the anchor at entry["origin"];
    # the current frame wants it at door_origin.
    shift_x = entry["origin"][0] - int(door_origin[0])
    shift_y = entry["origin"][1] - int(door_origin[1])
    src_rect = pygame.Rect(rect.left + shift_x, rect.top + shift_y,
                           rect.width, rect.height)
    buf_rect = entry["buf"].get_rect()
    if not buf_rect.contains(src_rect):
        # The cached buf doesn't cover the requested crop -- the camera moved
        # too far since the build. Force a fresh build (full-screen render).
        full = _render_through_full(target, anchor_px, camera, door_origin,
                                    loom, t)
        arr = pygame.surfarray.pixels3d(full)
        gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
        for c in range(3):
            arr[..., c] = np.clip(arr[..., c] * 0.55 + gray * 0.30,
                                  0, 255).astype(arr.dtype)
        del arr
        entry["buf"] = full; entry["frame"] = 0
        entry["origin"] = (int(door_origin[0]), int(door_origin[1]))
        src_rect = rect
    return entry["buf"].subsurface(src_rect).copy()


def _aperture_mask(quad):
    """A full-screen alpha mask shaped like the rift's standing-tear hole
    (`quad` = 4 screen points, base then top), opaque at the base and fading up
    into the liminal gray. White = show the room through; transparent = host."""
    mask = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    pygame.draw.polygon(mask, (255, 255, 255, 255), quad)
    top = max(0, int(min(p[1] for p in quad)))
    bot = min(SCREEN_H, int(max(p[1] for p in quad)))
    if bot > top:
        grad = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        span = bot - top
        for y in range(top, bot):
            f = (bot - y) / span                  # 1 at base -> 0 at the top
            a = int(255 * (0.32 + 0.68 * f))
            pygame.draw.line(grad, (255, 255, 255, a), (0, y), (SCREEN_W, y))
        mask.blit(grad, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return mask


# ---- the gold frame (light in the scene) ------------------------------------

def _gold_pool(screen, cx, cy, r, intensity):
    """An additive GOLD light-pool on the floor at the rift's base. Squashed to
    lie on the ground plane (pseudo-3D); cached per radius (RGB falloff baked
    in -- additive ignores alpha, so black adds nothing)."""
    r = max(10, int(r))
    base = _POOL_CACHE.get(r)
    if base is None:
        base = pygame.Surface((r * 2, r * 2))
        base.fill((0, 0, 0))
        for rr in range(r, 0, -1):
            ff = (1.0 - rr / r) ** 2
            pygame.draw.circle(base, (int(108 * ff), int(80 * ff),
                                      int(24 * ff)), (r, r), rr)
        _POOL_CACHE[r] = base
    k = max(0.2, min(1.0, intensity))
    pool = pygame.transform.scale(base, (r * 2, max(2, int(r * 1.1))))
    if k < 0.99:
        pool = pool.copy()
        pool.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(pool, (int(cx - r), int(cy - r * 0.55)),
                special_flags=pygame.BLEND_RGB_ADD)


def _tear_glow(screen, s0, s1, rise, intensity):
    """A soft additive gold glow climbing the standing tear, brightest at the
    base seam and fading up. Cached by (width, rise)."""
    x0, y0 = s0
    x1, y1 = s1
    w = max(2, int(math.hypot(x1 - x0, y1 - y0)))
    rise = max(2, int(rise))
    glow = _GLOW_CACHE.get((w, rise))
    if glow is None:
        glow = pygame.Surface((w, rise))
        glow.fill((0, 0, 0))
        for j in range(rise):
            ff = (1.0 - j / rise) ** 2
            pygame.draw.line(glow, (int(120 * ff), int(92 * ff), int(28 * ff)),
                             (0, rise - 1 - j), (w, rise - 1 - j))
        _GLOW_CACHE[(w, rise)] = glow
    k = max(0.2, min(1.0, intensity))
    g = glow
    if k < 0.99:
        g = glow.copy()
        g.fill((int(255 * k),) * 3, special_flags=pygame.BLEND_RGB_MULT)
    screen.blit(g, (int(min(x0, x1)), int(min(y0, y1) - rise)),
                special_flags=pygame.BLEND_RGB_ADD)


def _flat_peek(target, anchor, charge):
    """Pitch-0 (F3) fallback: the old flat top-down slice stood up as a panel."""
    w, h = PORTAL_W, PORTAL_H
    ax, ay = anchor
    surf = pygame.Surface((w, h))
    surf.fill((8, 8, 11))
    target.draw(surf, ax * TILE + 16 - w // 2, ay * TILE + 16 - h // 2)
    apply_grade(surf, 1.0)
    arr = pygame.surfarray.pixels3d(surf)
    gray = (arr[..., 0] * 0.30 + arr[..., 1] * 0.59 + arr[..., 2] * 0.11)
    for c in range(3):
        arr[..., c] = (arr[..., c] * 0.20 + gray * 0.66).astype(arr.dtype)
    del arr
    surf = surf.convert_alpha()
    mask = _fog_mask(w, h, (0, 1))
    pa = pygame.surfarray.pixels_alpha(surf)
    pa[:, :] = (mask * (150 + 90 * max(0.0, min(1.0, charge)))).astype(np.uint8)
    del pa
    return surf


def draw_rift_door(screen, target, anchor_px, fx, fy, camera, t,
                   formed=True, charge=1.0, cache_key=None):
    """The shared RIFT DOOR -- an upright black-gold door standing on the ground
    at world (fx, fy), showing `target` (centred on the EXACT world point
    `anchor_px`) through it with the same tilt camera, framed by the continuous
    tesseract rim. Used by BOTH the King's portal AND the hidden folds so every
    rift reads as one door-passage family (KING_PROMPT). `charge`/`formed` drive
    the form-up grow + the looming King; a fold passes formed=True, charge=1."""
    charge = max(0.0, min(1.0, charge))
    pulse = (0.78 + 0.22 * math.sin(t * 5.0)) * (0.5 + 0.5 * charge)
    seam_len = PORTAL_H
    bx, by = camera.project(fx, fy)
    sq = camera.ground_squash()
    growth = 0.30 + 0.70 * charge
    doorW = max(14, int(seam_len * camera.scale * 0.7 * growth))
    doorH = max(18, int(seam_len * camera.scale * (0.62 + 1.05 * sq) * growth))
    top = by - doorH
    quad = [(bx - doorW / 2, by), (bx + doorW / 2, by),
            (bx + doorW / 2, top), (bx - doorW / 2, top)]
    shadow = pygame.Surface((doorW + 10, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, int(120 * (0.4 + 0.6 * charge))),
                        shadow.get_rect())
    screen.blit(shadow, (int(bx - doorW / 2 - 5), int(by - 6)))
    _gold_pool(screen, bx, by, doorW * 0.7, pulse)
    rect = pygame.Rect(int(bx - doorW / 2), int(top),
                       doorW, doorH).clip(screen.get_rect())
    if (formed or charge > 0.5) and rect.width > 2 and rect.height > 2:
        try:
            loom = 0.0 if formed else charge
            win = _render_through(target, anchor_px, camera, rect,
                                  (bx, (by + top) / 2), loom=loom, t=t,
                                  cache_key=cache_key)
            # The through-view's own desaturate already supplies the liminal
            # look; no second crush -- that turned the room into a black hole
            # the player couldn't see into. Forming rifts still ramp alpha up
            # as the tear grows.
            if formed:
                if charge < 0.99:
                    win.set_alpha(int(160 + 95 * charge))
            else:
                win.set_alpha(int(60 + 195 * (charge - 0.5) / 0.5))
            screen.blit(win, rect.topleft)
        except Exception:
            pygame.draw.rect(screen, (10, 8, 12), rect)
    elif rect.width > 2 and rect.height > 2:
        pygame.draw.rect(screen, (10, 8, 12), rect)         # forming: dark wound
    _draw_rim(screen, quad, t, pulse)                       # the buzzing 4D edge


def draw_portal(screen, portal, cam_x, cam_y, camera, t):
    """Composite the King's torn rift onto `screen` (already showing the host)."""
    target = portal.get("_scene")
    if target is None:
        return
    charge = max(0.0, min(1.0, portal.get("charge", 1.0)))
    fx, fy = portal["x"], portal["y"]
    # EXACT emergence point in the target room (where the King stands / you walk
    # out): the dynamic world pos, falling back to the anchor tile centre.
    tp = portal.get("target_pos")
    anchor_px = tp if tp else (portal["anchor"][0] * TILE + TILE // 2,
                               portal["anchor"][1] * TILE + TILE // 2)
    formed = portal.get("formed", True)        # legacy/iso dicts read as formed
    if camera is not None and camera.pitch > 0.02:
        draw_rift_door(screen, target, anchor_px, fx, fy, camera, t,
                       formed=formed, charge=charge,
                       cache_key=("portal", id(portal)))
        return
    # Flat (pitch 0): stand the old peek panel up from the host tile.
    pulse = (0.78 + 0.22 * math.sin(t * 5.0)) * (0.5 + 0.5 * charge)
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    _gold_pool(screen, cx, cy, PORTAL_H * 0.7, pulse)
    screen.blit(_flat_peek(target, portal["anchor"], charge),
                (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
