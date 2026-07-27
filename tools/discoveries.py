"""THE DISCOVERY CATALOG -- every single thing the player can find, listed.

Run this before designing anything that touches investigation. It answers the
question the 2026-07 story audit could not answer from memory: *what is there
to find in this game, where is it, and can the player do anything with it once
they have it?*

    python tools/discoveries.py              # the catalog
    python tools/discoveries.py --md         # same, as markdown
    python tools/discoveries.py --problems   # only the rows that need a ruling

It is GENERATED from the source, never hand-maintained, for the same reason
`tools/index.py` generates TOOLS.md: a hand-written catalog of 40-odd finds
scattered across a dozen scene files is stale the day after it is written, and
a stale catalog is worse than none (you design against finds that no longer
exist and miss the ones that do).

WHAT COUNTS AS A DISCOVERY. Anything that fires `_evidence(...)` or
`_log_note(...)` -- the two writes that can put something in front of the
player as a find. That deliberately includes the ones that write NOTHING to
the casebook (`_evidence` with a non-canonical name and no `note=True` only
narrates a caption), because those are the interesting ones: they are objects
the player walked up to, looked at, and got a line about, which then vanished.

THE FOUR COLUMNS THAT MATTER:

  WRITES   evidence -> counts toward the King-gate (the five of Mara's trail)
           note     -> lives in the casebook, never counts
           caption  -> narrates once and is GONE. Nothing is recorded.
  VERB     how the player triggers it (see _VERBS: the enclosing function's
           name is the tell, so this is a heuristic and is marked "?" when it
           cannot be read confidently)
  ACT      surface (pre-descent) or deep (past the grove rite)
  SHARE    which NPC exchanges open BECAUSE of it -- read live off every
           conversation's `avail` source, so a new share shows up here the
           moment it is authored. "-" means the player can find this and then
           do nothing with it, ever, which is the audit's central finding.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enclosing-function name -> the verb the player actually performs. The scene
# hooks are named consistently enough that this reads correctly for nearly
# every site; anything unmatched prints "?" rather than guessing.
_VERBS = (
    ("_update", "walk over"),
    ("_interact", "press E"),
    ("_dialogue", "talk"),
    ("_convo", "talk"),
    ("grant_", "talk"),
    ("_told", "talk"),
    ("_given", "talk"),
    ("_provoked", "talk"),
    ("_voice", "talk"),
    ("_tick", "automatic"),
    ("_note_", "automatic"),
    ("_log_", "automatic"),
    ("_take_", "press E"),
    ("_on_enter", "enter room"),
    ("on_enter", "enter room"),
    ("_examine", "press E"),
)

# Text that is obviously placeholder rather than authored (the TODO.md
# voice/polish list calls these out by hand today).
_PLACEHOLDER = re.compile(
    r'^"?(A small stash|A weathered headstone|A scarecrow|A key|An axe)', re.I)


def _iter_sources():
    for base in ("scenes", "systems", "ui"):
        for root, _dirs, files in os.walk(os.path.join(ROOT, base)):
            if "__pycache__" in root:
                continue
            for f in sorted(files):
                if f.endswith(".py"):
                    p = os.path.join(root, f)
                    yield os.path.relpath(p, ROOT), open(p).read()


def _enclosing_def(src, idx):
    """The name of the nearest `def` above `idx` -- the function the call sits
    in, which is what tells us the player's verb."""
    head = src[:idx]
    hits = re.findall(r'\n\s*def (\w+)\(', head)
    return hits[-1] if hits else ""


def _verb_for(fn):
    for frag, verb in _VERBS:
        if frag in fn:
            return verb
    return "?"


def _first_line(tail):
    """The first quoted string in a call's argument tail: the beat's opening
    line, which is what the player actually reads."""
    m = re.search(r'"((?:[^"\\]|\\.){4,})"', tail)
    return m.group(1) if m else ""


def collect():
    """Every discovery site in the game, as dicts."""
    from scenes.dialogue import CANONICAL_EVIDENCE
    rows = {}
    # Four call shapes reach the casebook, and an earlier version of this
    # tool only matched the first, silently under-counting by a third:
    #   _evidence(game, "x", ...)      the scene-side beat
    #   _log_note(game, "x", ...)      the scene-side note
    #   game._log_note("x", ...)       the same, as a Game method
    #   self._log_note("x", ...)       the mixin-side note
    call = re.compile(
        r'(?:self\.|game\.)?(_evidence|_log_note)\('
        r'\s*(?:(?:game|self)\s*,\s*)?\n?\s*"(\w+)"', re.S)
    for path, src in _iter_sources():
        for m in call.finditer(src):
            kind, name = m.group(1), m.group(2)
            tail = src[m.end():m.end() + 700]
            fn = _enclosing_def(src, m.start())
            if kind == "_log_note":
                writes = "note"
            elif name in CANONICAL_EVIDENCE:
                writes = "evidence"
            elif "note=True" in tail.split(")\n")[0]:
                writes = "note"
            else:
                writes = "caption"
            row = rows.setdefault(name, {
                "name": name, "writes": writes, "where": path,
                "fn": fn, "verb": _verb_for(fn), "text": _first_line(tail),
                "share": [],
            })
            # An evidence beat can have two ways in (the warm handover and the
            # world-persistent fallback); keep the richest classification.
            if writes == "evidence":
                row["writes"] = "evidence"

        # Notes written straight into the save arg rather than through the
        # helpers (the intake, the dream): a dict literal with name + lines.
        for m in re.finditer(r'"name":\s*"(\w+)",\s*"lines"', src):
            name = m.group(1)
            if name in rows:
                continue
            fn = _enclosing_def(src, m.start())
            rows[name] = {
                "name": name, "writes": "note", "where": path, "fn": fn,
                "verb": _verb_for(fn),
                "text": _first_line(src[m.end():m.end() + 700]), "share": [],
            }

        # The newspaper allocation notes: the name is a literal ARGUMENT to
        # the shared helper, never the first arg of a _log_note call.
        for m in re.finditer(r'_paper_given\(\s*game,\s*"(\w+)",\s*"(\w+)"',
                             src):
            rows.setdefault(m.group(2), {
                "name": m.group(2), "writes": "note", "where": path,
                "fn": "_paper_given", "verb": "talk",
                "text": "the one newspaper, spent on %s" % m.group(1),
                "share": [],
            })

        # Table-driven notes: the descent-voice track is a dict of beats fired
        # by key, so no call site names them literally.
        if path.endswith("game.py") and "_DESCENT_VOICE = {" in src:
            seg = src[src.index("_DESCENT_VOICE = {"):]
            for key in re.findall(r'\n        "(\w+)": \{', seg[:9000]):
                rows.setdefault(key, {
                    "name": key, "writes": "note", "where": "the descent voice",
                    "fn": "_descent_voice", "verb": "automatic",
                    "text": "", "share": [],
                })
    return rows


# The descent-voice track has no scene file of its own, and it straddles: the
# barn's chalk door is surface, everything after it is underground.
_DESCENT_SURFACE = {"chalk_surface"}


def _act_for(path, name=""):
    """Surface or deep, by the file the beat lives in. well.py and depths.py
    are the mine; everything else the player reaches before the rite."""
    if path == "the descent voice":
        return "surface" if name in _DESCENT_SURFACE else "deep"
    if path.endswith(("well.py", "depths.py")):
        return "deep"
    return "surface"


def cross_reference_shares(rows):
    """Which conversation exchanges open BECAUSE of a discovery. Read off the
    `avail` source of every authored exchange, so this cannot drift from what
    actually ships: an avail that names `evidence_the_ledger` is a share of
    the Ledger, whatever the exchange happens to be called."""
    import scenes.dialogue as D
    import scenes.well as W
    convos = [(n, getattr(D, n)) for n in dir(D) if n.endswith("_CONVO")]
    convos += [("MARA_CONVO", getattr(W, "MARA_CONVO", None))]
    src = open(os.path.join(ROOT, "scenes", "dialogue.py")).read()
    src += open(os.path.join(ROOT, "scenes", "well.py")).read()
    for cname, convo in convos:
        if not convo:
            continue
        who = convo.get("id", cname.split("_")[0].lower())
        for ex in convo.get("exchanges", []):
            key = ex.get("key", "?")
            av = ex.get("avail")
            if av is None:
                continue
            # The avail source, located by the exchange key in the file text.
            m = re.search(
                r'"key":\s*"%s"[\s\S]{0,600}?"avail":\s*(lambda g:[\s\S]{0,400}?),\n\s*["}]'
                % re.escape(key), src)
            body = m.group(1) if m else ""
            for flag in re.findall(r'flag\("(\w+)"\)', body):
                nm = flag[len("evidence_"):] if flag.startswith("evidence_") \
                    else flag
                if nm in rows:
                    rows[nm]["share"].append(f"{who}/{key}")
            for item in re.findall(r'has\("(\w+)"\)', body):
                if item in rows:
                    rows[item]["share"].append(f"{who}/{key}")
    # The bear is shared with MARA and it is the sharpest beat in the game;
    # its exchange gates on the ITEM, not on the note name, so name it here
    # rather than let the catalog print a misleading "-".
    if "the_bear" in rows and not rows["the_bear"]["share"]:
        rows["the_bear"]["share"].append("mara/name (carries the bear)")
    return rows


def problems(rows):
    """The rows that need a ruling, and why. This is the working list."""
    out = []
    for r in rows.values():
        act = _act_for(r["where"], r["name"])
        if r["writes"] == "caption":
            if _PLACEHOLDER.match('"' + r["text"]):
                out.append((r, "PLACEHOLDER text, and records nothing"))
            else:
                out.append((r, "records NOTHING: narrates once, then gone"))
        elif r["writes"] in ("evidence", "note") and not r["share"] \
                and act == "surface" and r["verb"] in ("walk over", "press E",
                                                       "enter room"):
            out.append((r, "a real find with nobody to take it to"))
    return out


def render(rows, md=False):
    lines = []
    b = (lambda s: f"**{s}**") if md else (lambda s: s)

    def head(t):
        lines.append("")
        lines.append(f"## {t}" if md else f"\n{t}\n{'=' * len(t)}")
        if md:
            lines.append("")
            lines.append("| find | writes | verb | where | share |")
            lines.append("|---|---|---|---|---|")

    order = {"evidence": 0, "note": 1, "caption": 2}
    for act in ("surface", "deep"):
        group = [r for r in rows.values() if _act_for(r["where"], r["name"]) == act]
        group.sort(key=lambda r: (order[r["writes"]], r["name"]))
        head(f"{act.upper()}  ({len(group)} discoveries)")
        for r in group:
            share = ", ".join(sorted(set(r["share"]))) or "-"
            where = r["where"].replace("scenes/", "").replace(".py", "")
            if md:
                lines.append("| `%s` | %s | %s | %s | %s |" % (
                    r["name"], b(r["writes"]), r["verb"], where, share))
            else:
                lines.append("  %-24s %-9s %-11s %-18s %s" % (
                    r["name"], r["writes"], r["verb"], where, share))
    return "\n".join(lines)


def main():
    md = "--md" in sys.argv
    rows = cross_reference_shares(collect())
    if "--problems" in sys.argv:
        probs = problems(rows)
        print("\n%d discoveries need a ruling:\n" % len(probs))
        for r, why in sorted(probs, key=lambda x: x[1]):
            print("  %-24s %-42s %s" % (r["name"], why, r["where"]))
            if r["text"]:
                print("  %-24s   \"%s\"" % ("", r["text"][:76]))
        return
    print(render(rows, md=md))
    n = len(rows)
    ev = sum(1 for r in rows.values() if r["writes"] == "evidence")
    nt = sum(1 for r in rows.values() if r["writes"] == "note")
    cp = sum(1 for r in rows.values() if r["writes"] == "caption")
    sh = sum(1 for r in rows.values() if r["share"])
    surf = sum(1 for r in rows.values() if _act_for(r["where"], r["name"]) == "surface")
    print("\n%d discoveries: %d evidence, %d notes, %d record nothing."
          % (n, ev, nt, cp))
    print("%d on the surface. %d can be taken to anybody." % (surf, sh))
    print("\nRun with --problems for the rows that need a ruling.")


if __name__ == "__main__":
    main()
