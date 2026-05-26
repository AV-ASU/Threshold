"""Item definitions and inventory.

Item TEXT (names + descriptions) is intentionally generic placeholder
copy. The KEYS, `kind` fields, and numeric fields are load-bearing
(game logic + old saves depend on them) and must not change.

The Inventory class is unchanged.
"""
import time

ITEM_DEFS = {
    # ---- Core items (in circulation) ----
    "car_keys":      {"name": "Car Keys",
                       "kind": "key",
                       "desc": "Some keys."},
    "woodshed_key":  {"name": "Woodshed Key",
                       "kind": "key",
                       "desc": "A key."},
    "charcoal":      {"name": "Charcoal Stick",
                       "kind": "key",
                       "desc": "A stick of charcoal."},
    "paper":         {"name": "A Note",
                       "kind": "lore",
                       "desc": "A folded note."},
    "cellar_key":    {"name": "Cellar Key",
                       "kind": "key",
                       "desc": "A key."},
    "sigil_rubbing": {"name": "A Rubbing",
                       "kind": "lore",
                       "desc": "Charcoal on paper."},
    "kid_drawing":   {"name": "A Drawing",
                       "kind": "lore",
                       "desc": "A child's drawing."},
    "robe":          {"name": "Old Robe",
                       "kind": "lore",
                       "desc": "A coarse wool robe."},
    "mom_notebook":  {"name": "Mara's Journal",
                       "kind": "lore",
                       "desc": "Her descent, in her own words."},
    "cellar_bottle": {"name": "Cellar Bottle",
                       "kind": "key",
                       "desc": "A dusty bottle."},
    # ---- Re-meaned existing items ----
    "orb":           {"name": "A Yellow Playscript",
                       "kind": "key",
                       "desc": "A yellow playscript that has an "
                               "indentation of a mask on the cover."},
    "polaroid":      {"name": "Case Photo",
                       "kind": "lore",
                       "desc": "A faded photo of Mara Blaine -- the "
                               "woman you were hired to find."},
    "lumber_axe":    {"name": "Splitting Axe",
                       "kind": "weapon",
                       "desc": "An axe for chopping wood.",
                       "atk": 0},
    # ---- Backward-compat stubs (in DEFS so old saves don't crash;
    #      not dropped by anything new) ----
    "knife":         {"name": "Pocket Knife",  "kind": "weapon",
                       "desc": "A small knife.", "atk": 0},
    "short_sword":   {"name": "Bent Blade",    "kind": "weapon",
                       "desc": "A bent blade.", "atk": 0},
    "bandit_axe":    {"name": "Old Hatchet",   "kind": "weapon",
                       "desc": "An old hatchet.", "atk": 0},
    "old_pistol":    {"name": "Old Pistol",    "kind": "weapon",
                       "desc": "An old pistol. No bullets.", "atk": 0},
    "fishing_pole":  {"name": "Fishing Pole",  "kind": "weapon",
                       "desc": "A fishing pole.", "atk": 0},
    "cloth_tunic":   {"name": "Old Coat",      "kind": "armor",
                       "desc": "An old coat.",     "def": 0},
    "leather_armor": {"name": "Field Jacket",  "kind": "armor",
                       "desc": "A field jacket.", "def": 0},
    "iron_armor":    {"name": "Heavy Coat",    "kind": "armor",
                       "desc": "A heavy coat.",        "def": 0},
    "bread":         {"name": "Stale Bread",   "kind": "consumable",
                       "desc": "Some stale bread.", "heal": 0},
    "potion_red":    {"name": "Red Vial",      "kind": "consumable",
                       "desc": "A red vial.", "heal": 0},
    "potion_clear":  {"name": "Clear Vial",    "kind": "consumable",
                       "desc": "A clear vial.", "heal": 0},
    # ---- Vestigial keys / lore ----
    "brass_key":     {"name": "Brass Key",     "kind": "key",
                       "desc": "A brass key."},
    "rust_key":      {"name": "Rusted Key",    "kind": "key",
                       "desc": "A rusted key."},
    "rope":          {"name": "Coil of Rope",  "kind": "key",
                       "desc": "A coil of rope."},
    "liquor_crate":  {"name": "Crate of Liquor", "kind": "key",
                       "desc": "A crate of bottles."},
    "easter_egg":    {"name": "Painted Stone", "kind": "key",
                       "desc": "A painted stone."},
    "ring":          {"name": "Ring",          "kind": "key",
                       "desc": "A plain ring."},
    "small_fish":    {"name": "Small Fish",    "kind": "key",
                       "desc": "A small fish."},
    "big_fish":      {"name": "Big Fish",      "kind": "key",
                       "desc": "A big fish."},
    "wolf_pelt":     {"name": "Pelt",          "kind": "lore",
                       "desc": "An animal pelt."},
    "old_doll":      {"name": "Cloth Doll",    "kind": "lore",
                       "desc": "A cloth doll."},
    "badge":         {"name": "Old Badge",     "kind": "lore",
                       "desc": "A tarnished badge."},
    "slobbery_key":  {"name": "Wet Key",       "kind": "key",
                       "desc": "A wet key."},
    "reservation":   {"name": "A Slip",        "kind": "lore",
                       "desc": "A printed slip."},
    "summoner_tome": {"name": "Old Notebook",  "kind": "lore",
                       "desc": "An old notebook. Mostly blank."},
    "broken_crutch": {"name": "Broken Crutch", "kind": "lore",
                       "desc": "A bent crutch."},
    "old_photo":     {"name": "Old Photo",     "kind": "lore",
                       "desc": "A faded photo."},
    "diary_page_1":  {"name": "Torn Page",     "kind": "lore",
                       "desc": "A torn page."},
    "diary_page_2":  {"name": "Torn Page",     "kind": "lore",
                       "desc": "A torn page."},
    "letter_mom":    {"name": "A Note",        "kind": "lore",
                       "desc": "A folded note."},
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
