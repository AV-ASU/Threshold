"""CONVENTIONS -- the project's prose rules, enforced as failures.

Every check in here exists because a rule that lived only in a doc got broken
by someone who had read the doc. The pattern is consistent across this
project: the conventions that never regress (no dashes in player text, no
phantom furniture tiles, no diagonal wall joins) are the ones a harness
asserts. The ones that regress are the ones written down and remembered.

So: if a convention CAN be machine-checked, it belongs here, not only in
prose. The docs keep what cannot be automated -- canon facts, taste, intent.

Each check prints what it verified and fails LOUD with the rule it enforces
and where the violation is. Several carry an explicit ALLOWLIST of shipped
exceptions: the point is to freeze today's surface so NEW drift fails, without
relitigating deliberate old choices. Adding to an allowlist must be a
decision, which is exactly what the failure forces.

    python tests/conventions.py
"""
import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

FAILURES = []


def check(label):
    def deco(fn):
        print(f"[..] {label}", flush=True)
        try:
            detail = fn()
        except Exception as e:  # a broken check is a failing check
            FAILURES.append(f"{label}: check itself raised {e!r}")
            print(f"[!!] {label}: check raised {e!r}")
            return fn
        if detail:
            FAILURES.append(f"{label}\n{detail}")
            print(f"[!!] {label}\n{detail}")
        else:
            print(f"[ok] {label}")
        return fn
    return deco


# ---------------------------------------------------------------- 1. fonts
# THE RULE (CLAUDE.md): "Every sprite is drawn procedurally"; DESIGN.md §10:
# "Keep it asset-free." A system font pasted into the world reads as UI text
# lying on the scene, and it does not foreshorten with the tilt.
# WHY THIS CHECK: a neon store sign shipped rendered in SysFont. Lettering in
# the world is drawn geometry (see the `_GLYPH` neon-tube alphabet in
# rendering/props.py for the worked example).
# The budget is FROZEN PER FILE BY COUNT, not by filename: allowlisting a
# whole file would let a new font slip in beside an old one (the first cut of
# this check did exactly that and a fault-injection test caught it). To add a
# font use you must raise a number here, which is the decision point.
#   rendering/props.py     3 -- the BRIMLEY welcome board's three painted lines
#   entities/deco_horror.py 3 -- the stopped-calendar month/day label
#   entities/deco_structure.py 1 -- the tiny wall_sign label
FONT_BUDGET = {
    "rendering/props.py": 3,
    "entities/deco_horror.py": 3,
    "entities/deco_structure.py": 1,
}
FONT_SCAN_DIRS = ("rendering", "entities", "scenes")


@check("no NEW system fonts in the world draw layer (procedural rule)")
def _fonts():
    bad = []
    for d in FONT_SCAN_DIRS:
        for root, _dirs, files in os.walk(d):
            if "__pycache__" in root:
                continue
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(root, fn)
                n = sum(1 for l in open(p)
                        if "SysFont" in l or "pygame.font.Font" in l)
                budget = FONT_BUDGET.get(p, 0)
                if n > budget:
                    bad.append(f"    {p}: {n} font use(s), budget {budget}")
    if bad:
        return ("  world lettering must be DRAWN geometry, not a font.\n"
                "  See rendering/props.py `_GLYPH` + `_draw_neon_word` for the\n"
                "  neon-tube alphabet. To add a deliberate label, raise its\n"
                "  budget in FONT_BUDGET (that edit IS the decision).\n"
                + "\n".join(bad))


# ------------------------------------------------------------ 2. tilt sets
# THE RULE (CLAUDE.md, "Adding a new decoration/prop kind under the tilt"):
# register a kind in exactly ONE tilt set "or it renders as a flat stain on
# the floor" under the only shipping camera.
# WHY THIS CHECK: four kinds shipped into a new scene as flat stains because
# they were placed by NAME without being rendered first.
# ALLOWLIST = kinds with their own bespoke draw path, correctly in no set.
TILT_EXEMPT = {
    "dark_pool": "the REVERSE LIGHT: invisible by design (DESIGN.md §6)",
    "water_channel": "has a dedicated draw pass in scenes/terrain.py",
}


@check("every placed decoration kind renders under the tilt")
def _tilt_sets():
    from scenes import SCENE_BUILDERS, load_scene
    from rendering.props import SOLID_PROPS, _STANDEE_KINDS
    from rendering.assemblies import ASSEMBLIES
    from rendering.furniture import FURNITURE
    from scenes.terrain import (_FLOOR_DECAL_KINDS, _SURFACE_DECAL_KINDS,
                                _WALL_DECO_KINDS, _TABLETOP_PROP_KINDS)
    # ASSEMBLIES is the newest tilt registration: a kind declared as PARTS
    # (rendering/assemblies.py) is drawn by the central assembly renderer
    # and is as real a volume as anything in SOLID_PROPS.
    sets = (SOLID_PROPS, ASSEMBLIES, _STANDEE_KINDS, FURNITURE,
            _FLOOR_DECAL_KINDS, _SURFACE_DECAL_KINDS, _WALL_DECO_KINDS,
            _TABLETOP_PROP_KINDS)
    orphan = {}
    for key in sorted(SCENE_BUILDERS):
        try:
            sc = load_scene(key)
        except Exception:
            continue
        for d in getattr(sc, "decorations", []):
            k = getattr(d, "kind", None)
            if k and k not in TILT_EXEMPT and not any(k in s for s in sets):
                orphan.setdefault(k, set()).add(key)
    if orphan:
        rows = [f"    {k!r} placed in {sorted(v)[:4]}" for k, v in sorted(orphan.items())]
        return ("  these draw as flat floor stains under the tilt. Put each in\n"
                "  ONE tilt set (SOLID_PROPS / _STANDEE_KINDS / FURNITURE /\n"
                "  _FLOOR_DECAL_KINDS / _WALL_DECO_KINDS / ...), and render it\n"
                "  before placing it (CLAUDE.md SCENE-DRESSING #2).\n"
                + "\n".join(rows))


# --------------------------------------------------------- 3. light tables
# THE RULE (CLAUDE.md): a light-emitting kind lives in TWO tables --
# Scene._LIGHT_KINDS (the MECHANICAL cover radius stealth reads) and
# FIXTURE_POOLS (the VISIBLE pool _draw_dark casts). A kind in only one is a
# light that gates but does not shine, or shines but does not gate.
# No exemptions. The two this check found on its first run were real bugs and
# are fixed: `campfire` (the COLD indoor scorch decal) was handing out an 80px
# light-cover radius while casting nothing, and `burn_barrel` was casting a
# visible pool while giving no cover at all. Keep this empty if you can.
LIGHT_EXEMPT = {}


@check("light kinds agree across the mechanical + visible tables")
def _light_tables():
    from systems.render_mixin import FIXTURE_POOLS
    from scenes.base import Scene
    mech, vis = set(Scene._LIGHT_KINDS), set(FIXTURE_POOLS)
    rows = []
    for k in sorted(vis - mech):
        if k not in LIGHT_EXEMPT:
            rows.append(f"    {k!r}: in FIXTURE_POOLS, missing from Scene._LIGHT_KINDS "
                        "(shines but gives no stealth cover)")
    for k in sorted(mech - vis):
        if k not in LIGHT_EXEMPT:
            rows.append(f"    {k!r}: in Scene._LIGHT_KINDS, missing from FIXTURE_POOLS "
                        "(gates as lit but casts no visible light)")
    if rows:
        return "\n".join(rows)


# ------------------------------------------------------- 4. scene gate keys
# THE RULE: the scene-gating sets in systems/config.py drive King safety,
# darkness, storm stage, etc. A typo'd key silently gates NOTHING -- there is
# no error, the scene just never gets the behavior.
@check("every scene key in a config gating set is a registered scene")
def _gate_keys():
    import systems.config as C
    from scenes import SCENE_BUILDERS
    rows = []
    for nm in dir(C):
        if not nm.isupper() or "SCENE" not in nm:
            continue
        v = getattr(C, nm)
        if isinstance(v, (set, frozenset)) and v and all(isinstance(x, str) for x in v):
            miss = sorted(x for x in v if x not in SCENE_BUILDERS)
            if miss:
                rows.append(f"    {nm}: {miss} -- not in SCENE_BUILDERS (gates nothing)")
    if rows:
        return "\n".join(rows)


# ----------------------------------------------------------- 5. doc refs
# THE RULE (CLAUDE.md): a detail true in one doc and stale in another is rot.
# WHY THIS CHECK: the canon accumulated six references to files that had been
# deleted, including VISION.md pointing the four-facing workflow at a
# scratchpad script that no longer existed.
DOCS = ("CLAUDE.md", "NARRATIVE.md", "DESIGN.md", "TODO.md", "DIALOGUE.md",
        "VISION.md")
_PATH_RE = re.compile(r'`([A-Za-z_][\w/]*\.(?:py|md|sh))`')


@check("every file the canon docs reference actually exists")
def _doc_refs():
    rows = []
    for d in DOCS:
        for ref in sorted(set(_PATH_RE.findall(open(d).read()))):
            if os.path.exists(ref):
                continue
            base = os.path.basename(ref)
            found = any(base in files
                        for root, _dd, files in os.walk(".")
                        if "__pycache__" not in root and not root.startswith("./.git"))
            if not found:
                rows.append(f"    {d} -> `{ref}` does not exist")
    if rows:
        return "\n".join(rows)


# -------------------------------------------------- 6. lost spaces are mute
# THE RULE (maintainer, DIALOGUE.md): the lost fields carry NO narrator boxes,
# notices, case-notebook writes -- or place NAME. The dark and the hunted
# light are the whole text.
# WHY THE NAME HALF: the HUD labels every scene in the lower-left, and the
# default label is the titlecased scene key -- so a lost field silently
# announced itself as "Lost Forest", telling the player exactly what had
# happened to them. Same explaining-away as a caption, from a different layer,
# which is why this check covers both rather than only the words in the file.
@check("the lost spaces ship no narration and no place name")
def _lost_silent():
    src = open("scenes/lost_space.py").read()
    hits = [t for t in ("show_notice", "_evidence(", "_log_note", "DialogueBox",
                        "show_dialog") if t in src]
    if hits:
        return (f"    scenes/lost_space.py uses {hits}.\n"
                "    The lost spaces are wordless by ruling (DIALOGUE.md). If a\n"
                "    beat there seems to want words, it needs staging, not a line.")
    from systems.config import LOST_SPACE_SCENES
    from scenes import load_scene
    from scenes.base import scene_display_name
    named = sorted(k for k in LOST_SPACE_SCENES
                   if scene_display_name(load_scene(k)).strip())
    if named:
        return ("    these lost scenes label themselves in the HUD corner: "
                f"{named}.\n"
                "    A lost space is somewhere with no name you know. Set\n"
                "    `display_name = \"\"` (an explicit blank, which\n"
                "    scene_display_name honours; None falls back to the key).")


# --------------------------------------------------- 7. exits are walkable
# THE RULE: an exit fires from the tile the player is STANDING ON
# (`Scene.find_exit_at` off `char_object_at`), so an exit char that is SOLID
# in OBJECT_DEFS is an exit nobody can ever take. There is no error and no
# visible tell: the passage simply reads as a wall you bump into.
# WHY THIS CHECK: Brimley's north road to `gravel_road_north` used "R", which
# is a solid ROCK char. It shipped that way and the road out the top of town
# was unreachable until somebody walked it in a test harness. Two more of the
# same slipped into the safe-path network in the same session, which is the
# tell that this needs a machine and not a memo.
@check("every exit char is walkable (an exit you cannot stand on is a wall)")
def _exit_chars_walkable():
    from scenes import SCENE_BUILDERS, load_scene
    from scenes.terrain import is_object_solid
    rows = []
    for key in sorted(SCENE_BUILDERS):
        try:
            sc = load_scene(key)
        except Exception:
            continue
        if getattr(sc, "procedural", False):
            continue
        for ch in sorted(sc.exits):
            if is_object_solid(ch):
                rows.append(f"    {key}: exit {ch!r} -> {sc.exits[ch][0]!r} "
                            "is a SOLID char, so the passage is a wall")
    if rows:
        return ("  pick a non-solid char (an 'outdoor_passage' or 'door' kind\n"
                "  in scenes/terrain.py OBJECT_DEFS) for any exit the player\n"
                "  walks onto.\n" + "\n".join(rows))


# ------------------------------------------- 8. assemblies match their refs
# THE RULE: a prop declared as PARTS is built to a recorded reference
# (`rendering/references.py`), and both the structure and the proportion are
# machine-checkable BECAUSE it is data. This is the check that could not
# exist while props were imperative draw calls, and it is the whole reason
# the rework was worth doing.
# It has already earned its keep: on its first run it caught a mailbox being
# measured with its post included, a stoop whose reference axes were quoted
# the way a catalogue quotes them (and so was compared ninety degrees out),
# and a woodpile modelled with its logs along the stack instead of across it.
# All three were found before anything was rendered.
@check("every parts-built prop matches its recorded reference")
def _assemblies():
    from rendering.assemblies import ASSEMBLIES, base
    from rendering.assembly import validate
    from rendering import references as R
    rows = []
    # `base()` because a kind may be declared as a VARIANT FACTORY; the
    # reference describes the plain object, so that is what gets measured.
    for kind in sorted(ASSEMBLIES):
        asm = base(kind)
        for m in validate(asm, kind):
            rows.append("    " + m)
        if kind not in R.REFERENCES:
            rows.append(f"    {kind}: built as parts but has NO reference on "
                        "record -- search for one and add it to "
                        "rendering/references.py")
            continue
        for m in (R.check_proportion(kind, asm), R.check_stature(kind, asm)):
            if m:
                rows.append("    " + m)
    if rows:
        return ("  a parts-built prop is checked against the real object's "
                "proportions AND\n"
                "  against how tall it should stand in the world.\n"
                "  Fix the model, or correct the reference if the reference "
                "is what is wrong\n"
                "  (its `real` is in the MODEL's axes: +x length, +y across, "
                "+z up).\n"
                + "\n".join(rows))


# ------------------------------------- 8b. volumes answer to is_solid_prop
# THE RULE: registering a kind in a volume TABLE is not enough. The scene's
# emit path asks ONE question -- `props.is_solid_prop(kind)` -- and anything
# that answers False is treated as a flat decal, falls through to
# Decoration.draw, finds no `_draw_<kind>` method and ships a MAGENTA SQUARE
# into the world.
# This is not hypothetical: converting the first six props to assemblies
# removed them from SOLID_PROPS (correctly) and left `is_solid_prop` reading
# only the old two tables, so the freshly dressed lodge yard rendered six
# magenta placeholders. Check 2 passed the whole time -- it tests the tables,
# and the tables were right. The predicate is the thing that has to agree, so
# the predicate is what gets asserted here.
@check("every volume kind answers True to props.is_solid_prop")
def _solid_predicate():
    from rendering.props import SOLID_PROPS, _STANDEE_KINDS, is_solid_prop
    from rendering.assemblies import ASSEMBLIES
    rows = []
    for label, table in (("ASSEMBLIES", ASSEMBLIES),
                         ("SOLID_PROPS", SOLID_PROPS),
                         ("_STANDEE_KINDS", _STANDEE_KINDS)):
        for kind in sorted(table):
            if not is_solid_prop(kind):
                rows.append(f"    {kind!r} is in {label} but is_solid_prop "
                            "says no -> renders as a magenta square")
    # AND NOT IN TWO OF THEM. draw_prop_solid prefers the assembly, so a kind
    # left behind in SOLID_PROPS keeps a hand-written draw that no longer runs
    # -- dead code free to disagree with what actually ships. It did: `lantern`
    # was converted as a hand-carried hurricane lantern while the unreachable
    # function beside it went on being the iron POST lamp the scenes and the
    # light tables had always meant. Nothing pointed that out because nothing
    # was looking.
    for kind in sorted(set(ASSEMBLIES) & set(SOLID_PROPS)):
        rows.append(f"    {kind!r} is in BOTH ASSEMBLIES and SOLID_PROPS -- "
                    "the assembly wins, so\n      delete the hand-written "
                    "draw rather than leave it to rot")
    if rows:
        return ("  a kind the tilt draws as geometry must be recognised by\n"
                "  rendering/props.py is_solid_prop -- that predicate, not the\n"
                "  table, is what the scene emit path asks -- and must be\n"
                "  registered in exactly one place.\n"
                + "\n".join(rows))


# ------------------------------------ 8c. every billboard char has a drawer
# THE RULE: under the tilt, an object char in `_TILT_BILLBOARD_CHARS` is
# dispatched by its KIND, and only `tree` and `cornstalk` have a branch. A new
# billboard kind with no branch draws NOTHING -- the terrain version of the
# magenta square, except quieter, because empty ground looks like ground.
# This check also pins down a second failure it grew out of: `_tilt_standee`,
# the flat-card path the docs described as how trees are drawn, had been dead
# for some time (every billboard char routes to a solid). A full tree redesign
# went into the wrong function before anyone noticed.
@check("every tilt billboard char has a live draw branch")
def _billboard_kinds():
    from scenes.terrain import (_TILT_BILLBOARD_CHARS, _TILT_BILLBOARD_KINDS,
                                OBJECT_DEFS)
    rows = []
    for ch in sorted(_TILT_BILLBOARD_CHARS):
        kind = OBJECT_DEFS.get(ch, {}).get("kind")
        if kind not in _TILT_BILLBOARD_KINDS:
            rows.append(f"    {ch!r} is a billboard char of kind {kind!r}, "
                        "which _tilt_tile_box has no branch for -> it draws "
                        "nothing at all")
    if rows:
        return ("  a billboard char must be dispatched to a real drawer in\n"
                "  scenes/terrain.py _tilt_tile_box. Add a branch there AND\n"
                "  the kind to _TILT_BILLBOARD_KINDS.\n" + "\n".join(rows))


# ------------------------------------------------------- 9. TOOLS.md fresh
# THE RULE: TOOLS.md is GENERATED from each tool's own docstring
# (`python tools/index.py --md`) precisely so a hand-maintained list of 40+
# tools cannot rot the way the canon's dead file references did. This check
# is what makes "generated" true rather than aspirational.
@check("TOOLS.md matches the actual tool shelf")
def _tools_md():
    sys.path.insert(0, os.path.join(_ROOT, "tools"))
    import index as _index
    want = _index.render_md()
    try:
        have = open("TOOLS.md").read()
    except FileNotFoundError:
        return "    TOOLS.md is missing. Run: python tools/index.py --md"
    if have != want:
        return ("    TOOLS.md is stale (a tool was added, renamed, removed, or\n"
                "    its docstring's first line changed).\n"
                "    Regenerate: python tools/index.py --md")


# ------------------------------------------- 10. amalgam _MASS_DY in sync
# THE RULE: rendering/amalgam.py's `_MASS_DY` records how far ABOVE its `y`
# each MASS part draws itself, so `assemble` can aim at a body HEIGHT rather
# than a raw offset. Those numbers are a copy of each function's own
# `cy = y - N`, and a copy rots: change a part's cy and the table silently
# lies, which puts a body back to floating clear of the legs holding it up --
# exactly the defect the table was added to fix, and one no test would notice
# because nothing crashes. So the copy is verified against the source.
@check("amalgam _MASS_DY matches each mass part's own cy offset")
def _mass_dy():
    import re
    src = open(os.path.join(_ROOT, "rendering", "amalgam.py")).read()
    sys.path.insert(0, _ROOT)
    from rendering.amalgam import MASS, _MASS_DY
    rows = []
    for name, fn in MASS:
        body = src[src.index("def %s(" % fn.__name__):]
        nxt = body.find("\ndef ")
        body = body[:nxt] if nxt > 0 else body      # THIS function only
        # The assignment is a TUPLE -- `cx, cy = x + 2, y - 58` -- so a naive
        # r"cy\s*=\s*y\s*-\s*(\d+)" never matches it. It silently "passed"
        # three parts by running past the end of their bodies and matching a
        # LATER function's line, which is the failure mode a check must not
        # have: green for the wrong reason.
        m = re.search(r"\bcy\s*=[^\n]*?\by\s*-\s*(\d+)", body)
        if not m:
            rows.append("    %-8s %s has no 'cy = y - N' to check against"
                        % (name, fn.__name__))
            continue
        real = int(m.group(1))
        if _MASS_DY.get(name) != real:
            rows.append("    %-8s table says %s, %s draws at y - %d"
                        % (name, _MASS_DY.get(name), fn.__name__, real))
    missing = [n for n, _ in MASS if n not in _MASS_DY]
    if missing:
        rows.append("    not in _MASS_DY at all: " + ", ".join(missing))
    if rows:
        return ("  _MASS_DY is out of sync with the mass parts it describes;\n"
                "  assemble() will place these bodies at the wrong height.\n"
                + "\n".join(rows))


def main():
    print("THRESHOLD conventions guard\n")
    for fn in (_fonts, _tilt_sets, _light_tables, _gate_keys, _doc_refs,
               _lost_silent):
        pass  # checks already ran at import via the decorator
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} convention(s) violated.")
        return 1
    print("All conventions hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
