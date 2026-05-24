"""Player character: movement, attack (tap + charge), save/load."""
import math
import pygame
from systems.items import Inventory, ITEM_DEFS

# Charge mechanic: hold the attack input for >= CHARGE_THRESHOLD seconds
# to release a charged swing dealing CHARGE_MULT * weapon damage with a
# bigger hitbox + longer cooldown. Tap-release fires the regular swing.
CHARGE_THRESHOLD = 0.55
CHARGE_MULT = 2.0
CHARGE_HITBOX = 44     # px (regular = 30)
CHARGE_COOLDOWN = 0.65
CHARGE_SWING_T = 0.30


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
        self.attack_timer = 0.0     # cooldown after swing
        self.swing_t = 0.0          # active swing animation time
        self.swing_dir = (0, 1)
        self.swing_charged = False  # true while the active swing is a charge
        # Charge state: held while attack input is down. charge_t ticks
        # up while charging. Released swing reads charge_t and either
        # fires a regular tap or a charged swing.
        self.charging = False
        self.charge_t = 0.0
        # Round-13: tracks whether the player is currently standing in
        # the mistlands river. Toggled in Game.update_player based on
        # the floor under their feet. Walking out (onto bridge or land)
        # flips this to False; re-entering requires stepping onto the
        # designated river entry tile.
        self.in_river = False
        # THRESHOLD sprint state. Held SHIFT pumps speed by 1.7x for
        # up to sprint_t_max seconds, then enters a sprint_cd_max
        # cooldown during which sprint cannot fire. Spent state is
        # reset when the cooldown clears.
        self.sprint_active = False
        self.sprint_t = 3.0          # seconds remaining in current sprint
        self.sprint_t_max = 3.0
        self.sprint_cd = 0.0         # seconds remaining in cooldown
        self.sprint_cd_max = 6.0
        # THRESHOLD desperation melee. A non-lethal shove that STUNS a
        # cultist/shadow for a beat -- never a kill (the King is still
        # the only lethal thing). Kept fully separate from the legacy
        # swing_t/attack system so it can't deal damage. melee_swing_t
        # drives a brief visual; melee_cd gates the next swing.
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
        # THRESHOLD opening: how muddy the player's boots are. 1.0 on
        # wake (bedroom scene plants this), decays as they walk. Drives
        # the mud overlay in draw_player_sprite. Not persisted -- mud
        # is a one-time opening cue, not a saved condition.
        self.mud = 0.0
        # THRESHOLD save ritual: when the cot interaction starts the
        # sleep sequence the Game flips this true so draw_player_sprite
        # renders the prone variant on top of the cot. Cleared on wake.
        self.prone = False
        self.inventory = Inventory()
        # The knife now lives on the kitchen table in the house scene.
        # The player has to pick it up before they can attack effectively
        # (unequipped weapon = atk 1).

    def can_attack(self):
        return self.attack_timer <= 0 and self.swing_t <= 0

    def start_charge(self):
        """Begin a press-and-hold attack input. No swing yet; the swing
        fires on release_charge. If we can't attack right now, ignore."""
        if not self.can_attack():
            return False
        self.charging = True
        self.charge_t = 0.0
        return True

    def release_charge(self, audio=None):
        """End the press-and-hold. Returns one of: None (nothing fired),
        "swing" (regular tap melee), "swing_charged" (held melee), or
        "shoot" (pistol). Pistol fires its own ranged attack regardless
        of how long the input was held -- charging a gun is not a
        thing -- and the bare-fist branch never gets the charge bonus
        either; only an equipped melee weapon can deliver a charged
        swing."""
        if not self.charging:
            return None
        held = self.charge_t
        self.charging = False
        self.charge_t = 0.0
        if not self.can_attack():
            return None
        weapon = self.inventory.equipped["weapon"]
        self.swing_dir = self.facing
        if weapon == "old_pistol":
            self.attack_timer = 0.55
            self.swing_t = 0.0
            self.swing_charged = False
            return "shoot"
        if weapon is not None and held >= CHARGE_THRESHOLD:
            self.attack_timer = CHARGE_COOLDOWN
            self.swing_t = CHARGE_SWING_T
            self.swing_charged = True
            return "swing_charged"
        self.attack_timer = 0.45
        self.swing_t = 0.18
        self.swing_charged = False
        return "swing"

    def attack_hitbox(self):
        """Returns (rect, damage) if currently in active swing window, else (None, 0).
        Charged swings get a bigger box and 2x weapon damage."""
        if self.swing_t <= 0:
            return None, 0
        fx, fy = self.swing_dir
        cx = self.x + fx * 22
        cy = self.y + fy * 22
        if self.swing_charged:
            rect = pygame.Rect(0, 0, CHARGE_HITBOX, CHARGE_HITBOX)
            dmg = int(self.inventory.weapon_atk() * CHARGE_MULT)
        else:
            rect = pygame.Rect(0, 0, 30, 30)
            dmg = self.inventory.weapon_atk()
        rect.center = (cx, cy)
        return rect, dmg

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
