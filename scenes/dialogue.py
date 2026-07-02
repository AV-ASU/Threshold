"""All NPC dialogue functions.

The spoken lines are final, lore-bearing copy: each NPC reacts to the
case (the Blaine girl, the well, the cult). State reactivity comes from
per-NPC flag/count gates (see the stateful fns below and the `beats`
hook in scenes/brimley.py _brimley_voice); `escalate` still exists but
both its call sites pass identical tiers, so it is effectively inert --
kept only in case visibility-tiered copy is ever authored. Evidence
beats are surfaced through `_evidence`; only the six in
`CANONICAL_EVIDENCE` count toward the King-gate and the visibility
floor.
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


def _evidence(game, name, content, weight=None, show=True):
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
            if hasattr(game, "audio"):
                game.audio.play("evidence_added", 0.7)
    # `show=False` files the beat (log + scribble) WITHOUT the forced dialog --
    # for readable items whose text lives in the kit, so picking one up doesn't
    # hijack the moment to read it at you.
    if show:
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
    # One-shot: the PI rang his bell. Crane claims it, and in claiming
    # it he teaches what the peal is FOR (everything in this town walks
    # toward a loud enough sound). Never preempts the first meeting,
    # and doesn't advance his doom ladder.
    if (save.flag("bell_rung") and not save.flag("crane_bell_beat")
            and save.arg("old_count", 0) >= 1):
        save.set_flag("crane_bell_beat", True)
        game.dialog.show([
            "That was you in my tower. The bell has not swung in years. "
            "Nobody left worth calling.",
            "They heard it, though. Everything in this town comes when "
            "something rings loud enough. Remember that.",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")
        return
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
            "You came back. They mostly don't.",
            "There's a flock in this town that kneels in no church of "
            "mine. It kneels under the ground.",
            "They weren't taken. They walked down willing, and sold the "
            "Lord to ease their own aches.",
            "I preach it plain, and spare no sinner. The sheriff hears "
            "every word, and never once takes communion.",
            "Let them come for an old man. I've buried better than the "
            "thing they kneel to.",
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
    -- and before that they LIVED in his school (the commune). His witness
    does two jobs now (§14 descent rework): it poses the descent question
    (they went down a well no one can follow) and it SEEDS THE SCHOOL --
    the room the Invitation names and the chalk-door rite reopens. What he
    gives you is what he tells you (no inventory item -- the old keepsake
    object was purged). Children notice what adults pretend not to."""
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
            "[c=dim]Before that they had my school. All of them, living in "
            "it, in rows. Then one night they walked out of it in a "
            "line.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
        return
    if inv.has("cult_calling") and not save.flag("kid_playscript_noticed"):
        save.set_flag("kid_playscript_noticed", True)
        game.dialog.show([
            "That book. The one they write in.",
            "[c=dim]Don't open it where I can see.[/c]",
        ], speaker="Toby Tisdale", voice="blip_kid", portrait="tisdale_boy")
        return
    # The envelope in the PI's pocket points at the school; the boy it
    # belonged to confirms it, once, and begs him off it.
    if (save.flag("rite_envelope_given")
            and not save.flag("kid_school_warned")):
        save.set_flag("kid_school_warned", True)
        game.dialog.show([
            "They slept in my school. All of them, in rows.",
            "[c=dim]I looked in the window once. The board still has my "
            "lesson on it, under their door.[/c]",
            "Don't go in there, mister.",
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
    # A faint memory of the girl herself (TODO #6): fires once the PI
    # carries her journal (her hand is in his pocket; the asking got
    # real). Mara passed through Brimley for a season before she went
    # below; Hettie knew her the way a counter knows anyone. NARRATIVE
    # §2: she does NOT know Walter; this is the girl, never the family.
    if (save.arg("shop_count", 0) >= 1
            and not save.flag("hettie_mara_memory")
            and game.player.inventory.has("mom_notebook")):
        save.set_flag("hettie_mara_memory", True)
        game.dialog.show([
            "The Blaine girl. I'll tell you the one thing I know that's "
            "worth the telling.",
            "She used to come in here. Matches, canned milk. Counted her "
            "change twice, every time, like it mattered. Sad around the "
            "eyes, and polite with it.",
            "[c=dim]Then one day past the new year she set her basket "
            "down half filled and walked out smiling. Left the basket "
            "on the counter. I never saw her again.[/c]",
            "[c=dim]It was the smiling I minded.[/c]",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    # The trade: yesterday's paper (the April 14 issue, picked up before
    # the drive north) for ONE load of the cartridges she keeps under the
    # counter. One opportunistic barter, NOT a fetch chain (Sable's was
    # cut on purpose). The date is the point: Brimley hasn't seen a paper
    # since the trucks stopped at the mid-January seal (NARRATIVE §1
    # setting note 3), so yesterday's date makes the three-month cut-off
    # legible, and trading ammo for one is how starved for word they
    # are. Fires once, after she's met you (her first conversation is
    # too wary for it).
    if (save.arg("shop_count", 0) >= 1
            and not save.flag("newspaper_traded")
            and game.player.inventory.has("newspaper")):
        save.set_flag("newspaper_traded", True)
        game.player.inventory.remove("newspaper", 1)
        game.player.inventory.add("pistol_ammo", 6)
        game.audio.play("pickup_rare", 0.7)
        game.dialog.show([
            "[c=dim]Her eyes stop on the newspaper folded in your coat "
            "pocket. She goes very still.[/c]",
            "What's the date on that. The date.",
            "[c=dim]You show her. April 14. Yesterday. You bought it "
            "before the drive north.[/c]",
            "Yesterday's. We haven't had a paper through here since the "
            "trucks stopped.",
            "Leave it on the counter and take what's under it. The till's "
            "been empty since the new year. The shelf under it hasn't.",
            "[c=dim]One load of cartridges across the counter. She's "
            "already reading yesterday's news like a letter from someone "
            "she'd given up on.[/c]",
        ], speaker="Hettie", voice="blip_high", portrait="hettie")
        return
    count = save.arg("shop_count", 0) + 1
    save.set_arg("shop_count", count)
    if count == 1:
        plain = [
            "You're the one asking after the Blaine girl. Keep your voice "
            "down. In here.",
            "[c=dim]Can't help you. Not the way you want. Shelves are bare. "
            "Till's been empty since the new year. Nobody buys. Nobody "
            "sells.[/c]",
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
    weary warning -> the car (not his doing) -> the town's history.
    The preacher he couldn't save is a one-shot, gated on the player
    having SEEN the church floor (preacher_body_seen) -- it used to sit
    at visit 4, where it could announce the murder before it happened."""
    save = game.save
    _cult_tell(game, "sheriff")
    # The murder he can't report. Fires once, on the first visit after
    # the player has found the body -- but never as a first impression.
    if (save.flag("preacher_body_seen")
            and not save.flag("vane_preacher_noticed")
            and save.arg("fisher_count", 0) >= 1):
        save.set_flag("vane_preacher_noticed", True)
        game.dialog.show([
            "They killed the preacher.",
            "He named them from his pulpit. They came in the night.",
            "[c=dim]I went over Tuesday morning. I didn't write a report. "
            "Who would I send it to.[/c]",
            "[c=dim]He doesn't say the Reverend's name. You realize "
            "nobody in town has.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
        return
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
    else:
        game.dialog.show([
            "[c=dim]The badge is just clothing now. He keeps wearing it.[/c]",
        ], speaker="", voice="blip_soft", portrait="sheriff")


# ---- The Clerk: Mr. Sable ----

def clerk_dialogue(game, npc):
    """The Lodge Clerk, Mr. Sable -- the smiling trap-keeper (NARRATIVE §2).
    A LOCAL, and the most attuned of them: he dreamed the door longest and
    loudest of anyone born here, and has spent years keeping the desk and
    the guests ready. His menace is COMPULSION, NOT CONSPIRACY -- he voices
    certainties he can't account for (the door has spoken through him so
    long he mistakes it for hospitality), never a scheme he's in on. He
    keeps you comfortable, keeps you here, and the only thing he says about
    the car is deniable (the Sheriff carries the plain truth). The old
    fetch-quest chain is cut -- the car answers only to the Sign now, so he
    has no keys to dangle. He escalates over visits from warm host to
    something colder, and (visit 2) nudges you back to the front-desk
    register he can't say why he keeps.

    THE INVITATION (the act break): the congregation -- the guests who sign
    in and never out -- left an envelope at his desk when they went below,
    told to hold it until he was ready to follow. He KNOWS what it is and
    where its writers went (the robe in his closet was always the tell);
    what he does with it stays hospitality: at 3 evidence he judges the
    guest ready in his place, and hands it over like a room key. Somebody
    has to keep the desk. State-gated on what the PI knows -- never
    farmable by repeat visits."""
    save = game.save
    _cult_tell(game, "clerk")
    # The handoff preempts the visit rotation the moment the PI is ready.
    if (not save.flag("rite_envelope_given")
            and game._evidence_count() >= 3):
        save.set_flag("rite_envelope_given", True)
        game.player.inventory.add("rite_envelope", 1)
        game.audio.play("pickup_rare", 0.7)
        game.dialog.show([
            "You're past pretending to be a guest now, I think. All right.",
            "[c=dim](He reaches under the register and lays a long envelope "
            "on the desk. Wax seal, and the Sign pressed into the wax. He "
            "handles it like a room key.)[/c]",
            "The ones who stayed here before you left this at my desk when "
            "they went. They said I would know when I was ready to follow.",
            "I believe it meant you. Somebody has to keep the desk.",
            "[c=dim]He smiles the way he always smiles. \"Anything else you "
            "need, you ask me. Anything at all.\"[/c]",
        ], speaker="Mr. Sable", voice="blip_low", portrait="clerk")
        # The PI's case note (a NOTE, never evidence -- must not feed the
        # King-gate). Same live-list append pattern as _log_case_entry.
        notes = save.arg("notes", [])
        if isinstance(notes, list) and not any(
                isinstance(e, dict) and e.get("name") == "the_invitation"
                for e in notes):
            notes.append({"name": "the_invitation", "lines": [
                "Sable kept an envelope under the register. A year at "
                "least. Handed it to me like a room key.",
                "The guests who never signed out left it for him, for the "
                "day he was ready. He gave it away instead. Says the desk "
                "needs him.",
                "It reads like scripture and gives directions like a "
                "flyer. The school first, it says. Where they slept.",
            ]})
        return
    count = save.arg("clerk_count", 0) + 1
    save.set_arg("clerk_count", count)
    if count == 1:
        plain = [
            "Sable. I keep the desk here. Anything you need, you ask me. "
            "Anything at all.",
            "Can't account for the gloom that's settled on the town of late. "
            "Myself, I have never felt more content. Not in all my years "
            "behind this desk.",
            "The lodge has never been fuller, you know. Every room spoken for, "
            "going back a good while now.",
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
            "[c=dim]Every room above is spoken for, and yet the halls stay so "
            "quiet. They have all checked in. Not a one of them seems to be "
            "about. ...No matter. They will not have left.[/c]",
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
            "[c=dim](The same faces. The same unmoving eyes.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
