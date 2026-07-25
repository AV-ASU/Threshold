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
# SDL converts SIGTERM into a quit event instead of dying, so `timeout`
# and CI cancellation cannot stop a harness (it runs to completion while
# the wrapper reports 124). Keep the default kill behavior in tests.
os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")
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


# Sub-tile samples per tile edge for the fine flood. A tree blocks as a
# ROUND foot inside its cell now (scenes/terrain.py `tree_footprint`), so a
# tile-granular walk map is no longer the truth: it calls a whole cell solid
# when most of it is clear, and its 4-way steps cannot see the DIAGONAL gaps
# between trunks -- which are the way a stand of trees is meant to be
# crossed. Four samples per tile resolves a gap of about 8 world units; the
# diagonal gaps between neighbouring trees run near 18.
_FINE = 4


def _walkable(sc, tx, ty):
    if not (0 <= tx < sc.w and 0 <= ty < sc.h):
        return False
    return (not is_object_solid(sc.objects[ty][tx])
            and not is_floor_solid(sc.floor[ty][tx]))


def _has_plants(sc):
    from scenes.terrain import OBJECT_DEFS
    for row in sc.objects:
        for ch in row:
            od = OBJECT_DEFS.get(ch) or {}
            if od.get("kind") == "tree" and od.get("solid"):
                return True
    return False


def _flood(sc, sx, sy):
    """Walkable tiles reachable from (sx, sy).

    In a scene with solid plants this floods at SUB-TILE resolution through
    `sc.is_solid_at` -- the same predicate the player's own movement uses --
    and then reports which tiles were entered. The player collides as a
    POINT, so anywhere a point fits is somewhere they can stand, and the
    coarse map was rejecting real routes. Stepping stays 4-way: movement
    resolves x and y separately, so a pure diagonal squeeze through a corner
    where both orthogonal neighbours block is not actually walkable.
    """
    from collections import deque
    if not _has_plants(sc):
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

    step = TILE / float(_FINE)
    W, H = sc.w * _FINE, sc.h * _FINE

    def clear(ix, iy):
        if not (0 <= ix < W and 0 <= iy < H):
            return False
        px, py = (ix + 0.5) * step, (iy + 0.5) * step
        if is_floor_solid(sc.floor[int(py // TILE)][int(px // TILE)]):
            return False
        return not sc.is_solid_at(px, py)

    s0 = (int(sx * _FINE + _FINE // 2), int(sy * _FINE + _FINE // 2))
    if not clear(*s0):
        # the spawn's own sample may land in a trunk; try the rest of its tile
        cands = [(sx * _FINE + a, sy * _FINE + b)
                 for a in range(_FINE) for b in range(_FINE)]
        cands = [c for c in cands if clear(*c)]
        if not cands:
            return set()
        s0 = cands[0]
    seen_f = {s0}
    q = deque([s0])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if n not in seen_f and clear(*n):
                seen_f.add(n)
                q.append(n)
    return {(ix // _FINE, iy // _FINE) for ix, iy in seen_f}


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
        if getattr(sc, "procedural", False):
            continue                    # infinite generator field: no flood-fill
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
    """Each CANONICAL_EVIDENCE beat on Mara's trail (NARRATIVE §6, DESIGN.md
    §9) drives the King-gate and the visibility floor. If a beat's only
    `_evidence(...)` call site is renamed or deleted, the threat tuning
    silently changes and the King may become unreachable -- with no test to
    catch it. Statically scan the scene source tree for `_evidence(game,
    "<name>"` call sites and assert every canonical name is still wired into
    at least one scene. (grant_receipt wraps the receipt beat, so its call
    site lives in dialogue.py -- also under scenes/.)"""
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


# Per-run `self._x` attributes that are deliberately NOT cleared in
# _reset_run_state, with the reason. The guard below allows exactly these;
# any NEW per-run attr assigned outside __init__ must be reset or added here
# (with a reason), so a missed reset becomes a test failure, not a cross-run
# bug. Keep this list tight -- it is the audited set of legitimate exceptions.
_RESET_EXEMPT = {
    # Opening-drive state: (re)initialised wholesale by _begin_opening each
    # time the opening runs; never carries between play sessions.
    "_opening_t", "_opening_scroll", "_opening_speed", "_opening_phase",
    "_opening_phase_t", "_opening_stalls_left", "_opening_grain",
    "_opening_stars",
    # Pure render caches -- rebuilt on demand, hold no run state.
    "_vignette_surf", "_outdoor_vignette_surf",
    # Per-frame scratch, reset at the top of each draw_world.
    "_overlay_dark_used",
    # Dev perf overlay (F1): a diagnostic toggle + last-frame dt readout. Meant
    # to persist across New Game like fullscreen -- not run state.
    "_show_fps", "_last_dt",
    # World render scale (F2): a display/perf setting, persists like fullscreen.
    "_render_scale", "_world_buf", "_win", "_render_s",
    # Idle-King body card: a pure render cache, refreshed on its own interval.
    "_idle_king_card", "_idle_king_card_frame",
}


def check_reset_coverage():
    """Every per-run `self._x` assigned OUTSIDE __init__ must be cleared in
    _reset_run_state (so a New Game starts clean) OR be on the audited
    _RESET_EXEMPT allowlist. This kills the missed-reset bug class: adding a
    new per-run field without resetting it fails here instead of leaking from
    one run into the next."""
    import re
    path = os.path.join(PROJECT_ROOT, "systems", "game.py")
    with open(path, encoding="utf-8") as f:
        src = f.read().splitlines()

    def method_span(name):
        start = end = None
        indent = None
        for i, line in enumerate(src):
            if re.match(rf"\s*def {name}\(", line):
                start = i
                indent = len(line) - len(line.lstrip())
                continue
            if start is not None and i > start and line.strip():
                cur = len(line) - len(line.lstrip())
                if cur <= indent:
                    end = i
                    break
        return start, (end if end is not None else len(src))

    def assigns(lo, hi):
        out = set()
        for line in src[lo:hi]:
            for m in re.finditer(r"self\.(_[a-zA-Z]\w*)\s*=", line):
                out.add(m.group(1))
        return out

    i0, i1 = method_span("__init__")
    r0, r1 = method_span("_reset_run_state")
    reset_attrs = assigns(r0, r1)
    # All per-run attrs assigned somewhere outside __init__ and reset.
    outside = set()
    for i, line in enumerate(src):
        if (i0 <= i < i1) or (r0 <= i < r1):
            continue
        for m in re.finditer(r"self\.(_[a-zA-Z]\w*)\s*=", line):
            outside.add(m.group(1))

    errors = 0
    for attr in sorted(outside):
        if attr in reset_attrs or attr in _RESET_EXEMPT:
            continue
        errors += fail(
            f"per-run attribute '{attr}' is assigned outside __init__ but is "
            f"neither reset in _reset_run_state nor in _RESET_EXEMPT -- it will "
            f"leak from one run into the next. Reset it, or allowlist it with a "
            f"reason in tests/smoke.py:_RESET_EXEMPT."
        )
    return errors


def check_sprite_seed_variants():
    """The cultist mask variant is (sprite_seed >> 3) % 6. Draw sites
    used to seed from id(), whose 16-byte alignment locked the pick to
    EVEN variants -- half the masks never spawned. Guard the fix: the
    position-derived seed must cover all six variants over grid-
    quantized spawn coords (multiples of 16 are the worst case), and
    both actor classes must carry it."""
    fails = 0
    from entities.npc import NPC, sprite_seed_for
    from entities.enemy import Enemy
    seen = set()
    for a in range(1, 60):
        for b in range(1, 60):
            seen.add((sprite_seed_for(a * 32 + 16, b * 32 + 16) >> 3) % 6)
    if seen != set(range(6)):
        fail(f"sprite_seed_for covers only variants {sorted(seen)} "
             f"on grid coords (all 6 masks must be able to spawn)")
        fails += 1
    n = NPC(100, 200, "x", "cultist")
    e = Enemy(100, 200, kind="cultist")
    if getattr(n, "sprite_seed", None) != sprite_seed_for(100, 200) \
            or getattr(e, "sprite_seed", None) != sprite_seed_for(100, 200):
        fail("NPC/Enemy sprite_seed not wired to sprite_seed_for")
        fails += 1
    return fails


def check_no_dead_labels():
    """Every NPC movement mode handled in entities/npc.py and every NPC sprite
    kind drawn in rendering/sprites_npc.py must be REACHABLE -- assigned or
    spawned somewhere in the game. This kills the dead-label bug class: a
    movement branch or a sprite branch left behind by cut content (the
    patrol/stalker/follower modes, the cut haunted-house sprite kinds) fails
    HERE instead of lingering as unreachable code that survives 'cleanups'.
    A kind/mode that is genuinely runtime-only (assigned via self.movement =
    "x") still counts, because that assignment matches too."""
    import glob
    import re

    def repo_sources():
        for sub in ("scenes", "systems", "entities", "rendering", "ui"):
            for path in glob.glob(os.path.join(PROJECT_ROOT, sub, "*.py")):
                with open(path, encoding="utf-8") as f:
                    yield path, f.read()

    npc_src = open(os.path.join(PROJECT_ROOT, "entities", "npc.py"),
                   encoding="utf-8").read()
    spr_src = open(os.path.join(PROJECT_ROOT, "rendering", "sprites_npc.py"),
                   encoding="utf-8").read()
    sources = list(repo_sources())
    errors = 0

    # 1) movement modes handled in the update dispatch must be assigned.
    handled = set(re.findall(r'self\.movement == "(\w+)"', npc_src))
    assigned = set()
    for _p, src in sources:
        assigned |= set(re.findall(r'movement\s*=\s*"(\w+)"', src))
    for m in sorted(handled - assigned):
        errors += fail(f"movement mode '{m}' is handled in npc.py but never "
                       f"assigned anywhere -- dead label (delete it)")

    # 2) NPC sprite kinds with a draw branch must be spawned (the quoted
    #    literal appears in game code outside the draw file itself).
    drawn = set(re.findall(r'kind == "(\w+)"', spr_src))
    spawn_text = "".join(src for _p, src in sources
                         if not _p.endswith("sprites_npc.py"))
    for k in sorted(drawn):
        if f'"{k}"' not in spawn_text:
            errors += fail(f"sprite kind '{k}' has a draw branch in "
                           f"sprites_npc.py but is never spawned -- dead label")
    return errors


def check_no_raw_furniture_tiles():
    """No scene's FINAL object map may carry a raw furniture tile
    (t/b/c/k/f: table, bed, chair, stove, fireplace). The tilt render's
    occluder scan collects only wall/door/window/billboard/counter/rack
    chars, so a raw furniture tile is an INVISIBLE solid under the only
    shipping camera -- a phantom collision block the player bumps, with
    any [E] cue or tabletop prop floating over bare floor (2026-07 audit:
    13 such tiles across 7 scenes, incl. the lodge fireplace and the
    Scriptorium's evidence desks). Place furniture with add_furniture
    (a real projected volume + an 'x'/'X' footprint) instead."""
    from scenes import SCENE_BUILDERS, load_scene
    errors = 0
    for key in SCENE_BUILDERS:
        sc = load_scene(key)
        if getattr(sc, "procedural", False):
            continue                    # infinite generator field: no full scan
        for ty, row in enumerate(sc.objects):
            rr = row if isinstance(row, str) else "".join(row)
            for tx, ch in enumerate(rr):
                if ch in "tbckf":
                    errors += fail(
                        f"{key}: raw furniture tile '{ch}' at ({tx},{ty}) "
                        f"-- invisible under tilt; use add_furniture")
    return errors


def check_no_diagonal_wall_joins():
    """A _SLAB_SCENES scene renders its walls as THIN slabs, so two walls that
    meet only at a DIAGONAL (the shared corner tile missing) end in disconnected
    stubs instead of a connected corner (the maintainer's "no walls like that"
    rule, 2026-07). Fail any slab scene with such a join -- close the corner by
    making one of its open bridge tiles a wall so the walls connect
    orthogonally into a clean (rounded) L."""
    from scenes import load_scene
    from scenes.terrain import _SLAB_SCENES, diagonal_wall_joins
    errors = 0
    for key in _SLAB_SCENES:
        sc = load_scene(key)
        for a, b in diagonal_wall_joins(sc):
            errors += fail(
                f"{key}: diagonal-only wall join {a}<->{b} -- thin walls meet "
                f"at a point; add the missing corner tile to connect them")
    return errors


def main():
    failures = 0
    print("[1/10] scene builders ...")
    failures += check_scene_builds()
    print("[2/10] spawn walkability + non-overlapping with exits ...")
    failures += check_spawns_walkable()
    print("[3/10] exits resolve to target spawns ...")
    failures += check_exits_resolve()
    print("[4/10] room passability (flood-fill spawns -> exits/props) ...")
    failures += check_passability()
    print("[5/10] canonical evidence beats wired to scenes ...")
    failures += check_canonical_evidence_wired()
    print("[6/10] per-run state reset coverage ...")
    failures += check_reset_coverage()
    print("[7/10] sprite-seed variant coverage (all 6 cultist masks) ...")
    failures += check_sprite_seed_variants()
    print("[8/10] no dead movement-mode / sprite-kind labels ...")
    failures += check_no_dead_labels()
    print("[9/10] no raw furniture tiles (invisible under tilt) ...")
    failures += check_no_raw_furniture_tiles()
    print("[10/10] no diagonal-only wall joins in slab scenes ...")
    failures += check_no_diagonal_wall_joins()
    if failures:
        print(f"\n{failures} failure(s).")
        sys.exit(1)
    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
