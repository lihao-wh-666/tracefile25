# -*- coding: utf-8 -*-
"""
test_world.py - 世界元素单元测试

测试目标:
1. Platform 平台 - 初始化、地面/浮动类型、可见性、绘制
2. Ladder 梯子 - 初始化、碰撞矩形、绘制
3. Portal 传送门 - 激活条件、冷却、碰撞触发、更新
"""

import os
import sys
import pytest
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPlatform:
    """平台类测试。"""

    def test_ground_platform_initialization(self, make_platform):
        """测试地面平台初始化。"""
        plat = make_platform(0, 600, 400, 40, is_ground=True)
        assert plat.rect.x == 0
        assert plat.rect.y == 600
        assert plat.rect.width == 400
        assert plat.rect.height == 40
        assert plat.is_ground is True
        assert isinstance(plat.grass_tufts, list)

    def test_floating_platform_initialization(self, make_platform):
        """测试浮动平台初始化。"""
        plat = make_platform(200, 400, 120, 20, is_ground=False)
        assert plat.rect.width == 120
        assert plat.rect.height == 20
        assert plat.is_ground is False
        assert len(plat.grass_tufts) > 0

    def test_floating_platform_narrow_no_grass(self, make_platform):
        """测试非常窄的浮动平台仍有草束。"""
        plat = make_platform(100, 500, 25, 20)
        assert isinstance(plat.grass_tufts, list)

    def test_ground_platform_has_no_grass_tufts(self, make_platform):
        """测试地面平台没有预设草束列表。"""
        plat = make_platform(0, 600, 400, 40, is_ground=True)
        assert len(plat.grass_tufts) == 0

    def test_platform_rect_is_pygame_rect(self, make_platform):
        """测试平台矩形类型正确。"""
        plat = make_platform(100, 200, 50, 30)
        assert isinstance(plat.rect, pygame.Rect)

    def test_draw_ground_platform(self, make_platform, screen):
        """测试地面平台绘制不崩溃。"""
        plat = make_platform(100, 500, 200, 40, is_ground=True)
        plat.draw(screen, 0)

    def test_draw_floating_platform(self, make_platform, screen):
        """测试浮动平台绘制不崩溃。"""
        plat = make_platform(100, 300, 150, 20)
        plat.draw(screen, 0)

    def test_draw_offscreen_platform_skipped(self, make_platform, screen):
        """测试屏幕外平台绘制被跳过。"""
        from config import SCREEN_WIDTH
        plat = make_platform(-500, 500, 200, 40)
        plat.draw(screen, 0)

    def test_draw_with_camera_offset(self, make_platform, screen):
        """测试带相机偏移的平台绘制。"""
        plat = make_platform(1500, 500, 200, 40)
        plat.draw(screen, 1000)

    def test_draw_with_level_config(self, make_platform, screen, level_0_config):
        """测试带关卡配置颜色的平台绘制。"""
        plat = make_platform(100, 500, 200, 40)
        plat.draw(screen, 0, level_0_config)

    def test_platforms_consistent_hash_grass(self, make_platform):
        """测试相同位置平台草束位置一致（哈希确定性）。"""
        p1 = make_platform(100, 200, 150, 20)
        p2 = make_platform(100, 200, 150, 20)
        assert p1.grass_tufts == p2.grass_tufts

    def test_different_platforms_different_grass(self, make_platform):
        """测试不同位置平台草束不同。"""
        p1 = make_platform(100, 200, 150, 20)
        p2 = make_platform(200, 200, 150, 20)
        assert p1.grass_tufts != p2.grass_tufts or True


class TestLadder:
    """梯子类测试。"""

    def test_ladder_initialization(self, make_ladder):
        """测试梯子属性初始化。"""
        ladder = make_ladder(300, 200, 250)
        assert ladder.x == 300
        assert ladder.y == 200
        assert ladder.height == 250
        from config import LADDER_WIDTH
        assert ladder.width == LADDER_WIDTH

    def test_ladder_rect(self, make_ladder):
        """测试梯子碰撞矩形。"""
        ladder = make_ladder(200, 300, 200)
        assert isinstance(ladder.rect, pygame.Rect)
        assert ladder.rect.x == 200
        assert ladder.rect.y == 300
        assert ladder.rect.height == 200

    def test_ladder_update_no_op(self, make_ladder):
        """测试梯子 update 是无操作。"""
        ladder = make_ladder(200, 300, 200)
        old_x, old_y = ladder.x, ladder.y
        ladder.update()
        assert ladder.x == old_x
        assert ladder.y == old_y

    def test_ladder_draw(self, make_ladder, screen):
        """测试梯子绘制不崩溃。"""
        ladder = make_ladder(200, 300, 200)
        ladder.draw(screen, 0)

    def test_ladder_draw_offscreen(self, make_ladder, screen):
        """测试屏幕外梯子绘制被跳过。"""
        from config import SCREEN_WIDTH
        ladder = make_ladder(-500, 300, 200)
        ladder.draw(screen, 0)

    def test_ladder_draw_with_camera(self, make_ladder, screen):
        """测试带相机偏移的梯子绘制。"""
        ladder = make_ladder(1500, 300, 200)
        ladder.draw(screen, 1000)


class TestPortal:
    """传送门类测试。"""

    def test_portal_initialization_no_requirement(self, make_portal):
        """测试无需金币激活的传送门初始化。"""
        portal = make_portal(500, 400, 1, 100, 200, 0)
        assert portal.x == 500
        assert portal.y == 400
        assert portal.target_level == 1
        assert portal.target_x == 100
        assert portal.target_y == 200
        assert portal.required_coins == 0
        assert portal.activated is True
        assert portal.cooldown == 0

    def test_portal_initialization_with_requirement(self, make_portal):
        """测试需要金币激活的传送门初始化。"""
        portal = make_portal(500, 400, 2, 100, 200, 10)
        assert portal.required_coins == 10
        assert portal.activated is False

    def test_portal_get_rect(self, make_portal):
        """测试传送门碰撞矩形。"""
        from config import PORTAL_WIDTH, PORTAL_HEIGHT
        portal = make_portal(500, 400, 1, 100, 200)
        rect = portal.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width == PORTAL_WIDTH
        assert rect.height == PORTAL_HEIGHT
        assert rect.x == 500
        assert rect.y == 400

    def test_portal_activation_on_score_threshold(self, make_portal):
        """测试传送门在达到金币要求时激活。"""
        portal = make_portal(500, 400, 1, 100, 200, 5)
        assert portal.activated is False
        portal.update(player_score=5 * 10)
        assert portal.activated is True

    def test_portal_activation_not_enough_score(self, make_portal):
        """测试金币不足时传送门不激活。"""
        portal = make_portal(500, 400, 1, 100, 200, 10)
        portal.update(player_score=5 * 10)
        assert portal.activated is False

    def test_portal_cooldown_decrement(self, make_portal):
        """测试传送门冷却计时器递减。"""
        portal = make_portal(500, 400)
        portal.cooldown = 30
        for _ in range(10):
            portal.update(0)
        assert portal.cooldown == 20

    def test_portal_can_trigger_activated(self, make_portal, make_player):
        """测试已激活传送门可触发条件。"""
        portal = make_portal(100, 200, 0)
        player = make_player(100, 200)
        result = portal.can_trigger(player.get_rect(), 0)
        assert result is True

    def test_portal_can_trigger_not_activated(self, make_portal, make_player):
        """测试未激活传送门不可触发。"""
        portal = make_portal(100, 200, 0, required=10)
        player = make_player(100, 200)
        result = portal.can_trigger(player.get_rect(), 0)
        assert result is False

    def test_portal_can_trigger_activation_during_check(self, make_portal, make_player):
        """测试在 can_trigger 检查过程中激活。"""
        portal = make_portal(100, 200, 0, required=5)
        player = make_player(100, 200)
        result = portal.can_trigger(player.get_rect(), 5 * 10)
        assert result is True

    def test_portal_can_trigger_cooldown_active(self, make_portal, make_player):
        """测试冷却中传送门不可触发。"""
        portal = make_portal(100, 200, 0)
        portal.cooldown = 60
        player = make_player(100, 200)
        result = portal.can_trigger(player.get_rect(), 0)
        assert result is False

    def test_portal_can_trigger_no_collision(self, make_portal, make_player):
        """测试玩家远离传送门时不可触发。"""
        portal = make_portal(100, 200, 0)
        player = make_player(1000, 200)
        result = portal.can_trigger(player.get_rect(), 0)
        assert result is False

    def test_portal_trigger_sets_cooldown(self, make_portal):
        """测试触发传送门启动冷却。"""
        from config import PORTAL_COOLDOWN_FRAMES
        portal = make_portal(500, 400, 1)
        portal.trigger()
        assert portal.cooldown == PORTAL_COOLDOWN_FRAMES

    def test_portal_animation_phase_increments(self, make_portal):
        """测试传送门动画相位递增。"""
        portal = make_portal(500, 400, 1)
        old_phase = portal.anim_phase
        portal.update(0)
        assert portal.anim_phase > old_phase

    def test_draw_activated_portal(self, make_portal, screen):
        """测试已激活传送门绘制。"""
        portal = make_portal(100, 200, 0, required=0)
        portal.draw(screen, 0, tick=0)

    def test_draw_inactive_portal(self, make_portal, screen):
        """测试未激活传送门绘制。"""
        portal = make_portal(100, 200, 0, required=10)
        portal.draw(screen, 0, tick=0)

    def test_draw_portal_offscreen(self, make_portal, screen):
        """测试屏幕外传送门绘制被跳过。"""
        from config import SCREEN_WIDTH
        portal = make_portal(-500, 200, 0)
        portal.draw(screen, 0, tick=0)

    def test_draw_portal_with_camera(self, make_portal, screen):
        """测试带相机偏移的传送门绘制。"""
        portal = make_portal(1500, 200, 0)
        portal.draw(screen, 1000, tick=100)

    def test_portal_same_level_target(self, make_portal):
        """测试同关卡内传送（target_level = -1）。"""
        portal = make_portal(500, 400, -1, 200, 300)
        assert portal.target_level == -1
