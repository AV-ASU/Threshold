"""How PERMEABLE is a treeline? Measure it instead of arguing about it.

Since trees became solid with round sub-tile feet, a stand is something you
thread rather than something you bounce off -- the gaps fall out of the
geometry instead of being authored. That is the right model, and it has one
cost: nobody can tell by looking whether a particular band is "thread between
the trunks" or "fight the trees". Connectivity passing says only that SOME
route exists; it says nothing about whether walking at the treeline feels like
walking or like pinball.

So this measures the thing the eye cannot: for one scene edge, what fraction
of sub-tile LANES admit a STRAIGHT walk through the band. Straight, because a
player pushing north holds north -- a lane that needs three sidesteps is a
lane that feels blocked even though the flood fill counts it.

    python tools/band_gaps.py                     # every outdoor scene
    python tools/band_gaps.py brimley lodge_yard  # named scenes
    python tools/band_gaps.py --depth 10          # how far in to push

Read the number, not the verdict: an interior or a walled glade reports near
zero and that is correct (one doorway is the design). It is the OUTDOOR bands
where the figure means something.
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYTHONPATH", ".")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import TILE                                   # noqa: E402
from scenes import SCENE_BUILDERS, load_scene                # noqa: E402

# The default outdoor set: scenes whose edge is a scattered stand rather than
# a wall. Anything else can still be named on the command line.
OUTDOOR = ("brimley", "lodge_yard", "cornfield_path", "clearing",
           "effigy_grove", "cornfield_maze", "arrival_road")
LANE = 4.0        # sub-tile lane spacing, in world units
STEP = 2.0        # how finely a lane is walked


def band_pct(sc, side, depth=8):
    """Percent of lanes on `side` that cross `depth` tiles without a bump."""
    ok = tot = 0
    steps = int(depth * TILE / STEP)
    horiz = side in ("n", "s")
    n_lanes = int((sc.w if horiz else sc.h) * TILE / LANE)
    for i in range(n_lanes):
        a = i * LANE + LANE / 2
        tot += 1
        if horiz:
            b = 2.0 if side == "n" else sc.h * TILE - 2.0
            db = STEP if side == "n" else -STEP
        else:
            b = 2.0 if side == "w" else sc.w * TILE - 2.0
            db = STEP if side == "w" else -STEP
        for _ in range(steps):
            if sc.is_solid_at(*((a, b) if horiz else (b, a))):
                break
            b += db
        else:
            ok += 1
    return 100.0 * ok / max(1, tot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--depth", type=int, default=8,
                    help="tiles of band to push through (default 8)")
    args = ap.parse_args()
    keys = args.scenes or [k for k in OUTDOOR if k in SCENE_BUILDERS]
    print(f"straight-crossing lanes, pushing {args.depth} tiles in\n")
    for key in keys:
        sc = load_scene(key)
        if getattr(sc, "procedural", False):
            print(f"  {key:18s} (generated field, no fixed edge)")
            continue
        cells = "  ".join(f"{s}={band_pct(sc, s, args.depth):5.1f}%"
                          for s in "nesw")
        print(f"  {key:18s} {cells}")
    print("\n  Under ~15% is where a band stops reading as a wood you thread.")


if __name__ == "__main__":
    main()
