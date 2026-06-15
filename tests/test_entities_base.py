# -*- coding: utf-8 -*-
"""
test_entities_base.py - 实体基础模块单元测试

测试目标:
1. BaseEntity 基类接口 - 属性初始化、get_rect、is_visible
2. 水平碰撞解析 resolve_horizontal_collision - 正常碰撞、边界情况
3. 垂直碰撞解析 resolve_vertical_collision - 落地、撞头、刚落地检测
"""

import os
import sys
import pytest
import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockEntity:
    """用于碰撞测试的模拟实体类。"""

    def __init__(self, x, y, width, height, vx=0, vy=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = vx
        self.vy = vy


class TestBaseEntity:
    """BaseEntity 基类测试。"""

    def test_initialization(self):
        """测试基类属性初始化。"""
        from entities.base import BaseEntity
        ent = BaseEntity(100, 200, 32, 48)
        assert ent.x == 100
        assert ent.y == 200
        assert ent.width == 32
        assert ent.height == 48

    def test_get_rect(self):
        """测试碰撞矩形生成。"""
        from entities.base import BaseEntity
        ent = BaseEntity(50, 60, 28, 38)
        rect = ent.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 50
        assert rect.y == 60
        assert rect.width == 28
        assert rect.height == 38

    def test_update_not_implemented(self):
        """测试未重写 update 时抛出 NotImplementedError。"""
        from entities.base import BaseEntity
        ent = BaseEntity(0, 0, 10, 10)
        with pytest.raises(NotImplementedError):
            ent.update()

    def test_draw_not_implemented(self, screen):
        """测试未重写 draw 时抛出 NotImplementedError。"""
        from entities.base import BaseEntity
        ent = BaseEntity(0, 0, 10, 10)
        with pytest.raises(NotImplementedError):
            ent.draw(screen, 0)

    def test_is_visible_on_screen(self):
        """测试实体在屏幕可见范围内。"""
        from entities.base import BaseEntity
        from config import SCREEN_WIDTH
        ent = BaseEntity(100, 100, 50, 50)
        assert ent.is_visible(0) is True

    def test_is_visible_left_offscreen(self):
        """测试实体在屏幕左侧外不可见。"""
        from entities.base import BaseEntity
        ent = BaseEntity(-200, 100, 50, 50)
        assert ent.is_visible(0) is False

    def test_is_visible_right_offscreen(self):
        """测试实体在屏幕右侧外不可见。"""
        from entities.base import BaseEntity
        from config import SCREEN_WIDTH
        ent = BaseEntity(SCREEN_WIDTH + 200, 100, 50, 50)
        assert ent.is_visible(0) is False

    def test_is_visible_with_camera_offset(self):
        """测试相机偏移后的可见性判断。"""
        from entities.base import BaseEntity
        from config import SCREEN_WIDTH
        ent = BaseEntity(SCREEN_WIDTH + 100, 100, 50, 50)
        assert ent.is_visible(100) is True

    def test_is_visible_near_left_edge(self):
        """测试实体靠近左边缘但仍可见。"""
        from entities.base import BaseEntity
        ent = BaseEntity(-40, 100, 50, 50)
        assert ent.is_visible(0) is True

    def test_is_visible_near_right_edge(self):
        """测试实体靠近右边缘但仍可见。"""
        from entities.base import BaseEntity
        from config import SCREEN_WIDTH
        ent = BaseEntity(SCREEN_WIDTH - 10, 100, 50, 50)
        assert ent.is_visible(0) is True


class TestHorizontalCollision:
    """水平方向碰撞解析测试。"""

    def test_no_collision(self, sample_platforms):
        """测试无碰撞情况下实体位置不变。"""
        from entities.base import resolve_horizontal_collision
        ent = MockEntity(10, 500, 28, 38, vx=0)
        result = resolve_horizontal_collision(ent, sample_platforms)
        assert result is False
        assert ent.x == 10
        assert ent.vx == 0

    def test_collision_from_left(self, make_platform):
        """测试从左侧撞击平台，实体被推回左边。"""
        from entities.base import resolve_horizontal_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(95, 505, 28, 38, vx=5)
        result = resolve_horizontal_collision(ent, [plat])
        assert result is True
        assert ent.x == plat.rect.left - ent.width
        assert ent.vx == 0

    def test_collision_from_right(self, make_platform):
        """测试从右侧撞击平台，实体被推回右边。"""
        from entities.base import resolve_horizontal_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(180, 505, 28, 38, vx=-5)
        result = resolve_horizontal_collision(ent, [plat])
        assert result is True
        assert ent.x == plat.rect.right
        assert ent.vx == 0

    def test_collision_zero_velocity(self, make_platform):
        """测试速度为0但重叠时的碰撞处理。"""
        from entities.base import resolve_horizontal_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(95, 505, 28, 38, vx=0)
        result = resolve_horizontal_collision(ent, [plat])
        assert result is True
        assert ent.vx == 0

    def test_overlap_from_above_no_horizontal(self, make_platform):
        """测试从上方重叠但不在水平碰撞条件。"""
        from entities.base import resolve_horizontal_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(120, 498, 28, 38, vx=0)
        result = resolve_horizontal_collision(ent, [plat])
        assert result is True

    def test_multiple_platforms_collision(self, make_platform):
        """测试同时与多个平台水平碰撞。"""
        from entities.base import resolve_horizontal_collision
        plat1 = make_platform(100, 500, 100, 20)
        plat2 = make_platform(100, 520, 100, 20)
        ent = MockEntity(95, 505, 28, 38, vx=3)
        result = resolve_horizontal_collision(ent, [plat1, plat2])
        assert result is True
        assert ent.vx == 0

    def test_empty_platform_list(self):
        """测试空平台列表不发生碰撞。"""
        from entities.base import resolve_horizontal_collision
        ent = MockEntity(100, 500, 28, 38, vx=5)
        orig_x = ent.x
        result = resolve_horizontal_collision(ent, [])
        assert result is False
        assert ent.x == orig_x
        assert ent.vx == 5


class TestVerticalCollision:
    """垂直方向碰撞解析测试。"""

    def test_landing_on_platform(self, make_platform):
        """测试下落到平台顶部，触发落地。"""
        from entities.base import resolve_vertical_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(120, 495, 28, 38, vy=5)
        on_ground, landed = resolve_vertical_collision(ent, [plat], was_on_ground=False)
        assert on_ground is True
        assert landed is True
        assert ent.y == plat.rect.top - ent.height
        assert ent.vy == 0

    def test_hitting_head_on_ceiling(self, make_platform):
        """测试向上移动时撞到平台底部。"""
        from entities.base import resolve_vertical_collision
        plat = make_platform(100, 400, 100, 20)
        ent = MockEntity(120, 405, 28, 38, vy=-8)
        on_ground, landed = resolve_vertical_collision(ent, [plat], was_on_ground=False)
        assert on_ground is False
        assert landed is False
        assert ent.y == plat.rect.bottom
        assert ent.vy == 0

    def test_no_vertical_collision(self, sample_platforms):
        """测试无垂直碰撞情况。"""
        from entities.base import resolve_vertical_collision
        ent = MockEntity(10, 100, 28, 38, vy=1)
        orig_y = ent.y
        on_ground, landed = resolve_vertical_collision(ent, sample_platforms, was_on_ground=False)
        assert on_ground is False
        assert landed is False

    def test_already_on_ground_not_landed_again(self, make_platform):
        """测试已在地面上时 not 再次触发 landed。"""
        from entities.base import resolve_vertical_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(120, 500 - 38 + 1, 28, 38, vy=0)
        on_ground, landed = resolve_vertical_collision(ent, [plat], was_on_ground=True)
        assert on_ground is True
        assert landed is False

    def test_zero_velocity_sitting_on_platform(self, make_platform):
        """测试静止坐在平台上的情况。"""
        from entities.base import resolve_vertical_collision
        plat = make_platform(100, 500, 100, 40)
        ent = MockEntity(120, 500 - 38 + 1, 28, 38, vy=0)
        on_ground, landed = resolve_vertical_collision(ent, [plat], was_on_ground=False)
        assert on_ground is True
        assert landed is True

    def test_falling_through_gap_between_platforms(self, make_platform):
        """测试从平台间隙下落不触发碰撞。"""
        from entities.base import resolve_vertical_collision
        plat1 = make_platform(0, 500, 100, 40)
        plat2 = make_platform(200, 500, 100, 40)
        ent = MockEntity(150, 490, 28, 38, vy=5)
        orig_y = ent.y
        on_ground, landed = resolve_vertical_collision(ent, [plat1, plat2], was_on_ground=False)
        assert on_ground is False
        assert landed is False
        assert ent.y == orig_y

    def test_multiple_platforms_stack_landing(self, make_platform):
        """测试落在堆叠平台的最上层。"""
        from entities.base import resolve_vertical_collision
        plat1 = make_platform(100, 600, 100, 40)
        plat2 = make_platform(100, 500, 100, 20)
        ent = MockEntity(120, 490, 28, 38, vy=5)
        on_ground, landed = resolve_vertical_collision(ent, [plat1, plat2], was_on_ground=False)
        assert on_ground is True
        assert landed is True
        assert ent.y == plat2.rect.top - ent.height

    def test_empty_platform_list_vertical(self):
        """测试空平台列表不发生碰撞。"""
        from entities.base import resolve_vertical_collision
        ent = MockEntity(100, 500, 28, 38, vy=5)
        orig_y = ent.y
        orig_vy = ent.vy
        on_ground, landed = resolve_vertical_collision(ent, [], was_on_ground=False)
        assert on_ground is False
        assert landed is False
        assert ent.y == orig_y
        assert ent.vy == orig_vy
