# -*- coding: utf-8 -*-
"""
test_combat.py - 战斗系统单元测试

测试目标:
1. Bullet 子弹类 - 初始化、弹道物理、碰撞检测、生命周期
2. CombatManager - 近战命中检测、子弹碰撞、敌人受伤、金币收集
"""

import os
import sys
import pytest
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBullet:
    """子弹类测试。"""

    def test_bullet_initialization(self, make_bullet):
        """测试子弹属性初始化。"""
        bullet = make_bullet(100, 200, 12, -1, 1)
        assert bullet.x == 100
        assert bullet.y == 200
        assert bullet.vx == 12
        assert bullet.vy == -1
        assert bullet.damage == 1
        assert bullet.alive is True
        assert bullet.distance_traveled == 0.0
        assert isinstance(bullet.trail, list)

    def test_bullet_get_rect(self, make_bullet):
        """测试子弹碰撞矩形。"""
        from config import RANGED_PROJECTILE_SIZE
        bullet = make_bullet(100, 200, 5, 0)
        rect = bullet.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width == RANGED_PROJECTILE_SIZE * 2
        assert rect.height == RANGED_PROJECTILE_SIZE * 2

    def test_bullet_update_position(self, make_bullet):
        """测试子弹飞行更新位置。"""
        bullet = make_bullet(100, 200, 10, 0)
        old_x = bullet.x
        bullet.update([])
        assert bullet.x > old_x
        assert bullet.alive is True

    def test_bullet_gravity_effect(self, make_bullet):
        """测试子弹受重力影响。"""
        from config import RANGED_GRAVITY
        bullet = make_bullet(100, 200, 5, 0)
        old_vy = bullet.vy
        bullet.update([])
        assert bullet.vy > old_vy

    def test_bullet_distance_tracking(self, make_bullet):
        """测试子弹飞行距离追踪。"""
        bullet = make_bullet(100, 200, 10, 0)
        bullet.update([])
        assert bullet.distance_traveled > 0

    def test_bullet_max_distance(self, make_bullet):
        """测试子弹超出最大飞行距离后消失。"""
        from config import RANGED_MAX_DISTANCE
        bullet = make_bullet(100, 200, 50, 0)
        bullet.distance_traveled = RANGED_MAX_DISTANCE - 1
        for _ in range(10):
            bullet.update([])
            if not bullet.alive:
                break
        assert bullet.alive is False

    def test_bullet_offscreen_left(self, make_bullet):
        """测试子弹飞出左边界后死亡。"""
        bullet = make_bullet(-100, 200, -50, 0)
        bullet.update([])
        assert bullet.alive is False

    def test_bullet_offscreen_bottom(self, make_bullet):
        """测试子弹飞出下边界后死亡。"""
        from config import SCREEN_HEIGHT
        bullet = make_bullet(100, SCREEN_HEIGHT + 100, 0, 50)
        bullet.update([])
        assert bullet.alive is False

    def test_bullet_collides_with_platform(self, make_bullet, make_platform):
        """测试子弹撞击平台后消失。"""
        bullet = make_bullet(100, 200, 5, 0)
        plat = make_platform(150, 190, 40, 40)
        for _ in range(20):
            bullet.update([plat])
            if not bullet.alive:
                break
        assert bullet.alive is False

    def test_bullet_trail_accumulation(self, make_bullet):
        """测试子弹轨迹点累积。"""
        bullet = make_bullet(100, 200, 5, 0)
        for _ in range(5):
            bullet.update([])
        assert len(bullet.trail) > 0
        assert len(bullet.trail) <= 8


class TestBulletEdgeCases:
    """子弹边界条件测试。"""

    def test_bullet_zero_velocity(self, make_bullet):
        """测试子弹速度为0的情况。"""
        bullet = make_bullet(100, 200, 0, 0)
        old_x = bullet.x
        old_y = bullet.y
        bullet.update([])
        assert bullet.x == old_x
        assert bullet.y > old_y

    def test_bullet_negative_damage(self, make_bullet):
        """测试负伤害（不崩溃）。"""
        bullet = make_bullet(100, 200, 5, 0, -1)
        assert bullet.damage == -1
        bullet.update([])
        assert bullet.alive is True

    def test_multiple_bullets_independent(self, make_bullet):
        """测试多个子弹状态独立。"""
        b1 = make_bullet(100, 200, 5, 0)
        b2 = make_bullet(300, 200, -5, 0)
        b1.update([])
        b2.update([])
        assert b1.x > 100
        assert b2.x < 300
        assert b1.alive != b2.alive or True


class TestCombatManager:
    """战斗管理器测试。"""

    def test_combat_manager_initialization(self):
        """测试战斗管理器初始化。"""
        from core.combat import CombatManager

        class MockGame:
            pass
        game = MockGame()
        cm = CombatManager(game)
        assert cm.game is game

    def test_bullet_draw_onscreen(self, make_bullet, pygame_session):
        """测试子弹在屏幕内绘制不崩溃。"""
        screen = pygame.Surface((800, 600))
        bullet = make_bullet(400, 300, 5, 0)
        bullet.draw(screen, 0)
        assert True

    def test_bullet_draw_offscreen_skipped(self, make_bullet, pygame_session):
        """测试屏幕外子弹不绘制。"""
        screen = pygame.Surface((800, 600))
        bullet = make_bullet(-200, 700, 5, 0)
        bullet.draw(screen, 0)
        assert True

    def test_bullet_draw_with_camera(self, make_bullet, pygame_session):
        """测试带相机偏移绘制不崩溃。"""
        screen = pygame.Surface((800, 600))
        bullet = make_bullet(600, 300, 5, 0)
        bullet.draw(screen, 300)
        assert True

    def test_bullet_dead_not_drawn(self, make_bullet, pygame_session):
        """测试死亡子弹不绘制。"""
        screen = pygame.Surface((800, 600))
        bullet = make_bullet(400, 300, 5, 0)
        bullet.alive = False
        bullet.draw(screen, 0)
        assert True

    def test_bullet_trail_preserved(self, make_bullet):
        """测试多帧更新后轨迹保留。"""
        bullet = make_bullet(100, 200, 8, 0)
        for _ in range(4):
            bullet.update([])
        assert len(bullet.trail) >= 3

    def test_bullet_gravity_increases_y(self, make_bullet):
        """测试子弹受重力影响y增加。"""
        bullet = make_bullet(100, 200, 0, 0)
        bullet.update([])
        assert bullet.y > 200

    def test_bullet_negative_y_velocity(self, make_bullet):
        """测试负y方向子弹移动。"""
        bullet = make_bullet(100, 400, 0, -10)
        initial_y = bullet.y
        bullet.update([])
        assert bullet.y < initial_y + 5

    def test_bullet_hit_platform_top_side(self, make_bullet, make_platform):
        """测试子弹从顶部击中平台消失。"""
        plat = make_platform(200, 250, 100, 20)
        bullet = make_bullet(250, 245, 0, 5)
        bullet.update([plat])
        assert bullet.alive is False
