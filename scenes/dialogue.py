"""All NPC dialogue functions.

The story text here is intentionally generic placeholder copy. Every
function, signature, and helper is preserved (game.py and the scenes
import them), but the spoken lines carry no lore.
"""
import time
import re


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


# ---- The Preacher (key: old_man_dialogue) ----

def old_man_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "preacher")
    count = save.arg("old_count", 0) + 1
    save.set_arg("old_count", count)
    if count == 1:
        game.dialog.show([
            "Another new face. That's all that comes to Brimley anymore -- "
            "strangers off the highway, more every season. And not one of "
            "them leaves.",
            "I don't trust it. They arrive too easy, like something held "
            "the door. Then they go quiet, drift out to the corn, and they "
            "don't come back.",
            "A young woman came through last month. Bright thing, full of "
            "questions -- like you. She kneels out there now, with the "
            "rest. You looking for her?",
        ], speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 2:
        # The hubris that gets him killed. After this he's marked: the
        # church swaps him for his remains on the next entry (evidence #4).
        game.dialog.show([
            "You came back. Good -- then hear the rest of it.",
            "I say it from my pulpit, plain as I'm saying it now: that's no "
            "church in the corn. Something out there calls the strangers in "
            "and hollows them out. I name it, and the sheriff sits in my "
            "back pew while I do.",
            "Let them come for an old man. I've buried better than whatever "
            "it is they kneel to. God's on my side of the door.",
        ], speaker="Preacher", voice="blip_low", portrait="old")
        save.set_flag("preacher_doomed", True)
    else:
        game.dialog.show([
            "I've said my piece. Go on, now -- and watch the road.",
        ], speaker="Preacher", voice="blip_low", portrait="old")


# ---- The Kid ----

def kid_dialogue(game, npc):
    """The Kid -- innocent witness (NARRATIVE §2). He saw Mara walk into
    the corn; what he gives you is what he tells you (no inventory item --
    the old keepsake object was purged). Children notice what adults
    pretend not to."""
    save = game.save
    inv = game.player.inventory
    # The witness beat: first real conversation, he tells you what he saw.
    if not save.flag("kid_witnessed"):
        save.set_flag("kid_witnessed", True)
        game.dialog.show([
            "You're looking for the corn lady. The nice one with all the "
            "questions.",
            "I watched her walk right out into the rows. She didn't come "
            "back. The ones who go in after the corn never do.",
            "[c=dim]The grown-ups say nobody saw her go. They saw. They "
            "always see. They just look at their shoes.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        return
    # Playscript-recognition one-shot (kept; flow unchanged).
    if inv.has("playscript") and not save.flag("kid_playscript_noticed"):
        save.set_flag("kid_playscript_noticed", True)
        game.dialog.show([
            "That yellow book. The corn lady drew that sign too, over and "
            "over, on everything.",
            "[c=dim]You shouldn't have it. It looks at you back.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        return
    count = save.arg("kid_count", 0) + 1
    save.set_arg("kid_count", count)
    if count == 1:
        game.dialog.show([
            "She went down, you know. After the corn.",
            "[c=dim]Everybody who stays too long goes down in the end. "
            "That's just what Brimley's for.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 2:
        game.dialog.show([
            "My mom and dad smile all the time now. They didn't used to.",
            "[c=dim]I don't smile. That's how you can tell I'm still me.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 3:
        game.dialog.show([
            "The preacher was nice to me. Now there's a new quiet where he "
            "used to be.",
            "[c=dim]Are you going to go quiet too?[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 4:
        game.dialog.show([
            "If you find a way out, don't tell me where.",
            "[c=dim]They'd ask me, after. And I can't lie to them anymore.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    else:
        game.dialog.show([
            "[c=dim]The boy just watches the corn line, waiting.[/c]",
        ], speaker="", voice="blip_soft", portrait="kid")


# ---- The Store-Owner ----

SHOP_STOCK = [
    ("paper",        "Notebook Paper",   0),
    ("charcoal",     "Charcoal Stick",   0),
]


def _shop_purchase(game, key, name, cost):
    game.player.inventory.add(key, 1)
    game.audio.play("pickup", 0.7)
    game.show_notice(f"He hands you the {name}.")


def _shop_open_menu(game):
    """Open the shop menu. Item keys preserved; flavor blanked."""
    options = [name for (_k, name, _c) in SHOP_STOCK]
    options.append("Nothing.")

    def _on_pick(idx):
        if idx >= len(SHOP_STOCK):
            return
        key, name, cost = SHOP_STOCK[idx]
        _shop_purchase(game, key, name, cost)
        _shop_open_menu(game)

    prompt = "What can I get you?"
    game.dialog.show_choice(prompt, options, _on_pick,
                            speaker="Store-Owner", voice="blip_high",
                            portrait="shopkeep")


def shopkeep_dialogue(game, npc):
    save = game.save
    _cult_tell(game, "store_owner")
    count = save.arg("shop_count", 0) + 1
    save.set_arg("shop_count", count)
    if count == 1:
        def _then_open():
            _shop_open_menu(game)
        plain = [
            "Morning.",
            "Take a look if you like.",
        ]
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Store-Owner", voice="blip_high",
                         portrait="shopkeep", on_complete=_then_open)
        return
    if count == 2:
        def _then_open():
            _shop_open_menu(game)
        game.dialog.show([
            "Back again.",
            "[c=dim]...[/c]",
        ], speaker="Store-Owner", voice="blip_high",
            portrait="shopkeep", on_complete=_then_open)
        return
    if count == 3:
        game.dialog.show([
            "Not much left.",
            "[c=dim]...[/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    if count == 4:
        game.dialog.show([
            "[c=dim]He looks up.[/c]",
            "[c=dim]Nothing to say.[/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    if count == 5:
        game.dialog.show([
            "[c=dim]He doesn't look up.[/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    game.dialog.show([
        "[c=dim]He sits behind the counter.[/c]",
    ], speaker="", voice="blip_soft", portrait="shopkeep")


# ---- The Sheriff (legacy key: fisherman_dialogue) ----

def fisherman_dialogue(game, npc):
    """The Sheriff -- the law that keeps everyone in (NARRATIVE §2). The
    trap's enforcer: he killed your car, and his patrols are surveillance.
    Friendly small-town lawman with a cold floor under it; he never admits
    the cult, only ever 'helps you settle in.' Escalates over visits from
    welcome -> the car -> the outsider rule -> a closed door."""
    save = game.save
    _cult_tell(game, "sheriff")
    n = save.arg("fisher_count", 0) + 1
    save.set_arg("fisher_count", n)
    if n == 1:
        game.dialog.show([
            "Sheriff Vane. You'd be the fella asking after the Blaine girl.",
            "Word travels in a town this size. Not much else does.",
            "[c=dim]I'd slow down if I were you. Folks who come asking tend "
            "to forget they meant to leave.[/c]",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 2:
        # He killed your car -- said in deniable lawman's terms.
        game.dialog.show([
            "Saw your car out by the river. Took the liberty of looking it "
            "over -- bad spark, I'd say. Wouldn't trust it on these roads.",
            "[c=dim]He smiles. His hands are clean, but you believe the "
            "spark went bad the moment he wanted it to.[/c]",
            "Don't you fret. Nobody walks out of Brimley, and nobody drives. "
            "You'll be looked after.",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 3:
        # The outsider rule, from the enforcer's side: the town claims its
        # own; you are the one thing it hasn't claimed yet.
        game.dialog.show([
            "I see everyone who comes and everyone who goes. Lately it's all "
            "coming, no going. That's the way it's meant to be.",
            "This town belongs to something now, son, and it keeps what "
            "belongs to it. Every soul here's been spoken for.",
            "[c=dim]Every soul but yours. You're the one loose thread. We "
            "don't care for loose threads.[/c]",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 4:
        game.dialog.show([
            "Still walking around. Still asking.",
            "[c=dim]The preacher asked questions too. You won't be seeing "
            "him at services.[/c]",
            "Go home, son. While there's still a you to send.",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    else:
        game.dialog.show([
            "[c=dim]He watches you the whole way down the road. He does not "
            "blink.[/c]",
        ], speaker="", voice="blip_soft", portrait="guard")


# ---- The Clerk ----

def clerk_dialogue(game, npc):
    """The Clerk's quest chain (crate -> cellar key -> bottle ->
    car keys -> playscript) is preserved mechanically. All flags, item
    grants, and branch order are unchanged; only the spoken text is
    blanked."""
    save = game.save
    _cult_tell(game, "clerk")
    inv = game.player.inventory
    # PRIORITY 1: turn in the liquor crate -> advances the chain. The
    # cellar is no longer key-gated, so no key changes hands; the Clerk
    # just points you down to the un-locked hatch.
    if inv.has("liquor_crate"):
        inv.remove("liquor_crate", 1)
        save.set_flag("innkeeper_quest_done", True)
        save.set_flag("axe_quest_started", True)
        save.set_flag("innkeeper_bottle_done", True)   # legacy alias
        game.audio.play("pickup_rare", 0.7)
        if save.flag("crate_note_read"):
            game.dialog.show([
                "[c=dim]He sets the crate on the bar.[/c]",
                "Thanks for that.",
                "[c=dim]Cellar's open if you need it -- hatch under the\n"
                "kitchen.[/c]",
            ], speaker="Clerk", voice="blip_low", portrait="old")
        else:
            game.dialog.show([
                "There it is. Thanks.",
                "[c=dim]Hatch to the cellar's under the kitchen, if you're\n"
                "curious. It's not locked.[/c]",
            ], speaker="Clerk", voice="blip_low", portrait="old")
        return
    # Stage-2 turn-in -- the cellar bottle -> grants car keys.
    if inv.has("cellar_bottle"):
        inv.remove("cellar_bottle", 1)
        save.set_flag("cellar_bottle_done", True)
        if not inv.has("car_keys"):
            inv.add("car_keys", 1)
        game.audio.play("pickup_rare", 0.7)
        game.dialog.show([
            "That'll do.",
            "[c=dim]Here are your car keys.[/c]",
            "Not that they'll do you much good. The roads don't go where "
            "they used to.",
        ], speaker="Clerk", voice="blip_low", portrait="old")
        return
    # Quest complete once the keys are handed over. The Playscript is NOT
    # a Clerk turn-in -- it's the deep-gate key, found in the Works and
    # spent at the Deep Stair (handing it over here used to soft-lock the
    # descent). The old stage-3 turn-in + post-quest branch are removed.
    if save.flag("cellar_bottle_done"):
        game.dialog.show(
            ["[c=dim]He nods without looking up. Your tab's settled.[/c]"],
            speaker="", voice="blip_soft", portrait="old")
        return
    if save.flag("axe_quest_started"):
        game.dialog.show(
            ["Settle your tab and the keys are yours.",
             "[c=dim]There's a bottle down in the cellar -- the hatch is\n"
             "under the kitchen. Bring it up.[/c]"],
            speaker="Clerk", voice="blip_low", portrait="old",
        )
        return
    if not save.flag("innkeeper_quest_started"):
        save.set_flag("innkeeper_quest_started", True)
        plain = [
            "Morning. I could use a hand.",
            "[c=dim]I left a crate out by the field. Could you bring\n"
            "it back? I'll square things up after.[/c]",
            "Try the corn rows.",
        ]
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Clerk", voice="blip_low", portrait="old")
        return
    game.dialog.show(
        ["The crate's out in the corn rows.",
         "[c=dim]...[/c]"],
        speaker="Clerk", voice="blip_low", portrait="old",
    )


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
            "[c=dim](The same faces. The same smile. The same patient, "
            "unmoving eyes.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
