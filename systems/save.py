"""In-session game state.

THRESHOLD is a single-session game: there is no save file on disk.
This class is just an in-memory store for the flags / args /
scene-visit counts that the rest of the runtime reads and writes
during a run. New Game builds a fresh state; quitting to the title
throws it away.
"""
import json
import datetime

DEFAULT_SAVE = {
    "scene": "bedroom",
    "spawn": "default",
    "player": {"hp": 100, "max_hp": 100},
    # The PI starts with their sidearm and a handful of rounds (1994 noir),
    # plus yesterday's paper: the April 14 issue, picked up before the
    # drive north. Brimley hasn't seen a paper since the trucks stopped
    # in spring, so yesterday's date makes the cut-off legible, and
    # Hettie at the store trades a load of ammo for it
    # (scenes/dialogue.py).
    "inventory": {"items": [["pistol", 1], ["pistol_ammo", 8],
                            ["newspaper", 1]],
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
