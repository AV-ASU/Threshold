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
    "pistol":        {"name": "Pistol",
                       "kind": "weapon",
                       "desc": "Your gun."},
    "pistol_ammo":   {"name": "Cartridges",
                       "kind": "key",
                       "desc": "Pistol rounds. Never as many as you'd like."},
    "newspaper":     {"name": "Yesterday's Paper",
                       "kind": "lore",
                       "desc": "The Minneapolis paper for April 14, "
                               "carried in on the drive north. Yesterday's "
                               "date, and the freshest thing in Brimley by "
                               "months.\n\n"
                               "The whole front page is Kurt Cobain. "
                               "Tributes pouring in from everywhere at "
                               "once. Inside, the box scores, and a fat "
                               "Sunday run of the funnies."},
    "woodshed_key":  {"name": "Woodshed Key",
                       "kind": "key",
                       "desc": "A key."},
    "cellar_key":    {"name": "Lodge cellar key",
                       "kind": "key",
                       "desc": "A heavy iron key."},
    "batteries":     {"name": "Flashlight Batteries",
                       "kind": "key",
                       "desc": "A paper sack of loose flashlight "
                               "batteries, heavy for its size. Royce "
                               "hoarded them one drive at a time, for a "
                               "road that never opened."},
    "stone":         {"name": "River Stone",
                       "kind": "key",
                       "desc": "A smooth grey stone off the riverbank, a "
                               "good weight for the hand. Right click to "
                               "put a sound somewhere you are not."},
    "flashlight":    {"name": "Flashlight",
                       "kind": "key",
                       "desc": "A heavy steel flashlight. Press [F] to "
                               "switch it on in the dark. But a light in "
                               "the dark is a thing that can be seen. Burn "
                               "it too long and you will not be the only one "
                               "who knows where you are."},
    "pallid_mask": {"name": "The Pallid Mask",
                       "kind": "lore",
                       "desc": "The King's own pale half-mask, made an "
                               "object. His face. Brimley opens for it. So, "
                               "you suspect, does the door in the deep."},
    "cross":         {"name": "The Preacher's Cross",
                       "kind": "lore",
                       "desc": "A plain silver cross. It was still warm "
                               "when you took it. You try not to think "
                               "about that."},
    "robe":          {"name": "Old Robe",
                       "kind": "lore",
                       "desc": "A coarse wool robe."},
    # NB: the journal READS from MARA_JOURNAL_PAGES below (the paged
    # leaves); this desc is the skim text and must stay consistent with
    # those pages -- the ache first (grief that learned her name), then
    # the door, then the glad dig down (NARRATIVE §2: answered, not
    # deceived).
    "mom_notebook":  {"name": "Mara's Journal",
                       "kind": "lore",
                       "desc": "Her journal. Three leaves, in a hand that "
                               "gets calmer as it goes:\n\n"
                               "\"They told me grief would pass. It did not "
                               "pass. It only learned my name.\"\n\n"
                               "\"I have started to dream of a door. It is "
                               "not frightening. It feels like being "
                               "remembered.\"\n\n"
                               "\"They dreamed the same door, every one of "
                               "them. We are digging down to it together "
                               "now. I am not lost. I have never been this "
                               "close.\""},
    # The thing the player CARRIES out of her cell holds the ADMISSION
    # (NARRATIVE §4/§6, 2026-07): the pregnancy Walter never knew of,
    # the son-for-a-daughter reflection, the boy's father dismissed in a
    # clause. The door is never mentioned. Her guilt is grief's own lie,
    # hers alone, never the story's verdict. The last thing the human
    # Mara wrote.
    "unsent_letter": {"name": "Mara's Letter",
                       "kind": "lore",
                       "desc": "Stamped, never mailed.\n\n"
                               "\"Dad. There was going to be a baby. A boy. "
                               "I never told you, and then I could not find "
                               "a way to tell you the rest. I almost decided "
                               "different, right at the last, and then I "
                               "wanted him more than I have ever wanted "
                               "anything. He came still.\n\n"
                               "I keep finding ways it was my fault. I know "
                               "that isn't sane. I keep finding them anyway. "
                               "His father was never part of it. That was "
                               "never the part that mattered.\n\n"
                               "I wanted a son the way you wanted a "
                               "daughter. Somebody to wait up for. You never "
                               "once said it, but the kitchen light was "
                               "always on, however late I came in. I was "
                               "going to be that for him.\n\n"
                               "Don't come after me. I'm not lost. I've "
                               "never been this close.\"\n\n"
                               "It stops there. No signature."},
    # ---- Mara's surface trail (evidence; NARRATIVE §6, DESIGN.md §9) ----
    # The physical trace she left in the town: a resident's record, not a
    # visitor's. Each is carryable and self-evident (no cosmology, no
    # witness needed to read it), and WORLD-PERSISTENT -- it survives the
    # local who kept it, so killing Hettie or Vane can never soft-lock the
    # descent (the record is still on the shop spike, still in the office
    # files).
    "receipt":       {"name": "A Store Tab",
                       "kind": "lore",
                       "desc": "A curled slip off the shop spike, headed "
                               "\"M. Blaine\" in Hettie's careful hand.\n\n"
                               "Matches, two boxes.\n"
                               "Canned milk, a case.\n"
                               "Bread. Kerosene. Lamp oil.\n"
                               "A few dollars, cash, week on week, run "
                               "down most of a year.\n\n"
                               "Staples a resident lays in, not a "
                               "traveler's kit. She lived here."},
    "detention_record": {"name": "A Booking Slip",
                       "kind": "lore",
                       "desc": "A booking slip out of the Sheriff's files, "
                               "filled in a flat official hand.\n\n"
                               "NAME: Blaine, Mara\n"
                               "AGE: 24\n"
                               "DATE: Dec. 11, 1993\n"
                               "INCIDENT: disturbance, main road. Shouting "
                               "at the sky, at nothing anyone else could "
                               "see.\n"
                               "DISPOSITION: held overnight to calm. "
                               "Released at first light. No charge.\n\n"
                               "She was coming apart in the open, and the "
                               "law wrote it down and let her go."},
    # A newcomer's gas receipt, left under a schoolhouse cot. NOT evidence
    # and not Mara's: an ordinary paper trace of an ordinary drive, which is
    # exactly what makes it worth carrying. It corroborates the one thing
    # Vane could never get out of them (NARRATIVE §4: not one could tell him
    # where they had driven in from) without a word of testimony.
    "gas_receipt":   {"name": "A Gas Receipt",
                       "kind": "lore",
                       "desc": "A pump receipt, soft from a pocket, left "
                               "under a cot in the schoolhouse.\n\n"
                               "CLARK OIL / SEYMOUR, WIS.\n"
                               "JULY 2 1993\n"
                               "14.2 GAL      REG      $16.75\n"
                               "CASH\n\n"
                               "Four hundred miles south of here, and paid "
                               "for in cash. Whoever slept on that cot "
                               "drove up the same roads I did."},
    "maras_scrawl":  {"name": "The Sign, in Her Hand",
                       "kind": "lore",
                       "desc": "A single leaf off the copying desks in the "
                               "deep.\n\n"
                               "The Sign, inked over and over down the page, "
                               "in the hand you know from her journal and "
                               "her letter. Hers.\n\n"
                               "No captive draws this. She sat and did the "
                               "work with her own hand, willing, like the "
                               "rest of them."},
    # ---- The bear (the secret fourth; NARRATIVE §4/§6, DESIGN.md §9,
    # TODO #22b). OPTIONAL, never case-evidence, never gates. Toby lends it.
    # On the surface it is a tender, UNEXPLAINED thing in a boy's hands; once
    # the PI has read her letter it detonates (effective_desc, below). The
    # stitched tag is the ONLY place the boy's name appears besides the PI's
    # own mouth -- MARA never says it (invariant, guarded).
    "bear":          {"name": "A Stuffed Bear",
                       "kind": "lore",
                       "desc": "A small homemade bear, worn soft. A name is "
                               "stitched into the tag at its neck in careful "
                               "thread: SAM.\n\n"
                               "Toby says the lady from the photograph gave "
                               "it to him. She could not keep it, he said, "
                               "and could not throw it out. The only toy in "
                               "town.\n\n"
                               "Why a grown woman drove a child's bear this "
                               "far north, and then gave it away, you cannot "
                               "yet say."},
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
    # The congregation's invitation -- left at the Lodge desk by the guests
    # who never signed out, handed over by Sable at 3 evidence. Carries the
    # rite: the school first (smoke, then the chalk door), then the clearing.
    # Voice rules: compulsion-certainty, never explanation (NARRATIVE §2);
    # NO dashes in this text.
    "rite_envelope": {"name": "The Invitation",
                       "kind": "lore",
                       "desc": "A long envelope, the Sign pressed into its "
                               "wax. One sheet inside, in a careful hand:\n\n"
                               "\"Sleep where we slept, in the school. "
                               "Sweeten the air the way we did, at the "
                               "fire. Then take up the chalk and draw the "
                               "door once more, the smallest one, where the "
                               "lesson ends.\"\n\n"
                               "\"The clearing in the corn does the rest. "
                               "Speak nothing there. The dead fire knows "
                               "the way down.\"\n\n"
                               "\"When we are ready, all of us go down "
                               "together.\""},
    "chalk":         {"name": "Schoolroom Chalk",
                       "kind": "key",
                       "desc": "A worn stub of white chalk off the "
                               "teacher's desk. The board has been drawn "
                               "on over the lesson, the same door, smaller "
                               "and smaller. The last one was never "
                               "drawn."},
    "incense":       {"name": "Dried Incense",
                       "kind": "key",
                       "desc": "A bundle of dried incense left beside a "
                               "cot. A sweet, cold smell, like a church "
                               "with no god in it."},
    "powder":        {"name": "Blasting Powder",
                       "kind": "key",
                       "desc": "A miner's charge from the diggers' "
                               "stores, kept dry on the Sump ledge. "
                               "Enough to open a few feet of dead earth, "
                               "and a fuse to outrun."},
}


# The bear, AFTER the PI has read Mara's letter (evidence_maras_room): the
# tag's name and the letter's stillborn son collide, and the tender surface
# object becomes the worst thing he carries (TODO #22b, DESIGN.md §9). MARA
# never says the name; the tag and the PI do.
_BEAR_DESC_KNOWN = (
    "A small homemade bear, worn soft. The name stitched into the tag "
    "reads SAM.\n\n"
    "Her letter told the rest. A boy. She wanted him more than anything, "
    "and he came still. A nursery that never opened, and this bear meant "
    "for it.\n\n"
    "She could not keep it and could not throw it out, so she gave it to "
    "the one living child she found up here. You are carrying her dead "
    "son's bear down toward her."
)


def effective_desc(key, save=None):
    """Return the inventory description for `key`. Static, with one
    exception: once the PI has read Mara's letter (evidence_maras_room) the
    bear's tag and the letter's stillborn son collide and its description
    DETONATES (TODO #22b) -- the surface plant made the worst thing he
    carries. MARA never says the name; the tag and the PI do."""
    if (key == "bear" and save is not None
            and save.flag("evidence_maras_room")):
        return _BEAR_DESC_KNOWN
    return ITEM_DEFS.get(key, {}).get("desc", "")


# Mara's Journal, in her own words: three short leaves the player turns
# one Enter at a time in the inventory. The arc is the whole of her
# descent in miniature -- the ache that drew her, the dream of the door,
# the glad walk down toward it (NARRATIVE §2: she was answered, not
# deceived). The door-dream now fires on PICKUP of the journal (play-notes;
# scenes/interiors.py _barn_update), not on a page-turn -- reading these
# leaves is just reading. No dashes in any of this text -- it is read by
# the player.
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
