"""All NPC dialogue functions for THRESHOLD.

The town's adults are mostly Yellow-King cultists. Their tells
are subtle: pale skin, slept-poorly faces, a faint smell of pine
(from tending the cauldron-fire's wood). On the first interaction
with each cult NPC, a dim italic 'sensory notice' fires once -- the
player has to notice it on their own.

The kid is the only NPC the player can trust. His arc lands the
binary follower choice at visit 7 ('Can I come with you?').

The Innkeeper is host AND secret cult. He runs the inn and owns
the house the player sleeps in. His quest still works mechanically
(saw -> axe -> orb chain) but the orb hand-off feeds the cult, not
destroys the artifact. The front-door confrontation fires from
Game._check_innkeeper_confrontation when the player tries to leave
with cult evidence.
"""
import time
import re


def _evidence(game, name, content):
    """Player-voice realisation. Each call surfaces one of the
    player's own observations as a one-shot dialog. Gated by
    per-name save flag so the same beat never re-fires in a
    playthrough. Also appends to the save-state evidence list so
    the notebook UI / future review screen can show what the
    player has noticed."""
    if game is None or game.save is None:
        return
    flag = f"evidence_{name}"
    if game.save.flag(flag):
        return
    game.save.set_flag(flag, True)
    lines = content.split("\n") if isinstance(content, str) else list(content)
    log = game.save.arg("evidence", [])
    if isinstance(log, list):
        # Each entry: {"name": slug, "lines": [...]}. Older saves
        # might contain bare strings; we don't migrate them, but
        # we don't crash on them either -- the notebook UI tolerates
        # both shapes.
        if not any(isinstance(e, dict) and e.get("name") == name
                   for e in log):
            log.append({"name": name, "lines": list(lines)})
            game.save.set_arg("evidence", log)
    game.dialog.show(lines,
                     speaker="", voice="blip_soft",
                     portrait="narrator")


def escalate(game, low, mid, high):
    """Pick the right page-list for an NPC dialog.show() based on
    Pursuer proximity. Three tiers via systems.threat.proximity_tier
    so the bucketing logic is shared with the threat layer.

    Each argument is a list of strings (the same `pages` shape that
    game.dialog.show takes). Falls back to `low` if game/proximity
    is unavailable.
    """
    from systems.threat import (proximity_tier,
                                 PROX_TIER_LOW, PROX_TIER_MID)
    p = getattr(game, "pursuer_proximity", 0.0)
    tier = proximity_tier(p)
    if tier == PROX_TIER_LOW:
        return low
    if tier == PROX_TIER_MID:
        return mid
    return high


def _cult_tell(game, npc_key):
    """Surface the pale-tired-pine notice on first interaction with a
    cult NPC. Fires exactly once per NPC per playthrough. The notice
    is the player's own observation, in dim text."""
    flag = f"cult_tell_{npc_key}"
    if game.save.flag(flag):
        return
    game.save.set_flag(flag, True)
    # Pick one of three sensory notes per NPC so re-readers across
    # multiple playthroughs get variety. The pool is intentionally
    # specific to physical signs: pallor, sleeplessness, the smell.
    pool = (
        "He smells faintly of pine sap.",
        "His skin is the colour of paper.",
        "He looks like he hasn't slept this week.",
        "There is a fleck of soot in his hair.",
        "He doesn't quite blink.",
    )
    line = pool[hash(npc_key) % len(pool)]
    game.show_notice(line, duration=3.2)


# ---- Mom (orphan -- no NPC wired) ----
# THRESHOLD: Mom is dead. The kid speaks of HIS mom, not the
# player's. The player's mother is in the graveyard, headstone in
# the back row of the church plot. No mom_dialogue function.


# ---- The Preacher (key: old_man_dialogue, on the church OLDMAN NPC) ----

def old_man_dialogue(game, npc):
    """The Preacher. Cult elder. Believes the cult's purification
    is righteous -- 'we burn the evil from the world.' Speaks in
    half-quoted scripture and warmth that doesn't quite reach his
    eyes. Visit progression slips into open menace at the end."""
    save = game.save
    _cult_tell(game, "preacher")
    count = save.arg("old_count", 0) + 1
    save.set_arg("old_count", count)
    if count == 1:
        game.dialog.show(escalate(game,
            low=[
                "Welcome, friend. Sit, sit. Take the weight off.",
                "We don't get many strangers through here.",
                "[c=dim]The harvest was hard this year. The Lord giveth.[/c]",
            ],
            mid=[
                "[s=slow]Welcome, friend.[/s]",
                "We don't get many [s=slow]strangers[/s] through here.",
                "[c=dim]Not lately. Not whole.[/c]",
            ],
            high=[
                "[c=red][s=slow]Welcome.[/s][/c]",
                "[c=dim]He doesn't blink.[/c]",
                "[c=red]We knew you were coming.[/c]",
            ],
        ), speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 2:
        game.dialog.show(escalate(game,
            low=[
                "Are you settling in alright at the Innkeeper's place?",
                "He's a good man. Quiet. Carries his griefs.",
                "[c=dim]We all carry something.[/c]",
            ],
            mid=[
                "[s=slow]Settling in.[/s][w=0.3]",
                "He's a good man. Carries [s=slow]griefs[/s].",
                "[c=dim]We all carry. We all share.[/c]",
            ],
            high=[
                "[c=dim]His mouth moves before the words arrive.[/c]",
                "[c=red]He is keeping you for us.[/c]",
                "[c=red][s=slow]Stay where he put you.[/s][/c]",
            ],
        ), speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 3:
        game.dialog.show([
            "[s=slow]...the boy next door.[/s][w=0.4]",
            "Sad business with his folks. Just sad.",
            "[c=dim]He's a special boy. The Lord has plans for him.[/c]",
        ], speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 4:
        game.dialog.show([
            "I saw you out by the well today.",
            "[c=dim]A long time to stand at a well.[/c]",
            "There's nothing to see in it.",
        ], speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 5:
        game.audio.play("low_pulse", 0.45)
        game.dialog.show([
            "[s=slow]...how is your sleep, friend?[/s]",
            "[c=dim]Sometimes the King in the Field walks at night.[/c]",
            "[c=dim]A traveler may meet him. It is not a thing[/c]",
            "[c=dim]he is allowed to leave with.[/c]",
        ], speaker="Preacher", voice="blip_low", portrait="old")
    else:
        game.dialog.show([
            "[c=dim]He smiles without warmth.[/c]",
            "[c=dim][s=slow]...we will see you tonight.[/s][/c]",
        ], speaker="Preacher", voice="blip_low", portrait="old")


# ---- The Kid ----

def kid_dialogue(game, npc):
    """The kid. Sole non-cult NPC. Sole survivor of his family.
    The cult has marked him as the next vessel. He doesn't fully
    understand but he knows enough to be scared and to recognise
    the player as the only adult who isn't part of it.

    Visit 7 is the binary follower-choice prompt. The kid asks
    'Can I come with you?' -- choosing Yes flips
    Game._kid_follower_active (he then spawns as a follower in
    every scene). Choosing No leaves him here; the cult comes
    for him at dusk."""
    save = game.save
    inv = game.player.inventory
    # Orb-recognition one-shot.
    if inv.has("orb") and not save.flag("kid_orb_noticed"):
        save.set_flag("kid_orb_noticed", True)
        game.dialog.show([
            "Mister... why does it sound like that?",
            "Is it... talking?",
            "[c=dim]It says my name when you're not looking.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        return
    count = save.arg("kid_count", 0) + 1
    save.set_arg("kid_count", count)
    if count == 1:
        game.dialog.show([
            "Hi mister. Did you sleep okay at the inn?",
            "[c=dim]You got mud on your boots again.[/c]",
            "You scraped some off last spring. By our gate.",
            "I waved but you didn't see me.",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        _evidence(game, "kid_v1",
            "The boy says he saw me scrape mud off my boots\n"
            "by his gate last spring.\n"
            "I was not in this town last spring."
        )
    elif count == 2:
        game.dialog.show([
            "You want a cracker? I have a whole sleeve.",
            "[c=dim](He holds out a saltine, broken neat in half.)[/c]",
            "Does your head still hurt? It hurt for a long time.",
            "[c=dim]After. I don't know after what.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 3:
        game.dialog.show([
            "I made you something. Here.",
            "[c=dim](Crayon on lined paper. A tall man. Too many eyes.)[/c]",
            "I see him sometimes. Out in the cornfield.",
            "[c=dim]He stands really still. He's always looking here.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        _evidence(game, "kid_v3",
            "The boy drew the spiral-eye figure.\n"
            "The same shape is scratched on the well rim and\n"
            "the schoolhouse walls.\n"
            "He says it stands in the cornfield at night."
        )
    elif count == 4:
        game.dialog.show([
            "My sister doesn't come to dinner anymore.",
            "[c=dim]I still set her a plate. I keep forgetting not to.[/c]",
            "Then I eat both plates so it's not weird.",
            "Her name was Ellie. She liked the small spoons.",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        _evidence(game, "kid_v4",
            "He has an older sister named Ellie.\n"
            "He still sets her a plate at supper.\n"
            "He is alone in that house and pretending he isn't."
        )
    elif count == 5:
        game.dialog.show([
            "Mister, can I ask about your mom?",
            "Was her hair the colour of cornsilk? Pale, almost white?",
            "[c=dim]She had it pinned up. There was a window behind her.[/c]",
            "I dreamed about her. I don't know why.",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        _evidence(game, "kid_v5",
            "The boy described my mother's hair, and the\n"
            "kitchen window behind her.\n"
            "He has never met her. The polaroid is in my pocket.\n"
            "He has never seen the polaroid."
        )
    elif count == 6:
        game.audio.play("breath", 0.30)
        game.dialog.show([
            "[s=slow]Mister.[/s] I want you to take this.",
            "[c=dim](He holds out a cloth doll. The stitching is rough.)[/c]",
            "It was Ellie's. She gave it to me when she got too old.",
            "[c=dim]I'm too old now too. You take her. For luck.[/c]",
            "[c=dim]Don't let the others see it. They'll know it was hers.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        if not save.flag("kid_gave_doll"):
            save.set_flag("kid_gave_doll", True)
            game.player.inventory.add("old_doll", 1)
            game.show_notice("The boy gives you the cloth doll.")
    elif count == 7 and not save.flag("kid_choice_made"):
        # The follower-choice prompt. Yes flips the kid into a
        # follower in every scene the player loads from now on.
        # No leaves him here -- the cult comes for him at dusk.
        def _on_pick(idx):
            save.set_flag("kid_choice_made", True)
            if idx == 0:
                # Yes
                save.set_flag("kid_taken", True)
                game.audio.play("low_pulse", 0.45)
                game.dialog.show([
                    "[s=slow]...okay.[/s]",
                    "[c=dim](He stands up. He doesn't bring anything.)[/c]",
                    "[c=dim](He waits by the door.)[/c]",
                ], speaker="Boy", voice="blip_kid", portrait="kid")
                game._kid_follower_active = True
            else:
                # No
                save.set_flag("kid_left", True)
                game.audio.play("door_distant", 0.55)
                game.dialog.show([
                    "[c=dim](He nods. He doesn't say anything.)[/c]",
                    "[c=dim](He sits back down on the bed.)[/c]",
                    "[s=slow][c=dim]...okay.[/c][/s]",
                ], speaker="Boy", voice="blip_kid", portrait="kid")
        game.dialog.show_choice(
            "Mister... can I come with you?",
            ["Yes. Come on.", "I can't take you. I'm sorry."],
            _on_pick,
            speaker="Boy", voice="blip_kid", portrait="kid",
        )
    elif count >= 8 and save.flag("kid_left"):
        # If the player said no, the kid is no longer at his house
        # -- the cult took him. This branch fires on the visit
        # AFTER the No, when the player walks back into kid_house.
        game.dialog.show([
            "[c=dim]The bed is made. The drawings are gone.[/c]",
            "[c=dim]No one is in the house.[/c]",
        ], speaker="", voice="blip_soft", portrait="kid")
    elif count >= 8:
        # If the player said yes, the kid follower is now wherever
        # the player is. They wouldn't be talking to a copy in the
        # kid_house. But just in case (e.g. player went back without
        # the follower for some reason), fall through to a quiet
        # absence note.
        game.dialog.show([
            "[c=dim]Empty house. Empty bed. The drawings still on\n"
            "the walls.[/c]",
        ], speaker="", voice="blip_soft", portrait="kid")
    else:
        game.dialog.show([
            "[c=dim]The boy is quiet for a long time.[/c]",
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
    """The store has very little left. Pre-rite the shelves are
    nearly empty -- a single notepad and a piece of charcoal."""
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
        game.dialog.show(escalate(game,
            low=[
                "Mornin'. Down from up north?",
                "Not a lot left on the shelves but you're welcome to look.",
            ],
            mid=[
                "[s=slow]Mornin'.[/s][w=0.3]",
                "[c=dim]His glasses don't reflect anything.[/c]",
                "Not a lot left on the shelves.",
            ],
            high=[
                "[c=dim]The lenses are filled with black.[/c]",
                "[c=red][s=slow]We see you found us.[/s][/c]",
            ],
        ), speaker="Store-Owner", voice="blip_high",
            portrait="shopkeep", on_complete=_then_open)
        return
    if count == 2:
        def _then_open():
            _shop_open_menu(game)
        game.dialog.show([
            "Back in.",
            "[c=dim]Folks been moving slow this week.[/c]",
        ], speaker="Store-Owner", voice="blip_high",
            portrait="shopkeep", on_complete=_then_open)
        return
    if count == 3:
        game.dialog.show([
            "I'm closed.",
            "[c=dim]I don't think I ever was open.[/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    if count == 4:
        game.dialog.show([
            "[s=slow]...do I know you?[/s]",
            "[c=dim]You keep coming through that door.[/c]",
            "[c=dim]I don't remember you using it.[/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    if count == 5:
        game.audio.play("door_distant", 0.45)
        game.dialog.show([
            "[c=dim]He looks up but does not see you.[/c]",
            "[c=dim][s=slow]is somebody there?[/s][/c]",
        ], speaker="Store-Owner", voice="blip_high", portrait="shopkeep")
        return
    game.dialog.show([
        "[c=dim]He sits very still behind the counter.[/c]",
    ], speaker="", voice="blip_soft", portrait="shopkeep")


# ---- The Sheriff (legacy key: fisherman_dialogue, on Sheriff NPC in
# his office) ----

def fisherman_dialogue(game, npc):
    """The Sheriff sits in his office. Doesn't patrol -- the lesser
    cult does the chasing. He stays in the chair. Friendly on the
    surface, watching everything."""
    save = game.save
    _cult_tell(game, "sheriff")
    n = save.arg("fisher_count", 0) + 1
    save.set_arg("fisher_count", n)
    if n == 1:
        game.dialog.show(escalate(game,
            low=[
                "Howdy.",
                "Driftin' through? You can leave the truck at the diner,",
                "the lot's empty.",
                "[c=dim]Roads ice up after dark, this time of year.[/c]",
            ],
            mid=[
                "[s=slow]Howdy.[/s]",
                "[c=dim]His badge isn't quite straight.[/c]",
                "[c=dim]Roads ice up after dark.[/c]",
            ],
            high=[
                "[c=red][s=slow]You drove a long way for this.[/s][/c]",
                "[c=dim]His mouth doesn't move with the words.[/c]",
            ],
        ), speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 2:
        game.dialog.show([
            "Make sure you sign in if you're staying more than a night.",
            "[c=dim]County wants paperwork on every visitor.[/c]",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 3:
        game.dialog.show([
            "[c=dim]I saw you up near the well today.[/c]",
            "[c=dim]Nothing to see down there. Just stones.[/c]",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 4:
        game.dialog.show([
            "[s=slow]...you keep coming around at the same hour.[/s]",
            "[c=dim]I haven't moved in a while.[/c]",
        ], speaker="Sheriff", voice="blip_gruff", portrait="guard")
    else:
        game.dialog.show([
            "[c=dim]He stares at the radio. He does not turn.[/c]",
        ], speaker="", voice="blip_soft", portrait="guard")


# ---- The Innkeeper ----

def innkeeper_dialogue(game, npc):
    """THRESHOLD: the Innkeeper is the player's host AND the cult's
    keeper. He runs the inn, owns the house the player sleeps in,
    and steps into the front-door confrontation when the player
    tries to leave with cult evidence.

    The Innkeeper's quest is the LIQUOR CRATE: he tells the player
    he's prepping for guests / a dinner service that never seems
    to actually happen, and asks them to fetch a stashed crate of
    wine from the cornfield. The truth -- discovered via a hidden
    note in the maze -- is that the crate is for a 'religious
    service.' On turn-in: player gets the woodshed key (so the
    locked village/farm shed opens) AND their car keys back.

    The legacy `cellar_bottle` quest is gone. Saves that already
    set `innkeeper_bottle_done` simply fall through; the crate
    quest still fires for them. The orb hand-in remains the next
    stage."""
    save = game.save
    _cult_tell(game, "innkeeper")
    inv = game.player.inventory
    # PRIORITY 1: turn in the liquor crate. The Innkeeper trades
    # only the cellar key -- the player has to descend, find what
    # else is down there, and earn the rest of the chain. Arms
    # the orb stage as before so the across-the-river hook lands
    # the next time the player talks to him.
    if inv.has("liquor_crate"):
        inv.remove("liquor_crate", 1)
        save.set_flag("innkeeper_quest_done", True)
        save.set_flag("axe_quest_started", True)
        save.set_flag("innkeeper_bottle_done", True)   # legacy alias
        if not inv.has("cellar_key"):
            inv.add("cellar_key", 1)
        game.audio.play("pickup_rare", 0.7)
        if save.flag("crate_note_read"):
            # Player has seen the note -- the innkeeper's tone
            # shifts. He knows the player knows.
            game.dialog.show([
                "[c=dim]He sets the crate on the bar without looking.[/c]",
                "Good of you.",
                "[c=dim]Cellar key. There's something stuck down there.[/c]",
                "[s=slow]I'd be obliged if you took it out.[/s]",
                "[c=dim]Tomorrow. He said tomorrow.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
        else:
            game.dialog.show([
                "Ah -- there it is. Bless you.",
                "[c=dim]He inspects each bottle, counts under his breath.[/c]",
                "Service tomorrow. The whole town comes through.",
                "[c=dim]Here. Cellar key. The hatch under the kitchen.",
                "There's tools down there I'd rather you fetched than",
                "me -- old back, you understand.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    # Stage-2 turn-in -- the cellar bottle. Player descended,
    # found a bottle the Innkeeper had been keeping; he trades
    # the car keys back for it. Final piece of the trade chain
    # before the orb stage. (Walking past the shed key in the
    # cellar isn't enough -- you have to bring him the bottle.)
    if inv.has("cellar_bottle"):
        inv.remove("cellar_bottle", 1)
        save.set_flag("cellar_bottle_done", True)
        if not inv.has("car_keys"):
            inv.add("car_keys", 1)
        game.audio.play("pickup_rare", 0.7)
        game.dialog.show([
            "[c=dim]He weighs the bottle in one hand.[/c]",
            "Good. Yes. That'll do.",
            "[c=dim]Your car keys. Take them.[/c]",
            "There's a friend of mine across the river up north.",
            "He hasn't sent word in months. If you're going that\n"
            "way, bring me back what he's been holding.",
        ], speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    # Stage-2 turn-in -- the orb. The Innkeeper pretends it's just
    # an ugly trinket he wants gone.
    if inv.has("orb"):
        inv.remove("orb", 1)
        save.set_flag("orb_quest_done", True)
        game.audio.play("low_pulse", 0.45)
        game.dialog.show([
            "Good of you. Set it on the table.",
            "[c=dim]It can stay here a while.[/c]",
            "[c=dim]Don't tell anyone you were across the river.[/c]",
        ], speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    if save.flag("orb_quest_done"):
        nq = save.arg("innkeeper_post_count", 0) + 1
        save.set_arg("innkeeper_post_count", nq)
        if nq == 1:
            game.dialog.show(
                ["Coffee's on. Help yourself.",
                 "[c=dim]I'm out for a walk a while.[/c]"],
                speaker="Innkeeper", voice="blip_low", portrait="old",
            )
        elif nq == 2:
            game.dialog.show(
                ["[c=dim]The kitchen smells of pine again.[/c]",
                 "[c=dim]He's not here. He's never quite here.[/c]"],
                speaker="", voice="blip_soft", portrait="old",
            )
        else:
            game.dialog.show(
                ["[c=dim]He nods at you without looking up.[/c]"],
                speaker="", voice="blip_soft", portrait="old",
            )
        return
    # Already collected the crate but holding orb? Handled above.
    # Already arming axe quest but no crate? Reminder.
    if save.flag("axe_quest_started"):
        # The crate has already been turned in but the player has
        # come back. Route them to the orb stage.
        game.dialog.show(
            ["My friend. Across the river up north.",
             "Bring me back what he's been holding.",
             "[c=dim]He hasn't sent word in months.[/c]"],
            speaker="Innkeeper", voice="blip_low", portrait="old",
        )
        return
    if not save.flag("innkeeper_quest_started"):
        save.set_flag("innkeeper_quest_started", True)
        game.dialog.show(escalate(game,
            low=[
                "Up early. Good. I need a hand.",
                "[c=dim]He polishes a glass that's already clean.[/c]",
                "Big service tomorrow. The whole town comes through\n"
                "for it. I stocked a crate of wine out by the field\n"
                "last week so it'd be cool by now.",
                "Find it for me and I'll square things up. Your car\n"
                "keys, the shed key -- everything's yours.",
                "[c=dim]Try the corn. The deep rows.[/c]",
            ],
            mid=[
                "Up early. Good.",
                "[c=dim]He doesn't quite meet your eye.[/c]",
                "I have a service tomorrow. Stocked a crate of wine\n"
                "out by the field. Bring it back and we're square.",
                "[s=slow]The corn rows. The deep ones.[/s]",
            ],
            high=[
                "[s=slow]You're up.[/s]",
                "[c=dim]He's been waiting in the kitchen with the\n"
                "lights off.[/c]",
                "The service is tomorrow. I need that crate.",
                "[s=slow]The deep rows. Walk in until you can't see",
                "the road.[/s]",
            ],
        ), speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    game.dialog.show(
        ["The crate. Out in the corn rows.",
         "Walk in until you can't see the road.",
         "[c=dim]The service is tomorrow.[/c]"],
        speaker="Innkeeper", voice="blip_low", portrait="old",
    )


# ---- The Fisherman: NPC retired in THRESHOLD. Function preserved
# only for the static Sheriff in the office (which uses fisherman
# as its dialogue_fn binding). Leave intact above. ----


# ---- The Guard: replaced by the Sheriff. Function below is
# preserved for save-state compat -- it's no longer wired to any
# NPC in the new fiction. ----

def guard_dialogue(game, npc):
    """Legacy. Not wired in THRESHOLD. Falls through to the Sheriff
    line for save-state compatibility."""
    fisherman_dialogue(game, npc)


# ---- The Photo / Static figure / Doll ---- preserved as before.

def static_figure_dialogue(game, npc):
    """Legacy unbound dialogue. Preserved for any old save still
    pointing at a static_figure NPC."""
    game.audio.play("whisper", 0.8)
    game.dialog.show([
        "[c=dim][s=veryslow]you took longer than last time.[/s][/c]",
        "[c=dim][s=slow]go back. before they notice.[/s][/c]",
    ], speaker="???", voice="whisper", portrait="static_figure")


def doll_dialogue(game, npc):
    game.audio.play("blip_glitch", 0.4)
    game.dialog.show([
        "[c=dim](A small porcelain doll. Its eyes are crossed out.)[/c]",
        "[c=red][s=slow]'thank you for finding me'[/s][/c]",
    ], speaker="", voice="blip_soft", portrait="doll")


def bowl_examine(game):
    """Legacy. The bowl/easter-egg mechanic is gone in THRESHOLD."""
    pass


def basement_photo_dialogue(game, npc):
    """The Photo NPC in the Innkeeper's basement. The framed
    photograph IS the player's mother."""
    save = game.save
    n = save.arg("photo_reads", 0) + 1
    save.set_arg("photo_reads", n)
    if n == 1:
        game.dialog.show([
            "[c=dim](A framed photograph on a shelf.)[/c]",
            "[c=dim]A woman with your jaw, leaning against a kitchen\n"
            "window.[/c]",
            "[c=dim]Your mother. You haven't seen this picture.[/c]",
            "[c=dim]Why does the Innkeeper have it.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if not save.flag("polaroid_taken"):
            save.set_flag("polaroid_taken", True)
            game.player.inventory.add("polaroid", 1)
            game.show_notice("You take the photograph.")
            # Lifting her face out of the frame turns the world
            # over. Whatever time it was outside, it is night now.
            save.set_arg("day_phase", "night")
        _evidence(game, "innkeeper_had_photo",
            "The Innkeeper had your mother's picture.\n"
            "They were not friends.\n"
            "They were not anything you understood."
        )
    else:
        game.dialog.show([
            "[c=dim](The empty frame. You took the photo.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
