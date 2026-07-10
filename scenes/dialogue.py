"""All NPC dialogue functions.

The spoken lines are final, lore-bearing copy: each NPC reacts to the
case (the Blaine girl, the well, the cult). The PRINCIPALS (Sable, Vane,
Hettie, Toby, Crane) all speak through the organic ask verb now
(ui/conversation `*_CONVO` data, TODO #1): the menu options are the PI's
own spoken lines, every principal leads with the two guaranteed openers
(`_opener_exchanges`: introduce-as-PI + Mara's photograph), and each
NPC's story-critical one-shots (the witness account, the memory of the
girl, the murder he can't report, the paper trade) still VOLUNTEER
themselves ahead of the menu. Other state reactivity comes from per-NPC
flag gates and the `beats` hook in scenes/brimley.py _brimley_voice.
`escalate` still exists but now has NO call sites -- kept only in case
visibility-tiered copy is ever authored. Evidence beats are surfaced
through `_evidence`; only the six in `CANONICAL_EVIDENCE` count toward
the King-gate and the visibility floor.
"""
import random


# The SIX canonical evidence beats (NARRATIVE.md §6): ONLY these count toward
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
    # A discovery can point the PI back at someone he's met; those
    # interior lines ride the discovery's own narration so it reads as
    # one beat (and files their case notes). Collected REGARDLESS of
    # `show` -- a silently-filed beat (the journal reads from the kit)
    # must still land its nudges, or the case stalls without a voice
    # (the R-gate stall finding). Defined after this fn; safe at call
    # time.
    extra = _collect_revisit(game, name)
    # `show=False` files the beat (log + scribble) WITHOUT the forced dialog --
    # for readable items whose text lives in the kit, so picking one up doesn't
    # hijack the moment to read it at you. Any nudges still surface, as
    # their own caption.
    if show:
        game.dialog.show(lines + extra,
                         speaker="", voice="blip_soft",
                         portrait="narrator")
    elif extra:
        game.dialog.show(extra, speaker="", voice="blip_soft",
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
    "the_preacher": [{
        "key": "revisit_vane_murder",
        "met": "vane_greeted",
        "lines": [
            "[c=dim]They left him on the bank where the whole town draws "
            "its water. Nobody carried him home.",
            "The sheriff was born here. He knew this man his whole life. "
            "Worth hearing what he could not write down.[/c]",
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
    out.extend(_the_third_thread(game, name))
    out.extend(_ready_for_the_desk(game, name))
    return out


def _the_third_thread(game, name):
    """The stall-breaker for the Crane fork (R-gate finding). Only three
    evidence beats are reachable on the surface (the journal, the Ledger,
    the preacher's remains), and the descent needs three -- so a player
    who held Crane back (or never pressed him) caps at TWO and the case
    goes silent. When the second canonical beat lands with the preacher
    still alive, the PI's interior voice points him back at the pulpit:
    the forced return reads as the investigation forcing his hand, not a
    dead end. Fires once, only if Crane has been met. Never evidence."""
    if (name not in CANONICAL_EVIDENCE
            or game._evidence_count() != 2
            or game.save.flag("preacher_doomed")
            or not game.save.flag("crane_greeted")
            or game.save.flag("nudged_third_thread")):
        return []
    game.save.set_flag("nudged_third_thread", True)
    lines = [
        "[c=dim]Two threads in hand, and both of them end somewhere under "
        "this town.",
        "One man here still says the quiet part out loud, from a pulpit, "
        "to an empty room. He is not done saying it.",
        "I should hear him out. However that ends.[/c]",
    ]
    _log_note(game, "the_third_thread", lines)
    return lines


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


# ---- The two GUARANTEED openers (TODO #1) ----
# Every principal's question menu leads with the same two options: the PI
# introducing himself as a private investigator, and showing Mara's
# photograph. The QUESTIONS are shared word for word (he has said them a
# hundred times by now); every ANSWER is the NPC's own. This is also the
# fiction's fix: news does not spread in Brimley (a town of homebound
# locals), so nobody knows who the PI is or what he wants until he says
# it -- greets never assume the case is known; the PI initiates.

_INTRO_Q = ("I'm a private investigator, out of Minneapolis. A family "
            "hired me to find their daughter. She was last heard from "
            "headed to Brimley.")
_PHOTO_Q = "I want you to look at a photograph. Have you seen this woman?"


def _opener_exchanges(intro_beats, photo_beats, on_photo=None,
                      photo_avail=None):
    """Build the shared intro + photo exchanges from per-NPC answers.
    Both are once-asked (you only introduce yourself the one time); the
    photo exchange can carry a side effect (a flag another question
    gates on) and an avail gate (Hettie's drops once her volunteered
    memory has outrun it). The menu shows the short labels (the choice
    box is small); the full question still floats as the PI's spoken
    line."""
    photo = {
        "key": "photo", "q": _PHOTO_Q, "once": True,
        "label": "Have you seen this woman?",
        "beats": ([("pi", "(You hold her photograph out.)")]
                  + list(photo_beats)),
    }
    if on_photo is not None:
        photo["on_ask"] = on_photo
    if photo_avail is not None:
        photo["avail"] = photo_avail
    return [
        {"key": "intro", "q": _INTRO_Q, "once": True,
         "label": "I'm a private investigator.",
         "beats": list(intro_beats)},
        photo,
    ]


# ---- The Preacher: Reverend Asa Crane ----
# Ask-verb conversion (TODO #1 expand), carrying the ticket's pilot
# choice: his doom is no longer an automatic visit counter. The flock
# exchange ends on a real fork -- press him and he takes his naming to
# where they can hear it (preacher_doomed; the church swaps him for his
# remains on the next entry, evidence #4), or hold him back and he banks
# the fire for now (the question stays open; a held-back Crane can still
# be pressed later). Canon fence (§1b): the cult cannot be saved or
# converted; Crane dies for believing he can. The choice decides whether
# the PI is the one who points him.


def _crane_provoked(game):
    game.save.set_flag("preacher_doomed", True)
    _log_note(game, "crane_provoked", [
        "[c=dim]I wound the old man up and pointed him at them. He wanted "
        "pointing. That is what I will tell myself.[/c]",
    ])


def crane_on_leave(game):
    """His old dismissal, kept as the one-time last word."""
    if game.save.flag("crane_farewell_hook"):
        return None
    game.save.set_flag("crane_farewell_hook", True)
    return [
        ("npc", "I've said what I've said. Go on now, and watch the road."),
    ]


CRANE_CONVO = {
    "id":    "crane",
    "name":  "Rev. Crane",
    "voice": "blip_low",
    "pi_voice": "blip_soft",
    "prompt": "Crane waits, hands folded over the lectern.",
    "leave":  "That's all for now.",
    "greet": {
        "flag": "crane_greeted",
        "beats": [
            ("npc", "Another new face. That's all that comes to Brimley "
                    "anymore, strangers off the highway, more every "
                    "season. And not one of them leaves."),
        ],
    },
    "on_leave": crane_on_leave,
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "I don't trust it. They arrive too easy, like "
                    "something held the door. Then they go quiet, drift "
                    "out to the corn, and they don't come back."),
            ("npc", "A young woman came through in the fall. Bright "
                    "thing, full of questions, like you. She's one of "
                    "them now, whatever they are. That who you're after?"),
        ],
        photo_beats=[
            ("npc", "(He looks, and his mouth goes tight.)"),
            ("npc", "I know her. She sat my pews twice, early on, right "
                    "at the back. I remember thinking, there's one with "
                    "her eyes still open."),
            ("npc", "[c=dim]Then she stopped coming. They all stop.[/c]"),
        ],
    ) + [
        # Earned by the intro: his "they arrive too easy" answer is what
        # the PI is following up on.
        {
            "key": "flock",
            "q": "You watch this town from a pulpit. Tell me about the "
                 "new folk. The congregation that isn't yours.",
            "label": "Tell me about the new folk.",
            "avail": lambda g: (g.save.flag("convo_crane_intro_asked")
                                and not g.save.flag("preacher_doomed")),
            "beats": [
                ("npc", "There's a flock in this town that kneels in no "
                        "church of mine. Where they kneel now, I couldn't "
                        "tell you."),
                ("npc", "All I have is a rumor. The boy Toby swears he "
                        "watched them walk off down the river one night. "
                        "Nobody has seen them since."),
                ("npc", "They weren't taken. They walked off willing, "
                        "and sold the Lord to ease their own aches."),
                ("ask", "He is working himself hot. The next words go "
                        "somewhere they can be heard.", [
                    ("Press him. Names carry.", [
                        ("pi", "Somebody should say it where they can "
                               "hear. You're the only one in this town "
                               "still willing."),
                        ("npc", "I preach it plain, and spare no sinner. "
                                "The sheriff hears every word, and never "
                                "once takes communion."),
                        ("npc", "Let them come for an old man. I've "
                                "buried better than the thing they kneel "
                                "to."),
                    ], _crane_provoked),
                    ("Hold him back. It is not worth his life.", [
                        ("pi", "Keep it inside these walls, Reverend. In "
                               "this town the ones who go quiet are the "
                               "loud ones."),
                        ("npc", "(A long breath goes out of him.) You "
                                "sound like a man who means it. All "
                                "right. Inside these walls. For now."),
                        ("pi", "[c=dim]For now. A man like that only "
                               "banks a fire. He never puts it out.[/c]"),
                    ], None),
                ]),
            ],
        },
    ],
}


def preacher_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "preacher")
    # One-shot: the PI rang his bell. Crane claims it, and in claiming
    # it he teaches what the peal is FOR (everything in this town walks
    # toward a loud enough sound). Never preempts the first meeting,
    # and never the fork.
    if (save.flag("bell_rung") and not save.flag("crane_bell_beat")
            and save.flag("crane_greeted")):
        save.set_flag("crane_bell_beat", True)
        game.dialog.show([
            "That was you in my tower. The bell has not swung in years. "
            "Nobody left worth calling.",
            "They heard it, though. Everything in this town comes when "
            "something rings loud enough. Remember that.",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")
        return
    from ui.conversation import open_conversation
    open_conversation(game, npc, CRANE_CONVO)


# ---- The Kid: Toby ----

def toby_dialogue(game, npc):
    """Toby -- innocent witness (NARRATIVE §4). He FOLLOWED the night
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
    from ui.conversation import open_conversation
    open_conversation(game, npc, TOBY_CONVO)


# Ask-verb conversion (TODO #1 expand): everything Toby VOLUNTEERS (the
# witness account, the playscript flinch, the school warning) fires ahead
# of the menu in toby_dialogue above; the menu is what the PI chooses to
# ask a child, and the old visit-ladder lines are now his answers.
TOBY_CONVO = {
    "id":    "toby",
    "name":  "Toby",
    "voice": "blip_kid",
    "pi_voice": "blip_soft",
    "prompt": "Toby watches the corn line while you think.",
    "leave":  "That's all for now.",
    "greet": {
        "flag": "toby_greeted",
        "beats": [
            ("npc", "You came back. Grownups mostly don't. Not a second "
                    "time."),
            ("npc", "I see things. Nobody figures a kid for watching."),
        ],
    },
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "A detective. For real? Like on the TV."),
            ("npc", "Nobody here would hire one. Asking questions is what "
                    "you stop doing, if you live here."),
            ("pi", "You're talking to me."),
            ("npc", "[c=dim]I know. Don't tell my mom.[/c]"),
        ],
        photo_beats=[
            ("npc", "That's her. The lady from the lodge. I already told "
                    "you where she went."),
            ("npc", "Down where the ground is all broke open, past the "
                    "river. You can't walk there. I tried to find it "
                    "again in the daytime and the field just put me back."),
            ("npc", "[c=dim]Keep her picture put away. Some of them look "
                    "at what you carry.[/c]"),
        ],
    ) + [
        {
            "key": "home",
            "q": "How are things at home? Anything strange?",
            "label": "Anything strange at home?",
            "once": True,
            "beats": [
                ("npc", "My mom hums a song that doesn't stop. She doesn't "
                        "know she's doing it."),
                ("npc", "I keep biting my tongue. To check."),
                ("npc", "[c=dim]It still bleeds right.[/c]"),
            ],
        },
        {
            "key": "church",
            "q": "Do you go by the church much?",
            "once": True,
            "beats": [
                ("npc", "I don't walk past the church anymore."),
                ("npc", "[c=dim]The door is open. They left it open.[/c]"),
            ],
        },
        # Earned by the fold: the promise only means anything once he
        # knows the town does not let go.
        {
            "key": "way_out",
            "q": "If I find a way out of this town, I'll come get you "
                 "first.",
            "label": "If I find a way out, I'll come get you.",
            "avail": lambda g: g.save.flag("voice_fold_heard"),
            "once": True,
            "beats": [
                ("npc", "If you find a way out, don't tell me."),
                ("npc", "[c=dim]I tried to lie yesterday. My mouth "
                        "wouldn't.[/c]"),
            ],
        },
        {
            "key": "holding_up",
            "q": "You holding up okay, kid?",
            "beats": [
                ("npc", "I'm keeping count of things. Somebody has to."),
            ],
        },
    ],
}


# ---- Hettie (the store) ----
# The quiet resister behind the counter -- the same Hettie who keeps the
# shop open out in town. She has nothing left to sell (the shop is gutted
# of its old vendor items) -- her value is what she risks saying out loud.
# Ask-verb conversion (TODO #1 expand): her involuntary beats (the
# preacher, the memory of the girl, the paper trade) stay volunteered
# one-shots ahead of the menu; the old visit ladder is now questions the
# PI chooses to put to her.


def _hettie_saw_photo(game):
    game.save.set_flag("hettie_saw_photo", True)


def hettie_on_leave(game):
    """Her old closing beat, kept as the one-time last word: she has
    already said more than is safe."""
    if game.save.flag("hettie_farewell_hook"):
        return None
    game.save.set_flag("hettie_farewell_hook", True)
    return [
        ("npc", "(She shakes her head, just slightly. She has said too "
                "much already.)"),
    ]


HETTIE_CONVO = {
    "id":    "hettie",
    "name":  "Hettie",
    "voice": "blip_high",
    "pi_voice": "blip_soft",
    "prompt": "Hettie keeps one eye on the window.",
    "leave":  "That's all for now.",
    "greet": {
        "flag": "hettie_greeted",
        "beats": [
            ("npc", "We're open. Lord knows why, but we're open."),
            ("npc", "There's nothing on the shelves worth your money. If "
                    "it's talk you want, keep your voice down. In here."),
        ],
    },
    "on_leave": hettie_on_leave,
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "A missing girl. And you came HERE after her."),
            ("npc", "[c=dim]Can't help you. Not the way you want. Shelves "
                    "are bare. Till's been empty since the new year. "
                    "Nobody buys. Nobody sells.[/c]"),
            ("npc", "I'll say this much. Then nothing. Don't go where they "
                    "tell you it's safe. I've got a family. Look around."),
        ],
        photo_beats=[
            ("npc", "(She looks. Not long. Long enough.)"),
            ("npc", "Faces come through this shop. I stopped keeping them."),
        ],
        on_photo=_hettie_saw_photo,
        # Once her volunteered memory has already named the girl, the
        # photo question is moot -- showing it after the confession would
        # earn a denial she has already outrun.
        photo_avail=lambda g: not g.save.flag("hettie_mara_memory"),
    ) + [
        # Earned by the intro: she only said "don't go where they tell
        # you it's safe" to a man who told her what he is.
        {
            "key": "safe",
            "q": "You said don't go where they tell me it's safe. Who is "
                 "'they'?",
            "label": "Who is 'they'?",
            "avail": lambda g: g.save.flag("convo_hettie_intro_asked"),
            "beats": [
                ("npc", "You haven't gone quiet. Like the others. Good. "
                        "Then listen once."),
                ("npc", "[c=dim]Don't trust the easy ones. The first to "
                        "make peace, they went the soonest.[/c]"),
                ("npc", "That's the whole answer you're getting to that."),
            ],
        },
        # Opens once she has seen the photograph and swallowed the lie
        # (or already volunteered the memory): the counter remembers its
        # customers, and he is not the first to come asking.
        {
            "key": "others",
            "q": "You've had people ask after faces before me. Haven't you?",
            "label": "Others came asking before me.",
            "avail": lambda g: (g.save.flag("hettie_saw_photo")
                                or g.save.flag("hettie_mara_memory")),
            "beats": [
                ("npc", "I sold to the girl too. And the ones before her."),
                ("npc", "[c=dim]None of them came back to buy again. "
                        "You're the first.[/c]"),
            ],
        },
        # Earned by the fold: he only asks about a way OUT once a local
        # has told him there isn't one (the looping roads).
        {
            "key": "way_out",
            "q": "If there were a way out of this town, would you tell me?",
            "label": "Is there a way out?",
            "avail": lambda g: g.save.flag("voice_fold_heard"),
            "beats": [
                ("npc", "(She glances at the door before she speaks.)"),
                ("npc", "If you find the way out. The real one. You don't "
                        "owe this town a goodbye. Just go."),
            ],
        },
    ],
}


def hettie_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "store_owner")
    # The resister registers the resister-who-spoke being killed. Fires
    # once, on the first visit after the player has FOUND the body (never
    # before -- the doom flag latches while Crane still stands at his
    # lectern), and only if we've already met her -- it would be too
    # personal for first contact.
    if (save.flag("preacher_body_seen")
            and not save.flag("shop_preacher_noticed")
            and save.flag("hettie_greeted")):
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
    if (save.flag("hettie_greeted")
            and not save.flag("hettie_mara_memory")
            and game.player.inventory.has("mom_notebook")):
        save.set_flag("hettie_mara_memory", True)
        game.dialog.show([
            "Your girl. I'll tell you the one thing I know that's "
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
    if (save.flag("hettie_greeted")
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
    from ui.conversation import open_conversation
    open_conversation(game, npc, HETTIE_CONVO)


# ---- The Sheriff: Hollis Vane ----
# Ask-verb conversion (TODO #1 expand; the trust/despair arc itself is
# ticket #2a and slots in on top of this later). A LOCAL, born here, the
# last holdout, the town's one real investigator (NARRATIVE §4). Hopeful
# but mistrusting: the PI is one more outsider who drove in, the exact
# profile of every cultist, so he watches first. He did NOT kill the car
# (the fold did) and he carries the plain truth about it; the badge is
# just clothing now, and he keeps wearing it.


def _vane_car_told(game):
    """The car answer is a fold account (looping roads, nothing with an
    engine leaves). File the PI's fold note WITHOUT the chained narrator
    reflection -- the exchange carries the reflection as its own closing
    beat, and the conversation owns the float's on_complete chain."""
    if hasattr(game, "_fold_mentioned"):
        game._fold_mentioned("Sheriff Vane", reflect=False)


def vane_on_leave(game):
    """A last word the first time the PI walks out of the office. The
    holdout's hope, said sideways. Fires once."""
    if game.save.flag("vane_farewell_hook"):
        return None
    game.save.set_flag("vane_farewell_hook", True)
    return [
        ("npc", "Hey. If you do find her, don't bring her by the office. "
                "There's no report worth filing anymore."),
        ("npc", "Just get her out. If you find a way that works, that is. "
                "And then you come tell me what it was."),
    ]


VANE_CONVO = {
    "id":    "vane",
    "name":  "Sheriff Vane",
    "voice": "blip_gruff",
    "pi_voice": "blip_soft",
    "prompt": "Vane waits you out, thumbs in his belt.",
    "leave":  "That's all for now.",
    "greet": {
        "flag": "vane_greeted",
        "beats": [
            ("npc", "Sheriff Vane. That's the whole welcome I've got left."),
            ("npc", "Nobody comes up that north road anymore. Then you. "
                    "So you'll forgive me if I look at you a while before "
                    "I decide anything."),
        ],
    },
    "on_leave": vane_on_leave,
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "A detective. Hired and paid, all the way up here."),
            ("npc", "The ones who came before you walked in friendly and "
                    "smiling too. Every last one of them. You understand "
                    "my position."),
            ("pi", "If I were one of them, would I be standing in the "
                   "law's office announcing myself?"),
            ("npc", "No. No, they never had questions. That's the one "
                    "thing you've got going for you."),
            ("npc", "[c=dim]I'd head home if I were you. I'm supposed to "
                    "say that.[/c]"),
        ],
        photo_beats=[
            ("npc", "(He takes it to the window light and works it corner "
                    "to corner, a lawman's look.)"),
            ("npc", "I can't put a day or a door to her. The new folk came "
                    "in numbers and they keep to their own. She'd have "
                    "been one of them."),
            ("npc", "They filled the school, the barn, the lodge. Then one "
                    "night those rooms were empty, all at once. Wherever "
                    "your girl is, that's the direction. I can't tell you "
                    "where it GOES."),
            ("pi", "[c=dim]More of an answer than anyone else in this "
                   "town has risked. He watched those rooms. He is still "
                   "working it.[/c]"),
        ],
    ) + [
        {
            "key": "car",
            "q": "My car died at the lodge steps the night I drove in. It "
                 "won't turn over now.",
            "label": "My car died the night I drove in.",
            "on_ask": _vane_car_told,
            "beats": [
                ("npc", "Won't start. Won't ever. Nothing with an engine "
                        "leaves Brimley."),
                ("pi", "Engines don't all quit at once. Somebody got to it."),
                ("npc", "Nobody touched your car. I know how that sounds. "
                        "I've watched men tear three trucks down to the "
                        "block hunting the part that failed. There is no "
                        "part."),
                ("npc", "[c=dim]It's the town.[/c]"),
                ("pi", "[c=dim]He said it flat. Like weather. A town does "
                       "not talk that way about nothing. So.[/c]"),
            ],
        },
        {
            "key": "town",
            "q": "What happened to this town, Sheriff?",
            "label": "What happened to this town?",
            "beats": [
                ("npc", "I was born here. So was my dad."),
                ("npc", "They started showing up in the summer. The new "
                        "ones. Polite folks. After a while the road "
                        "stopped going anywhere."),
                ("npc", "[c=dim]I tell people to leave. I haven't been "
                        "able to in months.[/c]"),
            ],
        },
    ],
}


def sheriff_dialogue(game, npc):
    """The Sheriff -- Hollis Vane, the last holdout (NARRATIVE §4). The
    murder he can't report stays a VOLUNTEERED one-shot ahead of the
    menu, gated on the player having FOUND the body on the riverbank
    (preacher_body_seen) and on having met him -- he can never announce
    the killing before it is found, and never as a first impression.
    Everything else is the organic ask verb (VANE_CONVO)."""
    save = game.save
    _cult_tell(game, "sheriff")
    if (save.flag("preacher_body_seen")
            and not save.flag("vane_preacher_noticed")
            and save.flag("vane_greeted")):
        save.set_flag("vane_preacher_noticed", True)
        game.dialog.show([
            "They killed the preacher.",
            "He named them from his pulpit. Then he walked down to the "
            "water to fetch his flock home. They left him on the bank "
            "for us to find.",
            "[c=dim]I didn't write a report. Who would I send it to.[/c]",
            "[c=dim]He doesn't say the Reverend's name. You realize "
            "nobody in town has.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
        return
    from ui.conversation import open_conversation
    open_conversation(game, npc, VANE_CONVO)


# ---- The Clerk: Mr. Sable ----
# The organic ask-verb, piloted on Sable (TODO #1). The menu options ARE
# the PI's own spoken lines; picking one plays a back-and-forth over their
# heads. Sable checked the PI in the night before the game opens
# (NARRATIVE §3), so every exchange is a host RESUMING an acquaintance,
# never an introduction. He sets the tone for the whole town: the
# smiling, pro-newcomer host who DOES NOT give the girl up. He deflects the name, folds Mara in with "the new
# folk," and points the suspicion the wrong way -- at the "unfriendly" old
# families -- which is the exact trap the game punishes (the warm ones are
# the cult; NARRATIVE §4, Hettie's "don't trust the easy ones"). He is the
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
        "Sable kept an envelope under the register. Since the winter. Handed "
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
            ("npc", "Up early. You came in late off the north road. I put "
                    "you down in the book as staying a while."),
        ],
    },
    "on_leave": sable_on_leave,
    "exchanges": [
        {
            "key": "mara",
            "label": "I'm looking for someone.",
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
            "label": "About that cellar of yours.",
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
        # rite (it is mid-April now -- THREE months; NARRATIVE §1). The PI has
        # the dates from his own case; Sable downplays a supernatural seal as
        # ordinary winter and never lets the word "trapped" near it.
        {
            "key": "sealed",
            "label": "Nothing leaves this town. Why?",
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
            "label": "My car won't start.",
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
            "label": "Nobody ever signs out.",
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
            "label": "When did she change?",
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
            "label": "The road out brought me back.",
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
            "label": "You've been holding something for me.",
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
    """The Lodge Clerk, Mr. Sable -- the smiling trap-keeper (NARRATIVE §4).
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


def preacher_body_examine(game, npc):
    """E on the Preacher's remains at the riverbank: take his cross + log
    evidence #4 once. (2026-07 rework: the doom sends Crane out of his
    church to talk his flock home; the body is found by the river in
    Brimley, never on the church floor.)"""
    if game.save.flag("cross_taken"):
        game.dialog.show(["What's left of him. The flies have found it."],
                         speaker="", voice="blip_soft", portrait="narrator")
        return
    game.save.set_flag("cross_taken", True)
    game.player.inventory.add("cross", 1)
    game.audio.play("pickup_rare", 0.7)
    game.audio.play("low_pulse", 0.5)
    _evidence(game, "the_preacher", [
        "The Preacher. He named them from his pulpit, every Sunday. Then "
        "he went down to the river after them, believing a flock can be "
        "talked home.",
        "They opened him for it and left him on the bank, where the whole "
        "town could find him.",
        "His collar's still white. His cross lies in the mess. You take it.",
        "[c=dim]This is what naming them costs.[/c]",
    ])
