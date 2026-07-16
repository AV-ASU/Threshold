"""End-to-end flow harness for THRESHOLD's critical path.

Where smoke.py only *builds* scenes, this drives a full run headlessly and
asserts the spine is COMPLETABLE with no crash or soft-lock:

  3 evidence -> Sable hands over the Invitation -> the school rite
  (incense + the chalk door) -> the grove's descent fold -> take the
  Calling testimony -> the Sign Chamber (Mara rises; take the Pallid Mask) ->
  the blast at the Deepest Face (the one-way fall) -> cross the Depths ->
  seal the Threshold (the SEAL ending).

Plus the SPREAD ending (drive out with the Mask) and the 3-evidence King
gate. Interactions are driven by positioning the player on each
interactable and calling the scene's on_interact_fn (or an NPC's
dialogue_fn) directly, so no pathfinding/input simulation is needed.

Run from the repo root:  python tests/flow.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
# SDL converts SIGTERM into a quit event instead of dying, so `timeout`
# and CI cancellation cannot stop a harness (it runs to completion while
# the wrapper reports 124). Keep the default kill behavior in tests.
os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")
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

    # --- 1. THE ACT BREAK: evidence + rite + the grove fold -------------
    # The rope is CUT. The way down is the rite: at 3 evidence Sable hands
    # over the Invitation, the school rite (incense, then the chalk door)
    # opens the school<->grove fold, and the grove's descent fold (which
    # clarifies with the evidence count) drops you at the shaft floor.
    from scenes.dialogue import clerk_dialogue
    from systems.items import ITEM_DEFS as _IDEFS1
    check("rope" not in _IDEFS1, "act break: the rope item is cut")
    for key in ("rite_envelope", "chalk", "incense"):
        check(key in _IDEFS1, f"act break: the {key} item exists")
    check(not any(d in _IDEFS1["rite_envelope"]["desc"]
                  for d in ("—", "–", "--")),
          "act break: the Invitation text carries no dashes (HARD RULE)")

    def _take_fold(gg, ch):
        """Stand on fold tile `ch` facing its direction and fire the
        game's gated exit path (find_exit_at + exit_gate_fn + cross_fold),
        mirroring the step() block."""
        from rendering.folds import _DIRV
        pos = gg.scene.find_marker(ch)
        assert pos is not None, f"no {ch!r} tile in {gg.scene.key}"
        gg.player.x = pos[0] * 32 + 16
        gg.player.y = pos[1] * 32 + 16
        gg.player.facing = _DIRV[gg.scene.exit_directions[ch]]
        data = gg.scene.find_exit_at(gg.player.x, gg.player.y,
                                     facing=gg.player.facing)
        if data is None:
            return False
        gate = getattr(gg.scene, "exit_gate_fn", None)
        if gate is not None and not gate(gg, ch):
            return False
        gg.cross_fold(*data)
        return True

    # (a) Below 3 evidence: Sable holds the envelope; the grove fold is a
    # dim thread that will not cross; the well is dread set-dressing.
    g.load_scene_now("brimley")
    ready(g)
    wx, wy = g.scene._well_pos
    g.player.x, g.player.y = wx, wy
    g.scene.on_interact_fn(g)
    check(g.save.flag("well_examined") and g.scene.key == "brimley",
          "well: demoted to dread set-dressing (no descent)")
    ready(g)
    clerk_dialogue(g, None)
    check(not g.player.inventory.has("rite_envelope"),
          "sable: below 3 evidence the Invitation stays under the register")
    g.load_scene_now("effigy_grove")
    ready(g)
    check(0.0 < g.scene.fold_charge_fn(g, "O") < 0.2,
          "grove: at 0 evidence the descent fold is a faint thread")
    # The gate and charge key on the EVIDENCE COUNT (the five canonical
    # beats), never on visibility or its floor -- Watchers raise the
    # visibility floor and must never open the way down.
    import inspect as _insp_g
    from scenes import hidden_folds as _hf_mod
    _gsrc = _insp_g.getsource(_hf_mod.build_effigy_grove)
    check("_evidence_count" in _gsrc and "visibility" not in _gsrc,
          "grove: the descent keys on evidence, never the visibility floor")
    _vis_before = g.visibility
    g.visibility = 1.0                      # even pinned at the cap...
    check(g.scene.fold_charge_fn(g, "O") < 0.2 and not _take_fold(g, "O"),
          "grove: max visibility alone never charges or opens the fold")
    g.visibility = _vis_before
    check(not _take_fold(g, "O"),
          "grove: at 0 evidence the descent fold will not cross")
    check(g.scene.key == "effigy_grove", "grove: still in the grove")

    # (b) At 3 evidence the "way down" question OPENS; asking it hands over
    # the Invitation once, with the PI's note. The silent auto-handoff is
    # gone -- getting the rite is now an explicit, gated ask.
    from scenes.dialogue import (SABLE_CONVO as _SCV,
                                 _sable_give_invitation as _give)
    _wd = next(ex for ex in _SCV["exchanges"] if ex["key"] == "the_way_down")
    check(not _wd["avail"](g),
          "sable: below 3 evidence the 'way down' question is not offered")
    for i in range(3):
        g.save.arg("evidence", []).append(
            {"name": f"_act1_{i}", "lines": ["x"]})
    check(_wd["avail"](g),
          "sable: at 3 evidence the 'way down' question opens")
    _give(g)                       # the player asks; he hands it over
    check(g.player.inventory.has("rite_envelope"),
          "sable: asking for the way hands over the Invitation")
    check(any(isinstance(e, dict) and e.get("name") == "the_invitation"
              for e in g.save.arg("notes", [])),
          "sable: the handoff logs the PI's NOTE (never evidence)")
    check(len(g.save.arg("evidence", [])) == 3,
          "sable: the handoff does not inflate the evidence count")
    check(not _wd["avail"](g),
          "sable: the 'way down' question closes once he has given it")
    _give(g)                       # asking again does nothing
    check(g.player.inventory.count("rite_envelope") == 1
          and sum(1 for e in g.save.arg("notes", [])
                  if isinstance(e, dict)
                  and e.get("name") == "the_invitation") == 1,
          "sable: the handoff fires exactly once (no duplicate)")

    # (b2) Knowledge continuity: the early (ungated) 'car' exchange must not
    # put town-wide car/fold knowledge in the PI's mouth. He speaks only from
    # his OWN experience (his car died the night he drove in); that no engine
    # in Brimley catches is the fold, and he learns it from Vane/Royce, never
    # asserts it to Sable first. Guards the "cars not working with Sable" leak.
    _car = next(ex for ex in _SCV["exchanges"] if ex["key"] == "car")
    check("avail" not in _car,
          "sable: the car question is an early, ungated exchange")
    _pi_car = (_car["q"] + " " + " ".join(
        t for (who, t) in _car["beats"] if who == "pi")).lower()
    for _leak in ("no car in this town", "every car in this town", "i'm told"):
        check(_leak not in _pi_car,
              f"sable: the PI never leaks town-wide car knowledge ({_leak!r})")

    # (c) The school rite: incense first, then the chalk door; the fold
    # stays open from then on.
    g.load_scene_now("schoolhouse")
    ready(g)
    g.player.x, g.player.y = g.scene._board_pos
    g.scene.on_interact_fn(g)
    check(not g.save.flag("school_door_open"),
          "school: the board alone does not open the door (air first)")
    ready(g)
    g.player.x, g.player.y = g.scene._chalk_pos
    g.scene.on_interact_fn(g)
    check(g.player.inventory.has("chalk"), "school: chalk off the desk")
    ready(g)
    g.player.x, g.player.y = g.scene._incense_pos
    g.scene.on_interact_fn(g)
    check(g.player.inventory.has("incense"),
          "school: incense among the cot relics")
    ready(g)
    g.player.x, g.player.y = g.scene._fire_pos
    g.scene.on_interact_fn(g)
    check(g.save.flag("school_incense_lit"),
          "school: the incense burns at the indoor fire")
    check(not g.player.inventory.has("incense"),
          "school: the rite consumes the incense")
    ready(g)
    g.player.x, g.player.y = g.scene._board_pos
    g.scene.on_interact_fn(g)
    check(g.save.flag("school_door_open"),
          "school: smoke + chalk draw the final door")
    g._school_door_t0 = None              # skip the formation ramp
    ready(g)
    check(_take_fold(g, "O") and g.scene.key == "effigy_grove",
          "school: the drawn door crosses to the grove")

    # (d) THE RITE: at 3 evidence + the Invitation, E at the dead fire is
    # a TWO-PRESS commit (never a lone-press point of no return); the
    # second press plays the FULL door-dream (a pure cutscene, no input),
    # and completion tears the pane open and seals the circle.
    check(g.scene.fold_charge_fn(g, "O") >= 0.999,
          "grove: at 3 evidence the frame is fully formed (the meter)")
    ready(g)
    check(not _take_fold(g, "O") and g.scene.key == "effigy_grove",
          "grove: even at 3 evidence the fold will not cross before the rite")
    g.player.x, g.player.y = g.scene._rite_pos
    g.scene.on_interact_fn(g)                  # first press: the stakes
    check(g.save.flag("rite_laid") and not g.save.flag("rite_performed"),
          "rite: first press lays the stakes (two-press commit)")
    ready(g)
    g.scene.on_interact_fn(g)                  # second press: the dream
    check(g._flashback_phase is not None
          and g._flashback_mode == "rite",
          "rite: second press starts the FULL door-dream (cutscene only)")
    while g._flashback_phase is not None:
        g._tick_flashback(0.5)
    check(g.save.flag("rite_performed") and g.save.flag("flashback_seen"),
          "rite: the dream completes the rite (and seeds the Threshold beat)")
    check(any(isinstance(e, dict) and e.get("name") == "the_rite"
              for e in g.save.arg("notes", [])),
          "rite: acceptance lands as an oblique NOTE, never a banner")
    check(len(g.save.arg("evidence", [])) == 3,
          "rite: the rite never inflates evidence")
    g._rite_fold_t0 = None                        # skip the opening ramp
    check(not g.scene.exit_gate_fn(g, "M"),
          "rite: the circle seals the surface exit behind you")
    ready(g)
    check(_take_fold(g, "O") and g.scene.key == "well_bottom",
          "rite: the opened pane lands at the shaft floor")
    # (e) The way home is KEYED to His face, never one-way (the King keeps
    # his signature).
    ready(g)
    check(not _take_fold(g, "O") and g.scene.key == "well_bottom",
          "pane: without the Mask the way home refuses (keyed, not one-way)")
    # (f) Egress with the Mask seals the descent (the SPREAD lock) --
    # proven on a separate game so the main run stays underground.
    g2 = new_game()
    for i in range(3):
        g2.save.arg("evidence", []).append({"name": f"_e{i}", "lines": ["x"]})
    g2.save.set_flag("rite_performed", True)
    g2._rite_fold_t0 = None
    g2.player.inventory.add("pallid_mask", 1)
    g2.load_scene_now("well_bottom", "from_grove")
    ready(g2)
    check(_take_fold(g2, "O") and g2.scene.key == "effigy_grove",
          "egress: His face opens the way home")
    check(g2.save.flag("descent_sealed"),
          "egress: crossing up with the Mask seals the descent (SPREAD lock)")
    check(g2.scene.fold_charge_fn(g2, "O") == 0.0
          and not _take_fold(g2, "O"),
          "egress: the descent fold is dead behind you")
    g2.save.set_flag("school_door_open", True)
    g2._school_door_t0 = None
    check(g2.scene.exit_gate_fn(g2, "M"),
          "egress: the circle releases you once the way down is dead")

    # --- 1b. The Ledger: the locked cellar + the key behind the house ---
    # CANON (2026-07 rework): you SIGN the desk register on arrival; the
    # desk re-read is only a LEAD (a clean, new book). The Ledger itself
    # is the boxed old registers in the cellar, behind the padlocked
    # kitchen hatch; the cellar key hangs on a nail behind the house.
    gl = new_game()
    gl.load_scene_now("lodge")
    ready(gl)
    gl.player.x, gl.player.y = gl.scene._frontdesk_pos
    gl.scene.on_interact_fn(gl)                      # first press: sign
    check(gl.save.flag("register_signed"),
          "ledger: first press signs the front-desk register")
    ready(gl)
    gl.scene.on_interact_fn(gl)                      # re-read: only a lead
    check(not has_evidence(gl, "the_ledger"),
          "ledger: the desk register is a LEAD now, never the evidence")
    check(not gl.scene.exit_gate_fn(gl, "L"),
          "ledger: the cellar hatch is locked without the key")
    gl.load_scene_now("lodge_yard")
    check(any(it["key"] == "cellar_key" for it in gl.scene.items),
          "ledger: the cellar key hangs behind the house")
    gl.player.inventory.add("cellar_key", 1)   # (walk-over pickup in play)
    gl.save.set_flag("cellar_key_taken", True)
    gl.load_scene_now("lodge")
    check(gl.scene.exit_gate_fn(gl, "L")
          and gl.save.flag("cellar_unlocked"),
          "ledger: the carried key turns the padlock (one-time unlock)")
    gl.load_scene_now("lodge_cellar")
    ready(gl)
    gl.player.x, gl.player.y = gl.scene._ledger_pos
    gl.scene.on_interact_fn(gl)
    check(not has_evidence(gl, "the_ledger")
          and any(isinstance(e, dict) and e.get("name") == "the_ledger"
                  for e in gl.save.arg("notes", [])),
          "ledger: the old registers file a town NOTE, never case-evidence")
    # A fresh save's cellar is key-gated and panel-free.
    gcellar = new_game()
    gcellar.load_scene_now("lodge_cellar")
    ready(gcellar)
    check(not hasattr(gcellar.scene, "_wall_panel_pos"),
          "ledger: no loose wall panel (the old cache stays cut)")
    import inspect as _insp_l
    from scenes.dialogue import clerk_dialogue as _clerk_src_fn
    check("cellar" not in _insp_l.getsource(_clerk_src_fn).lower(),
          "ledger: Sable never points at the cellar himself")

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

    # --- 3. The Pallid Mask (Sign Chamber, the keystone item) -- LIFT the mask ---
    fire(g, "works_sign", "_sign_pos")
    g.dialog.choice_idx = 0
    g.dialog.advance()                          # "Lift the mask."
    check(g.player.inventory.has("pallid_mask"),
          "sign chamber: lifting the mask grants it (the ONLY source)")
    check(not has_evidence(g, "the_sign"),
          "sign chamber: the Mask is the keystone ITEM, never case-evidence")
    # THE TRAP (NARRATIVE §8): tearing the rite down here -- before sealing
    # the source -- is a game over, not a victory.
    gt = new_game()
    fire(gt, "works_sign", "_sign_pos")
    gt.dialog.choice_idx = 1
    gt.dialog.advance()                         # "Tear it down -- end this."
    check(gt._ending_active == "rite_broken",
          "sign chamber: tearing the rite down fires the rite_broken game over")
    check("rite_broken" in g._ENDING_SCRIPTS,
          "ending: rite_broken script is authored")

    # --- 4. The Deepest Face: powder + the blast (the dig never finished;
    # the cult's testimony left a few feet of earth; the stair is CUT) ---
    fire(g, "the_sump", "_powder_pos")
    check(g.player.inventory.has("powder"),
          "sump: the diggers' powder store arms the blast")
    # The investigator's discipline: no Mask, no fuse (sweep first).
    gb = new_game()
    gb.player.inventory.add("powder", 1)
    gb.load_scene_now("works_deepface")
    ready(gb)
    gb.player.x, gb.player.y = gb.scene._gate_pos
    gb.scene.on_interact_fn(gb)
    check(not gb.save.flag("blast_laid"),
          "face: without the Mask the charge stays unlit (sweep first)")
    # The real run: Mask + powder, two-press, light it.
    g.load_scene_now("works_deepface")
    ready(g)
    sc = g.scene
    g.player.x, g.player.y = sc._gate_pos
    sc.on_interact_fn(g)                      # first press: lay the fuse
    check(g.save.flag("blast_laid"),
          "face: first press lays the charge (two-press commit)")
    ready(g)
    sc.on_interact_fn(g)                      # second press: light it
    check(g.save.flag("depths_breached"),
          "face: the blast breaks the dig into the old workings")
    check(not g.player.inventory.has("powder"),
          "face: the charge is spent")
    # CANON (DESIGN.md §3): the Mask is NOT consumed at the face -- you
    # carry it down to spend at the Threshold door (or out, for SPREAD).
    check(g.player.inventory.has("pallid_mask"),
          "face: the keystone is NOT consumed (carried down, not spent)")

    # --- 5. The Depths chain loads + steps with no crash ---
    for k in ("depths_antechamber", "depths_procession", "depths_hall",
              "depths_threshing", "depths_stair", "dark", "threshold"):
        g.load_scene_now(k)
        g.step(1 / 60.0)
        check(g.scene.key == k, f"depths: {k} loads and ticks")
    # The door-dream is TWO-STAGE now: the journal fires a brief memory
    # FLASH (a longer dwelling look on PICKUP now, ~2s, no swarm -- the
    # half-dismissed memory surfacing); the FULL wordless dream (door +
    # accelerating mask swarm) plays at the GROVE RITE. Same dream, two weights.
    from ui.cutscenes import (FLASHBACK_DUR as _FBD,
                              FLASHBACK_FLASH_DUR as _FBF)
    check(0.0 < _FBF <= 3.0 < _FBD,
          "flashback: the journal flash is short; the rite dream is long")
    check(hasattr(g, "_spawn_flashback_masks")
          and hasattr(g, "_build_flashback_pool")
          and hasattr(g, "begin_rite_dream"),
          "flashback: the mask-swarm + rite-dream systems are wired")

    # --- 6. The Sign Chamber: speaking to Mara is the #6 payoff ---
    # (2026-07: she kneels at the Mask's foot now, not the deep hive.)
    g.load_scene_now("works_sign")
    ready(g)
    mara = next((n for n in g.scene.npcs if n.name == "Mara"), None)
    check(mara is not None,
          "sign chamber: Mara kneels among the congregation")
    if mara:
        mara.dialogue_fn(g, mara)
        check(g.save.flag("hive_seen"),
              "sign chamber: speaking to Mara fires the recognition")

    # --- 7. The Threshold seal -> the SEAL ending (consumes the keystone) ---
    # The keystone (the Mask) carried down from the Deepest Face is spent HERE,
    # at the door (§7 rework, Mask-only). g still holds it (the blast did not spend it).
    g.load_scene_now("threshold")
    ready(g)
    sc = g.scene
    check(g.player.inventory.has("pallid_mask"),
          "threshold: the keystone (Mask) arrives in hand (carried from the stair)")
    g.player.x, g.player.y = sc._lintel_pos
    sc.on_update_fn(g, sc, 0.1)               # walking THROUGH the frame
    check(getattr(g, "_seal_warp", None) is not None,
          "threshold: walking through the frame starts the LIVE warp")
    check(not g.player.inventory.has("pallid_mask"),
          "threshold: the seal CONSUMES the keystone (Mask) at the door")
    n_deco = len(sc.decorations)
    for _ in range(120):                      # the world pours through...
        if g._ending_active:
            break
        sc.on_update_fn(g, sc, 0.1)
    check(g._ending_active == "seal_threshold",
          "threshold: the live warp hands off to the SEAL ending")
    check(len(sc.decorations) < n_deco,
          "threshold: the warp consumed the room's dressing")
    # Canon (2026-06, approved text): the crossing lands you under the
    # black stars and the twin suns of Carcosa, and the run closes on
    # 'Rage approaches.' into the WORDLESS tableau (the final empty line).
    seal_text = " ".join(line for line, _ in
                         g._ENDING_SCRIPTS["seal_threshold"])
    check("black stars" in seal_text and "Rage approaches." in seal_text,
          "threshold: SEAL text is the approved set (black stars; Rage)")
    check("held the Mask" in seal_text and "the door slams shut" in seal_text,
          "threshold: SEAL text keeps the crossing + the slam beats")
    check(g._ENDING_SCRIPTS["seal_threshold"][-1][0] == "",
          "threshold: SEAL closes on the wordless tableau still")
    check("hole in the map" not in seal_text
          and "roads decline" not in seal_text,
          "threshold: SEAL carries no dead hole-in-the-map language")
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
    gs.player.inventory.add("pallid_mask", 1)
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
    fire(gt3, "the_old_stores", "_dig_note_pos")
    check(gt3.player.inventory.has("cult_digging"),
          "old stores: grants The Digging (optional testimony fragment)")
    check(any(isinstance(e, dict) and e.get("name") == "cult_digging"
              for e in gt3.save.arg("notes", [])),
          "old stores: The Digging logs the PI reaction to NOTES")
    check(evidence_count(gt3) == _e3,
          "old stores: The Digging never inflates evidence")
    # CANON (§1b discipline): the dimensional truth is NEVER stated in the
    # testimony the player reads.
    _triptych = ("cult_calling", "cult_bargain", "cult_digging")
    _blob = " ".join(_IDEFS[k]["desc"].lower() for k in _triptych)
    check("dimension" not in _blob,
          "testimony: never says 'dimension' (folk horror, not sci-fi)")
    check("playscript" not in _IDEFS,
          "items: the old single playscript keystone is retired")

    # --- 9. The 3-evidence King gate is reachable ON THE SURFACE (the
    # Act-1 threat ramp; NARRATIVE §6, DESIGN.md §9). Mara's three surface-
    # trail beats -- the store tab (shop), the booking slip (office), the
    # journal (barn) -- each a world-persistent pickup, findable in any
    # order. Three surface beats = exactly the King-gate above ground.
    from scenes.dialogue import hettie_dialogue as _hettie_fn
    ge = new_game()
    # The store tab comes from Hettie's WARM handover now (play-notes): show
    # her Mara's photo, she works the tab off the spike and hands it over.
    ge.load_scene_now("shop")
    ready(ge)
    _het = next((nn for nn in ge.scene.npcs if nn.name == "Hettie"), None)
    check(_het is not None, "shop: Hettie keeps the counter")
    ge.save.set_flag("hettie_greeted", True)
    ge.save.set_flag("hettie_saw_photo", True)         # the PI showed the photo
    _hettie_fn(ge, _het)                                # her Mara-memory beat
    check(ge.player.inventory.has("receipt")
          and has_evidence(ge, "maras_receipt"),
          "shop: Hettie hands over the store tab shown Mara's photo (surface evidence)")
    fire(ge, "sheriff_office", "_record_pos")          # maras_record
    check(ge.player.inventory.has("detention_record")
          and has_evidence(ge, "maras_record"),
          "office: the booking slip is a world-persistent pickup (surface evidence)")
    # The journal is a WALK-OVER pickup now (play-notes), not an [E] interact.
    ge.load_scene_now("barn")
    ready(ge)
    ge.player.x, ge.player.y = ge.scene._journal_pos   # step onto it
    ge.scene.on_update_fn(ge, ge.scene, 0.05)          # the walk-over pickup
    jlines = next((e["lines"] for e in ge.save.arg("evidence", [])
                   if e.get("name") == "maras_journal"), [])
    jtext = " ".join(jlines).lower()
    check(any(k in jtext for k in ("you go down", "below the town",
                                   "digging down")),
          "barn: Mara's journal motivates the descent (points down/below)")
    check("learned my name" in jtext,
          "barn: the journal log carries her ache (grief, page 1)")
    n = evidence_count(ge)
    check(n >= 3, f"evidence: the 3-gate is reachable on the SURFACE "
                  f"(gathered {n} canonical beats above ground)")

    # --- 9b. World-persistence: the surface records outlive the local, so
    # killing Hettie or Vane can never soft-lock the descent (NARRATIVE §6,
    # DESIGN.md §9). The tab is on the spike, the slip in the files, not on
    # the person -- reachable with the local recorded dead.
    gwp = new_game()
    gwp.save.set_arg("dead_locals", {"shop:Hettie": {
        "scene": "shop", "x": 0, "y": 0, "name": "Hettie", "idx": None}})
    # With Hettie dead, the spike is the FALLBACK: a walk-over pickup the
    # shop's on_update_fn opens (no warm handover to lean on).
    gwp.load_scene_now("shop")
    ready(gwp)
    gwp.player.x, gwp.player.y = gwp.scene._receipt_pos   # step onto the spike
    gwp.scene.on_update_fn(gwp, gwp.scene, 0.05)          # the walk-over pickup
    check(has_evidence(gwp, "maras_receipt"),
          "persist: the store tab is reachable with Hettie recorded dead")
    gwp.save.set_arg("dead_locals", {"sheriff_office:Sheriff": {
        "scene": "sheriff_office", "x": 0, "y": 0, "name": "Sheriff",
        "idx": None}})
    fire(gwp, "sheriff_office", "_record_pos")
    check(has_evidence(gwp, "maras_record"),
          "persist: the booking slip is reachable with Vane recorded dead")

    # --- 10. The Kid is the witness (NARRATIVE §4): tells, grants no item ---
    from scenes.dialogue import TOBY_CONVO as _TOBY_CV
    gk = new_game()
    gk.load_scene_now("toby_house")
    ready(gk)
    kid = next((nn for nn in gk.scene.npcs
                if nn.name == "Toby"), None)   # renamed in the merge
    check(kid is not None, "kid: the Kid is present in his house")
    # The witness account is EARNED, not volunteered: it rides the photo
    # exchange (the PI holds Mara's picture out), never a cold greeting -- a
    # kid cannot know the case on sight (only Sable met the PI).
    _photo = next((ex for ex in _TOBY_CV["exchanges"]
                   if ex.get("key") == "photo"), None)
    check(_photo is not None, "kid: the witness rides the photo exchange")
    _kid_text = " ".join(b[1] for b in _photo["beats"]).lower()
    # CANON (NARRATIVE §4, D rework 2026-07): the witness does two jobs -- it
    # poses the descent question (Toby FOLLOWED the procession down the RIVER
    # to the cult's dug-open ground, a way no one can follow now -- the grove
    # is fold-hidden) and it SEEDS THE SCHOOL (the commune the Invitation
    # names). Never the corn (the old wrong reading).
    check("river" in _kid_text and "down" in _kid_text,
          "kid: the witness points down the river to where they dug in")
    check("school" in _kid_text,
          "kid: the witness seeds the SCHOOL (the route the rite opens)")
    check("corn" not in _kid_text,
          "kid: the witness no longer sends you into the corn")
    check(not gk.player.inventory.has("polaroid"),
          "kid: the witness grants no inventory item")
    # He knows nothing cold: the greeting must not pre-know the case.
    _greet_text = " ".join(b[1] for b in _TOBY_CV["greet"]["beats"]).lower()
    check("lodge" not in _greet_text and "looking for" not in _greet_text,
          "kid: the greeting does not pre-know the case")

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
    # ("cellar_key" left this list 2026-07: it returned as a REAL item,
    # the gate on the padlocked cellar hatch where the Ledger lives.)
    for dead in ("charcoal", "paper", "car_keys", "cellar_bottle",
                 "liquor_crate", "polaroid"):
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
    _yard = _ld13("lodge_yard")
    check(_yard.exits.get("a", (None,))[0] == "arrival_road",
          "geo: the lodge yard's west exit lands on the arrival road")
    _road = _ld13("arrival_road")
    check(_road.exits.get("a", (None,))[0] == "country_lane"
          and _road.exits.get("e", (None,))[0] == "lodge_yard",
          "geo: the arrival road's dirt path links country_lane (W) and yard (E)")
    # The road reads INFINITE without a full-column wrap: a landmark-free north
    # BAND renders endlessly (_render_band) and loops travel (_treadmill), while
    # the southern arrival stretch (car / sign / dirt crossing) renders ONCE.
    # wrap_y is deliberately OFF -- a full wrap cloned those landmarks into the
    # northern view (the old loop tell, now reversed).
    check(not _road.wrap_y and hasattr(_road, "_render_band")
          and hasattr(_road, "_treadmill") and hasattr(_road, "_car_pos"),
          "geo: the arrival road renders endlessly via a north band "
          "(_render_band) + loops travel over it (_treadmill); no full wrap")
    # EVERY northern render row must map back into the landmark-free band, so no
    # car / sign / dirt path can ever clone into the distance up the runway.
    _bt, _bb = _road._render_band
    _north_ok = all(_bt <= _road.render_row(_ty) < _bb
                    for _ty in range(-60, _bt))
    _band_clean = all("d" not in "".join(_road.floor[_r])
                      and "X" not in "".join(_road.objects[_r])
                      for _r in range(_bt, _bb))
    check(_north_ok and _band_clean,
          "geo: the northern view only ever shows the landmark-free band "
          "(no dead car, town sign, or dirt path repeating up the road)")
    check(_road.h >= 30,
          "geo: the road is taller than a screen so the south landmarks stay "
          "off-frame from the looping band (you never see two cars at once)")
    check("_car_pos" not in inspect.getsource(_ml.build_brimley),
          "geo: the car is gone from brimley (consolidated at the lodge)")
    gr = new_game()
    gr.load_scene_now("arrival_road")
    ready(gr)
    gr.player.x, gr.player.y = gr.scene._car_pos
    gr.player.inventory.add("pallid_mask", 1)
    gr.scene.on_interact_fn(gr)
    check(gr._ending_active == "escape_alone",
          "geo: SPREAD fires at the car on the arrival road (with the Sign)")

    # --- 13c. The woodshed is consolidated into the lodge yard ------------
    # It used to sit across town in brimley; now it is a key-gated door in
    # the Arcadia yard (west of the lodge) and exits back to the yard. The
    # brimley shed door is gone.
    _yard2 = _ld13("lodge_yard")
    _shed = _ld13("woodshed")
    check(hasattr(_yard2, "_shed_door_pos"),
          "geo: the lodge yard has the woodshed door (west of the lodge)")
    check(_shed.exits.get("h", (None,))[0] == "lodge_yard",
          "geo: the woodshed exits back into the lodge yard")
    check("_shed_door_pos" not in inspect.getsource(_ml.build_brimley),
          "geo: brimley no longer hosts the woodshed door (consolidated)")
    gw = new_game()
    gw.load_scene_now("lodge_yard")
    ready(gw)
    gw.player.x, gw.player.y = gw.scene._shed_door_pos
    gw.scene.on_interact_fn(gw)                       # locked, no key
    check(gw.scene.key == "lodge_yard",
          "geo: the shed door is locked without the cellar key")
    gw.player.inventory.add("woodshed_key", 1)
    gw.scene.on_interact_fn(gw)                       # key in hand -> enters
    check(getattr(gw, "transition_target", (None,))[0] == "woodshed",
          "geo: the cellar key opens the yard shed -> woodshed interior")

    # --- 13c. Picking up Mara's journal (walk-over) fires the dream -----
    # The journal is a WALK-OVER pickup now (play-notes): stepping onto it
    # takes the item, logs the gate beat QUIETLY (no scribble before he has
    # read it), and fires the door-dream ON PICKUP. Reading it later is just
    # reading -- no second trigger.
    from systems.items import MARA_JOURNAL_PAGES, journal_page as _jpage
    from ui.journal_ui import PAPERS_TAB
    gj = new_game()
    gj.load_scene_now("barn", "default")
    ready(gj)
    gj.player.x, gj.player.y = gj.scene._journal_pos
    gj.scene.on_update_fn(gj, gj.scene, 0.05)         # step onto it
    check(gj.player.inventory.has("mom_notebook"),
          "journal: walking onto it picks it up (a ground item, not an [E] cue)")
    check(has_evidence(gj, "maras_journal"),
          "journal: the pickup logs the gate beat")
    check(gj.save.flag("flashback_pending"),
          "journal: the door-dream fires ON PICKUP, not the 3rd read")
    # Reading it is now just reading -- no second dream trigger.
    gj.save.set_flag("flashback_pending", False)
    gj.inv_ui.open = True
    gj.inv_ui.tab = PAPERS_TAB
    _fk = [k for _, k, _ in gj.inv_ui._filtered_items(gj.player.inventory)]
    gj.inv_ui.cursor = _fk.index("mom_notebook")
    check(_jpage(gj.save)[1] == 0,
          "journal: opens on page 1 (its words are visible immediately)")
    gj.inv_ui.use_selected(gj.player)                 # turn the leaves
    gj.inv_ui.use_selected(gj.player)
    gj.inv_ui.use_selected(gj.player)
    check(not gj.save.flag("flashback_pending"),
          "journal: reading it does NOT re-fire the dream (pickup is the trigger)")

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
    # CANON (NARRATIVE §2 / spectrum note): the PI dreamed of the door
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

    # --- 14c. The starting room: sidearm on the desk, notes readable ---
    # The PI wakes UNARMED; his revolver sits on the writing desk beside his
    # case notes (a visible `papers` prop), and the desk's [E] READS the
    # notes -- it used to be stolen by an overlapping hide spot, which has
    # moved to the wardrobe.
    import math
    from constants import TILE
    def _desk(g):
        return next((d for d in g.scene.decorations
                     if getattr(d, "tag", None) == "writing_desk"), None)
    def _gun_on_desk(g):
        d = _desk(g)
        return bool(d and getattr(d, "gun_present", False))
    gsr = new_game()
    gsr.load_scene_now("bedroom", "default")
    check(not gsr.player.inventory.has("pistol"),
          "startroom: the PI wakes without the pistol in his pocket")
    check(_desk(gsr) is not None,
          "startroom: the writing desk (with the case file on top) is present")
    check(_gun_on_desk(gsr),
          "startroom: the revolver is on the desk")
    # no hide spot overlaps the desk's [E] position
    dnx, dny = 11 * TILE, 6 * TILE
    hide_over_desk = any(math.hypot(hx - dnx, hy - dny) < 36
                         for hx, hy, _k in (gsr.scene.hide_spots or []))
    check(not hide_over_desk,
          "startroom: no hide spot shadows the desk's [E]")
    # [E] at the desk opens the close-up EXAMINE TABLEAU (play-notes): a
    # lamp-lit close-up of the pistol + case file with a menu.
    gsr.save.set_flag("wake_up", True)
    gsr.player.x, gsr.player.y = dnx, dny
    gsr.try_interact()
    check(gsr._tableau is not None and gsr._tableau["kind"] == "desk",
          "startroom: [E] at the desk opens the close-up examine tableau")
    _labels = [o[0] for o in gsr._tableau_options()]
    check("Take the pistol" in _labels and "Read the case file" in _labels
          and "Step back" in _labels,
          "startroom: the tableau menu offers take / read / step back")
    # Selecting TAKE removes the gun from the tableau AND the desk, equips it,
    # and drops the option.
    gsr._tableau_take_gun()
    check(gsr.player.inventory.has("pistol") and not _gun_on_desk(gsr)
          and gsr.player.inventory.equipped.get("weapon") == "pistol"
          and not gsr._tableau["state"]["gun_present"]
          and "Take the pistol" not in [o[0] for o in gsr._tableau_options()],
          "startroom: TAKE lifts the pistol off the desk and drops the option")
    # Selecting READ overlays the case notes (sets read_journal); the player
    # never hides from this.
    gsr._tableau_read_case()
    check(gsr._tableau["reading"] and gsr.save.flag("read_journal")
          and gsr.player.hidden is None,
          "startroom: READ opens the case notes and never hides the player")
    # Walking away (a movement key) interrupts and closes the tableau.
    class _MoveKey:
        type = pygame.KEYDOWN
        key = pygame.K_a
    gsr._tableau_input(_MoveKey())
    check(gsr._tableau is None,
          "startroom: walking away interrupts and closes the tableau")
    # the gun stays gone across a scene reload
    gsr.load_scene_now("bedroom", "from_lodge")
    check(not _gun_on_desk(gsr),
          "startroom: the taken revolver does not reappear on re-entry")

    # --- 15. The gun: the false-power threshold (DESIGN.md §1) ---
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
    # The Calling (the cult's testimony) SEEDS the want-to-leave -- a NOTE, not
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
          "voice: reading The Calling seeds the want-to-leave (descent_leave)")
    check(gp2._evidence_count() == ev_pre,
          "voice: the leave-seed is a NOTE, not evidence (never arms the King-gate)")
    # The Ledger -- a town NOTE now, not case-evidence (NARRATIVE §6) --
    # still carries the PI's voice (the checkout-date confusion), not a dry
    # description. Read from the cellar registers (behind the padlocked
    # hatch).
    gl2 = new_game()
    gl2.player.inventory.add("cellar_key", 1)
    gl2.load_scene_now("lodge_cellar")
    ready(gl2)
    gl2.player.x, gl2.player.y = gl2.scene._ledger_pos
    gl2.scene.on_interact_fn(gl2)         # read the old registers
    _lt = " ".join(l for e in gl2.save.arg("notes", [])
                   if e.get("name") == "the_ledger" for l in e["lines"]).lower()
    # CANON: the checkout dates stop A YEAR back (the same season the PI
    # dreamed the door once) -- never "months". Guard the duration.
    check("a year" in _lt and "months" not in _lt and "keep it in mind" in _lt,
          "voice: the Ledger carries the PI's voice (dates stop a YEAR back)")

    # Chalk-door swarm fills the Scriptorium (obsessive, none overlapping).
    _scr = _ldcd("works_scriptorium")
    _cd = [d for d in _scr.decorations
           if d.kind in ("chalk_door", "chalk_door_wall")]
    check(len(_cd) >= 6,
          "chalk: the Scriptorium is swarmed with chalk doors (the compulsion)")

    # --- 16c. The fold-talk note: the locals' looping-roads account now
    # lives in the ask verb (TODO #1 chorus): Royce's roads exchange (and
    # Garrick's warning) file the PI's note ONCE, named to the teller,
    # and only when actually ASKED -- earned, not ambient.
    gf2 = new_game()
    gf2.load_scene_now("brimley", "default")
    ready(gf2)
    _royce = next((n for n in gf2.scene.npcs if n.name == "Royce"), None)
    _garrick = next((n for n in gf2.scene.npcs if n.name == "Garrick"), None)
    check(_royce is not None and _garrick is not None,
          "fold: the fold-mentioning locals are present")
    _evp = gf2._evidence_count()
    # Drive the REAL path: greet floats, the menu opens, the PI picks
    # "What do the roads do?", and the exchange files the note.
    gf2.player.x, gf2.player.y = _royce.x + 20, _royce.y
    _royce.dialogue_fn(gf2, _royce)
    g_ = 0
    while gf2.float_speech.active and g_ < 30:
        gf2.float_speech._finish(); g_ += 1
    check(gf2.dialog.choices is not None,
          "fold: Royce's question menu opens after his greeting")
    check(not gf2.save.flag("voice_fold_heard"),
          "fold: merely talking to Royce files nothing (the ask earns it)")
    gf2.dialog.choice_idx = gf2.dialog.choices.index("What do the roads do?")
    gf2.dialog.advance()
    _ft = next((e for e in gf2.save.arg("notes", [])
                if isinstance(e, dict) and e.get("name") == "the_fold_told"), None)
    check(_ft is not None and "Royce" in " ".join(_ft["lines"]),
          "fold: a local describing the fold files the note, naming who told you")
    check(gf2._evidence_count() == _evp,
          "fold: the fold note is a NOTE, not evidence (never arms the King-gate)")
    # Garrick's warning carries the same account; the note stays one-shot.
    from scenes.dialogue import _garrick_roads_told as _grt16
    _grt16(gf2)
    check(sum(1 for e in gf2.save.arg("notes", [])
              if isinstance(e, dict) and e.get("name") == "the_fold_told") == 1,
          "fold: only the FIRST fold mention files the note (not every speaker)")
    if getattr(gf2, "_convo", None) is not None:
        gf2._convo.active = False
        gf2._convo = None
    gf2.float_speech.active = False
    ready(gf2)

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

    # --- 17. The principal locals are named (NARRATIVE §4/§8) ---
    # A small town knows its people by name. Every principal now speaks
    # through the organic conversation (TODO #1 expand), so the
    # proper-name label rides every floated line via the convo data.
    from scenes.dialogue import (toby_dialogue, clerk_dialogue,
                                 SABLE_CONVO as _SC, VANE_CONVO as _VC,
                                 HETTIE_CONVO as _HC, TOBY_CONVO as _TC,
                                 CRANE_CONVO as _CC)

    def first_speaker(dialogue_fn):
        g = new_game()
        cap = []
        g.dialog.show = (lambda real: (lambda p, **k: (
            cap.append(k.get("speaker", "")), real(p, **k))[1]))(g.dialog.show)
        dialogue_fn(g, type("N", (), {"name": "x", "x": 0, "y": 0})())
        return cap[0] if cap else None

    for expected, cv in [("Mr. Sable", _SC), ("Sheriff Vane", _VC),
                         ("Hettie", _HC), ("Toby", _TC),
                         ("Rev. Crane", _CC)]:
        check(cv["name"] == expected,
              f"naming: a principal local speaks as '{expected}' "
              "(not a role-tag)")
    # Sable checked the PI in the night before the game opens (NARRATIVE
    # §3), so his greeting RESUMES the acquaintance instead of introducing
    # him; his name still surfaces as the float-speech speaker label
    # (guarded above). Lock the arrival fact, not the wording.
    _sable_greet = _SC["greet"]["beats"][0][1]
    check(("came in" in _sable_greet or "last night" in _sable_greet),
          "canon: Sable's greeting acknowledges the night-before arrival")
    check(not _sable_greet.startswith("Sable"),
          "canon: Sable's greeting is not a self-introduction")
    check("Vane" in _VC["greet"]["beats"][0][1],
          "naming: Vane's floated greeting introduces him by name")
    # Toby's witness account is EARNED on the photo exchange (a kid cannot
    # know the case cold), and his conversation speaks under his own name.
    check(_TC["name"] == "Toby",
          "naming: Toby's conversation speaks under his own name")
    check(any(ex.get("key") == "photo" for ex in _TC["exchanges"]),
          "kid: the witness account rides the photo exchange, not a cold open")

    # --- 17b. Sable is the most-attuned LOCAL (NARRATIVE §4) -------------
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

    # --- 17c. The investigation ASK verb (pilot: Mr. Sable, TODO #1) -----
    # The menu options ARE the PI's own spoken lines; picking one plays an
    # organic PI<->NPC exchange over their heads (ui/conversation), and new
    # questions open as the case grows. Guard the engine + Sable's script.
    from scenes.dialogue import SABLE_CONVO
    from ui.conversation import Conversation

    def _npc_stub(gg):
        return type("N", (), {"name": "Mr. Sable",
                              "x": gg.player.x, "y": gg.player.y,
                              "alive": True, "_is_corpse": False,
                              "_inside": False})()

    # (1) A fresh talk floats the greeting once, THEN opens the menu.
    ga = new_game()
    convo = Conversation(ga, _npc_stub(ga), SABLE_CONVO)
    ga.dialog.active = False
    convo.start()
    check(ga.save.flag("sable_greeted") and ga.float_speech.active
          and not ga.dialog.active,
          "ask: the first talk floats Sable's greeting (no modal band)")
    # Drive the greeting to completion the way the loop would; the menu opens.
    ga.float_speech._finish()
    check(ga.dialog.choices is not None,
          "ask: once greeted, the menu of the PI's questions opens")

    # (2) The menu offers only AVAILABLE questions; base ones plus a leave.
    base = [ex for ex in SABLE_CONVO["exchanges"] if "avail" not in ex]
    check(len(ga.dialog.choices) == len(base) + 1,
          "ask: the menu lists the open questions plus a leave option")
    # Every option is a first-person spoken line, not an abstract topic
    # label (the whole point of the rework): none is of the form "The X."
    opts = ga.dialog.choices
    check(all(not (o.startswith("The ") and o.endswith(".") and " " not in o[4:-1])
              for o in opts),
          "ask: options are the PI's spoken lines, not 'The X' topic tags")

    # (3) Evidence-gated questions are hidden until the discovery is made.
    q_checkouts = next(ex for ex in SABLE_CONVO["exchanges"]
                       if ex["key"] == "checkouts")
    check(not q_checkouts["avail"](ga),
          "ask: the register question is hidden before the Ledger is found")
    ga.save.set_flag("evidence_the_ledger", True)
    check(q_checkouts["avail"](ga),
          "ask: reading the Ledger opens the register question")

    # (4) The per-discovery revisit nudges were CUT (play-notes): a discovery
    # no longer appends an "I should go back and ask him" line or files a
    # revisit note. The follow-up QUESTION still opens on the evidence alone
    # (tested above), so nothing is lost but the hand-holding.
    from scenes.dialogue import _collect_revisit
    ga.save.set_flag("sable_greeted", True)
    ga.save.set_arg("evidence", [])
    ga.save.set_arg("notes", [])
    check(_collect_revisit(ga, "the_ledger") == [],
          "ask: the revisit nudge is cut (a discovery adds no interior append)")
    check(not any(isinstance(e, dict)
                  and e.get("name") == "revisit_sable_checkouts"
                  for e in ga.save.arg("notes", [])),
          "ask: no revisit note is filed (the nudges were cut)")

    # (5) An inline branch (show the photo) is a real fork with a side effect.
    mara = next(ex for ex in SABLE_CONVO["exchanges"] if ex["key"] == "mara")
    ask_beat = next(b for b in mara["beats"] if b[0] == "ask")
    check(len(ask_beat[2]) == 2 and ask_beat[2][0][2] is not None,
          "ask: the photo beat is a two-way choice with a consequence")

    # (6) TONE: the first local we meet does NOT give the girl up. He
    # deflects the name, folds her in with the newcomers, and misdirects
    # at the "unfriendly" locals (the trap the game punishes). He must
    # never confirm he knows her or where she is.
    _mtxt = " ".join(b[1].lower() for b in mara["beats"] if b[0] in ("npc", "pi"))
    _mb0 = mara["beats"][0][1].lower()
    check("can't say" in _mb0 and "name" in _mb0,
          "tone: Sable deflects the name instead of confirming it")
    check(not any(s in _mtxt for s in
                  ("that is her", "sat right where", "smiling, by the end",
                   "i will know her")),
          "tone: Sable never confirms he knows the girl or where she is")
    check("new folk" in _mtxt
          and any(s in _mtxt for s in ("cold as our root cellar", "unfriendly",
                                       "not everyone")),
          "tone: the opener sets the newcomer/hostile-local split for the town")

    # (7) The Invitation drops with Sable if he is killed before the handoff
    # (he carries the way down), and NOT if he already gave it -- and the
    # drop never sets the _given flag (that would soft-lock a missed drop).
    from scenes.dialogue import sable_on_death
    gk = new_game()
    gk.load_scene_now("bedroom")
    _n0 = len(gk.scene.items)
    sable_on_death(gk, type("N", (), {"x": 100.0, "y": 100.0})())
    check(sum(1 for it in gk.scene.items if it.get("key") == "rite_envelope") == 1,
          "drop: killing Sable before the handoff drops the Invitation")
    check(not gk.save.flag("rite_envelope_given"),
          "drop: the corpse drop never sets the _given flag (no soft-lock)")
    gk2 = new_game()
    gk2.load_scene_now("bedroom")
    gk2.save.set_flag("rite_envelope_given", True)
    _n2 = len(gk2.scene.items)
    sable_on_death(gk2, type("N", (), {"x": 1.0, "y": 1.0})())
    check(len(gk2.scene.items) == _n2,
          "drop: no Invitation drops if he already handed it over")
    # And the desk handoff will not double-give once the PI already carries one.
    gk3 = new_game()
    gk3.player.inventory.add("rite_envelope", 1)
    for _i in range(3):
        gk3.save.arg("evidence", []).append({"name": f"_d{_i}", "lines": ["x"]})
    clerk_dialogue(gk3, None)
    check(gk3.player.inventory.count("rite_envelope") == 1,
          "drop: the desk handoff never gives a second Invitation")

    # (8) The starting questions the PI can open with from his OWN knowledge:
    # who he is looking for (Mara), his own dead car, and the cellar of the
    # lodge he is staying in. "Nothing leaves this town" was CUT (a knowledge
    # leak -- he has only seen his own car die; the fold pressure now rides
    # the gated "the_fold" exchange), and "when did she change" was CUT (Sable
    # barely met Mara). The cellar question LEADS to the key: it hints the lost
    # key only while the PI lacks it (callable beats), and asking it lets Sable
    # down to the Ledger (sable_cellar_permission colours that find).
    _keys = {ex["key"] for ex in SABLE_CONVO["exchanges"] if "avail" not in ex}
    check({"mara", "car", "cellar"} <= _keys,
          "ask: the PI can open with Mara, his dead car, and the cellar")
    _skeys = {ex["key"] for ex in SABLE_CONVO["exchanges"]}
    check("sealed" not in _skeys,
          "ask: the ungated 'nothing leaves this town' knowledge leak is gone")
    check("her_state" not in _skeys,
          "ask: the 'when did she change' question is gone (Sable barely met Mara)")
    _cellar = next(ex for ex in SABLE_CONVO["exchanges"] if ex["key"] == "cellar")
    check(callable(_cellar["beats"]),
          "ask: the cellar exchange builds its reply dynamically")
    _gc0 = new_game()
    check(any("misplaced" in b[1] for b in _cellar["beats"](_gc0)),
          "ask: Sable hints the lost cellar key when the PI lacks it")
    _gc1 = new_game()
    _gc1.player.inventory.add("cellar_key", 1)
    check(not any("misplaced" in b[1] for b in _cellar["beats"](_gc1)),
          "ask: no key hint once the PI already carries the key")
    _cellar["on_ask"](_gc0)
    check(_gc0.save.flag("sable_cellar_permission"),
          "ask: asking about the cellar records Sable's permission for the Ledger")

    # (9) The exit hook: the first time the PI tries to leave, Sable stops
    # him with a last word (planting the warped road); it fires once.
    from scenes.dialogue import sable_on_leave
    gx = new_game()
    _h1 = sable_on_leave(gx)
    _h2 = sable_on_leave(gx)
    check(_h1 and "Hold a moment" in _h1[0][1] and _h2 is None,
          "ask: Sable gets one last word the first time you try to leave")

    # (10) The reproach question opens only once the PI has BOTH heard a
    # local name the fold (the_fold_told note) AND crossed one himself
    # (crossed_a_fold, C13) -- so his first-person "it set me back down"
    # can never be a lie -- and it never confesses a plot.
    q_fold = next(ex for ex in SABLE_CONVO["exchanges"] if ex["key"] == "the_fold")
    gr = new_game()
    check(not q_fold["avail"](gr),
          "ask: the folded-roads reproach is hidden before the PI learns it")
    gr.save.set_arg("notes", [{"name": "the_fold_told", "lines": ["x"]}])
    check(not q_fold["avail"](gr),
          "ask: hearing of the fold without crossing one keeps the reproach "
          "hidden (C13)")
    gr.save.set_flag("crossed_a_fold", True)
    check(q_fold["avail"](gr),
          "ask: learning the roads loop opens the reproach to Sable")

    # (11) The readiness nudge: crossing 3 canonical evidence on the surface,
    # still without the rite, files a NOTE pointing the PI back to the desk
    # (so the act break is signposted, not a silent walk-back). Never evidence.
    from scenes.dialogue import _evidence as _evfn
    gn = new_game()
    gn.save.set_flag("sable_greeted", True)
    _evfn(gn, "maras_receipt", "a")
    _evfn(gn, "maras_record", "b")
    check(not any(e.get("name") == "ready_for_the_desk"
                  for e in gn.save.arg("notes", [])),
          "ask: no readiness nudge before the third evidence")
    _evfn(gn, "maras_journal", "c")
    check(any(e.get("name") == "ready_for_the_desk"
              for e in gn.save.arg("notes", [])),
          "ask: the third SURFACE evidence nudges the PI back to the desk")
    check(gn._evidence_count() == 3,
          "ask: the readiness nudge is a NOTE, never evidence")

    # --- 17d. The ask verb EXPANDED to the principals (TODO #1) ----------
    # Vane, Hettie, Toby, and Crane each carry their own conversation, and
    # every principal's menu leads with the two guaranteed openers: the PI
    # introducing himself, and Mara's photograph. News does not spread in
    # Brimley -- nobody knows the case until the PI says it.
    from scenes.dialogue import _INTRO_Q, _PHOTO_Q
    for _cv in (_VC, _HC, _TC, _CC):
        _ks = [ex["key"] for ex in _cv["exchanges"]]
        check(_ks[:2] == ["intro", "photo"],
              f"ask: {_cv['id']} leads with the two guaranteed openers")
        check(_cv["exchanges"][0]["q"] == _INTRO_Q
              and _cv["exchanges"][1]["q"] == _PHOTO_Q,
              f"ask: {_cv['id']} shares the openers word for word")
        check(_cv["exchanges"][0].get("once")
              and _cv["exchanges"][1].get("once"),
              f"ask: {_cv['id']} openers are once-asked")
        _gt = " ".join(b[1].lower() for b in _cv["greet"]["beats"])
        check("blaine" not in _gt and "girl" not in _gt,
              f"ask: {_cv['id']} greet never assumes the case is known")

    # The choice box is SMALL: every menu label (an exchange's `label`,
    # or its `q` where the q is short enough to be its own label) and
    # every inline-ask option must fit it. Budget ~44 chars.
    for _cv in (_SC, _VC, _HC, _TC, _CC):
        for _ex in _cv["exchanges"]:
            _lb = _ex.get("label", _ex["q"])
            check(len(_lb) <= 44,
                  f"ask: {_cv['id']}/{_ex['key']} menu label fits the "
                  f"choice box ({len(_lb)} chars)")
            _bt = _ex["beats"]
            if callable(_bt):
                continue                 # dynamic beats carry no inline asks
            for _b in _bt:
                if _b[0] != "ask":
                    continue
                for _opt in _b[2]:
                    check(len(_opt[0]) <= 44,
                          f"ask: {_cv['id']}/{_ex['key']} inline option "
                          f"fits the choice box ({len(_opt[0])} chars)")

    # Follow-up questions are EARNED, not ambient: Hettie's "who is
    # they" needs her intro answer said; the way-out questions (Hettie,
    # Toby) need a local to have told the PI about the looping roads.
    gg8 = new_game()
    _hsafe = next(ex for ex in _HC["exchanges"] if ex["key"] == "safe")
    _hout = next(ex for ex in _HC["exchanges"] if ex["key"] == "way_out")
    _tout = next(ex for ex in _TC["exchanges"] if ex["key"] == "way_out")
    check(not _hsafe["avail"](gg8),
          "gate: Hettie's 'they' follow-up waits on the intro")
    gg8.save.set_flag("convo_hettie_intro_asked", True)
    check(_hsafe["avail"](gg8),
          "gate: the intro opens Hettie's 'they' follow-up")
    check(not _hout["avail"](gg8) and not _tout["avail"](gg8),
          "gate: the way-out questions wait on the fold being told")
    gg8.save.set_flag("voice_fold_heard", True)
    check(_hout["avail"](gg8) and _tout["avail"](gg8),
          "gate: hearing the fold opens the way-out questions")
    # Once Hettie's volunteered memory has named the girl, the photo
    # question retires (a denial she has already outrun) and the
    # follow-up about the others opens without it.
    _hphoto = next(ex for ex in _HC["exchanges"] if ex["key"] == "photo")
    _hothers = next(ex for ex in _HC["exchanges"] if ex["key"] == "others")
    check(_hphoto["avail"](gg8) and not _hothers["avail"](gg8),
          "gate: pre-memory, the photo stands and the others wait")
    gg8.save.set_flag("hettie_mara_memory", True)
    check(not _hphoto["avail"](gg8) and _hothers["avail"](gg8),
          "gate: her memory retires the photo and opens the others")

    # The Crane fork (the ticket's pilot choice): the flock exchange ends
    # on a real two-way ask. Pressing him latches the doom and files the
    # PI's culpability as a NOTE (never evidence); holding him back leaves
    # the question open to press later; once doomed it retires.
    gcf = new_game()
    _flock = next(ex for ex in _CC["exchanges"] if ex["key"] == "flock")
    check(not _flock["avail"](gcf),
          "crane: the flock question waits on the intro")
    gcf.save.set_flag("convo_crane_intro_asked", True)
    check(_flock["avail"](gcf),
          "crane: after the intro the flock question is open while he lives")
    _fork = next(b for b in _flock["beats"] if b[0] == "ask")
    check(len(_fork[2]) == 2 and _fork[2][0][2] is not None
          and _fork[2][1][2] is None,
          "crane: the fork is press-him (consequence) vs hold-him-back")
    _hold_txt = " ".join(sb[1].lower() for sb in _fork[2][1][1])
    check("for now" in _hold_txt,
          "crane: holding him back only banks the fire (never a rescue)")
    check(not gcf.save.flag("preacher_doomed") and _flock["avail"](gcf),
          "crane: held back, he is not doomed and can be pressed later")
    _ev_cf = len(gcf.save.arg("evidence", []))
    _fork[2][0][2](gcf)                     # press him
    check(gcf.save.flag("preacher_doomed"),
          "crane: pressing him latches the doom (his death files as a note, not evidence)")
    check(any(isinstance(e, dict) and e.get("name") == "crane_provoked"
              for e in gcf.save.arg("notes", [])),
          "crane: the provocation files the PI's NOTE")
    check(len(gcf.save.arg("evidence", [])) == _ev_cf,
          "crane: the provocation never inflates the evidence count")
    check(not _flock["avail"](gcf),
          "crane: once doomed the flock question retires")

    # The Crane-provoke stall-breaker (`_the_third_thread`) was REMOVED with
    # the evidence rework (NARRATIVE §6, DESIGN.md §9): the surface trail is
    # now three carryable pickups in three fixed places (the tab, the slip,
    # the journal), none of them provoke-gated, so there is no third beat to
    # nudge the player toward and no stall to break.
    from scenes.dialogue import _evidence as _evfn2

    # The per-discovery revisit nudges were CUT (play-notes): even a
    # silently-filed beat (show=False) no longer files a revisit note. The
    # follow-up question still opens on the evidence alone, so the case can
    # never stall on a missing nudge.
    gsf = new_game()
    gsf.save.set_flag("sable_greeted", True)
    _evfn2(gsf, "maras_journal", "a", show=False)
    check(not any(e.get("name") == "revisit_sable_smile"
                  for e in gsf.save.arg("notes", [])),
          "ask: the revisit nudges are cut (no note on a silent discovery)")

    # Vane's car answer files the fold note WITHOUT hijacking the
    # conversation's float chain (reflect=False), and it opens Sable's
    # folded-roads reproach.
    from scenes.dialogue import _vane_car_told
    gvf = new_game()
    _sentinel = lambda: None
    gvf.float_speech.active = True
    gvf.float_speech.on_complete = _sentinel
    _vane_car_told(gvf)
    check(any(isinstance(e, dict) and e.get("name") == "the_fold_told"
              for e in gvf.save.arg("notes", [])),
          "vane: the car answer files the PI's fold note")
    check(gvf.float_speech.on_complete is _sentinel,
          "vane: the fold note never hijacks the conversation float chain")
    _qf2 = next(ex for ex in SABLE_CONVO["exchanges"]
                if ex["key"] == "the_fold")
    gvf.save.set_flag("crossed_a_fold", True)   # C13: the PI must have crossed one himself
    check(_qf2["avail"](gvf),
          "vane: his fold account opens the reproach to Sable")
    gvf.float_speech.active = False
    gvf.float_speech.on_complete = None

    # Vane's blind-cultist thread (NARRATIVE §4: his one window into the
    # HOW). TRUST-gated (DESIGN.md §2): it waits on the intro AND a real
    # discovery SHARED with him (found alone is not enough -- trust is
    # earned, not ambient); asking files the PI's NOTE (never evidence);
    # and the account keeps his knowledge boundary (the blind man, the
    # dream's offer, no destination and no cosmology).
    from scenes.dialogue import _vane_how_told
    gvh = new_game()
    _qhow = next(ex for ex in _VC["exchanges"] if ex["key"] == "how")
    check(_qhow.get("once"),
          "vane: the blind-cultist story is spent once")
    check(not _qhow["avail"](gvh),
          "gate: the how waits before the intro and any trust")
    gvh.save.set_flag("convo_vane_intro_asked", True)
    check(not _qhow["avail"](gvh),
          "gate: the intro alone does not open the how")
    _evfn2(gvh, "maras_journal", "a", show=False)
    check(not _qhow["avail"](gvh),
          "gate: a discovery found but never shared does not open the how")
    _qsj = next(ex for ex in _VC["exchanges"] if ex["key"] == "share_journal")
    check(_qsj["avail"](gvh),
          "gate: finding the journal opens its share")
    _qsj["on_ask"](gvh)
    check(_qhow["avail"](gvh),
          "gate: the intro plus a shared discovery opens the how")
    _ev_h = len(gvh.save.arg("evidence", []))
    _vane_how_told(gvh)
    check(any(isinstance(e, dict) and e.get("name") == "the_how"
              for e in gvh.save.arg("notes", [])),
          "vane: asking the how files the PI's NOTE")
    check(len(gvh.save.arg("evidence", [])) == _ev_h,
          "vane: the how never inflates the evidence count")
    _how_txt = " ".join(b[1].lower() for b in _qhow["beats"])
    check("blind" in _how_txt and "dream" in _how_txt,
          "canon: the account is the blind cultist promised by the dream")
    check(not any(w in _how_txt for w in ("below", "down there", "under the",
                                          "king", "door")),
          "canon: Vane keeps his knowledge boundary (no destination)")

    # (Vane town) The 'what happened' answer RECOILS once: the first telling
    # (before the PI knows the seal) lands the horror at "no one has left", and
    # marks the fold heard; once he's learned it (any source) the reaction goes
    # assertive-investigator ("it's not right. How?") with no fresh shock.
    _town = next(ex for ex in _VC["exchanges"] if ex["key"] == "town")
    check(callable(_town["beats"]), "vane: the town answer is dynamic")
    gtn = new_game()
    _tb_first = _town["beats"](gtn)
    check(any(b[0] == "pi" and "No one has left" in b[1] for b in _tb_first),
          "vane: the first telling recoils at 'no one has left'")
    check(gtn.save.flag("voice_fold_heard"),
          "vane: the first telling marks the fold heard (recoil fires once)")
    _tb_again = _town["beats"](gtn)          # knew is True now
    check(any(b[0] == "pi" and "It's not right. How?" in b[1]
              for b in _tb_again),
          "vane: once he knows the seal, the reaction is the assertive 'how'")
    check(not any("Wait. What are you saying" in b[1] for b in _tb_again),
          "vane: no fresh recoil on a restatement")

    # (Vane cache) The office gun cabinet is EARNED: trust-gated like the how,
    # spent once, and granting it arms the office ammo drop (vane_gave_cache).
    _cache = next(ex for ex in _VC["exchanges"] if ex["key"] == "cache")
    check(_cache.get("once"), "vane: the cabinet is handed over once")
    gca = new_game()
    check(not _cache["avail"](gca), "vane: the cabinet waits before trust")
    gca.save.set_flag("convo_vane_intro_asked", True)
    gca.save.set_arg("vane_informed", 1)
    check(_cache["avail"](gca), "vane: intro plus a shared find opens the cabinet")
    _cache["on_ask"](gca)
    check(gca.save.flag("vane_gave_cache"),
          "vane: taking the cabinet arms the office ammo drop")
    check(not _cache["avail"](gca),
          "vane: the cabinet does not re-offer once given")

    # The flow polish: once an exchange finishes, the menu only reopens
    # while both parties are still AT the talk -- the partner walking off
    # (or the player) ends it quietly instead of a modal yank.
    gpx = new_game()
    _stub = _npc_stub(gpx)
    gpx.save.set_flag("sable_greeted", True)
    cvx = Conversation(gpx, _stub, SABLE_CONVO)
    cvx.start()
    check(cvx.active and gpx.dialog.choices is not None,
          "flow: at the desk, the menu opens and the talk is live")
    gpx.dialog.active = False
    gpx.dialog.choices = None
    _stub.x = gpx.player.x + 500            # the player walked off
    cvx.queue = []
    cvx.current = None
    cvx._step()
    check(not cvx.active and gpx.dialog.choices is None,
          "flow: out of earshot the talk ends instead of reopening the menu")

    # The talk-hold: the conversation partner stands their ground and
    # faces the player instead of walking their route mid-exchange --
    # INCLUDING while the PI's own line floats (the float speaker is the
    # player then, and the partner must stay held through it; a worker
    # otherwise walks off between the asked question and its answer).
    ghd = new_game()
    ghd.load_scene_now("church", "default")
    _cr = next(n for n in ghd.scene.npcs
               if getattr(n, "tag", "") == "preacher")
    ghd.player.x, ghd.player.y = _cr.x + 40, _cr.y
    ghd._convo = type("C", (), {"active": True, "npc": _cr})()
    _pos0 = (_cr.x, _cr.y)
    for _ in range(30):
        ghd.scene.update(1 / 30.0, ghd)
    check((_cr.x, _cr.y) == _pos0,
          "flow: the talk-hold roots the partner at the desk")
    check(_cr.facing[0] > 0.9,
          "flow: the held partner faces the player")
    ghd.float_speech.active = True          # a PI beat is floating
    ghd.float_speech.speaker = ghd.player
    for _ in range(30):
        ghd.scene.update(1 / 30.0, ghd)
    check((_cr.x, _cr.y) == _pos0,
          "flow: the hold survives the PI's own floating beats")
    ghd.float_speech.active = False
    ghd.float_speech.speaker = None
    ghd._convo = None

    # A replaced conversation goes INERT: its pending float callback
    # must not reopen a menu over the talk that superseded it.
    from ui.conversation import open_conversation as _oc
    gor = new_game()
    gor.save.set_flag("sable_greeted", True)
    _stub_a = _npc_stub(gor)
    _oc(gor, _stub_a, SABLE_CONVO)
    _old = gor._convo
    gor.dialog.active = False
    gor.dialog.choices = None
    _oc(gor, _npc_stub(gor), SABLE_CONVO)
    check(_old.active is False and gor._convo is not _old,
          "flow: opening a new talk deactivates the replaced one")
    gor.dialog.active = False
    gor.dialog.choices = None
    _old._step()                            # the orphaned callback fires
    check(gor.dialog.choices is None,
          "flow: an orphaned talk's pending callback is inert")

    # --- 17e. The ask verb reaches the Brimley chorus (TODO #1) ----------
    # Old Pell, Mrs. Calder, Royce, and Garrick come off the
    # _brimley_voice page-lists: each carries a conversation that leads
    # with the two guaranteed openers, and their reactive one-shots (the
    # town reacting to the case) still volunteer ahead of the menu.
    from scenes.dialogue import (PELL_CONVO as _PLC, CALDER_CONVO as _CLC,
                                 ROYCE_CONVO as _RCC, GARRICK_CONVO as _GRC)
    for _cv in (_PLC, _CLC, _RCC, _GRC):
        _ks = [ex["key"] for ex in _cv["exchanges"]]
        check(_ks[:2] == ["intro", "photo"],
              f"chorus: {_cv['id']} leads with the two guaranteed openers")
        check(_cv["exchanges"][0]["q"] == _INTRO_Q
              and _cv["exchanges"][1]["q"] == _PHOTO_Q,
              f"chorus: {_cv['id']} shares the openers word for word")
        check(_cv["exchanges"][0].get("once")
              and _cv["exchanges"][1].get("once"),
              f"chorus: {_cv['id']} openers are once-asked")
        _gt = " ".join(b[1].lower() for b in _cv["greet"]["beats"])
        check("blaine" not in _gt and "girl" not in _gt,
              f"chorus: {_cv['id']} greet never assumes the case is known")
        for _ex in _cv["exchanges"]:
            _lb = _ex.get("label", _ex["q"])
            check(len(_lb) <= 44,
                  f"chorus: {_cv['id']}/{_ex['key']} menu label fits the "
                  f"choice box ({len(_lb)} chars)")
            for _b in _ex["beats"]:
                if _b[0] != "ask":
                    continue
                for _opt in _b[2]:
                    check(len(_opt[0]) <= 44,
                          f"chorus: {_cv['id']}/{_ex['key']} inline option "
                          f"fits the choice box ({len(_opt[0])} chars)")

    # The fold note moved off the old any-talk trigger onto the exchanges
    # that actually carry the account: Royce's roads and Garrick's warning
    # file it (reflect=False, never hijacking the float chain), and either
    # opens Sable's reproach and the way-out questions.
    from scenes.dialogue import _royce_roads_told, _garrick_roads_told
    for _teller, _fn in (("royce", _royce_roads_told),
                         ("garrick", _garrick_roads_told)):
        gfd = new_game()
        _sent = lambda: None
        gfd.float_speech.active = True
        gfd.float_speech.on_complete = _sent
        _fn(gfd)
        check(gfd.save.flag("voice_fold_heard") and any(
                  isinstance(e, dict) and e.get("name") == "the_fold_told"
                  for e in gfd.save.arg("notes", [])),
              f"chorus: {_teller}'s roads answer files the PI's fold note")
        check(gfd.float_speech.on_complete is _sent,
              f"chorus: {_teller}'s fold note never hijacks the float chain")
        gfd.float_speech.active = False
        gfd.float_speech.on_complete = None
    _rroads = next(ex for ex in _RCC["exchanges"] if ex["key"] == "roads")
    check(_rroads.get("on_ask") is _royce_roads_told,
          "chorus: Royce's roads exchange carries the fold filing")
    # Royce's counter-question (you got IN) is EARNED by hearing his
    # account first, and it ends on a real two-way ask.
    ghi = new_game()
    _rhow = next(ex for ex in _RCC["exchanges"] if ex["key"] == "how_in")
    check(not _rhow["avail"](ghi),
          "chorus: Royce's how-did-you-get-in waits on his roads account")
    ghi.save.set_flag("convo_royce_roads_asked", True)
    check(_rhow["avail"](ghi),
          "chorus: hearing the roads opens Royce's counter-question")
    _rask = next(b for b in _rhow["beats"] if b[0] == "ask")
    check(len(_rask[2]) == 2,
          "chorus: Royce's counter-question is a real two-way ask")

    # The LIVE wiring: the brimley scene's four chorus locals all open a
    # conversation, and a reactive beat (Garrick clocking the pulpit
    # going quiet) still volunteers ahead of the menu, once. The unnamed
    # "newcomer woman" NPC is CUT from the project (maintainer call,
    # 2026-07); nobody unnamed stands in Brimley.
    gch = new_game()
    gch.load_scene_now("brimley")
    for _nm in ("Old Pell", "Mrs. Calder", "Royce", "Garrick"):
        _lp = next(n for n in gch.scene.npcs
                   if getattr(n, "name", "") == _nm)
        gch.player.x, gch.player.y = _lp.x + 20, _lp.y
        ready(gch)
        gch._convo = None
        _lp.dialogue_fn(gch, _lp)
        check(getattr(gch, "_convo", None) is not None and gch._convo.active,
              f"chorus: {_nm} opens the organic conversation in brimley")
        gch._convo.active = False
        gch._convo = None
        gch.float_speech.active = False
    check(not any(getattr(n, "name", "") == "A woman"
                  for n in gch.scene.npcs),
          "chorus: the cut newcomer woman never spawns in brimley")
    # Homebody vanish only where the door doesn't lie: Old Pell keeps his
    # step (the schoolhouse behind him is enterable + empty), Hettie still
    # ducks into her shop (whose interior holds a Hettie). Guards the
    # "walked into a building, nobody there" consistency fix.
    _pell = next(n for n in gch.scene.npcs if n.name == "Old Pell")
    check(getattr(_pell, "_hb_vanish", True) is False,
          "homebody: Old Pell never vanishes (empty schoolhouse behind him)")
    _het = next((n for n in gch.scene.npcs if n.name == "Hettie"), None)
    check(_het is not None and getattr(_het, "_hb_vanish", None) is True,
          "homebody: Hettie still ducks into her shop (interior holds a Hettie)")
    gch.save.set_flag("preacher_doomed", True)
    gch.save.set_flag("preacher_body_seen", True)   # C10: Garrick's beat gates on the body found
    _gar = next(n for n in gch.scene.npcs if n.name == "Garrick")
    gch.player.x, gch.player.y = _gar.x + 20, _gar.y
    ready(gch)
    _gar.dialogue_fn(gch, _gar)
    check(gch.dialog.active and getattr(gch, "_convo", None) is None
          and gch.save.flag("beat_garrick_quiet"),
          "chorus: Garrick's pulpit beat volunteers ahead of the menu")
    ready(gch)
    _gar.dialogue_fn(gch, _gar)
    check(getattr(gch, "_convo", None) is not None and gch._convo.active,
          "chorus: once the beat is spent the conversation opens")
    gch._convo.active = False
    gch._convo = None
    gch.float_speech.active = False

    # --- 17f. Sheriff Vane's despair/hope arc (DESIGN.md §2; was TODO #2a) -
    # A hidden ledger decides the last holdout's fate; the player never
    # sees a number, only his mood. Sharing a discovery is the one hope
    # act (and the trust currency, guarded in 17d); the preacher's murder
    # and the newspaper are the despair acts. The hollow turn latches at
    # VANE_HOLLOW_AT and never lets go; the NEGLECT override hollows him
    # at the descent line with nothing ever shared.
    from scenes.dialogue import (_vane_ledger, _vane_share, _vane_prompt,
                                 _vane_paper_given, sheriff_dialogue)
    from systems.config import (VANE_HOLLOW_AT, VANE_DESPAIR_FLOOR,
                                VANE_PAPER_DESPAIR, VANE_MIN_INFORMED,
                                VANE_NEGLECT_EVIDENCE)

    # The ledger: shares bank hope only to the floor (real rapport is
    # never immunity), and the mood line reads the balance, no number.
    gva = new_game()
    check("belt" in _vane_prompt(gva),
          "vane-arc: the neutral mood is the old wait-you-out")
    _vane_share(gva); _vane_share(gva); _vane_share(gva)
    check(int(gva.save.arg("vane_despair", 0)) == VANE_DESPAIR_FLOOR,
          "vane-arc: hope banks only down to the floor")
    check(int(gva.save.arg("vane_informed", 0)) == 3,
          "vane-arc: every share counts toward the neglect override")
    check("welcome" in _vane_prompt(gva),
          "vane-arc: banked hope warms the framing line")
    _vane_ledger(gva, 4)
    check("window" in _vane_prompt(gva) and not gva.save.flag("vane_hollow"),
          "vane-arc: despair darkens the framing line before it latches")

    # The newspaper is the break lever (TODO #2): the exchange waits on
    # the intro, spends the one copy (Hettie's trade goes without), and
    # telegraphs the damage as mood -- the PI's own closing line.
    _qpp = next(ex for ex in _VC["exchanges"] if ex["key"] == "paper")
    gvp = new_game()
    check(not _qpp["avail"](gvp),
          "vane-arc: the paper waits on the introduction")
    gvp.save.set_flag("convo_vane_intro_asked", True)
    check(_qpp["avail"](gvp),
          "vane-arc: with the intro made, the paper can be given")
    _vane_paper_given(gvp)
    check(not gvp.player.inventory.has("newspaper"),
          "vane-arc: giving Vane the paper spends the one copy")
    check(int(gvp.save.arg("vane_despair", 0)) == VANE_PAPER_DESPAIR,
          "vane-arc: the paper walks him toward the edge, not over it")
    check(not _qpp["avail"](gvp),
          "vane-arc: the spent paper cannot be given twice")
    _pp_txt = " ".join(b[1] for b in _qpp["beats"])
    check("Cobain" in _pp_txt,
          "vane-arc: the front page carries its centerpiece")
    check("kindness" in _pp_txt,
          "vane-arc: the give-beat telegraphs the damage as mood")

    # The despair path latches: the paper plus the preacher's murder tips
    # a neutral Vane over, and once hollow no hope buys him back.
    gvd = new_game()
    gvd.save.set_flag("convo_vane_intro_asked", True)
    _vane_paper_given(gvd)
    gvd.save.set_flag("preacher_body_seen", True)
    gvd.save.set_flag("vane_greeted", True)
    sheriff_dialogue(gvd, None)             # the murder one-shot: +1
    check(gvd.save.flag("vane_hollow"),
          "vane-arc: paper plus the murder tips a neutral Vane over")
    _vane_ledger(gvd, -10)
    check(gvd.save.flag("vane_hollow")
          and int(gvd.save.arg("vane_despair", 0)) >= VANE_HOLLOW_AT,
          "vane-arc: once hollow, no return")
    # ...while a careful player who shared first eats the same two beats
    # and just survives (the floor is why).
    gvc = new_game()
    gvc.save.set_flag("convo_vane_intro_asked", True)
    _vane_share(gvc); _vane_share(gvc)
    _vane_paper_given(gvc)
    gvc.save.set_flag("preacher_body_seen", True)
    gvc.save.set_flag("vane_greeted", True)
    sheriff_dialogue(gvc, None)
    check(not gvc.save.flag("vane_hollow"),
          "vane-arc: banked hope survives the paper and the murder")

    # The NEGLECT override: the descent line reached with nothing ever
    # shared kills his last hope regardless of the ledger; one shared
    # discovery dodges it. Evaluated at the office gate (_vane_is_hollow),
    # which every share must walk through first.
    gvn = new_game()
    gvn.save.set_arg("evidence",
                     [{"name": f"vn_t{i}", "content": "x"}
                      for i in range(VANE_NEGLECT_EVIDENCE)])
    check(gvn._vane_is_hollow() and gvn.save.flag("vane_hollow"),
          "vane-arc: the neglect override hollows him at the descent line")
    gvm = new_game()
    gvm.save.set_arg("evidence",
                     [{"name": f"vm_t{i}", "content": "x"}
                      for i in range(VANE_NEGLECT_EVIDENCE)])
    for _ in range(VANE_MIN_INFORMED):
        _vane_share(gvm)
    check(not gvm._vane_is_hollow(),
          "vane-arc: one discovery shared dodges the neglect override")

    # The office reads the latch, not the rot stage: a hollow Vane hunts
    # at zero evidence, and a tended Vane still stands at three.
    gvo = new_game()
    gvo.save.set_flag("vane_hollow", True)
    gvo.load_scene_now("sheriff_office")
    ready(gvo)
    check(any(getattr(n, "tag", "") == "sheriff_hunt"
              for n in gvo.scene.npcs),
          "vane-arc: the hollow turn stands the hunter up, whatever the rot")
    gvo2 = new_game()
    gvo2.save.set_arg("evidence",
                      [{"name": f"vo_t{i}", "content": "x"}
                       for i in range(3)])
    _vane_share(gvo2)
    gvo2.load_scene_now("sheriff_office")
    ready(gvo2)
    check(not any(getattr(n, "tag", "") == "sheriff_hunt"
                  for n in gvo2.scene.npcs)
          and any(getattr(n, "name", "") == "Sheriff"
                  and getattr(n, "alive", True) for n in gvo2.scene.npcs),
          "vane-arc: the tended holdout still stands at three evidence")

    # --- 18. effigy_grove is a maker-less tableau (§1b/§8) ---------------
    # Individual cursing is redundant -- the closing rite claimed the town at
    # once -- so the grove is left as the work without the worker, with no
    # NPC tending it.
    from scenes import load_scene as _load2
    grove = _load2("effigy_grove")
    check(len(grove.npcs) == 0,
          "effigy_grove is a maker-less tableau (no NPC)")

    # --- 19. Eat-cult + time-loop fiction stays scrubbed (NARRATIVE §2/§8) -
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
        # The cauldron is REMOVED game-wide (eat-cult imagery; the old
        # clearing centrepiece is now the burn site's dead fire pit).
        "cauldron",
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

    # --- 19b. The underground is a MINE (2026-07 retrofit; DESIGN.md §5).
    # The Works + Depths were dug by the willing over old workings; the
    # claiming cult spills no one. Lock the charnel/killer-cult relics out
    # of the underground scene source: no blood, no gore, no bones, no
    # captivity fiction. ("bone_rack" is also purged from the furniture
    # registry -- guard that too so the art can't quietly return.)
    _charnel = [
        "bloodstain", "\"gore\"", "bone", "in the clerk's hand",
        "leave the body walking", "holding cell", "the claimed were kept",
        "grain mixed with old blood",
    ]
    _chits = []
    for fn in ("well.py", "depths.py"):
        with open(os.path.join(_scene_dir, fn), encoding="utf-8") as fh:
            low = fh.read().lower()
        for phrase in _charnel:
            if phrase in low:
                _chits.append(f"{fn}:{phrase!r}")
    check(not _chits,
          "mine: no charnel/killer-cult fiction underground"
          + (f" (found {_chits})" if _chits else ""))
    from rendering.furniture import FURNITURE as _FURN
    check("bone_rack" not in _FURN,
          "mine: the bone_rack furniture kind stays purged")
    # Underground doors are CAVE MOUTHS (adits), never hinged wood; the
    # surface keeps its framed doors. Draw-only, set by load_scene.
    from scenes import load_scene as _ldm
    from systems.config import UNDERGROUND_SCENES as _UG
    for _uk in sorted(_UG) + ["dark"]:
        check(getattr(_ldm(_uk), "door_style", "") == "cave",
              f"mine: {_uk} doors draw as cave mouths")
    check(getattr(_ldm("lodge"), "door_style", "") == "wood",
          "mine: surface doors stay framed wood")

    # --- 19c. The intro is CULT-FREE, and the welcome sign carries the
    # town's mundane corn pride (2026-07 intro rework; NARRATIVE §1, TODO
    # #11). The PI arrives knowing none of the cult, so the opening drive
    # cards and the bedroom case notebook must never say "found religion".
    # The old-timey BRIMLEY welcome board (intro drive-in + in-game) carries
    # the boast + the founding year.
    _root = os.path.join(os.path.dirname(__file__), "..")

    def _srclow(*parts):
        with open(os.path.join(_root, *parts), encoding="utf-8") as fh:
            return fh.read().lower()
    _cuts = _srclow("ui", "cutscenes.py")
    _lodge_src = _srclow("scenes", "lodge.py")
    check("found religion" not in _cuts and "found religion" not in _lodge_src,
          "intro: no 'found religion' in the drive cards or bedroom notebook")
    _props = _srclow("rendering", "props.py")
    check("northernmost corn" in _cuts and "1894" in _cuts,
          "intro sign: the drive-in welcome board carries the corn boast + EST. 1894")
    check("northernmost corn" in _props and "1894" in _props,
          "welcome sign: the in-game board carries the corn boast + EST. 1894")

    # --- 20. Cultists use dynamic AI, not preset coordinates (DESIGN.md §4) -
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

    # --- 21. A chase carries ONLY through rift FOLDS, not ordinary exits ----
    # (play-notes narrowing of DESIGN.md §7). A chaser follows within a scene
    # and across a direction-gated fold; an ORDINARY crossing shakes it -- a
    # seamless passage, a road loop, a door, or a descent target reached off a
    # non-fold tile. The rift-fold carry itself is guarded in
    # tests/fold_pursuit.py (which stands the player ON a fold tile).
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
        gp._note_fold_pursuit((next(iter(_UG)), "default"))   # not on a fold tile
        check(gp._fold_pursuer is None,
              "portal: an ordinary crossing (non-fold) does NOT carry the chase")
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
    for _br in ("the_sump", "the_cells", "the_old_stores"):
        check(_br in _UG, f"portal: branch room {_br} is registered underground")
        check(_br in _DK, f"dark: branch room {_br} gets the underground gloom")

    # --- 22. Ashfall scales with the world rot, never on the Threshold ----
    # (DESIGN.md §2) The pale-yellow ash is the vessel's pressure made
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

    # --- 23. The beat pass: paper trade, Vane one-shot, Calder, SPREAD ------
    # (a) The PI carries yesterday's paper (the April 14 issue, bought
    # before the drive north) and Hettie trades it ONCE for one load of
    # the cartridges under the counter: Brimley hasn't seen a paper since
    # the trucks stopped, so yesterday's date makes the cut-off legible,
    # and the trade is how starved for word they are. A single barter,
    # never a fetch chain.
    from scenes.dialogue import hettie_dialogue, sheriff_dialogue
    from systems.items import ITEM_DEFS as _IDEFS
    gp = new_game()
    check(gp.player.inventory.has("newspaper"),
          "paper: the PI drives in with yesterday's paper")
    check("April 14" in _IDEFS["newspaper"]["desc"],
          "paper: the issue is dated April 14 (the cut-off yardstick)")
    gp.save.set_flag("hettie_greeted", True)    # she has met you once
    _ammo0 = gp.player.inventory.count("pistol_ammo")
    hettie_dialogue(gp, None)
    check(gp.save.flag("newspaper_traded")
          and not gp.player.inventory.has("newspaper")
          and gp.player.inventory.count("pistol_ammo") == _ammo0 + 6,
          "paper: Hettie trades the paper for one load of cartridges")
    _ammo1 = gp.player.inventory.count("pistol_ammo")
    hettie_dialogue(gp, None)
    check(gp.player.inventory.count("pistol_ammo") == _ammo1,
          "paper: the trade fires exactly once (can't be farmed)")

    # (a2) The calendar sweep: the seal is mid-January
    # 1994, so nothing may date the cut-off to spring. Hettie's till went
    # empty at the new year, and the case note has Mara driving north in
    # the fall and going quiet by the new year.
    import inspect as _insp
    import scenes.dialogue as _dlg
    _dlg_src = _insp.getsource(_dlg)
    check("since the spring" not in _dlg_src and "since spring" not in _dlg_src,
          "calendar: no dialogue dates the cut-off to spring")
    check("since the new year" in _dlg_src,
          "calendar: Hettie's till went empty at the new year (the seal)")
    _case_n = next((e for e in gp.save.arg("notes", [])
                    if isinstance(e, dict) and e.get("name") == "the_case"),
                   None)
    _case_t = " ".join(_case_n["lines"]).lower() if _case_n else ""
    check("drove north in the fall" in _case_t
          and "by the new year" in _case_t
          and "spring" not in _case_t and "thaw" not in _case_t,
          "calendar: the case note keeps Mara's fall drive + new-year silence")

    # (b) Sheriff Vane's murder beat is a one-shot gated on the player
    # having SEEN the church floor -- he can never announce the killing
    # before it is found (the old visit-4 slot could).
    gv = new_game()
    _vane_lines = []
    gv.dialog.show = (lambda real: (lambda p, **k: (
        _vane_lines.extend(p if isinstance(p, list) else [p]),
        real(p, **k))[1]))(gv.dialog.show)
    gv.save.set_flag("vane_greeted", True)      # he has met you
    sheriff_dialogue(gv, None)
    check("preacher" not in " ".join(_vane_lines).lower(),
          "vane: never announces the murder before the body is found")
    del _vane_lines[:]
    gv.save.set_flag("preacher_body_seen", True)
    sheriff_dialogue(gv, None)
    check("preacher" in " ".join(_vane_lines).lower()
          and gv.save.flag("vane_preacher_noticed"),
          "vane: the murder one-shot lands after the church floor is seen")
    del _vane_lines[:]
    sheriff_dialogue(gv, None)
    check("preacher" not in " ".join(_vane_lines).lower(),
          "vane: the murder beat fires exactly once")

    # (c) The TOWN STAYS ORDINARY to the end (TODO #22c, NARRATIVE §2): the world rot is the PI's now, not the townsfolk's.
    # The old people-change is CUT -- no peace-maker is repainted a cultist,
    # no resister's voice curdles, and the machinery is gone.
    import systems.config as _cfg
    import rendering.sprites as _spr
    from ui.dialog import DialogueBox as _DB
    from systems import rot_mixin as _rm
    check(not hasattr(_cfg, "ROT_CONVERT") and not hasattr(_cfg, "ROT_TURN"),
          "rot: the convert/turn tables are removed from config")
    check(not any(hasattr(_rm, n) for n in
                  ("ROT_TURN_LINES", "_turned_local_dialogue",
                   "_converted_local_dialogue")),
          "rot: the curdled-dialogue helpers are removed from rot_mixin")
    check(not any(hasattr(_rm.RotMixin, m) for m in
                  ("_rot_locals", "_convert_local", "_spawn_counter_eater")),
          "rot: the people-change methods are removed from RotMixin")
    # The older mutate body-horror layer stays cut too (TODO #9).
    check(not hasattr(_cfg, "INFEST_MUTATE")
          and not hasattr(_spr, "draw_infested_overlay")
          and not hasattr(_DB, "_draw_infested_portrait"),
          "rot: the infested/mutate overlay + portrait stay removed")
    # Both place settings stand for the whole run: Mrs. Calder never joins
    # and never stops waiting, before AND at the old descent-line peak.
    g0 = new_game()
    g0.load_scene_now("brimley")
    check(sum(1 for d in g0.scene.decorations
              if getattr(d, "kind", "") == "place_setting") == 2,
          "calder: both settings stand at 0 evidence")
    gc = new_game()
    gc.save.set_arg("evidence", ["e0", "e1", "e2"])   # stage 3 (the old peak)
    gc.load_scene_now("brimley")
    check(sum(1 for d in gc.scene.decorations
              if getattr(d, "kind", "") == "place_setting") == 2,
          "calder: both settings STILL stand at stage 3 (she keeps waiting)")
    _cal = next((nn for nn in gc.scene.npcs
                 if getattr(nn, "name", "") == "Mrs. Calder"), None)
    check(_cal is not None and getattr(_cal, "sprite_kind", "") != "cultist"
          and getattr(_cal, "tag", "") != "cult_convert",
          "calder: stays an ordinary local at stage 3 (never converted)")
    check(not any(getattr(nn, "_mutated", False)
                  or getattr(nn, "tag", "") == "cult_convert"
                  or getattr(nn, "sprite_kind", "") == "cultist"
                  for nn in gc.scene.npcs),
          "rot: no townsperson is mutated or a cultist at stage 3 (town reads "
          "normal)")

    # (c2) The four-tier PI register (TODO #22c): the rot surfaces as the
    # PI's FRAMING of a conversation, keyed to evidence (0 / 1-2 / 3 / 4+),
    # never as a word the NPC says. The prompt is a callable that shifts;
    # the NPC observation is identical across tiers.
    from scenes.dialogue import (HETTIE_CONVO as _HCV_r, _pi_tier as _pit,
                                 _PI_WEATHER as _PW)
    _pr = _HCV_r["prompt"]
    check(callable(_pr), "register: the framing is a callable prompt(game)")
    gr = new_game()

    def _frame(ev):
        gr.save.set_arg("evidence", [{"name": f"e{i}"} for i in range(ev)])
        return _pr(gr)
    _f0, _f1, _f3, _f4 = _frame(0), _frame(1), _frame(3), _frame(4)
    check(len({_f0, _f1, _f3, _f4}) == 4,
          "register: the PI's framing deepens across all four tiers")
    check(all("Hettie keeps one eye" in f for f in (_f0, _f1, _f3, _f4)),
          "register: the NPC observation is unchanged (only the PI's read shifts)")
    check(_frame(2) == _f1,
          "register: 1 and 2 evidence share the unsettled tier")
    gr.save.set_arg("evidence", [{"name": f"e{i}"} for i in range(4)])
    check(_pit(gr) == 3, "register: 4+ evidence is the past-return tier")
    check(not any(d in w for w in _PW for d in ("—", "–", "--")),
          "register: no dashes in the PI weather (HARD RULE)")

    # (d) The SPREAD drive-out is the CLAIMING (script locked 2026-06):
    # the mask rides the passenger seat and turns; the PI answers the
    # gaze his one dream broke off a year ago; the verdict card is the
    # three-word close. Guard the load-bearing lines so a rewrite can't
    # drift them silently -- and hold the no-dash rule on all of them.
    spread_lines = [ln for ln, _ in Game._ENDING_SCRIPTS["escape_alone"]]
    check(any("mask shifts in the seat" in ln for ln in spread_lines),
          "spread: the mask turns in the passenger seat (the claiming)")
    check(any("deep sunken eyes" in ln for ln in spread_lines),
          "spread: the PI answers the gaze (the dream, completed)")
    check(spread_lines[-1] == "Everyone will know.",
          "spread: the verdict card closes the run")
    check(not any(("—" in ln) or ("–" in ln) or ("--" in ln)
                  for ln in spread_lines),
          "spread: no dashes in player-facing ending text")

    # --- 24. The town reacts to state (TODO #10) + descent beats (#8) ----
    # Each ambient local carries ONE state beat (a one-shot, gated on what
    # the PI has learned) before falling back to their ambient loop; the
    # procession's candle beat lands as a NOTE. None of
    # it may ever inflate the evidence count (the five canonical beats are
    # locked), and all of it holds the no-dash + no-cosmology rules.
    gb = new_game()
    gb.load_scene_now("brimley")
    ready(gb)
    shown = []
    _orig_show = gb.dialog.show

    def _spy(pages, *a, **k):
        shown[:] = [pages] if isinstance(pages, str) else list(pages)
        return _orig_show(pages, *a, **k)
    gb.dialog.show = _spy

    def _local(nm):
        return next((nn for nn in gb.scene.npcs
                     if getattr(nn, "name", "") == nm), None)

    _ga = _local("Garrick")
    _ev0 = evidence_count(gb)
    if _ga is not None:
        gb.save.set_flag("preacher_doomed", True)
        gb.save.set_flag("preacher_body_seen", True)   # C10: beat gates on the body found
        _ga.dialogue_fn(gb, _ga)
        check(any("gone quiet" in p for p in shown),
              "react: Garrick clocks the pulpit going silent (murder beat)")
        ready(gb)
        shown[:] = []
        gb.player.x, gb.player.y = _ga.x + 20, _ga.y
        _ga.dialogue_fn(gb, _ga)
        check(not any("gone quiet" in p for p in shown)
              and getattr(gb, "_convo", None) is not None,
              "react: the Garrick beat is one-shot; the conversation resumes")
        gb._convo.active = False
        gb._convo = None
        gb.float_speech.active = False
        ready(gb)
    else:
        check(False, "react: Garrick present in brimley")
    gb.save.set_arg("evidence", [{"key": "a", "weight": 0.05},
                                 {"key": "b", "weight": 0.05}])
    for nm, tell in (("Old Pell", "coal dust"), ("Mrs. Calder", "unlatched"),
                     ("Royce", "throat")):
        _n = _local(nm)
        if _n is None:
            check(False, f"react: {nm} present in brimley")
            continue
        _n.dialogue_fn(gb, _n)
        check(any(tell in p for p in shown),
              f"react: {nm} carries a state beat at the gate")
        ready(gb)
        joined = " ".join(shown).lower()
        check(not any(w in joined for w in
                      ("dimension", "lure", "bait", "the king")),
              f"react: the {nm} beat holds the no-cosmology fence")
        check(not any(("—" in p) or ("–" in p) or ("--" in p)
                      for p in shown),
              f"react: no dashes in the {nm} beat")
    check(evidence_count(gb) == 2,
          "react: state beats never inflate the evidence count")

    gp2 = new_game()
    gp2.load_scene_now("depths_procession")
    ready(gp2)
    gp2.player.x, gp2.player.y = 8 * _TILE + 16, 4 * _TILE + 16
    _evp = evidence_count(gp2)
    gp2.scene.on_interact_fn(gp2)
    _pnotes = gp2.save.arg("notes", []) or []
    check(any(isinstance(e, dict) and e.get("name") == "the_procession"
              for e in _pnotes) and evidence_count(gp2) == _evp,
          "descent: the procession candles land as a NOTE, never evidence")

    # --- 24b. Mara's exchange displays; the lure collides once (TODO #6/#7);
    # the SPREAD counterweight names the other road (TODO #9).
    gm = new_game()
    gm.load_scene_now("works_sign")
    ready(gm)
    gm.save.set_flag("flashback_seen", True)
    _mshown = []
    _morig = gm.dialog.show

    def _mspy(pages, *a, **k):
        _mshown.extend([pages] if isinstance(pages, str) else list(pages))
        return _morig(pages, *a, **k)
    gm.dialog.show = _mspy
    _mara = next((n for n in gm.scene.npcs
                  if getattr(n, "name", "") == "Mara"), None)
    if _mara is not None:
        _evm = evidence_count(gm)
        _mara.dialogue_fn(gm, _mara)
        check(getattr(gm, "_convo", None) is not None and gm._convo.active,
              "mara: the confrontation opens as a live conversation")
        check(evidence_count(gm) == _evm
              and any(isinstance(e, dict) and e.get("name") == "the_congregation"
                      for e in gm.save.arg("notes", [])),
              "mara: Mara is PROOF -- the calling-out files a NOTE, never evidence")
        _mj = " ".join(_mshown).lower()
        check("arithmetic" in _mj,
              "lure: the dream+case+Mara collision fires with her greeting")
        check(not any(w in _mj for w in ("marked", "lure", "bait",
                                         "the king", "dimension")),
              "lure: the collision beat holds the fence")
        check(not any(("—" in p) or ("–" in p) or ("--" in p)
                      for p in _mshown),
              "lure: no dashes in the beat")
    else:
        check(False, "mara: present at the Sign Chamber")

    # The confrontation's shape (NARRATIVE §4 canon invariants, 2026-07).
    import re as _re
    from scenes.well import MARA_CONVO as _MCV
    _mkeys = {ex["key"] for ex in _MCV["exchanges"]}
    check(_mkeys == {"leave", "way_out", "father", "name"},
          "mara: the asks are come-with-me / the-way-out / her father / "
          "the boy's name (bear-gated, TODO #22b)")
    _mf = next(ex for ex in _MCV["exchanges"] if ex["key"] == "father")
    check(bool(_mf.get("once")) and bool(_mf.get("ends")),
          "mara: the father card plays once and ENDS the talk (she turns "
          "back; no exchange is a rescue)")
    _ftxt = " ".join(b[1].lower() for b in _mf["beats"] if b[0] == "npc")
    check("what am i doing" in _ftxt and "only deeper" in _ftxt,
          "mara: the slip and the lucid turn-back live in the father card")
    _lvtxt = " ".join(b[1].lower() for b in
                      next(ex for ex in _MCV["exchanges"]
                           if ex["key"] == "leave")["beats"])
    check("nobody leaves" in _lvtxt,
          "mara: asked to come away, no one leaves")
    _wotxt = " ".join(b[1].lower() for b in
                      next(ex for ex in _MCV["exchanges"]
                           if ex["key"] == "way_out")["beats"])
    check("we can't" in _wotxt,
          "mara: asked the way out, there is none")
    # The withheld noun: she never names what she dug for. Every "he" in
    # her mouth stays undivided between her son and her god.
    _mara_mouth = " ".join(
        b[1].lower() for ex in _MCV["exchanges"] for b in ex["beats"]
        if b[0] == "npc")
    _mara_mouth += " " + " ".join(
        b[1].lower() for b in _MCV["greet"]["beats"])
    check(not _re.search(r"\b(son|baby|boy|child|children|pregnant)\b",
                         _mara_mouth),
          "mara: the withheld noun holds (her mouth never names the boy)")
    _all_beats = ([b[1] for ex in _MCV["exchanges"] for b in ex["beats"]
                   if b[0] in ("npc", "pi")]
                  + [b[1] for b in _MCV["greet"]["beats"]]
                  + [ex["q"] for ex in _MCV["exchanges"]])
    check(not any(("—" in t) or ("–" in t) or ("--" in t)
                  for t in _all_beats),
          "mara: no dashes anywhere in the confrontation")

    # The unsent letter (the letter beat's object) carries the ADMISSION
    # (NARRATIVE §6): the pregnancy Walter never knew of, the
    # son-for-a-daughter line; the door is never mentioned.
    from systems.items import ITEM_DEFS as _IDF
    _lt = _IDF["unsent_letter"]["desc"].lower()
    check("dad" in _lt and "a boy" in _lt and "came still" in _lt,
          "letter: the admission is in the letter")
    check("wait up" in _lt and "daughter" in _lt,
          "letter: a son the way he wanted a daughter")
    check("door" not in _lt,
          "letter: the door is never mentioned")
    check("never been this close" in _lt,
          "letter: her leaving line survives")
    check(not (("—" in _IDF["unsent_letter"]["desc"])
               or ("–" in _IDF["unsent_letter"]["desc"])
               or ("--" in _IDF["unsent_letter"]["desc"])),
          "letter: no dashes")

    gw = new_game()
    gw.player.inventory.add("pallid_mask", 1)
    gw.load_scene_now("well_bottom")
    _wtext = "".join(str(getattr(gw.dialog, "pages", "")))
    check(gw.save.flag("spread_counterweight"),
          "spread: the counterweight beat fires at the shaft floor with "
          "the Mask in hand")
    gw2 = new_game()
    gw2.player.inventory.add("pallid_mask", 1)
    gw2.save.set_flag("descent_sealed", True)
    gw2.load_scene_now("well_bottom")
    check(not gw2.save.flag("spread_counterweight"),
          "spread: the counterweight never fires after the seal")

    gh = new_game()
    gh.load_scene_now("shop")
    ready(gh)
    gh.save.set_flag("hettie_greeted", True)
    gh.save.set_flag("hettie_saw_photo", True)     # the PI showed Mara's photo
    from scenes.dialogue import hettie_dialogue as _hd
    _hshown = []
    _horig = gh.dialog.show

    def _hspy(pages, *a, **k):
        _hshown.extend([pages] if isinstance(pages, str) else list(pages))
        return _horig(pages, *a, **k)
    gh.dialog.show = _hspy

    class _HStub:
        pass
    _hd(gh, _HStub())
    check(any("smiling I minded" in p for p in _hshown),
          "hettie: the memory of the girl fires once shown Mara's photo")
    check(gh.player.inventory.has("receipt")
          and has_evidence(gh, "maras_receipt"),
          "hettie: the memory beat hands over the store tab (warm handover)")
    check(not any(("—" in p) or ("–" in p) or ("--" in p) for p in _hshown),
          "hettie: no dashes in the memory beat")

    # --- 24c. The soft lead (TODO #5): derived, oblique, never empty,
    # never dashed, and it climbs the milestone ladder.
    gl = new_game()
    _lead0 = gl._current_lead()
    check(isinstance(_lead0, str) and "Blaine girl" in _lead0,
          "lead: a fresh run points at asking the town")
    gl.save.set_arg("evidence", [{"name": c, "lines": [], "weight": 0.05}
                                 for c in "abc"])
    check("desk" in (gl._current_lead() or ""),
          "lead: three beats point back at the Lodge desk")
    gl.player.inventory.add("rite_envelope", 1)
    check("school" in (gl._current_lead() or ""),
          "lead: the Invitation points at the school")
    gl.save.set_flag("rite_performed", True)
    gl.player.inventory.add("pallid_mask", 1)
    _leadm = gl._current_lead() or ""
    check("carry" in _leadm,
          "lead: the Mask stage names the carried choice")
    gl.save.set_flag("descent_sealed", True)
    check("car" in (gl._current_lead() or ""),
          "lead: the SPREAD lock points at the car")
    for _st in (_lead0, _leadm):
        check(not (("—" in _st) or ("–" in _st) or ("--" in _st)),
              "lead: no dashes in the thread line")

    # --- 24d. The PI theory ladder (TODO #13): the notebook THINKS. The
    # working theory + timeline are first-person syntheses derived from WHICH
    # clues are held (any order); they revise as the case grows, never inflate
    # the evidence count, carry no dashes, keep the cosmology unnamed, and lean
    # toward SPREAD. The two wrong-space fold beats latch crossed_a_fold and
    # open the trap thread; the robes-as-lever read is the WRONG conclusion the
    # game never corrects (NARRATIVE invariant).
    def _dashed(t):
        return ("—" in t) or ("–" in t) or ("--" in t)

    def _theory(g):
        return " ".join(g._working_theory())

    def _timeline(g):
        return " ".join(g._case_timeline())

    def _nnames(g):
        return {e.get("name") for e in g.save.arg("notes", [])
                if isinstance(e, dict)}
    gt = new_game()
    check(gt._working_theory() == [],
          "theory: a fresh run has no theory yet (the job lives in the_case note)")
    check(gt._case_timeline() == [],
          "timeline: a fresh run has no chronology yet")
    check("get out" not in _theory(gt),
          "theory: no escape thread before a fold is crossed")
    # The notebook pins a surface only when it has content: nothing at the
    # start, the theory card the moment a clue lands.
    gpin = new_game()
    gpin.notebook_ui.save = gpin.save
    gpin.notebook_ui.game = gpin
    check("working_theory" not in {n for n, _ in gpin.notebook_ui._entries()},
          "notebook: a fresh run pins no theory card (just the job)")
    gpin.save.set_arg("evidence", [{"name": "maras_receipt"}])
    check("working_theory" in {n for n, _ in gpin.notebook_ui._entries()},
          "notebook: the theory card appears once a clue lands")
    gt.save.set_arg("evidence", [{"name": "maras_receipt"}])
    check("resident" in _theory(gt),
          "theory: the receipt reads her as a resident, not a drifter")
    gt.save.set_arg("evidence", [{"name": "maras_journal"},
                                 {"name": "maras_receipt"},
                                 {"name": "maras_record"}])
    check("came apart" in _theory(gt),
          "theory: record + journal read her breaking here")
    check("Booked one night" in _timeline(gt),
          "timeline: the booking slots into her chronology")
    check("robes" not in _theory(gt),
          "theory: no robes thread on clues alone, before he's met the cult")
    gt.save.set_flag("cult_talk_given", True)
    check("robes" in _theory(gt),
          "theory: meeting the cult (the grab) opens the robes-as-lever read")
    gt.save.set_arg("evidence", [{"name": "maras_dig"}])
    check("willing" in _theory(gt),
          "theory: the dig pivots her to willing, not taken")
    gt._note_fold_portal()
    check(gt.save.flag("crossed_a_fold") and "saw_the_door" in _nnames(gt),
          "fold: a visible pane latches crossed_a_fold and files the awe note")
    check("get out" in _theory(gt),
          "theory: crossing a fold opens the trap / escape thread")
    gl2 = new_game()
    gl2._note_fold_loop("cornfield_path")
    check("walked_in_circles" not in _nnames(gl2),
          "fold: one silent loop is not enough to notice")
    gl2._note_fold_loop("cornfield_path")
    check("walked_in_circles" in _nnames(gl2),
          "fold: the second silent loop is the tell")
    gt4 = new_game()
    gt4.save.set_arg("evidence", [{"name": "maras_room"}])
    check("Sam" not in _theory(gt4), "theory: no son thread without the bear")
    gt4.player.inventory.add("bear", 1)
    check("Sam" in _theory(gt4), "theory: bear + letter opens the son thread")
    gt4.player.inventory.add("pallid_mask", 1)
    check("carry it out" in _theory(gt4),
          "theory: the Mask leans the read toward carrying it out (SPREAD)")
    _all = _theory(gt4) + " " + _timeline(gt4)
    check(not _dashed(_theory(gt)) and not _dashed(_timeline(gt))
          and not _dashed(_all),
          "theory / timeline: no dashes in any produced line")
    check(("King" not in _all) and ("Carcosa" not in _all),
          "theory: the cosmology stays unnamed (sensation-only)")

    # --- 25. The placement pass (DESIGN.md §12): the gauntlet rooms
    # HAVE an enclosed hide, and EVERY declared hide in EVERY scene sits
    # on walkable ground (a spot inside a solid roots the player in a
    # wall and a sweeping searcher can never close to check range).
    from scenes import load_scene as _ld2, SCENE_BUILDERS as _SB2
    for _key in ("well_passage", "works_cistern", "works_sorting",
                 "works_scriptorium", "works_sign", "depths_antechamber",
                 "depths_procession", "depths_hall", "brimley"):
        check(len(_ld2(_key).hide_spots) >= 1,
              f"hides: {_key} has an enclosed hide")
    _bad_spots = []
    for _key in _SB2:
        try:
            _sc2 = _ld2(_key)
        except Exception:
            continue
        for hx, hy, _k in (getattr(_sc2, "hide_spots", None) or []):
            if _sc2.is_solid_at(hx, hy):
                _bad_spots.append((_key, hx, hy))
    check(not _bad_spots,
          f"hides: every declared spot in every scene sits on walkable "
          f"ground {_bad_spots or ''}")

    # --- 26. Floating NPC speech (2026-07 sound overhaul): a casual
    # talkable-NPC line reached through the interact path FLOATS over
    # the speaker's head and leaves the world running; narrator lines,
    # choices, and scripted (on_complete) beats stay in the MODAL box.
    gfs = new_game()
    gfs.load_scene_now("church", "default")
    for _ in range(20):
        gfs.state = "playing"
        gfs.step(1 / 30.0)
    _crane = next(n for n in gfs.scene.npcs
                  if getattr(n, "tag", "") == "preacher")
    gfs.player.x, gfs.player.y = _crane.x, _crane.y + 30
    gfs._speaking_npc = _crane
    _crane.interact(gfs)
    gfs._speaking_npc = None
    check(gfs.float_speech.active and not gfs.dialog.active,
          "float: an interact-path NPC line floats (not the modal box)")
    check(gfs.float_speech.speaker is _crane,
          "float: the caption tracks the speaker")
    _wf = (gfs.dialog.active or gfs.inv_ui.open or gfs.notebook_ui.open
           or gfs.text_input.active or gfs._flashback_phase is not None)
    check(not _wf, "float: the world is not frozen while a float is up")
    # A narrator line goes NON-MODAL too now -- the lower-third
    # narration caption (ui/narration.py), world still running.
    gfs.float_speech.active = False
    gfs._speaking_npc = _crane
    gfs.dialog.show(["A cold room."], speaker="", portrait="narrator")
    gfs._speaking_npc = None
    check(gfs.narration.active and not gfs.dialog.active,
          "narration: a narrator line runs as the lower-third caption")
    check(not (gfs.dialog.active or gfs.inv_ui.open),
          "narration: the world is not frozen while a caption is up")
    # E skims it: first press completes the reveal, further presses page
    # through, and the last one ends it.
    _consumed = gfs.narration.advance_from_input()
    check(_consumed, "narration: E is consumed by an active caption")
    gfs.narration.advance_from_input()
    check(not gfs.narration.active,
          "narration: paging past the last line ends the caption")
    # A scripted narrator beat WITH a completion callback keeps the
    # modal box (frozen world) -- those sequences depend on it.
    gfs.dialog.show(["A held beat."], speaker="", portrait="narrator",
                    on_complete=lambda: None)
    check(gfs.dialog.active and not gfs.narration.active,
          "narration: an on_complete narrator beat stays modal")
    gfs.dialog.active = False
    gfs.dialog.on_complete = None
    gfs._speaking_npc = _crane
    gfs.dialog.show_choice("Pick", ["a", "b"], lambda i: None,
                           speaker="Crane", portrait="preacher")
    gfs._speaking_npc = None
    check(gfs.dialog.active and gfs.dialog.choices is not None
          and not gfs.float_speech.active,
          "float: a choice stays modal")
    gfs.dialog.active = False
    gfs.dialog.show(["Scene voice."], speaker="Someone",
                    portrait="preacher")
    check(gfs.dialog.active and not gfs.float_speech.active,
          "float: a line outside the interact path stays modal")

    # --- 26b. the arrival road LOOPS south (silent same-scene fold) ---
    # Walking south past the loop line lands you back NORTH of the
    # crossing, still south of the render band -- so the idle King is
    # NEVER in view off the loop; he only shows walking north onto the
    # band (the maintainer's sightline rule).
    from constants import TILE as _T
    gr = new_game()
    gr.load_scene_now("arrival_road", "default")
    ready(gr)
    _tm = gr.scene._treadmill
    gr.player.x, gr.player.y = 7 * _T + 16, 74 * _T + 16
    gr.player.facing = (0, 1)               # striding SOUTH onto the line
    y_before = gr.player.y
    gr.step(1 / 30.0)
    check(gr.scene.key == "arrival_road" and gr.player.y < y_before - 300,
          "loop: walking south folds you back north of the crossing")
    check(gr.player.y >= _tm[1],
          "loop: the landing sits SOUTH of the band (no King in view)")
    gr.state = "playing"
    gr.step(1 / 30.0)
    check(gr._idle_king is None,
          "loop: the idle King is hidden after the loop")
    gr.player.y = _tm[1] - _T               # deliberately walk north onto it
    gr.step(1 / 30.0)
    check(gr._idle_king is not None,
          "loop: he shows again only once you walk north up the band")

    # --- 27. save-on-evidence + Continue (play-notes) ----------------
    # Evidence pickup is the ONLY writer of the disk slot now; Continue
    # reads it back and wakes at the scene the clue was found in, with a
    # COOLED visibility. The cot is a REST (heal + cool), not a save.
    import tempfile
    import shutil
    from scenes.dialogue import _evidence as _ev27
    _sd = tempfile.mkdtemp(prefix="th_save_")
    os.environ["THRESHOLD_SAVE_DIR"] = _sd
    try:
        gsl = new_game()
        check(gsl._title_menu_options() == ["New Game", "Quit"],
              "save: no slot, no Continue")
        gsl.save.set_flag("persist_probe", True)
        gsl.player.inventory.add("lumber_axe", 1)
        gsl.load_scene_now("barn", "default")
        gsl.visibility = 0.8
        _ev27(gsl, "maras_journal", ["a line"], show=False)   # a canonical clue
        check(os.path.isfile(gsl.save.disk_path()),
              "save: picking up evidence writes the disk slot")
        check(gsl.save.data.get("scene") == "barn",
              "save: the slot remembers the scene the clue was found in")
        check(abs(float(gsl.save.arg("visibility_at_sleep")) - 0.4) < 1e-9,
              "save: the reload visibility is cooled (halved)")
        check(gsl._title_menu_options()[0] == "Continue",
              "save: the title offers Continue once the slot exists")
        gsl.save.set_flag("post_save_probe", True)
        gsl.state = "title"                # any run end: death or quit
        check(gsl.save.load_disk(), "save: Continue reads the slot back")
        gsl._start_play()
        check(gsl.save.flag("persist_probe")
              and not gsl.save.flag("post_save_probe"),
              "save: continue restores the last clue, not the lost run")
        check(gsl.scene.key == "barn",
              "save: waking lands where the clue was found")
        check(gsl.player.inventory.has("lumber_axe"),
              "save: the inventory survives the round trip")
        check(abs(gsl.visibility - 0.4) < 1e-9,
              "save: the cooled attention survives the round trip")
        # The cot is now a REST, not a save: it heals + cools, no disk write.
        gsl.player.hp = 10
        gsl.visibility = 0.8
        _mtime = os.path.getmtime(gsl.save.disk_path())
        fire(gsl, "bedroom", "_cot_pos")
        check(gsl.player.hp == gsl.player.max_hp,
              "save: the cot rest restores hp")
        check(abs(gsl.visibility - 0.4) < 1e-9,
              "save: the cot rest cools the town's attention (halves it)")
        check(os.path.getmtime(gsl.save.disk_path()) == _mtime,
              "save: the cot no longer writes the disk slot")
    finally:
        os.environ.pop("THRESHOLD_SAVE_DIR", None)
        shutil.rmtree(_sd, ignore_errors=True)

    # --- 28. THE TALK: the first cult grab is a warning, not a capture ---
    gt2 = new_game()
    gt2.load_scene_now("brimley")
    ready(gt2)
    _tshown = []
    _torig = gt2.dialog.show

    def _tspy(pages, *a, **k):
        _tshown.extend([pages] if isinstance(pages, str) else list(pages))
        return _torig(pages, *a, **k)
    gt2.dialog.show = _tspy
    check(not gt2.save.flag("cult_talk_given"), "talk: fresh run, no talk yet")
    gt2._trigger_death("cultist")
    check(gt2._death_kind is None,
          "talk: the first grab does NOT capture (the freebie)")
    check(gt2.save.flag("cult_talk_given"), "talk: the freebie is spent")
    check(gt2.dialog.active, "talk: the warning is a modal beat")
    for _ in range(20):
        if not gt2.dialog.active:
            break
        gt2.dialog.advance()
    check(not gt2.dialog.active, "talk: the warning closes cleanly")
    check(gt2.player.invuln > 0,
          "talk: release grants a re-grab grace window")
    check(any(isinstance(e, dict) and e.get("name") == "the_talk"
              for e in gt2.save.arg("notes", [])),
          "talk: the PI files it as a NOTE")
    check(not has_evidence(gt2, "the_talk"),
          "talk: the note never inflates evidence")
    check(not any(("—" in s) or ("–" in s) or ("--" in s)
                  for s in _tshown),
          "talk: no dashes in the warning")
    _tblob = " ".join(_tshown).lower()
    check("hotel room" in _tblob and "run." in _tblob,
          "talk: the warning is the locked line (hotel room, then run)")
    check("midwestern welcome" in _tblob,
          "talk: the PI's reaction lands after the release")
    # After the Talk, the grab is TWO-TOUCH (play-notes): the first grab of an
    # encounter shoves the PI free, only the second is the capture.
    gt2._trigger_death("cultist")
    check(gt2._death_kind is None,
          "talk: after the Talk, the first grab SHOVES you free (two-touch)")
    check(gt2._cult_touch_count == 1,
          "talk: the shove registers one touch")
    gt2._trigger_death("cultist")
    check(gt2._death_kind == "cultist",
          "talk: the second grab is the CAPTURED card")

    # --- 28b. The calling-out: the staged confrontation at the Sign
    # Chamber (kneelers rise, one says her name, Mara comes to you).
    from constants import TILE as _T28
    gs2 = new_game()
    gs2.load_scene_now("works_sign")
    ready(gs2)
    _sc2 = gs2.scene
    check(all(getattr(k, "pose", None) == "kneel" for k in _sc2._kneelers)
          and getattr(_sc2._mara, "pose", None) == "kneel",
          "staging: the congregation and Mara start kneeling")
    check(all(not str(getattr(k, "tag", "")).startswith("cult_")
              for k in _sc2._kneelers + [_sc2._mara]),
          "staging: the rank carries no cult tag (no gaze, no chase)")
    gs2.state = "playing"
    # Row 6, centre aisle: inside the calling-out band (rows 2..7), a
    # step south of the kneeling rank.
    gs2.player.x, gs2.player.y = 6 * _T28 + 16, 6 * _T28 + 16
    for _ in range(1200):
        gs2.step(1 / 20.0)
        if gs2.dialog.active and gs2.dialog.choices is not None:
            break
    check(gs2.save.flag("mara_called"),
          "staging: entering the nave starts the calling-out")
    check(any(getattr(k, "pose", "kneel") is None for k in _sc2._kneelers),
          "staging: the kneelers rise")
    check(getattr(gs2, "_convo", None) is not None and gs2._convo.active
          and gs2.dialog.choices is not None,
          "staging: Mara comes to you and the ask menu opens")
    check(gs2.save.flag("hive_seen")
          and not has_evidence(gs2, "the_congregation"),
          "staging: the calling-out fires, but Mara is PROOF, not a filed beat")
    # Play the father card (the player's own ask) and let the talk run
    # its length: the slip, the stall, the lucid turn-back.
    _fidx = next(i for i, l in enumerate(gs2.dialog.choices)
                 if "father" in l.lower())
    gs2.dialog.choice_idx = _fidx
    gs2.dialog.advance()
    check(gs2.save.flag("mara_lucid"),
          "staging: the father card breaks her certainty (mara_lucid)")
    for _ in range(4000):
        gs2.step(1 / 20.0)
        if (getattr(gs2, "_mara_stage", None) is None
                and getattr(_sc2._mara, "pose", None) == "kneel"):
            break
    check(getattr(_sc2._mara, "pose", None) == "kneel"
          and all(getattr(k, "pose", None) == "kneel"
                  for k in _sc2._kneelers),
          "staging: lucidity changes nothing; the room folds back to the "
          "kneeling")
    check((_sc2._mara.x, _sc2._mara.y) == _sc2._mara_home,
          "staging: Mara returns to her place in the rank")
    # Her story's other end: a shot Mara kills the staging cleanly (no
    # crash, no soft-lock; #6 is forfeited with her and the gate still
    # opens on the other five beats).
    gsd = new_game()
    gsd.load_scene_now("works_sign")
    ready(gsd)
    gsd.scene._mara.alive = False
    gsd._mara_stage = {"t": 0.0, "step": 0, "sc": gsd.scene}
    gsd.scene.on_update_fn(gsd, gsd.scene, 0.05)
    check(getattr(gsd, "_mara_stage", None) is None,
          "staging: a dead Mara clears the calling-out (her story's other "
          "end)")

    # --- 28c. The bear + the name-beat (TODO #22b) ---
    from scenes.dialogue import (TOBY_CONVO as _TOBY_B,
                                 CANONICAL_EVIDENCE as _CE_B)
    from scenes.well import MARA_CONVO as _MARA_B
    from systems.items import effective_desc as _edesc
    import re as _re_b
    # The bear is OPTIONAL -- never a counted beat, so it can never gate.
    check("bear" not in _CE_B,
          "bear: optional -- never a counted evidence beat (never gates)")
    # Toby LENDS it, and only to the man he trusts: told what he saw
    # (toby_told) AND reassured (the holding-up promise). Not interrogable.
    gtb = new_game()
    gtb.load_scene_now("toby_house")
    ready(gtb)
    _toby = next(n for n in gtb.scene.npcs if n.name == "Toby")
    _toby.dialogue_fn(gtb, _toby)                      # cold: no lend
    check(not gtb.player.inventory.has("bear"),
          "bear: Toby never gives it up cold (trust is earned)")
    gtb.save.set_flag("toby_told", True)
    _toby.dialogue_fn(gtb, _toby)                      # told, not reassured
    check(not gtb.player.inventory.has("bear"),
          "bear: the witness alone does not earn the bear")
    gtb.save.set_flag("convo_toby_holding_up_asked", True)
    _toby.dialogue_fn(gtb, _toby)                      # trust earned -> lend
    check(gtb.player.inventory.has("bear")
          and gtb.save.flag("toby_lent_bear"),
          "bear: reassuring the kid earns the loan (he brings it out himself)")
    check(evidence_count(gtb) == 0
          and any(isinstance(e, dict) and e.get("name") == "the_bear"
                  for e in gtb.save.arg("notes", [])),
          "bear: the loan files a NOTE, never evidence")
    # It DETONATES once the letter is read (the tag's name + the stillborn son).
    _d0 = _edesc("bear", gtb.save)
    gtb.save.set_flag("evidence_maras_room", True)
    _d1 = _edesc("bear", gtb.save)
    check(_d0 != _d1 and "dead son" in _d1.lower(),
          "bear: reading the letter detonates the tender surface object")
    # The name-beat: bear-gated, ends the talk, changes her fate not at all.
    _nb = next(ex for ex in _MARA_B["exchanges"] if ex["key"] == "name")
    gnb = new_game()
    check(not _nb["avail"](gnb),
          "name: the name-beat is hidden without the bear")
    gnb.player.inventory.add("bear", 1)
    check(_nb["avail"](gnb) and _nb.get("ends") is True and _nb.get("once"),
          "name: the bear opens it, and saying the name ends the talk")
    _nb["on_ask"](gnb)
    check(gnb.save.flag("mara_named"),
          "name: the beat records that the PI reached for the name")
    # INVARIANT (NARRATIVE §4/§6): MARA never says the boy's name -- only the
    # PI and the tag do. Scan every line she speaks (greet + all exchanges).
    _mara_said = [t for _ex in _MARA_B["exchanges"]
                  for r, t in _ex["beats"] if r == "npc"]
    _mara_said += [t for r, t in _MARA_B["greet"]["beats"] if r == "npc"]
    check(not any(_re_b.search(r"\bsam(my|uel)?\b", t.lower())
                  for t in _mara_said),
          "name: INVARIANT -- Mara never says the boy's name (only the PI does)")
    check(_re_b.search(r"\bsam\b", _nb["q"].lower()) is not None,
          "name: the PI is the one who says it (the name-beat spoken line)")

    # --- 29. NPC jobs: a worker walks his stations (the JOBS layer) ---
    gj = new_game()
    gj.load_scene_now("brimley")
    ready(gj)
    _gar = next((n for n in gj.scene.npcs if n.name == "Garrick"), None)
    check(_gar is not None and _gar.movement == "worker"
          and len(getattr(_gar, "stations", [])) >= 2,
          "jobs: Garrick carries a personal station route")
    _visited = set()
    for _ in range(1500):                    # ~2.5 sim minutes
        _gar.update(0.1, gj.scene, gj.player)
        for _si, _st in enumerate(_gar.stations):
            if gj.scene.world_dist(_gar.x, _gar.y,
                                   _st["x"], _st["y"]) < 20.0:
                _visited.add(_si)
        if len(_visited) >= 2:
            break
    check(len(_visited) >= 2,
          "jobs: the worker walks between stations and dwells")
    check(_gar.movement == "worker",
          "jobs: the errand layer holds (his stations are reachable)")
    gj.load_scene_now("shop")
    ready(gj)
    _het = next((n for n in gj.scene.npcs if n.name == "Hettie"), None)
    check(_het is not None and _het.movement == "worker"
          and len(getattr(_het, "stations", [])) >= 3,
          "jobs: the store Hettie works her counter route")
    gj.load_scene_now("church")
    ready(gj)
    _rev = next((n for n in gj.scene.npcs
                 if getattr(n, "tag", "") == "preacher"), None)
    check(_rev is not None and _rev.movement == "worker",
          "jobs: Crane works the lectern route")

    # --- 30. The Preacher's end at the RIVER (2026-07 rework, NARRATIVE
    # §2/§4): the doom sends Crane out of his church; the body is found on
    # the Brimley riverbank, never on his own floor; the murder one-shots
    # key on FINDING it. Plus his knowledge stays a local's (rumor only).
    gpr = new_game()
    gpr.save.set_flag("preacher_doomed", True)
    gpr.load_scene_now("church")
    ready(gpr)
    check(not any(getattr(n, "tag", "") == "preacher"
                  for n in gpr.scene.npcs),
          "river: the doomed Crane has left his church")
    check(not any(getattr(n, "tag", "") == "preacher_body"
                  for n in gpr.scene.npcs),
          "river: no body on the church floor (it lies at the river)")
    check(gpr.save.flag("church_empty_seen")
          and not gpr.save.flag("preacher_body_seen"),
          "river: the emptied church never counts as finding him")
    gpr.load_scene_now("brimley")
    ready(gpr)
    _pb = next((n for n in gpr.scene.npcs
                if getattr(n, "tag", "") == "preacher_body"), None)
    check(_pb is not None, "river: the remains lie on the brimley bank")
    _bx, _by = gpr.scene._preacher_bank_pos
    gpr.player.x, gpr.player.y = _bx + 60, _by
    gpr.scene.update(1 / 30.0, gpr)
    check(gpr.save.flag("preacher_body_seen"),
          "river: walking up on the body counts as finding it")
    if _pb is not None:
        _pb.dialogue_fn(gpr, _pb)
        check(gpr.player.inventory.has("cross")
              and not has_evidence(gpr, "the_preacher")
              and any(isinstance(e, dict) and e.get("name") == "the_preacher"
                      for e in gpr.save.arg("notes", [])),
              "river: the cross lands + the death files a NOTE, never evidence")
    _gnb = new_game()
    _gnb.load_scene_now("brimley")
    check(not any(getattr(n, "tag", "") == "preacher_body"
                  for n in _gnb.scene.npcs),
          "river: no remains before the doom")
    # Hettie's one-shot keys on the FOUND body, never the mere doom.
    from scenes.dialogue import hettie_dialogue as _hd
    ghp = new_game()
    ghp.save.set_flag("preacher_doomed", True)
    ghp.save.set_flag("hettie_greeted", True)
    _hshown = []
    ghp.dialog.show = lambda p, **k: _hshown.extend(
        p if isinstance(p, list) else [p])
    _hn = type("N", (), {"name": "Hettie", "x": 0, "y": 0})()
    _hd(ghp, _hn)
    check(not any("preacher" in s.lower() for s in _hshown),
          "river: Hettie never mourns a man still standing")
    ghp.save.set_flag("preacher_body_seen", True)
    del _hshown[:]
    _hd(ghp, _hn)
    check(any("preacher" in s.lower() for s in _hshown),
          "river: Hettie's one-shot lands once the body is found")
    # Crane's knowledge stays a LOCAL's: never the underground, only the
    # rumor the boy told him (NARRATIVE §4).
    from scenes.dialogue import CRANE_CONVO as _CCV
    _fl = next(e for e in _CCV["exchanges"] if e.get("key") == "flock")
    _fltxt = " ".join(b[1] for b in _fl["beats"]
                      if b[0] in ("npc", "pi")).lower()
    check("under the ground" not in _fltxt and "underground" not in _fltxt,
          "river: Crane never speaks of the underground")
    check("rumor" in _fltxt and "river" in _fltxt and "toby" in _fltxt,
          "river: Crane carries only the boy's river rumor")

    # --- 31. The Mask temptation FIRES (the 2026-07 audit found it dead:
    # an on_complete parked on an inactive modal). Lifting the Mask must
    # end with the descent_mask NOTE in the case book (NARRATIVE §8, the
    # "permission to leave" beat).
    gmt = new_game()
    gmt.load_scene_now("works_sign")
    ready(gmt)
    _msx, _msy = gmt.scene._sign_pos
    gmt.player.x, gmt.player.y = _msx, _msy + 20
    gmt.scene.on_interact_fn(gmt)
    if gmt.dialog.choices:
        gmt.dialog.choice_idx = 0
        gmt.dialog.advance()                  # "Lift the mask."
    for _ in range(6000):
        if gmt.narration.active:
            gmt.narration.update(0.1)
        elif gmt.dialog.active:
            gmt.dialog.advance()
        else:
            break
    check(gmt.player.inventory.has("pallid_mask"),
          "tempt: the mask is lifted")
    check(any(isinstance(n, dict) and n.get("name") == "descent_mask"
              for n in gmt.save.arg("notes", [])),
          "tempt: the permission-to-leave beat fires (descent_mask note)")

    # --- 32. DEAD LOCALS STAY DEAD (2026-07 ruling; NARRATIVE §5) --------
    # A killed local is ledgered (save arg dead_locals) and the body is
    # laid back down where it fell on every re-entry; New Game clears it.
    gdl = new_game()
    gdl.load_scene_now("brimley")
    ready(gdl)
    pell = next((n for n in gdl.scene.npcs
                 if getattr(n, "name", "") == "Old Pell"), None)
    check(pell is not None, "dead-locals: Old Pell stands in brimley")
    if pell is not None:
        rx, ry = pell.x, pell.y
        pell.alive = False
        if gdl._kill_npc(pell):
            gdl._make_corpse(pell)
        check(bool(gdl.save.arg("dead_locals")),
              "dead-locals: the kill is written to the ledger")
        gdl.load_scene_now("shop")
        gdl.load_scene_now("brimley")
        ready(gdl)
        back = [n for n in gdl.scene.npcs
                if getattr(n, "name", "") == "Old Pell"]
        check(back and all(getattr(n, "_is_corpse", False)
                           and not getattr(n, "alive", True) for n in back),
              "dead-locals: the body persists across scene loads")
        check(back and abs(back[0].x - rx) < 1 and abs(back[0].y - ry) < 1,
              "dead-locals: the body lies where it fell")
    # The office interplay: a shot Vane never stands back up hollow; his
    # body holds the office at stage 3 instead of the sheriff_hunt spawn.
    gdl.load_scene_now("sheriff_office")
    ready(gdl)
    sher = next((n for n in gdl.scene.npcs
                 if getattr(n, "name", "") == "Sheriff"), None)
    check(sher is not None, "dead-locals: the Sheriff stands in his office")
    if sher is not None:
        sher.alive = False
        if gdl._kill_npc(sher):
            gdl._make_corpse(sher)
        gdl.save.set_arg("evidence",
                         [{"name": f"dl_t{i}", "content": "x"}
                          for i in range(3)])
        gdl.load_scene_now("brimley")
        gdl.load_scene_now("sheriff_office")
        ready(gdl)
        check(not any(getattr(n, "tag", "") == "sheriff_hunt"
                      for n in gdl.scene.npcs),
              "dead-locals: a dead Vane never rises as the hollow lawman")
        check(any(getattr(n, "name", "") == "Sheriff"
                  and getattr(n, "_is_corpse", False)
                  for n in gdl.scene.npcs),
              "dead-locals: Vane's body holds the stage-3 office")
    gdl.save.new()
    check(not gdl.save.arg("dead_locals"),
          "dead-locals: New Game clears the ledger")

    # --- 33. THE NAME STAYS OFF THE PAGE (Chambers, never quoted) --------
    # "Carcosa" / "the King in Yellow" / "the Yellow King" never appear in
    # a player-facing string. AST sweep of every string literal outside
    # docstrings (dev docstrings/comments may still use the names); the
    # SEAL ending's black stars + twin suns are the one deliberate,
    # UNNAMED reference (NARRATIVE §5).
    import ast as _ast
    _BAN = ("Carcosa", "King in Yellow", "Yellow King")
    _name_hits = []
    for _dirpath, _dirs, _files in os.walk(ROOT):
        _dirs[:] = [d for d in _dirs
                    if d not in ("__pycache__", ".git", "tools", "tests")]
        for _fn in _files:
            if not _fn.endswith(".py"):
                continue
            _fp = os.path.join(_dirpath, _fn)
            try:
                with open(_fp, encoding="utf-8") as _fh:
                    _tree = _ast.parse(_fh.read())
            except (SyntaxError, OSError):
                continue
            _docids = set()
            for _node in _ast.walk(_tree):
                if isinstance(_node, (_ast.Module, _ast.ClassDef,
                                      _ast.FunctionDef,
                                      _ast.AsyncFunctionDef)):
                    _body = getattr(_node, "body", [])
                    if (_body and isinstance(_body[0], _ast.Expr)
                            and isinstance(_body[0].value, _ast.Constant)
                            and isinstance(_body[0].value.value, str)):
                        _docids.add(id(_body[0].value))
            for _node in _ast.walk(_tree):
                if (isinstance(_node, _ast.Constant)
                        and isinstance(_node.value, str)
                        and id(_node) not in _docids
                        and any(_tok in _node.value for _tok in _BAN)):
                    _rel = os.path.relpath(_fp, ROOT)
                    _name_hits.append(f"{_rel}:{_node.lineno}")
    check(not _name_hits,
          "name ban: Carcosa / the King in Yellow never surface in a "
          "string literal" + (": " + ", ".join(_name_hits[:5])
                              if _name_hits else ""))

    print()
    if FAILS:
        print(f"{len(FAILS)} flow failure(s).")
        sys.exit(1)
    print("All flow checks passed -- the critical path is completable.")


if __name__ == "__main__":
    main()
