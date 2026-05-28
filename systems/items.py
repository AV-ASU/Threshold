"""Item definitions and inventory.

Saves are in-memory only (single session, no disk), so item keys are NOT
load-bearing across runs -- unused items get deleted outright rather than
kept as reskins. Keys only need to match the code that references them
within a run.

The Inventory class is unchanged.
"""
import time

ITEM_DEFS = {
    # ---- Core items (in circulation) ----
    "woodshed_key":  {"name": "Woodshed Key",
                       "kind": "key",
                       "desc": "A key."},
    "flashlight":    {"name": "Flashlight",
                       "kind": "key",
                       "desc": "A heavy steel flashlight. Press [F] to "
                               "switch it on in the dark -- but a light in "
                               "the dark is a thing that can be seen. The "
                               "longer it burns, the more the King feels "
                               "you."},
    "sigil_rubbing": {"name": "The Pallid Mask",
                       "kind": "lore",
                       "desc": "The King's own pale half-mask, made an "
                               "object. His face. It seats into the "
                               "Playscript's cover."},
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
                       "desc": "Her descent, in her own words."},
    "unsent_letter": {"name": "Mara's Letter",
                       "kind": "lore",
                       "desc": "Stamped, never mailed. Opens \"Dad.\" "
                               "Closes: \"I'm not lost. I've never been "
                               "this close.\""},
    # ---- Re-meaned existing items ----
    "playscript":           {"name": "A Yellow Playscript",
                       "kind": "key",
                       "desc": "A yellow playscript that has an "
                               "indentation of a mask on the cover."},
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

    def equip(self, key):
        d = ITEM_DEFS.get(key)
        if not d or d["kind"] not in ("weapon", "armor"):
            return False
        slot = d["kind"]
        prev = self.equipped[slot]
        if prev:
            self.add(prev, 1)
        self.equipped[slot] = key
        self.remove(key, 1)
        return True

    def unequip(self, slot):
        prev = self.equipped[slot]
        if prev:
            self.add(prev, 1)
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
