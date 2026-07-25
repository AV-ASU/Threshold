"""What tools does this project have? (run me before writing a throwaway script)

    python tools/index.py            # the whole shelf, grouped
    python tools/index.py sight      # only tools matching a word

This exists because the shelf got invisible. A session once hand-rolled four
scratchpad scripts to preview a prop, render a scene at four facings, and
check a light -- while `preview_props_sheet.py`, `capture_facings.py` and
`light_audit.py` sat right here doing it better. The docstring of every tool
is its own first line; this just reads them.

**If you are about to write a one-off script, check here first.** If the tool
you want does not exist, WRITE IT INTO tools/ rather than the scratchpad, so
the next person gets it too (CLAUDE.md, "Make the check, not the note").
"""
import ast
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# The handful worth reaching for by reflex, and the job each one owns.
START_HERE = [
    ("capture_facings.py",
     "LOOK at a scene from N/E/S/W. Asserts the facings differ, so it cannot\n"
     "     hand back the same view four times. The VISION.md look pass."),
    ("preview_props_sheet.py",
     "LOOK at a prop kind in isolation against a height ruler, BEFORE placing\n"
     "     it. Scene-dressing step 2: never place a kind by its name."),
    ("kind.py",
     "What tilt set / light tables / art / placements does a kind have?\n"
     "     Answers 'will this render as a flat stain' without a scratch script."),
    ("light_audit.py",
     "Coverage overlay for a scene's lighting: mechanical radius, visible\n"
     "     pool, and THE DARK as a reviewable shape. Run before/after placing\n"
     "     any fixture."),
    ("capture_world.py",
     "The deterministic before/after render gate (--tag / --diff) for\n"
     "     byte-identity on rendering refactors."),
    ("check_canon_keys.py",
     "Tripwire: the load-bearing item/scene keys named in NARRATIVE.md still\n"
     "     exist in the source."),
]

GROUPS = (
    ("LOOK AT THE WORLD", ("capture_", "contact_sheet", "render_scenes",
                           "preview_scene", "preview_tilt", "preview_arrival",
                           "preview_phase", "preview_skybox", "preview_wrap")),
    ("LOOK AT ONE THING", ("preview_props", "kind.py", "preview_king",
                           "preview_mask", "preview_bearer", "preview_storm",
                           "preview_pseudo", "preview_ashfall",
                           "preview_fold_shards")),
    ("LIGHT / SIGHT / OCCLUSION", ("light_audit", "preview_sight",
                                   "preview_blindspot", "preview_occlusion",
                                   "preview_heightfield",
                                   "preview_river_channel")),
    ("PORTALS & DOORS", ("portal", "preview_portal", "preview_rift",
                         "preview_door", "preview_seethrough")),
    ("AUDIO", ("audio_probe", "preview_sfx", "preview_chase_cues")),
    ("AUDIT / PROFILE", ("audit_", "check_canon", "profile_")),
)


def first_line(path):
    try:
        doc = ast.get_docstring(ast.parse(open(path).read())) or ""
        return doc.split("\n")[0].strip()
    except Exception:
        return ""


def render_md():
    """TOOLS.md, generated from each tool's own docstring so it cannot drift.
    `tests/conventions.py` regenerates this and fails if the checked-in file
    disagrees, so adding a tool without refreshing the doc is a red gate."""
    names = sorted(f for f in os.listdir(_HERE)
                   if f.endswith(".py") and f != "index.py")
    out = [
        "# THRESHOLD — Tools",
        "",
        "> **Generated file — do not hand-edit.** Rebuild with",
        "> `python tools/index.py --md`. Each line is the first line of that",
        "> tool's own docstring, so this list cannot drift from the shelf;",
        "> `tests/conventions.py` fails if it does. Every tool is headless and",
        "> self-configures the SDL dummy drivers.",
        "",
        "Not canon, and never required reading — it is a shelf label. The",
        "terminal version is `python tools/index.py [word]`.",
        "",
        "## Start here — the reflex tools",
        "",
    ]
    for name, why in START_HERE:
        if os.path.exists(os.path.join(_HERE, name)):
            flat = " ".join(why.split())
            out.append(f"- **`tools/{name}`** — {flat}")
    out.append("")
    shown = set()
    for title, prefixes in GROUPS:
        rows = [n for n in names
                if any(p in n for p in prefixes) and n not in shown]
        if not rows:
            continue
        out += [f"## {title.title()}", ""]
        for n in rows:
            shown.add(n)
            out.append(f"- `tools/{n}` — {first_line(os.path.join(_HERE, n))}")
        out.append("")
    rest = [n for n in names if n not in shown]
    if rest:
        out += ["## Other", ""]
        for n in rest:
            out.append(f"- `tools/{n}` — {first_line(os.path.join(_HERE, n))}")
        out.append("")
    return "\n".join(out)


def main():
    if "--md" in sys.argv[1:]:
        path = os.path.join(os.path.dirname(_HERE), "TOOLS.md")
        open(path, "w").write(render_md())
        print(f"wrote {path}")
        return 0
    q = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    names = sorted(f for f in os.listdir(_HERE)
                   if f.endswith(".py") and f != "index.py")

    if not q:
        print("\nSTART HERE -- the reflex tools\n" + "=" * 62)
        for name, why in START_HERE:
            if os.path.exists(os.path.join(_HERE, name)):
                print(f"  {name}\n     {why}")
        print()

    shown = set()
    for title, prefixes in GROUPS:
        rows = [n for n in names
                if any(p in n for p in prefixes) and n not in shown]
        if q:
            rows = [n for n in rows
                    if q in n.lower() or q in first_line(
                        os.path.join(_HERE, n)).lower()]
        if not rows:
            continue
        print(f"{title}\n" + "-" * 62)
        for n in rows:
            shown.add(n)
            print(f"  {n:30} {first_line(os.path.join(_HERE, n))[:60]}")
        print()

    rest = [n for n in names if n not in shown]
    if q:
        rest = [n for n in rest if q in n.lower()
                or q in first_line(os.path.join(_HERE, n)).lower()]
    if rest:
        print("OTHER\n" + "-" * 62)
        for n in rest:
            print(f"  {n:30} {first_line(os.path.join(_HERE, n))[:60]}")
        print()
    if not q:
        print("Every tool is headless and self-configures the SDL dummy drivers.\n"
              "Filter with: python tools/index.py <word>\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
