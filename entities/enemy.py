"""Enemies: chase + flee AI, on_kill callback support, optional dash
burst, optional projectile attack. Plus the standalone Projectile
entity used by ranged enemies."""
import math
import random
import pygame
from rendering.sprites import draw_npc_sprite
from rendering.transform import draw_vessel_bloom
from systems.config import SUS_NOTICE, SUS_SCORE_HOLD, CULT_CHASE_MULT
from systems.stealth import (detection_score, update_suspicion,
                             enter_search, sweep_check, hear_noise,
                             react_hold, errand_step, errand_drop,
                             sync_pause, handoff_step)


def _is_cultist(obj):
    """A cultist target for the player's gun: a cult-tagged NPC, or a
    cultist Enemy."""
    tag = getattr(obj, "tag", None)
    if isinstance(tag, str) and tag.startswith("cult_"):
        return True
    return getattr(obj, "kind", None) == "cultist" \
        or getattr(obj, "sprite_kind", None) == "cultist"


# Sprite kinds a bullet passes straight through: the King, the Watchers
# (the curse handles those on its own line-of-fire path), invisible
# interact-markers, and the various non-corporeal apparitions. Everything
# NOT in this set -- the human locals and the cult -- is flesh and can be
# shot. The player CAN now gun down innocent locals; the cult reacts.
_BULLET_PHANTOM = frozenset({"_invisible", "yellow_king", "watcher",
                             "amalgam"})


def _is_shootable(obj):
    return getattr(obj, "sprite_kind", None) not in _BULLET_PHANTOM


class Projectile:
    """Linear-motion projectile spawned by ranged enemies. Travels in
    its initial direction at `speed` px/s; deals `dmg` to the player
    on contact (one-shot) and despawns on wall hit or after `lifespan`
    seconds. The visual is a glowing pulsing dot in `color`."""

    def __init__(self, x, y, dx, dy, dmg=10, speed=220,
                 color=(210, 188, 70), lifespan=2.5):
        self.x = x; self.y = y
        norm = math.hypot(dx, dy) or 1
        self.dx = dx / norm
        self.dy = dy / norm
        self.speed = speed
        self.dmg = dmg
        self.color = color
        self.alive = True
        self.lifespan = lifespan
        self.t = 0.0
        self.friendly = False
        # Player-gun flags. `stun_only` staggers the target (sets _stun_t)
        # instead of killing -- the gun's behaviour above 3 evidence.
        # `cult_only` restricts a friendly shot to cultists so the player
        # can't accidentally gun down innocent locals.
        self.stun_only = False
        self.stun_dur = 1.6
        self.cult_only = False
        # Set to True for one frame on the tick we hit something. Read
        # by Game so it can play the impact SFX without coupling audio
        # into Projectile.
        self.hit = False

    def update(self, dt, scene, player):
        if not self.alive: return
        self.t += dt
        self.lifespan -= dt
        if self.lifespan <= 0:
            self.alive = False
            return
        new_x = self.x + self.dx * self.speed * dt
        new_y = self.y + self.dy * self.speed * dt
        if scene.is_solid_at(new_x, new_y):
            self.alive = False
            return
        self.x, self.y = new_x, new_y
        if self.friendly:
            for e in scene.enemies:
                if not e.alive: continue
                if self.cult_only and not _is_cultist(e):
                    continue
                if abs(self.x - e.x) < 14 and abs(self.y - e.y) < 14:
                    self._strike(e)
                    self.alive = False
                    self.hit = True
                    return
            for n in scene.npcs:
                if not getattr(n, "alive", True):
                    continue
                if self.cult_only and not _is_cultist(n):
                    continue
                # Phantoms (the King, Watchers, invisible markers) are
                # never struck by a round even with cult_only off.
                if not _is_shootable(n):
                    continue
                if abs(self.x - n.x) < 14 and abs(self.y - n.y) < 14:
                    self._strike(n)
                    self.alive = False
                    self.hit = True
                    return
        else:
            if abs(self.x - player.x) < 14 and abs(self.y - player.y) < 14:
                player.take_damage(self.dmg)
                self.alive = False
                self.hit = True

    def _strike(self, target):
        """Apply a friendly-bullet hit: stagger (stun_only) or wound/kill.
        Works on both Enemy (hp) and NPC (take_damage) targets.

        The stun_only gate is the world's growing refusal to let you kill
        the CULT once you know too much (3+ evidence). It never protected
        a living person: a clean shot always drops an innocent local. So
        the stagger applies only to cultists -- a local takes the round."""
        target.flash = 0.12
        if self.stun_only and _is_cultist(target):
            target._stun_t = max(getattr(target, "_stun_t", 0.0), self.stun_dur)
            # They lose their lock on the player when staggered.
            if hasattr(target, "_has_been_spotted"):
                target._has_been_spotted = False
            return
        if hasattr(target, "take_damage"):
            target.take_damage(self.dmg)        # NPC path
        else:
            target.hp -= self.dmg               # Enemy path
            if target.hp <= 0:
                target.alive = False

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        sx = int(self.x - cam_x); sy = int(self.y - cam_y)
        glow = pygame.Surface((24, 24), pygame.SRCALPHA)
        pulse = 1.0 + math.sin(self.t * 14) * 0.18
        outer = max(4, int(11 * pulse))
        inner = max(2, int(outer * 0.55))
        c = self.color
        pygame.draw.circle(glow, (c[0], c[1], c[2], 80), (12, 12), outer)
        pygame.draw.circle(glow, (c[0], c[1], c[2], 170), (12, 12), inner)
        surf.blit(glow, (sx - 12, sy - 12))
        pygame.draw.circle(surf, (220, 240, 255), (sx, sy), 3)

class Enemy:
    def __init__(self, x, y, kind="cultist", hp=20, atk=6, speed=1.6,
                 aggro=140, atk_range=22, color=(160, 80, 80), drops=None,
                 ai="chase", flee_dir=(1, 0), despawn_x=None, despawn_y=None,
                 drift_speed=None, on_kill=None, respawning=False,
                 can_dash=False, dash_speed_mult=3.2,
                 dash_dur=0.32, dash_cd=2.4, dash_telegraph=0.35,
                 can_shoot=False, shoot_cd=1.4, shoot_dmg=10,
                 shoot_range=320,
                 projectile_color=(210, 188, 70),
                 projectile_speed=220,
                 shoot_sfx=None,
                 attack_cd=1.1,
                 can_charge=None, charge_mult=2.0,
                 charge_windup=0.5, charge_cd=1.6):
        self.x = x; self.y = y
        self.home = (x, y)
        self.kind = kind
        self.hp = hp; self.max_hp = hp
        self.atk = atk
        self.speed = speed
        self.aggro = aggro
        self.atk_range = atk_range
        self.color = color
        self.attack_timer = 0
        self.flash = 0
        self._stun_t = 0.0      # player's shove freezes the AI for a beat
        # Stable per-actor sprite seed (entities/npc.py sprite_seed_for):
        # the fix for id()-alignment locking the cultist mask variant to
        # even picks -- half the masks never spawned.
        from entities.npc import sprite_seed_for
        self.sprite_seed = sprite_seed_for(x, y)
        self.facing = (0, 1)
        self.move_timer = random.uniform(0, 2)
        self.move_target = None
        self.drops = drops or []
        self.alive = True
        self.ai = ai
        self.flee_dir = flee_dir
        self.despawn_x = despawn_x
        self.despawn_y = despawn_y
        self.drift_speed = drift_speed if drift_speed is not None else speed / 2.0
        self.on_kill = on_kill
        # Respawning enemies are re-spawned by their scene's on_enter every
        # time the player walks in. To prevent loot farming, kills against
        # respawning enemies skip drops 85% of the time (gated in
        # Game.apply_attack_damage). First-spawn / boss / shadow drops set
        # this to False and always drop normally.
        self.respawning = respawning
        # Dash modifier on top of "chase" AI. Wolves use this: when the
        # player is in mid-range and the cooldown has expired, the enemy
        # bursts forward at dash_speed_mult * speed for dash_dur seconds,
        # then enters a dash_cd cooldown. dash_t > 0 means actively dashing.
        self.can_dash = can_dash
        self.dash_speed_mult = dash_speed_mult
        self.dash_dur = dash_dur
        self.dash_cd_full = dash_cd
        self.dash_cd = random.uniform(0.5, dash_cd)
        self.dash_t = 0.0
        # Per-enemy windup window for the dash. The default 0.35s suits
        # the wolves; the apex vessel bumps this to 0.8s so the
        # gold-ring telegraph reads as a *commit* rather than a flicker.
        self.dash_telegraph = dash_telegraph
        # Ranged-attack params: when can_shoot is True, the chase AI
        # spawns a Projectile every shoot_cd seconds toward the player
        # (gated by shoot_range so a shooter doesn't snipe across an
        # off-screen arena). projectile_color sets the visual tint --
        # jaundiced by default, but the field is generic for any
        # ranged enemy.
        self.can_shoot = can_shoot
        self.shoot_cd_full = shoot_cd
        self.shoot_cd = random.uniform(0.4, shoot_cd)
        self.shoot_dmg = shoot_dmg
        self.shoot_range = shoot_range
        self.projectile_color = projectile_color
        self.projectile_speed = projectile_speed
        # SFX name to play on each shot. None means silent. Set per-enemy
        # at construction so the policeman can fire `pistol_shot` while a
        # silent shooter stays quiet. The Game polls `just_shot` after
        # each update tick.
        self.shoot_sfx = shoot_sfx
        self.just_shot = False
        # Melee attack-cooldown override. The chase AI used to reset to
        # a hardcoded 1.1s; some enemies (the bosses, scaled to
        # 35 dmg/s) need a different rate. Default keeps prior behavior.
        self.attack_cd = attack_cd
        # Mirror of the player's tap/charge attack model. A `can_charge`
        # enemy winds up before swinging -- the gold-ring telegraph fires
        # during the final `charge_windup` seconds of the attack cooldown,
        # then the next melee tick lands a `charge_mult` x normal hit and
        # resets to `charge_cd` (longer than the regular 1.1s rhythm).
        # Defaulting `can_charge` to None means: opt in explicitly.
        if can_charge is None:
            can_charge = False
        self.can_charge = can_charge
        self.charge_mult = charge_mult
        self.charge_windup = charge_windup
        self.charge_cd = charge_cd
        # Charge telegraph: set each frame in update() when a heavy
        # attack (shoot, dash, or melee charge) is imminent, read each
        # frame in draw() to render a gold ring around the enemy.
        # Mirrors the player's charge ring so combat reads symmetrically.
        self.telegraph = False
        # Cultist behaviour state machine. Mirrors the one on
        # NPC.chaser: SCOUT (wander) -> CHASE on LOS
        # -> SEARCH on lost LOS -> back to SCOUT, with INVESTIGATE
        # detours triggered by loud step events. Only applied to
        # kind=="cultist" enemies. Depths corridors are too narrow
        # for the leader/flank coordination that the overworld
        # patrols use, so flanking is omitted here -- state
        # machine alone, no group dynamics.
        self._cult_state = "scout"
        self._cult_state_t = 0.0
        self._last_seen_pos = None
        # Vessel-bloom transform (see rendering.transform). PROTOTYPE:
        # cultist chasers bloom into the Yellow-King maw on lock-on;
        # final trigger still open.
        self.morph = 0.0
        self.morph_target = 0.0

    def update(self, dt, scene, player):
        if not self.alive: return
        # THRESHOLD: nothing in the world hurts you anymore. The thing
        # that does is never on screen. Force every enemy's damage to
        # zero at the start of every tick so any code path that still
        # triggers a hit lands as a soft tap. The AI keeps moving --
        # the wolves still slope toward you, the cult still falls in
        # behind -- but they don't strike. They only watch.
        self.atk = 0
        self.shoot_dmg = 0
        self.charge_mult = 0
        self.can_shoot = False
        dx = player.x - self.x; dy = player.y - self.y
        d = math.hypot(dx, dy) or 1
        # (The old respects_hide distance zap lived here -- binary
        # invisibility for hidden players. The stealth rework routed all
        # cover through _cult_tick's graded detection_score, and only
        # cultists ever set respects_hide, so the zap was dead code and
        # a trap for future variants: respects_hide now means exactly
        # "concealment scales this eye's score" inside _cult_tick.)
        self.attack_timer -= dt
        self.flash = max(0, self.flash - dt)
        if self._stun_t > 0:
            self._stun_t = max(0.0, self._stun_t - dt)
            return                      # frozen by the player's shove
        self.telegraph = False
        self.just_shot = False
        if self.morph != self.morph_target:
            step = dt / 1.4
            if self.morph < self.morph_target:
                self.morph = min(self.morph_target, self.morph + step)
            else:
                self.morph = max(self.morph_target, self.morph - step)

        if self.ai == "flee":
            if d < self.aggro:
                step_x = -(dx / d) * self.speed * 60 * dt
                step_y = -(dy / d) * self.speed * 60 * dt
                self.facing = (-dx / d, -dy / d)
            else:
                fx, fy = self.flee_dir
                step_x = fx * self.drift_speed * 60 * dt
                step_y = fy * self.drift_speed * 60 * dt
                self.facing = (fx, fy)
            if not scene.is_solid_at(self.x + step_x, self.y):
                self.x += step_x
            if not scene.is_solid_at(self.x, self.y + step_y):
                self.y += step_y
            if self.despawn_x is not None and (
                (self.flee_dir[0] >= 0 and self.x >= self.despawn_x) or
                (self.flee_dir[0] < 0 and self.x <= self.despawn_x)
            ):
                self.alive = False
            if self.despawn_y is not None and (
                (self.flee_dir[1] >= 0 and self.y >= self.despawn_y) or
                (self.flee_dir[1] < 0 and self.y <= self.despawn_y)
            ):
                self.alive = False
            return

        # Cultists run the SCOUT/CHASE/SEARCH/INVESTIGATE state
        # machine. Other chase-AI enemies (wolves, etc.) keep the prior
        # straight-line chase + waypoint/wander branch unchanged.
        if self.kind == "cultist":
            self._cult_tick(dt, scene, player)
            return

        if d < self.aggro:
            speed_mult = 1.0
            if self.can_dash:
                self.dash_cd -= dt
                self.dash_t -= dt
                if self.dash_t > 0:
                    speed_mult = self.dash_speed_mult
                elif self.dash_cd <= 0 and 60 < d < 180:
                    self.dash_t = self.dash_dur
                    self.dash_cd = self.dash_cd_full
                    speed_mult = self.dash_speed_mult
                elif self.dash_cd <= self.dash_telegraph and 60 < d < 180:
                    self.telegraph = True
            # Periodic ranged attack -- only the chase AI drives this
            # branch, matching how dash works. Fires when the player is
            # within shoot_range; never fires during a dash burst.
            if self.can_shoot and self.dash_t <= 0:
                self.shoot_cd -= dt
                if self.shoot_cd <= 0 and d < self.shoot_range:
                    self.shoot_cd = self.shoot_cd_full
                    proj = Projectile(self.x, self.y, dx, dy,
                                      dmg=self.shoot_dmg,
                                      color=self.projectile_color,
                                      speed=self.projectile_speed)
                    scene.projectiles.append(proj)
                    self.just_shot = True
                elif self.shoot_cd <= 0.35 and d < self.shoot_range:
                    self.telegraph = True
            # Charge buildup runs across the WHOLE aggro range, not just
            # in atk_range. Once cooldown clears, attack_timer keeps
            # ticking negative; -attack_timer is "time spent charging".
            # Gold ring shows the entire time the enemy is charging.
            # The swing lands the moment -attack_timer >= charge_windup
            # AND the player is in atk_range -- so a charger can finish
            # charging mid-chase and hit on the very first contact.
            if self.can_charge and self.attack_timer <= 0:
                self.telegraph = True
                if (-self.attack_timer >= self.charge_windup
                        and d <= self.atk_range):
                    player.take_damage(int(self.atk * self.charge_mult))
                    self.attack_timer = self.charge_cd
            if d > self.atk_range:
                step_x = (dx / d) * self.speed * speed_mult * 60 * dt
                step_y = (dy / d) * self.speed * speed_mult * 60 * dt
                if not scene.is_solid_at(self.x + step_x, self.y):
                    self.x += step_x
                if not scene.is_solid_at(self.x, self.y + step_y):
                    self.y += step_y
                if not getattr(self, "lock_facing", False):
                    self.facing = (dx / d, dy / d)
            else:
                if not self.can_charge and self.attack_timer <= 0:
                    player.take_damage(self.atk)
                    self.attack_timer = self.attack_cd
        else:
            self.move_timer -= dt
            if self.move_timer <= 0 or self.move_target is None:
                self.move_timer = random.uniform(2, 4)
                ang = random.uniform(0, math.tau)
                r = random.uniform(20, 80)
                self.move_target = (self.home[0] + math.cos(ang) * r,
                                    self.home[1] + math.sin(ang) * r)
            tx, ty = self.move_target
            ddx = tx - self.x; ddy = ty - self.y
            dd = math.hypot(ddx, ddy)
            if dd > 2:
                step_x = (ddx / dd) * self.speed * 30 * dt
                step_y = (ddy / dd) * self.speed * 30 * dt
                if not scene.is_solid_at(self.x + step_x, self.y):
                    self.x += step_x
                if not scene.is_solid_at(self.x, self.y + step_y):
                    self.y += step_y
                if not getattr(self, "lock_facing", False):
                    self.facing = (ddx / dd, ddy / dd)

    def _cult_step(self, tx, ty, dt, scene, speed_mult=1.0):
        """Move toward (tx, ty) with the chase-style step. Mirrors
        the inline movement used elsewhere in this class but
        usable from the state-machine helper. Returns True if any
        movement happened. Direction is wrap-aware so chasers take
        the shortest path through the fold. The target is first routed
        through scene.nav_toward, so the step bends AROUND cover (and
        through folds) instead of grinding straight into a pillar."""
        tx, ty = scene.nav_toward(self.x, self.y, tx, ty)
        dx = scene.world_dx(self.x, tx)
        dy = scene.world_dy(self.y, ty)
        d = math.hypot(dx, dy)
        if d < 0.5:
            return False
        step_x = (dx / d) * self.speed * speed_mult * 60 * dt
        step_y = (dy / d) * self.speed * speed_mult * 60 * dt
        moved = False
        if not scene.is_solid_at(self.x + step_x, self.y):
            self.x += step_x
            moved = True
        if not scene.is_solid_at(self.x, self.y + step_y):
            self.y += step_y
            moved = True
        # Keep enemy coords in the canonical wrapped range so
        # subsequent ticks compute distances correctly.
        from constants import TILE as _T
        if scene.wrap_x:
            self.x %= scene.w * _T
        if scene.wrap_y:
            self.y %= scene.h * _T
        if not getattr(self, "lock_facing", False) and moved:
            self.facing = (dx / d, dy / d)
        return moved

    def _cult_tick(self, dt, scene, player):
        """Cultist behaviour: SCOUT -> CHASE -> SEARCH (or
        INVESTIGATE on a loud step) -> back to SCOUT. Mirrors
        the NPC chaser machine, including the graded-suspicion
        detection (DESIGN.md §12 Pillar 1): the score (los *
        distance * facing cone * concealment) fills a per-enemy
        suspicion bar, only a FULL bar locks the chase, and an
        active chase holds while any usable score remains. SCOUT
        defaults to the prior waypoint / wander branch so the
        existing depths corridor routes still drive the patroller
        in idle. SEARCH sweeps nearby enclosed hides and CHECKS
        them (the struggle fires via scene._hide_check)."""
        # Wrap-aware distance so cultists in wrap scenes follow the
        # shortest path through the fold (used for atk_range below).
        dx = scene.world_dx(self.x, player.x)
        dy = scene.world_dy(self.y, player.y)
        d = math.hypot(dx, dy)
        # The graded detection score for this eye, this tick. Walls
        # still occlude absolutely; corn scales it; an enclosed hide
        # zeroes it. respects_hide=False eyes ignore cover entirely.
        # Fill/decay is the shared accumulator (systems/stealth.py) so
        # the two cult machines can never drift.
        score = detection_score(
            scene, self.x, self.y, self.facing, player, self.aggro,
            ignore_conceal=not getattr(self, "respects_hide", False))
        sus = update_suspicion(self, score, dt)
        self._sus_alert = False
        # Audio reaction (the shared ear, systems/stealth.hear_noise):
        # scouts turn on any fresh loud event; searchers/investigators
        # hold their target unless something strictly LOUDER pulls them.
        hear_noise(self, scene, 180.0)
        # Anything above a chore drops the chore (mirrors the NPC
        # machine): a worker pulled off his errand stands up out of
        # the task pose; the station index survives for the resume.
        if self._cult_state != "scout":
            errand_drop(self)
        # An active CHASE holds while any usable score remains.
        if self._cult_state == "chase":
            if score >= SUS_SCORE_HOLD:
                self._suspicion = 1.0
                # Bloom is decided ONCE at the lock (below) and held for the
                # chase (play-notes: the first-ever cultist stays human).
                self._last_seen_pos = (player.x, player.y)
                if d > self.atk_range:
                    self._cult_step(player.x, player.y, dt, scene,
                                    speed_mult=CULT_CHASE_MULT)
                return
            # Lost the line: SEARCH, and sweep the enclosed hides
            # around last-seen (Pillar 3 -- searchers hunt cover; the
            # budget scales with the sweep so it isn't abandoned
            # mid-check).
            enter_search(self, scene)
        # Promotion to CHASE only on a FULL suspicion bar.
        elif sus >= 1.0:
            self._cult_state = "chase"
            self._cult_state_t = 0.0
            self.move_target = None
            self._just_locked = True
            if getattr(scene, "_bloom_enabled", False):
                if getattr(scene, "_bloom_armed", False):
                    self.morph_target = 1.0
                else:
                    # First cultist of the run: introduced HUMAN, arms the rest.
                    self.morph_target = 0.0
                    scene._bloom_arm_pending = True
            else:
                self.morph_target = 0.0
            self._last_seen_pos = (player.x, player.y)
            if d > self.atk_range:
                self._cult_step(player.x, player.y, dt, scene,
                                speed_mult=CULT_CHASE_MULT)
            return
        # NOTICE: a scouting cultist whose suspicion is climbing stops
        # and turns toward what it half-saw (the telegraph window).
        if (self._cult_state == "scout" and sus >= SUS_NOTICE
                and score > 0.0 and not getattr(self, "lock_facing", False)):
            m = math.hypot(dx, dy) or 1.0
            self.facing = (dx / m, dy / m)
            self._sus_alert = True
            self.move_target = None
            return
        if self._cult_state == "search":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self.move_target = None
                self.move_timer = 0.0
                self.morph_target = 0.0
                self._sweep_list = []
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 30:
                self._cult_step(tx, ty, dt, scene)
                return
            # At last-known. Sweep the enclosed hides nearby -- walk to
            # each and CHECK it (shared sweep_check; an occupied hide
            # starts the struggle via scene._hide_check).
            if sweep_check(self, scene, player, dt,
                           lambda hx, hy: self._cult_step(hx, hy, dt,
                                                          scene)):
                return
            # Sweep exhausted: mill within ~80 px of last-seen.
            self.move_timer -= dt
            if self.move_timer <= 0 or self.move_target is None:
                self.move_timer = random.uniform(0.8, 1.6)
                ang = random.uniform(0, math.tau)
                r = random.uniform(20, 80)
                self.move_target = (tx + math.cos(ang) * r,
                                     ty + math.sin(ang) * r)
            mtx, mty = self.move_target
            self._cult_step(mtx, mty, dt, scene)
            return
        if self._cult_state == "investigate":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self.move_target = None
                self.move_timer = 0.0
                self.morph_target = 0.0
                self._noise_loud = 0.0
                return
            # The turn-first telegraph: face the sound, hold, then walk.
            if react_hold(self, scene, dt):
                return
            tx, ty = self._last_seen_pos
            d_target = scene.world_dist(self.x, self.y, tx, ty)
            if d_target > 14:
                self._cult_step(tx, ty, dt, scene)
            else:
                # At the source. Slow facing rotation so the
                # cultist visibly scans before giving up.
                ang = (pygame.time.get_ticks() / 1000.0) % math.tau
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # Default SCOUT: pure roam (DESIGN.md §4 -- no preset waypoints).
        # The cultist picks its own reachable goals and wanders the room,
        # pausing to scan, then rolls another -- emergent patrol that routes
        # around cover via _cult_step's nav. lock_facing kneelers are the one
        # exception: they hold their post (a deliberate stationary set-piece),
        # moving only once a trigger flips their aggro and LOS promotes them
        # to CHASE above.
        if getattr(self, "lock_facing", False):
            return
        # The liveness beats first (TODO #23a, mirrors the NPC machine:
        # the synchrony all-stop, then a crossing hand-off -- dressing
        # only, detection already scored this tick above), then errands
        # (stations put the workers to WORK), then the pure roam.
        if sync_pause(self):
            return
        peers = [e for e in getattr(scene, "enemies", [])
                 if getattr(e, "kind", "") == "cultist"]
        if handoff_step(self, peers, scene, dt):
            return
        if errand_step(self, scene, dt,
                       lambda ex, ey: self._cult_step(ex, ey, dt, scene)):
            return
        T = scene.TILE
        # Pause-and-scan on arrival: rotate facing slowly, no movement.
        if self.move_timer > 0:
            self.move_timer -= dt
            self._roam_look = getattr(self, "_roam_look", 0.0) - dt
            if self._roam_look <= 0:
                self._roam_look = 0.4
                ang = random.uniform(0, math.tau)
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # Roll a fresh goal when we have none, just arrived, or a travel
        # budget expired (the goal turned out unreachable -- e.g. boxed off
        # by cover). Picking is cheap (a walkable tile within ~8 blocks); the
        # nav in _cult_step does the routing and the budget re-rolls if it
        # can't get there. ALWAYS pause-scan when arriving or finding nothing,
        # so a boxed-in cultist never busy-loops a re-roll every frame.
        self._roam_travel = getattr(self, "_roam_travel", 0.0) - dt
        arrived = (self.move_target is not None
                   and scene.world_dist(self.x, self.y, self.move_target[0],
                                        self.move_target[1]) < 10)
        if self.move_target is None or arrived or self._roam_travel <= 0:
            had_goal = self.move_target is not None
            self.move_target = None
            for _ in range(12):
                gx = int(self.x // T) + random.randint(-8, 8)
                gy = int(self.y // T) + random.randint(-8, 8)
                wx, wy = gx * T + T // 2, gy * T + T // 2
                if scene._nav_solid_at(wx, wy):
                    continue
                self.move_target = (wx, wy)
                self._roam_travel = 5.0
                break
            if had_goal or self.move_target is None:
                self.move_timer = random.uniform(1.0, 2.2)
                self._roam_look = 0.0
                return
        self._cult_step(self.move_target[0], self.move_target[1], dt, scene)

    def draw(self, surf, cam_x, cam_y, view="front"):
        if not self.alive: return
        sx = int(self.x - cam_x); sy = int(self.y - cam_y)
        kind = self.kind
        m = getattr(self, "morph", 0.0)
        if m > 0.0:
            draw_vessel_bloom(surf, sx, sy, kind, self.facing, m,
                              seed=self.sprite_seed)
        else:
            draw_npc_sprite(surf, sx, sy, kind, self.facing,
                            seed=self.sprite_seed, view=view,
                            pose=getattr(self, "pose", None))
        # THRESHOLD: enemies can no longer hurt the player (atk is
        # zeroed every tick in update). Suppress the gold-ring
        # "charge incoming" telegraph in that case -- a wind-up
        # animation that never lands reads as a parryable combat
        # cue and undermines the dread of a silent approach. When
        # combat is live (atk > 0), telegraphs still draw so the
        # player can react.
        if self.telegraph and self.atk > 0:
            pygame.draw.circle(surf, (240, 220, 80), (sx, sy + 2), 18, 1)
        # Round-14: HP bars removed entirely. Combat is meant to feel
        # opaque -- the player swings, the enemy flashes white on hit
        # (`self.flash`), and at some point it dies. No progress meter,
        # no math. The cult and the wolves are all threats whose state
        # the player cannot read.
