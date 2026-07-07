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
import random


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
        # A discovery can point the PI back at someone he's met; those
        # interior lines ride the SAME narration so it reads as one beat
        # (and files their case notes). Defined after this fn; safe at
        # call time.
        extra = _collect_revisit(game, name)
        game.dialog.show(lines + extra,
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


def _log_note(game, key, lines):
    """File a PI case NOTE once, keyed by name. NOTES are the interior
    voice, shown in the notebook after the clues; they must NEVER go in
    `evidence` (that count drives the King-gate and the visibility floor)."""
    notes = game.save.arg("notes", [])
    if isinstance(notes, list) and not any(
            isinstance(e, dict) and e.get("name") == key for e in notes):
        notes.append({"name": key, "lines": list(lines)})
        game.save.set_arg("notes", notes)


# The investigation grows: when the PI makes a DISCOVERY, some of what he
# learns points back at someone he has already met (she left smiling; the
# clerk saw her every day; go ask him). Each nudge fires ONCE, only if the
# NPC has been met, and it (a) files a case note and (b) appends the PI's
# interior line onto the discovery's own narration so it reads as one beat
# ("...I should go back and ask him"). The matching follow-up QUESTION is
# gated on the same evidence in that NPC's conversation, so even if the
# nudge is missed (met the NPC after the find) the question still opens.
_REVISIT_NUDGES = {
    "the_ledger": [{
        "key": "revisit_sable_checkouts",
        "met": "sable_greeted",
        "lines": [
            "[c=dim]The register never shows a checkout. Not one, in years "
            "of guests.",
            "The clerk keeps that desk like it owes him something. I should "
            "put it to him straight.[/c]",
        ],
    }],
    "maras_journal": [{
        "key": "revisit_sable_smile",
        "met": "sable_greeted",
        "lines": [
            "[c=dim]She wrote like someone already halfway through a door.",
            "The clerk saw her every day she stayed here. He would know the "
            "day she stopped writing. Worth going back for.[/c]",
        ],
    }],
}


def _collect_revisit(game, name):
    """For a just-fired discovery `name`, file any met-gated revisit notes
    and return their interior-voice lines to append to the discovery's
    narration."""
    out = []
    for n in _REVISIT_NUDGES.get(name, []):
        if not game.save.flag(n["met"]):
            continue
        if game.save.flag("nudged_" + n["key"]):
            continue
        game.save.set_flag("nudged_" + n["key"], True)
        _log_note(game, n["key"], n["lines"])
        out.extend(n["lines"])
    out.extend(_ready_for_the_desk(game, name))
    return out


def _ready_for_the_desk(game, name):
    """When the PI crosses the readiness line (3 canonical beats) on the
    surface, still without the Invitation, nudge him back to Sable -- so the
    act break is signposted, not a silent 'walk back to the desk'. Fires
    once, only if Sable has been met and has not yet handed it over. (Once
    the PI is underground he already holds it, so this cannot fire there.)"""
    if (name not in CANONICAL_EVIDENCE
            or game._evidence_count() != 3
            or not game.save.flag("sable_greeted")
            or game.save.flag("rite_envelope_given")
            or game.player.inventory.has("rite_envelope")
            or game.save.flag("nudged_ready_for_desk")):
        return []
    game.save.set_flag("nudged_ready_for_desk", True)
    lines = [
        "[c=dim]That is the third thread that runs back into this town. I "
        "have enough now to stop asking and start moving.",
        "The clerk has been holding something for me since I walked in. Time "
        "to go back to that desk and let him give it to me.[/c]",
    ]
    _log_note(game, "ready_for_the_desk", lines)
    return lines


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


# ---- The Kid: Toby ----

def toby_dialogue(game, npc):
    """Toby -- innocent witness (NARRATIVE §2). He FOLLOWED the night
    procession down the river to the cult's dug-open ground and saw them go
    below -- the sole witness of where they went (D rework, 2026-07) -- and
    before that they LIVED in his school (the commune). His witness does two
    jobs (§14 descent rework): it poses the descent question (they went down a
    way no one can follow now -- the grove is fold-hidden) and it SEEDS THE
    SCHOOL -- the room the Invitation names and the chalk-door rite reopens.
    He does not know WHY they dig; given the state of the town he is sure the
    evil is down there. What he gives you is what he tells you (no inventory
    item). Children notice what adults pretend not to."""
    save = game.save
    inv = game.player.inventory
    # The witness beat: first real conversation, he tells you what he saw.
    if not save.flag("kid_witnessed"):
        save.set_flag("kid_witnessed", True)
        game.dialog.show([
            "You're looking for the lady from the lodge.",
            "She went with the others. A whole line of them, at night. I "
            "followed. Down along the river, to where the ground is all "
            "broke open. Before the cold came.",
            "They climbed down into it, down into the dark under the field. "
            "She never came back up. None of them did. I saw where they go.",
            "[c=dim]Whatever they do down there, that is where it is. The bad "
            "thing. I know it.[/c]",
            "[c=dim]Before that they had my school. All of them, living in "
            "it, in rows. Then one night they walked out of it in a "
            "line.[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
        return
    if inv.has("cult_calling") and not save.flag("kid_playscript_noticed"):
        save.set_flag("kid_playscript_noticed", True)
        game.dialog.show([
            "That book. The one they write in.",
            "[c=dim]Don't open it where I can see.[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
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
        ], speaker="Toby", voice="blip_kid", portrait="toby")
        return
    count = save.arg("kid_count", 0) + 1
    save.set_arg("kid_count", count)
    if count == 1:
        game.dialog.show([
            "My mom hums a song that doesn't stop. She doesn't know "
            "she's doing it.",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
    elif count == 2:
        game.dialog.show([
            "I keep biting my tongue. To check.",
            "[c=dim]It still bleeds right.[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
    elif count == 3:
        game.dialog.show([
            "I don't walk past the church anymore.",
            "[c=dim]The door is open. They left it open.[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
    elif count == 4:
        game.dialog.show([
            "If you find a way out, don't tell me.",
            "[c=dim]I tried to lie yesterday. My mouth wouldn't.[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
    else:
        game.dialog.show([
            "[c=dim]The boy is watching the corn line.[/c]",
        ], speaker="", voice="blip_soft", portrait="toby")


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
# The organic ask-verb, piloted on Sable (TODO #1). The menu options ARE
# the PI's own spoken lines; picking one plays a back-and-forth over their
# heads. Sable is the FIRST local the PI meets, and the exchange sets the
# tone for the whole town: he is the smiling, pro-newcomer host who DOES
# NOT give the girl up. He deflects the name, folds Mara in with "the new
# folk," and points the suspicion the wrong way -- at the "unfriendly" old
# families -- which is the exact trap the game punishes (the warm ones are
# the cult; NARRATIVE 2, Hettie's "don't trust the easy ones"). He is the
# most-attuned LOCAL: he knows, and never says he knows. The mask only
# thins as the case grows (the ledger and the journal each open a colder
# follow-up). Compulsion, never a confessed scheme. Engine:
# ui/conversation.Conversation.

def _sable_showed_photo(game):
    game.save.set_flag("sable_saw_photo", True)
    _log_note(game, "showed_the_clerk", [
        "I put her face on his desk. He looked at it a long while, smiling "
        "the whole time, and told me nothing at all.",
        "I had the feeling he did not need the picture.",
    ])


def _sable_give_invitation(game):
    """The act break, now a CHOSEN beat (not an auto-handoff). Fired by the
    'the_way_down' exchange's on_ask when the PI asks Sable for the way: he
    hands over the Invitation like a room key, sets the flag, and files the
    PI's NOTE (never evidence)."""
    save = game.save
    if save.flag("rite_envelope_given") or game.player.inventory.has(
            "rite_envelope"):
        return
    save.set_flag("rite_envelope_given", True)
    game.player.inventory.add("rite_envelope", 1)
    if hasattr(game, "audio"):
        game.audio.play("pickup_rare", 0.7)
    _log_note(game, "the_invitation", [
        "Sable kept an envelope under the register. A year at least. Handed "
        "it to me like a room key.",
        "The guests who never signed out left it for him, for the day he was "
        "ready. He gave it away instead. Says the desk needs him.",
        "It reads like scripture and gives directions like a flyer. The "
        "school first, it says. Where they slept.",
    ])


def sable_on_leave(game):
    """A last word the first time the PI tries to walk off. Sable stops him,
    and plants the sealed/warped town without spelling it out -- the host
    keeping the guest a beat longer, and the compulsion leaking through as
    hospitality. Fires once."""
    if game.save.flag("sable_farewell_hook"):
        return None
    game.save.set_flag("sable_farewell_hook", True)
    return [
        ("npc", "Hold a moment. You drove in off that road last night. So "
                "you'll know."),
        ("npc", "Did it feel to you like it went anywhere? Folk say it does "
                "not, lately. I wouldn't know. I never leave the desk."),
    ]


SABLE_CONVO = {
    "id":    "sable",
    "name":  "Mr. Sable",
    "voice": "blip_low",
    "pi_voice": "blip_soft",
    "prompt": "Sable folds his hands on the register and waits.",
    "leave":  "That's all for now.",
    "greet": {
        "flag": "sable_greeted",
        "beats": [
            ("npc", "Sable. I keep the desk here. Anything you need, you "
                    "ask me. Anything at all."),
        ],
    },
    "on_leave": sable_on_leave,
    "exchanges": [
        {
            "key": "mara",
            "q": "I'm looking for a woman. Mara Blaine. She'd have come "
                 "through here.",
            "beats": [
                ("npc", "Blaine. No, I can't say the name lands anywhere. We "
                        "get a great many faces through that door."),
                ("npc", "You'll mean one of the new folk, though. We have had "
                        "no end of those this past year. They come like they "
                        "heard something worth the drive."),
                ("npc", "And I am glad of every one. This town was drying up "
                        "before they started arriving. I keep every room "
                        "full now."),
                ("pi", "And the rest of Brimley feels the same?"),
                ("npc", "Ah. There you have it. Not everyone's been so warm. "
                        "Some of the old families have gone cold as a root "
                        "cellar about the newcomers."),
                ("npc", "I would mind who you take your questions to, friend. "
                        "Not everyone here wishes a stranger well. I do. You "
                        "remember that."),
                ("ask", "Show him her photograph?", [
                    ("Slide the photo across the desk.", [
                        ("pi", "(You lay her photo on the register.)"),
                        ("npc", "(He looks at it a good while, smiling.) "
                                "Pretty thing. No, I couldn't say. She'll "
                                "have found her feet by now. They all do."),
                    ], _sable_showed_photo),
                    ("Keep it in your coat.", [
                        ("pi", "(You leave it where it is.)"),
                        ("npc", "No matter. Ask around, if you must. Start "
                                "with the friendly ones. There are fewer of "
                                "those than you would think."),
                    ], None),
                ]),
            ],
        },
        # A STARTING question that seeds the Ledger: he points you at the
        # register on the desk (a lead) and shrugs off the padlocked cellar
        # where the old books really went.
        {
            "key": "cellar",
            "q": "A lot of doors in this town stay locked. You keep a cellar "
                 "under this place?",
            "beats": [
                ("npc", "Storage, mostly. The key is about somewhere. Nothing "
                        "down there worth the dust, I promise you."),
                ("npc", "If it is names you want, sign-in register is right "
                        "here on the desk. Guest and date, all the way back. "
                        "Read it as long as you like."),
            ],
        },
        # A STARTING question: the town has been sealed since the mid-January
        # rite (it is mid-April now -- THREE months; NARRATIVE 1). The PI has
        # the dates from his own case; Sable downplays a supernatural seal as
        # ordinary winter and never lets the word "trapped" near it.
        {
            "key": "sealed",
            "q": "Nothing leaves this town. No car, no truck, no mail since "
                 "January. That's three months. What happened here?",
            "beats": [
                ("npc", "Happened? Nothing happened. The snows came in around "
                        "the new year and the road just... stopped mattering. "
                        "It does that, up here."),
                ("npc", "Three months is nothing to a town like this. Folk "
                        "get comfortable. Warm bed, full larder, good company. "
                        "You will too, give it time."),
            ],
        },
        {
            "key": "car",
            "q": "My car won't start. I'm told no car in this town will.",
            "beats": [
                ("npc", "The roads are not going anywhere tonight. Neither "
                        "are you. I would not fret over the car."),
                ("pi", "I didn't ask about tonight. I asked what's wrong "
                       "with every car in this town."),
                ("npc", "It is the only one I have, and I have never needed "
                        "another. Get some rest."),
            ],
        },
        # Unlocked by reading the cellar Ledger (evidence the_ledger); the
        # discovery nudges the PI back here (see _REVISIT_NUDGES). The mask
        # thins: he stops pretending to keep the paperwork, keeps the promise.
        {
            "key": "checkouts",
            "q": "I read your register. Every guest signs in. Not one ever "
                 "signs out.",
            "avail": lambda g: g.save.flag("evidence_the_ledger"),
            "beats": [
                ("npc", "(The pleasant look does not shift.) Do they not? "
                        "Fancy that. I never was much of a hand with the "
                        "paperwork."),
                ("npc", "They will not have gone far. Nobody does. It is a "
                        "restful town, friend. People stay. It is the one "
                        "thing I can promise a guest."),
            ],
        },
        # Unlocked by reading Mara's journal (evidence maras_journal). This
        # is where the mask thins the most: "she is not lost" is as close as
        # he comes to admitting he knows, and still no scheme is confessed.
        {
            "key": "her_state",
            "q": "Her journal reads like someone already halfway out a "
                 "door. When did she change?",
            "avail": lambda g: g.save.flag("evidence_maras_journal"),
            "beats": [
                ("npc", "(He sets his hands flat on the desk.) You keep "
                        "telling me she is lost. I keep telling you she is "
                        "not."),
                ("npc", "She stopped fretting, toward the end. Folk do, "
                        "here. It is a mercy, if you let it be. You will let "
                        "it be too, in time."),
            ],
        },
        # The reproach: once the PI has learned the roads loop back on
        # themselves (a local told him, filing the_fold_told note, or he has
        # crossed a fold), he can put it to Sable -- who deflects by pointing
        # out he DID say it, plainly, and the PI simply heard hospitality.
        {
            "key": "the_fold",
            "q": "I walked the road out of town. Followed it two hours, due "
                 "west. It set me back down past this window.",
            "avail": lambda g: any(
                isinstance(e, dict) and e.get("name") == "the_fold_told"
                for e in (g.save.arg("notes", []) or [])),
            "beats": [
                ("npc", "I told you the roads were not going anywhere. You "
                        "heard a man being hospitable. I meant it plainly."),
                ("npc", "There is no call to be cross about it. You are safe "
                        "here. Safer than out there."),
            ],
        },
        # THE WAY DOWN (the act break, now an explicit ASK -- not a silent
        # auto-handoff). Offered once the PI is ready (3 evidence) and does
        # not already carry it; picking it fires _sable_give_invitation. A
        # case NOTE (_evidence readiness nudge) points him back to the desk
        # when he crosses the threshold, so it is signposted, not a guess.
        {
            "key": "the_way_down",
            "q": "You've kept something back from me since I walked in. "
                 "I'll take it now.",
            "once": True,
            "avail": lambda g: (g._evidence_count() >= 3
                                and not g.save.flag("rite_envelope_given")
                                and not g.player.inventory.has(
                                    "rite_envelope")),
            "on_ask": _sable_give_invitation,
            "beats": [
                ("npc", "You are past pretending to be a guest now, I think. "
                        "All right."),
                ("npc", "(He lays a long envelope on the desk. Wax seal, the "
                        "Sign pressed into it. He handles it like a room "
                        "key.)"),
                ("npc", "The ones who stayed before you left this for the day "
                        "they were ready to follow. I believe it meant you. "
                        "Somebody has to keep the desk."),
            ],
        },
    ],
}


def sable_on_death(game, npc):
    """The Invitation drops with him. Sable is the most-attuned LOCAL and
    the one who carries the way down (the envelope that opens the school
    rite). If the PI kills him BEFORE the handoff, the sealed envelope
    falls with the body and can be looted; if he already gave it (or the PI
    already has one), there is nothing to find. The `_given` flag is left
    ALONE on purpose -- setting it here would soft-lock a player who leaves
    the drop, since a killed local rebuilds LIVE on scene re-entry and the
    desk handoff (gated on the flag AND the item) could then re-arm."""
    inv = game.player.inventory
    if game.save.flag("rite_envelope_given") or inv.has("rite_envelope"):
        return
    game.scene.items.append({
        "x": npc.x + random.uniform(-6, 6),
        "y": npc.y + random.uniform(-6, 6),
        "key": "rite_envelope", "qty": 1,
    })
    if hasattr(game, "show_notice"):
        game.show_notice(
            "Something stiff in the clerk's coat: a wax-sealed envelope.",
            duration=2.6)


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
    _cult_tell(game, "clerk")
    # The organic conversation. His welcome floats once (the greet in
    # SABLE_CONVO), then the menu is the PI's own questions -- each picked
    # line is spoken, Sable answers in turn over the desk, the world keeps
    # running, and new questions surface as the case grows. The Invitation
    # is no longer an auto-handoff the moment you hit 3 evidence: it is an
    # explicit ASK ("the_way_down" exchange, gated on readiness), and a case
    # NOTE nudges the PI back to the desk when he is ready (see _evidence).
    from ui.conversation import open_conversation
    open_conversation(game, npc, SABLE_CONVO)


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
