"""ASSEMBLIES -- a prop declared as PARTS, drawn by one central renderer.

A prop used to be a function that emitted polygons. Every one of them
re-derived face culling, draw order, shading and world-vs-screen placement,
and so every one of them got those wrong independently. The bugs were not
related to each other except in cause:

  * a box that always called +y its near face, painting its own back over
    its front at most camera headings
  * log ends pasted at a fixed pixel radius in screen space, hanging off the
    volume they were supposed to sit on
  * treads and logs painted in loop order, so the far one covered the near
  * a flag placed off `cam.yaw`, swinging around its post as the view turned

Here a prop is DATA:

    MAILBOX = Assembly(
        Part(prim.cyl(r=1.2, length=24), mat="cedar"),
        Part(prim.arch(15, 7, 4, rise=3.5), at=(0, 0, 24), mat="tin"),
        Part(prim.plate(0.6, 3, 5), at=(2, 4.2, 28), mat="flag"),
    )

and `draw()` transforms, culls, sorts and shades the lot in one place. None
of the failures above is expressible any more, because a prop no longer
decides any of it.

Being data also makes a prop CHECKABLE, which imperative pygame calls never
were: `validate()` can see a part poking outside the assembly, a part sunk
under the ground, or a part touching nothing. That is why the camera-facing
detector could not be built before and can be now.
"""
import math

from rendering import prim
from rendering.materials import MATERIALS, shade_for


class Part:
    """One primitive, placed in the assembly's local space.

    `at` moves it, `yaw` turns it about its own z, `mat` names a material.
    A part is placed in the OBJECT's space, never the camera's -- which is
    the rule the flag, the log ends and the treads all broke.
    """

    __slots__ = ("faces", "at", "yaw", "pitch", "mat", "name")

    def __init__(self, faces, at=(0.0, 0.0, 0.0), yaw=0.0, mat="wood",
                 name="", pitch=0.0):
        self.faces = faces
        self.at = at
        self.yaw = yaw
        # PITCH tips a part in its own x-z plane (about +y), which `yaw`
        # alone cannot do: yaw spins a part about the vertical, so every part
        # stayed dead upright or dead flat. Anything that LEANS -- a splayed
        # sign leg, a knee brace, a ladder, a cantilever -- had to be faked
        # out of stacked boxes or left out of the model entirely.
        self.pitch = pitch
        self.mat = mat
        self.name = name

    def placed(self):
        """This part's faces in ASSEMBLY space."""
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        ox, oy, oz = self.at
        out = []
        for verts, nrm, role in self.faces:
            vs = []
            for x, y, z in verts:
                # pitch first, in the part's own x-z, then yaw about z
                px, pz = x * cp + z * sp, -x * sp + z * cp
                vs.append((px * c - y * s + ox, px * s + y * c + oy, pz + oz))
            nx, ny, nz = nrm
            pnx, pnz = nx * cp + nz * sp, -nx * sp + nz * cp
            out.append((vs, (pnx * c - ny * s, pnx * s + ny * c, pnz), role,
                        self.mat))
        return out


class Assembly:
    """A whole prop. Built once at import; drawn many times."""

    def __init__(self, *parts, scale=1.0, shadow=0.0, overlay=None):
        self.parts = list(parts)
        self.scale = scale
        # MARKINGS ON A FACE, opt-in per prop (None = none, and every prop
        # that does not ask for one draws exactly as before). Faces carry a
        # material, which is a colour and nothing else, so anything WRITTEN
        # or painted on a prop -- lettering, a stencil, a number -- had no
        # way in and got pasted on in screen space instead, where it slides
        # off the surface it belongs to as the camera turns. An overlay is
        # handed the prop's own local->screen projector after the faces are
        # drawn, so it can put paint in the plane of the thing it is painted
        # on. See `rendering/lettering.py`.
        self.overlay = overlay
        # A CONTACT SHADOW, opt-in per prop (0 = none, and every prop that
        # does not ask for one draws exactly as before). It earns its place on
        # anything held clear of the ground -- a truck on its wheels reads as
        # floating without it -- and is wrong on something that sits flush,
        # where the prop's own dark under-face already does the job.
        self.shadow = shadow
        self._cache = None

    def faces(self):
        if self._cache is None:
            self._cache = [f for p in self.parts for f in p.placed()]
        return self._cache

    def bounds(self):
        fs = [(v, n, r) for v, n, r, _m in self.faces()]
        return prim.bounds(fs)


def draw(surf, cam, asm, wx, wy, yaw=0.0, scale=1.0, z0=0.0, tint=None):
    """Draw an assembly at world (wx, wy), turned by `yaw`.

    ONE place decides everything that used to be per-prop:

    * **culling** -- a face is drawn only if its outward normal points at
      the viewer, tested in the projected sense so it accounts for the tilt
      as well as the yaw
    * **order** -- surviving faces are sorted back to front by their centre's
      camera depth, so a near part can never be covered by a far one
    * **shading** -- from the face's role and how far up it faces, through
      the shared material table, so props sit together in one palette
    """
    import pygame
    s = scale * asm.scale
    cyw, syw = cam._cy, cam._sy
    cp, sp = cam._cp, cam._sp
    ca, sa = math.cos(yaw), math.sin(yaw)
    if asm.shadow > 0.0:
        bx0, by0, _z0b, bx1, by1, _z1b = asm.bounds()
        # the footprint's half-extent, taken as a radius so the pool does not
        # swing as the prop turns
        rad = max(bx1 - bx0, by1 - by0) * 0.5 * s * asm.shadow
        shw = max(3, int(rad * cam.scale))
        shh = max(2, int(rad * cam.ground_squash() * cam.scale))
        px, py = cam.project(wx, wy, z0)
        sh = pygame.Surface((shw * 2 + 4, shh * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 105), (2, 2, shw * 2, shh * 2))
        surf.blit(sh, (px - shw - 2, py - shh - 2))
    def toward_viewer(nx, ny, nz):
        """How squarely a local-space normal meets the viewer.

        The object's yaw turns it into world space, then the camera's yaw and
        pitch into the camera's frame: the horizontal part swung toward the
        eye, plus the vertical part the tilt lets us see. Positive is facing
        us. One definition, used for culling AND handed to the overlay, so
        paint on a face can never disagree with the face about whether it is
        visible."""
        wnx, wny = nx * ca - ny * sa, nx * sa + ny * ca
        return (-wnx * syw + wny * cyw) * cp + nz * sp

    drawn = []
    for verts, nrm, role, mat in asm.faces():
        nx, ny, nz = nrm
        toward = toward_viewer(nx, ny, nz)
        if toward <= 0.001:
            continue                        # faces away: never drawn
        pts = []
        cx = cy = cz = 0.0
        for x, y, z in verts:
            rx, ry = x * ca - y * sa, x * sa + y * ca
            px, py = wx + rx * s, wy + ry * s
            pz = z0 + z * s
            cx += px; cy += py; cz += pz
            pts.append(cam.project(px, py, pz))
        n = float(len(verts))
        drawn.append((cam.depth(cx / n, cy / n, cz / n), pts, role, mat,
                      nz, toward))
    drawn.sort(key=lambda t: t[0])
    for _d, pts, role, mat, nz, toward in drawn:
        col = shade_for(mat, role, nz, toward, tint)
        if len(pts) >= 3:
            pygame.draw.polygon(surf, col, pts)
    if asm.overlay is not None:
        def to_screen(x, y, z):
            """A point in the prop's own local space, on the screen."""
            rx, ry = x * ca - y * sa, x * sa + y * ca
            return cam.project(wx + rx * s, wy + ry * s, z0 + z * s)
        asm.overlay(surf, to_screen, toward_viewer)


def validate(asm, name="assembly"):
    """Structural checks a DATA prop makes possible. Returns a list of
    complaints; empty is good.

    These are exactly the failures that shipped before, each of which was
    invisible to any check while props were imperative draw calls."""
    out = []
    if not asm.parts:
        return [f"{name}: no parts"]
    ax0, ay0, az0, ax1, ay1, az1 = asm.bounds()
    if az0 < -0.01:
        out.append(f"{name}: geometry sinks below the ground (z={az0:.1f})")
    boxes = []
    for i, p in enumerate(asm.parts):
        fs = [(v, n, r) for v, n, r, _m in p.placed()]
        b = prim.bounds(fs)
        boxes.append(b)
        if p.mat not in MATERIALS:
            out.append(f"{name}: part {p.name or i} uses unknown material "
                       f"{p.mat!r}")
    # a part touching nothing else is a floating part -- the log ends
    # hanging off the stack, the flag adrift from its post
    if len(boxes) > 1:
        for i, b in enumerate(boxes):
            touches = False
            for j, c in enumerate(boxes):
                if i == j:
                    continue
                if (b[0] <= c[3] + 0.6 and b[3] >= c[0] - 0.6
                        and b[1] <= c[4] + 0.6 and b[4] >= c[1] - 0.6
                        and b[2] <= c[5] + 0.6 and b[5] >= c[2] - 0.6):
                    touches = True
                    break
            if not touches:
                nm = asm.parts[i].name or i
                out.append(f"{name}: part {nm} touches nothing (floating)")
    return out
