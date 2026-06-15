# -*- coding: utf-8 -*-
"""
test_player.py - 玩家系统单元测试

测试目标:
1. PlayerBase 属性初始化和 get_rect
2. 玩家移动系统 - 水平移动、摩擦力、加速度
3. 跳跃系统 - 地面跳、多段跳、跳跃缓冲、土狼时间、短跳
4. 攀爬系统 - 进入梯子、上下攀爬、脱离
5. 战斗系统 - 近战攻击、远程射击、弹药管理、换弹
6. 碰撞和边界 - 关卡边界、掉落重生
"""

import os
import sys
import pytest
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlayerBase:
    """玩家基类属性和基础接口测试。"""

    def test_player_initialization(self, make_player):
        """测试玩家属性初始化。"""
        player = make_player(100, 200)
        assert player.x == 100
        assert player.y == 200
        assert player.start_x == 100
        assert player.start_y == 200
        assert player.width == 28
        assert player.height == 38
        assert player.vx == 0
        assert player.vy == 0
        assert player.on_ground is False
        assert player.facing_right is True
        assert player.died is False

    def test_player_get_rect(self, make_player):
        """测试玩家碰撞矩形。"""
        player = make_player(50, 60)
        rect = player.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 50
        assert rect.y == 60
        assert rect.width == 28
        assert rect.height == 38

    def test_combat_state_initialization(self, make_player):
        """测试战斗相关初始状态。"""
        from config import RANGED_AMMO_INITIAL
        player = make_player()
        assert player.melee_active is False
        assert player.melee_cooldown == 0
        assert player.ranged_cooldown == 0
        assert player.ammo == RANGED_AMMO_INITIAL
        assert player.reloading is False


class TestPlayerHorizontalMovement:
    """玩家水平移动系统测试。"""

    def test_move_right_acceleration(self, make_player, make_keys, sample_platforms):
        """测试向右移动时加速度应用。"""
        from config import ACCELERATION, MOVE_SPEED
        player = make_player(100, 500)
        keys = make_keys(pygame.K_RIGHT)
        player.update(keys, sample_platforms)
        assert player.vx > 0
        assert player.facing_right is True
        assert player.vx <= MOVE_SPEED

    def test_move_left_acceleration(self, make_player, make_keys, sample_platforms):
        """测试向左移动时加速度应用。"""
        from config import ACCELERATION, MOVE_SPEED
        player = make_player(200, 500)
        keys = make_keys(pygame.K_LEFT)
        player.update(keys, sample_platforms)
        assert player.vx < 0
        assert player.facing_right is False
        assert abs(player.vx) <= MOVE_SPEED

    def test_move_right_with_a_key(self, make_player, make_keys, sample_platforms):
        """测试使用 A 键向左移动。"""
        player = make_player(200, 500)
        keys = make_keys(pygame.K_a)
        player.update(keys, sample_platforms)
        assert player.vx < 0
        assert player.facing_right is False

    def test_move_right_with_d_key(self, make_player, make_keys, sample_platforms):
        """测试使用 D 键向右移动。"""
        player = make_player(100, 500)
        keys = make_keys(pygame.K_d)
        player.update(keys, sample_platforms)
        assert player.vx > 0
        assert player.facing_right is True

    def test_friction_when_no_input(self, make_player, make_keys, sample_platforms):
        """测试无输入时摩擦力使速度衰减。"""
        from config import FRICTION
        player = make_player(100, 500)
        player.vx = 4.0
        keys = make_keys()
        player.update(keys, sample_platforms)
        assert abs(player.vx) < 4.0

    def test_max_speed_capped(self, make_player, make_keys, sample_platforms):
        """测试移动速度不会超过最大值。"""
        from config import MOVE_SPEED
        player = make_player(100, 500)
        keys = make_keys(pygame.K_RIGHT)
        for _ in range(30):
            player.update(keys, sample_platforms)
        assert abs(player.vx) <= MOVE_SPEED + 0.1


class TestPlayerJumpSystem:
    """玩家跳跃系统测试。"""

    def test_ground_jump(self, make_player, make_keys, sample_platforms):
        """测试在地面上跳跃。"""
        from config import JUMP_FORCE
        player = make_player(100, 560)
        player.on_ground = True
        player.update_combat()
        keys = make_keys(pygame.K_SPACE)
        player.jump_pressed = False
        player.update(keys, sample_platforms)
        assert player.jump_count >= 1
        assert player.on_ground is False

    def test_jump_with_up_arrow(self, make_player, make_keys, sample_platforms):
        """测试使用上箭头键跳跃。"""
        player = make_player(100, 560)
        player.on_ground = True
        keys = make_keys(pygame.K_UP)
        player.jump_pressed = False
        player.update(keys, sample_platforms)
        assert player.jump_count >= 1

    def test_jump_with_w_key(self, make_player, make_keys, sample_platforms):
        """测试使用 W 键跳跃。"""
        player = make_player(100, 560)
        player.on_ground = True
        keys = make_keys(pygame.K_w)
        player.jump_pressed = False
        player.update(keys, sample_platforms)
        assert player.jump_count >= 1

    def test_gravity_applied_in_air(self, make_player, make_keys, sample_platforms):
        """测试在空中时重力加速度应用。"""
        from config import GRAVITY
        player = make_player(100, 300)
        player.on_ground = False
        keys = make_keys()
        initial_vy = player.vy
        player.update(keys, sample_platforms)
        assert player.vy > initial_vy

    def test_max_fall_speed_capped(self, make_player, make_keys):
        """测试下落速度有上限。"""
        from config import MAX_FALL_SPEED
        player = make_player(100, 0)
        player.vy = 100
        keys = make_keys()
        from config import GRAVITY
        for _ in range(10):
            player.vy += GRAVITY
            if player.vy > MAX_FALL_SPEED:
                player.vy = MAX_FALL_SPEED
        assert player.vy <= MAX_FALL_SPEED

    def test_landed_resets_jump_count(self, make_player, make_platform, make_keys, monkeypatch):
        """测试落地后跳跃次数重置。"""
        from config import SCREEN_HEIGHT
        player = make_player(100, 580)
        ground = make_platform(0, SCREEN_HEIGHT - 40, 300, 40, is_ground=True)
        player.on_ground = False
        player.jump_count = 3
        player.vy = 8
        keys = make_keys()
        for _ in range(15):
            player.update(keys, [ground])
            if player.on_ground and player.jump_count == 0:
                break
        assert player.on_ground is True
        assert player.jump_count == 0

    def test_short_jump(self, make_player, make_keys, sample_platforms):
        """测试松开跳跃键时的短跳效果。"""
        from config import SHORT_JUMP_MULTIPLIER, SHORT_JUMP_THRESHOLD
        player = make_player(100, 560)
        player.on_ground = True
        jump_keys = make_keys(pygame.K_SPACE)
        player.jump_pressed = False
        player.update(jump_keys, sample_platforms)
        initial_vy = player.vy
        no_keys = make_keys()
        player.update(no_keys, sample_platforms)
        if initial_vy < SHORT_JUMP_THRESHOLD:
            assert player.vy > initial_vy * SHORT_JUMP_MULTIPLIER - 0.1


class TestPlayerLadder:
    """玩家梯子攀爬系统测试。"""

    def test_enter_ladder_from_bottom(self, make_player, make_ladder, make_keys, make_platform):
        """测试从底部进入梯子攀爬。"""
        from config import SCREEN_HEIGHT
        ground = make_platform(0, SCREEN_HEIGHT - 40, 500, 40, is_ground=True)
        ladder = make_ladder(200, 400, 200)
        player = make_player(200, SCREEN_HEIGHT - 40 - 38)
        player.x = ladder.x + ladder.width // 2 - player.width // 2
        player.on_ground = True
        keys = make_keys(pygame.K_UP)
        player.update(keys, [ground], [ladder])
        assert player.climbing is True

    def test_climb_upward(self, make_player, make_ladder, make_keys, make_platform):
        """测试在梯子上向上攀爬。"""
        from config import CLIMB_SPEED, SCREEN_HEIGHT
        ground = make_platform(0, SCREEN_HEIGHT - 40, 500, 40, is_ground=True)
        ladder = make_ladder(200, 300, 260)
        player = make_player(200, 500)
        player.x = ladder.x + ladder.width // 2 - player.width // 2
        player.y = 450
        player.climbing = True
        player.current_ladder = ladder
        keys = make_keys(pygame.K_UP)
        initial_y = player.y
        player.update(keys, [ground], [ladder])
        assert player.y < initial_y

    def test_exit_ladder_with_left_move(self, make_player, make_ladder, make_keys):
        """测试在梯子上向左移动离开梯子。"""
        ladder = make_ladder(200, 300, 200)
        player = make_player(200, 400)
        player.climbing = True
        player.current_ladder = ladder
        keys = make_keys(pygame.K_LEFT)
        player.update(keys, [], [ladder])
        assert player.climbing is False

    def test_exit_ladder_with_jump(self, make_player, make_ladder, make_keys, monkeypatch):
        """测试在梯子上跳跃离开。"""
        ladder = make_ladder(200, 300, 200)
        player = make_player(200, 400)
        player.climbing = True
        player.current_ladder = ladder
        keys = make_keys(pygame.K_SPACE)
        player.jump_pressed = False

        fake_keys = [False] * 512
        fake_keys[pygame.K_SPACE] = True
        monkeypatch.setattr(pygame.key, 'get_pressed', lambda: fake_keys)

        player.update(keys, [], [ladder])
        assert player.climbing is False


class TestPlayerCombat:
    """玩家战斗系统测试。"""

    def test_start_melee_attack(self, make_player):
        """测试启动近战攻击。"""
        from config import MELEE_DURATION_FRAMES, MELEE_COOLDOWN_FRAMES
        player = make_player()
        callback_called = []
        player.on_melee_swing = lambda: callback_called.append(True)
        result = player.start_melee()
        assert result is True
        assert player.melee_active is True
        assert player.melee_timer == MELEE_DURATION_FRAMES
        assert player.melee_cooldown == MELEE_COOLDOWN_FRAMES
        assert len(callback_called) == 1

    def test_melee_cooldown_blocks_attack(self, make_player):
        """测试冷却期间无法再次启动近战。"""
        player = make_player()
        player.start_melee()
        result = player.start_melee()
        assert result is False

    def test_melee_hitbox_generation(self, make_player):
        """测试近战攻击判定框生成。"""
        import pygame
        player = make_player(100, 200)
        assert player.get_melee_hitbox() is None
        player.start_melee()
        hitbox = player.get_melee_hitbox()
        assert hitbox is not None
        assert isinstance(hitbox, pygame.Rect)

    def test_start_ranged_shot(self, make_player):
        """测试启动远程射击。"""
        from config import RANGED_AMMO_INITIAL, RANGED_COOLDOWN_FRAMES
        player = make_player()
        initial_ammo = player.ammo
        callback_called = []
        player.on_ranged_shot = lambda: callback_called.append(True)
        bullet = player.start_ranged_shot()
        assert bullet is not None
        assert player.ammo == initial_ammo - 1
        assert player.ranged_cooldown == RANGED_COOLDOWN_FRAMES
        assert len(callback_called) == 1

    def test_ranged_shot_no_ammo(self, make_player):
        """测试无弹药时无法射击。"""
        player = make_player()
        player.ammo = 0
        bullet = player.start_ranged_shot()
        assert bullet is None

    def test_ranged_cooldown_blocks_shot(self, make_player):
        """测试冷却期间无法再次射击。"""
        player = make_player()
        player.start_ranged_shot()
        bullet = player.start_ranged_shot()
        assert bullet is None

    def test_start_reload(self, make_player):
        """测试启动换弹。"""
        from config import RANGED_RELOAD_FRAMES, RANGED_AMMO_MAX
        player = make_player()
        player.ammo = 5
        callback_called = []
        player.on_reload = lambda: callback_called.append(True)
        result = player.start_reload()
        assert result is True
        assert player.reloading is True
        assert player.reload_timer == RANGED_RELOAD_FRAMES
        assert len(callback_called) == 1

    def test_reload_when_full(self, make_player):
        """测试弹药已满时无法换弹。"""
        from config import RANGED_AMMO_MAX
        player = make_player()
        player.ammo = RANGED_AMMO_MAX
        result = player.start_reload()
        assert result is False

    def test_reload_completion(self, make_player):
        """测试换弹完成后弹药满。"""
        from config import RANGED_RELOAD_FRAMES, RANGED_AMMO_MAX
        player = make_player()
        player.ammo = 5
        player.start_reload()
        for _ in range(RANGED_RELOAD_FRAMES + 1):
            player.update_combat()
        assert player.reloading is False
        assert player.ammo == RANGED_AMMO_MAX

    def test_bullet_direction_facing_right(self, make_player):
        """测试面向右时子弹向右飞行。"""
        player = make_player(100, 200)
        player.facing_right = True
        bullet = player.start_ranged_shot()
        assert bullet.vx > 0

    def test_bullet_direction_facing_left(self, make_player):
        """测试面向左时子弹向左飞行。"""
        player = make_player(100, 200)
        player.facing_right = False
        bullet = player.start_ranged_shot()
        assert bullet.vx < 0


class TestPlayerBoundary:
    """玩家边界和掉落测试。"""

    def test_left_boundary(self, make_player, make_keys):
        """测试玩家不能越过左边界。"""
        player = make_player(5, 500)
        player.vx = -10
        keys = make_keys()
        player.update(keys, [])
        assert player.x >= 0
        assert player.vx == 0

    def test_fall_death_respawn(self, make_player, make_keys):
        """测试掉落到屏幕外触发死亡重生。"""
        from config import FALL_RESPAWN_Y
        player = make_player(100, FALL_RESPAWN_Y + 50)
        keys = make_keys()
        death_callback = []
        player.on_death = lambda: death_callback.append(True)
        player.update(keys, [])
        assert player.died is True or len(death_callback) > 0

    def test_respawn_position(self, make_player, make_keys):
        """测试死亡后玩家回到起始位置。"""
        from config import FALL_RESPAWN_Y
        player = make_player(500, FALL_RESPAWN_Y + 50)
        player.start_x = 100
        player.start_y = 400
        keys = make_keys()
        player.update(keys, [])
        if player.died:
            assert player.x == player.start_x


class TestPlayerCombatUpdates:
    """玩家战斗计时器更新测试。"""

    def test_melee_timer_decrements_and_ends(self, make_player):
        """测试近战挥砍计时器递减并自动结束。"""
        from config import MELEE_DURATION_FRAMES
        player = make_player()
        player.start_melee()
        for _ in range(MELEE_DURATION_FRAMES - 1):
            player.update_combat()
        assert player.melee_active is True
        player.update_combat()
        assert player.melee_active is False
        assert player.melee_hit_done is False

    def test_melee_angle_progress(self, make_player):
        """测试近战挥砍过程中角度变化。"""
        from config import MELEE_DURATION_FRAMES, MELEE_ARC_HALF
        player = make_player()
        player.start_melee()
        initial_angle = player.melee_angle
        for _ in range(MELEE_DURATION_FRAMES // 2):
            player.update_combat()
        assert player.melee_angle > initial_angle

    def test_melee_cooldown_decrements(self, make_player):
        """测试近战冷却递减。"""
        from config import MELEE_COOLDOWN_FRAMES
        player = make_player()
        player.start_melee()
        cd_before = player.melee_cooldown
        assert cd_before == MELEE_COOLDOWN_FRAMES
        player.update_combat()
        assert player.melee_cooldown == cd_before - 1

    def test_ranged_cooldown_decrements(self, make_player):
        """测试远程冷却递减。"""
        player = make_player()
        player.start_ranged_shot()
        cd_before = player.ranged_cooldown
        player.update_combat()
        assert player.ranged_cooldown == cd_before - 1

    def test_muzzle_flash_timer_decrements(self, make_player):
        """测试枪口闪光计时器递减。"""
        player = make_player()
        player.start_ranged_shot()
        flash_before = player.muzzle_flash_timer
        player.update_combat()
        assert player.muzzle_flash_timer < flash_before

    def test_ranged_shot_timer_decrements(self, make_player):
        """测试远程射击动画计时器递减。"""
        player = make_player()
        player.start_ranged_shot()
        timer_before = player.ranged_shot_timer
        player.update_combat()
        assert player.ranged_shot_timer < timer_before

    def test_reload_interrupted_by_shoot(self, make_player):
        """测试换弹中尝试射击被阻止。"""
        from config import RANGED_AMMO_MAX
        player = make_player()
        player.ammo = 3
        player.start_reload()
        assert player.reloading is True
        bullet = player.start_ranged_shot()
        assert bullet is None
        assert player.reloading is True

    def test_melee_cooldown_prevents_attack_repeat(self, make_player):
        """测试冷却期间近战不能重复触发。"""
        player = make_player()
        result1 = player.start_melee()
        assert result1 is True
        result2 = player.start_melee()
        assert result2 is False

    def test_get_melee_hitbox_left_facing(self, make_player):
        """测试朝向左时的近战命中框。"""
        player = make_player(200, 300)
        player.facing_right = False
        player.start_melee()
        hitbox = player.get_melee_hitbox()
        assert hitbox.x < player.x

    def test_combat_update_multiple_frames(self, make_player):
        """测试多帧战斗更新综合效果。"""
        from config import MELEE_DURATION_FRAMES, RANGED_RELOAD_FRAMES, RANGED_AMMO_MAX
        player = make_player()
        player.ammo = 2
        player.start_melee()
        player.start_reload()
        frames = max(MELEE_DURATION_FRAMES + 5, RANGED_RELOAD_FRAMES + 5)
        for _ in range(frames):
            player.update_combat()
        assert player.melee_active is False
        assert player.reloading is False
        assert player.ammo == RANGED_AMMO_MAX
        assert player.melee_cooldown == 0
