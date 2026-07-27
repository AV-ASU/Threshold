"""Fold-pursuit guard (Stage 3): the cult follows through hidden FOLDS,
not through mundane architecture.

The design (the cult moves through the world's wrongness, not your ladders):
  - Flee through a direction-gated FOLD with a cultist hot on your heels
    and that one pursuer follows "a beat behind", re-emerging at the seam.
  - Flee through a DOOR / LADDER / ROPE or a seamless outdoor PASSAGE (any
    ordinary crossing) and the chase is shaken -- a chaser does not cross a
    scene boundary, only a rift fold (play-notes narrowing of DESIGN.md §7).
  - The pursuer never spawns on top of the player (the beat-behind grace).
  - A refuge (SAFE_SCENES) is never breached, even via a fold.

Run from repo root:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python tests/fold_pursuit.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
# SDL converts SIGTERM into a quit event instead of dying, so `timeout`
# and CI cancellation cannot stop a harness (it runs to completion while
# the wrapper reports 124). Keep the default kill behavior in tests.
os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from systems.game import Game
from constants import TILE
from entities.npc import NPC


def _boot(scene="schoolhouse"):
    # The maze's cross-scene discovery folds were cut (2026-07, the rite is
    # the grove's only thread in), so fold-carry tests boot the schoolhouse,
    # whose rite pane ('O', walked north -> effigy_grove) is the surviving
    # cross-scene fold. The gate doesn't matter here: these tests drive
    # _note_fold_pursuit / _roll_fold_watcher directly. The same-scene
    # relocation test still boots the maze (the I/Q relocations live there).
    g = Game()
    g.save.new()
    g._start_play()
    g.load_scene_now(scene, "default")
    return g


def _stand_on(g, tx, ty):
    g.player.x = tx * TILE + TILE // 2
    g.player.y = ty * TILE + TILE // 2


def _find_exit_tile(g, *, fold, same_scene=False):
    """The cornfield maze is procedurally generated, so exit tiles move
    between loads. Locate a fold (direction-gated) or mundane exit char in
    the *actual* loaded scene and return (tx, ty, char). `same_scene`
    selects the in-maze relocation folds (target == the scene itself);
    by default those are skipped (they relocate, they don't carry)."""
    for ty, row in enumerate(g.scene.objects):
        for tx, ch in enumerate(row):
            if ch not in g.scene.exits:
                continue
            is_fold = ch in g.scene.exit_directions
            is_same = g.scene.exits[ch][0] == g.scene.key
            if is_fold == fold and is_same == same_scene:
                return tx, ty, ch
    raise AssertionError(f"no {'fold' if fold else 'mundane'} exit in scene")


def _add_hot_cultist(g, offset=40):
    npc = NPC(g.player.x + offset, g.player.y, "", "cultist",
              movement="chaser")
    npc.tag = "cult_regular"
    npc._cult_state = "chase"
    npc._last_seen_pos = (g.player.x, g.player.y)
    g.scene.add_npc(npc)
    return npc


def _chasers(g):
    return sum(1 for n in g.scene.npcs
               if getattr(n, "movement", "") == "chaser"
               and getattr(n, "alive", True))


def test_fold_carries_pursuer():
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    target, spawn = g.scene.exits[ch]
    _stand_on(g, tx, ty)
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    assert g._fold_pursuer is not None, "a fold crossing must stash a pursuer"
    g.load_scene_now(target, spawn)
    et = g.scene._last_entry_exit_tile
    _stand_on(g, et[0] + 4, et[1])            # step clear of the seam
    for _ in range(120):
        g._tick_fold_pursuit(0.05)
    assert _chasers(g) >= 1, "the pursuer must follow through the fold"
    print("  OK  a hot pursuer follows through a fold")


def test_passage_does_not_carry_pursuer():
    # A seamless outdoor PASSAGE (both scenes in the open world) is an
    # ORDINARY crossing now, not a fold-carry: a chaser follows within a
    # scene and across a direction-gated rift fold, never across a scene
    # boundary (play-notes narrowing of DESIGN.md §7).
    g = _boot()
    # a street on the town's own network: seamless to the roads either side
    g.load_scene_now("store_row", "default")
    target, spawn, ch = None, None, None
    for c, (tgt, sp) in g.scene.exits.items():
        from systems.game import SEAMLESS_WORLD_SCENES
        if tgt in SEAMLESS_WORLD_SCENES and c not in g.scene.exit_directions:
            target, spawn, ch = tgt, sp, c
            break
    assert ch is not None, "the street should have a seamless passage exit"
    pos = g.scene.find_marker(ch)
    _stand_on(g, pos[0], pos[1])
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    assert g._fold_pursuer is None, "a seamless passage no longer carries a pursuer"
    print("  OK  a seamless passage does NOT carry a pursuer (ordinary crossing)")


def test_interior_door_loses_pursuer():
    # A fade transition into an INTERIOR (door / ladder / rope) shakes the
    # chase -- ordinary architecture is the player-only escape.
    g = _boot()
    # a YARD: not seamless (an island, DESIGN.md §15), and its house door is
    # the fade transition this is about.
    g.load_scene_now("shop_yard", "default")
    from systems.game import SEAMLESS_WORLD_SCENES
    target, spawn, ch = None, None, None
    for c, (tgt, sp) in g.scene.exits.items():
        if tgt not in SEAMLESS_WORLD_SCENES and c not in g.scene.exit_directions:
            target, spawn, ch = tgt, sp, c       # e.g. shop_yard -> shop
            break
    assert ch is not None, "the yard should have an interior-door exit"
    pos = g.scene.find_marker(ch)
    _stand_on(g, pos[0], pos[1])
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    assert g._fold_pursuer is None, "an interior door must clear the stash"
    g.load_scene_now(target, spawn)
    before = _chasers(g)
    for _ in range(120):
        g._tick_fold_pursuit(0.05)
    assert _chasers(g) == before, "an interior door must NOT carry a pursuer"
    print("  OK  an interior door (door/ladder/rope) shakes the chase")


def test_no_spawn_during_grace():
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    target, spawn = g.scene.exits[ch]
    _stand_on(g, tx, ty)
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    g.load_scene_now(target, spawn)
    et = g.scene._last_entry_exit_tile
    _stand_on(g, et[0], et[1])                # linger ON the seam
    g._tick_fold_pursuit(0.05)
    g._tick_fold_pursuit(0.05)               # still inside the beat-behind grace
    assert _chasers(g) == 0, "must not spawn during the beat-behind grace"
    print("  OK  no premature spawn on top of the player")


def test_safe_scene_never_breached():
    # A fold into a refuge (defensive guard -- no such fold exists today,
    # but the rule must hold if one is ever authored).
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    _stand_on(g, tx, ty)
    _add_hot_cultist(g)
    g._note_fold_pursuit(("lodge", "from_cornfield_maze"))   # house is SAFE
    assert g._fold_pursuer is None, "the refuge is never breached, even via a fold"
    print("  OK  a fold into a refuge is refused")


def test_fold_watcher_binds_on_hit():
    # A fold traversal with the RNG hit binds the curse (+1 Watcher seed).
    import random as _r
    from systems.game import FOLD_WATCHER_CHANCE
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    _stand_on(g, tx, ty)
    g._cursed = False
    g._watchers = []
    target = g.scene.exits[ch][0]
    orig = _r.random
    try:
        _r.random = lambda: 0.0   # guaranteed < chance
        g._roll_fold_watcher((target, "default"))
    finally:
        _r.random = orig
    if target in __import__("systems.game", fromlist=["SAFE_SCENES"]).SAFE_SCENES:
        assert not g._cursed, "a fold into a refuge never binds a Watcher"
        print("  OK  fold-watcher: refuge fold binds nothing")
    else:
        assert g._cursed, "a fold-watcher hit binds the curse"
        assert FOLD_WATCHER_CHANCE == 0.05, "the documented 1/20 odds"
        print("  OK  fold-watcher: a hit binds the curse (the +1 seed)")


def test_fold_watcher_misses_on_high_roll():
    import random as _r
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    _stand_on(g, tx, ty)
    g._cursed = False
    g._watchers = []
    target = g.scene.exits[ch][0]
    orig = _r.random
    try:
        _r.random = lambda: 0.99   # guaranteed >= chance
        g._roll_fold_watcher((target, "default"))
    finally:
        _r.random = orig
    assert not g._cursed, "a missed roll binds nothing"
    print("  OK  fold-watcher: a missed roll binds nothing")


def test_fold_watcher_never_exceeds_max():
    # At the 5-Watcher ceiling, even a guaranteed hit adds nothing.
    import random as _r
    from systems.game import WATCHER_MAX
    g = _boot()
    tx, ty, ch = _find_exit_tile(g, fold=True)
    _stand_on(g, tx, ty)
    target = g.scene.exits[ch][0]
    if target in __import__("systems.game", fromlist=["SAFE_SCENES"]).SAFE_SCENES:
        print("  OK  fold-watcher: (skip cap test -- only fold here is a refuge)")
        return
    g._cursed = True
    g._watchers = [object() for _ in range(WATCHER_MAX)]
    orig = _r.random
    try:
        _r.random = lambda: 0.0
        g._roll_fold_watcher((target, "default"))
    finally:
        _r.random = orig
    assert len(g._watchers) == WATCHER_MAX, "a fold never pushes past WATCHER_MAX"
    print("  OK  fold-watcher: +1 never fires at the WATCHER_MAX ceiling")


def test_same_scene_reloc_silent_and_seamless():
    # The maze 'I'/'Q' relocations are same-scene folds: crossing relocates
    # the player with NO load, NO pursuer stash (the chaser is still
    # physically in the room), and NO visible frame -- the lie is the world
    # itself, never a gold seam.
    g = _boot("cornfield_maze")
    tx, ty, ch = _find_exit_tile(g, fold=True, same_scene=True)
    target, spawn = g.scene.exits[ch]
    assert target == g.scene.key, "the relocation targets the maze itself"
    _stand_on(g, tx, ty)
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    assert g._fold_pursuer is None, "a same-scene relocation never stashes"
    assert all(f["target"].key != g.scene.key for f in g._folds), \
        "a relocation fold must never join the seen-fold (frame) list"
    before = g.scene
    sdx = g.player.x - g.cam_x
    sdy = g.player.y - g.cam_y
    g.cross_fold(target, spawn)
    assert g.scene is before, "a relocation must not reload the scene"
    assert (g.player.x, g.player.y) == before.spawns[spawn], \
        "relocated to the fold's destination spawn"
    assert abs((g.player.x - g.cam_x) - sdx) < 1e-6, \
        "the camera carries the screen offset (the swap is invisible)"
    assert abs((g.player.y - g.cam_y) - sdy) < 1e-6
    print("  OK  a same-scene relocation is silent, loadless, camera-carried")


if __name__ == "__main__":
    test_fold_carries_pursuer()
    test_passage_does_not_carry_pursuer()
    test_interior_door_loses_pursuer()
    test_no_spawn_during_grace()
    test_safe_scene_never_breached()
    test_fold_watcher_binds_on_hit()
    test_fold_watcher_misses_on_high_roll()
    test_fold_watcher_never_exceeds_max()
    test_same_scene_reloc_silent_and_seamless()
    print("All fold-pursuit guards held.")
