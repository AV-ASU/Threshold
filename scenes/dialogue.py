"""All NPC dialogue functions.

The spoken lines are final, lore-bearing copy: each NPC reacts to the
case (the Blaine girl, the well, the cult) and many escalate with the
visibility tier via `escalate`. Evidence beats are surfaced through
`_evidence`; only the six in `CANONICAL_EVIDENCE` count toward the
King-gate and the visibility floor.
"""


# The SIX canonical evidence beats (NARRATIVE.md §4): ONLY these count toward
# the King-gate (3 = armed) and the visibility floor. Each name's value is the
# floor it adds -- surface finds light, the deep truths heavy; all six sum to
# the cap. Every other `_evidence(...)` call is now just flavor narration.
CANONICAL_EVIDENCE = {
    "maras_room":       0.10,
    "maras_journal":    0.12,
    "the_ledger":       0.10,
    "the_preacher":     0.16,
    "the_sign":         0.18,
    "the_congregation": 0.24,
}


def _evidence(game, name, content, weight=None):
    """Surface a one-shot narrator line. If `name` is one of the six CANONICAL
    beats it is ALSO logged as evidence -- counting toward the King-gate and
    raising the visibility FLOOR by its canonical weight (the "knowing dooms
    you" engine), and firing the notebook-scribble toast. Any other name is
    just flavor narration. Gated by a per-name flag so a beat never re-fires.

    Signature preserved for callers; `weight` is accepted but ignored --
    canonical weights above are authoritative."""
    if game is None or game.save is None:
        return
    flag = f"evidence_{name}"
    if game.save.flag(flag):
        return
    game.save.set_flag(flag, True)
    lines = content.split("\n") if isinstance(content, str) else list(content)
    if name in CANONICAL_EVIDENCE:
        log = game.save.arg("evidence", [])
        if isinstance(log, list) and not any(
                isinstance(e, dict) and e.get("name") == name for e in log):
            log.append({"name": name, "lines": list(lines),
                        "weight": CANONICAL_EVIDENCE[name]})
            game.save.set_arg("evidence", log)
            if hasattr(game, "_flash_notebook"):
                game._flash_notebook()    # corner scribble: you wrote it down
    game.dialog.show(lines,
                     speaker="", voice="blip_soft",
                     portrait="narrator")


def escalate(game, low, mid, high):
    """Pick a page-list for an NPC dialog based on Pursuer proximity.

    Signature and tiering preserved; the three tiers are now bland.
    """
    from systems.threat import (proximity_tier,
                                 PROX_TIER_LOW, PROX_TIER_MID)
    p = getattr(game, "visibility", 0.0)
    tier = proximity_tier(p)
    if tier == PROX_TIER_LOW:
        return low
    if tier == PROX_TIER_MID:
        return mid
    return high


def _cult_tell(game, npc_key):
    """No-op kept for signature compatibility. (Formerly surfaced a
    one-shot sensory notice; the story text has been removed.)"""
    return


# ---- The Preacher: Reverend Asa Crane ----

def preacher_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "preacher")
    count = save.arg("old_count", 0) + 1
    save.set_arg("old_count", count)
    if count == 1:
        game.dialog.show([
            "Another new face. That's all that comes to Brimley anymore, "
            "strangers off the highway, more every season. And not one of "
            "them leaves.",
            "I don't trust it. They arrive too easy, like something held "
            "the door. Then they go quiet, drift out to the corn, and they "
            "don't come back.",
            "A young woman came through last month. Bright thing, full of "
            "questions, like you. She's one of them now, whatever they "
            "are. You looking for her?",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")
    elif count == 2:
        # The hubris that gets him killed. After this he's marked: the
        # church swaps him for his remains on the next entry (evidence #4).
        game.dialog.show([
            "You came back. Good.",
            "It isn't the corn. The mouth is under the well. The well "
            "is in the Clerk's yard. I name them from my pulpit.",
            "The sheriff comes to hear me say it. He stays for the "
            "whole sermon. He's never taken communion.",
            "Let them come for an old man. I've buried better than "
            "whatever it is they kneel to.",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")
        save.set_flag("preacher_doomed", True)
    else:
        game.dialog.show([
            "I've said my piece. Go on now, and watch the road.",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")


# ---- The Kid: Toby Tisdale ----

def tisdale_boy_dialogue(game, npc):
    """Toby Tisdale -- innocent witness (NARRATIVE §2). He saw Mara AND the
    other cultists go down into the well, in the procession, before the rite
    -- so his account is the player's clue to descend the well. What he gives
    you is what he tells you (no inventory item -- the old keepsake object was
    purged). Children notice what adults pretend not to."""
    save = game.save
    inv = game.player.inventory
    # The witness beat: first real conversation, he tells you what he saw.
    if not save.flag("kid_witnessed"):
        save.set_flag("kid_witnessed", True)
        game.dialog.show([
            "You're looking for the lady from the lodge.",
            "She went with the others. A whole line of them, at night, down "
            "to the well in the square. Before the cold came.",
            "They climbed down into it. Down the well. She didn't come back "
            "up. None of them did. I saw.",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
        return
    if inv.has("cult_calling") and not save.flag("kid_playscript_noticed"):
        save.set_flag("kid_playscript_noticed", True)
        game.dialog.show([
            "That book. The one they write in.",
            "[c=dim]Don't open it where I can see.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
        return
    count = save.arg("kid_count", 0) + 1
    save.set_arg("kid_count", count)
    if count == 1:
        game.dialog.show([
            "My mom hums a song that doesn't stop. She doesn't know "
            "she's doing it.",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
    elif count == 2:
        game.dialog.show([
            "I keep biting my tongue. To check.",
            "[c=dim]It still bleeds right.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
    elif count == 3:
        game.dialog.show([
            "I don't walk past the church anymore.",
            "[c=dim]The door is open. They left it open.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
    elif count == 4:
        game.dialog.show([
            "If you find a way out, don't tell me.",
            "[c=dim]I tried to lie yesterday. My mouth wouldn't.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
    else:
        game.dialog.show([
            "[c=dim]The boy is watching the corn line.[/c]",
        ], speaker="", voice="blip_soft", portrait="tisdale_boy")


# ---- Hettie (the store) ----
# The quiet resister behind the counter -- the same Hettie who keeps the
# shop open out in town. She has nothing left to sell (the shop is gutted
# of its old vendor items) -- her value is what she risks saying out loud.

def hettie_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "store_owner")
    # The resister registers the resister-who-spoke being killed. Fires
    # once, on the first visit after the Preacher is doomed, but only if
    # we've already met her -- it would be too personal for first contact.
    if (save.flag("preacher_doomed")
            and not save.flag("shop_preacher_noticed")
            and save.arg("shop_count", 0) >= 1):
        save.set_flag("shop_preacher_noticed", True)
        game.dialog.show([
            "Heard about the preacher. I won't be saying his prayers in "
            "here. Don't ask me to.",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    count = save.arg("shop_count", 0) + 1
    save.set_arg("shop_count", count)
    if count == 1:
        plain = [
            "You're the one asking after the Blaine girl. Keep your voice "
            "down. In here.",
            "[c=dim]Can't help you. Not the way you want. Shelves are bare. "
            "Till's been empty since the spring. Nobody buys. Nobody sells.[/c]",
            "I'll say this much. Then nothing. Don't go where they tell you "
            "it's safe. I've got a family. Look around.",
        ]
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Hettie", voice="blip_high",
                         portrait="hettie")
        return
    if count == 2:
        game.dialog.show([
            "Back again. Good. You haven't gone quiet. Like the others.",
            "[c=dim]Don't trust the easy ones. The first to make peace, "
            "they went the soonest.[/c]",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    if count == 3:
        game.dialog.show([
            "I sold to the girl too. And the ones before her.",
            "[c=dim]None of them came back to buy again. You're the first.[/c]",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    if count == 4:
        game.dialog.show([
            "[c=dim]She glances at the door before she speaks.[/c]",
            "If you find the way out. The real one. You don't owe this "
            "town a goodbye. Just go.",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    if count == 5:
        game.dialog.show([
            "[c=dim]She shakes her head, just slightly. She's said too "
            "much already.[/c]",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    game.dialog.show([
        "[c=dim]She sits behind the counter, watching the window.[/c]",
    ], speaker="", voice="blip_soft", portrait="hettie")


# ---- The Sheriff: Hollis Vane ----

def sheriff_dialogue(game, npc):
    """The Sheriff -- a LOCAL, born here, broken (NARRATIVE §2). Not a
    believer, not a cultist. He did NOT kill the car -- the fold did;
    he's watched it happen before. He tells outsiders to leave out of
    muscle memory, knowing they can't and he can't either. A witness who
    can't help; the badge is just clothing now. Escalates over visits:
    weary warning -> the car (not his doing) -> the town's history ->
    the preacher he couldn't save."""
    save = game.save
    _cult_tell(game, "sheriff")
    n = save.arg("fisher_count", 0) + 1
    save.set_arg("fisher_count", n)
    if n == 1:
        # Local, born here, weary. Not a believer. The line "head home"
        # is muscle memory of the job he used to do.
        game.dialog.show([
            "Sheriff Vane.",
            "You're the one asking after the Blaine girl.",
            "[c=dim]I'd head home if I were you. I'm supposed to say that.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
    elif n == 2:
        # The car. He did NOT kill it -- the fold did. He's seen it
        # happen before. He's seen it many times.
        game.dialog.show([
            "Saw your car out by the lodge.",
            "Won't start. Won't ever. Nothing with an engine leaves Brimley.",
            "[c=dim]I didn't touch it. None of us did. It's the town.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
        if hasattr(game, "_fold_mentioned"):
            game._fold_mentioned("Sheriff Vane")
    elif n == 3:
        # The town is gone. He's local. He watched it happen.
        game.dialog.show([
            "I was born here. So was my dad.",
            "They started showing up in the summer. The new ones. "
            "Polite folks. After a while the road stopped going anywhere.",
            "[c=dim]I tell people to leave. I haven't been able to in months.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
    elif n == 4:
        # The preacher. He couldn't stop it.
        game.dialog.show([
            "They killed the preacher.",
            "He named them from his pulpit. They came in the night.",
            "[c=dim]I went over Tuesday morning. I didn't write a report. "
            "Who would I send it to.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
    else:
        game.dialog.show([
            "[c=dim]The badge is just clothing now. He keeps wearing it.[/c]",
        ], speaker="", voice="blip_soft", portrait="sheriff")


# ---- The Clerk: Mr. Sable ----

def clerk_dialogue(game, npc):
    """The Lodge Clerk, Mr. Sable -- the smiling trap-keeper (NARRATIVE §2).
    A LOCAL, and the most attuned of them: he dreamed the door longest and
    loudest of anyone born here, and has spent years subconsciously keeping
    the desk and the guests ready for arrivals he could never name. His
    menace is COMPULSION, NOT CONSPIRACY -- he voices certainties he can't
    account for (the door has spoken through him so long he mistakes it for
    hospitality), never a scheme he's in on. He keeps you comfortable, keeps
    you here, and the only thing he says about the car is deniable (the
    Sheriff carries the plain truth). The old fetch-quest chain is cut -- the
    car answers only to the Sign now, so he has no keys to dangle. He
    escalates over visits from warm host to something colder, and (visit 2)
    nudges you back to the front-desk register he can't say why he keeps."""
    save = game.save
    _cult_tell(game, "clerk")
    count = save.arg("clerk_count", 0) + 1
    save.set_arg("clerk_count", count)
    if count == 1:
        plain = [
            "Sable. I keep the desk here. Anything you need, you ask me. "
            "Anything at all.",
            "Settling in all right? Good. Most folks do, once they stop "
            "fighting it.",
            "[c=dim]He doesn't ask what brought you. He just smiles, like "
            "he's glad you'll be staying.[/c]",
            "The roads aren't going anywhere tonight. Neither are you. Get "
            "some rest.",
        ]
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Mr. Sable", voice="blip_low",
                         portrait="clerk")
        return
    if count == 2:
        game.dialog.show([
            "Sleep all right? People do here, better than they expect.",
            "[c=dim]The register's right there on the desk if you're the "
            "restless sort. Sign and guest both, all the way back.[/c]",
            "Read it if you like. Folks always look for a name that left. "
            "Won't change a thing.",
        ], speaker="Mr. Sable", voice="blip_low", portrait="clerk")
        return
    if count == 3:
        game.dialog.show([
            "Still asking your questions. That's fine. Ask away.",
            "[c=dim]She asked hers too, the Blaine girl. Right up until she "
            "stopped needing to.[/c]",
        ], speaker="Mr. Sable", voice="blip_low", portrait="clerk")
        return
    if count == 4:
        game.dialog.show([
            "[c=dim]He smiles, and it doesn't reach anything.[/c]",
            "You're not a guest who checks out. None of my best ones are.",
        ], speaker="Mr. Sable", voice="blip_low", portrait="clerk")
        return
    game.dialog.show(
        ["[c=dim]He nods you toward the stairs, patient as a man with all "
         "the time in the world.[/c]"],
        speaker="Mr. Sable", voice="blip_low", portrait="clerk")


def basement_photo_dialogue(game, npc):
    """The framed staff photograph on the cellar shelf -- flavor that
    echoes the Ledger (the Arcadia's people never age, never leave). The
    Case Photo keepsake moved to the Kid (NARRATIVE §2), so this grants
    nothing now; it's a lore examine that reinforces evidence #3."""
    save = game.save
    n = save.arg("photo_reads", 0) + 1
    save.set_arg("photo_reads", n)
    if n == 1:
        game.dialog.show([
            "[c=dim](A framed staff photograph on the shelf. The Arcadia's "
            "people lined up out front, and a date in the corner from "
            "decades back.)[/c]",
            "[c=dim]The Clerk stands dead centre, smiling. He has not aged "
            "a day.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
    else:
        game.dialog.show([
            "[c=dim](The same faces. The same patient, unmoving eyes.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
