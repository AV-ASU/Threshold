"""Volumetric solids drawn through a Camera — PROTOTYPE kit.

Generalizes the pseudo-3D Watcher into a tiny set of reusable primitives so
"most objects" can be authored as 3D and projected through one camera:

  * draw_solid()  -- a body of revolution: stacked elliptical footprint
                     sections (a cylinder/column/figure), pitch-aware.
  * draw_box()    -- an axis-aligned crate: top face + visible side faces.
  * draw_billboard() -- the fallback: a flat sprite stood up as a
                     camera-facing card, so un-converted objects still place
                     correctly in a tilted scene.

All take a Camera and WORLD coordinates; the camera owns the tilt. Heights
are world-z (up off the ground). 100% procedural, no assets.
"""
import math
import pygame


def _shade(col, f):
    return (max(0, min(255, int(col[0] * f))),
            max(0, min(255, int(col[1] * f))),
            max(0, min(255, int(col[2] * f))))


# Scratch layers for draw_with_alpha, pooled so the hot faded-draw path stops
# allocating (and zero-filling) a fresh screen-sized SRCALPHA surface per call.
# A small pool (not a single slot) keeps re-entrant fns safe: an inner
# draw_with_alpha simply takes the next surface.
_SCRATCH_POOL = []
_SCRATCH_POOL_CAP = 4


def draw_with_alpha(surf, alpha, fn, rect=None):
    """Run draw callable `fn(target)` at the given alpha. Opaque draws go
    straight to `surf`; faded ones render to a scratch layer then blit, so
    an occluding wall can be made see-through without touching its art.

    `rect` (optional) is a screen-space bound on what `fn` draws. When given,
    only that region of the scratch is cleared + blitted back (the clip keeps
    fn inside it), which turns a full-screen alpha composite into a small one
    -- the difference between ~2.5ms and ~0.05ms per faded wall/actor."""
    if alpha >= 255:
        fn(surf)
        return
    size = surf.get_size()
    tmp = None
    for i, s in enumerate(_SCRATCH_POOL):
        if s.get_size() == size:
            tmp = _SCRATCH_POOL.pop(i)
            break
    if tmp is None:
        # stale sizes (a render-scale change) would otherwise pin the pool
        _SCRATCH_POOL[:] = [s for s in _SCRATCH_POOL if s.get_size() == size]
        tmp = pygame.Surface(size, pygame.SRCALPHA)
        # freshly created -> already transparent; skip the clearing fill
        if rect is None:
            fn(tmp)
            tmp.set_alpha(alpha)
            surf.blit(tmp, (0, 0))
            if len(_SCRATCH_POOL) < _SCRATCH_POOL_CAP:
                _SCRATCH_POOL.append(tmp)
            return
    if rect is not None:
        r = pygame.Rect(rect).clip(tmp.get_rect())
        if r.width <= 0 or r.height <= 0:
            if len(_SCRATCH_POOL) < _SCRATCH_POOL_CAP:
                _SCRATCH_POOL.append(tmp)
            return
        tmp.fill((0, 0, 0, 0), r)
        tmp.set_clip(r)
        fn(tmp)
        tmp.set_clip(None)
        tmp.set_alpha(alpha)
        surf.blit(tmp, r.topleft, r)
    else:
        tmp.fill((0, 0, 0, 0))
        fn(tmp)
        tmp.set_alpha(alpha)
        surf.blit(tmp, (0, 0))
    if len(_SCRATCH_POOL) < _SCRATCH_POOL_CAP:
        _SCRATCH_POOL.append(tmp)


def draw_solid(surf, cam, wx, wy, sections, palette, t=0.0, yaw=0.0,
               bob=0.0):
    """Body of revolution at ground point (wx, wy).

    `sections` = list of (height_z, radius_x, radius_y) up the body, where
    radius_x/y are the footprint (ground) ellipse semi-axes at that height.
    `palette` = dict(body=, lo=, rim=). Drawn pitch-aware via `cam`.
    """
    cp = cam.ground_squash()              # footprint vertical flatten
    body, lo, rim = palette["body"], palette["lo"], palette["rim"]

    # The footprint-yaw angle is the same for every section of one body, so its
    # cos/sin are hoisted out of the ring loop (this runs for every wall/tree/
    # prop section in the tilted town -- it was the hottest inner loop).
    a = yaw + cam.yaw
    ca, sa = math.cos(a), math.sin(a)

    # Precompute each section's screen ring: center, and on-screen x extent.
    rings = []
    for (hz, rx, ry) in sections:
        cx, cy = cam.project(wx, wy, hz + bob)
        # effective on-screen half-width of an elliptical footprint after the
        # camera's own yaw (broad side-on, thin head-on); reuse object yaw too.
        half = math.hypot(rx * ca, ry * sa) * cam.scale
        ydep = ry * cp * cam.scale        # how deep the footprint reads down
        rings.append((cx, cy, half, ydep, hz, rx, ry))

    # Body fill: a tapered polygon from the silhouette edges, base->crown.
    left = [(cx - half, cy) for (cx, cy, half, _d, *_r) in rings]
    right = [(cx + half, cy) for (cx, cy, half, _d, *_r) in rings]
    poly = right + left[::-1]
    if len(poly) >= 3:
        pygame.draw.polygon(surf, body, poly)
        pygame.draw.polygon(surf, lo, poly, 1)

    # Footprint ellipse at the base (the part touching the floor) and a top cap
    # so the form reads as round, not flat -- both squashed by pitch.
    bcx, bcy, bhalf, bdep, *_ = rings[0]
    if bdep > 0.5:
        pygame.draw.ellipse(surf, lo,
                            (bcx - bhalf, bcy - bdep, 2 * bhalf, 2 * bdep), 1)
    tcx, tcy, thalf, tdep, *_ = rings[-1]
    if tdep > 0.5 and thalf > 1:
        pygame.draw.ellipse(surf, _shade(body, 1.25),
                            (tcx - thalf, tcy - tdep, 2 * thalf, 2 * tdep))

    # Rim light down the lit side (light from front-left in world space).
    lit_right = math.cos(yaw + cam.yaw + 0.6) > 0
    edge = right if lit_right else left
    if len(edge) >= 2:
        pygame.draw.lines(surf, rim, False, edge, 1)


def draw_box(surf, cam, wx, wy, w, d, h, palette, yaw=0.0, z0=0.0):
    """Axis-aligned box: footprint w x d, rising from `z0` to `z0 + h`. Draws
    the visible vertical faces then the top, pitch-aware.

    `z0` is what lets a box be STACKED. Without it every box sat on the
    ground, which is how the woodpile's courses all ended up in one layer
    while their drawn log-ends floated at the heights they should have been
    at."""
    top, side, dark = palette["top"], palette["side"], palette["dark"]
    hw, hd = w / 2.0, d / 2.0
    # eight corners in world space
    def P(sx, sy, sz):
        # rotate footprint by object yaw about its center
        rx = sx * math.cos(yaw) - sy * math.sin(yaw)
        ry = sx * math.sin(yaw) + sy * math.cos(yaw)
        return cam.project(wx + rx, wy + ry, sz)
    # WHICH faces are drawn is decided by the CAMERA, not by a fixed world
    # axis. The original picked "near, left, right" from the +y face outward
    # and drew them unconditionally, which is only correct while the camera
    # looks down -y: at other headings it painted the box's BACK over its
    # front and left the real front undrawn, so you saw a concave scoop into
    # the inside of it. Visible on every box prop -- the mailbox and the
    # stoop both showed it -- and it is why a woodpile could not be stacked
    # out of boxes at all.
    # A box is convex, so its visible vertical faces never overlap each
    # other and can be drawn in any order; the top goes last.
    cy_, sy_ = cam._cy, cam._sy
    corners = ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))
    for i in range(4):
        ax, ay = corners[i]
        bx, by = corners[(i + 1) % 4]
        # outward normal of this face, rotated into world by the object yaw
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        nx = mx * math.cos(yaw) - my * math.sin(yaw)
        ny = mx * math.sin(yaw) + my * math.cos(yaw)
        if (-nx * sy_ + ny * cy_) <= 0.0:
            continue                       # faces away: never drawn
        # the face pointing most toward the viewer reads as the shaded near
        # side, the others as flanks
        quad = [P(ax, ay, z0), P(bx, by, z0),
                P(bx, by, z0 + h), P(ax, ay, z0 + h)]
        near = (-nx * sy_ + ny * cy_) > (abs(nx) + abs(ny)) * 0.5
        pygame.draw.polygon(surf, dark if near else side, quad)
    ttl, ttr = P(-hw, -hd, z0 + h), P(hw, -hd, z0 + h)
    tbr, tbl = P(hw, hd, z0 + h), P(-hw, hd, z0 + h)
    pygame.draw.polygon(surf, top, [ttl, ttr, tbr, tbl])    # top
    pygame.draw.polygon(surf, _shade(top, 0.6), [ttl, ttr, tbr, tbl], 1)


def draw_log(surf, cam, wx, wy, wz, yaw, length, radius, palette, seed=0):
    """ONE split log lying horizontally: a real closed cylinder with sawn end
    caps, centred at (wx, wy, wz) and running along `yaw`.

    A log is its own object, and a woodpile is a stack of these -- which is
    the only way the stack can occlude honestly. Building the pile out of
    `draw_box` instead could not work: that primitive paints all four of its
    vertical faces unconditionally and always treats +y as the near one, so
    at most camera headings it draws its own BACK faces over its front and
    you see inside it.

    Here only the surface facing the camera is drawn. The barrel is swept as
    quads around the cross-section, each kept or dropped by whether its
    outward normal points at the viewer, and each end cap is drawn only when
    that end faces us. `palette` = dict(bark=, bark_lo=, cut=).
    """
    bark, bark_lo = palette["bark"], palette["bark_lo"]
    cut = palette["cut"]
    ca, sa = math.cos(yaw), math.sin(yaw)
    # the cross-section's two basis vectors: across the log, and up
    axx, axy = -sa, ca
    half = length / 2.0
    # camera-facing test for a horizontal outward normal, as used elsewhere
    cy_, sy_ = cam._cy, cam._sy
    N = 12

    def _pt(th, end):
        """A point on the rim at angle `th`, at the +/- end of the log."""
        c, sn = math.cos(th), math.sin(th)
        ox, oy = axx * c * radius, axy * c * radius
        return cam.project(wx + ca * half * end + ox,
                           wy + sa * half * end + oy,
                           wz + sn * radius)

    # THE BARREL, back to front so the lit crown lands over the shaded belly
    segs = []
    for i in range(N):
        th0 = i * math.tau / N
        th1 = (i + 1) * math.tau / N
        thm = (th0 + th1) / 2.0
        # outward normal of this strip, in world terms
        nx = axx * math.cos(thm)
        ny = axy * math.cos(thm)
        nz = math.sin(thm)
        # a strip is visible if it faces the camera horizontally OR faces up
        toward = (-nx * sy_ + ny * cy_)
        vis = toward * cam._cp + nz * cam._sp
        if vis <= 0.0:
            continue
        segs.append((vis, th0, th1, nz))
    segs.sort(key=lambda t: t[0])
    for vis, th0, th1, nz in segs:
        # crown lit, belly dark: shade by how far up the strip faces
        f = 0.70 + 0.45 * max(0.0, nz)
        col = _shade(bark if nz > -0.2 else bark_lo, f)
        pygame.draw.polygon(surf, col, [_pt(th0, -1), _pt(th1, -1),
                                        _pt(th1, 1), _pt(th0, 1)])
    # THE SAWN ENDS, each only while it faces us
    for end in (1.0, -1.0):
        nx, ny = ca * end, sa * end
        if (-nx * sy_ + ny * cy_) <= 0.02:
            continue
        rim = [_pt(i * math.tau / N, end) for i in range(N)]
        pygame.draw.polygon(surf, _shade(cut, 1.0 - (seed % 5) * 0.06), rim)
        pygame.draw.polygon(surf, _shade(bark, 0.65), rim, 1)


def draw_billboard(surf, cam, wx, wy, sprite, h_anchor=1.0):
    """Fallback: place a flat pre-drawn `sprite` Surface as a camera-facing
    card whose BASE sits on the ground at (wx, wy). `h_anchor` is the fraction
    of the sprite height that hangs above the base (1.0 = whole sprite stands
    up). The card always faces the camera, so it reads correctly under tilt
    even though it has no real depth."""
    sw, sh = sprite.get_size()
    # base on the ground; the card rises by sprite height * the camera's
    # height_rise so it foreshortens consistently with real solids.
    bx, by = cam.project(wx, wy, 0.0)
    rise = sh * h_anchor * (0.4 + 0.6 * cam.ground_squash())  # squash standee
    top_y = int(by - rise)
    surf.blit(sprite, (int(bx - sw / 2), top_y))
