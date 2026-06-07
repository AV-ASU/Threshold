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


def draw_with_alpha(surf, alpha, fn):
    """Run draw callable `fn(target)` at the given alpha. Opaque draws go
    straight to `surf`; faded ones render to a scratch layer then blit, so
    an occluding wall can be made see-through without touching its art."""
    if alpha >= 255:
        fn(surf)
        return
    tmp = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    fn(tmp)
    tmp.set_alpha(alpha)
    surf.blit(tmp, (0, 0))


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


def draw_box(surf, cam, wx, wy, w, d, h, palette, yaw=0.0):
    """Axis-aligned box: footprint w x d on the ground, height h. Draws the
    visible vertical faces then the top, pitch-aware."""
    top, side, dark = palette["top"], palette["side"], palette["dark"]
    hw, hd = w / 2.0, d / 2.0
    # eight corners in world space
    def P(sx, sy, sz):
        # rotate footprint by object yaw about its center
        rx = sx * math.cos(yaw) - sy * math.sin(yaw)
        ry = sx * math.sin(yaw) + sy * math.cos(yaw)
        return cam.project(wx + rx, wy + ry, sz)
    ftl, ftr = P(-hw, -hd, 0), P(hw, -hd, 0)
    fbr, fbl = P(hw, hd, 0), P(-hw, hd, 0)
    ttl, ttr = P(-hw, -hd, h), P(hw, -hd, h)
    tbr, tbl = P(hw, hd, h), P(-hw, hd, h)
    # front (near, larger world-y) and the two visible sides
    pygame.draw.polygon(surf, dark, [fbl, fbr, tbr, tbl])   # near face
    pygame.draw.polygon(surf, side, [ftl, fbl, tbl, ttl])   # left
    pygame.draw.polygon(surf, side, [ftr, fbr, tbr, ttr])   # right
    pygame.draw.polygon(surf, top, [ttl, ttr, tbr, tbl])    # top
    pygame.draw.polygon(surf, _shade(top, 0.6), [ttl, ttr, tbr, tbl], 1)


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
