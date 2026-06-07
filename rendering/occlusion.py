"""Wall / occluder fade — keep the player (and other focus actors) visible when
a solid swings between them and the tilted camera.

At an oblique pitch with a rotating yaw, any wall, column or crate nearer the
camera than the player will paint over them. The fix used by virtually every
3D-ish iso game: detect occluders that (a) are nearer the camera than the
focus actor AND (b) cover the focus actor on screen, and fade them toward
transparent so the actor reads through.

The overlap test is done in SCREEN space against the occluder's projected
vertical extent (base..top), because at an oblique pitch a tall wall's body
projects well above its ground tile and would be missed by a ground-distance
test. Pure math, no assets.
"""
import math


def _screen_span(cam, wx, wy, h, half_w):
    """Approx screen bounding box of a solid at ground (wx, wy), height `h`,
    ground half-width `half_w`. Samples the base and top so the vertical rise
    from the oblique pitch is captured. Returns (xmin, xmax, ymin, ymax)."""
    bx, by = cam.project(wx, wy, 0.0)
    tx, ty = cam.project(wx, wy, h)
    sw = half_w * cam.scale
    xmin = min(bx, tx) - sw
    xmax = max(bx, tx) + sw
    ymin = min(by, ty)
    ymax = max(by, ty)
    return xmin, xmax, ymin, ymax


def focus_occ_data(cam, px, py, ph, p_halfw=8):
    """Precompute a focus actor's (ground depth, screen box) so a whole wall
    list can be tested against it without recomputing the actor's projection
    for every wall. Pairs with occluder_alpha_box below."""
    return cam.depth(px, py), _screen_span(cam, px, py, ph, p_halfw)


def occluder_alpha_box(o_depth, o_span, p_depth, p_span,
                       floor_alpha=60, feather=10):
    """occluder_alpha with the occluder's depth + screen box and the actor's
    precomputed (depth, box) already in hand -- identical math, just no repeated
    projection. The actor data comes from focus_occ_data()."""
    if o_depth <= p_depth:
        return 255
    oxn, oxx, oyn, oyx = o_span
    pxn, pxx, pyn, pyx = p_span
    ox_ov = min(oxx, pxx) - max(oxn, pxn)
    oy_ov = min(oyx, pyx) - max(oyn, pyn)
    if ox_ov <= -feather or oy_ov <= -feather:
        return 255
    p_w = max(1.0, pxx - pxn)
    cover_x = max(0.0, min(1.0, (ox_ov + feather) / (p_w + feather)))
    cover_y = max(0.0, min(1.0, (oy_ov + feather) / feather)) if oy_ov < feather else 1.0
    return int(255 - (255 - floor_alpha) * cover_x * cover_y)


def occluder_alpha(cam, ox, oy, oh, px, py, ph,
                   o_halfw=14, p_halfw=8, floor_alpha=60, feather=10):
    """Alpha (0..255) to draw an occluder at ground (ox, oy), height `oh`,
    given a focus actor at (px, py), height `ph`.

    255 = fully opaque (not occluding). Lower = faded so the actor shows
    through. The fade scales with how much of the actor the occluder covers,
    with a `feather` band so walls ease rather than pop."""
    # Only things NEARER the camera than the actor can occlude it.
    if cam.depth(ox, oy) <= cam.depth(px, py):
        return 255
    oxn, oxx, oyn, oyx = _screen_span(cam, ox, oy, oh, o_halfw)
    pxn, pxx, pyn, pyx = _screen_span(cam, px, py, ph, p_halfw)
    # horizontal + vertical overlap of the two screen boxes
    ox_ov = min(oxx, pxx) - max(oxn, pxn)
    oy_ov = min(oyx, pyx) - max(oyn, pyn)
    if ox_ov <= -feather or oy_ov <= -feather:
        return 255
    # coverage 0..1: how deep into the actor's box the occluder reaches,
    # feathered at the edges so it eases in/out.
    p_w = max(1.0, pxx - pxn)
    cover_x = max(0.0, min(1.0, (ox_ov + feather) / (p_w + feather)))
    cover_y = max(0.0, min(1.0, (oy_ov + feather) / feather)) if oy_ov < feather else 1.0
    cover = cover_x * cover_y
    return int(255 - (255 - floor_alpha) * cover)
