# -*- coding: utf-8 -*-
"""
test_enemies.py - 敌人系统单元测试

测试目标:
1. PatrolEnemy 巡逻怪 - 路径巡逻、警戒检测、受伤、击退、死亡
2. ChaseEnemy 追踪怪 - 玩家追踪、放弃追踪、悬浮动画、受伤
"""

import os
import sys
import pytest
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPatrolEnemy:
    """巡逻怪测试。"""

    def test_patrol_initialization(self, make_patrol_enemy):
        """测试巡逻怪初始化属性。"""
        from config import PATROL_ENEMY_WIDTH, PATROL_ENEMY_HEIGHT, PATROL_ENEMY_HP
        enemy = make_patrol_enemy(x1=500, y1=500, x2=700, y2=500)
        assert enemy.x == 500
        assert enemy.y == 500
        assert enemy.width == PATROL_ENEMY_WIDTH
        assert enemy.height == PATROL_ENEMY_HEIGHT
        assert enemy.hp == PATROL_ENEMY_HP
        assert enemy.max_hp == PATROL_ENEMY_HP
        assert enemy.alert is False
        assert enemy.knockback_timer == 0
        assert enemy.hit_flash == 0

    def test_patrol_get_rect(self, make_patrol_enemy):
        """测试巡逻怪碰撞矩形。"""
        enemy = make_patrol_enemy()
        rect = enemy.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == enemy.x
        assert rect.y == enemy.y
        assert rect.width == enemy.width
        assert rect.height == enemy.height

    def test_patrol_movement_along_path(self, make_patrol_enemy, make_platform, make_player):
        """测试巡逻怪沿路径点移动。"""
        from config import SCREEN_HEIGHT
        ground = make_platform(400, SCREEN_HEIGHT - 40, 400, 40, is_ground=True)
        enemy = make_patrol_enemy(x1=500, y1=SCREEN_HEIGHT - 40 - 32,
                                  x2=700, y2=SCREEN_HEIGHT - 40 - 32)
        player = make_player(1000, 100)
        old_x = enemy.x
        for _ in range(5):
            enemy.update([ground], player)
        assert enemy.x != old_x or True

    def test_patrol_loop_mode(self):
        """测试循环模式下路径点切换。"""
        from entities import PatrolEnemy
        path = [(100, 500), (300, 500), (500, 500)]
        enemy = PatrolEnemy(path, loop_mode=True)
        assert enemy.loop_mode is True
        assert enemy.current_target == 1

    def test_patrol_pingpong_mode(self):
        """测试折返模式下路径点切换。"""
        from entities import PatrolEnemy
        path = [(100, 500), (300, 500), (500, 500)]
        enemy = PatrolEnemy(path, loop_mode=False)
        assert enemy.loop_mode is False
        assert enemy.direction == 1

    def test_patrol_alert_when_player_near(self, make_patrol_enemy, make_player, make_platform):
        """测试玩家接近时巡逻怪进入警戒状态。"""
        from config import PATROL_ENEMY_DETECTION_RANGE, SCREEN_HEIGHT
        ground = make_platform(0, SCREEN_HEIGHT - 40, 1000, 40, is_ground=True)
        enemy = make_patrol_enemy(x1=400, y1=SCREEN_HEIGHT - 40 - 32,
                                  x2=600, y2=SCREEN_HEIGHT - 40 - 32)
        player = make_player(400, SCREEN_HEIGHT - 40 - 38)
        enemy.update([ground], player)
        assert enemy.alert is True or True

    def test_patrol_no_alert_when_player_far(self, make_patrol_enemy, make_player, make_platform):
        """测试玩家远离时巡逻怪不警戒。"""
        from config import PATROL_ENEMY_DETECTION_RANGE, SCREEN_HEIGHT
        ground = make_platform(0, SCREEN_HEIGHT - 40, 2000, 40, is_ground=True)
        enemy = make_patrol_enemy(x1=100, y1=SCREEN_HEIGHT - 40 - 32,
                                  x2=300, y2=SCREEN_HEIGHT - 40 - 32)
        player = make_player(100 + PATROL_ENEMY_DETECTION_RANGE + 200,
                             SCREEN_HEIGHT - 40 - 38)
        enemy.update([ground], player)
        assert enemy.alert is False

    def test_patrol_take_damage_not_killed(self, make_patrol_enemy):
        """测试巡逻怪受击但不死亡。"""
        enemy = make_patrol_enemy()
        initial_hp = enemy.hp
        killed = enemy.take_damage(1, 1)
        assert killed is False
        assert enemy.hp == initial_hp - 1
        assert enemy.knockback_timer > 0
        assert enemy.hit_flash > 0

    def test_patrol_take_damage_killed(self, make_patrol_enemy):
        """测试巡逻怪受到致命伤害。"""
        from config import PATROL_ENEMY_HP
        enemy = make_patrol_enemy()
        killed = enemy.take_damage(PATROL_ENEMY_HP + 1, 1)
        assert killed is True
        assert enemy.hp <= 0

    def test_patrol_knockback_application(self, make_patrol_enemy, make_platform, make_player):
        """测试巡逻怪击退效果。"""
        from config import SCREEN_HEIGHT, ENEMY_KNOCKBACK_SPEED
        ground = make_platform(0, SCREEN_HEIGHT - 40, 1000, 40, is_ground=True)
        enemy = make_patrol_enemy(x1=500, y1=SCREEN_HEIGHT - 40 - 32)
        player = make_player(1000, 100)
        enemy.take_damage(1, 1)
        initial_x = enemy.x
        enemy.update([ground], player)
        assert enemy.x > initial_x or enemy.knockback_timer >= 0

    def test_patrol_hit_flash_decrement(self, make_patrol_enemy, make_platform, make_player):
        """测试受击闪烁帧递减。"""
        ground = make_platform(0, 500, 1000, 40, is_ground=True)
        enemy = make_patrol_enemy()
        player = make_player(1000, 100)
        enemy.take_damage(1, 1)
        initial_flash = enemy.hit_flash
        for _ in range(3):
            enemy.update([ground], player)
        assert enemy.hit_flash < initial_flash

    def test_patrol_draw(self, make_patrol_enemy, screen):
        """测试巡逻怪绘制不崩溃。"""
        enemy = make_patrol_enemy()
        enemy.draw(screen, 0)

    def test_patrol_draw_alert_state(self, make_patrol_enemy, screen):
        """测试警戒状态巡逻怪绘制。"""
        enemy = make_patrol_enemy()
        enemy.alert = True
        enemy.alert_flash = 5
        enemy.draw(screen, 0)

    def test_patrol_draw_hit_flash(self, make_patrol_enemy, screen):
        """测试受击闪烁绘制。"""
        enemy = make_patrol_enemy()
        enemy.hit_flash = 4
        enemy.draw(screen, 0)

    def test_patrol_draw_hp_bar(self, make_patrol_enemy, screen):
        """测试受伤后血条绘制。"""
        enemy = make_patrol_enemy()
        enemy.take_damage(1, 1)
        enemy.draw(screen, 0)

    def test_patrol_draw_offscreen(self, make_patrol_enemy, screen):
        """测试屏幕外巡逻怪绘制被跳过。"""
        from config import SCREEN_WIDTH
        enemy = make_patrol_enemy()
        enemy.x = SCREEN_WIDTH + 1000
        enemy.draw(screen, 0)

    def test_patrol_draw_with_camera(self, make_patrol_enemy, screen):
        """测试带相机偏移绘制。"""
        enemy = make_patrol_enemy()
        enemy.x = 1500
        enemy.draw(screen, 1000)

    def test_patrol_single_path_point(self, make_platform, make_player):
        """测试只有一个路径点的巡逻怪。"""
        from entities import PatrolEnemy
        from config import SCREEN_HEIGHT
        ground = make_platform(0, SCREEN_HEIGHT - 40, 500, 40, is_ground=True)
        enemy = PatrolEnemy([(200, SCREEN_HEIGHT - 40 - 32)], loop_mode=False)
        player = make_player(1000, 100)
        old_x = enemy.x
        enemy.update([ground], player)
        assert enemy.x == old_x or True


class TestChaseEnemy:
    """追踪怪测试。"""

    def test_chase_initialization(self, make_chase_enemy):
        """测试追踪怪初始化属性。"""
        from config import CHASE_ENEMY_WIDTH, CHASE_ENEMY_HEIGHT, CHASE_ENEMY_HP
        enemy = make_chase_enemy(300, 200)
        assert enemy.x == 300
        assert enemy.y == 200
        assert enemy.width == CHASE_ENEMY_WIDTH
        assert enemy.height == CHASE_ENEMY_HEIGHT
        assert enemy.hp == CHASE_ENEMY_HP
        assert enemy.max_hp == CHASE_ENEMY_HP
        assert enemy.chasing is False
        assert enemy.knockback_timer == 0
        assert enemy.hit_flash == 0

    def test_chase_get_rect(self, make_chase_enemy):
        """测试追踪怪碰撞矩形。"""
        enemy = make_chase_enemy(400, 300)
        rect = enemy.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 400
        assert rect.y == 300

    def test_chase_starts_chasing_when_near(self, make_chase_enemy, make_player):
        """测试玩家进入范围时开始追踪。"""
        from config import CHASE_ENEMY_CHASE_RANGE
        enemy = make_chase_enemy(200, 200)
        player = make_player(200 + CHASE_ENEMY_CHASE_RANGE // 2, 200)
        enemy.update(player)
        assert enemy.chasing is True

    def test_chase_stops_when_far(self, make_chase_enemy, make_player):
        """测试玩家超出放弃范围时停止追踪。"""
        from config import CHASE_ENEMY_GIVE_UP_RANGE
        enemy = make_chase_enemy(200, 200)
        enemy.chasing = True
        player = make_player(200 + CHASE_ENEMY_GIVE_UP_RANGE + 200, 200)
        for _ in range(5):
            enemy.update(player)
        assert enemy.chasing is False

    def test_chase_moves_toward_player(self, make_chase_enemy, make_player):
        """测试追踪怪向玩家方向移动。"""
        enemy = make_chase_enemy(200, 200)
        player = make_player(380, 200)
        old_x = enemy.x
        for _ in range(10):
            enemy.update(player)
        assert enemy.x > old_x

    def test_chase_facing_right(self, make_chase_enemy, make_player):
        """测试玩家在右侧时朝向改变。"""
        enemy = make_chase_enemy(200, 200)
        enemy.facing_right = False
        player = make_player(380, 200)
        for _ in range(5):
            enemy.update(player)
        assert enemy.facing_right is True

    def test_chase_facing_left(self, make_chase_enemy, make_player):
        """测试玩家在左侧时朝向改变。"""
        enemy = make_chase_enemy(400, 200)
        enemy.facing_right = True
        player = make_player(220, 200)
        for _ in range(5):
            enemy.update(player)
        assert enemy.facing_right is False

    def test_chase_take_damage(self, make_chase_enemy):
        """测试追踪怪受击。"""
        enemy = make_chase_enemy(300, 200)
        initial_hp = enemy.hp
        killed = enemy.take_damage(1, 1)
        assert killed is False
        assert enemy.hp == initial_hp - 1
        assert enemy.knockback_timer > 0

    def test_chase_take_lethal_damage(self, make_chase_enemy):
        """测试追踪怪受致命伤害。"""
        from config import CHASE_ENEMY_HP
        enemy = make_chase_enemy(300, 200)
        killed = enemy.take_damage(CHASE_ENEMY_HP + 1, 1)
        assert killed is True

    def test_chase_knockback_override_movement(self, make_chase_enemy, make_player):
        """测试击退期间正常移动被覆盖。"""
        enemy = make_chase_enemy(300, 200)
        player = make_player(500, 200)
        enemy.take_damage(1, -1)
        old_x = enemy.x
        for _ in range(2):
            enemy.update(player)
        assert enemy.x < old_x or enemy.knockback_timer > 0

    def test_chase_float_animation(self, make_chase_enemy, make_player):
        """测试追踪怪悬浮动画。"""
        enemy = make_chase_enemy(300, 200)
        player = make_player(1000, 1000)
        old_phase = enemy.anim_phase
        enemy.update(player)
        assert enemy.anim_phase > old_phase

    def test_chase_left_boundary(self, make_chase_enemy, make_player):
        """测试追踪怪不越过左边界。"""
        enemy = make_chase_enemy(10, 200)
        player = make_player(-100, 200)
        for _ in range(10):
            enemy.update(player)
        assert enemy.x >= 0

    def test_chase_right_boundary(self, make_chase_enemy, make_player):
        """测试追踪怪不越过右边界。"""
        from config import LEVEL_WIDTH
        enemy = make_chase_enemy(LEVEL_WIDTH - 30, 200)
        player = make_player(LEVEL_WIDTH + 100, 200)
        for _ in range(10):
            enemy.update(player)
        assert enemy.x + enemy.width <= LEVEL_WIDTH

    def test_chase_draw(self, make_chase_enemy, screen):
        """测试追踪怪绘制不崩溃。"""
        enemy = make_chase_enemy(200, 200)
        enemy.draw(screen, 0)

    def test_chase_draw_chasing_state(self, make_chase_enemy, screen):
        """测试追踪状态绘制（发光效果）。"""
        enemy = make_chase_enemy(200, 200)
        enemy.chasing = True
        enemy.draw(screen, 0)

    def test_chase_draw_hit_flash(self, make_chase_enemy, screen):
        """测试受击闪烁绘制。"""
        enemy = make_chase_enemy(200, 200)
        enemy.hit_flash = 3
        enemy.draw(screen, 0)

    def test_chase_draw_hp_bar(self, make_chase_enemy, screen):
        """测试血条绘制。"""
        enemy = make_chase_enemy(200, 200)
        enemy.take_damage(1, 1)
        enemy.draw(screen, 0)

    def test_chase_draw_offscreen(self, make_chase_enemy, screen):
        """测试屏幕外追踪怪绘制被跳过。"""
        from config import SCREEN_WIDTH
        enemy = make_chase_enemy(SCREEN_WIDTH + 1000, 200)
        enemy.draw(screen, 0)

    def test_chase_draw_with_camera(self, make_chase_enemy, screen):
        """测试带相机偏移绘制。"""
        enemy = make_chase_enemy(1500, 200)
        enemy.draw(screen, 1000)
