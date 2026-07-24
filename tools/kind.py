"""What do I need to know about this decoration KIND, before I place it?

    python tools/kind.py boulder
    python tools/kind.py boulder haven_fire neon_pylon
    python tools/kind.py --unplaced          # registered kinds nobody places
    python tools/kind.py --stains            # kinds that draw as FLAT STAINS

Answers, per kind, the questions you otherwise re-derive with a throwaway
script every time (this tool exists because that throwaway got written three
times in one session):

  * **How does it draw under the tilt?** Which tilt set it is registered in --
    or the loud warning that it is in NONE and will render as a flat stain on
    the floor under the only shipping camera.
  * **Does it light?** Whether it is in the MECHANICAL cover table
    (`Scene._LIGHT_KINDS`) and the VISIBLE pool table (`FIXTURE_POOLS`).
    In only one, it either gates without shining or shines without gating.
  * **Does its art exist?** A `_draw_<kind>` flat fallback, a solid draw fn.
  * **Where is it already used?** Which scenes place it, and how many.

It deliberately does NOT show you the art. Go LOOK at it -- that is the point
of scene-dressing step 2, and the tool for it already exists:

    python tools/preview_props_sheet.py <kind> [...]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


def _tables():
    from rendering.props import SOLID_PROPS, _STANDEE_KINDS
    from rendering.furniture import FURNITURE
    from scenes.terrain import (_FLOOR_DECAL_KINDS, _SURFACE_DECAL_KINDS,
                                _WALL_DECO_KINDS, _TABLETOP_PROP_KINDS)
    return {
        "SOLID_PROPS (a projected 3D volume)": SOLID_PROPS,
        "STANDEE (a flat card stood up)": _STANDEE_KINDS,
        "FURNITURE (a box volume)": FURNITURE,
        "FLOOR_DECAL (warped onto the ground)": _FLOOR_DECAL_KINDS,
        "SURFACE_DECAL (warped onto a surface)": _SURFACE_DECAL_KINDS,
        "WALL_DECO (hung on a wall)": _WALL_DECO_KINDS,
        "TABLETOP (seated on furniture)": _TABLETOP_PROP_KINDS,
    }


def _placements():
    """kind -> {scene: count} across every registered scene."""
    from scenes import SCENE_BUILDERS, load_scene
    out = {}
    for key in sorted(SCENE_BUILDERS):
        try:
            sc = load_scene(key)
        except Exception:
            continue
        for d in getattr(sc, "decorations", []):
            k = getattr(d, "kind", None)
            if k:
                out.setdefault(k, {}).setdefault(key, 0)
                out[k][key] += 1
    return out


def report(kind, tables, places):
    from systems.render_mixin import FIXTURE_POOLS
    from scenes.base import Scene
    from entities.decoration import Decoration
    from rendering.props import SOLID_PROPS

    print(f"\n=== {kind} ===")
    hits = [name for name, s in tables.items() if kind in s]
    if hits:
        for h in hits:
            print(f"  tilt set   : {h}")
        if len(hits) > 1:
            print("  !! in MORE THAN ONE tilt set -- register a kind in exactly one")
    else:
        print("  tilt set   : *** NONE -- draws as a FLAT STAIN on the floor ***")
        print("               (CLAUDE.md: register it in exactly one set)")

    mech = kind in Scene._LIGHT_KINDS
    vis = kind in FIXTURE_POOLS
    if mech or vis:
        print(f"  light      : mechanical cover={'yes' if mech else 'NO'} "
              f"({Scene._LIGHT_KINDS.get(kind, '-')})   "
              f"visible pool={'yes' if vis else 'NO'}")
        if mech != vis:
            print("               !! in only ONE table: it " + (
                "gates as lit but casts nothing" if mech else
                "shines but gives no stealth cover"))
    else:
        print("  light      : not an emitter")

    print(f"  flat art   : {'yes' if hasattr(Decoration, f'_draw_{kind}') else 'NO _draw_ method'}")
    print(f"  solid art  : {'yes' if kind in SOLID_PROPS else 'no (not a SOLID_PROPS volume)'}")

    where = places.get(kind)
    if where:
        tot = sum(where.values())
        top = ", ".join(f"{s}x{n}" for s, n in sorted(where.items())[:6])
        print(f"  placed     : {tot} in {len(where)} scene(s): {top}")
    else:
        print("  placed     : nowhere yet")
    print(f"  SEE IT     : python tools/preview_props_sheet.py {kind}")


def main():
    args = [a for a in sys.argv[1:]]
    tables = _tables()
    places = _placements()

    if "--stains" in args:
        bad = {k: v for k, v in places.items()
               if not any(k in s for s in tables.values())}
        print("placed kinds in NO tilt set (flat stains under the tilt):")
        for k, v in sorted(bad.items()):
            print(f"   {k:22} {sorted(v)}")
        if not bad:
            print("   none")
        return 0

    if "--unplaced" in args:
        known = set()
        for s in tables.values():
            known |= set(s)
        print("registered kinds that no scene places (reusable art, or cut):")
        for k in sorted(known - set(places)):
            print(f"   {k}")
        return 0

    if not args:
        print(__doc__)
        return 1
    for kind in args:
        report(kind, tables, places)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
