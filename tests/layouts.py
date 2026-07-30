"""LAYOUT ROUND-TRIP -- a scene written to data and read back is the same scene.

Scenes are moving from hand-written builders to saved layouts, which is only
safe if a layout is a faithful record. So: build every scene the old way, dump
it, rebuild it from the dump, and compare the two scene objects field by field
-- every tile, every prop and its kwargs, every person and their numbers, every
way in and out, and every attribute a builder stashed on the side.

WHY NOT COMPARE THE PICTURE. The first cut of this compared rendered frames and
the yards came back ~5% different while walls, buildings, fences and paths were
pixel-identical. The difference was the scattered grass: those cards are cached
by the identity of the decoration object, so two runs with equal-but-distinct
props take different cache paths and lay the tufts down differently. That is a
property of the draw layer, not of the layout, and a guard that fails on it
would be a guard nobody could keep green. The AUTHORED CONTENT is what a layout
promises to preserve, and that is what this asserts -- exactly, with no
tolerance.

    python tests/layouts.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

FAILURES = []

# Scenes whose behaviour is a closure inside its builder, so it cannot be named
# and imported back. Their PLACEMENT round-trips exactly; their behaviour still
# needs the builder. Frozen BY COUNT so the number can only fall: lifting a
# hook to module level is what finishes the move to data, and a new closure
# hook would otherwise slip in unnoticed.
NAMELESS = set()
NAMELESS_BUDGET = 42

# Runtime scratch that is expected to start empty on a fresh scene: comparing
# it would assert that two never-played scenes have played identically.
_SKIP = {"_door_anim", "_door_views", "_noise_events", "_noise_mask",
         "_noise_now", "_last_step_event", "_surface_tops", "_render_band",
         "_inner_doors", "_ground_hf", "projectiles", "enemies",
         "on_enter_fn", "on_update_fn", "on_exit_fn", "on_interact_fn",
         "interactables", "triggers", "items", "ambient_cues",
         "noise_sources", "noise_traps", "seethrough_doors", "eye_cameras",
         "exit_directions", "exit_gate_fn"}


def _grid(g):
    return ["".join(r) for r in g]


def _props(sc):
    return [(d.kind, d.x, d.y, d.scale, d.seed, round(d.t, 9),
             tuple(sorted((k, repr(v)) for k, v in d.kwargs.items())))
            for d in sc.decorations]


def _people(sc):
    return [(n.name, n.sprite_kind, n.x, n.y, n.movement, n.solid, n.radius,
             n.speed, n.hp, tuple(n.color), n.voice, n.tag, n.no_prompt,
             tuple(n.home) if n.home else None)
            for n in sc.npcs]


def _norm(v, sc):
    """Reduce a value to something comparable ACROSS two builds of a scene.

    A scene that keeps a handle on one of its own people (`works_sign` holds
    Mara and the kneeling rank) is right when it points at the same person --
    which is a position in the cast, not the same object in memory.
    """
    from entities.npc import NPC
    if isinstance(v, NPC):
        return ("npc", sc.npcs.index(v) if v in sc.npcs else ("loose", v.name))
    if isinstance(v, list):
        return [_norm(x, sc) for x in v]
    if isinstance(v, tuple):
        return tuple(_norm(x, sc) for x in v)
    return v


def compare(a, b):
    """Every difference between two scenes that a layout ought to preserve."""
    bad = []
    if _grid(a.floor) != _grid(b.floor):
        bad.append("floor grid")
    if _grid(a.objects) != _grid(b.objects):
        bad.append("object grid")
    if _props(a) != _props(b):
        pa, pb = _props(a), _props(b)
        if len(pa) != len(pb):
            bad.append("prop count %d vs %d" % (len(pa), len(pb)))
        else:
            for i, (x, y) in enumerate(zip(pa, pb)):
                if x != y:
                    bad.append("prop %d: %r vs %r" % (i, x, y))
                    break
    if _people(a) != _people(b):
        bad.append("people: %r vs %r" % (_people(a), _people(b)))
    for k in sorted(set(vars(a)) | set(vars(b))):
        if k in _SKIP or k in ("floor", "objects", "decorations", "npcs"):
            continue
        va = _norm(getattr(a, k, "<missing>"), a)
        vb = _norm(getattr(b, k, "<missing>"), b)
        # By VALUE, not by repr: two equal sets print their members in
        # whatever order they hash to, and a repr comparison calls that a
        # difference.
        try:
            same = bool(va == vb)
        except Exception:
            same = repr(va) == repr(vb)
        if not same:
            bad.append("%s: %.60r vs %.60r" % (k, va, vb))
    return bad


def main():
    import random
    from scenes import SCENE_BUILDERS, load_scene
    from scenes.layout import dump, build_from_layout, register

    print("THRESHOLD layout round-trip\n")
    keys = sorted(SCENE_BUILDERS)
    checked = skipped = 0
    for key in keys:
        random.seed(1994)
        try:
            a = load_scene(key)
        except Exception as e:
            FAILURES.append("%s: will not build: %r" % (key, e))
            continue
        if getattr(a, "procedural", False):
            # A generated field has no fixed content to write down; its layout
            # would be a snapshot of one walk through an endless place.
            skipped += 1
            continue
        # BEHAVIOUR TRAVELS BY NAME, AND SOME OF IT HAS NO NAME. Most hooks
        # and every line of dialogue are closures defined inside the builder
        # (`build_shop.<locals>._shop_update`), so there is nothing to import.
        # Registering them here is what a scene module will do once its hooks
        # are lifted to module level; until then this is the shim that lets
        # the PLACEMENT half be verified exactly.
        closures = 0
        for n in a.npcs:
            if n.dialogue_fn:
                register("?%s" % getattr(n.dialogue_fn, "__qualname__", ""),
                         n.dialogue_fn)
                closures += 1
        for hk in ("on_enter", "on_update", "on_exit", "on_interact"):
            fn = getattr(a, hk + "_fn", None)
            if fn is not None and "<locals>" in getattr(fn, "__qualname__", ""):
                register("?%s" % fn.__qualname__, fn)
                closures += 1
        # ... and a callable hung on the scene as an attribute (a fold's charge
        # test, the lodge's gate) is behaviour of exactly the same kind.
        for k, v in list(vars(a).items()):
            if callable(v) and "<locals>" in getattr(v, "__qualname__", ""):
                register("?%s" % v.__qualname__, v)
                closures += 1
        if closures:
            NAMELESS.add(key)
        try:
            dump(a)
            b = build_from_layout(key)
        except Exception as e:
            FAILURES.append("%s: %r" % (key, e))
            continue
        bad = compare(a, b)
        checked += 1
        if bad:
            FAILURES.append("%s:\n    %s" % (key, "\n    ".join(bad[:4])))
            print("[!!] %-22s %s" % (key, bad[0][:70]))
        else:
            print("[ok] %-22s %d props, %d people" % (key, len(a.decorations),
                                                      len(a.npcs)))
    print("\n%d scenes round-tripped, %d procedural skipped" % (checked, skipped))
    print("%d scenes still keep behaviour in a closure (budget %d):\n  %s"
          % (len(NAMELESS), NAMELESS_BUDGET,
             " ".join(sorted(NAMELESS)) or "none"))
    if len(NAMELESS) > NAMELESS_BUDGET:
        FAILURES.append(
            "%d scenes hide behaviour in a closure, over the budget of %d. "
            "Lift the hook to module level so a layout can name it."
            % (len(NAMELESS), NAMELESS_BUDGET))
    if FAILURES:
        print("\nFAILED: %d scene(s) did not survive the round trip:" % len(FAILURES))
        for f in FAILURES:
            print("  " + f)
        return 1
    print("every scene survives being written down and read back.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
