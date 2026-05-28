"""Enemies: chase + flee AI, on_kill callback support, optional dash
burst, optional projectile attack. Plus the standalone Projectile
entity used by ranged enemies."""
import math
import random
import pygame
from rendering.sprites import draw_npc_sprite
from rendering.transform import draw_vessel_bloom


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
                if abs(self.x - e.x) < 14 and abs(self.y - e.y) < 14:
                    e.hp -= self.dmg
                    e.flash = 0.12
                    self.alive = False
                    self.hit = True
                    return
            # Round-14: friendly bullets hit NPCs too. Any village
            # NPC -- the kid, the fisherman, the shopkeep -- can be
            # shot. The kill counter tracks it.
            for n in scene.npcs:
                if not getattr(n, "alive", True):
                    continue
                if abs(self.x - n.x) < 14 and abs(self.y - n.y) < 14:
                    n.take_damage(self.dmg)
                    self.alive = False
                    self.hit = True
                    return
        else:
            if abs(self.x - player.x) < 14 and abs(self.y - player.y) < 14:
                player.take_damage(self.dmg)
                self.alive = False
                self.hit = True

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
    def __init__(self, x, y, kind="bandit", hp=20, atk=6, speed=1.6,
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
        # Mirror of the player's tap/charge attack model. `can_charge`
        # bandits (and the well kid-boss) wind up before swinging --
        # the gold-ring telegraph fires during the final
        # `charge_windup` seconds of the attack cooldown, then the next
        # melee tick lands a `charge_mult` x normal hit and resets to
        # `charge_cd` (longer than the regular 1.1s rhythm). Defaulting
        # `can_charge` to None means: bandits get it for free, anything
        # else opts in explicitly.
        if can_charge is None:
            can_charge = (kind == "bandit")
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
        # NPC.chaser: SCOUT (wander/waypoints) -> CHASE on LOS
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
        # the wolves still slope toward you, the bandits still fall in
        # behind -- but they don't strike. They only watch.
        self.atk = 0
        self.shoot_dmg = 0
        self.charge_mult = 0
        self.can_shoot = False
        dx = player.x - self.x; dy = player.y - self.y
        d = math.hypot(dx, dy) or 1
        # Hidden players are invisible to enemies that respect hiding
        # (cultist chasers in the depths). Forces the wander branch by
        # treating distance as effectively infinite.
        if (getattr(self, "respects_hide", False)
                and getattr(player, "hidden", None) is not None):
            d = 1e9
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
        # machine. Other chase-AI enemies (wolves, bandits, etc.)
        # keep the prior straight-line chase + waypoint/wander
        # branch unchanged.
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
            # Gold ring shows the entire time the bandit is charging.
            # The swing lands the moment -attack_timer >= charge_windup
            # AND the player is in atk_range -- so a bandit can finish
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
            wps = getattr(self, "waypoints", None)
            if wps:
                # Fixed-route patrol: walk to current waypoint, advance
                # the index when arrived. No random wander.
                wi = getattr(self, "_wp_i", 0) % len(wps)
                tx, ty = wps[wi]
                ddx = tx - self.x; ddy = ty - self.y
                dd = math.hypot(ddx, ddy)
                if dd <= 4:
                    self._wp_i = (wi + 1) % len(wps)
                    self.move_timer = getattr(self, "wp_pause", 1.2)
                elif self.move_timer > 0:
                    self.move_timer -= dt
                else:
                    step_x = (ddx / dd) * self.speed * 30 * dt
                    step_y = (ddy / dd) * self.speed * 30 * dt
                    if not scene.is_solid_at(self.x + step_x, self.y):
                        self.x += step_x
                    if not scene.is_solid_at(self.x, self.y + step_y):
                        self.y += step_y
                    self.facing = (ddx / dd, ddy / dd)
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
        the shortest path through the fold."""
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
        the NPC chaser machine. SCOUT defaults to the prior
        waypoint / wander branch so the existing depths corridor
        routes still drive the patroller in idle. CHASE walks
        straight at the player; SEARCH walks to last-seen and
        mills; INVESTIGATE walks to step source and mills."""
        import pygame
        # Wrap-aware distance so cultists in wrap scenes follow the
        # shortest path through the fold. If the player is at the
        # west edge and the cultist is at the east edge of a wrap_x
        # scene, they read each other as adjacent, not as the full
        # map width apart.
        dx = scene.world_dx(self.x, player.x)
        dy = scene.world_dy(self.y, player.y)
        d = math.hypot(dx, dy)
        # Hidden players are invisible to cultists that respect
        # hiding. Forces has_los False without leaking 1e9 into
        # downstream math.
        is_hidden = (getattr(self, "respects_hide", False)
                     and getattr(player, "hidden", None) is not None)
        has_los = (not is_hidden
                   and d < self.aggro
                   and getattr(player, "hidden", None) is None)
        # Audio reaction. Only in SCOUT (existing target intent
        # would otherwise rubber-band on every step).
        if self._cult_state == "scout":
            evt = getattr(scene, "_last_step_event", None)
            if evt is not None:
                ex, ey, loud, et = evt
                now = pygame.time.get_ticks() / 1000.0
                if (now - et < 0.4
                        and math.hypot(ex - self.x, ey - self.y) < 180
                        and loud >= 0.7):
                    self._cult_state = "investigate"
                    self._cult_state_t = 4.0
                    self._last_seen_pos = (ex, ey)
                    self.move_target = None
        # Promotion to CHASE on LOS, from any state.
        if has_los:
            if self._cult_state != "chase":
                self._cult_state = "chase"
                self._cult_state_t = 0.0
                self.move_target = None
                self.morph_target = 1.0
            self._last_seen_pos = (player.x, player.y)
            if d > self.atk_range:
                self._cult_step(player.x, player.y, dt, scene)
            return
        # Demotion from CHASE: lost the player. Drop into SEARCH.
        if self._cult_state == "chase":
            self._cult_state = "search"
            self._cult_state_t = 6.0
        if self._cult_state == "search":
            self._cult_state_t -= dt
            if self._cult_state_t <= 0 or self._last_seen_pos is None:
                self._cult_state = "scout"
                self.move_target = None
                self.move_timer = 0.0
                self.morph_target = 0.0
                return
            tx, ty = self._last_seen_pos
            d_target = math.hypot(self.x - tx, self.y - ty)
            if d_target > 30:
                self._cult_step(tx, ty, dt, scene)
            else:
                # Mill: small random steps within ~80 px of last-
                # seen. Re-uses the wander move_target field --
                # picks a new one on a short timer.
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
                return
            tx, ty = self._last_seen_pos
            d_target = math.hypot(self.x - tx, self.y - ty)
            if d_target > 14:
                self._cult_step(tx, ty, dt, scene)
            else:
                # At the source. Slow facing rotation so the
                # cultist visibly scans before giving up.
                ang = (pygame.time.get_ticks() / 1000.0) % math.tau
                self.facing = (math.cos(ang), math.sin(ang))
            return
        # Default SCOUT: fall through to the prior waypoint /
        # wander branch. Mirrors the original code path so depths
        # corridor routes keep working.
        wps = getattr(self, "waypoints", None)
        if wps:
            wi = getattr(self, "_wp_i", 0) % len(wps)
            tx, ty = wps[wi]
            ddx = tx - self.x; ddy = ty - self.y
            dd = math.hypot(ddx, ddy)
            if dd <= 4:
                self._wp_i = (wi + 1) % len(wps)
                self.move_timer = getattr(self, "wp_pause", 1.2)
            elif self.move_timer > 0:
                self.move_timer -= dt
            else:
                step_x = (ddx / dd) * self.speed * 30 * dt
                step_y = (ddy / dd) * self.speed * 30 * dt
                if not scene.is_solid_at(self.x + step_x, self.y):
                    self.x += step_x
                if not scene.is_solid_at(self.x, self.y + step_y):
                    self.y += step_y
                self.facing = (ddx / dd, ddy / dd)
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

    def draw(self, surf, cam_x, cam_y):
        if not self.alive: return
        sx = int(self.x - cam_x); sy = int(self.y - cam_y)
        kind = "glitch_npc" if self.kind == "_glitch" else self.kind
        m = getattr(self, "morph", 0.0)
        if m > 0.0:
            draw_vessel_bloom(surf, sx, sy, kind, self.facing, m,
                              seed=id(self) & 0xffff)
        else:
            draw_npc_sprite(surf, sx, sy, kind, self.facing)
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
        # no math. The cult and the bandits and the wolves are all
        # threats whose state the player cannot read.
