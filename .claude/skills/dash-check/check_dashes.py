"""Dash police — enforce the CLAUDE.md HARD RULE: no em-dashes (—), en-dashes
(–), or double-hyphen (`--`) punctuation in any string the player might read.

Walks the player-facing packages, parses each file's AST, and checks every
string literal (docstrings excluded — those are dev-facing). Exits nonzero
with file:line listings on any hit, prints OK otherwise.

    python .claude/skills/dash-check/check_dashes.py
"""
import ast
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

# Packages whose string literals can reach the screen. tools/ and tests/ are
# dev-only; main.py has no player text but is one file, so include it.
SCAN = ["scenes", "ui", "systems", "entities", "rendering", "main.py"]

EM, EN = "—", "–"
# `--` used as punctuation: exactly two hyphens (3+ is a divider, not a dash).
DOUBLE = re.compile(r"(?<!-)--(?!-)")


def _docstring_nodes(tree):
    """The Constant nodes that are docstrings (first stmt of a module/class/
    function body) — dev-facing, skipped."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                out.add(id(body[0].value))
    return out


def _check_file(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        return [(e.lineno or 0, f"SYNTAX ERROR: {e.msg}")]
    docs = _docstring_nodes(tree)
    hits = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        if id(node) in docs:
            continue
        s = node.value
        bad = []
        if EM in s:
            bad.append("em-dash")
        if EN in s:
            bad.append("en-dash")
        if DOUBLE.search(s):
            bad.append("double-hyphen")
        if bad:
            snip = s.strip().replace("\n", "\\n")
            if len(snip) > 70:
                snip = snip[:67] + "..."
            hits.append((node.lineno, f"[{', '.join(bad)}] {snip!r}"))
    return hits


def main():
    files = []
    for entry in SCAN:
        full = os.path.join(_ROOT, entry)
        if os.path.isfile(full):
            files.append(full)
            continue
        for dirpath, _dirs, names in os.walk(full):
            files.extend(os.path.join(dirpath, n)
                         for n in sorted(names) if n.endswith(".py"))

    total = 0
    for path in sorted(files):
        for lineno, msg in _check_file(path):
            rel = os.path.relpath(path, _ROOT)
            print(f"{rel}:{lineno}: {msg}")
            total += 1

    if total:
        print(f"\nFAIL: {total} dash hit(s) in string literals. "
              f"Rewrite with a period, comma, colon, or a new sentence.")
        return 1
    print(f"OK: no dash punctuation in string literals "
          f"across {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
