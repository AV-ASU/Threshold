"""THE CORRIDOR FIELD, walked -- the deck turned into rooms and driven.

`tests/conventions.py` check 15 asserts every DRAWN piece is legal. This is
the other half: that a legal deck, dealt into a field, is a place you can walk
through and back out of. It boots a real game, falls through a street verge in
the dark, crosses rooms by pressing into their mouths, and checks the things
that can only be wrong once the pieces are load-bearing:

  * the seam. Every crossing lands on an edge carrying the SAME mouth offsets
    the one you left carried, or the corridor tears.
  * the DISCOVERED law. A room two behind you is re-decided, and the field
    stays consistent across the swap.
  * the WATCHED law. The span moves while it is in the sight cone, holds
    still when it is not, and never moves out from under the player.
  * the loop closes. Walk far enough and the way out is dealt, reaching it
    spends the anchor `_tick_lost_edge` wrote, and you are back where the
    world let go of you.

    python tests/lost_field.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scenes.base import TILE                                   # noqa: E402
from scenes import lost_field as LF                            # noqa: E402
from scenes import lost_pieces as LP                           # noqa: E402

FAILS = []


def check(ok, label):
    print(("  [ok] " if ok else "  [!!] ") + label)
    if not ok:
        FAILS.append(label)


def _boot():
    from tools.capture_world import _boot_game
    return _boot_game()


def _press_mouth(game, side):
    """Stand in a mouth on `side` and let the room's own tick carry it.

    Deliberately drives the SHIPPING path (`on_update_fn`) rather than calling
    the crossing directly: the thing under test is that walking into the wall
    where a mouth is crosses, and walking into the wall where one is not does
    nothing.
    """
    sc = game.scene
    rows = sc._field.rows_at(sc._cell)
    slots = LP.edge_slots(rows, side)
    if not slots:
        return None
    s = slots[0]
    band, span = 0.4 * TILE, LP.SIZE * TILE
    game.player.x, game.player.y = {
        "n": ((s + 0.5) * TILE, band),
        "s": ((s + 0.5) * TILE, span - band),
        "w": (band, (s + 0.5) * TILE),
        "e": (span - band, (s + 0.5) * TILE)}[side]
    before_rows, before_cell = rows, sc._cell
    # Two ticks: the first gives the room a previous position to measure
    # from, the second is the step that walks out. That IS the shipping rule
    # (you cross by walking through, not by standing near), so the harness
    # drives it rather than working around it.
    sc.on_update_fn(game, sc, 0.016)
    if game.scene._cell == before_cell:
        game.player.x += {"n": 0, "s": 0, "w": -4.0, "e": 4.0}[side]
        game.player.y += {"n": -4.0, "s": 4.0, "w": 0, "e": 0}[side]
        sc.on_update_fn(game, sc, 0.016)
    if game.scene._cell == before_cell:
        return None
    return before_rows, side


def main():
    print("THRESHOLD corridor field\n")

    # --- 1. the mouth: a dark verge drops you into corridors ---------------
    print("1. falling in")
    g = _boot()
    g.save.set_arg("evidence", [{"name": "e%d" % i, "content": "x"}
                                for i in range(3)])
    g.load_scene_now("store_row")
    check(g.scene.lost_edges and g.scene.lost_edges.get("n") == "lost_road",
          "the street's north verge names the road field")
    g.player.x, g.player.y = 3 * TILE + 8, 0.4 * TILE
    fell = g._tick_lost_edge(0.0, -60.0)
    check(fell and g.scene.key == "lost_road",
          "in the dark, walking into the verge lands you in the field")
    check(g._lost_return is not None and g._lost_return[0] == "store_row",
          "the way back is anchored where the world let go")
    fld = LF.FIELD
    check(fld is not None and g.scene.w == LP.SIZE and g.scene.h == LP.SIZE,
          "the room is one drawn piece, %dx%d" % (LP.SIZE, LP.SIZE))
    check(g.scene.display_name == "",
          "the field is wordless: no place name in the corner")

    # --- 2. the seam holds across every crossing ---------------------------
    print("\n2. walking it")
    came, walked = None, 0
    for i in range(24):
        sc = g.scene
        rows = sc._field.rows_at(sc._cell)
        ways = [s for s in "nesw" if LP.edge_slots(rows, s) and s != came]
        if not ways:
            ways = [s for s in "nesw" if LP.edge_slots(rows, s)]
        if not ways:
            break
        side = ways[i % len(ways)]
        got = _press_mouth(g, side)
        if got is None:
            continue
        left_rows, side = got
        arrived = g.scene._field.rows_at(g.scene._cell)
        if LP.edge_slots(left_rows, side) != LP.edge_slots(arrived,
                                                           LF._OPP[side]):
            check(False, "seam torn crossing %s out of room %d" % (side, walked))
            break
        came = LF._OPP[side]
        walked += 1
        if fld.exit_cell is not None and g.scene._cell == fld.exit_cell:
            break
    check(walked >= 4, "crossed %d rooms by pressing into their mouths" % walked)
    check(all(LP.edge_slots(fld.rows_at(c), s)
              == LP.edge_slots(fld.rows_at((c[0] + d[0], c[1] + d[1])),
                               LF._OPP[s])
              for c in fld.cells for s, d in LF._STEP.items()
              if (c[0] + d[0], c[1] + d[1]) in fld.cells),
          "every seam in the dealt field agrees, %d rooms" % len(fld.cells))

    # --- 3. a wall is a wall -----------------------------------------------
    sc = g.scene
    rows = sc._field.rows_at(sc._cell)
    walled = None
    for s in "nesw":
        if not LP.edge_slots(rows, s):
            walled = s
            break
    if walled:
        before = sc._cell
        off = [i for i in range(LP.SIZE)
               if not any(sl <= i < sl + LP.MOUTH_W
                          for sl in LP.edge_slots(rows, walled))][0]
        band, span = 0.4 * TILE, LP.SIZE * TILE
        g.player.x, g.player.y = {
            "n": ((off + 0.5) * TILE, band),
            "s": ((off + 0.5) * TILE, span - band),
            "w": (band, (off + 0.5) * TILE),
            "e": (span - band, (off + 0.5) * TILE)}[walled]
        sc.on_update_fn(g, sc, 0.016)
        g.player.x += {"n": 0, "s": 0, "w": -4.0, "e": 4.0}[walled]
        g.player.y += {"n": -4.0, "s": 4.0, "w": 0, "e": 0}[walled]
        sc.on_update_fn(g, sc, 0.016)
        check(g.scene._cell == before,
              "pressing a blank edge crosses nothing (a wall is a wall)")

    # --- 4. the DISCOVERED law ---------------------------------------------
    print("\n3. what moves behind you")
    f2 = LF.LostField("lost_road", "road", seed=7)
    for c in ((1, 0), (2, 0), (3, 0), (4, 0)):
        f2.ensure(c)
        f2.arrive(c)
    snapshot = dict(f2.cells)
    f2.ensure((5, 0))
    f2.arrive((5, 0))
    moved = [c for c in snapshot if f2.cells.get(c) != snapshot[c]]
    check(moved, "a room you left and cannot see is re-decided (%d of %d)"
          % (len(moved), len(snapshot)))
    check((4, 0) not in moved and (5, 0) not in moved,
          "the room you are in and the one at your back hold still")
    torn = [(c, s) for c in f2.cells for s, d in LF._STEP.items()
            if (c[0] + d[0], c[1] + d[1]) in f2.cells
            and LP.edge_slots(f2.rows_at(c), s)
            != LP.edge_slots(f2.rows_at((c[0] + d[0], c[1] + d[1])),
                             LF._OPP[s])]
    check(not torn, "the mouth grammar survives every re-decision")
    lit = [c for c in f2.visited if f2._room_is_lit(c)]
    check(all(c in f2.pinned for c in lit if c != f2.here),
          "a lit room you stood in is pinned: light never lies")

    # --- 5. the WATCHED law ------------------------------------------------
    print("\n4. what moves in front of you")
    gs = _boot()
    f3 = LF.LostField("lost_road", "road", seed=5)
    f3.cells[(0, 0)] = ("moving_stair", 0)
    LF.FIELD = f3
    room = LF._make(f3, (0, 0))
    gs.scene = room
    base = f3.rows_at((0, 0))
    sockets = LP.span_sockets(base)
    check(len(sockets) == 3, "the staircase has three sockets to slide between")

    def span_at():
        r = f3.rows_at((0, 0))
        for y in range(LP.SIZE):
            for x in range(LP.SIZE):
                if r[y][x] == LP.SHIFT:
                    return x
        return None

    home = span_at()
    gs.player.x, gs.player.y = (home + 0.5) * TILE, 8.5 * TILE
    gs.look.aim = math.pi / 2                       # south, straight at it
    seen = set()
    for _ in range(24):
        room._span_t = 0.0
        LF._tick_span(gs, room, 0.016)
        seen.add(span_at())
    check(len(seen) == 3,
          "watched, it slides and reaches every socket (%s)" % sorted(seen))
    f3.span[(0, 0)] = home
    gs.look.aim = -math.pi / 2                      # north, away from the gap
    held = set()
    for _ in range(8):
        room._span_t = 0.0
        LF._tick_span(gs, room, 0.016)
        held.add(span_at())
    check(held == {home}, "unwatched, it holds still")
    f3.span[(0, 0)] = home
    gs.look.aim = math.pi / 2
    band = LP._gap_band(f3.rows_at((0, 0)))
    gs.player.x = (home + 0.5) * TILE
    gs.player.y = (band[1] + 0.5) * TILE            # standing ON the span
    for _ in range(8):
        room._span_t = 0.0
        LF._tick_span(gs, room, 0.016)
    check(span_at() == home, "it never moves out from under you")

    # --- 6. the void: seen across, never crossed ---------------------------
    f3.span[(0, 0)] = home
    room2 = LF._make(f3, (0, 0))
    gap_y = (band[1] + 0.5) * TILE
    open_x = (home + 0.5) * TILE
    hole_x = None
    for c in sockets:
        if c != home:
            hole_x = (c + 0.5) * TILE
            break
    check(room2.is_solid_at(hole_x, gap_y) and not room2.is_solid_at(open_x,
                                                                     gap_y),
          "the gap is solid and the span across it is not")
    check(not room2.blocks_sight(hole_x, gap_y),
          "and you can see across the gap you cannot cross")

    # --- 6b. dressed, every room is still walkable -------------------------
    # The deck's own check proves the DRAWING is walkable. This proves the
    # ROOM is: a rust hulk is a solid prop and a corridor is two tiles wide,
    # so scatter placed anywhere open and away from the edges can wall a piece
    # off while leaving it perfectly legal on paper. Read through the room's
    # real collision, in every orientation, because the narrow ones are narrow
    # in different places when turned.
    print("\n4b. dressed and still walkable")
    walled = []
    for name in sorted(LP.DECK):
        rots = LP.orientations(LP.DECK[name]["rows"])
        for orient in range(len(rots)):
            fd = LF.LostField("lost_road", "road", seed=11)
            fd.cells[(0, 0)] = (name, orient)
            LF.FIELD = fd
            room = LF._make(fd, (0, 0))
            grid = fd.rows_at((0, 0))
            solid = {(x, y)
                     for y in range(LP.SIZE) for x in range(LP.SIZE)
                     if grid[y][x] in LP._WALKABLE
                     and room.is_solid_at(x * TILE + TILE // 2,
                                          y * TILE + TILE // 2)}
            if LF._would_wall_off(grid, solid):
                walled.append("%s/%d" % (name, orient))
    check(not walled,
          "no dressed room walls its own corridor off (%d rooms)"
          % sum(len(LP.orientations(p["rows"])) for p in LP.DECK.values())
          + ("" if not walled else ": " + ", ".join(walled[:6])))
    LF.clear_field()

    # --- 7. the loop closes ------------------------------------------------
    print("\n5. the way out")
    g2 = _boot()
    g2.save.set_arg("evidence", [{"name": "e%d" % i, "content": "x"}
                                 for i in range(3)])
    g2.load_scene_now("store_row")
    g2.player.x, g2.player.y = 3 * TILE + 8, 0.4 * TILE
    g2._tick_lost_edge(0.0, -60.0)
    f4 = LF.FIELD
    came, out = None, False
    for i in range(40):
        sc = g2.scene
        rows = sc._field.rows_at(sc._cell)
        ways = [s for s in "nesw" if LP.edge_slots(rows, s) and s != came]
        if not ways:
            ways = [s for s in "nesw" if LP.edge_slots(rows, s)]
        if not ways:
            break
        side = ways[i % len(ways)]
        got = _press_mouth(g2, side)
        if got is None:
            continue
        came = LF._OPP[side]
        light = getattr(g2.scene, "_exit_light", None)
        if light is not None:
            g2.player.x, g2.player.y = light.x, light.y
            g2.scene.on_update_fn(g2, g2.scene, 0.016)
            out = True
            break
    check(f4.exit_cell is not None,
          "the way out is dealt once you are deep enough to have earned it")
    check(out and g2.scene.key == "store_row",
          "reaching the light puts you back on the street you fell from")
    check(g2._lost_return is None and LF.FIELD is None,
          "and the field is spent: a fresh descent is a fresh place")

    print()
    if FAILS:
        print("FAILED: %d" % len(FAILS))
        for f in FAILS:
            print("   " + f)
        return 1
    print("the corridors chain, shift, and let you out.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
