# -*- coding: utf-8 -*-
"""
core/level_loader.py - 关卡加载模块

负责关卡数据的构建和加载。
"""

from config import (
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
)

from entities import Platform, Coin, Ladder, Portal, PatrolEnemy, ChaseEnemy, AmmoPickup, Player, FragilePlatform
from levels import get_level_config


class LevelLoader:
    """
    关卡加载器。

    负责:
    - 根据关卡配置构建关卡数据
    - 加载关卡资源（天空、星星、云朵、山脉）
    - 重置玩家和游戏状态
    """

    def __init__(self, game):
        self.game = game

    def build_level(self, level_config):
        """
        根据关卡配置构建关卡数据。

        Args:
            level_config: LevelConfig 关卡配置对象
        """
        self.game.platforms = []
        self.game.fragile_platforms = []
        self.game.coins = []
        self.game.ladders = []
        self.game.portals = []
        self.game.patrol_enemies = []
        self.game.chase_enemies = []
        self.game.bullets = []
        self.game.ammo_pickups = []

        for x, y, w, h in level_config.ground_specs:
            self.game.platforms.append(Platform(x, y, w, h, is_ground=True))

        for x, y, w, h in level_config.floating_specs:
            self.game.platforms.append(Platform(x, y, w, h))

        for x, y, w, h in level_config.fragile_platform_specs:
            fp = FragilePlatform(x, y, w, h)
            fp.spawn_particles_cb = self.game._spawn_fragile_platform_particles
            self.game.fragile_platforms.append(fp)
            self.game.platforms.append(fp)

        for x, y in level_config.coin_positions:
            self.game.coins.append(Coin(x, y))

        for x, y, h in level_config.ladder_specs:
            self.game.ladders.append(Ladder(x, y, h))

        for spec in level_config.portal_specs:
            if len(spec) == 6:
                x, y, target_level, tx, ty, required_coins = spec
            else:
                x, y, target_level, tx, ty = spec
                required_coins = 0
            self.game.portals.append(Portal(x, y, target_level, tx, ty, required_coins))

        for path_points, loop_mode in level_config.patrol_enemy_specs:
            self.game.patrol_enemies.append(PatrolEnemy(path_points, loop_mode))

        for x, y in level_config.chase_enemy_specs:
            self.game.chase_enemies.append(ChaseEnemy(x, y))

        for x, y in level_config.ammo_pickup_specs:
            self.game.ammo_pickups.append(AmmoPickup(x, y))

    def load_level(self, level_id, spawn_x, spawn_y, immediate=False):
        """
        加载指定关卡，重置所有游戏数据。

        Args:
            level_id: 目标关卡编号
            spawn_x, spawn_y: 玩家出生坐标
            immediate: 是否立即加载（跳过过渡动画）
        """
        from menus import GameState

        self.game.level_config = get_level_config(level_id)
        self.game.current_level = level_id
        self.build_level(self.game.level_config)

        self.game.player = Player(spawn_x, spawn_y)
        self.game.player.start_x = spawn_x
        self.game.player.start_y = spawn_y
        self.game._bind_player_audio_callbacks()

        self.game.audio.play_bgm(f"level_{level_id % 3}")

        self.game._sky_surface = self.game.background_manager.build_sky_surface(
            self.game.level_config.sky_top, self.game.level_config.sky_bottom
        )
        self.game._stars_surface = self.game.background_manager.build_stars_surface(
            self.game.level_config.star_count, self.game.level_config.star_seed
        ) if self.game.level_config.has_stars else None
        self.game.clouds = self.game.background_manager.build_clouds(
            self.game.level_config.cloud_color,
            self.game.level_config.cloud_alpha_inner,
            self.game.level_config.cloud_alpha_outer,
        )
        self.game.bg_mountains = self.game.background_manager.build_mountains()

        self.game.camera_x = 0
        self.game.particles = []

        if immediate:
            self.game.game_state = GameState.PLAYING
            self.game.state_manager.transition_phase = 0
            self.game.state_manager.transition_frame = 0
        else:
            self.game.game_state = GameState.TRANSITIONING
            self.game.state_manager.transition_phase = 2
            self.game.state_manager.transition_frame = 0
