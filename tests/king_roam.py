"""Roaming-King guards (KING_PROMPT rework): the persistent, world-positioned
apex that idles down the road, arms at the 3-evidence gate, roams the surface
scene-to-scene, hunts on sight, and de-escalates when you break his sight.

The rules these lock (settled in the opening design conversation):
  - IDLE until 3 evidence; the gate ARMS him into searching, and he NEVER
    returns to idle after that.
  - He roams ONLY the outdoor surface domain (passages + folds), never indoors,
    never a safe room.
  - He becomes a concrete body only while he shares the player's scene, placed
    AWAY from the player (never on top).
  - Seeing the player (line of sight, unhidden, in range) = HUNTING + fast
    visibility climb; reaching the player ends the run.
  - Breaking his sight (cover) drops hunting back to searching -- the relief
    that always works, even at full evidence.
  - He follows the player through his own ground (a passage/fold) but a door
    is the player-only escape.

Run from repo root:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python tests/king_roam.py
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
from systems.config import (KING_ROAM_SCENES, KING_ROAM_START, KING_GATE_EVIDENCE,
                            KING_CATCH_DIST, SAFE_SCENES, KING_FREE_SCENES,
                            CULT_REGULARS, PORTAL_CHARGE_TIME, PORTAL_PIN_VIS,
                            PORTAL_CROSS_DIST)


def _boot(scene="graveyard"):
    g = Game()
    g.save.new()
    g._start_play()
    g.load_scene_now(scene, "default")
    return g


def _arm(g, n=KING_GATE_EVIDENCE):
    """Log n canonical-shaped evidence dicts so the gate reads as crossed."""
    g.save.set_arg("evidence", [{"name": f"e{i}", "weight": 0.1}
                                for i in range(n)])


def _open_spot(g, near, dx):
    """A walkable point dx px right of `near`, falling back along a few offsets
    so the test isn't wedged against a wall."""
    for off in (dx, -dx, dx // 2, -dx // 2, dx * 2):
        x, y = near[0] + off, near[1]
        if not g.scene.is_solid_at(x, y):
            return x, y
    return near


def test_idle_until_gate():
    g = _boot()
    g.visibility = 1.0
    g._tick_king_roam(0.05)
    assert not g._roam_king["armed"], "below 3 evidence he stays idle, not armed"
    assert g._roam_king["state"] == "idle", "state is idle before the gate"
    assert g._king is None, "no body walks before the gate"
    print("  OK  idle below the 3-evidence gate (no King walks)")


def test_arms_at_gate():
    g = _boot()
    _arm(g)
    g._tick_king_roam(0.05)
    rk = g._roam_king
    assert rk["armed"], "3 evidence must arm him"
    assert rk["state"] == "searching", "arming drops him into searching"
    assert rk["scene"] == KING_ROAM_START, "he peels off the road (arrival_road)"
    print("  OK  3 evidence arms him into searching, off the road")


def test_arm_grace_holds_the_breath():
    # The play-notes ramp: crossing the gate arms him, but the world HOLDS ITS
    # BREATH for KING_ARM_GRACE first -- he does not materialise or hunt, the
    # window to reach the lodge before the hunt begins.
    g = _boot(KING_ROAM_START)                 # player in his arm scene
    _arm(g)
    g._tick_king_roam(0.05)                     # arm frame
    assert g._roam_king["armed"], "the gate arms him"
    assert g._roam_king["arm_grace"] > 0, "arming opens the grace window"
    assert g._king is None, "he does not materialise during the grace"
    g._roam_king["arm_grace"] = 0.0            # burn past the grace
    g._tick_king_roam(0.05)
    assert g._king is not None, "past the grace he materialises in your scene"
    print("  OK  the arm-grace holds the hunt, then releases it")


def test_never_returns_to_idle():
    g = _boot()
    _arm(g)
    g._tick_king_roam(0.05)              # arm
    # Force him into another scene and run a long dry search.
    g._roam_king["scene"] = "country_lane"
    for _ in range(4000):               # ~200s of ticks at dt 0.05
        g._tick_king_roam(0.05)
    assert g._roam_king["armed"], "he stays armed forever"
    assert g._roam_king["state"] != "idle", "once armed he never goes idle again"
    print("  OK  once armed he never returns to idle (cools to check-nearby)")


def test_leaving_his_scene_drops_the_hunt():
    # Hunting, then the player leaves the King's scene (he can't see you from a
    # room away): his abstract state must fall back to searching, not stay stuck
    # hunting forever.
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)               # materialise as a concrete hunter
    # Player escapes to a DIFFERENT surface scene the King isn't in.
    other = next(t for t in KING_ROAM_SCENES if t != g._roam_king["scene"])
    g.load_scene_now(other, "default")
    g._tick_king_roam(0.05)               # now abstract (not co-located)
    assert g._roam_king["state"] == "searching", \
        "leaving his scene must drop hunting to searching (no stuck hunt)"
    print("  OK  leaving his scene drops the hunt to searching")


def test_roam_domain_excludes_indoors_and_safe():
    g = _boot()
    graph = g._king_roam_graph()
    for k in graph:
        assert k in KING_ROAM_SCENES, f"{k} is outside the roam domain"
        assert k not in SAFE_SCENES, f"{k} is a safe room -- he must not roam it"
    # Every adjacency target is also in-domain (no door leaks into the graph).
    for k, nbrs in graph.items():
        for nb in nbrs:
            assert nb in KING_ROAM_SCENES, f"{k}->{nb} leaks outside the domain"
    print("  OK  the roam graph is surface-only (no indoors / safe rooms)")


def test_materializes_away_from_player():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="searching", scene=g.scene.key)
    g._tick_king_roam(0.05)
    assert g._king is not None, "sharing your scene materialises the body"
    assert g._king.sprite_kind == "yellow_king", "the body is the King sprite"
    assert getattr(g._king, "_phase", False), "the roaming King phases walls"
    import math
    d = math.hypot(g._king.x - g.player.x, g._king.y - g.player.y)
    assert d > KING_CATCH_DIST, "he never materialises on top of the player"
    print("  OK  he materialises in your scene, away from you, phasing")


def test_hunts_on_sight():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="searching", scene=g.scene.key)
    g._tick_king_roam(0.05)             # materialise
    king = g._king
    king.x, king.y = _open_spot(g, (g.player.x, g.player.y), 120)
    king._birth = 1.0
    g.player.hidden = None
    g.visibility = 0.2
    g._tick_king_roam(0.05)
    assert g._roam_king["state"] == "hunting", "line of sight = hunting"
    assert g.visibility > 0.2, "seeing you climbs visibility fast"
    print("  OK  he hunts on sight and visibility climbs fast")


def test_hiding_drops_hunt():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)
    king = g._king
    king.x, king.y = _open_spot(g, (g.player.x, g.player.y), 120)
    king._birth = 1.0
    g.player.hidden = "corn"            # break his sight
    g._tick_king_roam(0.05)
    assert g._roam_king["state"] == "searching", "breaking sight drops the hunt"
    print("  OK  hiding (breaking sight) drops hunting back to searching")


def test_catch_ends_the_run():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)
    king = g._king
    king.x, king.y = g.player.x + 12, g.player.y   # inside the catch radius
    king._birth = 1.0
    g.player.hidden = None
    g.player.invuln = 0
    g._tick_king_roam(0.05)
    assert g._death_kind == "king", "contact while hunting ends the run (king)"
    print("  OK  reaching the player ends the run (the King catch)")


def test_birth_grace_no_catch():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)
    king = g._king
    king.x, king.y = g.player.x + 12, g.player.y
    king._birth = 0.3                   # still erupting -- the grace window
    g.player.hidden = None
    g._tick_king_roam(0.05)
    assert g._death_kind is None, "mid-eruption he can't catch (the grace)"
    print("  OK  he can't catch mid-eruption (the birth grace holds)")


def test_safe_room_never_hosts():
    safe = next(iter(SAFE_SCENES))
    g = _boot(safe)
    _arm(g)
    # Even if his record somehow points at the safe room, no body forms.
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)
    assert g._king is None, "a safe room never hosts the King, ever"
    print("  OK  a safe room never hosts the King")


def test_follow_through_passage_not_door():
    g = _boot()
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)             # a concrete King in the room
    assert g._king is not None
    # A passage/fold (a surface target in the domain): he follows.
    passage = next(t for t in KING_ROAM_SCENES if t != g.scene.key)
    g._note_king_follow((passage, "default"))
    assert g._roam_king["scene"] == passage, "he follows through a passage/fold"
    # A door (a target outside the domain -- an interior): he stays put.
    g._roam_king["scene"] = g.scene.key
    door_target = next(iter(SAFE_SCENES))      # an interior, never in the domain
    g._note_king_follow((door_target, "default"))
    assert g._roam_king["scene"] == g.scene.key, "a door loses him (player escape)"
    print("  OK  he follows through passages/folds but a door loses him")


def _arm_elsewhere(g):
    """Armed, with the King in a DIFFERENT surface scene than the player -- the
    precondition for a portal to be able to tear in."""
    _arm(g)
    g._tick_king_roam(0.05)               # arm
    other = next(t for t in KING_ROAM_SCENES if t != g.scene.key)
    # arm_grace=0.0: past the "world holds its breath" window, the hunt is on
    # (the play-notes ramp holds him for KING_ARM_GRACE right after arming).
    g._roam_king.update(armed=True, state="searching", scene=other,
                        arm_grace=0.0)
    g._king = None


def test_portal_charges_and_tears():
    g = _boot()
    _arm_elsewhere(g)
    g.visibility = 1.0
    steps = int(PORTAL_CHARGE_TIME / 0.1) + 3
    for _ in range(steps):
        g.visibility = 1.0                # held pinned
        g._tick_king_roam(0.1)
    assert g._portal is not None, "pinned 100% for the window tears a portal"
    assert g._portal["x"] is not None, "the rift has a world position"
    print("  OK  pinned 100% for the window tears a portal")


def test_portal_cancels_on_vis_drop():
    g = _boot()
    _arm_elsewhere(g)
    g.visibility = 1.0
    g._tick_king_roam(0.1)
    g._tick_king_roam(0.1)
    assert g._portal_charge_t > 0, "charge builds while pinned"
    g.visibility = 0.5                    # break 100%
    g._tick_king_roam(0.1)
    assert g._portal_charge_t == 0.0, "dropping below 100% collapses the charge"
    assert g._portal is None, "no rift forms once the charge is broken"
    print("  OK  breaking 100% collapses the forming rift (the cancel window)")


def test_portal_brings_him_through():
    g = _boot()
    _arm_elsewhere(g)
    g.visibility = 1.0
    for _ in range(int(PORTAL_CHARGE_TIME / 0.1) + 3):
        g.visibility = 1.0
        g._tick_king_roam(0.1)
    assert g._roam_king["scene"] == g.scene.key, "he folds INTO your room"
    assert g._roam_king["state"] == "hunting", "he comes through hunting"
    # The rift's far side is the room he LEFT (your escape).
    assert g._portal["target"] != g.scene.key, "the rift leads to the room he left"
    print("  OK  he folds through to your room; the rift leads to where he was")


def test_portal_never_tears_in_safe_room():
    safe = next(iter(SAFE_SCENES))
    g = _boot(safe)
    _arm(g)
    g._tick_king_roam(0.05)
    other = next(t for t in KING_ROAM_SCENES if t != safe)
    g._roam_king.update(armed=True, state="searching", scene=other)
    g.visibility = 1.0
    for _ in range(int(PORTAL_CHARGE_TIME / 0.1) + 5):
        g.visibility = 1.0
        g._tick_king_roam(0.1)
    assert g._portal is None, "a safe room never lets a rift tear in"
    print("  OK  a portal never tears into a safe room")


def test_portal_tears_underground():
    # The descent rework: the Works/Depths are NOT
    # KING_FREE -- pinning 100% underground still tears his rift in.
    from systems.config import UNDERGROUND_SCENES, KING_FREE_SCENES
    g = _boot("well_bottom")
    _arm_elsewhere(g)
    g.load_scene_now("well_bottom")
    assert g.scene.key in UNDERGROUND_SCENES
    assert g.scene.key not in KING_FREE_SCENES
    steps = int(PORTAL_CHARGE_TIME / 0.1) + 3
    for _ in range(steps):
        g.visibility = 1.0                # held pinned
        g._tick_king_roam(0.1)
    assert g._portal is not None, "a portal must tear into the underground"
    print("  OK  pinned 100% underground still tears his portal in")


def test_no_pathing_underground():
    # His AI never PATHS underground: the roam domain holds no
    # underground room, and the grove's descent fold (target
    # well_bottom) releases him rather than carrying him down.
    from systems.config import UNDERGROUND_SCENES
    assert not (KING_ROAM_SCENES & UNDERGROUND_SCENES), \
        "the roam domain must hold no underground scene"
    g = _boot("effigy_grove")
    _arm(g)
    g._roam_king.update(armed=True, state="hunting", scene=g.scene.key)
    g._tick_king_roam(0.05)               # concrete in the grove
    g._note_king_follow(("well_bottom", "from_grove"))
    assert g._roam_king["scene"] == "effigy_grove", \
        "the descent fold must release him (he never follows below)"
    print("  OK  the descent fold releases him; the roam domain stays surface")


def test_portal_cross_jukes_and_clears():
    g = _boot()
    _arm_elsewhere(g)
    g.visibility = 1.0
    for _ in range(int(PORTAL_CHARGE_TIME / 0.1) + 3):
        g.visibility = 1.0
        g._tick_king_roam(0.1)
    assert g._portal is not None
    target = g._portal["target"]
    king_side = g._roam_king["scene"]
    # Step into the rift.
    g.player.x, g.player.y = g._portal["x"], g._portal["y"]
    g.player.hidden = None
    g._tick_king_roam(0.05)
    assert g._portal is None, "the rift shuts the instant you cross"
    assert g.scene.key == target, "crossing jukes you to the room he left"
    assert g._roam_king["scene"] == king_side, "he is stranded on the far side"
    assert g._roam_king["scene"] != g.scene.key, "one-way: he can't follow you through"
    print("  OK  stepping through jukes you across and strands him (one-way)")


if __name__ == "__main__":
    test_idle_until_gate()
    test_arms_at_gate()
    test_arm_grace_holds_the_breath()
    test_never_returns_to_idle()
    test_leaving_his_scene_drops_the_hunt()
    test_roam_domain_excludes_indoors_and_safe()
    test_materializes_away_from_player()
    test_hunts_on_sight()
    test_hiding_drops_hunt()
    test_catch_ends_the_run()
    test_birth_grace_no_catch()
    test_safe_room_never_hosts()
    test_follow_through_passage_not_door()
    test_portal_charges_and_tears()
    test_portal_cancels_on_vis_drop()
    test_portal_brings_him_through()
    test_portal_never_tears_in_safe_room()
    test_portal_tears_underground()
    test_no_pathing_underground()
    test_portal_cross_jukes_and_clears()
    print("All roaming-King guards held.")
