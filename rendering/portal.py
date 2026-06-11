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
    # draw_terrain_tilted grew a 4th return (neighbor seam solids) in the
    # perf pass; the through-view only needs this room's walls + props.
    walls, solid_decos, _wall_decos, _neighbors = draw_terrain_tilted(
        buf, target, pcam)
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


def _render_through(target, anchor_px, camera, rect, door_origin,
                    loom=0.0, t=0.0, cache_key=None):
    """Return a `rect`-sized Surface showing `target` through the rift, with the
    same tilt camera as the host. CACHED per `cache_key` (id of the fold/portal)
    and BUILT ONCE -- the destination room's orientation is frozen at
    build-time yaw, like a CCTV screen showing elsewhere rather than a live
    window panning with your head. This is a deliberate canon move (the other
    room doesn't share our rotation -- eldritch) and it kills the rebuild
    spikes that fast head whips otherwise provoke (~150 ms each).

    Pitch and scale changes still invalidate (those are rare in actual play,
    and a pitch flip via F3 should genuinely repaint). Loom changes too, for
    the King's portal forming animation. Camera translation is handled by
    shifting the crop position on the cached buf, NOT by rebuilding.

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
            refresh = (entry["pitch"] != pitch_b
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
        entry = {"buf": full,
                 "pitch": pitch_b, "scale": scale_b,
                 "origin": (int(door_origin[0]), int(door_origin[1])),
                 "loom": loom_b}
        if cache_key is not None:
            _THROUGH_CACHE[cache_key] = entry
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
        entry["buf"] = full
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


def _contact_shadow(screen, p0, p1, charge):
    """The pane's ground contact: a soft dark ellipse laid ALONG the projected
    base segment (which slants with the seam's world orientation under tilt),
    not an axis-aligned smudge. Contact is what glues the frame to the floor."""
    length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    w = max(12, int(length) + 10)
    shadow = pygame.Surface((w, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, int(120 * (0.4 + 0.6 * charge))),
                        shadow.get_rect())
    ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    if abs(ang) > 0.5:
        shadow = pygame.transform.rotate(shadow, -ang)
    mx = (p0[0] + p1[0]) / 2.0
    my = (p0[1] + p1[1]) / 2.0
    screen.blit(shadow, (int(mx - shadow.get_width() / 2),
                         int(my - shadow.get_height() / 2)))



def draw_rift_throat(screen, fx, fy, camera, t, charge=1.0):
    """The RITE'S presentation of the rift family (PORTALS.md): not a
    standing pane but the ground itself opened -- a ring of gold-rimmed
    dark at world (fx, fy) that descends as a THROAT. Drawn by
    projecting a world-space circle point by point, so under the tilt
    it reads as a true ellipse on the floor plane (never a pinching
    cylinder). `charge` 0..1 is the opening ramp. Used exactly once,
    at the grove's descent fold after the rite; everything else keeps
    the anchored pane."""
    import random as _rnd
    if charge <= 0.0:
        return
    R = TILE * 1.25 * (0.25 + 0.75 * charge)
    n = 26
    rings = []
    for depth in (1.0, 0.74, 0.50, 0.28):
        pts = []
        for i in range(n):
            a = i / n * math.tau
            wx = fx + math.cos(a) * R * depth
            wy = fy + math.sin(a) * R * depth
            sx, sy = camera.project(wx, wy)
            # deeper rings sink down-screen a touch: the throat
            sy += int((1.0 - depth) * TILE * 0.55)
            pts.append((sx, sy))
        rings.append(pts)
    # The gold pool bleeding onto the ground around the mouth.
    cx, cy = camera.project(fx, fy)
    pool_r = int(R * 1.7)
    glow = pygame.Surface((pool_r * 2, pool_r * 2), pygame.SRCALPHA)
    for i in range(pool_r, 0, -3):
        a = int(40 * charge * (1 - i / pool_r))
        pygame.draw.circle(glow, (206, 178, 70, a), (pool_r, pool_r), i)
    screen.blit(glow, (cx - pool_r, cy - pool_r + 4))
    # The dark, ring by ring, descending.
    shades = ((14, 12, 16), (9, 8, 11), (5, 4, 7), (2, 2, 3))
    for pts, col in zip(rings, shades):
        pygame.draw.polygon(screen, col, pts)
    # Faint inner rims so the descent reads as stepped depth.
    for pts in rings[1:]:
        pygame.draw.polygon(screen, (52, 42, 18), pts, 1)
    # The gold rim + crackling arcs (the living wound, the rift family's
    # signature edge).
    k = max(0.4, min(1.0, charge))
    pygame.draw.polygon(screen, (int(96 * k), int(74 * k), int(24 * k)),
                        rings[0], 5)
    pygame.draw.polygon(screen, (int(150 * k), int(120 * k), int(52 * k)),
                        rings[0], 2)
    rng = _rnd.Random(int(t * 60) & 0xffff)
    for _ in range(rng.randint(3, 6)):
        i = rng.randint(0, n - 1)
        p = rings[0][i]
        q = rings[0][(i + 1) % n]
        x, y = p
        tx, ty = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(tx, ty) or 1.0
        tx /= ln; ty /= ln
        pts2 = [(x, y)]
        for _ in range(rng.randint(2, 3)):
            x += tx * rng.uniform(4, 8) + rng.uniform(-4, 4)
            y += ty * rng.uniform(4, 8) + rng.uniform(-3, 3)
            pts2.append((x, y))
        pygame.draw.lines(screen, (int(228 * k), int(196 * k), int(94 * k)),
                          False, pts2, 1)

def draw_rift_door(screen, target, anchor_px, fx, fy, camera, t,
                   formed=True, charge=1.0, cache_key=None,
                   seam_dir=None, vis=1.0):
    """The shared RIFT DOOR -- an upright black-gold pane standing on the ground
    at world (fx, fy), showing `target` (centred on the EXACT world point
    `anchor_px`) through it with the same tilt camera, framed by the living
    gold rim. Used by BOTH the King's portal AND the hidden folds so every
    rift reads as one door-passage family (KING_PROMPT). `charge`/`formed`
    drive the form-up grow + the looming King; a fold passes formed=True,
    charge=1.

    ANCHORED, not a billboard: `seam_dir` (a unit WORLD vector) is the line
    the pane stands along; its base edge is the PROJECTION of the seam's two
    world endpoints, so the frame foreshortens with the head-turn yaw and
    with where you stand, exactly like the walls do. It is a fixed object in
    the room you can circle. `vis` (0..1) is the approach-angle falloff: a
    pane seen obliquely thins and dims toward nothing (it has no back)."""
    charge = max(0.0, min(1.0, charge))
    vis = max(0.0, min(1.0, vis))
    if vis <= 0.0:
        return
    pulse = ((0.78 + 0.22 * math.sin(t * 5.0))
             * (0.5 + 0.5 * charge) * (0.35 + 0.65 * vis))
    seam_len = PORTAL_H
    bx, by = camera.project(fx, fy)
    sq = camera.ground_squash()
    growth = 0.30 + 0.70 * charge
    sdx, sdy = seam_dir if seam_dir is not None else (1.0, 0.0)
    half = seam_len * 0.5 * growth
    p0 = camera.project(fx - sdx * half, fy - sdy * half)
    p1 = camera.project(fx + sdx * half, fy + sdy * half)
    base_w = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    if base_w < 14.0:
        # Seam nearly along the view axis: hold a minimum apparent width so
        # an open rift never collapses to literally nothing on screen.
        mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        if base_w > 0.5:
            ux, uy = (p1[0] - p0[0]) / base_w, (p1[1] - p0[1]) / base_w
        else:
            ux, uy = 1.0, 0.0
        p0 = (mx - ux * 7.0, my - uy * 7.0)
        p1 = (mx + ux * 7.0, my + uy * 7.0)
        base_w = 14.0
    doorH = max(18, int(seam_len * camera.scale * (0.62 + 1.05 * sq) * growth))
    # World height projects straight up the screen (the standee/wall rule),
    # so the pane is a parallelogram: the base slants with the seam, the
    # sides stay vertical.
    quad = [p0, p1, (p1[0], p1[1] - doorH), (p0[0], p0[1] - doorH)]
    _contact_shadow(screen, p0, p1, charge)
    _gold_pool(screen, bx, by, base_w * 0.7, pulse)
    left = int(min(p0[0], p1[0]))
    top = int(min(p0[1], p1[1]) - doorH)
    rect = pygame.Rect(left, top,
                       int(max(p0[0], p1[0])) - left + 1,
                       int(max(p0[1], p1[1])) - top + 1
                       ).clip(screen.get_rect())
    if (formed or charge > 0.5) and rect.width > 2 and rect.height > 2:
        try:
            loom = 0.0 if formed else charge
            win = _render_through(target, anchor_px, camera, rect,
                                  (bx, by - doorH / 2), loom=loom, t=t,
                                  cache_key=cache_key)
            # The through-view's own desaturate already supplies the liminal
            # look; no second crush -- that turned the room into a black hole
            # the player couldn't see into. Forming rifts still ramp alpha up
            # as the tear grows; oblique approaches dim with `vis`.
            win = win.convert_alpha()
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.polygon(mask, (255, 255, 255, 255),
                                [(qx - rect.left, qy - rect.top)
                                 for qx, qy in quad])
            win.blit(mask, (0, 0),
                     special_flags=pygame.BLEND_RGBA_MULT)
            if formed:
                base_a = 255 if charge >= 0.99 else int(160 + 95 * charge)
            else:
                base_a = int(60 + 195 * (charge - 0.5) / 0.5)
            a = int(base_a * (0.25 + 0.75 * vis))
            if a < 255:
                win.fill((255, 255, 255, a),
                         special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(win, rect.topleft)
        except Exception:
            pygame.draw.polygon(screen, (10, 8, 12), quad)
    elif rect.width > 2 and rect.height > 2:
        pygame.draw.polygon(screen, (10, 8, 12), quad)      # forming: dark wound
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
        # seam_dir was fixed at tear time (across the line to the player when
        # the King tore it) -- the rift is an object in the room, not a
        # billboard that swivels to face you. The King's rift never angle-
        # fades (vis=1): his violence has no polite edge-on side.
        draw_rift_door(screen, target, anchor_px, fx, fy, camera, t,
                       formed=formed, charge=charge,
                       cache_key=("portal", id(portal)),
                       seam_dir=portal.get("seam_dir"))
        return
    # Flat (pitch 0): stand the old peek panel up from the host tile.
    pulse = (0.78 + 0.22 * math.sin(t * 5.0)) * (0.5 + 0.5 * charge)
    cx, cy = int(fx - cam_x), int(fy - cam_y)
    _gold_pool(screen, cx, cy, PORTAL_H * 0.7, pulse)
    screen.blit(_flat_peek(target, portal["anchor"], charge),
                (cx - PORTAL_W // 2, cy - PORTAL_H))
    _draw_seam(screen, (cx - PORTAL_W // 2, cy), (cx + PORTAL_W // 2, cy), t)
