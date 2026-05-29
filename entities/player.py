"""Player character: movement, desperation melee (stun), save/load."""
import math
import pygame
from systems.items import Inventory


class Player:
    def __init__(self, x, y):
        self.x = x; self.y = y
        self.speed = 130
        self.facing = (0, 1)
        self.size = 12
        self.walk_phase = 0.0
        self.step_timer = 0.0
        self.bump_timer = 0.0
        self.hp = 100
        self.max_hp = 100
        self.invuln = 0.0
        # Round-13: tracks whether the player is currently standing in
        # the brimley river. Toggled in Game.update_player based on
        # the floor under their feet. Walking out (onto bridge or land)
        # flips this to False; re-entering requires stepping onto the
        # designated river entry tile.
        self.in_river = False
        # THRESHOLD sprint state. Held SHIFT pumps speed by 1.7x and
        # drains the wind meter. Wind regenerates (sprint_regen) whenever
        # you are NOT sprinting; only running the meter fully to empty
        # trips the hard winded lockout (sprint_cd_max) during which
        # sprint cannot fire.
        self.sprint_active = False
        self.sprint_t = 3.0          # seconds of wind remaining
        self.sprint_t_max = 3.0
        self.sprint_cd = 0.0         # winded lockout remaining (full depletion)
        self.sprint_cd_max = 6.0
        self.sprint_regen = 0.75     # wind recovered per second while not sprinting
        # THRESHOLD desperation melee. A non-lethal shove that STUNS a
        # cultist/shadow for a beat -- never a kill (the King is still
        # the only lethal thing). melee_swing_t drives a brief visual;
        # melee_cd gates the next swing.
        self.melee_cd = 0.0
        self.melee_swing_t = 0.0
        self.melee_dir = (0, 1)
        # THRESHOLD hide state. Set to a hide-spot id while the player
        # is in cover; None when out in the open. While hidden, the
        # player draws at low alpha, watchers/cultists ignore them,
        # and Pursuer proximity rises faster (the Ire feels them
        # holding still).
        self.hidden = None
        self.hide_origin = None
        # THRESHOLD save ritual: when the cot interaction starts the
        # sleep sequence the Game flips this true so draw_player_sprite
        # renders the prone variant on top of the cot. Cleared on wake.
        self.prone = False
        self.inventory = Inventory()
        # The knife now lives on the kitchen table in the house scene.
        # The player has to pick it up before they can attack effectively
        # (unequipped weapon = atk 1).

    def take_damage(self, amt):
        # THRESHOLD: nothing in the world can harm the player. HP is
        # vestigial -- it stays on the save object for compatibility,
        # but no enemy can drain it, and the death/respawn loop is
        # disconnected from this number. The thing that ends the
        # player is the Pursuer, and the Pursuer doesn't deal damage
        # -- it closes the threshold.
        return

    def from_save(self, data):
        p = data.get("player", {})
        self.hp = p.get("hp", 100)
        self.max_hp = p.get("max_hp", 100)
        inv_data = data.get("inventory")
        if inv_data:
            self.inventory.from_save(inv_data)

    def to_save(self):
        return {"hp": int(self.hp), "max_hp": int(self.max_hp)}
