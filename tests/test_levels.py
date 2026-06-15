# -*- coding: utf-8 -*-
"""
test_levels.py - 关卡系统模块测试

测试范围:
- LevelConfig 数据类字段完整性与默认值
- build_level_0/1/2 三个关卡构建函数的数据正确性
- get_level_config 关卡循环获取逻辑
- LevelLoader 关卡构建器实体生成
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
)
from levels import (
    LevelConfig,
    build_level_0, build_level_1, build_level_2,
    LEVEL_BUILDERS, get_level_config,
)


class TestLevelConfig:
    """LevelConfig 数据类测试。"""

    def test_init_required_fields(self):
        """测试必填字段初始化。"""
        cfg = LevelConfig(
            level_id=0,
            name="Test",
            description="Test level",
            spawn_x=100,
            spawn_y=200,
            ground_specs=[(0, 500, 200, 40)],
            floating_specs=[(100, 400, 80, 20)],
            coin_positions=[(150, 350)],
            ladder_specs=[(50, 300, 200)],
            portal_specs=[(300, 400, 1, 50, 400, 0)],
        )
        assert cfg.level_id == 0
        assert cfg.name == "Test"
        assert cfg.description == "Test level"
        assert cfg.spawn_x == 100
        assert cfg.spawn_y == 200
        assert cfg.ground_specs == [(0, 500, 200, 40)]
        assert cfg.floating_specs == [(100, 400, 80, 20)]
        assert cfg.coin_positions == [(150, 350)]
        assert cfg.ladder_specs == [(50, 300, 200)]
        assert cfg.portal_specs == [(300, 400, 1, 50, 400, 0)]

    def test_init_optional_defaults(self):
        """测试可选字段的默认值。"""
        cfg = LevelConfig(
            level_id=0, name="N", description="D",
            spawn_x=0, spawn_y=0,
            ground_specs=[], floating_specs=[], coin_positions=[],
            ladder_specs=[], portal_specs=[],
        )
        assert cfg.patrol_enemy_specs == []
        assert cfg.chase_enemy_specs == []
        assert cfg.ammo_pickup_specs == []
        assert cfg.sky_top == (100, 180, 255)
        assert cfg.sky_bottom == (200, 230, 255)
        assert cfg.has_stars is False
        assert cfg.star_count == 0
        assert cfg.has_sun is False
        assert cfg.has_moon is False
        assert cfg.ground_color == (80, 160, 60)
        assert cfg.dirt_color == (120, 80, 40)
        assert cfg.platform_color == (90, 70, 50)
        assert cfg.platform_top_color == (70, 150, 50)

    def test_init_optional_custom(self):
        """测试可选字段自定义值。"""
        cfg = LevelConfig(
            level_id=2, name="N2", description="D2",
            spawn_x=50, spawn_y=60,
            ground_specs=[], floating_specs=[], coin_positions=[],
            ladder_specs=[], portal_specs=[],
            patrol_enemy_specs=[([(0, 0)], True)],
            chase_enemy_specs=[(10, 20)],
            ammo_pickup_specs=[(30, 40)],
            has_stars=True, star_count=50, star_seed=123,
            has_sun=True, sun_color=(255, 200, 50), sun_pos=(0.5, 0.1),
            has_moon=True, moon_color=(240, 240, 220), moon_pos=(0.8, 0.1),
            sky_top=(10, 10, 40), sky_bottom=(30, 20, 80),
            mountain_color=(30, 20, 60), mountain_snow_color=(180, 180, 230),
            cloud_color=(80, 70, 120), cloud_alpha_inner=80, cloud_alpha_outer=100,
            ground_color=(40, 35, 60), dirt_color=(30, 25, 50),
            platform_color=(60, 50, 90), platform_top_color=(80, 70, 120),
        )
        assert cfg.patrol_enemy_specs == [([(0, 0)], True)]
        assert cfg.chase_enemy_specs == [(10, 20)]
        assert cfg.ammo_pickup_specs == [(30, 40)]
        assert cfg.has_stars is True
        assert cfg.star_count == 50
        assert cfg.star_seed == 123
        assert cfg.has_sun is True
        assert cfg.sun_color == (255, 200, 50)
        assert cfg.sun_pos == (0.5, 0.1)
        assert cfg.has_moon is True
        assert cfg.sky_top == (10, 10, 40)

    def test_field_mutability(self):
        """测试配置对象字段可修改。"""
        cfg = LevelConfig(
            level_id=0, name="N", description="D",
            spawn_x=0, spawn_y=0,
            ground_specs=[], floating_specs=[], coin_positions=[],
            ladder_specs=[], portal_specs=[],
        )
        cfg.level_id = 5
        cfg.name = "Modified"
        cfg.spawn_x = 999
        cfg.ground_specs.append((0, 0, 100, 20))
        assert cfg.level_id == 5
        assert cfg.name == "Modified"
        assert cfg.spawn_x == 999
        assert len(cfg.ground_specs) == 1


class TestBuildLevel0:
    """build_level_0 翠绿草原关卡测试。"""

    def test_level_0_basic_info(self):
        """测试关卡 0 基本信息。"""
        cfg = build_level_0()
        assert cfg.level_id == 0
        assert cfg.name == "翠绿草原"
        assert "第一关" in cfg.description
        assert cfg.spawn_x == PLAYER_SPAWN_X
        assert cfg.spawn_y == PLAYER_SPAWN_Y

    def test_level_0_platform_counts(self):
        """测试关卡 0 平台数量。"""
        cfg = build_level_0()
        assert len(cfg.ground_specs) == 7
        assert len(cfg.floating_specs) == 17

    def test_level_0_ground_specs_format(self):
        """测试关卡 0 地面规格格式。"""
        cfg = build_level_0()
        for spec in cfg.ground_specs:
            assert len(spec) == 4
            x, y, w, h = spec
            assert isinstance(x, int) and isinstance(y, int)
            assert w > 0 and h > 0
            assert y == SCREEN_HEIGHT - 40

    def test_level_0_floating_specs_format(self):
        """测试关卡 0 浮动平台规格格式。"""
        cfg = build_level_0()
        for spec in cfg.floating_specs:
            assert len(spec) == 4
            x, y, w, h = spec
            assert w > 0 and h > 0
            assert y < SCREEN_HEIGHT - 40

    def test_level_0_coins_count_and_format(self):
        """测试关卡 0 金币。"""
        cfg = build_level_0()
        assert len(cfg.coin_positions) == 17
        for pos in cfg.coin_positions:
            assert len(pos) == 2
            assert isinstance(pos[0], int) and isinstance(pos[1], int)

    def test_level_0_ladders_and_portals(self):
        """测试关卡 0 梯子和传送门。"""
        cfg = build_level_0()
        assert len(cfg.ladder_specs) == 6
        for spec in cfg.ladder_specs:
            assert len(spec) == 3
            x, y, h = spec
            assert h > 0
        assert len(cfg.portal_specs) == 3
        for spec in cfg.portal_specs:
            assert len(spec) == 6

    def test_level_0_enemies_and_ammo(self):
        """测试关卡 0 敌人和弹药拾取。"""
        cfg = build_level_0()
        assert len(cfg.patrol_enemy_specs) == 3
        assert len(cfg.chase_enemy_specs) == 2
        assert len(cfg.ammo_pickup_specs) == 4
        for path_points, loop_mode in cfg.patrol_enemy_specs:
            assert isinstance(path_points, list)
            assert len(path_points) >= 2
            assert isinstance(loop_mode, bool)
        for x, y in cfg.chase_enemy_specs:
            assert isinstance(x, int) and isinstance(y, int)

    def test_level_0_visual_settings(self):
        """测试关卡 0 视觉风格。"""
        cfg = build_level_0()
        assert cfg.has_sun is True
        assert cfg.has_stars is False
        assert cfg.has_moon is False
        assert cfg.sky_top == (100, 180, 255)
        assert cfg.sun_color == (255, 230, 100)


class TestBuildLevel1:
    """build_level_1 日落沙丘关卡测试。"""

    def test_level_1_basic_info(self):
        """测试关卡 1 基本信息。"""
        cfg = build_level_1()
        assert cfg.level_id == 1
        assert cfg.name == "日落沙丘"
        assert "第二关" in cfg.description

    def test_level_1_required_coins_portal(self):
        """测试关卡 1 终点传送门需要 5 枚金币。"""
        cfg = build_level_1()
        final_portal = cfg.portal_specs[-1]
        assert final_portal[2] == 2
        assert final_portal[5] == 5

    def test_level_1_counts(self):
        """测试关卡 1 各类实体数量。"""
        cfg = build_level_1()
        assert len(cfg.ground_specs) == 8
        assert len(cfg.floating_specs) == 17
        assert len(cfg.coin_positions) == 17
        assert len(cfg.ladder_specs) == 6
        assert len(cfg.portal_specs) == 2
        assert len(cfg.patrol_enemy_specs) == 4
        assert len(cfg.chase_enemy_specs) == 3
        assert len(cfg.ammo_pickup_specs) == 4

    def test_level_1_visual_settings(self):
        """测试关卡 1 暖色调视觉。"""
        cfg = build_level_1()
        assert cfg.has_sun is True
        assert cfg.has_stars is False
        assert cfg.sky_top[0] > 200
        assert cfg.sky_top[1] < 200
        assert cfg.sun_pos == (0.5, 0.18)


class TestBuildLevel2:
    """build_level_2 星空之巅关卡测试。"""

    def test_level_2_basic_info(self):
        """测试关卡 2 基本信息。"""
        cfg = build_level_2()
        assert cfg.level_id == 2
        assert cfg.name == "星空之巅"
        assert "第三关" in cfg.description

    def test_level_2_required_coins_final(self):
        """测试关卡 2 终点传送门需要 10 枚金币。"""
        cfg = build_level_2()
        final_portal = cfg.portal_specs[-1]
        assert final_portal[2] == 0
        assert final_portal[5] == 10

    def test_level_2_counts(self):
        """测试关卡 2 各类实体数量。"""
        cfg = build_level_2()
        assert len(cfg.ground_specs) == 9
        assert len(cfg.floating_specs) == 19
        assert len(cfg.coin_positions) == 19
        assert len(cfg.ladder_specs) == 7
        assert len(cfg.portal_specs) == 3
        assert len(cfg.patrol_enemy_specs) == 4
        assert len(cfg.chase_enemy_specs) == 4
        assert len(cfg.ammo_pickup_specs) == 5

    def test_level_2_visual_settings(self):
        """测试关卡 2 夜晚星空视觉。"""
        cfg = build_level_2()
        assert cfg.has_stars is True
        assert cfg.star_count == 80
        assert cfg.star_seed == 789
        assert cfg.has_moon is True
        assert cfg.has_sun is False
        assert cfg.sky_top[0] <= 30
        assert cfg.sky_top[1] <= 30


class TestGetLevelConfig:
    """get_level_config 循环获取逻辑测试。"""

    def test_level_builders_list_length(self):
        """测试 LEVEL_BUILDERS 包含 3 个构建函数。"""
        assert len(LEVEL_BUILDERS) == 3

    def test_valid_level_ids(self):
        """测试合法关卡编号。"""
        cfg0 = get_level_config(0)
        cfg1 = get_level_config(1)
        cfg2 = get_level_config(2)
        assert cfg0.level_id == 0
        assert cfg1.level_id == 1
        assert cfg2.level_id == 2

    def test_wraparound_positive(self):
        """测试超出范围的正编号循环返回。"""
        cfg3 = get_level_config(3)
        cfg4 = get_level_config(4)
        cfg5 = get_level_config(5)
        cfg6 = get_level_config(6)
        assert cfg3.level_id == 0
        assert cfg4.level_id == 1
        assert cfg5.level_id == 2
        assert cfg6.level_id == 0

    def test_wraparound_negative(self):
        """测试负编号循环返回。"""
        cfg_neg1 = get_level_config(-1)
        cfg_neg2 = get_level_config(-2)
        cfg_neg3 = get_level_config(-3)
        assert cfg_neg1.level_id == 2
        assert cfg_neg2.level_id == 1
        assert cfg_neg3.level_id == 0

    def test_wraparound_large_ids(self):
        """测试很大的关卡编号。"""
        cfg_100 = get_level_config(100)
        cfg_999 = get_level_config(999)
        assert cfg_100.level_id == 100 % 3
        assert cfg_999.level_id == 999 % 3

    def test_new_instance_each_call(self):
        """测试每次调用返回独立实例。"""
        cfg_a = get_level_config(0)
        cfg_b = get_level_config(0)
        assert cfg_a is not cfg_b
        cfg_a.name = "Modified"
        assert cfg_b.name == "翠绿草原"
