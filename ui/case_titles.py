"""Case-file titles for save slugs -- one shared home.

The notebook writes evidence/notes under load-bearing SLUGS (saves + logic
depend on them, NARRATIVE canon invariants). The player should never SEE a
slug: "maras_room" reads as "Mara's Room", "the_ledger" as "The Old
Registers". This map is that display layer, shared by the journal book
(ui/journal_ui) AND the notebook-scribble toast (systems/render_mixin) so
a note is titled the SAME way wherever it surfaces.

Anything unmapped falls back to Title Case, so a new slug is never a crash,
only a plainer header until it earns an authored one.
"""

NOTE_TITLES = {
    # Derived pins (front of the case book).
    "working_theory":          "Working Theory",
    "case_timeline":           "Timeline",
    # The intake + the interior beats.
    "the_case":                "The Case",
    # The newspaper choice (TODO #2): the one copy, wherever it went.
    "paper_royce":             "Royce's Best Road",
    "paper_pell":              "Pell's Calendar",
    "paper_toby":              "The Funny Pages",
    "paper_sable":             "The Unopened Paper",
    "paper_hettie":            "The Counter Trade",
    "paper_vane":              "The Front Page",
    "the_dream":               "The Dream, a Year Back",
    "the_rite":                "What I Did at the Fire",
    "saw_the_door":            "The Door in the Air",
    "walked_in_circles":       "The Roads That Loop",
    "the_fold_told":           "The Roads",
    # Mara's trail (the five that count).
    "maras_receipt":           "Her Store Tab",
    "maras_record":            "Her Booking Slip",
    "maras_journal":           "Mara's Journal",
    "maras_dig":               "The Sign, in Her Hand",
    "maras_room":              "Mara's Letter",
    # Real finds that are not Mara (notes, never evidence).
    "the_ledger":              "The Old Registers",
    "the_preacher":            "The Preacher on the Bank",
    "the_congregation":        "The Ones Who Knelt",
    # Revisit nudges (kept minimal now -- one pointed thought each).
    "revisit_sable_checkouts": "Back to the Desk",
    "revisit_sable_smile":     "Ask the Clerk About Her",
    "revisit_vane_murder":     "Tell the Sheriff",
    # The descent interior voice.
    "chalk_surface":           "The Chalk Door",
    "chalk_works":             "The Drawn Doors",
    "chalk_deep":              "Past the Deepest Face",
    "descent_dig":             "The Dig",
    "descent_leave":           "The Urge to Leave",
    "descent_mask":            "Permission to Leave",
    # The cult's own testimony.
    "cult_calling":            "The Calling",
    "cult_bargain":            "The Bargain",
    "cult_digging":            "The Digging",
    # Older beats still referenced by save data.
    "chalk_works_old":         "The Works",
    "calder_table":            "Mrs. Calder's Table",
    "crane_provoked":          "The Preacher, Provoked",
    "clerk_robe":              "The Pressed Robe",
    "worn_stone":              "The Worn Stone",
    "bell_tower_view":         "From the Bell Tower",
    "backwoods_note":          "The Backwoods Stash",
    "barrow_tools":            "The Barrow",
    "lodge_candle_callback":   "Candles at the Lodge",
    "scarecrow":               "The Scarecrow",
    "the_old_stores_shelves":  "The Old Stores",
    "threshing_floor":         "The Threshing Floor",
    "works_cistern_seen":      "The Water Below",
}


def humanise(slug):
    """Case-file title for a save slug: the authored header where one
    exists, else 'some_note' -> 'Some Note'."""
    t = NOTE_TITLES.get(slug)
    if t:
        return t
    return " ".join(p.capitalize() for p in str(slug).split("_"))
