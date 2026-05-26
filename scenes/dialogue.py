"""All NPC dialogue functions.

The story text here is intentionally generic placeholder copy. Every
function, signature, and helper is preserved (game.py and the scenes
import them), but the spoken lines carry no lore.
"""
import time
import re


def _evidence(game, name, content, weight=0.10):
    """Surface a one-shot narrator line and record it in the save's
    `evidence` list so the notebook UI can show it. Gated by a
    per-name save flag so the same beat never re-fires.

    `weight` is how much this piece raises the visibility FLOOR -- the
    King-in-Yellow "knowing dooms you" engine. Deeper finds weigh more.
    Signature preserved for callers (scenes + game.py)."""
    if game is None or game.save is None:
        return
    flag = f"evidence_{name}"
    if game.save.flag(flag):
        return
    game.save.set_flag(flag, True)
    lines = content.split("\n") if isinstance(content, str) else list(content)
    log = game.save.arg("evidence", [])
    if isinstance(log, list):
        # Each entry: {"name": slug, "lines": [...], "weight": float}.
        # Tolerates older bare-string entries without migrating or crashing.
        if not any(isinstance(e, dict) and e.get("name") == name
                   for e in log):
            log.append({"name": name, "lines": list(lines), "weight": weight})
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
    plain = [
        "Hello there.",
        "[c=dim]Not much to say.[/c]",
    ]
    if count == 1:
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 2:
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 3:
        game.dialog.show(plain,
                         speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 4:
        game.dialog.show(plain,
                         speaker="Preacher", voice="blip_low", portrait="old")
    elif count == 5:
        game.dialog.show(plain,
                         speaker="Preacher", voice="blip_low", portrait="old")
    else:
        game.dialog.show([
            "[c=dim]Nothing to say.[/c]",
        ], speaker="Preacher", voice="blip_low", portrait="old")


# ---- The Kid ----

def kid_dialogue(game, npc):
    """A generic boy NPC. Placeholder lines per visit count."""
    save = game.save
    inv = game.player.inventory
    # Orb-recognition one-shot (kept; flow unchanged, text bland).
    if inv.has("orb") and not save.flag("kid_orb_noticed"):
        save.set_flag("kid_orb_noticed", True)
        game.dialog.show([
            "What's that?",
            "[c=dim]Just passing through?[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        return
    count = save.arg("kid_count", 0) + 1
    save.set_arg("kid_count", count)
    if count == 1:
        game.dialog.show([
            "Hi there.",
            "[c=dim]Just passing through?[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 2:
        game.dialog.show([
            "Hello again.",
            "[c=dim]Not much going on.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 3:
        game.dialog.show([
            "Hi.",
            "[c=dim]Nothing much.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 4:
        game.dialog.show([
            "Hello.",
            "[c=dim]...[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 5:
        game.dialog.show([
            "Hi there.",
            "[c=dim]Not much to say.[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
    elif count == 6:
        game.dialog.show([
            "Here, take this.",
            "[c=dim](He hands you a small cloth doll.)[/c]",
        ], speaker="Boy", voice="blip_kid", portrait="kid")
        if not save.flag("kid_gave_doll"):
            save.set_flag("kid_gave_doll", True)
            game.player.inventory.add("old_doll", 1)
            game.show_notice("The boy gives you the cloth doll.")
    else:
        game.dialog.show([
            "[c=dim]Nothing to say.[/c]",
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
    save = game.save
    _cult_tell(game, "sheriff")
    n = save.arg("fisher_count", 0) + 1
    save.set_arg("fisher_count", n)
    plain = [
        "Howdy.",
        "[c=dim]Just passing through?[/c]",
    ]
    if n == 1:
        game.dialog.show(escalate(game, low=plain, mid=plain, high=plain),
                         speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 2:
        game.dialog.show(plain,
                         speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 3:
        game.dialog.show(plain,
                         speaker="Sheriff", voice="blip_gruff", portrait="guard")
    elif n == 4:
        game.dialog.show(plain,
                         speaker="Sheriff", voice="blip_gruff", portrait="guard")
    else:
        game.dialog.show([
            "[c=dim]He doesn't look up.[/c]",
        ], speaker="", voice="blip_soft", portrait="guard")


# ---- The Innkeeper ----

def innkeeper_dialogue(game, npc):
    """The Innkeeper's quest chain (crate -> cellar key -> bottle ->
    car keys -> orb) is preserved mechanically. All flags, item
    grants, and branch order are unchanged; only the spoken text is
    blanked."""
    save = game.save
    _cult_tell(game, "innkeeper")
    inv = game.player.inventory
    # PRIORITY 1: turn in the liquor crate -> grants cellar key.
    if inv.has("liquor_crate"):
        inv.remove("liquor_crate", 1)
        save.set_flag("innkeeper_quest_done", True)
        save.set_flag("axe_quest_started", True)
        save.set_flag("innkeeper_bottle_done", True)   # legacy alias
        if not inv.has("cellar_key"):
            inv.add("cellar_key", 1)
        game.audio.play("pickup_rare", 0.7)
        if save.flag("crate_note_read"):
            game.dialog.show([
                "[c=dim]He sets the crate on the bar.[/c]",
                "Thanks for that.",
                "[c=dim]Here's the cellar key.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
        else:
            game.dialog.show([
                "There it is. Thanks.",
                "[c=dim]Here's the cellar key. Hatch is under the\n"
                "kitchen.[/c]",
            ], speaker="Innkeeper", voice="blip_low", portrait="old")
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
            "If you head up north, bring me back what's there.",
        ], speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    # Stage-3 turn-in -- the orb.
    if inv.has("orb"):
        inv.remove("orb", 1)
        save.set_flag("orb_quest_done", True)
        game.audio.play("low_pulse", 0.45)
        game.dialog.show([
            "Thanks. Set it on the table.",
            "[c=dim]...[/c]",
        ], speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    if save.flag("orb_quest_done"):
        nq = save.arg("innkeeper_post_count", 0) + 1
        save.set_arg("innkeeper_post_count", nq)
        if nq == 1:
            game.dialog.show(
                ["Coffee's on. Help yourself.",
                 "[c=dim]...[/c]"],
                speaker="Innkeeper", voice="blip_low", portrait="old",
            )
        elif nq == 2:
            game.dialog.show(
                ["[c=dim]He's not here.[/c]"],
                speaker="", voice="blip_soft", portrait="old",
            )
        else:
            game.dialog.show(
                ["[c=dim]He nods without looking up.[/c]"],
                speaker="", voice="blip_soft", portrait="old",
            )
        return
    if save.flag("axe_quest_started"):
        game.dialog.show(
            ["If you head up north, bring me back what's there.",
             "[c=dim]...[/c]"],
            speaker="Innkeeper", voice="blip_low", portrait="old",
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
                         speaker="Innkeeper", voice="blip_low", portrait="old")
        return
    game.dialog.show(
        ["The crate's out in the corn rows.",
         "[c=dim]...[/c]"],
        speaker="Innkeeper", voice="blip_low", portrait="old",
    )


# ---- The Guard: legacy, not wired. Falls through to the Sheriff. ----

def guard_dialogue(game, npc):
    """Legacy. Not wired. Falls through to the Sheriff line for
    save-state compatibility."""
    fisherman_dialogue(game, npc)


# ---- Legacy unbound dialogues, preserved for old saves. ----

def static_figure_dialogue(game, npc):
    """Legacy unbound dialogue. Preserved for old saves."""
    game.audio.play("whisper", 0.8)
    game.dialog.show([
        "[c=dim]...[/c]",
    ], speaker="???", voice="whisper", portrait="static_figure")


def doll_dialogue(game, npc):
    game.audio.play("blip_glitch", 0.4)
    game.dialog.show([
        "[c=dim](A small cloth doll.)[/c]",
    ], speaker="", voice="blip_soft", portrait="doll")


def bowl_examine(game):
    """Legacy no-op."""
    pass


def basement_photo_dialogue(game, npc):
    """The Photo NPC in the basement. Flow preserved (grants the
    polaroid item); text blanked."""
    save = game.save
    n = save.arg("photo_reads", 0) + 1
    save.set_arg("photo_reads", n)
    if n == 1:
        game.dialog.show([
            "[c=dim](A framed photograph on a shelf.)[/c]",
            "[c=dim]Nothing here.[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
        if not save.flag("polaroid_taken"):
            save.set_flag("polaroid_taken", True)
            game.player.inventory.add("polaroid", 1)
            game.show_notice("You take the photograph.")
    else:
        game.dialog.show([
            "[c=dim](An empty frame.)[/c]",
        ], speaker="", voice="blip_soft", portrait="narrator")
