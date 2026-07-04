"""Game state + the cot's disk save.

The in-memory store for the flags / args / scene-visit counts the
runtime reads and writes during a run, plus ONE disk slot (2026-07,
the shipping persistence pass). The typewriter rule holds: the only
thing that ever writes the slot is SLEEPING AT THE COT
(Game._sleep_at_cot), which snapshots the run and lands the wake-up
back at the cot. Continue on the title menu reads it back; a death or
a quit costs everything since the last sleep, never the whole run.

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
        # 2026-07 rename: the keystone item was always the Pallid Mask,
        # but its key was "sigil_rubbing" (a relic of a cut charcoal-
        # rubbing design). Slots written before the rename migrate on
        # read; the taken-flag came along for the same reason.
        items = base.get("inventory", {}).get("items")
        if isinstance(items, list):
            for it in items:
                if (isinstance(it, list) and it
                        and it[0] == "sigil_rubbing"):
                    it[0] = "pallid_mask"
        flags = base.get("flags")
        if isinstance(flags, dict) and flags.pop("sign_rubbing_taken",
                                                 False):
            flags["pallid_mask_taken"] = True
        self.data = base
        return True
