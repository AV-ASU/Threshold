"""Item definitions and inventory.

THRESHOLD: combat is gone. Item meanings re-anchored for the 1994
Yellow-King-cult fiction. Items the player can ACTUALLY find in the
new world: the orb (cult artifact), the polaroid (mom's), the lumber
axe (chops debris in the woodshed), car keys (escape), sigil rubbing
(evidence + door-confrontation trigger), charcoal stick + paper
(combine to make the rubbing), kid's drawing (kid arc beat), robe
(in the Innkeeper's closet, behind the orb), Mom's notebook (lore +
counter-rite), flashlight (was fishing_pole; lights dark scenes).

Combat-era items (knife, sword, pistols, armor, potions, bread,
fish) stay in ITEM_DEFS so old saves don't crash on load, but
nothing in the new world drops them. Their descriptions are
rewritten as bleak flavor.
"""
import time

ITEM_DEFS = {
    # ---- THRESHOLD core items (in circulation) ----
    "car_keys":      {"name": "Car Keys",
                       "kind": "key",
                       "desc": "A worn '88 keyring. Three keys, one ignition."},
    "woodshed_key":  {"name": "Woodshed Key",
                       "kind": "key",
                       "desc": "Heavy iron, on a leather thong. You\n"
                               "lifted it from the hook by his head."},
    "charcoal":      {"name": "Charcoal Stick",
                       "kind": "key",
                       "desc": "Black on your fingers."},
    "paper":         {"name": "Innkeeper's Note",
                       "kind": "lore",
                       "desc": "His handwriting, slow and pressed-in:\n"
                               "'If you mean to go down there,\n"
                               "ask Carl. North of the road.\n"
                               "Spare's on his step, under the bird.\n"
                               "I won't say it twice.'"},
    "cellar_key":    {"name": "Cellar Key",
                       "kind": "key",
                       "desc": "Iron. Cold. The padlock on the kitchen\n"
                               "hatch turns with this."},
    "sigil_rubbing": {"name": "Sigil Rubbing",
                       "kind": "lore",
                       "desc": "Charcoal on paper. A spiraling open\n"
                               "eye. You took it from the well rim."},
    "kid_drawing":   {"name": "Kid's Drawing",
                       "kind": "lore",
                       "desc": "Crayon on lined paper. The eye again.\n"
                               "He doesn't know what it is."},
    "robe":          {"name": "Cult Robe",
                       "kind": "lore",
                       "desc": "Coarse undyed wool. Smells of pine\n"
                               "smoke. The hem is scorched."},
    "mom_notebook":  {"name": "Mom's Notebook",
                       "kind": "lore",
                       "desc": "Spiral-bound. Her handwriting. She\n"
                               "knew. She was finding out before they\n"
                               "took her."},
    "flashlight":    {"name": "Flashlight",
                       "kind": "key",
                       "desc": "Heavy 4-D-cell Maglite. The bulb still\n"
                               "works.\n\n"
                               "Press F to toggle. Battery drains\n"
                               "while it's on."},
    "spare_batteries": {"name": "Spare Batteries",
                       "kind": "consumable",
                       "desc": "Four D-cells in a sealed pack. Use to\n"
                               "recharge the flashlight."},
    # The bottle from the inn's cellar. The Innkeeper holds the
    # car keys "until you settle your tab" -- handing this in
    # closes the loop. Hand-rolled label, dusty.
    "cellar_bottle": {"name": "Cellar Bottle",
                       "kind": "key",
                       "desc": "From the inn's cellar. Hand-labelled,\n"
                               "the strong stuff. The innkeeper wants\n"
                               "this back before he'll talk about\n"
                               "your keys."},
    # ---- Re-meaned existing items ----
    # The orb the cult wants back. The Innkeeper will ask after it.
    # In the new fiction the orb is a cult-binding object Mom hid
    # before they took her; the Innkeeper wants it returned to the rite.
    "orb":           {"name": "Orb",
                       "kind": "key",
                       "desc": "Heavy, the colour of a bruise. It hums\n"
                               "when no one is looking."},
    # The polaroid is now Mom's. Same devolution as before.
    "polaroid":      {"name": "Polaroid",
                       "kind": "lore",
                       "desc": "A woman with your jaw. Standing in\n"
                               "front of a kitchen window. Your\n"
                               "mother."},
    # The axe still chops debris -- found in the Innkeeper's woodshed.
    "lumber_axe":    {"name": "Splitting Axe",
                       "kind": "weapon",
                       "desc": "From the Innkeeper's woodshed. Chops\n"
                               "wood. Won't help against people.",
                       "atk": 0},
    # ---- Backward-compat stubs (in DEFS so old saves don't crash;
    #      not dropped by anything in THRESHOLD) ----
    "knife":         {"name": "Pocket Knife",  "kind": "weapon",
                       "desc": "Useless against them.", "atk": 0},
    "short_sword":   {"name": "Bent Blade",    "kind": "weapon",
                       "desc": "Doesn't matter.", "atk": 0},
    "bandit_axe":    {"name": "Old Hatchet",   "kind": "weapon",
                       "desc": "Doesn't matter.", "atk": 0},
    "old_pistol":    {"name": "Old Pistol",    "kind": "weapon",
                       "desc": "No bullets. Wouldn't matter if there\n"
                               "were.", "atk": 0},
    "fishing_pole":  {"name": "Fishing Pole",  "kind": "weapon",
                       "desc": "You don't fish anymore.", "atk": 0},
    "cloth_tunic":   {"name": "Old Coat",      "kind": "armor",
                       "desc": "Stained.",     "def": 0},
    "leather_armor": {"name": "Field Jacket",  "kind": "armor",
                       "desc": "Smells of pine.", "def": 0},
    "iron_armor":    {"name": "Heavy Coat",    "kind": "armor",
                       "desc": "Cold.",        "def": 0},
    "bread":         {"name": "Stale Bread",   "kind": "consumable",
                       "desc": "You aren't hungry.", "heal": 0},
    "potion_red":    {"name": "Red Vial",      "kind": "consumable",
                       "desc": "You don't know what it is.", "heal": 0},
    "potion_clear":  {"name": "Clear Vial",    "kind": "consumable",
                       "desc": "Smells like the well water.", "heal": 0},
    # ---- Vestigial keys / lore ----
    "brass_key":     {"name": "Brass Key",     "kind": "key",
                       "desc": "From the basement door."},
    "rust_key":      {"name": "Rusted Key",    "kind": "key",
                       "desc": "From a forgotten lock."},
    "rope":          {"name": "Coil of Rope",  "kind": "key",
                       "desc": "Long enough for the well."},
    "liquor_crate":  {"name": "Crate of Liquor", "kind": "key",
                       "desc": "Six bottles, straw-packed. Heavier than\n"
                               "it looks. The Innkeeper wants it back."},
    "easter_egg":    {"name": "Painted Stone", "kind": "key",
                       "desc": "Someone painted it like an egg."},
    "ring":          {"name": "Ring",          "kind": "key",
                       "desc": "Plain gold. No engraving."},
    "small_fish":    {"name": "Small Fish",    "kind": "key",
                       "desc": "It came up wrong. Throw it back."},
    "big_fish":      {"name": "Big Fish",      "kind": "key",
                       "desc": "It came up wrong. Throw it back."},
    "wolf_pelt":     {"name": "Coyote Pelt",   "kind": "lore",
                       "desc": "Coyote, not wolf. Same shape, smaller."},
    "old_doll":      {"name": "Cloth Doll",    "kind": "lore",
                       "desc": "From the kid's house. He doesn't have\n"
                               "a sister anymore."},
    "badge":         {"name": "Sheriff's Badge", "kind": "lore",
                       "desc": "Tarnished tin. He wears it on a chain\n"
                               "under his collar."},
    "slobbery_key":  {"name": "Wet Key",       "kind": "key",
                       "desc": "From the well bottom. Brass. Cold."},
    "reservation":   {"name": "Reservation Slip", "kind": "lore",
                       "desc": "Dorian's Steakhouse -- Reservation Slip\n"
                               "Party: 2\n"
                               "Booked under: Mom\n"
                               "Names: Mom, you\n"
                               "Date: she never made it."},
    "summoner_tome": {"name": "Old Notebook",  "kind": "lore",
                       "desc": "Bound in cracked leather. Most pages\n"
                               "are blank."},
    "broken_crutch": {"name": "Broken Crutch", "kind": "lore",
                       "desc": "From the well bottom. Bent."},
    "old_photo":     {"name": "Old Photo",     "kind": "lore",
                       "desc": "Faded."},
    "diary_page_1":  {"name": "Diary Page 1",  "kind": "lore",
                       "desc": "Torn page. Your handwriting:\n\n"
                               "'They were chanting in the woods.\n"
                               " I followed him out and I shouldn't have.\n"
                               " They saw me. He turned and he saw me.'"},
    "diary_page_2":  {"name": "Diary Page 2",  "kind": "lore",
                       "desc": "Torn page. Your handwriting:\n\n"
                               "'The kid is next.\n"
                               " Tonight.\n"
                               " I have to get him out.'"},
    "letter_mom":    {"name": "Note",          "kind": "lore",
                       "desc": "Folded paper. Your handwriting:\n\n"
                               "'Keys are in his dresser.'"},
}


POLAROID_DEVOLUTION = [
    # Stage 0: untouched.
    "A woman with your jaw. Standing in front of a\n"
    "kitchen window. Your mother.",
    # Stage 1 (>=3 reads): the kitchen blurs.
    "A woman with your jaw. The window behind her\n"
    "is blurred white.",
    # Stage 2 (>=6 reads): she stops looking at the camera.
    "A woman with your jaw, looking down at\n"
    "something out of frame.",
    # Stage 3 (>=10 reads): the woman is partly gone.
    "A figure with your jaw. Half of her is empty\n"
    "paper.",
    # Stage 4 (>=15 reads): only the kitchen.
    "An empty kitchen. A window. Light.",
    # Stage 5 (>=20 reads): nothing.
    "Empty paper. You can't remember what was on it.",
]


def _polaroid_stage(reads):
    if reads >= 20: return 5
    if reads >= 15: return 4
    if reads >= 10: return 3
    if reads >= 6:  return 2
    if reads >= 3:  return 1
    return 0


def effective_desc(key, save=None):
    """Return the inventory description for `key`, applying any save-
    state overrides. Falls back to ITEM_DEFS[key]['desc'] when there
    is no override or no save reference is supplied (e.g. in tools
    that don't need the dynamic flavour)."""
    d = ITEM_DEFS.get(key, {})
    base = d.get("desc", "")
    if save is None:
        return base
    if key == "polaroid":
        # The polaroid devolves with each read. Reads are incremented
        # by the inventory UI when the player highlights this entry.
        reads = save.arg("polaroid_reads", 0)
        return POLAROID_DEVOLUTION[_polaroid_stage(reads)]
    if key == "mom_notebook":
        # Mom's notebook has staged readings: pages 1, 2, 3. Page 3
        # triggers the witnessing flashback (handled in game.py via
        # the notebook_pages_read save arg). Description grows with
        # each page read so the player sees their progress.
        reads = save.arg("notebook_pages_read", 0)
        if reads <= 0:
            return ("Spiral-bound. Her handwriting. You haven't\n"
                    "opened it.")
        if reads == 1:
            return ("Page one: her sketches of the spiral eye.\n"
                    "Names. The Innkeeper is on the list.")
        if reads == 2:
            return ("Page two: the cauldron. The procedure. How\n"
                    "they bind. What they call him.")
        return ("Page three. You read it and you remember.\n"
                "You wish you didn't.")
    if key == "badge":
        # Legacy: surfaces the LOGIN code if any.
        import re
        code = save.arg("user_code") or ""
        m = re.search(r"\d+", code)
        if m:
            return base + " D-" + m.group()
    return base


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
        # THRESHOLD: weapons do nothing. Returns 0 always so any
        # vestigial damage call resolves to a no-op.
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
