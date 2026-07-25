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
        "world_h": 19.6,   # box floor at chest height on a 20-tall player
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
        "world_h": 8.4,   # three risers up to the door sill
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
        "world_h": 17.0,   # a stack you could rest a hand on, not a barricade
        "mount": "on the ground, usually against something",
        "tells": ["it is LOGS, not a mass -- the separate pieces and the "
                  "ragged ends are the whole read",
                  "courses offset by half a log as the stack settles"],
        "src": "(shape is self-evident; kept for the proportion)",
    },
    "lantern": {
        # WHAT THIS KIND IS was settled by its LIGHT DATA, not by its name.
        # FIXTURE_POOLS gives it src_z 20, arm 0, a warm flickering colour and
        # no place in _ELECTRIC_KINDS: a flame, directly over its own base, at
        # about the eye height of a 20-tall player. That is a garden post
        # lantern. It was briefly modelled as a hand-carried hurricane lantern
        # -- right name, wrong object, and a third of the height -- which is
        # why the reference now opens by naming the mount.
        "is": "A residential POST LANTERN: a tapered glass head with a peaked "
              "vented cap and a finial, sitting on top of a slim iron post "
              "with a flared foot. Burns a flame; there is no wire to it.",
        # a stock post-lantern head: 17.5in tall, 7.25in across. The head is
        # what `real` measures -- the post is a mount, and letting its length
        # into the ratio is the error the mailbox's post made first.
        "real": (7.25, 7.25, 17.5),
        "part": "head",
        "world_h": 26.0,   # wall height, flame at eye level (FIXTURE_POOLS src_z 20)
        "mount": "on top of a post about 5ft tall, so the flame lands at "
                 "roughly eye height (world z 20, which is what FIXTURE_POOLS "
                 "lights)",
        "tells": ["the head TAPERS inward toward the top -- straight sides "
                  "read as a tin can or a matchbox on a stick",
                  "the cap is a PEAK with a finial on it, not a flat lid",
                  "the head is WIDER than the post it stands on, so the "
                  "silhouette steps out at the top",
                  "astragal bars divide the glass into panes, and the lit "
                  "glass sits BEHIND them"],
        "src": "https://www.1stoplighting.com/lighting/4-11-11121-0-1276910/"
               "CWI-Lighting_Granville---1-Light-Outdoor-Post-Lantern-Head-"
               "17.5-Inches-Tall-and-6.9-Inches-Wide-0412PT7-1-101.htm",
    },
    "pickup_truck": {
        "is": "A 1980s half-ton pickup: a CAB with a roof and glass, a hood "
              "in front of it, and an open bed behind, on four wheels.",
        # a 1985 F-150 regular cab: 194 x 79 x 75in
        # 75in is the WHOLE vehicle's height, roof to road -- not the body
        # pan's. Naming a `part` here made the check compare the overall
        # height against one slab of the chassis and fail a correct model.
        "real": (194.0, 79.0, 75.0),
        "world_h": 19.7,   # roof just under the player's own height
        "mount": "on its wheels",
        "tells": ["the CAB ROOF is the thing -- an open-topped body reads as "
                  "a jeep or a flatbed, not a pickup",
                  "the bed sides are lower than the cab roof, so the "
                  "silhouette steps DOWN from front to back",
                  "the hood is lower again, so it steps down twice"],
        "src": "(period half-ton regular cab dimensions)",
    },
    "yard_fence": {
        "is": "A rural boundary fence: split cedar posts with two or three "
              "sagging wire strands. NOT chain-link, which is the filling "
              "station's and wrong for a 1994 Minnesota yard.",
        "real": (96.0, 4.0, 42.0),       # one bay, post to post
        "world_h": 15.5,   # waist high: a boundary you step over
        "mount": "posts sunk in the ground, leaning where they are old",
        "tells": ["the wire sags between posts; taut wire reads as new",
                  "posts are round or roughly split, never milled square"],
        "src": "(provenance rule, CLAUDE.md scene-dressing #1)",
    },
    "semi_truck": {
        # Royce's rig. The point of the object is that it is FULL-SIZE and
        # going nowhere: a 48ft trailer parked on a verge in a town of
        # two-storey buildings is the biggest man-made thing in Brimley, and
        # it has not moved since the week before the new year.
        "is": "A 1980s conventional semi: a long-nose tractor (hood out in "
              "front of the cab, exhaust stack behind it) coupled to a 48ft "
              "dry van trailer. Picked over since it stopped: rear doors "
              "hanging open, wheels robbed off the drive axle.",
        # the TRAILER BOX is what `real` measures -- the whole rig's length
        # would fold the tractor into the ratio and mean nothing
        "real": (576.0, 102.0, 110.0),   # 48ft x 102in x 110in van body
        "part": "trailer",
        "world_h": 33.0,   # a shade over a wall: it towers, which is the read
        "mount": "trailer deck about 48in up on its bogie; the tractor's "
                 "fifth wheel takes the nose, so the box runs level",
        "tells": ["the box is the silhouette, and it is LONG -- a short box "
                  "reads as a delivery van or a boxcar",
                  "the hood in FRONT of the cab is what makes it a "
                  "conventional rather than a cab-over",
                  "the trailer's underside is open: you see daylight between "
                  "the deck and the road, between the landing gear and the "
                  "bogie",
                  "rear doors are the full height of the box and swing on "
                  "the corners"],
        "src": "(48ft dry van + period conventional tractor dimensions)",
    },
    "seed_corn": {
        # WHAT IT HAS TO SAY comes first: it is APRIL, and these are not
        # open. A corn man with unopened seed in April is a man who has not
        # started the year, which is Old Pell's whole beat now that the
        # calendars are gone -- so the sacks must read as SEALED and STACKED,
        # never as a spilled or working heap.
        "is": "A pallet of 50lb seed-corn sacks, unopened: woven paper sacks "
              "stacked flat and squared up, ends folded and sewn, sitting on "
              "a rough wooden pallet clear of the ground.",
        "real": (30.0, 18.0, 6.0),       # one full 50lb sack, inches
        "part": "sack0",
        "world_h": 10.4,   # about knee high on a 20-tall player
        "mount": "on a pallet, so the bottom sack never touches wet ground",
        "tells": ["a full sack BULGES -- straight square sides read as "
                  "cardboard boxes",
                  "they are STACKED and squared, because nobody has started "
                  "on them; a leaning or spilled heap says the opposite",
                  "the pallet under them is the tell that they were delivered "
                  "and set down, not carried out of a shed"],
        "src": "(50lb seed sack, standard US agricultural packaging)",
    },
    "town_sign": {
        "is": "A 1960s GOOGIE roadside welcome sign, of the 1959 Welcome to "
              "Fabulous Las Vegas family: a BRIGHT cream 8x24ft panel in a "
              "coral frame, lined with light bulbs, a bulb-lit atomic "
              "STARBURST rising clear above it, a coloured band carrying the "
              "second line, a small hanging plaque for the third, and two "
              "SPLAYED steel legs. Not a weathered farm board.",
        # 288 x 96in: an 8 x 24ft panel, three sheets wide. The WIDTH is set
        # by legibility, not by taste -- see `sign_legibility()`. At 8x16 the
        # board rendered 80 x 44 screen pixels and its long line got 4.5px a
        # character, which no lettering resolves. +x is the board's WIDTH
        # (the way you read it), +y its thickness, +z its height.
        "real": (288.0, 2.0, 96.0),
        "part": "panel",   # the face + back plates together
        # A googie welcome sign is TALL on purpose -- built to be seen over
        # whatever is in front of it. The archetype stands 25ft, which here
        # is about 81 units, and Brimley's lands just under that: not for
        # grandeur, but because the panel had to grow until its lettering
        # could be read at the shipping camera.
        "world_h": 78.0,   # ~3x a wall, star included
        "mount": "held UP, the panel's bottom edge around 5ft, with the "
                 "starburst clearing the top: a googie sign is meant to be "
                 "seen over whatever is in front of it. Legs inset from the "
                 "panel's ends and splayed outward.",
        "tells": ["the STARBURST clearing the top is the silhouette; without "
                  "it the same panel is any decade's billboard",
                  "it is BRIGHT -- pale panel, saturated frame. A dark board "
                  "is a farm sign, and its lettering cannot be read at "
                  "distance against dark ground",
                  "BULBS in a row around the panel, separate points of light; "
                  "an even edge glow reads as a modern LED strip",
                  "the legs SPLAY outward. Two posts straight down is a farm "
                  "board however good the artwork is",
                  "each subordinate line gets its own coloured ground (a band, "
                  "a hung plaque) instead of sharing the main field",
                  "the back is plain, so from behind it is sheet and legs"],
        # 4x8 panel + wood post stock; 5ft is the MUTCD rural minimum to the
        # bottom of a regulatory sign, which a decorative community board
        # sits below -- it is not a traffic control device.
        "src": "https://en.wikipedia.org/wiki/"
               "Welcome_to_Fabulous_Las_Vegas_sign",
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


def check_stature(kind, asm, tol=0.16):
    """Does the prop STAND at the height the world expects?

    `check_proportion` compares a model against itself -- its own L:W:H --
    and so is completely blind to a prop built correctly at the wrong SIZE.
    A mailbox shipped 36 units tall (a wall is 26, the player is 20) with a
    perfect 2.11 : 1 : 1.22, because the exaggeration in the model's `k` got
    applied a second time to the post. From three of four facings it read as
    a bar on a stick and nothing said a word.

    So every reference records `world_h`: how tall this thing stands in the
    world, in world units, decided against the player's 20 and the wall's 26.
    That number is a design decision -- props here are drawn somewhat larger
    than life so they read at play zoom -- but it is a RECORDED one, which is
    what makes drifting off it a failure instead of a surprise.
    """
    ref = REFERENCES.get(kind)
    if not ref:
        return None
    want = ref.get("world_h")
    if want is None:
        return (f"{kind}: no `world_h` on record. Add how tall it should "
                "stand in world units (player 20, wall 26) so its SIZE is "
                "checked and not just its shape.")
    b = asm.bounds()
    got = b[5] - b[2]
    if abs(got - want) / max(want, 0.01) > tol:
        return (f"{kind}: stands {got:.1f} units tall, expected about "
                f"{want:.1f} (player 20, wall 26). Either the model is "
                "sized off the wrong scale -- a mount height must be in "
                "WORLD units, never the model's `k` -- or `world_h` is what "
                "needs updating.")


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
    # `part` may name ONE part or a GROUP of them by prefix ("head" matches
    # head_glass, head_cap, head_finial ...). What a catalogue measures is
    # rarely one primitive: a lantern head is its collar, glass, bars, cap
    # and finial together, and forcing that into a single part would mean
    # modelling it as a box -- losing the taper the reference exists to hold
    # us to.
    want_part = REFERENCES[kind].get("part")
    parts = ([p for p in asm.parts
              if p.name == want_part or p.name.startswith(want_part + "_")]
             if want_part else [])
    if want_part and not parts:
        return (f"{kind}: reference measures part {want_part!r}, which the "
                "assembly does not have (name the part that, or prefix a "
                f"group of parts {want_part + '_'!r})")
    from rendering import prim
    if parts:
        fs = [(v, n, r) for p in parts for v, n, r, _m in p.placed()]
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
