"""THE SURFACE MAP -- how the above-ground world actually connects.

There is no town map any more (DESIGN.md §15): Brimley is a string of house
islands on a street network, so the only place the geography exists is the
exit tables of a dozen separate scenes. That makes "how does the surface fit
together" a question nobody could answer without reading every scene builder,
which is exactly the kind of thing that gets remembered wrong.

This reads it out of the built scenes instead:

  * every exit's COMPASS DIRECTION, taken from which map edge its tile sits on
    (an interior door -- a tile not on an edge -- is reported as a door, since
    a door into a building is not a direction on the map);
  * a geographic LAYOUT, walked out from `arrival_road` by placing each
    neighbour in the direction its exit actually faces;
  * the SEAM DISAGREEMENTS that fall out of doing that -- where A says B is
    west but B says A is south, the two scenes disagree about where they are,
    and the crossing reads as a teleport (`audit_traversal.py` finds the same
    class from the spawn side);
  * which edges are §13 LOST-SPACE MOUTHS, since on this layer an unlit map
    edge is not a wall, it is the way out of the world.

    python tools/surface_map.py                    # the ASCII map + the report
    python tools/surface_map.py --svg out.svg      # the compass plate
    python tools/surface_map.py --json net.json    # the raw network
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from scenes import SCENE_BUILDERS, load_scene            # noqa: E402

# The three layers of DESIGN.md §14/§15, named here so the map can colour and
# rank them. STREETS are the safe-path spine; a YARD is one household's ground;
# everything a yard door leads into is an INTERIOR.
STREETS = ("arrival_road", "country_lane", "gravel_road_north", "store_row",
           "chapel_row", "south_row", "bank_row", "lane_end", "river_road",
           "river_bend")
# Outdoor scenes that are neither spine nor yard: the corn, the woods, the
# river's far bank. They hang off the network but hold no household.
WILD = ("cornfield_path", "cornfield_maze", "clearing", "backwoods_cabin",
        "effigy_grove")

_DELTA = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
_OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


def _edge_of(sc, tx, ty, margin=2):
    """Which map EDGE a tile sits on, or None for an interior tile.

    The margin is what makes this honest: an exit is authored a tile or two
    inside the boundary so the player can stand on it, so an exact ==0/==w-1
    test reports a door where there is an edge.
    """
    if tx <= margin:
        return "W"
    if tx >= sc.w - 1 - margin:
        return "E"
    if ty <= margin:
        return "N"
    if ty >= sc.h - 1 - margin:
        return "S"
    return None


def _find_tile(sc, ch):
    for ty in range(sc.h):
        row = sc.objects[ty] if ty < len(sc.objects) else ""
        for tx in range(min(sc.w, len(row))):
            if row[tx] == ch:
                return tx, ty
    return None


def collect():
    """{scene: {"exits": [(dir_or_None, char, target)], "lost": {...}, ...}}"""
    world = {}
    for key in sorted(SCENE_BUILDERS):
        try:
            sc = load_scene(key)
        except Exception as e:                      # a scene that will not
            world[key] = {"error": repr(e)}         # build is itself a finding
            continue
        out = []
        for ch, (tgt, spawn) in sc.exits.items():
            pos = _find_tile(sc, ch)
            out.append((_edge_of(sc, *pos) if pos else None, ch, tgt, spawn))
        world[key] = {
            "exits": sorted(out, key=lambda r: (r[0] or "door", r[2])),
            "lost": dict(getattr(sc, "lost_edges", None) or {}),
            "size": (sc.w, sc.h),
            "name": getattr(sc, "display_name", "") or key,
        }
    return world


def layout(world, root="arrival_road"):
    """Walk the graph from `root`, placing each scene in its compass cell.

    Returns (cells, conflicts). A cell already claimed by another scene is a
    genuine conflict in the world's geometry, not a layout bug, so it is
    reported rather than nudged around -- and the walk keeps going, so one
    contradiction does not truncate the whole map.
    """
    at = {root: (0, 0)}
    taken = {(0, 0): root}
    conflicts, order, seen = [], [root], {root}
    while order:
        cur = order.pop(0)
        cx, cy = at[cur]
        for d, ch, tgt, _spawn in world.get(cur, {}).get("exits", []):
            if d is None or tgt not in world or tgt == cur:
                continue
            dx, dy = _DELTA[d]
            cell = (cx + dx, cy + dy)
            if tgt in at:
                if at[tgt] != cell:
                    conflicts.append((cur, d, tgt, at[tgt], cell))
                continue
            if cell in taken:
                conflicts.append((cur, d, tgt, taken[cell], cell))
                # keep walking outward in the SAME direction so the rest of
                # the network still gets placed and drawn
                while cell in taken:
                    cell = (cell[0] + dx, cell[1] + dy)
            at[tgt] = cell
            taken[cell] = tgt
            if tgt not in seen:
                seen.add(tgt)
                order.append(tgt)
    return at, conflicts


def spine(world, root="arrival_road"):
    """The street network as the player WALKS it: an ordered chain of streets.

    Walk order is the one presentation the contradictions below cannot break,
    because it never asks two scenes to agree about a direction -- only about
    which door leads where.
    """
    chain, cur, seen = [], root, set()
    while cur and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        nxt = None
        for d, _c, t, _s in world.get(cur, {}).get("exits", []):
            if t in STREETS and t not in seen:
                nxt = t
                break
        cur = nxt
    return chain


def disagreements(world):
    """A -> B by direction d, but B -> A by something other than opposite(d)."""
    bad = []
    for a, info in world.items():
        for d, ch, b, _s in info.get("exits", []):
            if d is None or b not in world:
                continue
            back = [bd for bd, _c, bt, _bs in world[b].get("exits", [])
                    if bt == a and bd is not None]
            if back and _OPPOSITE[d] not in back:
                bad.append((a, d, b, back[0]))
    return bad


def _layer(key):
    if key in STREETS:
        return "street"
    if key.endswith("_yard"):
        return "yard"
    if key in WILD:
        return "wild"
    return "interior"


def ascii_map(world, at):
    """The spine and its households, printed north to south."""
    lines = []
    placed = {k: v for k, v in at.items() if _layer(k) in ("street", "wild")}
    if not placed:
        return "  (nothing placed)"
    ys = sorted({y for _x, y in placed.values()})
    for y in ys:
        row = sorted((x, k) for k, (x, yy) in placed.items() if yy == y)
        cells = []
        for _x, k in row:
            tag = "=" if k in STREETS else "-"
            cells.append("%s%s%s" % (tag, k, tag))
        lines.append("   " + "   ".join(cells))
        # the households hanging off each street on this row, W and E
        for _x, k in row:
            yards = [(d, t) for d, _c, t, _s in world[k]["exits"]
                     if t.endswith("_yard")]
            if yards:
                lines.append("      %-18s %s" % (
                    "", ", ".join("%s:%s" % (d, t) for d, t in sorted(yards))))
    return "\n".join(lines)


def main():
    world = collect()
    at, conflicts = layout(world)
    bad = disagreements(world)

    print("THRESHOLD surface map\n")
    broke = [k for k, v in world.items() if "error" in v]
    if broke:
        print("  SCENES THAT WILL NOT BUILD: %s\n" % broke)

    print("=" * 66)
    print("THE SPINE  (= street, - other outdoor; north at the top)")
    print("=" * 66)
    print(ascii_map(world, at))

    print("\n" + "=" * 66)
    print("EVERY SURFACE SCENE, BY LAYER")
    print("=" * 66)
    for want in ("street", "yard", "wild"):
        keys = sorted(k for k in world if _layer(k) == want and k in at)
        print("\n  %s (%d)" % (want.upper(), len(keys)))
        for k in keys:
            info = world[k]
            ex = ", ".join("%s->%s" % (d or "door", t)
                           for d, _c, t, _s in info["exits"])
            print("    %-18s %s" % (k, ex))
            if info["lost"]:
                print("    %-18s   mouths: %s" % ("", info["lost"]))

    print("\n" + "=" * 66)
    print("SEAMS WHERE THE TWO SCENES DISAGREE  (%d)" % len(bad))
    print("=" * 66)
    if not bad:
        print("  none -- every crossing comes back the way it went.")
    for a, d, b, back in bad:
        print("  %-18s %s-> %-18s but %s comes back %s (want %s)"
              % (a, d, b, b, back, _OPPOSITE[d]))

    if conflicts:
        print("\n" + "=" * 66)
        print("CELLS TWO SCENES BOTH CLAIM  (%d)" % len(conflicts))
        print("=" * 66)
        for a, d, b, other, cell in conflicts:
            print("  %-18s %s-> %-18s wants %s, held by %s"
                  % (a, d, b, cell, other))

    if "--json" in sys.argv:
        # The authoring-level network, for tools/network_editor.html: nodes
        # with their layer, and every link with the SIDE each end leaves by.
        import json
        nodes, links = [], []
        for k in sorted(world):
            lay = _layer(k)
            if lay == "interior" or k not in at or "exits" not in world[k]:
                continue
            nodes.append({"key": k, "layer": lay, "cell": list(at[k]),
                          "size": list(world[k]["size"]),
                          "lost": world[k]["lost"]})
            for d, ch, t, sp in world[k]["exits"]:
                if d is None or _layer(t) == "interior":
                    continue
                links.append({"from": k, "side": d, "char": ch,
                              "to": t, "spawn": sp})
        out = {"nodes": nodes, "links": links,
               "doors": {k: [t for d, c, t, s in world[k]["exits"]
                             if _layer(t) == "interior"]
                         for k in sorted(world)
                         if _layer(k) == "yard" and "exits" in world[k]}}
        path = "network.json"
        if sys.argv[-1].endswith(".json"):
            path = sys.argv[-1]
        open(path, "w").write(json.dumps(out, indent=1))
        print("\n  wrote %s (%d nodes, %d links)"
              % (path, len(nodes), len(links)))

    if "--svg" in sys.argv:
        out = sys.argv[sys.argv.index("--svg") + 1]
        open(out, "w").write(svg(world, at))
        print("\n  wrote %s" % out)
    return 0


def svg(world, at, cell=210, pad=70):
    """A geographic SVG: streets on their walked cells, households flanking."""
    xs = [x for x, _y in at.values()]
    ys = [y for _x, y in at.values()]
    W = (max(xs) - min(xs) + 1) * cell + pad * 2
    H = (max(ys) - min(ys) + 1) * cell + pad * 2
    ox, oy = -min(xs) * cell + pad, -min(ys) * cell + pad

    def px(k):
        x, y = at[k]
        return ox + x * cell, oy + y * cell

    FILL = {"street": "#2b2a26", "yard": "#3a3226", "wild": "#232a22",
            "interior": "#2a2630"}
    EDGE = {"street": "#c8b26a", "yard": "#9a8552", "wild": "#6f8a63",
            "interior": "#7d6f96"}
    p = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
         'width="%d" height="%d" font-family="ui-monospace,monospace">'
         % (W, H, W, H),
         '<rect width="%d" height="%d" fill="#14130f"/>' % (W, H)]

    # seams first, so the boxes sit on top of their own lines
    for k in at:
        for d, _c, t, _s in world.get(k, {}).get("exits", []):
            if d is None or t not in at:
                continue
            x1, y1 = px(k)
            x2, y2 = px(t)
            p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#5a5344" '
                     'stroke-width="3"/>' % (x1, y1, x2, y2))
    for k, _cell in sorted(at.items()):
        lay = _layer(k)
        if lay == "interior":
            continue
        x, y = px(k)
        w, h = 168, 52
        p.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" '
                 'stroke="%s" stroke-width="2"/>'
                 % (x - w // 2, y - h // 2, w, h, FILL[lay], EDGE[lay]))
        p.append('<text x="%d" y="%d" fill="#e8e0cc" font-size="15" '
                 'text-anchor="middle">%s</text>' % (x, y + 5, k))
    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    sys.exit(main())
