"""Persistent save state."""
import time
import os
import json
import datetime
import getpass
from constants import SAVE_DIR

DEFAULT_SAVE = {
    "version": 3,
    "scene": "bedroom",
    "spawn": "default",
    "player": {"hp": 100, "max_hp": 100},
    "inventory": {"items": [], "equipped": {"weapon": None, "armor": None}},
    "flags": {},
    "arg": {
        "evidence_count": 0,
        "save_count": 0,
        "first_played": None,
        # Round-7: evidence list is mirrored in save data so the in-game
        # Notes page (N key) can show what's been collected without
        # having to read .archive/. Cleared on New Game; the .archive/
        # files persist on disk for the meta-ARG layer.
        "evidence": [],
        # Day counter -- advances on sleep + on patrol capture. Sets
        # the floor for the day-phase / event scheduler. Day 1 is
        # the player's first night in the Innkeeper's spare room.
        "day_count": 1,
        # Day phase: "morning" | "afternoon" | "dusk" | "night".
        # Drives ambient mood + which patrols are awake. Most things
        # in the build still treat _is_dusk as a save flag, so this
        # is purely additive scaffolding for the next pass.
        "day_phase": "afternoon",
    },
    "stats": {
        "total_play_seconds": 0,
        "scene_visits": {},
    },
}


class Save:
    def __init__(self, slot=1):
        self.slot = slot
        self.path = os.path.join(SAVE_DIR, f"slot{slot}.json")
        self.data = None
        self.session_started = time.time()

    def exists(self):
        return os.path.exists(self.path)

    def delete(self):
        """Wipe the slot file from disk and clear in-memory state.
        Used by the title-screen 'Delete Save' option so the next
        title-menu render flips to the 'New Save' label."""
        self.data = None
        try:
            os.remove(self.path)
        except OSError:
            pass

    def new(self):
        self.data = json.loads(json.dumps(DEFAULT_SAVE))
        self.data["arg"]["first_played"] = datetime.datetime.now().isoformat()
        return self.data

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            for k, v in DEFAULT_SAVE.items():
                if k not in self.data:
                    self.data[k] = v
            for k, v in DEFAULT_SAVE["arg"].items():
                if k not in self.data["arg"]:
                    self.data["arg"][k] = v
            return self.data
        except Exception:
            return self.new()

    def write(self):
        if self.data is None: return
        delta = time.time() - self.session_started
        self.data["stats"]["total_play_seconds"] = self.data["stats"].get("total_play_seconds", 0) + delta
        self.session_started = time.time()
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

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
