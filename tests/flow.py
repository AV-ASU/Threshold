"""End-to-end flow harness for THRESHOLD's critical path.

Where smoke.py only *builds* scenes, this drives a full run headlessly and
asserts the spine is COMPLETABLE with no crash or soft-lock:

  rope down the well -> take the Playscript -> take the Pallid Mask ->
  fork at the Deep Stair (Mask + Play) -> cross the Depths -> the hive
  (speak to Mara) -> seal the Threshold (the SEAL ending).

Plus the SPREAD ending (drive out with the Mask) and the 3-evidence King
gate. Interactions are driven by positioning the player on each
interactable and calling the scene's on_interact_fn (or an NPC's
dialogue_fn) directly, so no pathfinding/input simulation is needed.

Run from the repo root:  python tests/flow.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
pygame.init()
pygame.display.set_mode((960, 540))

from constants import TILE
from systems.game import Game

FAILS = []


def check(cond, msg):
    ok = bool(cond)
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


def new_game():
    g = Game()
    g.save.new()
    g._start_play()
    return g


def ready(g):
    """Reset to a clean interactable state between scripted steps:
    clear any transition lock and dismiss an open dialog so the next
    interact/transition fires."""
    g.state = "playing"
    if getattr(g, "dialog", None) is not None:
        g.dialog.active = False


def fire(g, key, pos_attr):
    """Load `key`, stand the player on the interactable named by the
    scene attribute `pos_attr`, and run the scene interact once."""
    g.load_scene_now(key)
    ready(g)
    g.player.x, g.player.y = getattr(g.scene, pos_attr)
    if g.scene.on_interact_fn:
        g.scene.on_interact_fn(g)
    return g.scene


def evidence_count(g):
    return len(g.save.arg("evidence", []))


def has_evidence(g, name):
    return any(isinstance(e, dict) and e.get("name") == name
               for e in g.save.arg("evidence", []))


def main():
    print("THRESHOLD flow harness\n")

    # --- 0. Boot ---
    g = new_game()
    check(g.state == "playing" and g.player is not None,
          "new game boots into a playable state")

    # --- 1. Descend the well (needs the rope) ---
    g.load_scene_now("brimley")
    ready(g)
    g.player.inventory.add("rope", 1)
    g.player.x, g.player.y = 16 * TILE + 16, 11 * TILE + 16   # the well tile
    g.scene.on_interact_fn(g)
    check(g.save.flag("well_rope_tied"), "well: rope ties on first descent")
    check(not g.player.inventory.has("rope"), "well: rope consumed into the rig")

    # --- 2. The Playscript (Scriptorium) ---
    fire(g, "works_scriptorium", "_desk_pos")
    check(g.player.inventory.has("playscript"),
          "scriptorium: grants the Playscript")

    # --- 3. The Pallid Mask (Sign Chamber, evidence #5) -- LIFT the mask ---
    fire(g, "works_sign", "_sign_pos")
    g.dialog.choice_idx = 0
    g.dialog.advance()                          # "Lift the mask."
    check(g.player.inventory.has("sigil_rubbing"),
          "sign chamber: lifting the mask grants it (the ONLY source)")
    check(has_evidence(g, "the_sign"),
          "sign chamber: logs the_sign evidence (canonical beat)")
    # THE TRAP (NARRATIVE §6): tearing the rite down here -- before sealing
    # the source -- is a game over, not a victory.
    gt = new_game()
    fire(gt, "works_sign", "_sign_pos")
    gt.dialog.choice_idx = 1
    gt.dialog.advance()                         # "Tear it down -- end this."
    check(gt._ending_active == "rite_broken",
          "sign chamber: tearing the rite down fires the rite_broken game over")
    check("rite_broken" in g._ENDING_SCRIPTS,
          "ending: rite_broken script is authored")

    # --- 4. The Deep Stair fork (Mask + Play together) ---
    g.load_scene_now("works_deepstair")
    ready(g)
    sc = g.scene
    g.player.x, g.player.y = sc._gate_pos
    sc.on_interact_fn(g)                      # first press: lay out the fork
    check(g.save.flag("deepstair_fork_seen"),
          "deep stair: first press shows the fork")
    ready(g)                                  # dismiss the fork dialog
    sc.on_interact_fn(g)                      # second press: commit (Seal road)
    check(g.save.flag("deepstair_open"),
          "deep stair: Mask + Play opens the descent")
    check(g.save.flag("well_rope_broken"),
          "deep stair: committing snaps the rope (point of no return)")
    check(not g.player.inventory.has("playscript")
          and not g.player.inventory.has("sigil_rubbing"),
          "deep stair: both Mask and Play are spent")

    # --- 5. The Depths chain loads + steps with no crash ---
    for k in ("depths_antechamber", "depths_procession", "depths_hall",
              "depths_threshing", "depths_stair", "dark", "threshold"):
        g.load_scene_now(k)
        g.step(1 / 60.0)
        check(g.scene.key == k, f"depths: {k} loads and ticks")
    # The descent rooms each fire a one-shot first-visit narration beat.
    for flag in ("first_antechamber", "first_procession", "first_hall",
                 "first_depthstair"):
        check(g.save.flag(flag), f"depths: {flag} narration fired on entry")
    # The journal flashback is now a WORDLESS visual dream (the burning
    # doorway + the accelerating mask swarm), not text stills: a single
    # None-line phase held for FLASHBACK_DUR. Assert the visual mechanics
    # exist rather than authored prose.
    check(g._flashback_stills == [(None, __import__("systems.game",
          fromlist=["FLASHBACK_DUR"]).FLASHBACK_DUR)],
          "flashback: the dream is a single wordless visual phase")
    check(hasattr(g, "_spawn_flashback_masks")
          and hasattr(g, "_build_flashback_pool"),
          "flashback: the mask-swarm system is wired")

    # --- 6. The hive: speaking to Mara is the #6 payoff ---
    g.load_scene_now("dark")
    ready(g)
    mara = next((n for n in g.scene.npcs if n.name == "Mara"), None)
    check(mara is not None, "hive: Mara is among the congregation")
    if mara:
        mara.dialogue_fn(g, mara)
        check(g.save.flag("hive_seen"),
              "hive: speaking to Mara fires the recognition")

    # --- 7. The Threshold seal -> the SEAL ending ---
    g.load_scene_now("threshold")
    ready(g)
    sc = g.scene
    g.player.x, g.player.y = sc._lintel_pos
    sc.on_interact_fn(g)
    check(g._ending_active == "seal_threshold",
          "threshold: sealing fires the SEAL ending")
    seal_text = " ".join(line for line, _ in
                         g._ENDING_SCRIPTS["seal_threshold"])
    check("Nothing leaves Brimley again" in seal_text
          and "Not the hunger" in seal_text and "Not you" in seal_text,
          "threshold: SEAL ending is authored (canonical close present)")

    # --- 8. The SPREAD ending: drive out with the Mask ---
    gs = new_game()
    ready(gs)
    gs.player.inventory.add("sigil_rubbing", 1)
    gs._begin_car_escape()
    check(gs._ending_active == "escape_alone",
          "spread: holding the Mask fires the escape ending")
    gb = new_game()
    ready(gb)
    gb._begin_car_escape()                    # no Mask in hand
    check(gb._ending_active is None,
          "spread: blocked without the Mask (no free escape)")

    # --- 9. The 3-evidence King gate is reachable ---
    ge = new_game()
    fire(ge, "works_sign", "_sign_pos")               # the_sign (#5)
    ge.dialog.choice_idx = 0
    ge.dialog.advance()                               # "Lift the mask."
    fire(ge, "barn", "_journal_pos")                  # maras_journal (#2)
    jlines = next((e["lines"] for e in ge.save.arg("evidence", [])
                   if e.get("name") == "maras_journal"), [])
    jtext = " ".join(jlines).lower()
    check("you go down" in jtext or "below the town" in jtext,
          "barn: Mara's journal motivates the descent (points down/below)")
    ge.load_scene_now("dark")                          # the_congregation (#6)
    ready(ge)
    mara_e = next((n for n in ge.scene.npcs if n.name == "Mara"), None)
    if mara_e:
        mara_e.dialogue_fn(ge, mara_e)
    n = evidence_count(ge)
    check(n >= 3, f"evidence: the 3-gate is reachable (gathered {n} canonical beats)")

    # --- 10. The Kid is the witness (NARRATIVE §2): tells, grants no item ---
    gk = new_game()
    gk.load_scene_now("kid_house")
    ready(gk)
    kid = next((nn for nn in gk.scene.npcs if nn.name == "Village Kid"), None)
    check(kid is not None, "kid: the Kid is present in his house")
    if kid:
        kid.dialogue_fn(gk, kid)
        check(gk.save.flag("kid_witnessed")
              and not gk.player.inventory.has("polaroid"),
              "kid: the witness beat fires and grants no inventory item")

    # --- 11. The flashlight: found, toggles, double-edged in the dark ---
    gf = new_game()
    fire(gf, "woodshed", "_flash_pos")
    check(gf.player.inventory.has("flashlight"),
          "flashlight: picked up in the woodshed")
    # In a dark, non-safe scene the beam lights and burns the meter.
    gf.load_scene_now("well_passage")
    ready(gf)
    gf.flashlight_on = True
    check(gf._flashlight_lit(),
          "flashlight: lit once switched on in a dark scene")
    gf.visibility, gf._gaze_count, gf._watchers = 0.30, 0, []
    before = gf.visibility
    for _ in range(10):
        gf._tick_visibility(0.1)                  # ~1s of held light
    check(gf.visibility > before,
          "flashlight: holding the beam raises visibility (double-edged)")
    # Switching off stops the burn -- the meter idles back down.
    gf.flashlight_on = False
    check(not gf._flashlight_lit(), "flashlight: off means no beam")
    off0 = gf.visibility
    for _ in range(10):
        gf._tick_visibility(0.1)
    check(gf.visibility < off0,
          "flashlight: beam off, the meter bleeds back down")
    # Cult-dark swallows the beam regardless of the switch.
    gf.load_scene_now("dark")
    ready(gf)
    gf.flashlight_on = True
    check(not gf._flashlight_lit(),
          "flashlight: cult-dark scenes force the beam off")

    # --- 12. Purged items stay purged (no defs, no icons) ---
    from systems.items import ITEM_DEFS
    from ui.item_icons import _DISPATCH
    for dead in ("charcoal", "paper", "car_keys", "cellar_bottle",
                 "liquor_crate", "cellar_key", "polaroid"):
        check(dead not in ITEM_DEFS and dead not in _DISPATCH,
              f"cleanup: '{dead}' has no item def or icon")
    # --- 13. The Brimley escape gates on the Sign alone (no car keys) ---
    import inspect
    from scenes import brimley as _ml
    src = inspect.getsource(_ml.build_brimley)
    check("car_keys" not in src,
          "escape: the car no longer checks for car_keys")

    # --- 14. "He knows you": the dream note + Threshold recognition ---
    # Living the journal door-dream writes a personal NOTE (not a clue), and
    # arriving at the real Threshold having dreamed it lands a recognition
    # line before the doorframe beat.
    gd = new_game()
    gd.load_scene_now("bedroom", "default")
    gd.state = "playing"
    ev_pre = gd._evidence_count()
    gd.save.set_flag("flashback_pending", True)
    gd._tick_flashback(1 / 60.0)
    guard = 0
    while gd._flashback_phase is not None and guard < 2000:
        gd.screen.fill((0, 0, 0))
        gd._draw_flashback()
        gd._tick_flashback(1 / 60.0)
        guard += 1
    notes = gd.save.arg("notes", [])
    check(any(isinstance(e, dict) and e.get("name") == "the_dream"
              for e in notes),
          "heknows: the dream logs a case-notebook NOTE")
    check(gd._evidence_count() == ev_pre,
          "heknows: the dream note never inflates the evidence/King gate")
    gd._log_dream_entry()                     # idempotent: no duplicate
    check(sum(1 for e in gd.save.arg("notes", [])
              if isinstance(e, dict) and e.get("name") == "the_dream") == 1,
          "heknows: re-logging the dream does not duplicate the note")
    # Recognition line at the real Threshold (only when dreamed).
    from scenes import load_scene as _load
    seen = []
    gd2 = new_game(); gd2.save.set_flag("flashback_seen", True)
    gd2.dialog.show = (lambda real: (lambda p, **k: (
        seen.append((p if isinstance(p, list) else [p])[0]), real(p, **k))[1]
    ))(gd2.dialog.show)
    sct = _load("threshold")
    sct.on_enter_fn(gd2, sct)
    guard = 0
    while gd2.dialog.active and guard < 50:
        gd2.dialog.advance(); guard += 1
    check(seen and "in sleep" in seen[0].lower(),
          "heknows: dreamed -> recognition line lands at the Threshold")
    check(any("doorframe" in s.lower() for s in seen),
          "heknows: the doorframe beat still follows the recognition")
    seen2 = []
    gd3 = new_game()                          # never dreamed
    gd3.dialog.show = (lambda real: (lambda p, **k: (
        seen2.append((p if isinstance(p, list) else [p])[0]), real(p, **k))[1]
    ))(gd3.dialog.show)
    sct3 = _load("threshold")
    sct3.on_enter_fn(gd3, sct3)
    check(seen2 and "in sleep" not in seen2[0].lower(),
          "heknows: never dreamed -> no recognition line (doorframe only)")

    print()
    if FAILS:
        print(f"{len(FAILS)} flow failure(s).")
        sys.exit(1)
    print("All flow checks passed -- the critical path is completable.")


if __name__ == "__main__":
    main()
