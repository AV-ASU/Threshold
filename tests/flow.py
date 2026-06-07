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
    wx, wy = g.scene._well_pos              # the well moved in the brimley merge
    g.player.x, g.player.y = wx, wy
    g.scene.on_interact_fn(g)
    check(g.save.flag("well_rope_tied"), "well: rope ties on first descent")
    check(not g.player.inventory.has("rope"), "well: rope consumed into the rig")

    # --- 1b. The Ledger fires from the Lodge FRONT DESK, not the cellar ---
    # CANON (NARRATIVE §4, §5): one register, on the front desk; you sign on
    # arrival and the evidence lands when you RE-READ it. The old cellar copy
    # behind a loose panel is cut.
    gl = new_game()
    gl.load_scene_now("house")
    ready(gl)
    gl.player.x, gl.player.y = gl.scene._frontdesk_pos
    gl.scene.on_interact_fn(gl)                      # first press: sign
    check(gl.save.flag("register_signed"),
          "ledger: first press signs the front-desk register")
    check(not has_evidence(gl, "the_ledger"),
          "ledger: signing alone does not log the evidence")
    ready(gl)
    gl.scene.on_interact_fn(gl)                      # re-read: the evidence
    check(has_evidence(gl, "the_ledger"),
          "ledger: re-reading the front-desk register fires the_ledger")
    # The cellar no longer carries the Ledger.
    gcellar = new_game()
    gcellar.load_scene_now("basement")
    ready(gcellar)
    check(not hasattr(gcellar.scene, "_wall_panel_pos"),
          "ledger: the cellar copy is cut (no loose wall panel)")
    import inspect as _insp_l
    from scenes import house as _house_mod
    check("the_ledger" not in _insp_l.getsource(_house_mod.basement_interact),
          "ledger: basement_interact no longer logs the_ledger")
    from scenes.dialogue import clerk_dialogue as _clerk_src_fn
    check("cellar" not in _insp_l.getsource(_clerk_src_fn).lower(),
          "ledger: Sable no longer points at a cellar register")

    # --- 2. The Calling (Scriptorium) -- first cult-testimony fragment ---
    _ev_before = len(g.save.arg("evidence", []))
    fire(g, "works_scriptorium", "_desk_pos")
    check(g.player.inventory.has("cult_calling"),
          "scriptorium: grants The Calling (cult testimony, not a keystone)")
    check(any(isinstance(e, dict) and e.get("name") == "cult_calling"
              for e in g.save.arg("notes", [])),
          "scriptorium: logs the PI's reaction to NOTES")
    check(len(g.save.arg("evidence", [])) == _ev_before,
          "scriptorium: the testimony is lore, never inflates evidence")

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

    # --- 4. The Deep Stair fork (the keystone: the Pallid Mask alone) ---
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
          "deep stair: the keystone opens the descent")
    check(g.save.flag("well_rope_broken"),
          "deep stair: committing snaps the rope (point of no return)")
    # CANON (NARRATIVE §6/§7 rework): the stair opens WITHOUT consuming the
    # keystone (the Mask) -- you carry it down to spend at the Threshold door.
    check(g.player.inventory.has("sigil_rubbing"),
          "deep stair: the keystone is NOT consumed (carried down, not spent)")

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

    # --- 7. The Threshold seal -> the SEAL ending (consumes the keystone) ---
    # The keystone (the Mask) carried down from the Deep Stair is spent HERE,
    # at the door (§7 rework, Mask-only). g still holds it (stair did not spend).
    g.load_scene_now("threshold")
    ready(g)
    sc = g.scene
    check(g.player.inventory.has("sigil_rubbing"),
          "threshold: the keystone (Mask) arrives in hand (carried from the stair)")
    g.player.x, g.player.y = sc._lintel_pos
    sc.on_update_fn(g, sc, 0.1)               # walking THROUGH the frame seals it
    check(g._ending_active == "seal_threshold",
          "threshold: walking through the frame fires the SEAL ending")
    check(not g.player.inventory.has("sigil_rubbing"),
          "threshold: the seal CONSUMES the keystone (Mask) at the door")
    seal_text = " ".join(line for line, _ in
                         g._ENDING_SCRIPTS["seal_threshold"])
    check("Nothing leaves Brimley again" in seal_text
          and "Not the hunger" in seal_text and "Not you" in seal_text,
          "threshold: SEAL ending is authored (canonical close present)")
    # The door seals ONLY to the keystone: empty-handed, it does not fire.
    gnokey = new_game()
    gnokey.load_scene_now("threshold")
    ready(gnokey)
    gnokey.player.x, gnokey.player.y = gnokey.scene._lintel_pos
    gnokey.scene.on_update_fn(gnokey, gnokey.scene, 0.1)
    check(gnokey._ending_active is None,
          "threshold: without the keystone the door does not seal (no free seal)")

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

    # --- 8b. The cult-testimony triptych: pure lore, never evidence ---
    from systems.items import ITEM_DEFS as _IDEFS
    gt2 = new_game()
    _e2 = evidence_count(gt2)
    fire(gt2, "the_sump", "_note_pos")
    check(gt2.player.inventory.has("cult_bargain"),
          "sump: grants The Bargain (optional testimony fragment)")
    check(any(isinstance(e, dict) and e.get("name") == "cult_bargain"
              for e in gt2.save.arg("notes", [])),
          "sump: The Bargain logs the PI reaction to NOTES")
    check(evidence_count(gt2) == _e2,
          "sump: The Bargain never inflates evidence (lore, not a beat)")
    gt3 = new_game()
    _e3 = evidence_count(gt3)
    fire(gt3, "the_ossuary", "_dig_note_pos")
    check(gt3.player.inventory.has("cult_digging"),
          "ossuary: grants The Digging (optional testimony fragment)")
    check(any(isinstance(e, dict) and e.get("name") == "cult_digging"
              for e in gt3.save.arg("notes", [])),
          "ossuary: The Digging logs the PI reaction to NOTES")
    check(evidence_count(gt3) == _e3,
          "ossuary: The Digging never inflates evidence")
    # CANON (§1b discipline): the dimensional truth is NEVER stated in the
    # testimony the player reads.
    _triptych = ("cult_calling", "cult_bargain", "cult_digging")
    _blob = " ".join(_IDEFS[k]["desc"].lower() for k in _triptych)
    check("dimension" not in _blob,
          "testimony: never says 'dimension' (folk horror, not sci-fi)")
    check("playscript" not in _IDEFS,
          "items: the old single playscript keystone is retired")

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
    kid = next((nn for nn in gk.scene.npcs
                if nn.name == "the Tisdale boy"), None)   # renamed in the merge
    check(kid is not None, "kid: the Kid is present in his house")
    if kid:
        _kid_lines = []
        gk.dialog.show = (lambda real: (lambda p, **k: (
            _kid_lines.extend(p if isinstance(p, list) else [p]),
            real(p, **k))[1]))(gk.dialog.show)
        kid.dialogue_fn(gk, kid)
        check(gk.save.flag("kid_witnessed")
              and not gk.player.inventory.has("polaroid"),
              "kid: the witness beat fires and grants no inventory item")
        # CANON (NARRATIVE §2): the witness is the clue to DESCEND THE WELL --
        # Mara AND the others went down it in the procession. The account must
        # point down the well, not into the corn (the old wrong reading).
        _kid_text = " ".join(_kid_lines).lower()
        check("well" in _kid_text and "down" in _kid_text,
              "kid: the witness points down the well (the clue to descend)")
        check("corn" not in _kid_text,
              "kid: the witness no longer sends you into the corn")

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

    # --- 13b. The SPREAD car lives on the ARRIVAL ROAD west of the lodge ---
    # The dead car (and the escape) moved off brimley onto the looping arrival
    # road; the yard's west exit routes through it, and the road wraps (the
    # fold made the drive-in an endless loop you can turn off of any time).
    from scenes import load_scene as _ld13
    _yard = _ld13("our_house_area")
    check(_yard.exits.get("a", (None,))[0] == "arrival_road",
          "geo: the lodge yard's west exit lands on the arrival road")
    _road = _ld13("arrival_road")
    check(_road.exits.get("a", (None,))[0] == "country_lane"
          and _road.exits.get("e", (None,))[0] == "our_house_area",
          "geo: the arrival road's dirt path links country_lane (W) and yard (E)")
    check(hasattr(_road, "_treadmill") and not _road.wrap_y
          and hasattr(_road, "_car_pos"),
          "geo: the arrival road loops a small NORTH band (_treadmill, not full "
          "wrap_y) and holds the dead car")
    check(_road.h >= 30,
          "geo: the road is taller than a screen so the loop's repeat stays "
          "off-frame (you don't see two cars at once)")
    check("_car_pos" not in inspect.getsource(_ml.build_brimley),
          "geo: the car is gone from brimley (consolidated at the lodge)")
    gr = new_game()
    gr.load_scene_now("arrival_road")
    ready(gr)
    gr.player.x, gr.player.y = gr.scene._car_pos
    gr.player.inventory.add("sigil_rubbing", 1)
    gr.scene.on_interact_fn(gr)
    check(gr._ending_active == "escape_alone",
          "geo: SPREAD fires at the car on the arrival road (with the Sign)")

    # --- 13c. The woodshed is consolidated into the lodge yard ------------
    # It used to sit across town in brimley; now it is a key-gated door in
    # the Arcadia yard (west of the lodge) and exits back to the yard. The
    # brimley shed door is gone.
    _yard2 = _ld13("our_house_area")
    _shed = _ld13("woodshed")
    check(hasattr(_yard2, "_shed_door_pos"),
          "geo: the lodge yard has the woodshed door (west of the lodge)")
    check(_shed.exits.get("h", (None,))[0] == "our_house_area",
          "geo: the woodshed exits back into the lodge yard")
    check("_shed_door_pos" not in inspect.getsource(_ml.build_brimley),
          "geo: brimley no longer hosts the woodshed door (consolidated)")
    gw = new_game()
    gw.load_scene_now("our_house_area")
    ready(gw)
    gw.player.x, gw.player.y = gw.scene._shed_door_pos
    gw.scene.on_interact_fn(gw)                       # locked, no key
    check(gw.scene.key == "our_house_area",
          "geo: the shed door is locked without the cellar key")
    gw.player.inventory.add("woodshed_key", 1)
    gw.scene.on_interact_fn(gw)                       # key in hand -> enters
    check(getattr(gw, "transition_target", (None,))[0] == "woodshed",
          "geo: the cellar key opens the yard shed -> woodshed interior")

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
    dream_note = next((e for e in notes if isinstance(e, dict)
                       and e.get("name") == "the_dream"), None)
    check(dream_note is not None,
          "heknows: the dream logs a case-notebook NOTE")
    # CANON (NARRATIVE 1b / spectrum note): the PI dreamed of the door
    # exactly ONCE, a year ago -- it never took and never came again. The
    # note must read as that single, half-dismissed memory, NOT a recurring
    # dream. Guard against the recurrence regression.
    dream_text = " ".join(dream_note["lines"]).lower() if dream_note else ""
    check("year" in dream_text,
          "heknows: the dream note places it a year ago (single, not recurring)")
    check(not any(w in dream_text for w in
                  ("again the", "same dream", "every night", "each night",
                   "fourth night", "fifth", "the dreams", "keeps coming")),
          "heknows: the dream note does NOT imply a recurring dream")
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

    # --- 15. The gun: the false-power threshold (NARRATIVE §3) ---
    # "It exists to fail; lethal only on the victims." Lock the four canon
    # facts: below 3 evidence a clean round KILLS a cultist; at 3+ it only
    # STAGGERS; the King (and the Watchers) are unshootable; and a clean
    # round ALWAYS kills a local -- the gate only ever protected the cult.
    from entities.enemy import (Projectile, _is_cultist, _is_shootable,
                                _BULLET_PHANTOM)
    from systems.game import KING_GATE_EVIDENCE

    class _Tgt:
        """Minimal stand-in carrying just what _strike touches."""
        def __init__(self, **kw):
            self.alive = True; self.flash = 0.0; self._stun_t = 0.0
            self.hp = 100; self._has_been_spotted = True
            self.__dict__.update(kw)
        def take_damage(self, d):
            self.hp -= d
            if self.hp <= 0:
                self.alive = False

    # Below 3 evidence (stun_only False): a clean round drops a cultist.
    cult = _Tgt(kind="cultist")
    pk = Projectile(0, 0, 1, 0, dmg=100); pk.stun_only = False
    pk._strike(cult)
    check(not cult.alive and cult._stun_t == 0,
          "gun: below 3 evidence, a clean round KILLS a cultist")

    # At 3+ evidence (stun_only True): the same round only staggers a cultist.
    cult2 = _Tgt(kind="cultist")
    ps = Projectile(0, 0, 1, 0, dmg=100); ps.stun_only = True; ps.stun_dur = 1.4
    ps._strike(cult2)
    check(cult2.alive and cult2._stun_t > 0,
          "gun: at 3+ evidence, the round only STAGGERS a cultist")

    # A local is never a cult target, so the stagger gate can't shield it:
    # a clean round ALWAYS kills a local, even with stun_only set (3+ ev).
    local = _Tgt(kind="local", sprite_kind="townsfolk")
    check(not _is_cultist(local), "gun: a living local is not a cult target")
    pl = Projectile(0, 0, 1, 0, dmg=100); pl.stun_only = True
    pl._strike(local)
    check(not local.alive,
          "gun: a clean round ALWAYS kills a local (even past the 3-gate)")

    # The King and the Watchers are bullet-phantom -- you can't fire down a
    # direction you can't point at (§1b). The round passes straight through.
    check("yellow_king" in _BULLET_PHANTOM and "watcher" in _BULLET_PHANTOM,
          "gun: the King and the Watchers are bullet-phantom (unshootable)")
    check(not _is_shootable(_Tgt(sprite_kind="yellow_king")),
          "gun: a round passes straight through the King")

    # The fire path itself: the round is friendly, NOT cult-only (so it can
    # reach a local), and its stun_only flag tracks the evidence gate live.
    gg = new_game()
    gg.load_scene_now("brimley")
    ready(gg)
    gg.player.inventory.add("pistol", 1)
    gg.player.inventory.add("pistol_ammo", 9)
    gg._gun_cd = 0.0
    gg.player_fire_gun()
    shot = gg.scene.projectiles[-1]
    check(shot.friendly and not shot.cult_only,
          "gun: the player's round is friendly and NOT cult-only (reaches locals)")
    check(shot.stun_only is False,
          "gun: with no evidence, the round is lethal (stun_only False)")
    for i in range(KING_GATE_EVIDENCE):
        gg.save.arg("evidence", []).append({"name": f"_gun_gate_{i}"})
    gg._gun_cd = 0.0
    gg.player_fire_gun()
    shot2 = gg.scene.projectiles[-1]
    check(shot2.stun_only is True,
          "gun: at 3+ evidence, the fire path arms stun_only (cult goes unkillable)")

    # --- 16. The lure, seeded across the notebook (NARRATIVE §1/§1b) ---
    # The PI starts a run with the case already in his notebook -- a NOTE,
    # never a clue, so it can't arm the King-gate. The case IS the bait, but
    # that truth must arrive only as sensation: the note reads as a grudging
    # summary, and the hook is the one line he can't account for.
    gc = new_game()
    notes_c = gc.save.arg("notes", [])
    case = next((e for e in notes_c if isinstance(e, dict)
                 and e.get("name") == "the_case"), None)
    check(case is not None, "lure: a new run seeds the_case note in the notebook")
    case_text = " ".join(case["lines"]).lower() if case else ""
    check("mara" in case_text and "brimley" in case_text,
          "lure: the case note carries the canon hook (Mara / Brimley)")
    # The hook lands as sensation -- a numb man who can't say why he took it --
    # and NEVER as exposition. Guard the discipline (§1b: never explain).
    check(not any(w in case_text for w in
                  ("lure", "bait", "trap", "hook", "dimension", "the king",
                   "reeled", "marked")),
          "lure: the case note never NAMES the lure (truth as sensation only)")
    check(gc._evidence_count() == 0,
          "lure: the case note is a NOTE, not evidence (never arms the King-gate)")
    gc._log_case_entry()                      # idempotent: no duplicate
    check(sum(1 for e in gc.save.arg("notes", [])
              if isinstance(e, dict) and e.get("name") == "the_case") == 1,
          "lure: re-logging the case does not duplicate the note")

    # --- 16b. The PI's interior voice -- from DIVERSE examined things ------
    # The voice fires on what the PI EXAMINES (chalk doors, the dig's lives,
    # the Mask), NOT on bare room entry. Chalk doors are ONE recurring motif,
    # not the only source. NOTES, never evidence. §1b: never explains the door.
    gv = new_game()
    def _vnotes(g):
        return [e["name"] for e in g.save.arg("notes", []) if isinstance(e, dict)]
    ev_before = gv._evidence_count()
    # (a) Examining a chalk door fires the scene's voice beat (surface->deep).
    for key, note in (("barn", "chalk_surface"),
                      ("well_passage", "chalk_works"),
                      ("depths_antechamber", "chalk_deep")):
        gv.dialog.active = False
        gv.load_scene_now(key, "default")
        doors = getattr(gv.scene, "_chalk_doors", None)
        check(bool(doors), f"voice: {key} has chalk doors registered")
        if doors:
            gv.player.x, gv.player.y = doors[0]
            handled = gv._try_chalk_interact()
            check(handled and note in _vnotes(gv),
                  f"voice: examining the chalk door in {key} files '{note}'")
    # (b) A DIFFERENT thing -- the Sorting Hall's catalogued lives -- fires its
    # own beat. The voice is not all chalk doors.
    gv.dialog.active = False
    gv.load_scene_now("works_sorting", "default")
    gv.player.x, gv.player.y = gv.scene._table_pos
    gv.scene.on_interact_fn(gv)
    check("descent_dig" in _vnotes(gv),
          "voice: examining the dig's catalogued lives fires its own beat (a different trigger)")
    # (c) The notes never arm the King-gate.
    check(gv._evidence_count() == ev_before,
          "voice: the interior-voice notes never inflate the evidence/King-gate")
    # (d) Re-examining a chalk door does not duplicate its beat.
    gv.dialog.active = False
    gv.load_scene_now("well_passage", "default")
    gv.player.x, gv.player.y = gv.scene._chalk_doors[1]   # a second door
    gv._try_chalk_interact()
    check(sum(1 for n in _vnotes(gv) if n == "chalk_works") <= 1,
          "voice: re-examining chalk doors does not duplicate the beat")
    # (e) Chalk doors come in FLOOR and WALL variants.
    from scenes import load_scene as _ldcd
    _kinds = set()
    for k in ("barn", "well_passage", "depths_antechamber"):
        for d in _ldcd(k).decorations:
            if d.kind in ("chalk_door", "chalk_door_wall"):
                _kinds.add(d.kind)
    check("chalk_door" in _kinds and "chalk_door_wall" in _kinds,
          "voice: chalk doors are drawn on the FLOOR and on WALLS")
    # Content: the Mask beat baits leaving; nothing ever says 'dimension'.
    from systems.game import Game as _G
    _mask = " ".join(_G._DESCENT_VOICE["descent_mask"]["beat"]
                     + _G._DESCENT_VOICE["descent_mask"]["note"]).lower()
    check(any(w in _mask for w in ("the way out", "let you out", "lets go",
                                   "could just go", "in the car")),
          "voice: the Mask beat baits the player toward leaving (SPREAD off-ramp)")
    _allvoice = " ".join(
        " ".join(s["beat"] + s["note"]) for s in _G._DESCENT_VOICE.values()).lower()
    check("dimension" not in _allvoice,
          "voice: the interior voice never says 'dimension' (truth as sensation)")
    # The King's influence (the want-to-leave) must read as the PI's OWN
    # judgment -- he must NEVER notice his thoughts/wants changing, or the
    # horror collapses. Guard the leave/mask/deep beats against self-aware-of-
    # the-shift phrasing.
    _pull = " ".join(
        " ".join(_G._DESCENT_VOICE[k]["beat"] + _G._DESCENT_VOICE[k]["note"])
        for k in ("descent_leave", "descent_mask", "chalk_deep")).lower()
    check(not any(p in _pull for p in (
        "an hour ago", "when did", "started thinking", "didn't want that",
        "i don't trust a want", "a want i can't", "turn around")),
        "voice: the leave-urge never reads as the PI noticing his mind change")
    # The Playscript (the cult's notes) SEEDS the want-to-leave -- a NOTE, not
    # evidence (and it must not arm the King-gate).
    gp2 = new_game()
    gp2.load_scene_now("works_scriptorium", "default")
    ready(gp2)
    ev_pre = gp2._evidence_count()
    gp2.player.x, gp2.player.y = gp2.scene._desk_pos
    gp2.scene.on_interact_fn(gp2)
    guard = 0
    while gp2.dialog.active and guard < 40:
        gp2.dialog.advance(); guard += 1
    _pn = [e["name"] for e in gp2.save.arg("notes", []) if isinstance(e, dict)]
    check("descent_leave" in _pn,
          "voice: taking the Playscript seeds the want-to-leave (descent_leave)")
    check(gp2._evidence_count() == ev_pre,
          "voice: the leave-seed is a NOTE, not evidence (never arms the King-gate)")
    # The Ledger -- first evidence -- carries the PI's voice (the checkout-date
    # confusion), not a dry description.
    gl2 = new_game()
    gl2.load_scene_now("house", "from_bedroom")
    ready(gl2)
    gl2.player.x, gl2.player.y = gl2.scene._frontdesk_pos
    gl2.scene.on_interact_fn(gl2)         # sign
    ready(gl2)
    gl2.scene.on_interact_fn(gl2)         # re-read -> evidence
    _lt = " ".join(l for e in gl2.save.arg("evidence", [])
                   if e.get("name") == "the_ledger" for l in e["lines"]).lower()
    check("months" in _lt and "keep it in mind" in _lt,
          "voice: the Ledger carries the PI's voice (the checkout-date confusion)")

    # Chalk-door swarm fills the Scriptorium (obsessive, none overlapping).
    _scr = _ldcd("works_scriptorium")
    _cd = [d for d in _scr.decorations
           if d.kind in ("chalk_door", "chalk_door_wall")]
    check(len(_cd) >= 6,
          "chalk: the Scriptorium is swarmed with chalk doors (the compulsion)")

    # --- 16c. The fold-talk note: a local describing the fold (looping roads)
    # files the PI's note ONCE (the first speaker), names them, stays a NOTE.
    gf2 = new_game()
    gf2.load_scene_now("brimley", "default")
    ready(gf2)
    _royce = next((n for n in gf2.scene.npcs if n.name == "Royce"), None)
    _garrick = next((n for n in gf2.scene.npcs if n.name == "Garrick"), None)
    check(_royce is not None and _garrick is not None,
          "fold: the fold-mentioning locals are present")
    _evp = gf2._evidence_count()
    if _royce:
        _royce.dialogue_fn(gf2, _royce)
        g_ = 0
        while gf2.dialog.active and g_ < 30:
            gf2.dialog.advance(); g_ += 1
    _ft = next((e for e in gf2.save.arg("notes", [])
                if isinstance(e, dict) and e.get("name") == "the_fold_told"), None)
    check(_ft is not None and "Royce" in " ".join(_ft["lines"]),
          "fold: a local describing the fold files the note, naming who told you")
    check(gf2._evidence_count() == _evp,
          "fold: the fold note is a NOTE, not evidence (never arms the King-gate)")
    if _garrick:
        ready(gf2)
        _garrick.dialogue_fn(gf2, _garrick)
    check(sum(1 for e in gf2.save.arg("notes", [])
              if isinstance(e, dict) and e.get("name") == "the_fold_told") == 1,
          "fold: only the FIRST fold mention files the note (not every speaker)")

    # --- 16d. STYLE RULE: no em-dashes in ANY player-facing writing (keep it
    # human). Tokenize every source file and flag every non-docstring STRING
    # literal that contains '--'. Docstrings + comments are exempt (not game
    # writing). Locks the whole game's prose, not just this work.
    import tokenize as _tok
    import glob as _glob
    import os as _os
    _dash_hits = []
    for _fn in sorted(_glob.glob(_os.path.join(ROOT, "scenes", "*.py"))
                      + _glob.glob(_os.path.join(ROOT, "systems", "*.py"))
                      + _glob.glob(_os.path.join(ROOT, "ui", "*.py"))
                      + _glob.glob(_os.path.join(ROOT, "entities", "*.py"))):
        with open(_fn, "rb") as _fh:
            _tks = list(_tok.tokenize(_fh.readline))
        _sig = [t for t in _tks
                if t.type not in (_tok.NL, _tok.COMMENT, _tok.ENCODING)]
        _doc = set()
        for _i, _t in enumerate(_sig):
            if _t.type == _tok.STRING:
                _prev = _sig[_i - 1].type if _i > 0 else _tok.NEWLINE
                _nxt = _sig[_i + 1].type if _i + 1 < len(_sig) else _tok.NEWLINE
                if (_prev in (_tok.NEWLINE, _tok.INDENT, _tok.DEDENT)
                        and _nxt == _tok.NEWLINE):
                    _doc.add((_t.start, _t.string))
        for _t in _tks:
            if (_t.type == _tok.STRING and "--" in _t.string
                    and (_t.start, _t.string) not in _doc):
                _dash_hits.append(f"{_os.path.basename(_fn)}:{_t.start[0]}")
    check(not _dash_hits,
          "style: no em-dashes in any player-facing string (keep it human)"
          + (f" (found {_dash_hits[:8]})" if _dash_hits else ""))

    # --- 17. The principal locals are named (NARRATIVE §2/§8) ---
    # A small town knows its people by name. Each principal surfaces a
    # proper-name speaker label, not a role-tag. (The Clerk, Mr. Sable, is
    # the most-attuned LOCAL, NARRATIVE §2 -- not a newcomer; he introduces
    # himself first thing all the same.)
    from scenes.dialogue import (sheriff_dialogue, preacher_dialogue,
                                 hettie_dialogue, clerk_dialogue)

    def first_speaker(dialogue_fn):
        g = new_game()
        cap = []
        g.dialog.show = (lambda real: (lambda p, **k: (
            cap.append(k.get("speaker", "")), real(p, **k))[1]))(g.dialog.show)
        dialogue_fn(g, type("N", (), {"name": "x", "x": 0, "y": 0})())
        return cap[0] if cap else None

    roster = [("Sheriff Vane", sheriff_dialogue), ("Rev. Crane", preacher_dialogue),
              ("Hettie", hettie_dialogue), ("Mr. Sable", clerk_dialogue)]
    for expected, fn in roster:
        check(first_speaker(fn) == expected,
              f"naming: a principal local speaks as '{expected}' (not a role-tag)")

    # --- 17b. Sable is the most-attuned LOCAL (NARRATIVE §2) -------------
    # His menace is compulsion, not conspiracy. Lock the framing: the
    # characterization must not tag him a newcomer/recruiter or have him
    # scheme, and it must name him a local.
    import inspect as _insp_s
    _sable_src = _insp_s.getsource(clerk_dialogue).lower()
    check("local" in _sable_src,
          "sable: characterized as a local (most-attuned), not a newcomer")
    check(not any(w in _sable_src for w in
                  ("newcomer", "recruiter", "recruit")),
          "sable: never tagged newcomer/recruiter (compulsion, not conspiracy)")

    # --- 18. effigy_grove is a maker-less tableau (§1b/§8) ---------------
    # Individual cursing is redundant -- the closing rite claimed the town at
    # once -- so the grove is left as the work without the worker, with no
    # NPC tending it, like its siblings husk_grove / scarecrow_ring.
    from scenes import load_scene as _load2
    grove = _load2("effigy_grove")
    check(len(grove.npcs) == 0,
          "effigy_grove is a maker-less tableau (no NPC, like its siblings)")

    # --- 19. Eat-cult + time-loop fiction stays scrubbed (NARRATIVE §1b/§8) -
    # Canon: a CLAIMING cult that renders no bodies (no cannibalism, no
    # tallow), and a SPATIAL fold -- stasis, nowhere to go -- never a TEMPORAL
    # loop. Those phrasings were scrubbed; lock them out of the scene source so
    # the fiction can't quietly regress.
    import os
    _scene_dir = os.path.join(os.path.dirname(__file__), "..", "scenes")
    _forbidden = [
        "tasting it", "tallow", "the rendering at", "feed what waits",
        "grain threaded through", "fold back on themselves",
        "comes home for dinner",
    ]
    _hits = []
    for fn in sorted(os.listdir(_scene_dir)):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(_scene_dir, fn), encoding="utf-8") as fh:
            low = fh.read().lower()
        for phrase in _forbidden:
            if phrase in low:
                _hits.append(f"{fn}:{phrase!r}")
    check(not _hits,
          "scrub: no eat-cult/time-loop fiction in scene source"
          + (f" (found {_hits})" if _hits else ""))

    # --- 20. Cultists use dynamic AI, not preset coordinates (NARRATIVE §8) -
    # Pure-roam SCOUT + cover-aware pursuit. Guard the two canon facts: no
    # roaming cultist carries a baked patrol route, and the nav routes a
    # pursuer AROUND a blocked line instead of straight through it.
    from constants import TILE as _TILE
    from scenes import load_scene as _ld, SCENE_BUILDERS as _SB
    no_wp = routed = False
    for _key in _SB:
        try:
            _sc = _ld(_key)
        except Exception:
            continue
        for _e in _sc.enemies:
            if getattr(_e, "kind", None) == "cultist":
                check(not getattr(_e, "waypoints", None),
                      f"ai: cultist in {_key} has no preset waypoint route")
                no_wp = True
        # Probe one blocked-line pair and confirm nav bends around it.
        if not routed:
            _wt = [(tx, ty) for ty in range(_sc.h) for tx in range(_sc.w)
                   if not _sc._nav_solid_at(tx * _TILE + 16, ty * _TILE + 16)]
            for _i in range(0, len(_wt), 7):
                for _j in range(len(_wt) - 1, 0, -11):
                    if _i >= _j:
                        continue
                    (ax, ay), (bx, by) = _wt[_i], _wt[_j]
                    x0, y0 = ax * _TILE + 16, ay * _TILE + 16
                    x1, y1 = bx * _TILE + 16, by * _TILE + 16
                    if (not _sc.nav_clear_line(x0, y0, x1, y1)
                            and _sc.nav_path(x0, y0, x1, y1)):
                        check(_sc.nav_toward(x0, y0, x1, y1) != (x1, y1),
                              "ai: nav routes a pursuer around blocking cover")
                        routed = True
                        break
                if routed:
                    break
    check(no_wp, "ai: cultist spawns were exercised by the waypoint guard")
    check(routed, "ai: a blocked-line route was found to exercise the nav guard")

    # --- 21. A chase carries through PORTALS and folds (NARRATIVE §8) -------
    # The only thing that shakes a hot pursuer is a SAFE room. Guard both: a
    # plain portal (non-fold) exit to a non-safe scene stashes the pursuer; a
    # SAFE destination clears it (the refuge is never breached).
    from systems.game import (CULTIST_SCENES as _CS, UNDERGROUND_SCENES as _UG,
                              SAFE_SCENES as _SAFE)
    gp = new_game()
    gp.load_scene_now(next(iter(_CS)))
    _ch = gp._spawn_cultist("cult_regular", "cultist",
                            at=(gp.player.x + 30, gp.player.y))
    check(_ch is not None, "portal: a surface chaser could be planted")
    if _ch is not None:
        _ch.x, _ch.y = gp.player.x + 30, gp.player.y
        _ch._cult_state = "chase"
        gp._note_fold_pursuit((next(iter(_UG)), "default"))   # plain portal
        check(gp._fold_pursuer is not None,
              "portal: an active chase carries through a portal exit")
        _ch._cult_state = "chase"
        gp._note_fold_pursuit((next(iter(_SAFE)), "default"))
        check(gp._fold_pursuer is None,
              "portal: a SAFE room shakes the chase (refuge never breached)")
        # Mara's cell is a deliberate refuge: it hosts no cultists, so a chase
        # fled into it does NOT carry (no spawn-then-sweep). Locked by choice.
        _ch._cult_state = "chase"
        gp._note_fold_pursuit(("maras_room", "default"))
        check(gp._fold_pursuer is None,
              "portal: maras_room is a refuge -- the chase does not follow in")
    # The dead-end branch rooms must be registered underground, or a pursuer
    # fled into them spawns as a surface NPC that _tick_cultists sweeps (the
    # chase silently evaporates). They also need the dark/flashlight gate.
    from systems.game import DARK_SCENES as _DK
    for _br in ("the_sump", "the_cells", "the_ossuary"):
        check(_br in _UG, f"portal: branch room {_br} is registered underground")
        check(_br in _DK, f"dark: branch room {_br} gets the underground gloom")

    # --- 22. Ashfall scales with the infestation, never on the Threshold ----
    # (NARRATIVE §4b) The pale-yellow ash is the vessel's pressure made
    # visible: zero at stage 0, light->steady as evidence climbs, thicker
    # underground (nearer the source), clean in safe rooms until stage 3, and
    # NEVER on the Threshold (the still eye of it, §1b).
    def _ash(scene, ev):
        ga = new_game()
        ga.save.set_arg("evidence", [f"ev{i}" for i in range(ev)])
        ga.load_scene_now(scene)
        return ga._ashfall_target()

    check(_ash("brimley", 0) == 0,
          "ashfall: stage 0 air is clean (no evidence, no ash)")
    check(_ash("brimley", 1) > 0 and _ash("brimley", 3) > _ash("brimley", 1),
          "ashfall: density climbs with the evidence stage")
    check(_ash("works_scriptorium", 3) > _ash("brimley", 3),
          "ashfall: thicker underground (nearer the source)")
    check(_ash("threshold", 3) == 0,
          "ashfall: never on the Threshold (the still eye of it)")
    _safe = next(iter(_SAFE))
    check(_ash(_safe, 2) == 0 and _ash(_safe, 3) > 0,
          "ashfall: safe rooms stay clean until stage 3 claims them too")

    print()
    if FAILS:
        print(f"{len(FAILS)} flow failure(s).")
        sys.exit(1)
    print("All flow checks passed -- the critical path is completable.")


if __name__ == "__main__":
    main()
