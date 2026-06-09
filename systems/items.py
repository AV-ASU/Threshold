"""Item definitions and inventory.

Saves are in-memory only (single session, no disk), so there is no
save-migration concern across runs -- a cut item can be deleted outright
rather than kept as a reskin for old saves. WITHIN the codebase, though,
the surviving item keys ARE load-bearing (Bible §7): dialogue gates and
scene logic reference them by name, so a key may not be renamed without
updating every reference.

The Inventory class is unchanged.
"""

ITEM_DEFS = {
    # ---- Core items (in circulation) ----
    "pistol":        {"name": "Revolver",
                       "kind": "weapon",
                       "desc": "Your sidearm. Left-click fires it in "
                               "the way you're facing. While the case is "
                               "still shallow a clean shot drops a cultist; "
                               "once you understand too much (3+ evidence) the "
                               "rounds only stagger them. The deeper you "
                               "see, the less the world lets you kill."},
    "pistol_ammo":   {"name": "Cartridges",
                       "kind": "key",
                       "desc": "Pistol rounds. Never as many as you'd like."},
    "newspaper":     {"name": "Yesterday's Paper",
                       "kind": "lore",
                       "desc": "The Minneapolis paper for April 14. "
                               "Yesterday. Picked up before the drive "
                               "north. Ordinary headlines, box scores, the "
                               "funnies. The freshest thing in Brimley by "
                               "months."},
    "woodshed_key":  {"name": "Woodshed Key",
                       "kind": "key",
                       "desc": "A key."},
    "flashlight":    {"name": "Flashlight",
                       "kind": "key",
                       "desc": "A heavy steel flashlight. Press [F] to "
                               "switch it on in the dark. But a light in "
                               "the dark is a thing that can be seen. The "
                               "longer it burns, the more the King feels "
                               "you."},
    "sigil_rubbing": {"name": "The Pallid Mask",
                       "kind": "lore",
                       "desc": "The King's own pale half-mask, made an "
                               "object. His face. The fold opens for it. So, "
                               "you suspect, does the door in the deep."},
    "cross":         {"name": "The Preacher's Cross",
                       "kind": "lore",
                       "desc": "A plain silver cross. It was still warm "
                               "when you took it. You try not to think "
                               "about that."},
    "robe":          {"name": "Old Robe",
                       "kind": "lore",
                       "desc": "A coarse wool robe."},
    "mom_notebook":  {"name": "Mara's Journal",
                       "kind": "lore",
                       "desc": "Her last entries, in a hand that gets calmer "
                               "as it goes:\n\n"
                               "\"I just had this urge to go north. Stopped "
                               "for gas in this town. Everyone smiles like "
                               "I'm already home.\"\n\n"
                               "\"I had Him wrong. He isn't out past the corn. "
                               "He's under it. You don't walk to Him. You go "
                               "down.\"\n\n"
                               "\"There's a mouth below the town. The others "
                               "went ahead of me, down it, and not one has "
                               "climbed back up. Tomorrow I follow them down. "
                               "I feel so close now.\""},
    "unsent_letter": {"name": "Mara's Letter",
                       "kind": "lore",
                       "desc": "Stamped, never mailed.\n\n"
                               "\"Dad. ...I'm sorry for how I left. I couldn't "
                               "explain it and have it sound sane. The dreams "
                               "aren't dreams anymore. They're full of answers. "
                               "I'm just hunting the questions now. Don't come "
                               "after me. I'm not lost. I've never been this "
                               "close.\""},
    # ---- The cult's testimony (three found fragments; gate nothing) ----
    # The congregation's own record, split across three leaves found down the
    # descent. The cult's voice lives in the DESCRIPTION (their personal
    # testimony); the PI's reaction is logged to `notes` on pickup. They are
    # pure lore -- the keystone is the Pallid Mask alone now (the old single
    # `playscript` item that half-made the keystone is retired). The aches are
    # solvable problems (a debt, an addiction, a broken back); the arc runs
    # from a human problem, to the bargain, to the self lost in the dig.
    "cult_calling":  {"name": "The Calling",
                       "kind": "lore",
                       "desc": "Cultist personal testimony:\n\n"
                               "\"I had been drinking for eleven years. I quit "
                               "a hundred times and never once stayed quit. "
                               "Then I dreamed of a door, and a voice that "
                               "said it could take it from me clean. I have "
                               "not touched a drop since I came.\"\n\n"
                               "\"The bank took the farm in the spring. By "
                               "summer I was dreaming the same dream as a "
                               "hundred strangers, and every one of us was "
                               "already driving north to the same town.\""},
    "cult_bargain":  {"name": "The Bargain",
                       "kind": "lore",
                       "desc": "Cultist personal testimony:\n\n"
                               "\"My back has been broken nine years. He says "
                               "I will stand straight the day our work is "
                               "finished. We are nearly finished. Soon we can "
                               "all help ourselves.\"\n\n"
                               "\"He asks so little of us. Only everything, "
                               "and only the once.\""},
    "cult_digging":  {"name": "The Digging",
                       "kind": "lore",
                       "desc": "Cultist personal testimony:\n\n"
                               "\"There are only a few feet of earth left "
                               "between us and the door now. We dig in shifts "
                               "so the work never stops, one hand on the rite, "
                               "one hand in the dirt. We have only to reach "
                               "the door.\"\n\n"
                               "\"I do not sleep. I dig. We hold the rite and "
                               "we dig and we do not stop. Almost there. "
                               "Almost. The door. The door. The door.\""},
    "lumber_axe":    {"name": "Splitting Axe",
                       "kind": "weapon",
                       "desc": "An axe for chopping wood.",
                       "atk": 0},
    "rope":          {"name": "Coil of Rope",  "kind": "key",
                       "desc": "A coil of rope."},
}


def effective_desc(key, save=None):
    """Return the inventory description for `key`.

    Signature is preserved for callers; the `save` parameter is
    accepted but ignored (no dynamic flavour anymore)."""
    return ITEM_DEFS.get(key, {}).get("desc", "")


# Mara's Journal, in her own words: three short leaves the player turns
# one Enter at a time in the inventory. The arc is the whole of her
# descent in miniature -- the ache that drew her, the dream of the door,
# the glad walk down toward it (NARRATIVE 1b: she was answered, not
# deceived). Turning past the LAST page is what fires the door-dream
# flashback, so the count here must stay at three (it drives the
# `notebook_pages_read` 3-gate the Game system polls). No dashes in any
# of this text -- it is read by the player.
MARA_JOURNAL_PAGES = [
    "I came north because I could not stand the quiet of that "
    "apartment one more night. They told me grief would pass. It did "
    "not pass. It only learned my name.\n\n"
    "Brimley is small, and kind the way tired places are. No one here "
    "asks what I am running from. They look at me like they already "
    "know.",

    "I have started to dream of a door. Plain wood, a little warped, "
    "standing alone in a field with nothing around it. I know, the way "
    "you know things in dreams, that everything I have ever wanted is "
    "on the other side.\n\n"
    "It is not frightening. That is the part I cannot explain to anyone "
    "who has not felt it. It feels like being remembered.",

    "They are not strangers. They dreamed the same door, every one of "
    "them, and drove here the way I did. We are digging down to it "
    "together now. My hands are raw and I have never been so happy.\n\n"
    "I was not tricked. I was asked, and I said yes. I am not lost. I "
    "have never been this close.",
]


def journal_page(save):
    """Return (page_text, page_index, page_count) for Mara's Journal,
    keyed to how many times the player has turned through it
    (`notebook_pages_read`). Opening the journal shows page 1 even
    before the first Enter, so the words are visible immediately -- the
    read counter only ever advances the page forward, clamped to the
    last leaf."""
    read = save.arg("notebook_pages_read", 0) if save is not None else 0
    idx = max(0, min(read, len(MARA_JOURNAL_PAGES) - 1))
    return MARA_JOURNAL_PAGES[idx], idx, len(MARA_JOURNAL_PAGES)


class Inventory:
    """Simple stackable inventory + 2 equipment slots."""
    def __init__(self):
        self.items = []  # list of (key, qty)
        self.equipped = {"weapon": None, "armor": None}

    def add(self, key, qty=1):
        for i, (k, q) in enumerate(self.items):
            if k == key:
                self.items[i] = (k, q + qty)
                return
        self.items.append((key, qty))

    def remove(self, key, qty=1):
        for i, (k, q) in enumerate(self.items):
            if k == key:
                if q <= qty:
                    self.items.pop(i)
                else:
                    self.items[i] = (k, q - qty)
                return True
        return False

    def has(self, key):
        return any(k == key for k, _ in self.items)

    def count(self, key):
        """How many of `key` are stacked (0 if none) -- used for ammo."""
        for k, q in self.items:
            if k == key:
                return q
        return 0

    def equip(self, key):
        """Set the active item for its slot. POINTER model: the item STAYS in
        `items` (you're still carrying it) and `equipped[slot]` just names which
        carried item is active. This matches `Game._active_weapon`, which reads
        the weapon slot as a pointer and requires the weapon to still be
        `has()`-carried -- the old move-out-of-items semantics silently broke
        that (the gun + axe could never round-trip through the slot)."""
        d = ITEM_DEFS.get(key)
        if not d or d["kind"] not in ("weapon", "armor"):
            return False
        if not self.has(key):
            return False
        self.equipped[d["kind"]] = key
        return True

    def unequip(self, slot):
        # Pointer model: the item was never removed from `items`, so just
        # clear the pointer.
        self.equipped[slot] = None

    def weapon_atk(self):
        # Weapons do nothing; returns 0 always.
        return 0

    def armor_def(self):
        return 0

    def to_save(self):
        return {"items": [[k, q] for k, q in self.items],
                "equipped": dict(self.equipped)}

    def from_save(self, data):
        self.items = [tuple(x) for x in data.get("items", [])]
        eq = data.get("equipped", {})
        self.equipped = {"weapon": eq.get("weapon"), "armor": eq.get("armor")}
