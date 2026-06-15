# -*- coding: utf-8 -*-
"""
core/game.py - 游戏主类

Game 主类，负责游戏主循环、输入处理、状态管理和各子系统的协调。
"""

import sys
import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, HEADLESS, HEALTHCHECK,
    HEALTHCHECK_MAX_FRAMES,
    SKY_TOP, SKY_BOTTOM, WHITE, BLACK,
    MOUNTAIN_COLOR, MOUNTAIN_SNOW_COLOR,
    CLOUD_COLOR, CLOUD_ALPHA_INNER, CLOUD_ALPHA_OUTER,
    CLOUD_COUNT, CLOUD_SEED,
    MOUNTAIN_COUNT, MOUNTAIN_SEED,
    PARTICLE_COLORS, DUST_PARTICLE_COLORS, PORTAL_PARTICLE_COLORS,
    COIN_COLOR, COIN_DARK, COIN_COLLECT_SCORE,
    CAMERA_LERP, CAMERA_TARGET_RATIO,
    LEVEL_WIDTH, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    TRANSITION_DURATION_FRAMES, TRANSITION_COLOR,
    LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT,
    LOADING_BAR_BG, LOADING_BAR_FG, LOADING_TEXT_COLOR,
    TOTAL_LEVELS,
    SHOW_VOLUME_PANEL_KEY,
    RANGED_AMMO_MAX,
    PORTAL_COOLDOWN_FRAMES,
)

from entities import Player, Particle, Coin, Platform, Ladder, Portal, PatrolEnemy, ChaseEnemy, Bullet, AmmoPickup
from levels import get_level_config, LEVEL_BUILDERS
from audio import AudioManager
from ui import VolumePanel
from menus import GameState, MenuManager, get_chinese_font

from .state import StateManager
from .level_loader import LevelLoader
from .background import BackgroundManager
from .hud import HUDManager
from .particles import ParticleManager
from .combat import CombatManager


class Game:
    """
    游戏主控制器，管理整个游戏生命周期。

    状态属性:
        screen: 主显示 Surface
        clock: pygame 时钟，用于控制帧率
        tick: 全局帧计数器
        score: 游戏得分（金币 * 10）
        particles: 活跃粒子列表
        camera_x: 相机水平滚动偏移
        platforms: 所有平台列表
        coins: 所有金币列表
        ladders: 所有梯子列表
        portals: 所有传送门列表
        patrol_enemies: 所有巡逻怪列表
        chase_enemies: 所有追踪怪列表
        player: 玩家对象
        font: 小字体（HUD）
        big_font: 大字体（标题等）
        clouds: 云朵数据 + 预渲染 Surface 列表
        bg_mountains: 背景山脉数据列表
        _sky_surface: 预渲染的天空渐变 Surface（性能优化）
        _stars_surface: 预渲染的星空 Surface
        current_level: 当前关卡编号
        game_state: 当前游戏状态（playing/transitioning/loading）
        transition_frame: 过渡动画帧计数器
        transition_phase: 过渡阶段（0=淡出，1=加载，2=淡入）
        pending_level: 待加载的目标关卡编号
        pending_spawn: 待加载的目标出生点 (x, y)
        level_config: 当前关卡配置对象
        loading_progress: 加载进度 0.0~1.0
    """

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("平台跳跃")
        self.clock = pygame.time.Clock()
        self.tick = 0
        self.score = 0
        self.particles = []
        self.camera_x = 0

        self.platforms = []
        self.coins = []
        self.ladders = []
        self.portals = []
        self.patrol_enemies = []
        self.chase_enemies = []
        self.bullets = []
        self.ammo_pickups = []

        self.current_level = 0
        self.game_state = GameState.LOADING
        self.transition_frame = 0
        self.transition_phase = 0
        self.pending_level = 0
        self.pending_spawn = (PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.is_same_level_transition = False
        self.level_config = None
        self.loading_progress = 0.0

        self.player = Player(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.font = get_chinese_font(26)
        self.big_font = get_chinese_font(52)
        self.title_font = get_chinese_font(72)

        self._sky_surface = None
        self._stars_surface = None
        self.clouds = []
        self.bg_mountains = []

        self.audio = AudioManager()
        self.volume_panel = VolumePanel(self.audio)
        self.volume_panel.on_bgm_change = self._on_bgm_volume_change
        self.volume_panel.on_sfx_change = self._on_sfx_volume_change

        self.rng = random.Random()

        self.state_manager = StateManager(self)
        self.level_loader = LevelLoader(self)
        self.background_manager = BackgroundManager(self)
        self.hud_manager = HUDManager(self)
        self.particle_manager = ParticleManager(self)
        self.combat_manager = CombatManager(self)

        self._bind_player_audio_callbacks()

        self.menu_manager = MenuManager(self)
        self.game_state = GameState.MAIN_MENU

        self._load_level(0, PLAYER_SPAWN_X, PLAYER_SPAWN_Y, immediate=True)

    def _bind_player_audio_callbacks(self):
        """为玩家对象绑定音频事件回调。"""
        self.player.on_jump = lambda: self.audio.play_sfx(AudioManager.SFX_JUMP)
        self.player.on_double_jump = lambda: self.audio.play_sfx(
            AudioManager.SFX_DOUBLE_JUMP
        )
        self.player.on_land = lambda: self.audio.play_sfx(AudioManager.SFX_LAND)
        self.player.on_death = lambda: self.audio.play_sfx(AudioManager.SFX_DEATH)
        self.player.on_melee_swing = lambda: self.audio.play_sfx(AudioManager.SFX_MELEE_SWING)
        self.player.on_ranged_shot = lambda: self.audio.play_sfx(AudioManager.SFX_RANGED_SHOT)
        self.player.on_reload = lambda: self.audio.play_sfx(AudioManager.SFX_RELOAD)
        self.player.on_ammo_pickup = lambda: self.audio.play_sfx(AudioManager.SFX_AMMO_PICKUP)

    def _on_bgm_volume_change(self, volume):
        """背景音乐音量滑块变化回调。"""
        self.audio.set_bgm_volume(volume)

    def _on_sfx_volume_change(self, volume):
        """音效音量滑块变化回调。"""
        self.audio.set_sfx_volume(volume)

    def _build_sky_surface(self, sky_top, sky_bottom):
        """预渲染天空渐变 Surface。"""
        return self.background_manager.build_sky_surface(sky_top, sky_bottom)

    def _build_stars_surface(self, star_count, star_seed):
        """预渲染星空 Surface。"""
        return self.background_manager.build_stars_surface(star_count, star_seed)

    def _build_clouds(self, cloud_color, alpha_inner, alpha_outer):
        """构建并预渲染云朵数据。"""
        return self.background_manager.build_clouds(cloud_color, alpha_inner, alpha_outer)

    def _build_mountains(self):
        """构建背景山脉数据。"""
        return self.background_manager.build_mountains()

    def _build_level(self, level_config):
        """根据关卡配置构建关卡数据。"""
        self.level_loader.build_level(level_config)

    def _load_level(self, level_id, spawn_x, spawn_y, immediate=False):
        """加载指定关卡，重置所有游戏数据。"""
        self.level_loader.load_level(level_id, spawn_x, spawn_y, immediate)

    def _start_transition(self, target_level, target_x, target_y):
        """启动关卡切换过渡流程。"""
        self.menu_manager.set_state(GameState.TRANSITIONING)
        self.game_state = GameState.TRANSITIONING
        self.transition_phase = 0
        self.transition_frame = 0

        if target_level == -1:
            self.is_same_level_transition = True
            self.pending_level = self.current_level
        else:
            self.is_same_level_transition = False
            self.pending_level = target_level % len(LEVEL_BUILDERS)
        self.pending_spawn = (target_x, target_y)
        self.state_manager.is_same_level = self.is_same_level_transition

        self._spawn_particles(
            self.player.x + self.player.width / 2,
            self.player.y + self.player.height / 2,
            count=20,
            colors=PORTAL_PARTICLE_COLORS,
            spread=5,
            life=30,
            size=5,
        )

    def _update_transition(self):
        """更新过渡动画状态机。"""
        result = self.state_manager.update_transition()
        if result == "start_loading":
            spawn_x, spawn_y = self.pending_spawn
            if self.is_same_level_transition:
                self._teleport_within_level(spawn_x, spawn_y)
            else:
                self._load_level(self.pending_level, spawn_x, spawn_y, immediate=False)

    def _teleport_within_level(self, target_x, target_y):
        """同关卡内传送，只移动玩家位置，保留所有物品和怪物状态。"""
        self.player.x = target_x
        self.player.y = target_y
        self.player.vx = 0
        self.player.vy = 0
        self.player.climbing = False
        self.player.current_ladder = None
        self.player.jump_count = 0
        self.player.on_ground = False

        self.camera_x = 0
        target_camera_x = target_x - SCREEN_WIDTH / CAMERA_TARGET_RATIO
        self.camera_x = max(0, min(target_camera_x, LEVEL_WIDTH - SCREEN_WIDTH))

        portal = None
        for p in self.portals:
            if abs(p.x + p.width / 2 - target_x) < 50 and abs(p.y + p.height / 2 - target_y) < 50:
                portal = p
                break
        if portal is not None and portal.cooldown <= 0:
            portal.cooldown = PORTAL_COOLDOWN_FRAMES

    def _spawn_particles(
        self, x, y, count, colors=PARTICLE_COLORS,
        spread=3, life=20, size=3
    ):
        """在指定位置生成一批粒子。"""
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread * 1.5, -0.5)
            color = random.choice(colors)
            l = random.randint(life // 2, life)
            s = random.randint(1, size)
            self.particles.append(Particle(x, y, vx, vy, color, l, s))

    def _update_camera(self):
        """更新相机位置，使用 LERP 平滑跟随。"""
        target_x = self.player.x - SCREEN_WIDTH / CAMERA_TARGET_RATIO
        self.camera_x += (target_x - self.camera_x) * CAMERA_LERP
        self.camera_x = max(0, min(self.camera_x, LEVEL_WIDTH - SCREEN_WIDTH))

    def _draw_sky(self):
        """绘制预渲染的天空渐变背景。"""
        self.background_manager.draw_sky(self.screen, self._sky_surface)

    def _draw_stars(self):
        """绘制预渲染的星空背景，附带闪烁动画。"""
        self.background_manager.draw_stars(self.screen, self._stars_surface, self.tick)

    def _draw_sun(self):
        """绘制太阳，含光晕和射线效果。"""
        self.background_manager.draw_sun(self.screen, self.level_config, self.tick)

    def _draw_moon(self):
        """绘制月亮，含光晕和月牙效果。"""
        self.background_manager.draw_moon(self.screen, self.level_config)

    def _draw_mountains(self):
        """绘制远景山脉，固定在屏幕空间不随相机移动。"""
        self.background_manager.draw_mountains(self.screen, self.bg_mountains, self.level_config)

    def _draw_clouds(self):
        """绘制云朵，固定在屏幕空间缓慢飘移，不随相机移动。"""
        self.background_manager.draw_clouds(self.screen, self.clouds)

    def _check_coins(self):
        """检测玩家与金币的碰撞。"""
        player_rect = self.player.get_rect()
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                coin.collect_anim = 15
                self.score += COIN_COLLECT_SCORE
                self.audio.play_sfx(AudioManager.SFX_COIN)
                self._spawn_particles(
                    coin.x,
                    coin.y,
                    8,
                    colors=[COIN_COLOR, COIN_DARK, (255, 255, 200)],
                    spread=4,
                    life=15,
                    size=4,
                )

    def _check_portals(self):
        """检测玩家与传送门的交互。"""
        player_rect = self.player.get_rect()
        for portal in self.portals:
            if portal.can_trigger(player_rect, self.score):
                portal.trigger()
                self.audio.play_sfx(AudioManager.SFX_PORTAL)
                self._start_transition(
                    portal.target_level,
                    portal.target_x,
                    portal.target_y,
                )
                px = portal.x + portal.width / 2
                py = portal.y + portal.height / 2
                self._spawn_particles(
                    px, py,
                    count=15,
                    colors=PORTAL_PARTICLE_COLORS,
                    spread=4,
                    life=25,
                    size=4,
                )
                break

    def _check_enemy_collisions(self):
        """检测玩家与敌人的碰撞。"""
        player_rect = self.player.get_rect()

        for enemy in self.patrol_enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self._player_hit_by_enemy()
                return

        for enemy in self.chase_enemies:
            if player_rect.colliderect(enemy.get_rect()):
                self._player_hit_by_enemy()
                return

    def _player_hit_by_enemy(self):
        """玩家被敌人击中时的处理。"""
        self.player.died = True
        if self.player.on_death:
            self.player.on_death()
        self.player.x = self.player.start_x
        self.player.y = 0
        self.player.vx = 0
        self.player.vy = 0
        self.player.climbing = False
        self.player.current_ladder = None
        self.player.jump_count = 0

        final_score = self.score
        self.score = 0
        for coin in self.coins:
            coin.collected = False
            coin.collect_anim = 0
        self.player.died = False
        self.menu_manager.trigger_game_over(final_score)

    def _handle_melee_input(self):
        """处理近战攻击输入。"""
        if self.player.start_melee():
            direction = 1 if self.player.facing_right else -1
            self._spawn_particles(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height / 2,
                count=6,
                colors=[(255, 230, 150), (255, 200, 100), (255, 255, 200)],
                spread=5,
                life=10,
                size=4,
            )
            self._spawn_particles(
                self.player.x + self.player.width / 2 + direction * 20,
                self.player.y + self.player.height / 2 - 5,
                count=4,
                colors=[(220, 230, 255), (255, 255, 255)],
                spread=6,
                life=6,
                size=2,
            )

    def _handle_ranged_input(self):
        """处理远程攻击输入。"""
        bullet = self.player.start_ranged_shot()
        if bullet is not None:
            self.bullets.append(bullet)
            direction = 1 if self.player.facing_right else -1
            gun_angle = -0.15 if self.player.facing_right else math.pi + 0.15
            cos_a = math.cos(gun_angle)
            sin_a = math.sin(gun_angle)
            muzzle_x = self.player.x + self.player.width / 2 + direction * 22 + cos_a * 32
            muzzle_y = self.player.y + self.player.height * 0.5 + sin_a * 32
            self._spawn_particles(
                muzzle_x,
                muzzle_y,
                count=8,
                colors=[(255, 200, 50), (255, 150, 0), (255, 255, 200)],
                spread=5,
                life=8,
                size=3,
            )
            self._spawn_particles(
                muzzle_x,
                muzzle_y,
                count=6,
                colors=[(255, 255, 255), (200, 200, 200)],
                spread=6,
                life=6,
                size=2,
            )

    def _update_bullets(self):
        """更新子弹状态。"""
        for bullet in self.bullets:
            bullet.update(self.platforms)
        self.bullets = [b for b in self.bullets if b.alive]

    def _check_combat_hits(self):
        """检测战斗命中。"""
        from config import (
            MELEE_DAMAGE, MELEE_DURATION_FRAMES, MELEE_HIT_FRAME,
            COMBAT_HIT_PARTICLE_COLORS, ENEMY_PARTICLE_COLORS,
            RANGED_HIT_PARTICLE_COLORS,
        )

        if self.player.melee_active and not self.player.melee_hit_done:
            if self.player.melee_timer <= MELEE_DURATION_FRAMES - MELEE_HIT_FRAME:
                hitbox = self.player.get_melee_hitbox()
                if hitbox is not None:
                    direction = 1 if self.player.facing_right else -1
                    for enemy in self.patrol_enemies[:]:
                        if hitbox.colliderect(enemy.get_rect()):
                            killed = enemy.take_damage(MELEE_DAMAGE, direction)
                            self.audio.play_sfx(AudioManager.SFX_ENEMY_HIT)
                            self._spawn_particles(
                                enemy.x + enemy.width / 2,
                                enemy.y + enemy.height / 2,
                                count=10,
                                colors=COMBAT_HIT_PARTICLE_COLORS,
                                spread=6,
                                life=14,
                                size=5,
                            )
                            self._spawn_particles(
                                enemy.x + enemy.width / 2,
                                enemy.y + enemy.height / 2,
                                count=4,
                                colors=[(255, 255, 255), (220, 230, 255)],
                                spread=3,
                                life=6,
                                size=3,
                            )
                            if killed:
                                self._spawn_particles(
                                    enemy.x + enemy.width / 2,
                                    enemy.y + enemy.height / 2,
                                    count=20,
                                    colors=ENEMY_PARTICLE_COLORS,
                                    spread=8,
                                    life=25,
                                    size=6,
                                )
                                self._spawn_particles(
                                    enemy.x + enemy.width / 2,
                                    enemy.y + enemy.height / 2,
                                    count=6,
                                    colors=[(255, 255, 200), (255, 255, 255)],
                                    spread=4,
                                    life=10,
                                    size=3,
                                )
                                self.patrol_enemies.remove(enemy)
                                self.score += 20
                    for enemy in self.chase_enemies[:]:
                        if hitbox.colliderect(enemy.get_rect()):
                            killed = enemy.take_damage(MELEE_DAMAGE, direction)
                            self.audio.play_sfx(AudioManager.SFX_ENEMY_HIT)
                            self._spawn_particles(
                                enemy.x + enemy.width / 2,
                                enemy.y + enemy.height / 2,
                                count=10,
                                colors=COMBAT_HIT_PARTICLE_COLORS,
                                spread=6,
                                life=14,
                                size=5,
                            )
                            self._spawn_particles(
                                enemy.x + enemy.width / 2,
                                enemy.y + enemy.height / 2,
                                count=4,
                                colors=[(255, 255, 255), (220, 230, 255)],
                                spread=3,
                                life=6,
                                size=3,
                            )
                            if killed:
                                self._spawn_particles(
                                    enemy.x + enemy.width / 2,
                                    enemy.y + enemy.height / 2,
                                    count=20,
                                    colors=ENEMY_PARTICLE_COLORS,
                                    spread=8,
                                    life=25,
                                    size=6,
                                )
                                self._spawn_particles(
                                    enemy.x + enemy.width / 2,
                                    enemy.y + enemy.height / 2,
                                    count=6,
                                    colors=[(255, 255, 200), (255, 255, 255)],
                                    spread=4,
                                    life=10,
                                    size=3,
                                )
                                self.chase_enemies.remove(enemy)
                                self.score += 20
                    self.player.melee_hit_done = True

        for bullet in self.bullets[:]:
            if not bullet.alive:
                continue
            bullet_rect = bullet.get_rect()
            direction = 1 if bullet.vx > 0 else -1
            for enemy in self.patrol_enemies[:]:
                if bullet_rect.colliderect(enemy.get_rect()):
                    killed = enemy.take_damage(bullet.damage, direction)
                    bullet.alive = False
                    self.audio.play_sfx(AudioManager.SFX_HIT_IMPACT)
                    self._spawn_particles(
                        bullet.x, bullet.y,
                        count=8,
                        colors=RANGED_HIT_PARTICLE_COLORS,
                        spread=5,
                        life=12,
                        size=4,
                    )
                    self._spawn_particles(
                        bullet.x, bullet.y,
                        count=3,
                        colors=[(255, 255, 200), (255, 200, 80)],
                        spread=2,
                        life=5,
                        size=2,
                    )
                    if killed:
                        self._spawn_particles(
                            enemy.x + enemy.width / 2,
                            enemy.y + enemy.height / 2,
                            count=20,
                            colors=ENEMY_PARTICLE_COLORS,
                            spread=8,
                            life=25,
                            size=6,
                        )
                        self.patrol_enemies.remove(enemy)
                        self.score += 20
                    break
            if not bullet.alive:
                continue
            for enemy in self.chase_enemies[:]:
                if bullet_rect.colliderect(enemy.get_rect()):
                    killed = enemy.take_damage(bullet.damage, direction)
                    bullet.alive = False
                    self.audio.play_sfx(AudioManager.SFX_HIT_IMPACT)
                    self._spawn_particles(
                        bullet.x, bullet.y,
                        count=8,
                        colors=RANGED_HIT_PARTICLE_COLORS,
                        spread=5,
                        life=12,
                        size=4,
                    )
                    self._spawn_particles(
                        bullet.x, bullet.y,
                        count=3,
                        colors=[(255, 255, 200), (255, 200, 80)],
                        spread=2,
                        life=5,
                        size=2,
                    )
                    if killed:
                        self._spawn_particles(
                            enemy.x + enemy.width / 2,
                            enemy.y + enemy.height / 2,
                            count=20,
                            colors=ENEMY_PARTICLE_COLORS,
                            spread=8,
                            life=25,
                            size=6,
                        )
                        self.chase_enemies.remove(enemy)
                        self.score += 20
                    break

    def _check_ammo_pickups(self):
        """检测弹药拾取。"""
        player_rect = self.player.get_rect()
        remaining = []
        for ammo in self.ammo_pickups:
            if player_rect.colliderect(ammo.get_rect()):
                self.player.ammo = min(
                    self.player.ammo + ammo.amount,
                    self.player.ammo_max,
                )
                if self.player.on_ammo_pickup:
                    self.player.on_ammo_pickup()
                self._spawn_particles(
                    ammo.x,
                    ammo.y,
                    count=10,
                    colors=[(255, 215, 0), (255, 255, 150), (255, 200, 50)],
                    spread=4,
                    life=20,
                    size=3,
                )
            else:
                remaining.append(ammo)
        self.ammo_pickups = remaining

    def _draw_hud(self):
        """绘制抬头显示（HUD）。"""
        SHADOW_OFFSET = 3

        coin_text = self.font.render(f"金币: {self.score}", True, WHITE)
        shadow_text = self.font.render(f"金币: {self.score}", True, BLACK)
        self.screen.blit(shadow_text, (20 + SHADOW_OFFSET, 15 + SHADOW_OFFSET))
        self.screen.blit(coin_text, (20, 15))

        if self.level_config:
            level_num = self.current_level + 1
            level_text = self.font.render(
                f"第 {level_num}/{TOTAL_LEVELS} 关: {self.level_config.name}",
                True, WHITE,
            )
            level_shadow = self.font.render(
                f"第 {level_num}/{TOTAL_LEVELS} 关: {self.level_config.name}",
                True, BLACK,
            )
            text_x = (SCREEN_WIDTH - level_text.get_width()) // 2
            self.screen.blit(level_shadow, (text_x + SHADOW_OFFSET, 15 + SHADOW_OFFSET))
            self.screen.blit(level_text, (text_x, 15))

        hint = self.font.render(
            "移动:方向键/WASD  跳跃:空格  攀爬:上下  J:近战  K:射击  R:换弹",
            True, (50, 50, 80),
        )
        self.screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 15, 15))

        ammo_color = (255, 255, 100) if self.player.ammo > 5 else (255, 80, 80)
        if self.player.reloading:
            ammo_color = (150, 150, 150)
        ammo_text = self.font.render(
            f"弹药: {self.player.ammo}/{RANGED_AMMO_MAX}",
            True, ammo_color,
        )
        ammo_shadow = self.font.render(
            f"弹药: {self.player.ammo}/{RANGED_AMMO_MAX}",
            True, BLACK,
        )
        self.screen.blit(ammo_shadow, (20 + SHADOW_OFFSET, 40 + SHADOW_OFFSET))
        self.screen.blit(ammo_text, (20, 40))

        audio_hint = self.font.render(
            "[V] 音频设置",
            True, (80, 80, 120) if not self.volume_panel.visible else (100, 200, 255),
        )
        self.screen.blit(audio_hint, (SCREEN_WIDTH - audio_hint.get_width() - 15, 40))

    def _draw_transition(self):
        """绘制过渡动画遮罩层（淡出/淡入）。"""
        half_duration = TRANSITION_DURATION_FRAMES // 2
        if self.transition_phase == 0:
            alpha = int(255 * self.transition_frame / half_duration)
        elif self.transition_phase == 2:
            alpha = int(255 * (1 - self.transition_frame / half_duration))
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*TRANSITION_COLOR, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_loading_screen(self):
        """绘制加载界面，含关卡名称、描述和进度条。"""
        self.state_manager.draw_loading_screen(
            self.screen, self.title_font, self.big_font, self.font
        )

    def _build_healthcheck_keys(self):
        """生成健康检查模拟按键。"""
        if self.tick % 180 < 90:
            keys = {pygame.K_RIGHT: True, pygame.K_SPACE: True}
        else:
            keys = {pygame.K_LEFT: True, pygame.K_SPACE: True}
        return keys

    def _handle_events(self):
        """处理 pygame 事件队列。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.menu_manager.is_menu_active():
                if self.menu_manager.handle_event(event):
                    continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == GameState.PLAYING:
                        self.menu_manager.set_state(GameState.PAUSED)
                    elif self.game_state == GameState.PAUSED:
                        self.menu_manager.set_state(GameState.PLAYING)
                    else:
                        return False
                if event.key == SHOW_VOLUME_PANEL_KEY and self.game_state == GameState.PLAYING:
                    self.volume_panel.toggle()

                if self.game_state == GameState.PLAYING:
                    key_char = event.unicode.lower() if event.unicode else ''
                    if event.key == pygame.K_j or key_char == 'j':
                        self._handle_melee_input()
                    elif event.key == pygame.K_k or key_char == 'k':
                        self._handle_ranged_input()
                    elif event.key == pygame.K_r or key_char == 'r':
                        self.player.start_reload()

            if self.game_state == GameState.PLAYING:
                self.volume_panel.handle_event(event)
        return True

    def _update_world(self, keys):
        """更新游戏世界状态（逻辑帧）。"""
        old_on_ground = self.player.on_ground
        self.player.update(keys, self.platforms, self.ladders)

        if self.player.died:
            final_score = self.score
            self.score = 0
            for coin in self.coins:
                coin.collected = False
                coin.collect_anim = 0
            self.player.died = False
            self.menu_manager.trigger_game_over(final_score)

        if self.player.on_ground and not old_on_ground and self.player.vy == 0:
            self._spawn_particles(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height,
                count=6,
                spread=3,
                life=15,
                size=3,
            )

        if (
            self.player.on_ground
            and abs(self.player.vx) > 3
            and self.tick % 4 == 0
        ):
            self._spawn_particles(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height,
                count=2,
                colors=DUST_PARTICLE_COLORS,
                spread=2,
                life=10,
                size=2,
            )

        for enemy in self.patrol_enemies:
            enemy.update(self.platforms, self.player)

        for enemy in self.chase_enemies:
            enemy.update(self.player)

        self._check_coins()

        for coin in self.coins:
            coin.update()

        self._check_portals()

        for portal in self.portals:
            portal.update(self.score)

        self._check_enemy_collisions()

        self._update_bullets()
        self._check_combat_hits()
        self._check_ammo_pickups()

        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        self._update_camera()

    def _render(self):
        """
        渲染整个场景（渲染帧）。

        绘制顺序（从远到近）:
        1. 天空渐变（最底层，屏幕固定）
        2. 星空（屏幕固定，仅夜光关卡）
        3. 太阳/月亮（屏幕固定）
        4. 远景山脉（屏幕固定）
        5. 云朵（屏幕固定缓慢飘移）
        6. 所有平台（随相机滚动）
        7. 所有梯子（随相机滚动）
        8. 所有金币（随相机滚动）
        9. 所有传送门（随相机滚动）
        10. 粒子特效（随相机滚动）
        11. 玩家（随相机滚动）
        12. HUD（最顶层，屏幕空间）

        特殊状态:
        - LOADING: 绘制加载界面覆盖层
        - TRANSITIONING: 绘制过渡遮罩
        - 菜单状态: 绘制菜单覆盖层
        """
        self._draw_sky()
        self._draw_stars()
        self._draw_sun()
        self._draw_moon()
        self._draw_mountains()
        self._draw_clouds()

        for plat in self.platforms:
            plat.draw(self.screen, self.camera_x, self.level_config)

        for ladder in self.ladders:
            ladder.draw(self.screen, self.camera_x)

        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.tick)

        for portal in self.portals:
            portal.draw(self.screen, self.camera_x, self.tick)

        for enemy in self.patrol_enemies:
            enemy.draw(self.screen, self.camera_x)

        for enemy in self.chase_enemies:
            enemy.draw(self.screen, self.camera_x)

        for ammo in self.ammo_pickups:
            ammo.draw(self.screen, self.camera_x, self.tick)

        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera_x)

        for p in self.particles:
            p.draw(self.screen, self.camera_x)

        self.player.draw(self.screen, self.camera_x)

        self._draw_hud()

        if self.game_state == GameState.LOADING:
            self._draw_loading_screen()
        elif self.game_state == GameState.TRANSITIONING:
            self._draw_transition()

        if self.game_state == GameState.PLAYING:
            self.volume_panel.draw(self.screen, self.big_font, self.font)

        if self.menu_manager.is_menu_active():
            self.menu_manager.draw(self.screen, self.big_font, self.font, self.font)

    def run(self):
        """游戏主循环入口。"""
        running = True
        while running:
            self.tick += 1

            if HEALTHCHECK and self.tick > HEALTHCHECK_MAX_FRAMES:
                pygame.quit()
                sys.exit(0)

            current_state = self.menu_manager.current_state
            self.game_state = current_state

            running = self._handle_events()
            if not running:
                break

            keys = pygame.key.get_pressed()

            if HEADLESS and HEALTHCHECK:
                keys = self._build_healthcheck_keys()

            if current_state == GameState.PLAYING:
                self._update_world(keys)
            elif current_state == GameState.PAUSED:
                pass
            elif current_state in (GameState.TRANSITIONING, GameState.LOADING):
                self._update_transition()
            else:
                self.menu_manager.update()

            self._render()

            if not HEADLESS:
                pygame.display.flip()
                self.clock.tick(FPS)
            else:
                self.clock.tick(FPS)
