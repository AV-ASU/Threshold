"""REFERENCES -- what a prop is supposed to BE, recorded before it is built.

The maintainer's diagnosis, and it is right: the best-looking thing in this
project is the googie filling-station sign, and it is the only prop that was
built from a reference handed over first. Everything built from my own
description of it went round five revisions.

**Why this is text and not a folder of photographs.** Downloading reference
images is blocked by this environment's egress policy (the proxy answers 403
to CONNECT and its own README says report that rather than route around it).
Web SEARCH works, though, and it turns out to carry most of the value: what a
photo fixes is SHAPE LANGUAGE and PROPORTION, and both of those are written
down somewhere. The Joroleman mailbox is "a tunnel with an arched top and
flat front, back and bottom", 23 3/16 x 11 x 13 3/8 inches. That is the
reference. It caught a prop that had shipped as a rectangular prism at the
wrong ratio, without a single pixel being fetched.

It also keeps the tree clean: no third-party images with unclear licensing
sitting in a repo, just facts and the URL they came from.

**The workflow.** Before building or reworking a prop: search for it, write
its entry here, then build the assembly against the entry. `real` is the
object's true dimensions in inches; `proportion()` turns that into the
length:width:height ratio the model must hold, whatever tile scale it ends up
at. The preview sheet prints the entry beside the render, so a wrong
proportion is visible at the moment of judging rather than three revisions
later.

A maintainer-supplied image always wins over anything in here. This is the
fallback for when nobody has handed one over.
"""

# `real` is (along +x, across +y, up +z) IN THE MODEL'S OWN LOCAL AXES, which
# is not always how a catalogue quotes it. A stoop is sold as "48 inches
# wide" but its +x is the direction you CLIMB, so its entry reads (22, 48,
# 14). Getting that backwards is not a cosmetic slip: it silently inverts the
# ratio the check compares against, and the check then passes a prop that is
# rotated ninety degrees from the real object.
#
# `part` names which PART of the assembly carries those dimensions, where the
# assembly is more than the object -- a mailbox reference describes the BOX,
# and comparing it against bounds that include the post is meaningless.
REFERENCES = {
    "mailbox": {
        "is": "Joroleman rural mailbox, the 1915 US design still standard in "
              "1994: a TUNNEL -- arched top with flat front, back and bottom "
              "-- on a wooden post, with a small signal flag on one flank.",
        "real": (23.2, 11.0, 13.4),      # No. 2 size, inches
        "part": "box",
        "mount": "box floor 41-45in above the road, so the post is about "
                 "three times the box's own height",
        "tells": ["the arch is the silhouette; a rectangular box reads as a "
                  "toolbox or a birdhouse",
                  "the flag is on the FLANK, near the door end",
                  "door hinges at the bottom of the road-facing end"],
        "src": "https://99percentinvisible.org/article/"
               "open-source-icon-rural-americas-classic-metal-mailbox-"
               "with-flag-design/",
    },
    "stoop": {
        # REWRITTEN once the first model was judged and found wanting: it was
        # two treads and no LANDING, which is a flight of steps, not a stoop.
        # A stoop is the platform at the door, with steps coming off it -- the
        # landing is the object and the steps are its approach.
        "is": "A front stoop: a timber LANDING at the house door, at least "
              "36in deep and wider than the door, with two or three steps "
              "coming down off it. Side cheeks close the ends.",
        # 60in is the WIDTH, across (+y); +x is the direction you climb,
        # which is the landing depth plus the run of the steps
        "real": (60.0, 60.0, 21.0),      # 36in landing + 2 runs, 3 risers
        "mount": "the landing's top sits just below the interior threshold, "
                 "so the door can swing clear of it",
        "tells": ["the LANDING is what makes it a stoop; steps alone are a "
                  "flight and read as slabs stacked on grass",
                  "6-7in rise to 11-12in run; wider than the door by a foot "
                  "each side",
                  "the tread overhangs its riser (the nosing), and that "
                  "shadow line is what reads as a step at distance",
                  "side cheeks enclose the step ends, so you never see the "
                  "treads floating"],
        "src": "https://www.gardenista.com/posts/hardscaping-101-"
               "the-front-stoop/",
    },
    "woodpile": {
        "is": "A stack of split firewood against a wall or fence, ends OUT. "
              "The logs lie across the stack, so the stack's long axis is "
              "the wall it runs along and its depth is one log's length.",
        "real": (48.0, 16.0, 30.0),      # 4ft high, 8ft long, 16in logs
        "mount": "on the ground, usually against something",
        "tells": ["it is LOGS, not a mass -- the separate pieces and the "
                  "ragged ends are the whole read",
                  "courses offset by half a log as the stack settles"],
        "src": "(shape is self-evident; kept for the proportion)",
    },
    "yard_fence": {
        "is": "A rural boundary fence: split cedar posts with two or three "
              "sagging wire strands. NOT chain-link, which is the filling "
              "station's and wrong for a 1994 Minnesota yard.",
        "real": (96.0, 4.0, 42.0),       # one bay, post to post
        "mount": "posts sunk in the ground, leaning where they are old",
        "tells": ["the wire sags between posts; taut wire reads as new",
                  "posts are round or roughly split, never milled square"],
        "src": "(provenance rule, CLAUDE.md scene-dressing #1)",
    },
}


def get(kind):
    return REFERENCES.get(kind)


def proportion(kind):
    """(length, width, height) normalised so width == 1.0.

    The ratio is what a model has to hold; the absolute size is whatever the
    scene needs. Checking the ratio is how a mailbox at 1.76 : 1 : 1.06 gets
    caught against a real one at 2.11 : 1 : 1.22."""
    r = REFERENCES.get(kind, {}).get("real")
    if not r:
        return None
    l, w, h = r
    return (l / w, 1.0, h / w)


def check_proportion(kind, asm, tol=0.22):
    """Compare an assembly's actual L:W:H against the reference's.

    Returns a complaint or None. This is the check that a data prop makes
    possible and an imperative one never did, and it earns its keep: it
    caught a mailbox at 1.98 : 1 : 4.45 (measuring the post along with the
    box), a stoop whose reference axes were quoted the way a catalogue quotes
    them and so was compared ninety degrees out, and a woodpile modelled with
    its logs along the stack instead of across it -- all before anything was
    rendered."""
    ref = proportion(kind)
    if ref is None:
        return f"{kind}: no reference on record to check against"
    want_part = REFERENCES[kind].get("part")
    parts = [p for p in asm.parts if p.name == want_part] if want_part else []
    if want_part and not parts:
        return (f"{kind}: reference measures part {want_part!r}, which the "
                "assembly does not have")
    from rendering import prim
    if parts:
        fs = [(v, n, r) for v, n, r, _m in parts[0].placed()]
        b = prim.bounds(fs)
    else:
        b = asm.bounds()
    L, W, H = b[3] - b[0], b[4] - b[1], b[5] - b[2]
    if W <= 0:
        return f"{kind}: zero width"
    got = (L / W, 1.0, H / W)
    dl = abs(got[0] - ref[0]) / max(ref[0], 0.01)
    dh = abs(got[2] - ref[2]) / max(ref[2], 0.01)
    if dl > tol or dh > tol:
        return (f"{kind}: proportion {got[0]:.2f} : 1 : {got[2]:.2f} against "
                f"reference {ref[0]:.2f} : 1 : {ref[2]:.2f}"
                + (f" (measuring part {want_part!r})" if want_part else ""))
    return None


def describe(kind, width=64):
    """The entry as lines, for printing beside a render."""
    e = REFERENCES.get(kind)
    if not e:
        return [f"{kind}: NO REFERENCE ON RECORD -- search for one and add it",
                "  (rendering/references.py; a prop built from memory is how"]
    import textwrap
    out = []
    out += textwrap.wrap(e["is"], width)
    p = proportion(kind)
    if p:
        out.append(f"proportion L:W:H = {p[0]:.2f} : 1 : {p[2]:.2f}")
    if e.get("mount"):
        out += textwrap.wrap("mount: " + e["mount"], width)
    for t in e.get("tells", []):
        out += textwrap.wrap("- " + t, width)
    return out
