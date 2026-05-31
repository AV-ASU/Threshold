"""Fold-pursuit guard (Stage 3): the cult follows through hidden FOLDS,
not through mundane architecture.

The design (the cult moves through the world's wrongness, not your ladders):
  - Flee through a direction-gated FOLD with a cultist hot on your heels
    and that one pursuer follows "a beat behind", re-emerging at the seam.
  - Flee through a DOOR / LADDER / ROPE (a mundane exit) and the chase is
    shaken -- architecture is player-only.
  - The pursuer never spawns on top of the player (the beat-behind grace).
  - A refuge (SAFE_SCENES) is never breached, even via a fold.

Run from repo root:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python tests/fold_pursuit.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from systems.game import Game
from constants import TILE
from entities.npc import NPC


def _boot():
    g = Game()
    g.save.new()
    g._start_play()
    g.load_scene_now("cornfield_maze", "default")
    return g


def _stand_on(g, tx, ty):
    g.player.x = tx * TILE + TILE // 2
    g.player.y = ty * TILE + TILE // 2


def _find_exit_tile(g, *, fold):
    """The cornfield maze is procedurally generated, so exit tiles move
    between loads. Locate a fold (direction-gated) or mundane exit char in
    the *actual* loaded scene and return (tx, ty, char)."""
    for ty, row in enumerate(g.scene.objects):
        for tx, ch in enumerate(row):
            if ch not in g.scene.exits:
                continue
            is_fold = ch in g.scene.exit_directions
            if is_fold == fold:
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


def test_passage_carries_pursuer():
    # A seamless outdoor PASSAGE (both scenes in the open world) is the
    # cult's ground too -- they follow across it, just like a fold.
    g = _boot()
    g.load_scene_now("brimley", "default")    # an outdoor town, full of passages
    target, spawn, ch = None, None, None
    for c, (tgt, sp) in g.scene.exits.items():
        from systems.game import SEAMLESS_WORLD_SCENES
        if tgt in SEAMLESS_WORLD_SCENES and c not in g.scene.exit_directions:
            target, spawn, ch = tgt, sp, c
            break
    assert ch is not None, "brimley should have a seamless passage exit"
    pos = g.scene.find_marker(ch)
    _stand_on(g, pos[0], pos[1])
    _add_hot_cultist(g)
    g._note_fold_pursuit((target, spawn))
    assert g._fold_pursuer is not None, "a seamless passage must carry a pursuer"
    print("  OK  a hot pursuer follows through an outdoor passage")


def test_interior_door_loses_pursuer():
    # A fade transition into an INTERIOR (door / ladder / rope) shakes the
    # chase -- ordinary architecture is the player-only escape.
    g = _boot()
    g.load_scene_now("brimley", "default")
    from systems.game import SEAMLESS_WORLD_SCENES
    target, spawn, ch = None, None, None
    for c, (tgt, sp) in g.scene.exits.items():
        if tgt not in SEAMLESS_WORLD_SCENES and c not in g.scene.exit_directions:
            target, spawn, ch = tgt, sp, c       # e.g. brimley -> shop (a door)
            break
    assert ch is not None, "brimley should have an interior-door exit"
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
    g._note_fold_pursuit(("house", "from_cornfield_maze"))   # house is SAFE
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


if __name__ == "__main__":
    test_fold_carries_pursuer()
    test_passage_carries_pursuer()
    test_interior_door_loses_pursuer()
    test_no_spawn_during_grace()
    test_safe_scene_never_breached()
    test_fold_watcher_binds_on_hit()
    test_fold_watcher_misses_on_high_roll()
    test_fold_watcher_never_exceeds_max()
    print("All fold-pursuit guards held.")
