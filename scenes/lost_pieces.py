"""THE CORRIDOR DECK -- the hand-drawn pieces the lost spaces are built from.

Every shape in here was drawn by hand, tile by tile. Nothing in this file is
generated and nothing in it ever will be: the maintainer's ruling is that the
GEOMETRY is authored and only the ORDER is chosen at runtime. A piece is a
20x20 block with mouths on its edges; the field director picks which piece
lies beyond a mouth, and that is the whole of what the machine decides.

WHY 20x20. A lost space is not one big map. It is a chain of small rooms, each
its own scene, crossed through `Game.cross_fold` (the seamless primitive: no
fade, no sting, stride and screen position preserved). So walking out of a
mouth is not a load, it is a step, and the field can go on forever without any
scene ever being bigger than what fits in the camera window.

THE MOUTH GRAMMAR. An edge is 20 tiles. A mouth is exactly 2 tiles wide and
starts at one of four offsets:

    3      6            12      15
    |      |            |       |
    ##ooo##oo###########oo##oo###      (schematic)
              ^^^^^^^^^
              the centre, which is never a mouth

The centre (9, 10) is deliberately excluded. A corridor that always arrives
down the middle of the wall reads as a corridor in a video game; one that
arrives off to one side reads as a place. The four offsets are also closed
under rotation and mirroring (3 <-> 15, 6 <-> 12), so a hand-drawn piece can
be turned or flipped into 8 orientations and every mouth still lands on a
legal offset. Twenty drawn pieces is 160 placements, all of them hand-made
shapes.

TWO PIECES MATE when the edges they meet carry the SAME set of offsets. That
single rule is what "respect the geography" means mechanically: the field can
never open a corridor that runs into a wall, and it can never close the way
you came.

THE CHARACTER SET. The deck authors SHAPE. The biome authors MATERIAL: a `#`
is a wall of corn in the corn field, a stand of trees in the forest, and a
black nothing on the road.

    #   wall            .   open floor
    @   void            the black. Not a wall, not a floor: the ground has
                        fallen away. You can see across it and never cross it.
    *   a find          something is here: a body, a light, a left thing
    ~   a fixed light   lit ground. Lit ground NEVER shifts (the field's one
                        honest promise, and the reason light is worth walking
                        toward)
    S   a shifting      a segment that MOVES WHILE YOU WATCH between the
        segment         sockets its piece gives it. It never moves under you.
    > < a warp pair     two panes in one piece with no floor between them.
                        Step into one, stride out of the other.

THE TWO SHIFT LAWS, and they run at the same time:

  * WATCHED   the architecture moves in front of your eyes. `S` segments slide
              between sockets while they are inside your sight cone and you
              are not standing on them. This is the staircase that swings
              while you are looking straight at it.
  * DISCOVERED  the field re-decides what lies beyond mouths you have not
              crossed, and re-decides a piece you left once you are two
              pieces away from it. The mouth grammar holds, so the way back
              is always there. It is simply not the room you walked through.

What is PINNED and never lies: the piece you are standing in, any piece
holding a fixed light, and any piece where you found a person.
"""

# The four legal mouth offsets. Closed under rotate/mirror (3<->15, 6<->12);
# the centre pair (9, 10) is excluded on purpose.
SLOTS = (3, 6, 12, 15)
MOUTH_W = 2          # tiles: a mouth is always exactly this wide
SIZE = 20            # tiles: a piece is always this square

WALL = "#"
OPEN = "."
VOID = "@"
FIND = "*"
LIT = "~"
SHIFT = "S"
WARP_A = ">"
WARP_B = "<"

# everything a body can stand on
_WALKABLE = set(OPEN + FIND + LIT + SHIFT + WARP_A + WARP_B)


# ============================================================ THE DECK ======
# Each entry: rows (20 strings of 20), and the JOB it does in a field. The job
# is why the piece exists; a piece that does the same job as another one is a
# piece that should have been a rotation of it.

DECK = {}


def _piece(name, job, rows):
    DECK[name] = {"name": name, "job": job, "rows": tuple(rows)}


# ---- the runs -------------------------------------------------------------

_piece("west_run", "A straight run that is not straight: it holds one side of "
       "the piece and swells halfway along, so a corridor you have walked "
       "twice still does not read as a copy.", [
    "######..############",
    "######..############",
    "#####...############",
    "#####...############",
    "####....############",
    "####....############",
    "####....############",
    "#####...############",
    "#####...############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
])

_piece("twin_run", "Two corridors sharing a piece and never touching. One of "
       "them widens and the other does not, so the choice you think you made "
       "at the last junction stays felt.", [
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "##...##########..###",
    "##...##########..###",
    "##...##########..###",
    "##...##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
])

_piece("throat", "A room that narrows to a corridor. Walked one way it funnels "
       "you; walked the other it opens out, and the same piece is a different "
       "place depending on which mouth you came in by.", [
    "####################",
    "####################",
    "####........########",
    "............########",
    "............########",
    "####........########",
    "####................",
    "####................",
    "####........########",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("pinch", "A squeeze. The corridor opens into a bulge and then closes to "
       "a single tile, so you go through it sideways and you cannot turn round "
       "in it.", [
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "##########....######",
    "##########....######",
    "##########....######",
    "############.#######",
    "############.#######",
    "############.#######",
    "############.#######",
    "############.#######",
    "############.#######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
])

# ---- the turns and the junctions ------------------------------------------

_piece("bend_se", "A turn with a stub. The corner is honest; the short spur "
       "off it is not a way anywhere, it is a place something was left.", [
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######........######",
    "######.......*######",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..............",
    "######..............",
    "####################",
    "####################",
    "####################",
])

_piece("tee_south", "A hall crossed by one spur going the other way. The spur "
       "leaves off-centre, so from either end of the hall it is behind you "
       "before you see it.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "....................",
    "....................",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
])

_piece("cross_skew", "A crossroads whose four arms do not line up. You walk "
       "into a chamber, and the way out on the far side is not where the way "
       "in put you. Two pillars keep you from seeing all four at once.", [
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..............",
    "######..............",
    "######........######",
    "######...#....######",
    "######....#...######",
    "######........######",
    "..............######",
    "..............######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
])

_piece("fork_rejoin", "A fork where both ways get there. One of them passes "
       "something and the other does not, and nothing tells you which is "
       "which until you have picked.", [
    "####################",
    "####################",
    "####################",
    "#####....*.....#####",
    "#####..........#####",
    "#####..######..#####",
    ".......######.......",
    ".......######.......",
    "#####..######..#####",
    "#####..######..#####",
    "#####..........#####",
    "#####..........#####",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("hub", "An open junction with four ways out, all at different offsets, "
       "and pillars set so that no standing spot in the room shows you more "
       "than two of them.", [
    "###############..###",
    "###############..###",
    "###############..###",
    "###.................",
    "###.................",
    "###..............###",
    "###...##.........###",
    "###..............###",
    "###..............###",
    "###.........##...###",
    "###..............###",
    "###..............###",
    ".....##..........###",
    ".................###",
    "###..............###",
    "###..............###",
    "###..............###",
    "######..############",
    "######..############",
    "######..############",
])

# ---- the loops ------------------------------------------------------------

_piece("ring", "A circle. Both ways round arrive, which means the piece cannot "
       "be used to tell you where you are, which is the point of it.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####............####",
    "####............####",
    "......########..####",
    "......########..####",
    "####..########..####",
    "####..########..####",
    "####..########..####",
    "####..########..####",
    "####..########......",
    "####..########......",
    "####............####",
    "####............####",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("loop_blind", "A ring you meet head on, so it splits you left or right "
       "the moment you are in it. The far side carries the only other way out, "
       "and you cannot see it from the mouth you came in by.", [
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "######..############",
    "###...........######",
    "###...........######",
    "###..#######..######",
    "###..#######..######",
    "###..#######..######",
    "###..#######..######",
    "###...........######",
    "###...........######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
])

_piece("spiral", "A coil that turns you through more than a full circle and "
       "ends in a core. There is no walking back out: the core holds a warp "
       "that puts you at the mouth you entered by, facing in.", [
    "###..###############",
    "###..###############",
    "###<.............###",
    "###..............###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "#####........##..###",
    "#####........##..###",
    "#####..####..##..###",
    "#####..####..##..###",
    "#####..#*....##..###",
    "#####..#.>...##..###",
    "#####..########..###",
    "#####..########..###",
    "#####............###",
    "#####............###",
    "####################",
    "####################",
])

_piece("switchback", "Three hairpins. It crosses the same ground four times "
       "and never once lets you see where it is going, so a piece you can "
       "cross in twenty tiles takes seventy.", [
    "###..###############",
    "###..###############",
    "###..###############",
    "###..............###",
    "###..............###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###..............###",
    "###..............###",
    "###..###############",
    "###..###############",
    "###..###############",
    "###..............###",
    "###..............###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
    "###############..###",
])

# ---- the rooms ------------------------------------------------------------

_piece("hall_cells", "A long hall with cells opening off one side. One of them "
       "is lit, and lit ground never shifts, so this is a place you can come "
       "back to and find again.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "....................",
    "....................",
    "###..###..###..#####",
    "###..###..###..#####",
    "###..###~*###..#####",
    "###..###..###..#####",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("gallery", "The big black room. Four ways in at the corners, pillars "
       "scattered off the grid, and enough floor that the far wall is out of "
       "the light you are carrying.", [
    "###..##########..###",
    "###..##########..###",
    "##................##",
    "##................##",
    "##................##",
    "##...##......##...##",
    "##...##......##...##",
    "##................##",
    "##................##",
    "##......##........##",
    "##......##........##",
    "##................##",
    "##................##",
    "##..##........##..##",
    "##..##........##..##",
    "##................##",
    "##................##",
    "##................##",
    "###..##########..###",
    "###..##########..###",
])

_piece("haven", "A lit room with someone in it. Pinned forever the moment you "
       "find it: the field is allowed to lie about everything except the "
       "places you have actually stood and the places that are lit.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####............####",
    "................####",
    "................####",
    "####............####",
    "####.....~*.....####",
    "####............####",
    "####............####",
    "####............####",
    "####............####",
    "####............####",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
])

_piece("collapse", "A corridor with its roof down. It still goes through, and "
       "the pocket the fall opened in the side does not go anywhere at all.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    ".......*......##....",
    "........*...........",
    "##############..####",
    "##############.*####",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("deadend_find", "One mouth, two stubs, one thing. The piece exists so "
       "that walking a long way and finding nothing stays possible, because "
       "a field where every corridor pays is a field with no tension in it.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "####################",
    "########..##########",
    "########*.##########",
    "########..##########",
    "########..##########",
    "..........##########",
    "..........##########",
    "########..##########",
    "########..##########",
    "########..##########",
    "########..##########",
    "####################",
    "####################",
])

# ---- the impossible ones --------------------------------------------------

_piece("warp_pair", "Two corridors with a wall between them and no door in it. "
       "The pane in one puts you in the other, mid stride, no fade. The piece "
       "is the fold doing openly what the field does behind your back.", [
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###>.##########<.###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
    "###..##########..###",
])

_piece("comb", "The landing the staircase reaches: three ways in along one "
       "edge and one way on. It is the piece that keeps a shifting span from "
       "only ever mating with another shifting span.", [
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..............###",
    "###..............###",
    "###..............###",
    "###..............###",
    "###..............###",
    "###..............###",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
])

_piece("pit", "A walkway around a hole. You can see the ledge in the middle of "
       "it and the whole way round the ledge is out of reach, which is the "
       "argument for stepping into the pane on the near side.", [
    "####################",
    "####################",
    "####################",
    "####################",
    "####....>.......####",
    "####............####",
    "......@@@@@@@@..####",
    "......@@@@@@@@..####",
    "####..@@@@@@@@..####",
    "####..@@@<@@@@..####",
    "####..@@@*@@@@..####",
    "####..@@@@@@@@..####",
    "####..@@@@@@@@......",
    "####..@@@@@@@@......",
    "####............####",
    "####............####",
    "####################",
    "####################",
    "####################",
    "####################",
])

_piece("moving_stair", "The staircase. A bank, a gap you can see across and "
       "not cross, and one span that slides between three sockets while you "
       "stand there watching it. Which of the three ways out exists is a "
       "question the room answers again every few seconds.", [
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "############..######",
    "###..............###",
    "###..............###",
    "###@@@SS@@@@@@@@@###",
    "###@@@SS@@@@@@@@@###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
    "###..#..#######..###",
])


# ====================================================== READING A PIECE =====

def _edge_cells(rows, side):
    """The 20 border cells along one side, west to east / north to south."""
    if side == "n":
        return list(rows[0])
    if side == "s":
        return list(rows[SIZE - 1])
    if side == "w":
        return [r[0] for r in rows]
    return [r[SIZE - 1] for r in rows]


def edge_slots(rows, side):
    """Which mouth offsets this edge carries, as a sorted tuple.

    Two pieces mate on an edge when their facing edges answer this the same
    way. That is the whole compatibility rule.
    """
    cells = _edge_cells(rows, side)
    return tuple(s for s in SLOTS
                 if all(cells[s + i] in _WALKABLE for i in range(MOUTH_W)))


def signature(rows):
    """The piece's four edges, north east south west."""
    return tuple(edge_slots(rows, s) for s in "nesw")


def rotate(rows):
    """Turn the piece a quarter turn clockwise. Mouth offsets stay legal
    because the slot set is closed under the turn (3 <-> 15, 6 <-> 12)."""
    return tuple("".join(rows[SIZE - 1 - c][r] for c in range(SIZE))
                 for r in range(SIZE))


def mirror(rows):
    """Flip the piece east to west. Also closed over the slot set."""
    return tuple(r[::-1] for r in rows)


def orientations(rows):
    """All eight placements of one drawn shape."""
    out, cur = [], tuple(rows)
    for _ in range(4):
        out.append(cur)
        out.append(mirror(cur))
        cur = rotate(cur)
    return out


def reachable_from(rows, start):
    """Flood the walkable cells from one tile, stepping through warp panes.

    The warp pair is floor for this purpose: two corridors joined only by
    their panes ARE connected, and a validator that could not see that would
    reject the one piece built to prove the field can lie.
    """
    warps = [(r, c) for r in range(SIZE) for c in range(SIZE)
             if rows[r][c] in (WARP_A, WARP_B)]
    seen, stack = {start}, [start]
    while stack:
        r, c = stack.pop()
        here = rows[r][c]
        nbrs = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        if here in (WARP_A, WARP_B):
            nbrs += [w for w in warps if w != (r, c)]
        for nr, nc in nbrs:
            if not (0 <= nr < SIZE and 0 <= nc < SIZE):
                continue
            if rows[nr][nc] not in _WALKABLE or (nr, nc) in seen:
                continue
            seen.add((nr, nc))
            stack.append((nr, nc))
    return seen


def mouth_tiles(rows):
    """Every border tile that is part of a mouth, as (row, col)."""
    out = []
    for side in "nesw":
        for s in edge_slots(rows, side):
            for i in range(MOUTH_W):
                if side == "n":
                    out.append((0, s + i))
                elif side == "s":
                    out.append((SIZE - 1, s + i))
                elif side == "w":
                    out.append((s + i, 0))
                else:
                    out.append((s + i, SIZE - 1))
    return out


def span_sockets(rows):
    """Where a shifting span can land, derived from the gap it spans.

    A socket is a run of void the span's width with walkable ground on both
    banks. Deriving it beats declaring it: the sockets are then a property of
    the drawn shape, and moving one wall in the drawing moves the sockets with
    it instead of leaving a hand-written list pointing at nothing.
    """
    band = _gap_band(rows)
    if band is None:
        return []
    across, lo, hi = band
    out = []
    for k in range(SIZE - MOUTH_W + 1):
        span = range(k, k + MOUTH_W)
        if not all(_at(rows, across, lo - 1, x) in _WALKABLE for x in span):
            continue
        if not all(_at(rows, across, hi + 1, x) in _WALKABLE for x in span):
            continue
        if not all(_at(rows, across, d, x) in (VOID, SHIFT)
                   for d in range(lo, hi + 1) for x in span):
            continue
        out.append(k)
    return out


def _gap_band(rows):
    """The void the span crosses: (across, first, last) in the gap's own axis.

    `across` is True when the gap is a band of ROWS (banks north and south of
    it) and False when it is a band of COLUMNS. Working this out from the
    drawing rather than declaring it is what lets a rotated piece keep its
    sockets: turn the shape and the gap turns with it.
    """
    cells = [(r, c) for r in range(SIZE) for c in range(SIZE)
             if rows[r][c] in (VOID, SHIFT)]
    if not cells:
        return None
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    across = (r1 - r0) <= (c1 - c0)
    lo, hi = (r0, r1) if across else (c0, c1)
    if lo - 1 < 0 or hi + 1 >= SIZE:
        return None
    return across, lo, hi


def _at(rows, across, depth, along):
    return rows[depth][along] if across else rows[along][depth]


def with_span_at(rows, k):
    """The piece as it stands with its shifting span parked at one socket."""
    band = _gap_band(rows)
    if band is None:
        return tuple(rows)
    across, lo, hi = band
    grid = [list(r) for r in rows]
    for d in range(lo, hi + 1):
        for a in range(SIZE):
            if _at(rows, across, d, a) == SHIFT:
                if across:
                    grid[d][a] = VOID
                else:
                    grid[a][d] = VOID
    for d in range(lo, hi + 1):
        for i in range(MOUTH_W):
            if across:
                grid[d][k + i] = SHIFT
            else:
                grid[k + i][d] = SHIFT
    return tuple("".join(r) for r in grid)


def faults(name, rows):
    """Everything wrong with one drawn piece. Empty list means it is legal.

    Drawn by hand means mistyped by hand, and a piece with a mouth two tiles
    off its slot mates with nothing and quietly never gets placed.
    """
    bad = []
    if len(rows) != SIZE:
        return ["%s: %d rows, want %d" % (name, len(rows), SIZE)]
    for i, r in enumerate(rows):
        if len(r) != SIZE:
            bad.append("%s: row %d is %d wide, want %d"
                       % (name, i, len(r), SIZE))
    if bad:
        return bad
    # every walkable border cell belongs to a legal mouth
    legal = set(mouth_tiles(rows))
    for side in "nesw":
        cells = _edge_cells(rows, side)
        for i, ch in enumerate(cells):
            if ch not in _WALKABLE:
                continue
            if side == "n":
                pos = (0, i)
            elif side == "s":
                pos = (SIZE - 1, i)
            elif side == "w":
                pos = (i, 0)
            else:
                pos = (i, SIZE - 1)
            if pos not in legal:
                bad.append("%s: open border tile at %s edge offset %d is not "
                           "on a mouth slot %s" % (name, side, i, list(SLOTS)))
    mouths = mouth_tiles(rows)
    if not mouths:
        bad.append("%s: no mouths, so nothing can ever reach it" % name)
        return bad
    # A SHIFTING piece is connected differently at each span position, and
    # that IS the piece: which ways out exist depends on where the span is.
    # So the rule is not "every mouth reaches every mouth" but "every mouth is
    # reachable at some span position, and no span position strands you".
    if any(SHIFT in r for r in rows):
        sockets = span_sockets(rows)
        if len(sockets) < 2:
            bad.append("%s: a shifting span with %d sockets does not shift"
                       % (name, len(sockets)))
            return bad
        union = set()
        for c in sockets:
            placed = with_span_at(rows, c)
            seen_c = set()
            for m in mouths:
                seen_c |= reachable_from(placed, m)
            got = [m for m in mouths if m in seen_c]
            if len(got) < 2:
                bad.append("%s: with the span at %d only %d mouth tiles are "
                           "reachable, so the room is a trap" % (name, c, len(got)))
            union |= seen_c
        for m in mouths:
            if m not in union:
                bad.append("%s: mouth at %s is unreachable at every span "
                           "position" % (name, m))
        seen = union
    else:
        # Every walkable tile has to be reachable from SOME mouth. Not from
        # every mouth: `twin_run` is two channels through one block that never
        # meet, and that is the piece, not a defect in it.
        seen = set()
        for m in mouths:
            seen |= reachable_from(rows, m)
    # no walkable pocket that no mouth can get to
    for r in range(SIZE):
        for c in range(SIZE):
            if rows[r][c] in _WALKABLE and (r, c) not in seen:
                bad.append("%s: sealed pocket at row %d col %d" % (name, r, c))
                break
        else:
            continue
        break
    # warps come in pairs
    a = sum(r.count(WARP_A) for r in rows)
    b = sum(r.count(WARP_B) for r in rows)
    if a != b:
        bad.append("%s: %d warp panes in and %d out" % (name, a, b))
    # a shifting span needs somewhere to shift to
    if any(SHIFT in r for r in rows) and not any(VOID in r for r in rows):
        bad.append("%s: a shifting span with no gap to span" % name)
    return bad


def all_faults():
    out = []
    for name, p in sorted(DECK.items()):
        base = faults(name, p["rows"])
        out += base
        if any("wide, want" in f or "rows, want" in f for f in base):
            continue        # a mis-shaped grid cannot be turned; say so once
        # every orientation must survive the same rules: a piece that is only
        # legal facing north is a piece the field can place one way in eight.
        for i, rot in enumerate(orientations(p["rows"])):
            out += ["%s (orientation %d): %s" % (name, i, f)
                    for f in faults(name, rot) if not f.startswith(name + ":")]
            out += [f.replace(name + ":", "%s orientation %d:" % (name, i))
                    for f in faults(name, rot) if f.startswith(name + ":")]
    return out
