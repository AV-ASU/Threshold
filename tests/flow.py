"""End-to-end flow harness for THRESHOLD's critical path.

Where smoke.py only *builds* scenes, this drives a full run headlessly and
asserts the spine is COMPLETABLE with no crash or soft-lock:

  3 evidence -> Sable hands over the Invitation -> the school rite
  (incense + the chalk door) -> the grove's descent fold -> take the
  Playscript -> the Sign Chamber (Mara rises; take the Pallid Mask) ->
  fork at the Deep Stair (the descent seals) -> cross the Depths ->
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
    # The gate and charge key on the EVIDENCE COUNT (the six canonical
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

    # (b) At 3 evidence: the handoff fires once, with the PI's note.
    for i in range(3):
        g.save.arg("evidence", []).append(
            {"name": f"_act1_{i}", "lines": ["x"]})
    ready(g)
    clerk_dialogue(g, None)
    check(g.player.inventory.has("rite_envelope"),
          "sable: at 3 evidence he hands over the Invitation")
    check(any(isinstance(e, dict) and e.get("name") == "the_invitation"
              for e in g.save.arg("notes", [])),
          "sable: the handoff logs the PI's NOTE (never evidence)")
    check(len(g.save.arg("evidence", [])) == 3,
          "sable: the handoff does not inflate the evidence count")
    ready(g)
    _notes_n = sum(1 for e in g.save.arg("notes", [])
                   if isinstance(e, dict)
                   and e.get("name") == "the_invitation")
    clerk_dialogue(g, None)
    check(_notes_n == 1 and sum(
              1 for e in g.save.arg("notes", [])
              if isinstance(e, dict)
              and e.get("name") == "the_invitation") == 1,
          "sable: the handoff fires exactly once (no duplicate note)")

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
    check(not g.scene.exit_gate_fn(g, "G")
          and not g.scene.exit_gate_fn(g, "M"),
          "rite: the circle seals the surface exits behind you")
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
    check(g2.scene.exit_gate_fn(g2, "G"),
          "egress: the circle releases you once the way down is dead")

    # --- 1b. The Ledger: the locked cellar + the key behind the house ---
    # CANON (2026-07 rework): you SIGN the desk register on arrival; the
    # desk re-read is only a LEAD (a clean, new book). The Ledger itself
    # is the boxed old registers in the cellar, behind the padlocked
    # kitchen hatch; the cellar key hangs on a nail behind the house.
    gl = new_game()
    gl.load_scene_now("house")
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
    gl.load_scene_now("our_house_area")
    check(any(it["key"] == "cellar_key" for it in gl.scene.items),
          "ledger: the cellar key hangs behind the house")
    gl.player.inventory.add("cellar_key", 1)   # (walk-over pickup in play)
    gl.save.set_flag("cellar_key_taken", True)
    gl.load_scene_now("house")
    check(gl.scene.exit_gate_fn(gl, "L")
          and gl.save.flag("cellar_unlocked"),
          "ledger: the carried key turns the padlock (one-time unlock)")
    gl.load_scene_now("basement")
    ready(gl)
    gl.player.x, gl.player.y = gl.scene._ledger_pos
    gl.scene.on_interact_fn(gl)
    check(has_evidence(gl, "the_ledger"),
          "ledger: the old registers in the cellar fire the_ledger")
    # A fresh save's cellar is key-gated and panel-free.
    gcellar = new_game()
    gcellar.load_scene_now("basement")
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

    # --- 3. The Pallid Mask (Sign Chamber, evidence #5) -- LIFT the mask ---
    fire(g, "works_sign", "_sign_pos")
    g.dialog.choice_idx = 0
    g.dialog.advance()                          # "Lift the mask."
    check(g.player.inventory.has("pallid_mask"),
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

    # --- 4. The Deepest Face: powder + the blast (the dig never finished;
    # the cult's testimony left a few feet of earth; the stair is CUT) ---
    fire(g, "the_sump", "_powder_pos")
    check(g.player.inventory.has("powder"),
          "sump: the diggers' powder store arms the blast")
    # The investigator's discipline: no Mask, no fuse (sweep first).
    gb = new_game()
    gb.player.inventory.add("powder", 1)
    gb.load_scene_now("works_deepstair")
    ready(gb)
    gb.player.x, gb.player.y = gb.scene._gate_pos
    gb.scene.on_interact_fn(gb)
    check(not gb.save.flag("blast_laid"),
          "face: without the Mask the charge stays unlit (sweep first)")
    # The real run: Mask + powder, two-press, light it.
    g.load_scene_now("works_deepstair")
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
    # CANON (NARRATIVE §7): the Mask is NOT consumed at the face -- you
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
    # FLASH (two flickers, ~0.5s, no swarm -- the half-dismissed memory
    # surfacing); the FULL wordless dream (door + accelerating mask
    # swarm) plays at the GROVE RITE. Same dream, two weights.
    from ui.cutscenes import (FLASHBACK_DUR as _FBD,
                              FLASHBACK_FLASH_DUR as _FBF)
    check(0.0 < _FBF <= 1.0 < _FBD,
          "flashback: the journal flash is brief; the rite dream is long")
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
    # The keystone (the Mask) carried down from the Deep Stair is spent HERE,
    # at the door (§7 rework, Mask-only). g still holds it (stair did not spend).
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
    check(any(k in jtext for k in ("you go down", "below the town",
                                   "digging down")),
          "barn: Mara's journal motivates the descent (points down/below)")
    check("learned my name" in jtext,
          "barn: the journal log carries her ache (grief, page 1)")
    ge.load_scene_now("works_sign")                    # the_congregation (#6)
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
        # CANON (NARRATIVE §2, §14 rework): the witness does two jobs --
        # it poses the descent question (Mara AND the others went down the
        # well, which can no longer be followed) and it SEEDS THE SCHOOL
        # (the commune the Invitation names). Never the corn (the old
        # wrong reading).
        _kid_text = " ".join(_kid_lines).lower()
        check("well" in _kid_text and "down" in _kid_text,
              "kid: the witness still points down the well (the history)")
        check("school" in _kid_text,
              "kid: the witness seeds the SCHOOL (the route the rite opens)")
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
    _yard = _ld13("our_house_area")
    check(_yard.exits.get("a", (None,))[0] == "arrival_road",
          "geo: the lodge yard's west exit lands on the arrival road")
    _road = _ld13("arrival_road")
    check(_road.exits.get("a", (None,))[0] == "country_lane"
          and _road.exits.get("e", (None,))[0] == "our_house_area",
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

    # --- 13c. Reading Mara's journal in the inventory fires the dream ---
    # The journal is a paged, readable item: opening it shows page 1, and
    # turning past the LAST leaf (the third Enter) sets flashback_pending.
    # Lock that the three-read count drives the door-dream, since the
    # mechanic is the only in-game trigger for the §1b cutscene.
    from systems.items import MARA_JOURNAL_PAGES, journal_page as _jpage
    gj = new_game()
    gj.player.inventory.add("mom_notebook", 1)
    gj.inv_ui.open = True
    gj.inv_ui.tab = 1                                 # Notes tab
    _fk = [k for _, k, _ in gj.inv_ui._filtered_items(gj.player.inventory)]
    gj.inv_ui.cursor = _fk.index("mom_notebook")
    check(_jpage(gj.save)[1] == 0,
          "journal: opens on page 1 (its words are visible immediately)")
    gj.inv_ui.use_selected(gj.player)                 # turn 1 -> page 2
    gj.inv_ui.use_selected(gj.player)                 # turn 2 -> page 3
    check(_jpage(gj.save)[1] == len(MARA_JOURNAL_PAGES) - 1
          and not gj.save.flag("flashback_pending"),
          "journal: reading short of the last leaf does NOT fire the dream")
    gj.inv_ui.use_selected(gj.player)                 # turn past the last leaf
    check(gj.save.flag("flashback_pending"),
          "journal: turning past the last leaf fires the door-dream")
    check(not gj.inv_ui.open,
          "journal: the inventory closes as the dream takes over")

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
    # 1st [E] at the desk TAKES the gun: sprite removed, pistol equipped
    gsr.save.set_flag("wake_up", True)
    gsr.player.x, gsr.player.y = dnx, dny
    gsr.try_interact()
    check(gsr.player.inventory.has("pistol") and not _gun_on_desk(gsr)
          and gsr.player.inventory.equipped.get("weapon") == "pistol",
          "startroom: [E] takes the revolver off the desk (sprite -> inventory)")
    # 2nd [E] READS the notes (does not hide)
    gsr.player.x, gsr.player.y = dnx, dny
    gsr.player.hidden = None
    gsr.dialog.active = False
    gsr.try_interact()
    check(gsr.player.hidden is None and gsr.save.flag("read_journal"),
          "startroom: a second [E] READS the notes (does not hide)")
    # the gun stays gone across a scene reload
    gsr.load_scene_now("bedroom", "from_house")
    check(not _gun_on_desk(gsr),
          "startroom: the taken revolver does not reappear on re-entry")

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
    # confusion), not a dry description. Read from the cellar registers
    # (2026-07: behind the padlocked hatch).
    gl2 = new_game()
    gl2.player.inventory.add("cellar_key", 1)
    gl2.load_scene_now("basement")
    ready(gl2)
    gl2.player.x, gl2.player.y = gl2.scene._ledger_pos
    gl2.scene.on_interact_fn(gl2)         # read the old registers
    _lt = " ".join(l for e in gl2.save.arg("evidence", [])
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

    # --- 17c. The investigation ASK verb (pilot: Mr. Sable, TODO #1) -----
    # After his two scripted intro visits, E opens a modal topic menu whose
    # answer floats over the desk. Guard the wiring: the third visit opens
    # the choice; the menu lists every topic plus a back-out; each topic
    # answers at both evidence tiers; and the colder tier tracks knowing.
    from scenes.dialogue import _SABLE_TOPICS, _sable_girl, _sable_well
    ga = new_game()
    ga.save.set_arg("clerk_count", 2)          # past intro + register nudge
    ga.dialog.active = False
    ga.dialog.choices = None
    clerk_dialogue(ga, None)
    check(ga.dialog.choices is not None,
          "ask: Sable's third visit opens the investigative topic menu")
    check(ga.dialog.choices is not None
          and len(ga.dialog.choices) == len(_SABLE_TOPICS) + 1,
          "ask: the menu lists every topic plus a back-out")
    for _lbl, _res in _SABLE_TOPICS:
        ga.save.set_arg("evidence", [])
        _lo = _res(ga)
        for _i in range(3):
            ga.save.arg("evidence", []).append({"name": f"_ask{_i}",
                                                "lines": ["x"]})
        _hi = _res(ga)
        check(bool(_lo) and bool(_hi),
              f"ask: '{_lbl}' answers at low and high evidence")
        check(_lo != _hi,
              f"ask: '{_lbl}' turns colder as the PI learns more")
    # Canon anchors: the girl reply names Blaine; the colder well reply
    # knows the guests went down and did not return (never a confessed
    # plot, just hospitality).
    ga.save.set_arg("evidence", [])
    check(any("Blaine" in p for p in _sable_girl(ga)),
          "ask: the girl topic names the Blaine girl")
    for _i in range(3):
        ga.save.arg("evidence", []).append({"name": f"_w{_i}", "lines": ["x"]})
    check(any("down" in p for p in _sable_well(ga)),
          "ask: the colder well reply knows the guests went down")

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
    gp.save.set_arg("shop_count", 1)            # she has met you once
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

    # (a2) The calendar sweep (GAME_CHANGES §13): the seal is mid-January
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
    gv.save.set_arg("fisher_count", 6)          # well past the old slot
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

    # (c) Mrs. Calder's place-setting thread pays off when she converts
    # (stage 2): the extra place is cleared, her converted voice carries
    # the beat, and it lands as a case NOTE (never evidence).
    g0 = new_game()
    g0.load_scene_now("brimley")
    check(sum(1 for d in g0.scene.decorations
              if getattr(d, "kind", "") == "place_setting") == 2,
          "calder: both settings stand before she turns")
    gc = new_game()
    gc.save.set_arg("evidence", ["ev0", "ev1"])     # stage 2
    gc.load_scene_now("brimley")
    _cal = next((nn for nn in gc.scene.npcs
                 if getattr(nn, "name", "") == "Mrs. Calder"), None)
    check(_cal is not None and getattr(_cal, "tag", "") == "cult_convert",
          "calder: converted at stage 2 (INFEST_CONVERT)")
    check(sum(1 for d in gc.scene.decorations
              if getattr(d, "kind", "") == "place_setting") == 1,
          "calder: the extra place is cleared once she joins")
    if _cal:
        _ev_before = evidence_count(gc)
        _cal.dialogue_fn(gc, _cal)
        _notes = gc.save.arg("notes", [])
        check(any(isinstance(e, dict) and e.get("name") == "calder_table"
                  for e in _notes) and evidence_count(gc) == _ev_before,
              "calder: stopped-waiting lands as a NOTE, never evidence")

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
    # Each ambient local carries ONE pre-mutation state beat (a one-shot,
    # gated on what the PI has learned) before falling back to their
    # ambient loop; the procession's candle beat lands as a NOTE. None of
    # it may ever inflate the evidence count (the six canonical beats are
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
        _ga.dialogue_fn(gb, _ga)
        check(any("gone quiet" in p for p in shown),
              "react: Garrick clocks the pulpit going silent (murder beat)")
        ready(gb)
        _ga.dialogue_fn(gb, _ga)
        check(not any("gone quiet" in p for p in shown),
              "react: the Garrick beat is one-shot; ambient loop resumes")
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
        check(len(gm.dialog.pages) == 4,
              "mara: her four-line exchange is the ACTIVE dialog (evidence "
              "one-liner no longer clobbers it)")
        check(evidence_count(gm) == _evm + 1,
              "mara: evidence #6 still files immediately")
        if gm.dialog.on_complete:
            gm.dialog.on_complete()
        _mj = " ".join(_mshown).lower()
        check("arithmetic" in _mj,
              "lure: the dream+case+Mara collision fires after her lines")
        check(not any(w in _mj for w in ("marked", "lure", "bait",
                                         "the king", "dimension")),
              "lure: the collision beat holds the fence")
        check(not any(("—" in p) or ("–" in p) or ("--" in p)
                      for p in _mshown),
              "lure: no dashes in the beat")
    else:
        check(False, "mara: present at the Sign Chamber")

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
    gh.save.set_arg("shop_count", 1)
    gh.player.inventory.add("mom_notebook", 1)
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
          "hettie: the memory of the girl fires once the journal is carried")
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

    # --- 25. The placement pass (STEALTH_REWORK §6): the gauntlet rooms
    # HAVE an enclosed hide, and EVERY declared hide in EVERY scene sits
    # on walkable ground (a spot inside a solid roots the player in a
    # wall and a sweeping searcher can never close to check range).
    from scenes import load_scene as _ld2, SCENE_BUILDERS as _SB2
    for _key in ("well_passage", "works_vats", "works_sorting",
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
    # choices, infested portraits, and scripted (on_complete) beats
    # stay in the MODAL box.
    gfs = new_game()
    gfs.load_scene_now("old_man_house", "default")
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

    # --- 27. the cot's disk save + Continue (the typewriter rule) -----
    # Sleeping at the spare-room cot is the ONLY writer of the disk
    # slot; Continue reads it back and wakes at the cot; anything done
    # after the sleep is the stake a death or a quit loses.
    import tempfile
    import shutil
    _sd = tempfile.mkdtemp(prefix="th_save_")
    os.environ["THRESHOLD_SAVE_DIR"] = _sd
    try:
        gsl = new_game()
        check(gsl._title_menu_options() == ["New Game", "Quit"],
              "save: no slot, no Continue")
        gsl.save.set_flag("persist_probe", True)
        gsl.player.inventory.add("lumber_axe", 1)
        gsl.visibility = 0.6
        fire(gsl, "bedroom", "_cot_pos")
        check(os.path.isfile(gsl.save.disk_path()),
              "save: sleeping at the cot writes the disk slot")
        check(abs(gsl.visibility - 0.3) < 1e-9,
              "save: sleep cools the town's attention (visibility halves)")
        check(gsl._title_menu_options()[0] == "Continue",
              "save: the title offers Continue once the slot exists")
        gsl.save.set_flag("post_sleep_probe", True)
        gsl.state = "title"                # any run end: death or quit
        check(gsl.save.load_disk(), "save: Continue reads the slot back")
        gsl._start_play()
        check(gsl.save.flag("persist_probe")
              and not gsl.save.flag("post_sleep_probe"),
              "save: continue restores the last sleep, not the lost run")
        check(gsl.scene.key == "bedroom", "save: waking lands at the cot")
        check(gsl.player.inventory.has("lumber_axe"),
              "save: the inventory survives the round trip")
        check(abs(gsl.visibility - 0.3) < 1e-9,
              "save: the cooled attention survives the round trip")
        check(gsl.player.hp == gsl.player.max_hp,
              "save: sleep rests the PI (hp restored)")
        # A pre-rename slot (the keystone was keyed "sigil_rubbing"
        # until 2026-07) must migrate on read: the item becomes
        # pallid_mask, the flag sign_rubbing_taken becomes
        # pallid_mask_taken.
        import json as _json
        with open(gsl.save.disk_path(), encoding="utf-8") as f:
            _legacy = _json.load(f)
        _legacy["inventory"]["items"].append(["sigil_rubbing", 1])
        _legacy["flags"]["sign_rubbing_taken"] = True
        with open(gsl.save.disk_path(), "w", encoding="utf-8") as f:
            _json.dump(_legacy, f)
        check(gsl.save.load_disk(), "save: a legacy slot still reads")
        gsl._start_play()
        check(gsl.player.inventory.has("pallid_mask"),
              "save: a legacy sigil_rubbing migrates to pallid_mask")
        check(gsl.save.flag("pallid_mask_taken")
              and not gsl.save.flag("sign_rubbing_taken"),
              "save: the legacy taken-flag migrates with it")
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
    for _ in range(400):
        gs2.step(1 / 20.0)
        if gs2.dialog.active:
            break
    check(gs2.save.flag("mara_called"),
          "staging: entering the nave starts the calling-out")
    check(any(getattr(k, "pose", "kneel") is None for k in _sc2._kneelers),
          "staging: the kneelers rise")
    check(gs2.dialog.active and len(gs2.dialog.pages) == 4,
          "staging: Mara comes to you and her exchange fires unprompted")
    check(gs2.save.flag("hive_seen")
          and has_evidence(gs2, "the_congregation"),
          "staging: the confrontation lands evidence #6")
    for _ in range(20):
        if not gs2.dialog.active:
            break
        gs2.dialog.advance()
    for _ in range(400):
        gs2.step(1 / 20.0)
        if (getattr(gs2, "_mara_stage", None) is None
                and getattr(_sc2._mara, "pose", None) == "kneel"):
            break
    check(getattr(_sc2._mara, "pose", None) == "kneel"
          and all(getattr(k, "pose", None) == "kneel"
                  for k in _sc2._kneelers),
          "staging: the room folds back to the kneeling")
    check((_sc2._mara.x, _sc2._mara.y) == _sc2._mara_home,
          "staging: Mara returns to her place in the rank")

    # --- 29. NPC jobs: a worker walks his stations (GAME_CHANGES §19) ---
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
    gj.load_scene_now("old_man_house")
    ready(gj)
    _rev = next((n for n in gj.scene.npcs
                 if getattr(n, "tag", "") == "preacher"), None)
    check(_rev is not None and _rev.movement == "worker",
          "jobs: Crane works the lectern route")

    print()
    if FAILS:
        print(f"{len(FAILS)} flow failure(s).")
        sys.exit(1)
    print("All flow checks passed -- the critical path is completable.")


if __name__ == "__main__":
    main()
