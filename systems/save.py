"""Game state + the evidence-checkpoint disk save.

The in-memory store for the flags / args / scene-visit counts the
runtime reads and writes during a run, plus ONE disk slot (2026-07).
The only writer of the slot is EVIDENCE PICKUP (Game._autosave, fired
from _evidence's canonical branch: the clue IS the checkpoint), which
snapshots hp / inventory / the current scene and a cooled visibility.
Continue on the title menu reads it back and wakes at the scene the
last clue was found in; a death or a quit costs everything since the
last clue, never the whole run. The cot is a pure REST (heal +
visibility cool), not a save.

The slot lives in a per-user data dir (THRESHOLD_SAVE_DIR overrides
it for tests); writes are atomic (tmp + replace); a missing or corrupt
file simply means no Continue.
"""
import json
import os
import tempfile
import datetime

DEFAULT_SAVE = {
    "scene": "bedroom",
    "spawn": "default",
    "player": {"hp": 100, "max_hp": 100},
    # The PI starts with a handful of rounds (1994 noir) and yesterday's
    # paper. The SIDEARM itself is not in his pocket at wake: it is on the
    # writing desk in the spare room, beside his case notes, and he grabs
    # it on the way out (scenes/house.py build_bedroom). The paper is the
    # April 14 issue, picked up before the drive north; Brimley hasn't seen
    # one since the trucks stopped at the mid-January seal, so yesterday's
    # date makes the three-month cut-off legible, and Hettie at the store
    # trades a load of ammo for it (scenes/dialogue.py).
    "inventory": {"items": [["pistol_ammo", 8], ["newspaper", 1]],
                  "equipped": {"weapon": None, "armor": None}},
    "flags": {},
    "arg": {
        "evidence": [],
    },
    "stats": {
        "scene_visits": {},
    },
}


class Save:
    def __init__(self, slot=1):
        self.data = None

    def new(self):
        self.data = json.loads(json.dumps(DEFAULT_SAVE))
        self.data["arg"]["first_played"] = datetime.datetime.now().isoformat()
        return self.data

    def flag(self, key, default=False):
        return self.data["flags"].get(key, default)

    def set_flag(self, key, value=True):
        self.data["flags"][key] = value

    def arg(self, key, default=None):
        return self.data["arg"].get(key, default)

    def set_arg(self, key, value):
        self.data["arg"][key] = value

    def next_seq(self):
        """The next write-order number for the PI's notebook.

        The Casebook is ONE RUNNING DOCUMENT (maintainer, 2026-07): things go
        in the order he wrote them down, and nothing is ever reordered or
        overwritten. The entries themselves still live in two lists, because
        `evidence` is what the King-gate counts and `notes` is what it must
        not; the ORDER is carried by this stamp instead, so the book can merge
        the two and read as one hand writing down one case without a save
        migration through a hundred call sites.

        Entries with no stamp (a hand-built save in a harness) sort ahead of
        the stamped ones, in their own order, which keeps every existing
        fixture readable."""
        n = int(self.arg("book_seq", 0)) + 1
        self.set_arg("book_seq", n)
        return n

    def visit_scene(self, scene_key):
        v = self.data["stats"]["scene_visits"].get(scene_key, 0)
        self.data["stats"]["scene_visits"][scene_key] = v + 1
        self.data["scene"] = scene_key

    def visits(self, scene_key):
        return self.data["stats"]["scene_visits"].get(scene_key, 0)

    # ---- the disk slot (the cot writes it; Continue reads it) ----
    @staticmethod
    def _disk_dir():
        env = os.environ.get("THRESHOLD_SAVE_DIR")
        if env:
            return env
        if os.name == "nt":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            return os.path.join(base, "THRESHOLD")
        return os.path.join(os.path.expanduser("~"), ".threshold")

    def disk_path(self):
        return os.path.join(self._disk_dir(), "save.json")

    def disk_exists(self):
        try:
            return os.path.isfile(self.disk_path())
        except OSError:
            return False

    def write_disk(self):
        """Atomically write the current state to the slot. Returns True
        on success; a failed write must never crash the sleep beat."""
        if self.data is None:
            return False
        try:
            d = self._disk_dir()
            os.makedirs(d, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
            os.replace(tmp, self.disk_path())
            return True
        except OSError:
            return False

    def load_disk(self):
        """Read the slot into self.data (layered over DEFAULT_SAVE so a
        save from an older build inherits new defaults). Returns True on
        success; False (state untouched) on a missing/corrupt file."""
        try:
            with open(self.disk_path(), "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, ValueError):
            return False
        if not isinstance(loaded, dict) or "flags" not in loaded:
            return False
        base = json.loads(json.dumps(DEFAULT_SAVE))
        for k, v in loaded.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k].update(v)
            else:
                base[k] = v
        self.data = base
        return True
