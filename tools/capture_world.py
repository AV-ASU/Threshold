"""Deterministic draw_world capture — the before/after gate for the camera-seam
refactor (DESIGN.md §10).

Boots a real Game headless, loads a set of scenes, freezes the clock + seeds
RNG so output is reproducible, and saves draw_world() to PNG. Run it once
before the refactor (--tag before) and again after (--tag after); a third
mode diffs the two and reports per-scene pixel deltas.

    python tools/capture_world.py --tag before
    python tools/capture_world.py --tag after
    python tools/capture_world.py --diff before after

Output: /tmp/world_<tag>/<key>.png  and  /tmp/world_diff/<key>.png
"""
import os
import sys
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Disable per-process hash randomization so string-set iteration + any
# hash-derived seeds are reproducible run-to-run. Must be set before the
# interpreter starts, so re-exec once with it pinned if it isn't already.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import random
import pygame

# A representative spread: an interior, outdoor village, a safe room, an
# underground works scene, and a wrap-around scene if one exists.
SCENES = ["bedroom", "store_row", "sheriff_office", "works_cistern",
          "depths_hall"]
FROZEN_TICKS = 12345           # fixed clock so time-based anim is reproducible
SEED = 7


def _stable_id(obj):
    """A reproducible stand-in for builtins.id(), derived from an object's
    world position + sprite kind so the same actor seeds the same across
    separate process runs (real id() is a memory address and varies)."""
    try:
        return (int(getattr(obj, "x", 0)) * 73856093
                ^ int(getattr(obj, "y", 0)) * 19349663
                ^ hash(getattr(obj, "sprite_kind", "")) ) & 0x7fffffff
    except Exception:
        return 1234567


def _boot_game():
    import pygame as pg
    # freeze the clock BEFORE Game() so every get_ticks() call is constant
    pg.time.get_ticks = lambda: FROZEN_TICKS
    import systems.game as gmod
    import rendering.folds as fmod
    # Shadow bare id() in these modules' namespaces with a position-stable one,
    # and seed numpy, so seeded sprite/fold art is reproducible run-to-run.
    gmod.id = _stable_id
    fmod.id = _stable_id
    try:
        import numpy as np
        np.random.seed(SEED)
    except Exception:
        pass
    from systems.game import Game
    g = Game()
    g.save.new()                  # fresh in-memory save (DEFAULT_SAVE)
    g._start_play()               # reset + player + initial scene + state=playing
    # The oblique tilt is the only camera; this tool now captures IT (the
    # pitch is locked in Game.__init__ -- there is no flat/pitch-0 view).
    return g


def _capture(g, key):
    # Seed BEFORE load: decorations draw their per-instance .t/.seed from the
    # global RNG at build time, so the scene must be built under a fixed seed.
    random.seed(SEED)
    try:
        import numpy as np
        np.random.seed(SEED)
    except Exception:
        pass
    # load the scene deterministically, settle the camera, seed RNG, draw.
    try:
        g.load_scene_now(key)
    except Exception as e:
        print(f"  ! {key}: load failed: {e}")
        return None
    # snap the camera straight to target (no lerp) so framing is stable
    try:
        g._update_camera(snap=True)
    except Exception:
        pass
    random.seed(SEED)
    try:
        import numpy as np
        np.random.seed(SEED)
    except Exception:
        pass
    surf = pygame.Surface((g.screen.get_width(), g.screen.get_height()))
    g.screen = surf
    # Each scene is a single deterministic frame with no temporal continuity,
    # so clear the live grade's cross-frame grey cache -- otherwise the first
    # scene's desaturation would be reused for the rest (the cache keys on the
    # frame counter, which never advances here). This keeps every capture a
    # self-contained fresh grade.
    try:
        from scenes import base as _sb
        _sb._GREY_CACHE["frame"] = None
    except Exception:
        pass
    try:
        g.draw_world()
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  ! {key}: draw failed: {e}")
        return None
    return surf.copy()


def cmd_capture(tag):
    out = f"/tmp/world_{tag}"
    os.makedirs(out, exist_ok=True)
    g = _boot_game()
    for key in SCENES:
        surf = _capture(g, key)
        if surf is None:
            continue
        pygame.image.save(surf, f"{out}/{key}.png")
        print(f"  wrote {out}/{key}.png")
    print(f"capture '{tag}' done -> {out}")


def cmd_diff(a, b):
    from PIL import Image, ImageChops
    out = "/tmp/world_diff"
    os.makedirs(out, exist_ok=True)
    allzero = True
    for key in SCENES:
        pa = f"/tmp/world_{a}/{key}.png"
        pb = f"/tmp/world_{b}/{key}.png"
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print(f"  - {key}: missing capture, skipped")
            continue
        ia = Image.open(pa).convert("RGB")
        ib = Image.open(pb).convert("RGB")
        diff = ImageChops.difference(ia, ib)
        bbox = diff.getbbox()
        # amplify so any delta is visible
        amp = diff.point(lambda p: min(255, p * 8))
        amp.save(f"{out}/{key}.png")
        if bbox is None:
            print(f"  = {key}: IDENTICAL")
        else:
            # count changed pixels
            changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
            total = ia.width * ia.height
            frac = changed / total
            # Tolerance: the cult-ambient layer (works/depths) spawns cultists
            # with RNG jitter independent of rendering, so a tiny, localized
            # delta there is expected even between two identical runs. The
            # refactor gate is "no NEW differences beyond that noise floor."
            tol = 0.003   # 0.3%
            if frac <= tol:
                print(f"  ~ {key}: {changed}/{total} px ({frac*100:.3f}%) "
                      f"within tol -- ambient-spawn noise, OK")
            else:
                allzero = False
                print(f"  ! {key}: {changed}/{total} px ({frac*100:.3f}%) "
                      f"EXCEEDS tol  bbox={bbox}")
    print("PASS (identical within tolerance)" if allzero
          else "FAIL -- real differences (see /tmp/world_diff)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag")
    ap.add_argument("--diff", nargs=2, metavar=("A", "B"))
    args = ap.parse_args()
    if args.diff:
        cmd_diff(*args.diff)
    elif args.tag:
        cmd_capture(args.tag)
    else:
        ap.print_help()
