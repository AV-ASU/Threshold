"""All NPC dialogue functions.

The spoken lines are final, lore-bearing copy: each NPC reacts to the
case (the Blaine girl, the well, the cult). The PRINCIPALS (Sable, Vane,
Hettie, Toby, Crane) AND the Brimley chorus (Old Pell, Mrs. Calder,
Royce, Garrick) all speak through the organic ask verb now
(ui/conversation `*_CONVO` data, TODO #1): the menu options are
the PI's own spoken lines, everyone leads with the two guaranteed openers
(`_opener_exchanges`: introduce-as-PI + Mara's photograph), and each
NPC's story-critical one-shots (the witness account, the memory of the
girl, the murder he can't report, the paper trade, the town-reaction
beats) still VOLUNTEER themselves ahead of the menu. Other state
reactivity comes from per-NPC flag gates; scenes/brimley.py
_brimley_voice survives only for the doorstep Hettie cameo.
`escalate` still exists but now has NO call sites -- kept only in case
visibility-tiered copy is ever authored. Evidence beats are surfaced
through `_evidence`; only the five in `CANONICAL_EVIDENCE` count toward
the King-gate and the visibility floor.
"""
import random


# Mara's trail -- the ONLY evidence, and the whole point of the case
# (NARRATIVE.md §6, DESIGN.md §9). Each is a carryable, self-evident thing
# that is HERS: felt it (the journal) -> did it (the dig) -> why (the
# letter). The three SURFACE beats (receipt, record, journal) keep the
# Act-1 threat ramp reachable above ground (the cult wakes at 1, the King
# arms at 3); the two DEEP beats run past the gate. Mara herself is PROOF,
# never a filed beat; the Ledger, the Preacher and the Pallid Mask left the
# count (they file as notes / the Mask is the keystone item). ONLY these
# five count toward the King-gate and the visibility floor; every other
# `_evidence(...)` call is flavor narration (or a case NOTE with
# note=True). Each value is the floor it adds, rising along the trail.
CANONICAL_EVIDENCE = {
    "maras_receipt":  0.08,   # surface: her store tab (Hettie's shop)
    "maras_record":   0.12,   # surface: her booking slip (Vane's office)
    "maras_journal":  0.16,   # surface: her journal (the barn) -- fires the dream
    "maras_dig":      0.20,   # deep: the Sign in her own hand (the Scriptorium)
    "maras_room":     0.24,   # deep: her unsent letter (her cell)
}


def _evidence(game, name, content, weight=None, show=True, note=False,
              quiet=False):
    """Surface a one-shot narrator line. If `name` is one of the CANONICAL
    beats it is ALSO logged as evidence -- counting toward the King-gate and
    raising the visibility FLOOR by its canonical weight (the "knowing dooms
    you" engine), and firing the notebook-scribble toast. A non-canonical
    name with `note=True` files the lines as a case NOTE instead (the
    Ledger, the Preacher: real discoveries that are not Mara, so they keep a
    home in the notebook without touching the gate -- NARRATIVE §6). Any
    other name is just flavor narration. Gated by a per-name flag so a beat
    never re-fires.

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
            log.append({"name": name,
                        "lines": [_strip_markup(x) for x in lines],
                        "weight": CANONICAL_EVIDENCE[name]})
            game.save.set_arg("evidence", log)
            if not quiet and hasattr(game, "_flash_notebook"):
                game._flash_notebook(name)    # corner scribble: you wrote it down
            if not quiet and hasattr(game, "audio"):
                game.audio.play("evidence_added", 0.7)
            # Save on evidence pickup (play-notes): the clue IS the
            # checkpoint, not a trip back to the cot.
            if hasattr(game, "_autosave"):
                game._autosave()
    elif note:
        # Not Mara's, so not case-evidence -- but a real find; keep it in
        # the notebook as a case NOTE (never counts toward the gate).
        _log_note(game, name, lines)
    # A discovery can point the PI back at someone he's met; those
    # interior lines ride the discovery's own narration so it reads as
    # one beat (and files their case notes). Collected REGARDLESS of
    # `show` -- a silently-filed beat (the journal reads from the kit)
    # must still land its nudges, or the case stalls without a voice
    # (the R-gate stall finding). Defined after this fn; safe at call
    # time.
    # quiet=True (the journal walk-over pickup): log + autosave for the gate,
    # but surface NOTHING -- no scribble, no nudges, no caption. No note pops
    # before the PI has read the thing (play-notes).
    extra = [] if quiet else _collect_revisit(game, name)
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


def _cult_tell(game, npc_key):
    """No-op kept for signature compatibility. (Formerly surfaced a
    one-shot sensory notice; the story text has been removed.)"""
    return


def _strip_markup(text):
    """Drop dialog markup tags ([c=dim] ... [/c], [f=], [s=], [w=], ...)
    from a string, mirroring how parse_dialogue consumes them, so text
    STORED to the casebook (notes + evidence) is plain. The Case card
    renders through a non-markup wrapper, so any tag left in a stored
    line prints literally (the '[c=dim]' leak the player saw)."""
    out = []
    i = 0
    while i < len(text):
        if text[i] == "[":
            end = text.find("]", i)
            if end != -1:
                i = end + 1
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _log_note(game, key, lines):
    """File a PI case NOTE once, keyed by name. NOTES are the interior
    voice, shown in the notebook after the clues; they must NEVER go in
    `evidence` (that count drives the King-gate and the visibility floor).
    Fires the corner scribble like every other case-book write, so the
    player always gets the one quiet 'noted that' tell (the Ledger, the
    Preacher, etc. used to file silently -- a bug)."""
    notes = game.save.arg("notes", [])
    if isinstance(notes, list) and not any(
            isinstance(e, dict) and e.get("name") == key for e in notes):
        notes.append({"name": key, "lines": [_strip_markup(x) for x in lines]})
        game.save.set_arg("notes", notes)
        if hasattr(game, "_flash_notebook"):
            game._flash_notebook(key)


# The per-discovery revisit nudges ("...I should go back and ask him") were
# CUT (play-notes: the game should not do the player's thinking -- the
# follow-up QUESTION still opens on the same evidence in each NPC's
# conversation, so nothing is lost but the hand-holding append). The only
# survivor is the act-break desk pointer below, which is progression signage,
# not a revisit nudge.


def _collect_revisit(game, name):
    """For a just-fired discovery, return the act-break desk pointer (the
    Invitation signpost) if the readiness line is crossed. The old
    per-discovery revisit nudges were cut (play-notes)."""
    return _ready_for_the_desk(game, name)


def _ready_for_the_desk(game, name):
    """When the PI crosses the readiness line (3 canonical beats) on the
    surface, still without the Invitation, nudge him back to Sable -- so the
    act break is signposted, not a silent 'walk back to the desk'. Fires
    once, as long as Sable has not yet handed it over. (Once the PI is
    underground he already holds it, so this cannot fire there.) C16: the
    pointer no longer requires having greeted Sable first -- the PI checked
    in at that desk on arrival, so the nudge reads for any player who
    crosses the line without the Invitation.)"""
    if (name not in CANONICAL_EVIDENCE
            or game._evidence_count() != 3
            or game.save.flag("rite_envelope_given")
            or game.player.inventory.has("rite_envelope")
            or game.save.flag("nudged_ready_for_desk")):
        return []
    game.save.set_flag("nudged_ready_for_desk", True)
    lines = [
        "[c=dim]The clerk has been holding something for me since I walked "
        "in.[/c]",
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

_INTRO_Q = ("I'm a private investigator, out of Minneapolis. I was hired "
            "to find a woman named Mara Blaine. She was last heard from "
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


# ---- The four-tier PI register (TODO #22c) ----
# The world rot lives in the INVESTIGATOR now, not the town (NARRATIVE §2): the locals stay exactly themselves, and what deteriorates
# is the man hearing them. It surfaces ONLY as the PI's framing of a
# conversation -- the question menu's opening line -- never as a word the NPC
# says. Four tiers, keyed to how far up Mara's trail he has climbed
# (evidence count): 0 clear and professional / 1-2 unsettled / 3 he knows /
# 4+ past return. (The engine already renders a callable prompt(game); Vane's
# mood prompt proves it.)
def _pi_tier(game):
    if game is None or not hasattr(game, "_evidence_count"):
        return 0
    ev = game._evidence_count()
    if ev >= 4:
        return 3
    if ev >= 3:
        return 2
    if ev >= 1:
        return 1
    return 0


# The PI's own interior weather, composed onto a principal's framing line.
# Empty at tier 0 (he is a professional doing a job); it deepens from there.
# The NPC's words never change; only this framing does.
_PI_WEATHER = (
    "",
    " Something in this town isn't sitting right, and I can't put a name to "
    "it yet.",
    " I know what's under this town now. It's work, keeping a plain face "
    "plain while I listen.",
    " I've been down where the road ends. Ordinary's a thing I decide to "
    "believe now.",
)


def _pi_framing(base):
    """Wrap a static framing line into a four-tier PI-register callable (TODO
    #22c): the base observation at tier 0, the same observation plus the PI's
    deepening interior weather after. The locals stay ordinary; the man
    reading them is the one who rots."""
    def _framing(game):
        return base + _PI_WEATHER[_pi_tier(game)]
    return _framing


# ---- The Preacher: Reverend Asa Crane ----
# Ask-verb conversion (TODO #1 expand), carrying the ticket's pilot
# choice: his doom is no longer an automatic visit counter. The flock
# exchange ends on a real fork -- press him and he takes his naming to
# where they can hear it (preacher_doomed; the church swaps him for his
# remains on the next entry, files a case note), or hold him back and he banks
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


def _crane_prompt(game):
    """The framing line reads the fork the way his tableau pose does: at
    rest he waits, hands folded; once the press has latched
    (preacher_doomed) he is done waiting. Composes the PI's four-tier
    weather like every principal framing (_pi_framing)."""
    base = ("Crane stands square at the lectern, done waiting."
            if game.save.flag("preacher_doomed")
            else "Crane waits, hands folded over the lectern.")
    return base + _PI_WEATHER[_pi_tier(game)]


CRANE_CONVO = {
    "id":    "crane",
    "name":  "Rev. Crane",
    "voice": "blip_low",
    "pi_voice": "blip_soft",
    "prompt": _crane_prompt,
    "leave":  "That's all for now.",
    "greet": {
        "flag": "crane_greeted",
        "beats": [
            ("npc", "Another new face. Strangers off the highway were all "
                    "that came to Brimley this past year, more every "
                    "season. And not one of them left."),
        ],
    },
    "on_leave": crane_on_leave,
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "I never trusted it. They arrived too easy, like "
                    "something held the door. Then they went quiet, "
                    "drifted out to the corn, and they didn't come back."),
            ("npc", "A young woman came through in the fall. Bright "
                    "thing, full of questions, like you. She's one of "
                    "them now, whatever they are. That who you're after?"),
        ],
        photo_beats=[
            ("npc", "(He looks, and his mouth goes tight.)"),
            ("npc", "I know her. She sat my pews twice, early on, right "
                    "at the back. I remember thinking, there's one with "
                    "her eyes still open."),
            ("npc", "[c=dim]Then she stopped coming. They all stopped.[/c]"),
        ],
    ) + [
        # Earned by the intro: his "they arrived too easy" answer is what
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
                        ("pi", "[c=dim]For now. He's only banking the fire.[/c]"),
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
            "They heard it, though. Down that road, something always does.",
        ], speaker="Rev. Crane", voice="blip_low", portrait="preacher")
        return
    # The organic conversation, PRESENTED as a frozen close-up TABLEAU (#2b,
    # the Sable/Vane/Hettie precedent): the chancel behind his lectern in
    # candled dusk, and his HANDS reading the fork the way the framing line
    # does (folded and waiting, or gripping the lectern once the press has
    # latched). The bell one-shot above still volunteers as a plain beat
    # first; the next press opens the close-up.
    game._open_crane_tableau(npc)


# ---- The Kid: Toby ----

def toby_dialogue(game, npc):
    """Toby -- innocent witness (NARRATIVE §4). He FOLLOWED the night
    procession down the river to the cult's dug-open ground and saw them go
    below -- the sole witness of where they went. His account does two jobs
    (NARRATIVE §4, D rework): it poses the descent question (they went down a
    way no one can follow now -- the grove is fold-hidden) and it SEEDS THE
    SCHOOL -- the room the Invitation names and the chalk-door rite reopens.
    It is EARNED, never volunteered: he gives it when the PI holds Mara's
    photograph out (the `photo` exchange below), not as a cold greeting -- a
    kid has no way to know the case on sight (only Sable ever met the PI).
    The one OBJECT he gives is the bear (TODO #22b), and only to the man he
    trusts: once the PI has heard him out AND reassured him, Toby brings out
    the only toy in town on his own."""
    save = game.save
    # The bear (22b). You cannot interrogate it out of him: the PI is numb
    # everywhere but soft with children, and that trait is the key. Once he
    # has told the PI what he saw (`toby_told`, the photo) AND been
    # reassured (`convo_toby_holding_up_asked`, the "you holding up" promise
    # -- his one soft spot), he LENDS it: Mara's, a loan for a reunion the
    # PI already knows can't happen. OPTIONAL, never evidence, never gates.
    # The tag reads the boy's name; MARA never says it.
    if (save.flag("toby_told")
            and save.flag("convo_toby_holding_up_asked")
            and not save.flag("toby_lent_bear")
            and not game.player.inventory.has("bear")):
        save.set_flag("toby_lent_bear", True)
        game.player.inventory.add("bear", 1)
        game.audio.play("pickup_rare", 0.7)
        game._log_note("the_bear", [
            "The kid put a stuffed bear in my hands. Homemade, a name sewn "
            "on the tag. Said the girl in the photo gave it to him, that "
            "she couldn't keep it and couldn't throw it out.",
            "He asked me to give it back to her, if I find her. I said I "
            "would. I have carried worse lies than that one lighter.",
        ])
        game.dialog.show([
            "[c=dim]He digs in his coat and holds something out with both "
            "hands. A stuffed bear, worn soft, a name stitched on the "
            "tag.[/c]",
            "The lady gave it to me. The one in your picture. She said she "
            "couldn't keep it and she couldn't throw it out.",
            "It's the only toy in the whole town. If you find her... give "
            "it back? She should have it.",
            "[c=dim](You take a bear from a boy, and you promise. You do "
            "not let yourself read the name on the tag. Not yet.)[/c]",
        ], speaker="Toby", voice="blip_kid", portrait="toby")
        return
    # The organic conversation, PRESENTED as a frozen close-up TABLEAU (#2b,
    # the last principal seat): the one almost-normal room in Brimley, his
    # drawings taped up, the window on the corn line he watches (the framing
    # line made pose). The room carries what the talk earns: the procession
    # drawing goes up once he has told what he saw, and his worried brows
    # level once the PI has promised. The bear one-shot above still
    # volunteers as a plain beat first; the next press opens the close-up.
    game._open_toby_tableau(npc)


# Ask-verb conversation: Toby volunteers nothing cold (a kid can't know the
# case on sight -- only Sable ever met the PI). His witness account is
# EARNED -- it rides the `photo` exchange, given when the PI holds Mara's
# picture out. The menu is what the PI chooses to ask a child; the old
# visit-ladder lines are now his answers.
# ---- The newspaper choice (TODO #2): one copy, five doors ----
# The PI carried in the April 14 paper, the first word from outside since
# the mid-January seal, and there is ONE copy. Who he gives it to yields
# different, incommensurable payoffs, and the town feels the allocation
# (mood, never a meter). The one-copy economy is the inventory itself:
# every paper exchange gates on still carrying it, so the first give
# closes the rest. Every allocation files a case NOTE, never evidence
# (the fences). Vane's give (the trap; _vane_paper_given below) rides
# the same helper.


def _paper_given(game, who, note_name, note_lines):
    """Spend the one copy: remove it, record the recipient, file the
    allocation note (the toast is the tell)."""
    game.player.inventory.remove("newspaper", 1)
    game.save.set_arg("paper_given", who)
    game._log_note(note_name, note_lines)


def _royce_paper_given(game):
    """Royce: escape-hope. He pays in his hoarded flashlight batteries
    and the one road that held longest (testimony, fallible)."""
    game.player.inventory.add("batteries", 1)
    game.audio.play("pickup", 0.6)
    _paper_given(game, "royce", "paper_royce", [
        "Spent the paper on Royce. He paid in hoarded flashlight "
        "batteries and the one road that held longest: river road "
        "south, two bends past the bridge.",
        "His account, not mine. But he would know.",
    ])


def _pell_paper_given(game):
    """Old Pell: mercy, no item. He starts marking days again."""
    _paper_given(game, "pell", "paper_pell", [
        "Gave Old Pell the paper. He said he'd pencil today into his "
        "calendar. He'd stopped marking days at all.",
        "No trade. Didn't want one.",
    ])


def _toby_paper_given(game):
    """Toby: mercy. The funny pages; the front page stays out of his
    house."""
    _paper_given(game, "toby", "paper_toby", [
        "Gave the kid the funny pages. His mother reads over his "
        "shoulder, and she doesn't hum while she's reading.",
        "Best price I got for it all day.",
    ])


def _sable_paper_given(game):
    """Sable: the null, and the tell (NARRATIVE 4: his want was never
    the outside). No reward. The chill is the payoff."""
    _paper_given(game, "sable", "paper_sable", [
        "Left the paper with Sable. He squared it on the desk, "
        "unopened, and thanked me for the house.",
        "The whole town is starving for word from outside. He is not.",
    ])


def _hettie_trade_quiet(game):
    """Hettie's barter, mechanics only (the caller narrates: the
    volunteered offer closes with a stage page, the menu exchange with
    its own beats). One load of cartridges across the counter."""
    game.save.set_flag("newspaper_traded", True)
    game.player.inventory.add("pistol_ammo", 6)
    game.audio.play("pickup_rare", 0.7)
    _paper_given(game, "hettie", "paper_hettie", [
        "Traded the paper across Hettie's counter for a load of "
        "cartridges.",
        "She was reading it before I reached the door.",
    ])


TOBY_CONVO = {
    "id":    "toby",
    "name":  "Toby",
    "voice": "blip_kid",
    "pi_voice": "blip_soft",
    "prompt": _pi_framing("Toby watches the corn line while I think."),
    "leave":  "That's all for now.",
    "greet": {
        "flag": "toby_greeted",
        "beats": [
            ("npc", "You're not from here. I'd have seen you before."),
            ("npc", "What are you doing, mister?"),
        ],
    },
    "exchanges": _opener_exchanges(
        on_photo=lambda g: g.save.set_flag("toby_told", True),
        intro_beats=[
            ("npc", "A detective. For real? Like on the TV."),
            ("npc", "Nobody here would hire one. Asking questions is what "
                    "you stop doing, if you live here."),
            ("pi", "Well. I'm asking. And I don't mind talking to you."),
            ("npc", "I know. Don't tell my mom."),
        ],
        photo_beats=[
            ("npc", "That's her. She came in after all the others did. The "
                    "last one. Folks thought the strangers were done coming, "
                    "and then her car came up the road alone."),
            ("npc", "They slept all over then. The barn. The lodge. My "
                    "school too, in rows, right where we do our letters."),
            ("npc", "Then one night they all went down. A whole line of "
                    "them in the dark, along the river to where the ground "
                    "is broke open. I followed."),
            ("npc", "They climbed into it. Under the field. She never came "
                    "back up. None of them did. I saw where they go."),
            ("npc", "You can't walk there. I looked in the daytime, and the field just put me back."),
            ("npc", "[c=dim]Keep her picture put away. Some of them look at "
                    "what you carry.[/c]"),
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
        # The promise. Only after he has confided what he saw (`toby_told`,
        # set by the photo exchange): you do not reassure a scared kid about
        # a thing he has not told you, and the weight of it is that it is the
        # man who listened. The player knows what the PI does not: nobody
        # comes back for anybody in this town.
        {
            "key": "holding_up",
            "q": "You holding up okay, kid?",
            "avail": lambda g: g.save.flag("toby_told"),
            "once": True,
            "beats": [
                ("npc", "Do you know what's wrong here, mister? Nobody will "
                        "tell me."),
                ("pi", "Not all of it. But I'm going to find out, and I'm "
                       "going to make it stop."),
                ("npc", "Am I gonna be okay?"),
                ("pi", "You're gonna be okay. I promise. When I'm done, I'll "
                       "come back for you."),
                ("npc", "[c=dim]Okay. I believe you.[/c]"),
            ],
        },
        # The funny pages (TODO #2, mercy). One copy; giving a kid the
        # comics spends the town's only word from outside, and that is
        # the choice.
        {
            "key": "paper",
            "q": "There's a fat run of funnies in yesterday's paper. You "
                 "want them?",
            "label": "I brought the funny pages.",
            "once": True,
            "avail": lambda g: (g.save.flag("convo_toby_intro_asked")
                                and g.player.inventory.has("newspaper")),
            "on_ask": _toby_paper_given,
            "beats": [
                ("npc", "The funnies? Whole ones?"),
                ("pi", "[c=dim](You fold the front page under and away, "
                       "and hand him the back of the paper.)[/c]"),
                ("npc", "(He spreads it flat on the table with both "
                        "hands, like a map of somewhere good.)"),
                ("npc", "Calvin's still in it. He didn't stop."),
                ("npc", "Can I keep it? Mom reads over my shoulder when "
                        "I've got something. She doesn't hum when she's "
                        "reading."),
                ("pi", "[c=dim]He gets the funnies. The front page stays "
                       "out of this house.[/c]"),
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


# Mara's store tab -- surface evidence (the receipt; NARRATIVE §6,
# DESIGN.md §9). WORLD-PERSISTENT: reachable whether Hettie is alive or
# dead, so killing her can never soft-lock the descent. Two ways in funnel
# HERE so it can never double-fire: Hettie's WARM handover (her Mara-memory
# beat, when she's alive -- show her the photo) and the spike FALLBACK (a
# walk-over pickup the shop's on_update_fn opens only once Hettie is dead).
def grant_receipt(game):
    if game.save.flag("evidence_maras_receipt"):
        return
    game.player.inventory.add("receipt", 1)
    game.audio.play("pickup_rare", 0.7)
    # Files silently and reads from the item (its desc carries the tab); the
    # log excerpt is the case entry.
    _evidence(game, "maras_receipt", [
        "A store tab off Hettie's spike, headed 'M. Blaine' in her hand.",
        "Matches, canned milk, the same short list run down most of a "
        "year. The staples a resident buys, week on week.",
        "She lived here.",
    ], show=False)
    if hasattr(game, "show_notice"):
        game.show_notice("Her tab from the shop.")


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
    "prompt": _pi_framing("Hettie keeps one eye on the window."),
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
                ("npc", "Don't trust the easy ones. The first to "
                        "make peace, they went the soonest."),
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
                ("npc", "None of them came back to buy again. "
                        "You're the first."),
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
        # TODO #2: the trade she offered, reopenable while the copy is
        # still in the coat (declining the counter offer is not a
        # forever-no). Quiet mechanics; the beats narrate.
        {
            "key": "paper",
            "q": "That trade you offered. The paper for what's under the "
                 "till.",
            "label": "About that trade.",
            "once": True,
            "avail": lambda g: (g.save.flag("hettie_paper_offered")
                                and not g.save.flag("newspaper_traded")
                                and g.player.inventory.has("newspaper")),
            "on_ask": _hettie_trade_quiet,
            "beats": [
                ("npc", "(Her hand is under the counter before you finish "
                        "saying it.)"),
                ("npc", "Counter. Now. Before I think better of what I "
                        "keep under here."),
                ("pi", "[c=dim]One load of cartridges across the counter. "
                       "She's already reading the front page.[/c]"),
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
    # A faint memory of the girl herself (TODO #6): fires once the PI has
    # SHOWN HER MARA'S PHOTOGRAPH (the asking got real, and it is how you get
    # her tab now -- NARRATIVE §6: show the photo, they react and hand it
    # over; play-notes). Mara passed through Brimley for a season before she
    # went below; Hettie knew her the way a counter knows anyone. NARRATIVE
    # §2: she does NOT know Walter; this is the girl, never the family.
    if (save.flag("hettie_greeted")
            and not save.flag("hettie_mara_memory")
            and save.flag("hettie_saw_photo")):
        save.set_flag("hettie_mara_memory", True)
        _lines = [
            "Your girl. I'll tell you the one thing I know that's "
            "worth the telling.",
            "She used to come in here. Matches, canned milk. Counted her "
            "change twice, every time, like it mattered. Sad around the "
            "eyes, and polite with it.",
            "Then one day past the new year she set her basket "
            "down half filled and walked out smiling. Left the basket "
            "on the counter. I never saw her again.",
            "[c=dim]It was the smiling I minded.[/c]",
        ]
        # Her warm handover of the store tab (surface evidence), only if
        # the PI has not already lifted it off the spike himself. The tab
        # is world-persistent either way (grant_receipt is flag-gated).
        if not save.flag("evidence_maras_receipt"):
            _lines.append(
                "[c=dim]She works a curled slip off the spike by the till "
                "and sets it on the counter, turned toward you. Her tab for "
                "the girl. Matches, canned milk, week on week.[/c]")
        game.dialog.show(_lines, speaker="Hettie", voice="blip_high",
                         portrait="hettie")
        grant_receipt(game)
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
            and not save.flag("hettie_paper_offered")
            and not save.flag("newspaper_traded")
            and game.player.inventory.has("newspaper")):
        # TODO #2 rework: she still NOTICES and makes the offer the moment
        # she sees the date, but the trade is the PLAYER'S call now (one
        # copy, five doors). Declining keeps the offer open as a menu
        # question (the `paper` exchange below) for as long as the copy
        # is still in the coat.
        save.set_flag("hettie_paper_offered", True)

        def _offer():
            def _pick(idx):
                if idx == 0:
                    _hettie_trade_quiet(game)
                    game.dialog.show([
                        "[c=dim]One load of cartridges across the "
                        "counter. She's already reading yesterday's news "
                        "like a letter from someone she'd given up "
                        "on.[/c]",
                    ], speaker="Hettie", voice="blip_high",
                        portrait="hettie")
                else:
                    game.dialog.show([
                        "(She looks at your pocket a beat longer, then "
                        "lets it go.) Suit yourself. The shelf keeps.",
                    ], speaker="Hettie", voice="blip_high",
                        portrait="hettie")
            game.dialog.show_choice(
                "The offer sits on the counter.",
                ["Trade the paper.",
                 "Keep it. I've got somewhere for it."],
                _pick, speaker="", voice="blip_soft", portrait="narrator")
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
        ], speaker="Hettie", voice="blip_high", portrait="hettie",
            on_complete=_offer)
        return
    # The organic conversation, PRESENTED as a frozen close-up TABLEAU (#2b,
    # the Sable/Vane precedent): the gutted shop behind her counter, her one
    # kept bulb burning over it, and her idle glancing at the door (the
    # framing line made pose). The counter carries what the talk earns:
    # Mara's tab leaves the spike once the receipt is taken, the traded
    # newspaper lies open after the barter. The one-shots above (the
    # preacher, the memory, the trade) still volunteer as plain beats
    # first; the next press opens the close-up.
    game._open_hettie_tableau(npc)


# ---- The Sheriff: Hollis Vane ----
# The despair/hope arc (DESIGN.md §2; was TODO #2a) on top of the ask-verb conversion
# (TODO #1). A LOCAL, born here, the last holdout, the town's one real
# investigator (NARRATIVE §4). Hopeful but mistrusting: the PI is one
# more outsider who drove in, the exact profile of every cultist, so he
# watches first. He did NOT kill the car (the fold did) and he carries
# the plain truth about it; the badge is just clothing now, and he keeps
# wearing it.
#
# His FATE is player-driven: a hidden despair/hope ledger (vane_despair,
# the VANE_* config block) that the player never sees as a number, only
# as his mood. Sharing a real discovery with him is the one hope act,
# and it is ALSO the trust that opens his investigation thread (the
# blind-cultist how) -- the same act builds the rapport that makes his
# fall hurt, and holds him back from it. The newspaper (TODO #2) is its
# exact inverse: his break lever, +VANE_PAPER_DESPAIR. The hollow turn
# latches at VANE_HOLLOW_AT net despair (or by the NEGLECT override in
# systems/rot_mixin._vane_is_hollow); once hollow, no return -- the next
# load of his office stands the hunter up instead of the man.


def _vane_ledger(game, delta):
    """Move Sheriff Vane's hidden despair/hope ledger (DESIGN.md §2).
    Positive is despair, negative is hope. Hope banks only down to
    VANE_DESPAIR_FLOOR (real rapport is not immunity), and reaching
    VANE_HOLLOW_AT latches `vane_hollow` for good -- once hollow, no
    return, whatever hope arrives after. The office spawn gate
    (systems/rot_mixin._vane_is_hollow) reads the flag on scene load."""
    from systems.config import VANE_HOLLOW_AT, VANE_DESPAIR_FLOOR
    if game.save.flag("vane_hollow"):
        return
    net = max(VANE_DESPAIR_FLOOR,
              int(game.save.arg("vane_despair", 0)) + delta)
    game.save.set_arg("vane_despair", net)
    if net >= VANE_HOLLOW_AT:
        game.save.set_flag("vane_hollow", True)


def _vane_share(game):
    """A real discovery shared with Vane -- the trust currency and the
    hope currency in one act (DESIGN.md §2). Counts toward dodging the
    neglect override (vane_informed) and buys down despair."""
    from systems.config import VANE_HOPE_ACT
    game.save.set_arg("vane_informed",
                      int(game.save.arg("vane_informed", 0)) + 1)
    _vane_ledger(game, VANE_HOPE_ACT)


def _vane_paper_given(game):
    """The newspaper handed to Vane (TODO #2: his is a TRAP, not a
    gift). To a man who wants it all to end, the front page reads as
    permission, not hope -- the outside is dying the same death one day
    north. One copy: giving it to him means everyone else goes without
    (Hettie's cartridge trade among them)."""
    from systems.config import VANE_PAPER_DESPAIR
    _paper_given(game, "vane", "paper_vane", [
        "Gave the sheriff the paper. Kurt Cobain on the front page.",
        "He didn't look up from it again.",
    ])
    _vane_ledger(game, VANE_PAPER_DESPAIR)


def _vane_prompt(game):
    """The 'mood, not a meter' surface (DESIGN.md §2): the question menu's
    framing line reads the ledger without ever showing a number."""
    net = int(game.save.arg("vane_despair", 0))
    if net >= 2:
        return ("Vane is looking at the window, not at you. It takes "
                "him a moment to come back.")
    if net <= -1:
        return ("Vane hooks a chair out with his boot and nods at it. "
                "As close to a welcome as this office gets.")
    return "Vane waits you out, thumbs in his belt."


def _vane_car_told(game):
    """The car answer is a fold account (looping roads, nothing with an
    engine leaves). File the PI's fold note WITHOUT the chained narrator
    reflection -- the exchange carries the reflection as its own closing
    beat, and the conversation owns the float's on_complete chain."""
    if hasattr(game, "_fold_mentioned"):
        game._fold_mentioned("Sheriff Vane", reflect=False)


def _vane_how_told(game):
    """Vane's blind-cultist account is the case's one honest piece of the
    HOW (NARRATIVE §4). File it as a NOTE, never evidence."""
    _log_note(game, "the_how", [
        "[c=dim]The sheriff spent his one card. A blind man, no name, lit "
        "up with certainty, promised his own eyes by the dream once the "
        "work is finished. Sent to fetch the last holdout, and thanked "
        "him for refusing.",
        "Nobody was argued north. Each of them was promised the one thing they were starving for, and every one came gladly.[/c]",
    ])


def _vane_town_beats(game):
    """The 'what happened to this town' answer, built to Vane's lived arc: a
    dying quiet town, the summer influx of unplaceable newcomers, then the
    exits closing. The reveal that no one has left in MONTHS lands as a horror
    RECOIL the first time (before the PI has learned the seal) and as an
    assertive 'then how' from a PI who already knows -- and either way Vane,
    the last man still asking, has no how to give. Marks the fold heard on the
    first-time branch, chosen BEFORE the mark so it never skips its own recoil
    (the play-notes recoil-once rule: subsequent tellings are flat restatement,
    no fresh shock)."""
    knew = (game.save.flag("voice_fold_heard")
            or game.save.flag("crossed_a_fold"))
    beats = [
        ("npc", "Brimley was dying before any of this. Half the town gone "
                "south for work, storefronts boarded up. Some weeks the phone "
                "never rang once."),
        ("npc", "Then last summer the strangers started coming up the north "
                "road, and they didn't stop. More than we had beds for. "
                "Polite, every one. Kept to their own. Not one could tell me "
                "where they'd driven in from, or why they'd want a dead town "
                "like this."),
        ("npc", "I kept waiting on the trouble strangers bring. It never came. "
                "Something quieter did. The trucks stopped running. The mail "
                "stopped. And the road out stopped taking anybody anywhere."),
        ("npc", "You need to get out of here. We all do. No one has been able "
                "to leave in months."),
    ]
    if knew:
        beats += [
            ("pi", "Then you tell me how, Sheriff. Every road out, every "
                   "engine, a whole town that can't leave. It's not right. "
                   "How?"),
            ("npc", "You think I haven't stood right where you're standing "
                    "and asked that, every night for a year? I don't have a "
                    "how for you. Just this badge, and a list of folks I "
                    "can't help."),
        ]
    else:
        beats += [
            ("pi", "Wait. What are you saying, Sheriff? No one has left?"),
            ("npc", "Not a soul, not since the winter. They try. I tried, "
                    "more times than I'll admit to a stranger. Every road out "
                    "of Brimley turns you around and sets you back at that "
                    "well."),
            ("npc", "You'll learn that yourself soon enough. Everybody does."),
        ]
        if hasattr(game, "_fold_mentioned"):
            game._fold_mentioned("Sheriff Vane", reflect=False)
    return beats


def _vane_give_cache(game):
    """Vane hands over the office gun cabinet -- the best ammo in town, and
    EARNED, not free (DESIGN.md §2). The lawman with no deputies and no law
    left arms the one fellow investigator who brought him the truth. Sets the
    flag the office on_enter reads, and drops the cache live so the PI can
    take it while he is standing there (the gun is not required to finish, so
    gating it soft-locks nothing -- it exists to fail; DESIGN.md §1)."""
    game.save.set_flag("vane_gave_cache", True)
    scene = getattr(game, "scene", None)
    if scene is not None:
        from scenes.base import drop_ammo_cache
        drop_ammo_cache(game, scene, 13, 4, 6, "ammo_sheriff")


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
    "prompt": _vane_prompt,
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
            ("npc", "I'd head home if I were you. I'm supposed to "
                    "say that."),
        ],
        photo_beats=[
            ("npc", "(He takes it to the window light and works it corner "
                    "to corner, a lawman's look.)"),
            ("npc", "The new folk came in numbers and they kept to their "
                    "own. She'd have been one of them."),
            ("npc", "They filled the school, the barn, the lodge. Then one "
                    "night those rooms were empty, all at once. Wherever "
                    "your girl is, that's the direction."),
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
                ("pi", "[c=dim]He said it flat.[/c]"),
            ],
        },
        {
            # Vane tells the town's fall as he lived it: a dying quiet town,
            # the summer influx of unplaceable newcomers, the exits closing.
            # The "no one has left in months" reveal RECOILS the first time and
            # goes assertive-investigator once the PI already knows the seal
            # (dynamic beats, _vane_town_beats). Either way Vane has no HOW for
            # the seal (distinct from his gated recruitment "how" below).
            "key": "town",
            "q": "What happened to this town, Sheriff?",
            "label": "What happened to this town?",
            "beats": _vane_town_beats,
        },
        # The SHARES (DESIGN.md §2): the PI bringing a real discovery to the
        # one other investigator in town. Each opens as its find lands,
        # spends once, and is both the trust that opens his thread (the
        # how, below) and the hope that holds him back from the hollow
        # turn (_vane_share). Only the two surface-reachable finds an
        # honest PI could put on his desk pre-descent (the journal, the
        # Ledger); the preacher he learns of on his own, and it cuts the
        # other way.
        {
            "key": "share_journal",
            "q": "I found her journal. They all dreamed the same door, "
                 "every one of them. She wrote that she was digging down "
                 "to it. Glad about it.",
            "label": "I found Mara's journal.",
            "avail": lambda g: (g.save.flag("convo_vane_intro_asked")
                                and g.save.flag("evidence_maras_journal")),
            "once": True,
            "on_ask": _vane_share,
            "beats": [
                ("npc", "Say the first part again. The same door. All of "
                        "them."),
                ("pi", "All of them. And she didn't write like a prisoner. "
                       "She wrote like a woman nearly home."),
                ("npc", "A year I've been asking this town for one honest "
                        "page. You walk in off a dead road and hand me her "
                        "whole hand."),
                ("npc", "That's the first real piece of work anybody has "
                        "brought through that door since it all shut. I "
                        "won't forget you did."),
                ("pi", "[c=dim]Something in him let go a notch.[/c]"),
            ],
        },
        {
            "key": "share_ledger",
            "q": "The lodge's old registers. A year of guests signed in "
                 "and not one of them ever signed out. The clean book on "
                 "the desk starts right where the boxes stop.",
            "label": "The lodge registers are wrong.",
            "avail": lambda g: (g.save.flag("convo_vane_intro_asked")
                                and g.save.flag("evidence_the_ledger")),
            "once": True,
            "on_ask": _vane_share,
            "beats": [
                ("npc", "Now that is evidence. Paper with dates on it. "
                        "God, I have missed paper with dates on it."),
                ("npc", "I never got past that desk. Sable smiles, the "
                        "whole building goes polite, and you walk out "
                        "without whatever you came in for."),
                ("npc", "Keep pulling threads like that and this town "
                        "might finally owe somebody the truth. Watch who "
                        "sees you pull them."),
                ("pi", "[c=dim]He wrote it down.[/c]"),
            ],
        },
        # The newspaper (TODO #2): to everyone else in Brimley the paper
        # is word from outside. To Vane it is the break lever. The front
        # page tells a man who wants it all to end that the outside is
        # dying the same death, and its brightest walked out of a room he
        # could have left any time. The give-beat telegraphs the damage
        # as MOOD; the number (VANE_PAPER_DESPAIR) stays hidden.
        {
            "key": "paper",
            "q": "I've got yesterday's paper in my coat. April "
                 "fourteenth. Figured the law here should have some word "
                 "from outside.",
            "label": "I brought yesterday's newspaper.",
            "avail": lambda g: (g.save.flag("convo_vane_intro_asked")
                                and g.player.inventory.has("newspaper")),
            "once": True,
            "on_ask": _vane_paper_given,
            "beats": [
                ("npc", "(He takes it in both hands, careful, like "
                        "something that might go out.)"),
                ("npc", "(He spreads it flat on the desk and stands over "
                        "the front page a long time.)"),
                ("npc", "Kurt Cobain. Huh."),
                ("npc", "I drove down to the Cities to see him play, "
                        "before all this. Stood at the back. Best night I "
                        "had that whole year."),
                ("pi", "Sheriff?"),
                ("npc", "He had every road out of every town, that man. "
                        "The whole world open. And he shut the door on it "
                        "from the inside."),
                ("npc", "So it isn't just here. That's what a front page "
                        "is for, I guess. Telling you the weather's the "
                        "same all over."),
                ("npc", "Thank you for the paper, son. Go on home now. "
                        "(He doesn't look up from the page again.)"),
                ("pi", "[c=dim]I meant it as a kindness. Walking out, I "
                       "couldn't remember why I thought it would land as "
                       "one.[/c]"),
            ],
        },
        # The blind cultist: his one window into the HOW (NARRATIVE §4:
        # one post-seal conversation with a nameless blind cultist,
        # radiant with unaccountable conviction, promised his own sight
        # restored by the dream, in truth sent to convert him; Vane
        # refused). TRUST-gated (DESIGN.md §2): he spends his one card only
        # on a fellow investigator -- the PI has announced himself AND
        # shared at least one real discovery (another outsider who only
        # takes never earns it). He keeps his knowledge boundary: no
        # destination, no direction, only the offer.
        {
            "key": "how",
            "q": "A hundred strangers drove north to the same dying "
                 "town. Nobody talks that many people into anything. How "
                 "was it done?",
            "label": "How were the newcomers gathered?",
            "avail": lambda g: (g.save.flag("convo_vane_intro_asked")
                                and int(g.save.arg("vane_informed", 0)) >= 1),
            "once": True,
            "on_ask": _vane_how_told,
            "beats": [
                ("npc", "I asked that question every night for a year. "
                        "What I've got is one conversation. I'll spend "
                        "it on you."),
                ("npc", "After the rooms emptied, one of them came back "
                        "up the road to this office. Blind. Born blind, "
                        "he said. Walked in without a stick and sat down "
                        "square in that chair."),
                ("npc", "No name. I asked twice. He sat there lit up "
                        "like a man warming his hands at a stove. Said "
                        "the dream had promised him his eyes. Said when "
                        "the work is finished he'll open them, and "
                        "they'll work."),
                ("pi", "He wasn't there to confess anything. He was "
                       "there to fetch you."),
                ("npc", "He made the offer. Told me to name the thing I "
                        "want most in this world, and come with him, and "
                        "it would be waiting. I put him out. He thanked "
                        "me for my time and he left smiling."),
                ("npc", "You don't talk a hundred strangers onto one road. "
                        "They weren't tricked. Every one of them was going "
                        "toward something, and glad of it."),
                ("npc", "What it was, who was holding it out, I never got "
                        "closer than that chair. That's the piece that keeps "
                        "my lights on at night."),
            ],
        },
        # The office gun cabinet -- the best ammo in town, and EARNED (the
        # trust-gated LEAD, DESIGN.md §2). Opens like the "how" (intro + at
        # least one shared discovery), spends once, and hands the cache over:
        # the lawman with no deputies and no law left arms the one fellow
        # investigator who brought him the truth, knowing full well it will
        # not help against what took Brimley (the gun exists to fail,
        # DESIGN.md §1). _vane_give_cache drops it live and gates the office
        # on_enter drop on the flag.
        {
            "key": "cache",
            "q": "If this goes the way it's been going, I'll be out there "
                 "alone. Is there anything you can put in my hand, Sheriff?",
            "label": "Am I on my own out there?",
            "avail": lambda g: (g.save.flag("convo_vane_intro_asked")
                                and int(g.save.arg("vane_informed", 0)) >= 1
                                and not g.save.flag("vane_gave_cache")),
            "once": True,
            "on_ask": _vane_give_cache,
            "beats": [
                ("npc", "Protection. That's a thing this office used to hand "
                        "out."),
                ("npc", "I've got no deputies, no cell that holds, and a law "
                        "nobody up here answers to anymore. What I've got is "
                        "a cabinet in the back. Shells, and a spare piece I "
                        "kept oiled for no reason I could name."),
                ("npc", "Take what you need. It won't help you against what "
                        "took this town. But it'll make you feel like it "
                        "might, and some nights that's the whole of the "
                        "job."),
                ("pi", "[c=dim]He unlocks the cabinet and steps back. The "
                       "last thing the law here has to give.[/c]"),
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
        # An ordinary bad beat on the despair ledger (DESIGN.md §2): a man he
        # knew his whole life, murdered, and no report worth filing.
        from systems.config import VANE_DESPAIR_ACT
        _vane_ledger(game, VANE_DESPAIR_ACT)
        game.dialog.show([
            "They killed the preacher.",
            "He named them from his pulpit. Then he walked down to the "
            "water to fetch his flock home. They left him on the bank "
            "for us to find.",
            "I didn't write a report. Who would I send it to.",
            "[c=dim]He doesn't say the Reverend's name. Nobody in town has.[/c]",
        ], speaker="Sheriff Vane", voice="blip_gruff", portrait="sheriff")
        return
    # The organic conversation, PRESENTED as a frozen close-up TABLEAU (#2b,
    # the Sable precedent): his office in cold window light, and his POSE
    # reading the despair ledger the way the framing line does (mood, never
    # a number). The desk carries what the talk earns: the newspaper he was
    # given stays spread flat, the gun cabinet stands open once he unlocks
    # it. The preacher one-shot above still volunteers itself as a plain
    # beat first; the next press opens the close-up.
    game._open_vane_tableau(npc)


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
    # The tableau art reads this flag to lay the photo on the register.
    game.save.set_flag("sable_showed_photo", True)
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
    "prompt": _pi_framing("Sable folds his hands on the register and waits."),
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
            "q": "I'm looking for a woman named Mara Blaine. Is that a name "
                 "you know, Mr. Sable?",
            "beats": [
                ("npc", "Mara. No, I cannot say I know the name. But I have had "
                        "the pleasure of hosting a great many guests these "
                        "past months. You are welcome to look over the "
                        "register any time you like."),
                ("npc", "You will mean one of the new folk, I expect. We had no "
                        "end of those this past year. They came like they had "
                        "heard something worth the drive."),
                ("npc", "And I was glad of every one. This town was drying up "
                        "before they came. I had every room full. You should "
                        "have seen this house with every window lit."),
                ("pi", "And the rest of Brimley feels the same?"),
                ("npc", "Ah. There you have it. Not everyone has been so warm. "
                        "Some of the old families have gone as cold as our "
                        "root cellar about the newcomers."),
                ("npc", "I would mind who you take your questions to, friend. "
                        "Not everyone here wishes a stranger well. I do. You "
                        "remember that."),
                ("ask", "Show him her photograph?", [
                    ("Slide the photo across the desk.", [
                        ("pi", "(You lay her photo on the register.)"),
                        ("npc", "(He looks at it a good while, then hands it "
                                "back.) No. A pretty thing, but no. I could "
                                "not put a name or a room to her. So many "
                                "faces came through that door."),
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
        # An early question that LEADS to the key: the guest asks after the
        # cellar, and Sable gives free permission (he is hiding nothing -- the
        # host is the lucky one, not a conspirator) plus a hint that the key
        # is lost about the place, IF the PI does not already carry it (the
        # callable beats). Asking sets `sable_cellar_permission`, which colours
        # the Ledger find below (the host let you down to his own damning
        # book). Seeds the descent to the Ledger without gating on it.
        {
            "key": "cellar",
            "label": "What's in your cellar?",
            "q": "What do you keep down in that cellar of yours? Mind if I "
                 "take a look?",
            "on_ask": lambda g: g.save.set_flag("sable_cellar_permission", True),
            "beats": lambda g: (
                [("npc", "The cellar? Storage, mostly. Old registers, a broken "
                         "chair or two. Nothing down there worth hiding from a "
                         "guest.")]
                + ([] if (g.save.flag("cellar_key_taken")
                          or g.player.inventory.has("cellar_key"))
                   else [("npc", "Shoot. I seem to have misplaced the key. If "
                                 "you find it, you are welcome to take a "
                                 "look.")])
            ),
        },
        {
            # The PI asks the mundane question: his car died at the lodge
            # steps the night he drove in, so is there a mechanic? He speaks
            # only from his OWN experience and does NOT yet know the fold kills
            # every engine (that comes from Vane / Royce), so this puts no
            # town-wide car knowledge in his mouth. When pressed, Sable does
            # not stonewall -- he gives his own LIVED EXPERIENCE (he has seen
            # guests' cars go the same way and never one put right; he stopped
            # asking why). That is a local's SURRENDER, distinct from Vane's
            # plain-truth register: Sable names no mechanism and no pattern,
            # only what he has watched and given up on, and lands on his own
            # want -- keep the guest HERE (NARRATIVE §4/§7).
            "key": "car",
            "q": "My car won't start. Turns over and won't catch. Is there "
                 "anyone in town who could take a look at it?",
            "label": "Is there a mechanic in town?",
            # The ask is REMEMBERED (sable_car_asked): his closing hospitality
            # plants the road warning in plain sight, and the_fold's reproach
            # quotes it back only if he actually said it.
            "on_ask": lambda g: g.save.set_flag("sable_car_asked", True),
            "beats": [
                ("npc", "A mechanic? No, nothing like that in Brimley now, "
                        "and it would do you no good if there were."),
                ("npc", "The car is not broken, friend."),
                ("pi", "What do you mean, not broken? It turns over and dies "
                       "at the step."),
                ("npc", "Only that I have seen it before. Now and then a "
                        "guest's car went the same way, and never once have I "
                        "seen one put right."),
                ("npc", "A man quits asking why, after a time. I am long past "
                        "it, and it is no trouble to me. Needn't be to you "
                        "either."),
                ("npc", "You have a good bed and a standing welcome. The "
                        "roads are not going anywhere. Stay as long as you "
                        "need."),
            ],
        },
        # Unlocked by reading the cellar Ledger (evidence the_ledger): the
        # follow-up question opens on the evidence alone (the old revisit
        # nudge that pointed here was cut). The mask thins: he stops
        # pretending to keep the paperwork, keeps the promise.
        {
            "key": "checkouts",
            "label": "The checkouts stop a year back.",
            "q": "I read your old registers. Guests used to settle up and "
                 "leave. The dates stop a year back. Since then everyone "
                 "signs in and nobody signs out.",
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
        # The reproach: the PI puts the looping road to Sable once he has
        # both HEARD a local name it (the_fold_told note) AND actually
        # walked it himself (crossed_a_fold, C13) -- so the first-person
        # "it set me back down" is never a lie. The detonation is ANCHORED:
        # the car exchange planted "the roads are not going anywhere" inside
        # his closing hospitality (sable_car_asked), so "I meant it plainly"
        # quotes his own words back and the kindness rereads as the warning
        # it always was. A PI who never asked after the mechanic gets the
        # same truth fresh, with no false "I told you" claim.
        {
            "key": "the_fold",
            "label": "The road out brought me back.",
            "q": "I walked the road out of town. Followed it two hours, due "
                 "west. It set me back down past this window.",
            "avail": lambda g: g.save.flag("crossed_a_fold") and any(
                isinstance(e, dict) and e.get("name") == "the_fold_told"
                for e in (g.save.arg("notes", []) or [])),
            "beats": lambda g: ([
                ("npc", "I told you the roads were not going anywhere. You "
                        "heard a man being hospitable. I meant it plainly."),
            ] if g.save.flag("sable_car_asked") else [
                ("npc", "So you walked it. The roads are not going anywhere, "
                        "friend. They never were."),
            ]) + [
                ("npc", "There is no call to be cross about it. You are safe "
                        "here. Safer than out there."),
            ],
        },
        # The newspaper (TODO #2): the NULL door, and the tell. To
        # everyone else in Brimley the paper is the first word from
        # outside in three months; to the lucky host it is a coaster.
        # His want was never the outside (NARRATIVE 4). No reward on
        # purpose; the chill files as the note.
        {
            "key": "paper",
            "q": "Yesterday's newspaper, Mr. Sable. First word from "
                 "outside since the winter. It's the house's if you "
                 "want it.",
            "label": "I brought yesterday's newspaper.",
            "once": True,
            "avail": lambda g: g.player.inventory.has("newspaper"),
            "on_ask": _sable_paper_given,
            "beats": [
                ("npc", "(He takes it in both hands and squares it on the "
                        "desk, unopened, the fold lined up with the "
                        "register's edge.)"),
                ("npc", "That is a kindness, friend. The Arcadia thanks "
                        "you."),
                ("npc", "We will set it out in the common room. Guests do "
                        "like having something to read."),
                ("pi", "You're not going to open it?"),
                ("npc", "Oh, I expect I will get to it. The news keeps, "
                        "friend. It always has."),
                ("npc", "Now. Was there anything else?"),
                ("pi", "[c=dim]Half this town would give a finger for "
                       "that page. He squared it to the desk like a "
                       "coaster.[/c]"),
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
                ("npc", "My guests left it at the desk when they went below. "
                        "It was meant for me. They wanted me to come down "
                        "after them, and they meant it kindly."),
                ("npc", "But I never wanted what they went to find. I wanted "
                        "a full house, friend, and I had one. Take it. "
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
    """The Lodge Clerk, Mr. Sable -- the LUCKY HOST (NARRATIVE §4, 2026-07
    reframe: the door never spoke through him). A LOCAL, the most attuned
    of them -- and the one soul in Brimley whose want was FED: he always
    wanted a full house, and the migration the door caused filled the
    Arcadia with real guests for a season (the door provided nothing; the
    migration did). It was fun; he was fulfilled; and a fed want takes no
    bait, so he alone among the attuned never followed the dream down.
    His funereal undertow is GRIEF FOR A FULL HOUSE, never conspiracy or
    a channel; his certainties are a host's pattern-sense. He keeps you
    comfortable, keeps you here (you are the first guest since the seal),
    and the only thing he says about the car is deniable (the Sheriff
    carries the plain truth).

    THE INVITATION (the act break): the congregation -- his guests, the
    ones who sign in and never out -- left the envelope at his desk when
    they went below: THEIR OFFER TO BRING HIM WITH THEM. He knows what it
    is and where its writers went (the never-worn robe in his closet came
    with it); he just never wanted what they went to find. At 3 evidence
    he judges the guest ready to go where he himself never wanted to, and
    hands it over like a room key. Somebody has to keep the desk.
    State-gated on what the PI knows -- never farmable by repeat visits."""
    _cult_tell(game, "clerk")
    # The organic conversation, PRESENTED as a frozen close-up TABLEAU (#2b):
    # the world holds, his host face animates, and SABLE_CONVO renders its
    # beats as the tableau caption and its menu as the option panel. His
    # welcome plays once (the greet), then the menu is the PI's own questions
    # -- each picked line is spoken, Sable answers over the desk, and new
    # questions surface as the case grows. The Invitation is an explicit ASK
    # ("the_way_down", gated on readiness); the photo + envelope appear on the
    # register live as the talk earns them (the art reads the save flags).
    game._open_sable_tableau(npc)


# ---- The Brimley chorus ----
# The last of the ask-verb expansion (TODO #1): Old Pell, Mrs. Calder,
# Royce, and Garrick come off the _brimley_voice page-lists and onto the
# organic conversation. Every one leads with the shared opener pair
# (introduce-as-PI + the photograph) with short answers of their own,
# plus a question or two carrying their signature material. Their reactive one-shots (the town reacting to the case,
# TODO #10) keep firing ahead of the menu, exactly as the principals'
# volunteered beats do. The town stays visually ordinary end to end
# (TODO #22c): no dialogue swap, no people-transform. What rots is the
# PI's framing (_pi_framing), never the locals' words. The fold note
# moves off the old
# any-talk trigger onto the exchanges that actually carry the account
# (Royce's roads, Garrick's warning) -- earned by asking, like
# everything else in the verb.


def chorus_dialogue(convo, beats=()):
    """Build a dialogue_fn for a Brimley chorus local. Reactive one-shot
    `beats` keep the _brimley_voice contract: on each talk the first
    beat whose predicate holds and whose one-shot flag is unset fires
    INSTEAD of the conversation (and sets its flag); otherwise the
    organic conversation opens."""
    def _fn(game, npc):
        portrait = (getattr(npc, "portrait", None)
                    or getattr(npc, "sprite_kind", None))
        for flag, pred, pages in beats:
            if game.save.flag(flag):
                continue
            if pred(game):
                game.save.set_flag(flag, True)
                game.dialog.show(pages, speaker=npc.name,
                                 voice=convo.get("voice", "blip_mid"),
                                 portrait=portrait)
                return
        from ui.conversation import open_conversation
        open_conversation(game, npc, convo)
    return _fn


def _royce_roads_told(game):
    """Royce's account IS the looping-roads fact (the corn hands you
    back); file the PI's fold note without hijacking the conversation
    float chain (reflect=False) -- the exchange carries the PI's
    reflection as its own closing beat."""
    if hasattr(game, "_fold_mentioned"):
        game._fold_mentioned("Royce", reflect=False)


def _garrick_roads_told(game):
    """Garrick's road warning carries the same account (make for the
    county line and you are back at this well); same reflect=False
    rule as Royce and Vane."""
    if hasattr(game, "_fold_mentioned"):
        game._fold_mentioned("Garrick", reflect=False)


# Old Pell -- the schoolhouse step and the corn: Pell corn, the town's
# northernmost-in-the-world pride (TODO #11, a mundane human feat, never
# the door's doing), dead standing since the missed fall harvest. Stasis
# register; he turns at rot stage 3, so this talk is his pre-turn
# window. The stopped calendar stays a rot-layer detail (the decoration
# + his turned lines), deliberately NOT an ask topic. (His old
# persistent-cold line was CUT, maintainer call (2026-07):
# the ice goes out and the season turns -- weather stasis would be a
# second impossible thing.)
PELL_CONVO = {
    "id":    "pell",
    "name":  "Old Pell",
    "voice": "blip_low",
    "pi_voice": "blip_soft",
    "prompt": _pi_framing("Pell stays put on his step, arms folded."),
    "leave":  "That's all for now.",
    "greet": {
        "flag": "pell_greeted",
        "beats": [
            ("npc", "[c=dim]You're new. We don't get new. Nobody gets in. "
                    "Nobody gets...[/c]"),
            ("npc", "Hm. Well."),
        ],
    },
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "A detective. On my step."),
            ("npc", "There's a foulness set over this whole town, son. You "
                    "feel it more than smell it. Folk are tired under it, "
                    "all of them, and sleep doesn't mend it."),
            ("npc", "[c=dim]You're breathing it now too. Same as the rest "
                    "of us.[/c]"),
        ],
        photo_beats=[
            ("npc", "(He tips the photograph toward the light, slow about "
                    "it.)"),
            ("npc", "Could be she went by in the fall. Could be she "
                    "didn't. The new faces all ran together after a "
                    "while. Then they stopped going by at all."),
        ],
    ) + [
        {
            "key": "corn",
            "q": "All that corn west of the river, dead and still standing "
                 "in April. Nobody brought it in?",
            "label": "Nobody brought the corn in?",
            "beats": [
                ("npc", "That's Pell corn, son. Northernmost corn in the "
                        "world, grown on this ground since 1894. My father "
                        "took ribbons on it. So did I."),
                ("npc", "Nobody cut it last fall. First harvest this town "
                        "ever missed. It stood there and died standing."),
                ("npc", "[c=dim]I don't look at the fields long "
                        "anymore.[/c]"),
            ],
        },
        # The newspaper (TODO #2): mercy, no item. An old man who
        # stopped marking days picks the calendar back up. His stoop
        # beat swaps to match (scenes/brimley.py).
        {
            "key": "paper",
            "q": "It's yesterday's paper, Mr. Pell. Out of the Cities. "
                 "I'd like you to have it.",
            "label": "I brought yesterday's newspaper.",
            "once": True,
            "avail": lambda g: (g.save.flag("convo_pell_intro_asked")
                                and g.player.inventory.has("newspaper")),
            "on_ask": _pell_paper_given,
            "beats": [
                ("npc", "(He doesn't reach for it. He reads the masthead "
                        "where it sits in your hand, slow, like a man "
                        "reading a headstone.)"),
                ("npc", "April 14. Out there it got to April 14."),
                ("npc", "I quit marking days, son. Nothing was coming "
                        "that a marked day would bring any closer."),
                ("npc", "(He takes it, folds it once, and tucks it under "
                        "his arm the way you carry tools.)"),
                ("npc", "There'll be a corn report in here somewhere. "
                        "Prices. Somebody's weather. Somebody still "
                        "growing, somewhere south of us."),
                ("npc", "I believe I'll pencil today in when I get home. "
                        "Just today. We'll see about the one after it."),
                ("pi", "[c=dim]Nothing came back across for it. I wasn't "
                       "waiting on anything to.[/c]"),
            ],
        },
    ],
}


# Mrs. Calder -- the east-edge road, the extra place set at supper for a
# guest she cannot name (a certainty she doesn't question; §1b: no
# perceptible individual loss). She converts at rot stage 2, so her talk
# lives at evidence 0-1.
CALDER_CONVO = {
    "id":    "calder",
    "name":  "Mrs. Calder",
    "voice": "blip_mid",
    "pi_voice": "blip_soft",
    "prompt": _pi_framing("Mrs. Calder watches the road past my shoulder."),
    "leave":  "That's all for now.",
    "greet": {
        "flag": "calder_greeted",
        "beats": [
            ("npc", "Oh. Is it you? ...Are you the one the place is set "
                    "for?"),
            ("npc", "No. No, it couldn't be you. Forgive an old "
                    "woman her hoping."),
        ],
    },
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "(She takes your hand in both of hers before you "
                    "finish saying it.)"),
            ("npc", "Somebody's daughter. And somebody sent for, to bring "
                    "her home. There's still such a thing. Isn't that "
                    "fine."),
        ],
        photo_beats=[
            ("npc", "(She holds it out at arm's length, the way the "
                    "far-sighted do.)"),
            ("npc", "No, dear. I don't know her. I've not seen her at my "
                    "gate."),
        ],
    ) + [
        {
            "key": "plate",
            "q": "You asked if I was the one the place is set for. What "
                 "place? Set for who?",
            "label": "Who's the place set for?",
            "beats": [
                ("npc", "I lay an extra plate at supper. Have done a while "
                        "now. Couldn't tell you who for. Someone's coming. "
                        "I know it the way I know my own name."),
                ("npc", "[c=dim]I'll know the face when it's across the "
                        "table from me. Till then it would be unkind not "
                        "to be ready.[/c]"),
            ],
        },
    ],
}


# Royce -- he tried to drive out like everyone in town did (it is
# northern Minnesota; everyone drives) and gave it up with the rest.
# His roads exchange is the town's plainest looping-roads account and
# files the PI's fold note; his one impossible fact (you got IN) is a
# question HE puts to the PI, once he's earned it. He converts at rot
# stage 3.
ROYCE_CONVO = {
    "id":    "royce",
    "name":  "Royce",
    "voice": "blip_mid",
    "pi_voice": "blip_soft",
    "prompt": _pi_framing("Royce looks down the road while I talk."),
    "leave":  "That's all for now.",
    "greet": {
        "flag": "royce_greeted",
        "beats": [
            ("npc", "(He looks you over a long moment before he says a "
                    "word.)"),
            ("npc", "You're the one who drove in. Off the north road, at "
                    "night. Nothing has come up that road in months."),
            ("npc", "I'd shake your hand, mister, but I don't know yet "
                    "what you are."),
        ],
    },
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "A detective. Come up here to find somebody, and then "
                    "drive her home."),
            ("pi", "That's the shape of it."),
            ("npc", "The finding I can't speak to. The driving "
                    "home I can. Ask me about the roads sometime. Ask me "
                    "what they do."),
        ],
        photo_beats=[
            ("npc", "(He wipes his hands on his jacket before he takes "
                    "it. Looks properly, corner to corner.)"),
            ("npc", "No. A lot of new faces drove in this past year, same "
                    "as anybody comes anywhere. Hers isn't one I know."),
        ],
    ) + [
        {
            "key": "roads",
            "q": "Everyone in this town talks around the roads. You drove "
                 "them. What do they do?",
            "label": "What do the roads do?",
            "once": True,
            "on_ask": _royce_roads_told,
            "beats": [
                ("npc", "I drove it. River road, county line, every road "
                        "out of Brimley. Same as everybody in this town "
                        "with a set of keys. The corn handed me back "
                        "every time."),
                ("npc", "Same bend. Same bridge. Same town coming up in "
                        "the windshield. And I'd swear to you on anything "
                        "I never turned the wheel."),
                ("npc", "[c=dim]I gave it up. Everybody did. There's no "
                        "out to drive to.[/c]"),
                ("pi", "[c=dim]Said flat. No fear left in it.[/c]"),
            ],
        },
        {
            "key": "how_in",
            "q": "You keep looking at me like I owe you something. Say "
                 "it.",
            "label": "Something on your mind?",
            "once": True,
            "avail": lambda g: g.save.flag("convo_royce_roads_asked"),
            "beats": [
                ("npc", "You came IN. That's what's on my mind. That road "
                        "only ever hands a man BACK, and it carried you "
                        "in easy as Sunday."),
                ("ask", "He wants the answer more than he wants air.", [
                    ("Tell him the truth. The road just drove.", [
                        ("pi", "I drove up at night. Radio went to static "
                               "past the county line, and the road just "
                               "drove. There was nothing to it."),
                        ("npc", "(Something goes out of him.) Nothing to "
                                "it. Every driver in this town tried that "
                                "same drive till they quit. For you it "
                                "just drove."),
                        ("npc", "[c=dim]Then it wanted you in, mister. "
                                "I'd chew a while on what that means for "
                                "getting out.[/c]"),
                    ], None),
                    ("Give him nothing.", [
                        ("pi", "Same as anybody drives anywhere. I wasn't "
                               "paying attention."),
                        ("npc", "Wasn't paying attention. (He laughs, and "
                                "there's no fun in it.) No. I don't "
                                "suppose you were."),
                        ("npc", "[c=dim]Sure you weren't. (He looks back down the road.) Nobody drives that road easy. Nobody but you.[/c]"),
                    ], None),
                ]),
            ],
        },
        # The newspaper (TODO #2): escape-hope. Proof the outside is
        # still running, paid for in the batteries he hoarded for a
        # drive he quit believing in, and the one road that held
        # longest (his account: testimony, fallible, filed as a note).
        {
            "key": "paper",
            "q": "I carried yesterday's paper up with me. April 14, off "
                 "a Cities rack. It's yours.",
            "label": "I brought yesterday's newspaper.",
            "once": True,
            "avail": lambda g: (g.save.flag("convo_royce_intro_asked")
                                and g.player.inventory.has("newspaper")),
            "on_ask": _royce_paper_given,
            "beats": [
                ("npc", "(He checks the date before anything else on the "
                        "page. Then he checks it again.)"),
                ("npc", "Printed yesterday. Yesterday this page was "
                        "OUTSIDE. Presses running. Trucks rolling. Some "
                        "kid throwing this at a porch."),
                ("npc", "I'd about talked myself out of all that still "
                        "being there."),
                ("npc", "Hold on. You're not walking off with nothing "
                        "for it."),
                ("npc", "[c=dim]He digs under his truck seat and comes "
                        "back with a paper sack, heavy for its size. "
                        "Flashlight batteries, loose, a careful winter's "
                        "hoard.[/c]"),
                ("npc", "And hear this, it's the only thing I own worth "
                        "telling. River road, south. That one held "
                        "longest before it handed me back. Two bends "
                        "past the bridge. If any road out of here ever "
                        "remembers where it goes, it'll be that one."),
                ("pi", "[c=dim]He walked off with the box scores open. "
                       "Lighter on his feet than I've seen him.[/c]"),
            ],
        },
    ],
}


# Garrick -- the old man at the well, watching the square. The law is
# hollow and he says so plainly; his road warning carries the fold
# account and files the note. He turns at rot stage 3.
GARRICK_CONVO = {
    "id":    "garrick",
    "name":  "Garrick",
    "voice": "blip_mid",
    "pi_voice": "blip_soft",
    "prompt": _pi_framing("Garrick leans on the well and waits."),
    "leave":  "That's all for now.",
    "greet": {
        "flag": "garrick_greeted",
        "beats": [
            ("npc", "Seen you already, son. Door to door, both banks. I "
                    "sit this square most of the day. Everything in "
                    "Brimley crosses it sooner or later."),
        ],
    },
    "exchanges": _opener_exchanges(
        intro_beats=[
            ("npc", "Folks who ask questions in this town go quiet. Real "
                    "quiet. I'm not threatening you, son. I'm counting "
                    "for you."),
            ("npc", "[c=dim]The Sheriff will tell you to head on home. He "
                    "knows you can't. He can't either.[/c]"),
        ],
        photo_beats=[
            ("npc", "(He barely looks at the photograph. He looks at you "
                    "instead.)"),
            ("npc", "Faces pass this well all year. Maybe hers did too, "
                    "with the new folk. They kept to their own side of "
                    "things, and then they stopped being seen at all."),
        ],
    ) + [
        {
            "key": "roads",
            "q": "Is there a safe way to move around this town? You watch "
                 "it all day.",
            "label": "Any safe way around this town?",
            "on_ask": _garrick_roads_told,
            "beats": [
                ("npc", "Stay on the roads. People who go off the roads "
                        "come out wrong-side of where they went in. I've "
                        "watched it happen to better walkers than you."),
                ("npc", "And don't put your faith in a road going where "
                        "it went last week. Make for the county line and "
                        "you'll be back at this well by supper."),
                ("npc", "[c=dim]Go on home, son. ...Oh. Right. None of us "
                        "can.[/c]"),
            ],
        },
    ],
}


def preacher_body_examine(game, npc):
    """E on the Preacher's remains at the riverbank: take his cross + log
    files a case note once. (2026-07 rework: the doom sends Crane out of his
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
    # Real, and terrible, but not Mara -- so it files as a case NOTE, never
    # case-evidence (NARRATIVE §6: the cult's hostility is already proven by
    # the sealed roads and the grabbing cultists). note=True keeps it in the
    # notebook without touching the King-gate.
    _evidence(game, "the_preacher", [
        "The Preacher. He named them from his pulpit, every Sunday. Then "
        "he went down to the river after them, believing a flock can be "
        "talked home.",
        "They opened him for it and left him on the bank, where the whole "
        "town could find him.",
        "His collar's still white. His cross lies in the mess. You take it.",
    ], note=True)
