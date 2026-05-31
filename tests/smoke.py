"""Smoke test for THRESHOLD.

Run from the project root with:

    python tests/smoke.py

The test sets SDL to dummy drivers itself, so no env-var ceremony is
needed. It verifies three invariants in order, fast-failing on the first
broken one:

  1. Every scene in SCENE_BUILDERS builds without raising.
  2. Every named spawn point sits on a non-solid (object + floor) tile,
     and is NOT on an exit tile (which would re-trigger the transition
     immediately and loop).
  3. Every exit (target_scene, spawn_id) resolves -- target exists in
     SCENE_BUILDERS and target.spawns has the named spawn id.
  4. Every named spawn is reachable from its room's other spawns/exits
     (flood-fill passability).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Resolve project root from this file's location so the test runs from
# anywhere (project root, tests dir, IDE, etc.) without env vars.
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from scenes import SCENE_BUILDERS, load_scene
from scenes.base import is_object_solid, is_floor_solid, TILE


def fail(msg):
    print(f"FAIL: {msg}")
    return 1


def check_scene_builds():
    errors = 0
    for key in SCENE_BUILDERS:
        try:
            sc = load_scene(key)
        except Exception as e:
            errors += fail(f"build {key}: {e}")
            continue
        if sc is None or sc.w <= 0 or sc.h <= 0:
            errors += fail(f"build {key}: empty scene")
    return errors


def check_spawns_walkable():
    errors = 0
    for key in SCENE_BUILDERS:
        sc = load_scene(key)
        for spawn_name, (px, py) in sc.spawns.items():
            tx = int(px // TILE); ty = int(py // TILE)
            if not (0 <= tx < sc.w and 0 <= ty < sc.h):
                errors += fail(
                    f"{key}/{spawn_name}: spawn ({tx},{ty}) out of bounds "
                    f"{(sc.w, sc.h)}"
                )
                continue
            obj = sc.objects[ty][tx]
            flo = sc.floor[ty][tx]
            if is_object_solid(obj):
                errors += fail(
                    f"{key}/{spawn_name}: spawn ({tx},{ty}) on solid object "
                    f"'{obj}'"
                )
            if is_floor_solid(flo):
                errors += fail(
                    f"{key}/{spawn_name}: spawn ({tx},{ty}) on solid floor "
                    f"'{flo}'"
                )
            for ech in sc.exits:
                if obj == ech:
                    errors += fail(
                        f"{key}/{spawn_name}: spawn ({tx},{ty}) is ON exit "
                        f"tile '{ech}' -> would re-trigger transition"
                    )
    return errors


def check_exits_resolve():
    errors = 0
    scenes = {k: load_scene(k) for k in SCENE_BUILDERS}
    for key, sc in scenes.items():
        for ech, (target, spawn_id) in sc.exits.items():
            if target not in scenes:
                errors += fail(f"{key} exit '{ech}' -> unknown target '{target}'")
                continue
            if spawn_id not in scenes[target].spawns:
                errors += fail(
                    f"{key} exit '{ech}' -> {target}: spawn '{spawn_id}' "
                    f"missing (have: {sorted(scenes[target].spawns)})"
                )
    return errors


def _walkable(sc, tx, ty):
    if not (0 <= tx < sc.w and 0 <= ty < sc.h):
        return False
    return (not is_object_solid(sc.objects[ty][tx])
            and not is_floor_solid(sc.floor[ty][tx]))


def _flood(sc, sx, sy):
    from collections import deque
    seen = set()
    if not _walkable(sc, sx, sy):
        return seen
    seen.add((sx, sy))
    q = deque([(sx, sy)])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if n not in seen and _walkable(sc, n[0], n[1]):
                seen.add(n)
                q.append(n)
    return seen


def _reachable(region, tx, ty):
    """A point counts as reachable if its tile -- or any 4-adjacent
    tile -- is in the walkable region (you interact with / exit from an
    adjacent tile, and exit tiles are themselves walkable)."""
    if (tx, ty) in region:
        return True
    return any((tx + dx, ty + dy) in region
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def check_passability():
    """Flood-fill the walkable tiles from each scene's default spawn and
    verify nothing is walled off: every named spawn, every exit tile,
    and every interaction point (furniture/prop *_pos, hide spots,
    talkable NPCs) must be reachable. Guards against sized furniture or
    decor footprints splitting a room or blocking a door."""
    errors = 0
    for key in SCENE_BUILDERS:
        sc = load_scene(key)
        if not sc.spawns:
            continue
        start = sc.spawns.get("default") or next(iter(sc.spawns.values()))
        sx, sy = int(start[0] // TILE), int(start[1] // TILE)
        if not _walkable(sc, sx, sy):
            errors += fail(f"{key}: default spawn ({sx},{sy}) not walkable")
            continue
        region = _flood(sc, sx, sy)
        for nm, (px, py) in sc.spawns.items():
            tx, ty = int(px // TILE), int(py // TILE)
            if not _reachable(region, tx, ty):
                errors += fail(f"{key}: spawn '{nm}' ({tx},{ty}) unreachable "
                               f"from default spawn")
        for ech in sc.exits:
            for ty in range(sc.h):
                for tx in range(sc.w):
                    if sc.objects[ty][tx] == ech or sc.floor[ty][tx] == ech:
                        if not _reachable(region, tx, ty):
                            errors += fail(f"{key}: exit '{ech}' ({tx},{ty}) "
                                           f"unreachable")
        pts = []
        for a in dir(sc):
            if a.startswith("_") and a.endswith("_pos"):
                v = getattr(sc, a, None)
                if (isinstance(v, tuple) and len(v) == 2
                        and all(isinstance(c, (int, float)) for c in v)):
                    pts.append((a, v))
        for hs in getattr(sc, "hide_spots", []):
            pts.append(("hide_spot", (hs[0], hs[1])))
        for n in getattr(sc, "npcs", []):
            if not getattr(n, "no_prompt", False):
                pts.append((f"npc:{getattr(n, 'name', '?')}", (n.x, n.y)))
        for lbl, (px, py) in pts:
            tx, ty = int(px // TILE), int(py // TILE)
            if not _reachable(region, tx, ty):
                errors += fail(f"{key}: {lbl} ({tx},{ty}) unreachable")
    return errors


def check_canonical_evidence_wired():
    """Each of the six CANONICAL_EVIDENCE beats drives the King-gate and the
    visibility floor. If a beat's only `_evidence(...)` call site is renamed
    or deleted, the threat tuning silently changes and the King may become
    unreachable -- with no test to catch it. Statically scan the scene source
    tree for `_evidence(game, "<name>"` call sites and assert every canonical
    name is still wired into at least one scene."""
    import glob
    import re
    from scenes.dialogue import CANONICAL_EVIDENCE

    surfaced = set()
    call_re = re.compile(r"""_evidence\(\s*game\s*,\s*['"]([a-z_]+)['"]""")
    for path in glob.glob(os.path.join(PROJECT_ROOT, "scenes", "*.py")):
        with open(path, encoding="utf-8") as f:
            surfaced.update(call_re.findall(f.read()))

    errors = 0
    for name in CANONICAL_EVIDENCE:
        if name not in surfaced:
            errors += fail(
                f"canonical evidence '{name}' has no _evidence(game, ...) "
                f"call site in scenes/ -- the King-gate beat is unreachable"
            )
    return errors


def main():
    failures = 0
    print("[1/5] scene builders ...")
    failures += check_scene_builds()
    print("[2/5] spawn walkability + non-overlapping with exits ...")
    failures += check_spawns_walkable()
    print("[3/5] exits resolve to target spawns ...")
    failures += check_exits_resolve()
    print("[4/5] room passability (flood-fill spawns -> exits/props) ...")
    failures += check_passability()
    print("[5/5] canonical evidence beats wired to scenes ...")
    failures += check_canonical_evidence_wired()
    if failures:
        print(f"\n{failures} failure(s).")
        sys.exit(1)
    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
