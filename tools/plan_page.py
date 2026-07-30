"""THE PLAN, DRAWN -- one HTML page showing the world's geography as shapes.

The town is a string of scenes and the lost spaces are a deck of hand-drawn
corridor pieces; neither of those is a thing you can hold in your head from
reading the source. This renders both as pictures on one page: every surface
scene as a mini map read straight out of its built tile grid, and every piece
of the corridor deck at tile resolution beside what it is for.

Nothing here is drawn by hand into the page. The surface maps come from
`scenes.load_scene`, the corridor pieces from `scenes.lost_pieces`, so a page
that disagrees with the game is a page that has been regenerated after the
game changed, not a page that was written down once and rotted.

    python tools/plan_page.py [out.html]
"""
import collections
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scenes import load_scene                                  # noqa: E402
from scenes.terrain import FLOOR_DEFS, OBJECT_DEFS             # noqa: E402
from scenes import lost_pieces as LP                           # noqa: E402


# ------------------------------------------------------------ tile colours --
# The floor takes its real colour from the game's own table, so a mini map
# reads in the palette the scene actually ships in. Objects are keyed by KIND
# rather than char: a wall is a wall whether it is stone or board.
_OBJ_COLOR = {
    "stone_wall": (92, 88, 84), "wood_wall": (96, 74, 52),
    "fake_wall": (70, 66, 62), "boarded": (74, 60, 46),
    "tree": (34, 58, 40), "cornstalk": (104, 96, 46),
    "rock": (78, 76, 80), "boulder": (78, 76, 80),
    "debris": (66, 58, 52), "invisible": None,
    "window": (86, 116, 128), "counter": (110, 86, 58),
    "timber_rack": (110, 86, 58), "bed": (110, 86, 58),
    "table": (110, 86, 58), "chair": (110, 86, 58),
    "fireplace": (120, 70, 40), "stove": (90, 84, 80),
    "roof": (58, 50, 46), "bridge": (108, 88, 62),
    "door": (214, 176, 72), "outdoor_passage": (214, 176, 72),
    "void_passage": (214, 176, 72),
    "ladder_down": (214, 176, 72), "ladder_up": (214, 176, 72),
}

_PIECE_COLOR = {
    LP.WALL: (58, 54, 50), LP.OPEN: (128, 124, 116), LP.VOID: (10, 9, 14),
    LP.FIND: (198, 96, 48), LP.LIT: (252, 232, 168), LP.SHIFT: (128, 92, 176),
    LP.WARP_A: (108, 190, 190), LP.WARP_B: (108, 190, 190),
}


def _hex(c):
    return "#%02x%02x%02x" % c


def _scene_colors(sc):
    """One colour per tile, floor under objects, as a grid of hex strings."""
    grid = []
    for y in range(sc.h):
        row = []
        for x in range(sc.w):
            fch = sc.floor[y][x]
            col = FLOOR_DEFS.get(fch, {}).get("color", (24, 22, 28))
            och = sc.objects[y][x]
            d = OBJECT_DEFS.get(och)
            if d:
                oc = _OBJ_COLOR.get(d.get("kind"), (100, 96, 92))
                if oc:
                    col = oc
            row.append(_hex(tuple(col)))
        grid.append(row)
    return grid


def _svg(grid, px, pad=0, extra=""):
    """A grid of hex strings as an SVG, merging equal runs along each row.

    A 60 by 80 scene is 4800 tiles and one rect each makes a page nothing can
    open. Runs cut it by roughly ten to one and the picture is identical.
    """
    h, w = len(grid), len(grid[0])
    out = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" '
           'shape-rendering="crispEdges" class="map">'
           % (w * px, h * px, w * px + pad, h * px + pad)]
    for y, row in enumerate(grid):
        x = 0
        while x < w:
            c = row[x]
            run = 1
            while x + run < w and row[x + run] == c:
                run += 1
            out.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
                       % (x * px, y * px, run * px, px, c))
            x += run
    out.append(extra)
    out.append("</svg>")
    return "".join(out)


def _piece_svg(rows, px=9):
    grid = [[_hex(_PIECE_COLOR.get(ch, (200, 0, 200))) for ch in r]
            for r in rows]
    # mark the mouths on the border so the grammar is visible in the picture
    marks = []
    for (r, c) in LP.mouth_tiles(rows):
        marks.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" '
                     'stroke="#d6b048" stroke-width="1.2"/>'
                     % (c * px, r * px, px, px))
    return _svg(grid, px, extra="".join(marks))


# --------------------------------------------------------------- the world --
# What each surface scene IS. Facts (size, exits, what stands in it) come from
# the built scene; this is the one line about what the place is FOR, which no
# amount of reading the tile grid will tell you.
NUANCE = {
    "arrival_road": "Where the car stopped. The longest scene in the game and "
        "deliberately one way: a corridor of poles and dead crows that only "
        "goes forward, so the first thing the town does is refuse to let you "
        "leave the way you came.",
    "country_lane": "The first junction, and the first choice. Four ways: back "
        "the way you came, north to the river, west to the gravel, south into "
        "the corn. Nothing is signed.",
    "gravel_road_north": "The high road. Twelve lamps and almost nothing else; "
        "it exists to be the long walk between the river and the shops, and to "
        "put the cabin at the end of a branch you have to choose.",
    "river_road": "The river runs beside you the whole way. Carries the "
        "Preacher's remains and the way west into the clearing.",
    "river_bend": "The bridge, and the space under it. The rail is real "
        "geometry, so the hide under the span is a place you can be in and not "
        "be seen from the road.",
    "store_row": "The square. The well, the news rack, the payphone and the "
        "town sign all stand here, which makes this the one street with a "
        "reason to come back to it.",
    "chapel_row": "The church street. Everything on it is a lamp; the two yards "
        "off it carry the weight.",
    "south_row": "The sheriff on one side and the cult's camp on the other, "
        "which is the whole town in one crossing.",
    "bank_row": "The quiet street. Calder east, the boy west.",
    "lane_end": "The bottom of the town. Three households hang off it, the only "
        "street that ends in a yard rather than another street.",
    "clearing": "Off the river and off the road. The hanging figures and the "
        "hidden trunk; the one outdoor place that is dressed like an interior.",
    "backwoods_cabin": "The end of a branch. Small, off the road, and the only "
        "reason to walk the gravel north at all.",
    "cornfield_path": "Sixty tiles long and fourteen wide. A funnel with walls "
        "of corn, and the only approach to the maze.",
    "cornfield_maze": "Corn dolls and candles. The maze relocates you inside "
        "itself rather than moving you between scenes, which is the surface's "
        "one rehearsal for what the lost spaces do.",
    "lodge_yard": "The worked yard. Its treeline is the mouth that is already "
        "live: walk into the dark at the back of it and you are gone.",
    "shop_yard": "Hettie's. The worked example of the whole layer: road exit "
        "east, door across the lot, everything else authored for this "
        "household and no other.",
    "school_yard": "Old Pell's schoolhouse. His step keeps him because the "
        "building behind it can be walked into and is empty.",
    "church_yard": "Eight headstones and the bell door. The only yard where "
        "the ground itself is the content.",
    "barn_yard": "Washing on the line and the barn behind it. The journal is "
        "inside, which makes this the yard the whole first act ends in.",
    "farm_yard": "The cult's camp, in plain sight from the road. The named "
        "target for the outdoor dread pass: the corn should close the rim so "
        "the camp is not seen until you are committed to the lot.",
    "sheriff_yard": "Vane's. Fenced hardest of the eleven, which is a man "
        "telling you something without a line of dialogue.",
    "calder_yard": "Two place settings laid outside. Nobody eats there.",
    "toby_yard": "The boy's. The bear comes from here.",
    "garrick_yard": "The witness. A fuel can and no generator running.",
    "royce_yard": "Deepest grass of the eleven. Nothing has walked it in a "
        "while.",
    "pell_yard": "Thickest hedge in town, and a schoolteacher who is not in it.",
}

STREETS = ["arrival_road", "country_lane", "gravel_road_north", "river_road",
           "river_bend", "store_row", "chapel_row", "south_row", "bank_row",
           "lane_end"]
WILD = ["clearing", "backwoods_cabin", "cornfield_path", "cornfield_maze"]
YARDS = ["lodge_yard", "shop_yard", "school_yard", "church_yard", "barn_yard",
         "farm_yard", "sheriff_yard", "calder_yard", "toby_yard",
         "garrick_yard", "royce_yard", "pell_yard"]

DECK_ORDER = [
    ("The runs", ["west_run", "twin_run", "throat", "pinch"]),
    ("The turns and the junctions",
     ["bend_se", "tee_south", "cross_skew", "fork_rejoin", "hub", "comb"]),
    ("The loops", ["ring", "loop_blind", "spiral", "switchback"]),
    ("The rooms", ["gallery", "hall_cells", "haven", "collapse",
                   "deadend_find"]),
    ("The impossible ones", ["warp_pair", "pit", "moving_stair"]),
]


def _scene_card(key):
    sc = load_scene(key)
    kinds = collections.Counter(d.kind for d in sc.decorations)
    ways = []
    for ch, tgt in sorted(sc.exits.items()):
        t = tgt[0] if isinstance(tgt, (tuple, list)) else tgt
        if t != key:
            ways.append(t)
    mouths = getattr(sc, "lost_edges", None) or {}
    top = [k for k, _ in kinds.most_common(20)
           if k not in ("tall_grass", "grass_tuft", "bush", "leaves",
                        "street_lamp", "mote")][:5]
    big = max(sc.w, sc.h)
    px = 8 if big <= 26 else (5 if big <= 38 else (4 if big <= 48 else 3))
    return """<figure class="scene">
  <div class="shot">%s</div>
  <figcaption>
    <h4>%s</h4>
    <p class="dims">%d x %d tiles &middot; %d props &middot; %d way%s out%s</p>
    <p class="says">%s</p>
    <p class="holds">%s</p>
  </figcaption>
</figure>""" % (
        _svg(_scene_colors(sc), px),
        key.replace("_", " "),
        sc.w, sc.h, len(sc.decorations),
        len(ways), "" if len(ways) == 1 else "s",
        (" &middot; %d dark mouth%s" % (len(mouths),
                                        "" if len(mouths) == 1 else "s"))
        if mouths else "",
        NUANCE.get(key, ""),
        ("holds: " + ", ".join(t.replace("_", " ") for t in top))
        if top else "&nbsp;")


def _piece_card(name):
    p = LP.DECK[name]
    sig = LP.signature(p["rows"])
    sides = "NESW"
    edges = " &middot; ".join(
        "%s %s" % (sides[i], ",".join(str(s) for s in sl) or "&mdash;")
        for i, sl in enumerate(sig))
    n_or = len(set(LP.orientations(p["rows"])))
    shot = _piece_svg(p["rows"])
    # A shifting piece is not one shape, it is the shapes it takes. Drawing
    # only its home socket shows the reader a corridor with a purple block in
    # it and none of the reason the piece exists.
    sockets = LP.span_sockets(p["rows"]) if any(LP.SHIFT in r
                                                for r in p["rows"]) else []
    if len(sockets) > 1:
        shot = "".join(_piece_svg(LP.with_span_at(p["rows"], c), px=5)
                       for c in sockets)
    return """<figure class="piece">
  <div class="shot%s">%s</div>
  <figcaption>
    <h4>%s</h4>
    <p class="edges">%s &middot; %d placements</p>
    <p class="says">%s</p>
  </figcaption>
</figure>""" % (" triple" if len(sockets) > 1 else "", shot,
                name.replace("_", " "), edges, n_or, p["job"])


def _mouth_ruler():
    """The 20 tile edge with the four legal offsets marked and the centre not."""
    row = []
    for i in range(LP.SIZE):
        on = any(s <= i < s + LP.MOUTH_W for s in LP.SLOTS)
        mid = i in (9, 10)
        row.append(_hex((214, 176, 72) if on else
                        ((120, 52, 52) if mid else (58, 54, 50))))
    return _svg([row], 18)


def build(out_path):
    total_placements = sum(len(set(LP.orientations(p["rows"])))
                           for p in LP.DECK.values())
    parts = [_HEAD]

    parts.append("""
<section>
  <h2>1. Three layers, and only three</h2>
  <p>Everything the player walks is one of these. There is no town map and no
  overview: the geography lives in the exits, which is why the whole of it is
  drawn out below rather than described.</p>
  <div class="layers">
    <div class="layer l-int"><b>INTERIOR</b><span>one building, entered by its
      door. The people are in here.</span></div>
    <div class="arrow">&rarr;</div>
    <div class="layer l-yard"><b>YARD</b><span>one building's ground. Road on
      one edge, that door across the way. Never shared.</span></div>
    <div class="arrow">&rarr;</div>
    <div class="layer l-path"><b>SAFE PATH</b><span>the lit paved spine. Safe by
      its geometry, not by its lamps.</span></div>
    <div class="arrow">&harr;</div>
    <div class="layer l-lost"><b>LOST SPACE</b><span>every dark edge of the
      above. This is the part being built.</span></div>
  </div>
  <p class="fine">A yard is reached from the road and a house is reached from
  its yard, so a building is never something you walk past. It is something you
  turn off the road to find, like an island.</p>
</section>""")

    # ---- the spine, drawn -------------------------------------------------
    parts.append("""
<section>
  <h2>2. The surface, as it actually connects</h2>
  <p>Read out of the built scenes, not remembered. North at the top. A street
  is a box; the yards hanging off it are the small boxes; the line into the
  dark on every side is a mouth.</p>
  <div class="spine">""")
    SPINE = [
        ("arrival_road", ["lodge_yard"]),
        ("country_lane", []),
        ("gravel_road_north", []),
        ("store_row", ["shop_yard", "school_yard"]),
        ("chapel_row", ["church_yard", "barn_yard"]),
        ("south_row", ["sheriff_yard", "farm_yard"]),
        ("bank_row", ["toby_yard", "calder_yard"]),
        ("lane_end", ["royce_yard", "garrick_yard", "pell_yard"]),
    ]
    for street, yards in SPINE:
        parts.append('<div class="rung"><div class="street">%s</div><div '
                     'class="hooks">%s</div></div>'
                     % (street.replace("_", " "),
                        "".join('<span class="yard">%s</span>'
                                % y.replace("_", " ") for y in yards)))
    parts.append("""</div>
  <p class="fine">Off the top of that spine the river carries its own branch
  (river road, river bend, the clearing) and the corn carries the other
  (cornfield path, the maze). Twenty six outdoor scenes, every one of them
  below.</p>
</section>""")

    for title, keys, note in (
        ("The streets", STREETS,
         "The spine. Every one of these has a mouth into the dark on every "
         "side that is not a road."),
        ("The yards", YARDS,
         "Eleven households and the lodge. One building each, its resident "
         "inside it, every non road edge a mouth."),
        ("Off the road", WILD,
         "The branches. Not on the spine and not a yard: the places you only "
         "reach by turning off."),
    ):
        parts.append('<section><h3>%s</h3><p class="fine">%s</p><div '
                     'class="grid">' % (title, note))
        for k in keys:
            parts.append(_scene_card(k))
        parts.append("</div></section>")

    # ---- the lost spaces --------------------------------------------------
    parts.append("""
<section class="dark">
  <h2>3. The lost spaces: a deck, not a generator</h2>
  <p>A lost space is not one big map. It is a chain of small rooms, each one a
  scene twenty tiles square, crossed by the same seamless step the world edges
  already use: no fade, no sound, stride and screen position kept. So walking
  out of a corridor is not a load. It is a step, and the field can run forever
  without any room being bigger than the camera.</p>
  <p><b>Every shape is drawn by hand.</b> The machine picks the ORDER and
  nothing else. %d pieces are drawn today; each is legal in eight orientations,
  which is %d distinct rooms, all of them hand made shapes.</p>

  <h3>The mouth grammar</h3>
  <p>An edge is twenty tiles. A mouth is exactly two wide and starts at one of
  four offsets. The centre is not one of them, and that is the whole reason the
  corridors do not read like a video game: a passage that always arrives down
  the middle of the wall is a passage somebody laid out on graph paper.</p>
  <div class="ruler">%s</div>
  <p class="fine">Gold: the four legal offsets (3, 6, 12, 15). Red: the centre,
  which is never a mouth. The four are also closed under turning and flipping,
  so a drawn piece can be placed eight ways and every mouth still lands on a
  legal offset. <b>Two pieces mate when the edges they meet carry the same
  offsets.</b> That one rule is what respecting the geography means
  mechanically: the field can never open a corridor into a wall, and it can
  never close the way you came.</p>

  <h3>The two shift laws, running at once</h3>
  <div class="laws">
    <div class="law"><b>WATCHED</b>
      <p>The architecture moves in front of your eyes. A span slides between
      the sockets its room gives it while it is inside your sight cone. It
      never moves under you. This is the staircase that swings while you are
      looking straight at it, and which of the ways out exists is a question
      the room answers again every few seconds.</p></div>
    <div class="law"><b>DISCOVERED</b>
      <p>The field re decides what lies beyond mouths you have not crossed, and
      re decides a room you left once you are two rooms away from it. The mouth
      grammar holds, so the way back is always there. It is simply not the room
      you walked through.</p></div>
  </div>
  <p class="fine"><b>What never lies:</b> the room you are standing in, any
  room holding a fixed light, and any room where you found a person. Light is
  the field's one honest promise, which is what makes walking toward it worth
  doing.</p>
</section>""" % (len(LP.DECK), total_placements, _mouth_ruler()))

    parts.append('<section class="dark"><h3>The deck</h3><div class="key">')
    for ch, label in ((LP.WALL, "wall"), (LP.OPEN, "floor"), (LP.VOID, "void"),
                      (LP.FIND, "a find"), (LP.LIT, "fixed light"),
                      (LP.SHIFT, "shifting span"), (LP.WARP_A, "warp pane")):
        parts.append('<span><i style="background:%s"></i>%s</span>'
                     % (_hex(_PIECE_COLOR[ch]), label))
    parts.append('<span><i class="mouth"></i>mouth</span></div>')
    parts.append('<p class="fine">The deck authors SHAPE. The biome authors '
                 'MATERIAL: a wall is a wall of corn in the corn field, a stand '
                 'of trees in the forest, and a black nothing on the road.</p>')
    for title, names in DECK_ORDER:
        parts.append('<h4 class="deckhead">%s</h4><div class="grid pieces">'
                     % title)
        for n in names:
            parts.append(_piece_card(n))
        parts.append("</div>")
    parts.append("</section>")

    parts.append("""
<section>
  <h2>4. What is built, and what is next</h2>
  <table class="state">
    <tr><th>The surface geography</th><td class="done">built</td>
      <td>Twenty six outdoor scenes, eleven yards, every seam agreeing.</td></tr>
    <tr><th>The seamless step</th><td class="done">built</td>
      <td>One primitive carries world edges, folds, the maze and the fall into
        the dark. Crossing a mouth is that same step.</td></tr>
    <tr><th>The corridor deck</th><td class="done">drawn</td>
      <td>Twenty two pieces, checked in the gate: legal mouths, every floor
        tile reachable, warps paired, all eight orientations.</td></tr>
    <tr><th>Piece into scene</th><td class="next">next</td>
      <td>Turn one drawn grid plus a biome into a real room: materials, props,
        lights, and the mouths wired as exits.</td></tr>
    <tr><th>The field director</th><td class="next">next</td>
      <td>What lies beyond each mouth, what is pinned, what is allowed to
        change and when.</td></tr>
    <tr><th>The shifting span</th><td class="next">next</td>
      <td>The watched law, moving geometry with the sight cone as its
        trigger.</td></tr>
    <tr><th>The people in there</th><td class="next">next</td>
      <td>A haven holds one person, pinned the moment you find them. They are
        not Mara. She is what the field is between you and.</td></tr>
  </table>
</section>
</main></body>""")
    open(out_path, "w").write("\n".join(parts))
    return out_path


_HEAD = """<meta charset="utf-8">
<title>THRESHOLD: the geography, drawn</title>
<style>
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin:0; background:#0d0c11; color:#d8d3c8;
  font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:1180px; margin:0 auto; padding:36px 22px 90px; }
h1 { font-size:30px; letter-spacing:.14em; margin:0 0 6px; color:#e8dfc8;
  font-weight:600; }
.sub { color:#8f8878; margin:0 0 40px; letter-spacing:.04em; }
h2 { font-size:21px; color:#e0d4a8; margin:52px 0 12px;
  border-bottom:1px solid #2b2822; padding-bottom:8px; letter-spacing:.05em; }
h3 { font-size:17px; color:#cbbf98; margin:34px 0 8px; letter-spacing:.04em; }
h4 { font-size:14px; margin:0 0 3px; color:#e8dfc8; letter-spacing:.05em;
  text-transform:uppercase; }
p { margin:0 0 12px; max-width:78ch; }
.fine { color:#8b8578; font-size:13.5px; }
section.dark { background:#100e15; margin:36px -22px; padding:24px 22px 34px;
  border-top:1px solid #241f2e; border-bottom:1px solid #241f2e; }
.layers { display:flex; align-items:stretch; gap:8px; flex-wrap:wrap;
  margin:18px 0 14px; }
.layer { flex:1 1 190px; border:1px solid #333; border-radius:5px;
  padding:12px 13px; background:#141319; }
.layer b { display:block; letter-spacing:.12em; font-size:12.5px;
  margin-bottom:5px; }
.layer span { color:#928b7c; font-size:13px; }
.l-int b { color:#c98f5a; } .l-yard b { color:#8fae72; }
.l-path b { color:#d6b048; } .l-lost b { color:#9a7fc4; }
.arrow { align-self:center; color:#5a5348; }
.spine { margin:16px 0; border-left:3px solid #d6b048; padding-left:16px; }
.rung { display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  padding:5px 0; }
.street { min-width:190px; background:#1c1a22; border:1px solid #3a3547;
  border-radius:4px; padding:5px 11px; letter-spacing:.05em; color:#e0d4a8; }
.hooks { display:flex; gap:7px; flex-wrap:wrap; }
.yard { background:#161a14; border:1px solid #2f3a2a; border-radius:4px;
  padding:4px 9px; font-size:12.5px; color:#9db487; }
.grid { display:grid; gap:16px; margin:16px 0 8px;
  grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); }
.grid.pieces { grid-template-columns:repeat(auto-fill,minmax(255px,1fr)); }
figure { margin:0; background:#131218; border:1px solid #262230; border-radius:6px;
  padding:13px; display:flex; flex-direction:column; gap:10px; }
.shot { display:flex; justify-content:center; align-items:flex-start;
  background:#08070b; border-radius:4px; padding:9px; overflow:auto;
  max-height:320px; }
.shot.triple { gap:7px; }
svg.map { display:block; }
figcaption p { margin:0 0 5px; font-size:13px; }
.dims, .edges { color:#7d7768; font-size:12px; letter-spacing:.03em; }
.says { color:#c3bdae; }
.holds { color:#6f6a5e; font-size:12px; }
.laws { display:flex; gap:14px; flex-wrap:wrap; margin:14px 0; }
.law { flex:1 1 320px; background:#141319; border:1px solid #2c2738;
  border-radius:5px; padding:13px 15px; }
.law b { color:#b79ae0; letter-spacing:.12em; font-size:12.5px; }
.law p { margin:6px 0 0; font-size:13.5px; color:#a9a396; }
.ruler { margin:12px 0; overflow-x:auto; }
.key { display:flex; gap:16px; flex-wrap:wrap; margin:10px 0 4px;
  font-size:12.5px; color:#8b8578; }
.key i { display:inline-block; width:12px; height:12px; margin-right:6px;
  vertical-align:-2px; border-radius:2px; }
.key i.mouth { background:transparent; border:1.5px solid #d6b048; }
.deckhead { margin:26px 0 0; color:#9a7fc4; }
table.state { border-collapse:collapse; width:100%; margin-top:14px;
  font-size:13.5px; }
table.state th { text-align:left; padding:9px 12px 9px 0; color:#cbbf98;
  font-weight:500; white-space:nowrap; vertical-align:top;
  border-top:1px solid #262230; }
table.state td { padding:9px 12px 9px 0; color:#9a9488; vertical-align:top;
  border-top:1px solid #262230; }
td.done { color:#8fae72; letter-spacing:.08em; font-size:12px; }
td.next { color:#c98f5a; letter-spacing:.08em; font-size:12px; }
</style>
<body><main>
<h1>THRESHOLD</h1>
<p class="sub">The geography as it stands, and the plan for the part that is
not built yet. Every picture on this page is read out of the game.</p>"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/threshold_plan.html"
    print("wrote", build(out))
