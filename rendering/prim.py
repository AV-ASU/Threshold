"""PRIMITIVES -- parametric solids, as GEOMETRY rather than as pixels.

Each builder here returns a list of FACES in the object's own local space,
and draws nothing. A face is `(verts, normal, role)`:

    verts   [(x, y, z), ...] wound counter-clockwise seen from outside
    normal  (nx, ny, nz) unit outward normal
    role    "top" / "side" / "end" / "under" -- what the material shades it as

Everything that used to be re-derived per prop -- which faces are visible,
what order they draw in, how they shade -- happens ONCE in
`rendering/assembly.py`, against these faces. That split is the whole point.
Before it, every prop emitted its own polygons and so every prop got face
culling and depth order wrong independently: a `draw_box` that always called
+y its near face and painted its own back over its front, log ends pasted in
screen space that hung off the volume they belonged to, treads painted in
loop order so the far one covered the near one. None of those are expressible
here, because a prop no longer decides any of it.

**Why the library is this wide.** The old set was four shapes (revolve, box,
billboard, log), and props got built out of whatever was closest rather than
what the object actually is -- a rural mailbox is a TUNNEL ARCH and shipped
as a rectangular prism because a prism was available. The vocabulary has to
be at least as wide as the things being modelled.

Local axes: +x is the object's LENGTH (its `yaw` points down +x), +y is
across it, +z is up. Origin is the footprint centre at z=0 unless a builder
says otherwise, so a part sits ON its own placement point.
"""
import math

# --- face roles, for the material to shade against -----------------------
TOP = "top"        # faces up
SIDE = "side"      # faces out horizontally
END = "end"        # the cut/flat ends of a length (a sawn log, a box end)
UNDER = "under"    # faces down; almost never drawn, but kept for closure


def _n(ax, ay, az):
    m = math.sqrt(ax * ax + ay * ay + az * az) or 1.0
    return (ax / m, ay / m, az / m)


def _quad(a, b, c, d, normal, role):
    return ([a, b, c, d], normal, role)


def box(w, d, h, z0=0.0):
    """A rectangular prism: `w` along x, `d` along y, rising z0 -> z0+h."""
    hw, hd = w / 2.0, d / 2.0
    z1 = z0 + h
    p = [(-hw, -hd, z0), (hw, -hd, z0), (hw, hd, z0), (-hw, hd, z0),
         (-hw, -hd, z1), (hw, -hd, z1), (hw, hd, z1), (-hw, hd, z1)]
    return [
        _quad(p[4], p[5], p[6], p[7], (0, 0, 1), TOP),
        _quad(p[3], p[2], p[1], p[0], (0, 0, -1), UNDER),
        _quad(p[0], p[1], p[5], p[4], (0, -1, 0), SIDE),
        _quad(p[2], p[3], p[7], p[6], (0, 1, 0), SIDE),
        _quad(p[1], p[2], p[6], p[5], (1, 0, 0), END),
        _quad(p[3], p[0], p[4], p[7], (-1, 0, 0), END),
    ]


def plate(w, d, t, z0=0.0):
    """A thin panel -- a sign face, a flag, a board. Just a flat box."""
    return box(w, d, t, z0)


def arch(w, d, h, rise=None, segs=8, z0=0.0):
    """A TUNNEL: flat bottom, flat vertical ends, and a barrel-vaulted top.

    `w` along x (the tunnel's length), `d` across, `h` to the springing of
    the arch, `rise` the arch's height above that (defaults to a semicircle,
    d/2). This is the Joroleman rural-mailbox form -- arched top with flat
    front, back and bottom -- which is the shape a mailbox IS, and which no
    combination of the old primitives could make.
    """
    hw, hd = w / 2.0, d / 2.0
    if rise is None:
        rise = hd
    zs = z0 + h

    def rib(x):
        """The arch outline at station x: bottom corners then the vault."""
        pts = [(x, -hd, z0), (x, -hd, zs)]
        for i in range(1, segs):
            th = math.pi * i / segs
            pts.append((x, -hd * math.cos(th), zs + rise * math.sin(th)))
        pts += [(x, hd, zs), (x, hd, z0)]
        return pts

    a, b = rib(-hw), rib(hw)
    faces = [(list(reversed(a)), (-1, 0, 0), END), (b, (1, 0, 0), END)]
    faces.append(_quad(a[0], b[0], b[-1], a[-1], (0, 0, -1), UNDER))
    for i in range(len(a) - 1):
        va, vb = a[i], a[i + 1]
        mx = (va[1] + vb[1]) / 2.0
        mz = (va[2] + vb[2]) / 2.0 - zs
        nrm = _n(0, mx, max(mz, 0.0)) if mz > 0 else _n(0, mx, 0)
        role = TOP if mz > hd * 0.35 else SIDE
        faces.append(_quad(a[i], b[i], b[i + 1], a[i + 1], nrm, role))
    return faces


def cyl(r, length, axis="z", segs=12, z0=0.0):
    """A closed cylinder. `axis` 'z' stands it up (a post, a barrel); 'x'
    lays it along the object's length (a log, a pipe, a rolled thing), in
    which case it is centred on z0 rather than rising from it."""
    faces = []
    if axis == "z":
        z1 = z0 + length
        ring0 = [(math.cos(i * math.tau / segs) * r,
                  math.sin(i * math.tau / segs) * r, z0) for i in range(segs)]
        ring1 = [(x, y, z1) for x, y, _z in ring0]
        faces.append((list(reversed(ring0)), (0, 0, -1), UNDER))
        faces.append((ring1, (0, 0, 1), TOP))
        for i in range(segs):
            j = (i + 1) % segs
            nrm = _n((ring0[i][0] + ring0[j][0]) / 2,
                     (ring0[i][1] + ring0[j][1]) / 2, 0)
            faces.append(_quad(ring0[i], ring0[j], ring1[j], ring1[i],
                               nrm, SIDE))
        return faces
    hl = length / 2.0
    ring = [(math.cos(i * math.tau / segs) * r,
             math.sin(i * math.tau / segs) * r) for i in range(segs)]
    capm = [(-hl, y, z0 + z) for y, z in ring]
    capp = [(hl, y, z0 + z) for y, z in ring]
    faces.append((list(reversed(capm)), (-1, 0, 0), END))
    faces.append((capp, (1, 0, 0), END))
    for i in range(segs):
        j = (i + 1) % segs
        my = (ring[i][0] + ring[j][0]) / 2.0
        mz = (ring[i][1] + ring[j][1]) / 2.0
        nrm = _n(0, my, mz)
        role = TOP if mz > r * 0.45 else SIDE
        faces.append(_quad(capm[i], capm[j], capp[j], capp[i], nrm, role))
    return faces


def prism(sides, r, h, z0=0.0, rot=0.0):
    """An n-sided prism: a squared post, a hex nut, a fence post."""
    z1 = z0 + h
    ring0 = [(math.cos(rot + i * math.tau / sides) * r,
              math.sin(rot + i * math.tau / sides) * r, z0)
             for i in range(sides)]
    ring1 = [(x, y, z1) for x, y, _z in ring0]
    faces = [(list(reversed(ring0)), (0, 0, -1), UNDER),
             (ring1, (0, 0, 1), TOP)]
    for i in range(sides):
        j = (i + 1) % sides
        nrm = _n((ring0[i][0] + ring0[j][0]) / 2,
                 (ring0[i][1] + ring0[j][1]) / 2, 0)
        faces.append(_quad(ring0[i], ring0[j], ring1[j], ring1[i], nrm, SIDE))
    return faces


def frustum(sides, r0, r1, h, z0=0.0, rot=0.0):
    """An n-sided TAPERED prism: `r0` at the bottom, `r1` at the top.

    The shape that keeps coming up and had no primitive, so it kept being
    built as a straight `prism` and the taper -- which is usually the whole
    identifying tell -- went missing. A lantern head tapers inward; a peaked
    cap is this with `r1=0`; a bucket, a chimney pot and a cone are all this.
    `sides=4` gives a square housing, high `sides` a smooth cone.

    A face's normal has to lean with the slope, or a tapered side lights like
    a vertical one and the model reads as a straight box after all.
    """
    z1 = z0 + h
    ring0 = [(math.cos(rot + i * math.tau / sides) * r0,
              math.sin(rot + i * math.tau / sides) * r0, z0)
             for i in range(sides)]
    ring1 = [(math.cos(rot + i * math.tau / sides) * r1,
              math.sin(rot + i * math.tau / sides) * r1, z1)
             for i in range(sides)]
    faces = [(list(reversed(ring0)), (0, 0, -1), UNDER)]
    if r1 > 1e-6:
        faces.append((ring1, (0, 0, 1), TOP))
    # how far the wall leans out of vertical: the normal's z component
    run = r0 - r1
    for i in range(sides):
        j = (i + 1) % sides
        mx = (ring0[i][0] + ring0[j][0]) / 2.0
        my = (ring0[i][1] + ring0[j][1]) / 2.0
        nrm = _n(mx * h, my * h, run * math.hypot(mx, my))
        if r1 <= 1e-6:
            # a point at the top: the quad collapses to a triangle
            faces.append(([ring0[i], ring0[j], ring1[j]], nrm, SIDE))
        else:
            faces.append(_quad(ring0[i], ring0[j], ring1[j], ring1[i],
                               nrm, SIDE))
    return faces


def _rrect(l, w, r, segs=3):
    """A rounded rectangle in x-y, as a point ring."""
    hw, hd = max(0.0, l / 2.0 - r), max(0.0, w / 2.0 - r)
    pts = []
    for cx, cy, a0 in ((hw, hd, 0.0), (-hw, hd, math.pi / 2),
                       (-hw, -hd, math.pi), (hw, -hd, 3 * math.pi / 2)):
        for i in range(segs + 1):
            a = a0 + (math.pi / 2) * (i / segs)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def pillow(l, w, h, z0=0.0, waist=0.74, segs=3):
    """A stuffed SACK: a rounded oblong that BULGES at its waist and draws
    in top and bottom, `l` along x and `w` across y.

    The shape a filled bag actually is, and the library had nothing for it.
    `frustum` looked like the answer and is RADIAL -- equal in x and y -- so
    a 30 x 18in seed sack modelled with it came out square in plan and the
    proportion check caught it at 0.89 : 1 against a real 1.67 : 1. A `box`
    is worse: crisp square sides read as a carton, which is precisely the
    mistaken identity a sack has to dodge. Also serves bedrolls, cushions,
    sandbags -- anything soft and filled.
    """
    r = min(l, w) * 0.30
    mid = _rrect(l, w, r, segs)
    end = _rrect(l * waist, w * waist, r * waist, segs)
    z1, zm = z0 + h, z0 + h * 0.5
    bot = [(x, y, z0) for x, y in end]
    belly = [(x, y, zm) for x, y in mid]
    top = [(x, y, z1) for x, y in end]
    faces = [(list(reversed(bot)), (0, 0, -1), UNDER),
             (top, (0, 0, 1), TOP)]
    for ring_a, ring_b, up in ((bot, belly, -0.45), (belly, top, 0.45)):
        for i in range(len(ring_a)):
            j = (i + 1) % len(ring_a)
            mx = (ring_a[i][0] + ring_a[j][0]) / 2.0
            my = (ring_a[i][1] + ring_a[j][1]) / 2.0
            faces.append(_quad(ring_a[i], ring_a[j], ring_b[j], ring_b[i],
                               _n(mx, my, up * max(l, w) * 0.25), SIDE))
    return faces


def star(points, r_out, r_in, thick, z0=0.0):
    """A STARBURST: a flat star standing UPRIGHT in the x-z plane, extruded
    a little way through +/-y so it has real body seen edge-on.

    The atomic star is the single most identifying shape in 1950s-60s roadside
    signage (the Welcome to Fabulous Las Vegas sign, every googie pylon), and
    nothing in the library could make one: `prism` walks a regular polygon at
    ONE radius, and a star is the alternation between two. Faked out of
    crossed boxes it reads as a plus sign.

    Unlike every other builder here this one stands UP rather than lying flat,
    because a sign's artwork faces the reader: `points` spikes around the x-z
    plane starting at the top, and the thin axis is +/-y, the way you look at
    it.
    """
    n = max(3, int(points))
    ring = []
    for i in range(n * 2):
        ang = math.pi / 2 - i * math.pi / n
        rr = r_out if i % 2 == 0 else r_in
        ring.append((math.cos(ang) * rr, math.sin(ang) * rr + z0))
    ht = thick / 2.0
    front = [(x, -ht, z) for x, z in ring]
    back = [(x, ht, z) for x, z in ring]
    faces = [(front, (0, -1, 0), SIDE),
             (list(reversed(back)), (0, 1, 0), SIDE)]
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        ax, az = ring[j][0] - ring[i][0], ring[j][1] - ring[i][1]
        # the rim's outward normal is perpendicular to the edge, in x-z
        faces.append(_quad(back[i], back[j], front[j], front[i],
                           _n(az, 0, -ax), END))
    return faces


def wedge(w, d, h, z0=0.0):
    """A ramp: full height at -x, falling to nothing at +x. Roof pitches,
    spoil slopes, a cellar door."""
    hw, hd = w / 2.0, d / 2.0
    z1 = z0 + h
    a = (-hw, -hd, z0); b = (hw, -hd, z0)
    c = (hw, hd, z0); e = (-hw, hd, z0)
    f = (-hw, -hd, z1); g = (-hw, hd, z1)
    nrm = _n(h, 0, w)
    return [
        _quad(e, c, b, a, (0, 0, -1), UNDER),
        _quad(a, b, f, f, (0, -1, 0), SIDE),
        _quad(c, e, g, g, (0, 1, 0), SIDE),
        ([e, a, f, g], (-1, 0, 0), END),
        _quad(f, b, c, g, nrm, TOP),
    ]


def revolve(profile, segs=12):
    """A body of revolution about z from `[(z, radius), ...]`, bottom up --
    the old `draw_solid` shape, kept because a barrel, a churn or a hood
    genuinely is one. Use it ONLY when the thing really is round in plan; a
    smooth body of revolution is what made a stoop read as a churn lid."""
    faces = []
    rings = []
    for z, r in profile:
        rings.append([(math.cos(i * math.tau / segs) * r,
                       math.sin(i * math.tau / segs) * r, z)
                      for i in range(segs)])
    if profile[0][1] > 0:
        faces.append((list(reversed(rings[0])), (0, 0, -1), UNDER))
    if profile[-1][1] > 0:
        faces.append((rings[-1], (0, 0, 1), TOP))
    for k in range(len(rings) - 1):
        dz = profile[k + 1][0] - profile[k][0]
        dr = profile[k + 1][1] - profile[k][1]
        for i in range(segs):
            j = (i + 1) % segs
            mx = (rings[k][i][0] + rings[k][j][0]) / 2
            my = (rings[k][i][1] + rings[k][j][1]) / 2
            nrm = _n(mx * dz, my * dz, -dr * math.hypot(mx, my))
            role = TOP if dz > 0 and abs(dr) > abs(dz) else SIDE
            faces.append(_quad(rings[k][i], rings[k][j],
                               rings[k + 1][j], rings[k + 1][i], nrm, role))
    return faces


def bounds(faces):
    """(minx, miny, minz, maxx, maxy, maxz) of a face list -- what the
    validator uses to catch a part hanging outside the thing it belongs to,
    or geometry sunk below the ground."""
    xs = [v[0] for f in faces for v in f[0]]
    ys = [v[1] for f in faces for v in f[0]]
    zs = [v[2] for f in faces for v in f[0]]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
