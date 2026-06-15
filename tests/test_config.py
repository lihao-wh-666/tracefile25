# -*- coding: utf-8 -*-
"""
test_config.py - 配置模块单元测试

测试目标:
1. 环境变量整数读取 (get_env_int) - 正常值、边界值、异常值
2. 环境变量布尔读取 (get_env_bool) - 各种布尔字符串表示
3. 游戏常量的有效性验证 - 物理参数、尺寸参数等
4. 颜色配置格式正确性
"""

import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetEnvInt:
    """环境变量整数读取函数测试类。"""

    def test_valid_int_value(self, monkeypatch):
        """测试正常读取有效整数值。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_INT", "123")
        assert get_env_int("TEST_INT", 0) == 123

    def test_zero_value(self, monkeypatch):
        """测试读取零值。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_INT", "0")
        assert get_env_int("TEST_INT", -1) == 0

    def test_negative_value(self, monkeypatch):
        """测试读取负整数值。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_INT", "-456")
        assert get_env_int("TEST_INT", 0) == -456

    def test_missing_env_uses_default(self):
        """测试环境变量不存在时返回默认值。"""
        from config import get_env_int
        if "TEST_MISSING" in os.environ:
            del os.environ["TEST_MISSING"]
        assert get_env_int("TEST_MISSING", 999) == 999

    def test_invalid_value_uses_default(self, monkeypatch):
        """测试非数字字符串时返回默认值。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_BAD", "not_a_number")
        assert get_env_int("TEST_BAD", 42) == 42

    def test_empty_string_uses_default(self, monkeypatch):
        """测试空字符串时返回默认值。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_EMPTY", "")
        assert get_env_int("TEST_EMPTY", 7) == 7

    def test_float_value_uses_default(self, monkeypatch):
        """测试浮点数字符串时返回默认值（不自动转换）。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_FLOAT", "3.14")
        assert get_env_int("TEST_FLOAT", 100) == 100

    def test_whitespace_value(self, monkeypatch):
        """测试带空白字符的数字字符串。"""
        from config import get_env_int
        monkeypatch.setenv("TEST_SPACE", "  789  ")
        result = get_env_int("TEST_SPACE", 0)
        assert result == 0 or result == 789


class TestGetEnvBool:
    """环境变量布尔读取函数测试类。"""

    @pytest.mark.parametrize("true_val", [
        "1", "true", "TRUE", "True", "yes", "YES", "y", "on", "ON"
    ])
    def test_true_values(self, monkeypatch, true_val):
        """测试各种表示真值的字符串。"""
        from config import get_env_bool
        monkeypatch.setenv("TEST_BOOL", true_val)
        assert get_env_bool("TEST_BOOL", False) is True

    @pytest.mark.parametrize("false_val", [
        "0", "false", "FALSE", "False", "no", "NO", "n", "off", "OFF"
    ])
    def test_false_values(self, monkeypatch, false_val):
        """测试各种表示假值的字符串。"""
        from config import get_env_bool
        monkeypatch.setenv("TEST_BOOL", false_val)
        assert get_env_bool("TEST_BOOL", True) is False

    def test_missing_env_default_false(self):
        """测试环境变量不存在时默认返回 False。"""
        from config import get_env_bool
        if "TEST_MISSING" in os.environ:
            del os.environ["TEST_MISSING"]
        assert get_env_bool("TEST_MISSING") is False

    def test_missing_env_custom_default(self):
        """测试环境变量不存在时返回自定义默认值。"""
        from config import get_env_bool
        if "TEST_MISSING" in os.environ:
            del os.environ["TEST_MISSING"]
        assert get_env_bool("TEST_MISSING", True) is True

    def test_unknown_value_uses_default(self, monkeypatch):
        """测试未识别字符串时返回默认值。"""
        from config import get_env_bool
        monkeypatch.setenv("TEST_UNKNOWN", "maybe")
        assert get_env_bool("TEST_UNKNOWN", True) is True
        assert get_env_bool("TEST_UNKNOWN", False) is False

    def test_whitespace_unknown_value(self, monkeypatch):
        """测试带前后空白的字符串处理。"""
        from config import get_env_bool
        monkeypatch.setenv("TEST_WS", "  true  ")
        assert get_env_bool("TEST_WS", False) is True

    def test_empty_string_uses_default(self, monkeypatch):
        """测试空字符串时返回默认值。"""
        from config import get_env_bool
        monkeypatch.setenv("TEST_EMPTY", "")
        assert get_env_bool("TEST_EMPTY", True) is True


class TestGameConstants:
    """游戏常量有效性验证测试类。"""

    def test_screen_dimensions_positive(self):
        """测试屏幕尺寸为正整数。"""
        from config import SCREEN_WIDTH, SCREEN_HEIGHT
        assert SCREEN_WIDTH > 0
        assert SCREEN_HEIGHT > 0
        assert isinstance(SCREEN_WIDTH, int)
        assert isinstance(SCREEN_HEIGHT, int)

    def test_fps_positive(self):
        """测试帧率为正整数。"""
        from config import FPS
        assert FPS > 0
        assert isinstance(FPS, int)

    def test_physics_constants_valid(self):
        """测试物理参数的合理性。"""
        from config import (
            GRAVITY, JUMP_FORCE, MOVE_SPEED, MAX_FALL_SPEED,
            ACCELERATION, FRICTION,
        )
        assert GRAVITY > 0
        assert JUMP_FORCE < 0
        assert MOVE_SPEED > 0
        assert MAX_FALL_SPEED > 0
        assert ACCELERATION > 0
        assert 0 < FRICTION < 1

    def test_jump_parameters_valid(self):
        """测试跳跃参数的合理性。"""
        from config import (
            MAX_JUMP_COUNT, MULTI_JUMP_FORCE, MULTI_JUMP_INTERVAL_FRAMES,
            JUMP_BUFFER_FRAMES, COYOTE_TIME_FRAMES,
        )
        assert MAX_JUMP_COUNT >= 1
        assert MULTI_JUMP_FORCE < 0
        assert MULTI_JUMP_INTERVAL_FRAMES >= 0
        assert JUMP_BUFFER_FRAMES >= 0
        assert COYOTE_TIME_FRAMES >= 0

    def test_player_dimensions_valid(self):
        """测试玩家尺寸合理性。"""
        from config import PLAYER_SPAWN_X, PLAYER_SPAWN_Y, FALL_RESPAWN_Y, SCREEN_HEIGHT
        assert PLAYER_SPAWN_X >= 0
        assert PLAYER_SPAWN_Y >= 0
        assert FALL_RESPAWN_Y > SCREEN_HEIGHT

    def test_color_tuples_valid(self):
        """测试颜色元组格式正确性（RGB三通道，各值在0-255之间）。"""
        from config import (
            WHITE, BLACK, SKY_TOP, SKY_BOTTOM,
            PLAYER_BODY, COIN_COLOR,
        )
        colors_to_test = [WHITE, BLACK, SKY_TOP, SKY_BOTTOM, PLAYER_BODY, COIN_COLOR]
        for color in colors_to_test:
            assert isinstance(color, tuple), f"{color} 不是元组"
            assert len(color) == 3, f"{color} 长度应为3"
            for channel in color:
                assert 0 <= channel <= 255, f"{color} 通道值 {channel} 超出范围"

    def test_level_width_valid(self):
        """测试关卡宽度合理性。"""
        from config import LEVEL_WIDTH, SCREEN_WIDTH
        assert LEVEL_WIDTH >= SCREEN_WIDTH

    def test_total_levels_positive(self):
        """测试关卡总数为正整数。"""
        from config import TOTAL_LEVELS
        assert TOTAL_LEVELS > 0
        assert isinstance(TOTAL_LEVELS, int)

    def test_melee_parameters_valid(self):
        """测试近战参数合理性。"""
        from config import (
            MELEE_COOLDOWN_FRAMES, MELEE_RANGE, MELEE_DAMAGE,
            MELEE_DURATION_FRAMES, MELEE_HIT_FRAME,
        )
        assert MELEE_COOLDOWN_FRAMES >= 0
        assert MELEE_RANGE > 0
        assert MELEE_DAMAGE > 0
        assert MELEE_DURATION_FRAMES > 0
        assert 0 < MELEE_HIT_FRAME <= MELEE_DURATION_FRAMES

    def test_ranged_parameters_valid(self):
        """测试远程参数合理性。"""
        from config import (
            RANGED_COOLDOWN_FRAMES, RANGED_AMMO_MAX, RANGED_AMMO_INITIAL,
            RANGED_PROJECTILE_SPEED, RANGED_DAMAGE, RANGED_RELOAD_FRAMES,
            RANGED_AMMO_PICKUP_AMOUNT,
        )
        assert RANGED_COOLDOWN_FRAMES >= 0
        assert RANGED_AMMO_MAX > 0
        assert 0 <= RANGED_AMMO_INITIAL <= RANGED_AMMO_MAX
        assert RANGED_PROJECTILE_SPEED > 0
        assert RANGED_DAMAGE > 0
        assert RANGED_RELOAD_FRAMES >= 0
        assert RANGED_AMMO_PICKUP_AMOUNT > 0

    def test_enemy_parameters_valid(self):
        """测试敌人参数合理性。"""
        from config import (
            PATROL_ENEMY_WIDTH, PATROL_ENEMY_HEIGHT, PATROL_ENEMY_SPEED,
            PATROL_ENEMY_HP,
            CHASE_ENEMY_WIDTH, CHASE_ENEMY_HEIGHT, CHASE_ENEMY_SPEED,
            CHASE_ENEMY_HP, CHASE_ENEMY_CHASE_RANGE, CHASE_ENEMY_GIVE_UP_RANGE,
        )
        assert PATROL_ENEMY_WIDTH > 0
        assert PATROL_ENEMY_HEIGHT > 0
        assert PATROL_ENEMY_SPEED > 0
        assert PATROL_ENEMY_HP > 0

        assert CHASE_ENEMY_WIDTH > 0
        assert CHASE_ENEMY_HEIGHT > 0
        assert CHASE_ENEMY_SPEED > 0
        assert CHASE_ENEMY_HP > 0
        assert CHASE_ENEMY_GIVE_UP_RANGE >= CHASE_ENEMY_CHASE_RANGE

    def test_portal_parameters_valid(self):
        """测试传送门参数合理性。"""
        from config import PORTAL_WIDTH, PORTAL_HEIGHT, PORTAL_COOLDOWN_FRAMES
        assert PORTAL_WIDTH > 0
        assert PORTAL_HEIGHT > 0
        assert PORTAL_COOLDOWN_FRAMES >= 0


class TestAudioConstants:
    """音频配置常量测试类。"""

    def test_audio_sample_rate_positive(self):
        """测试采样率为正整数。"""
        from config import AUDIO_SAMPLE_RATE
        assert AUDIO_SAMPLE_RATE > 0

    def test_volume_defaults_in_range(self):
        """测试音量默认值在 0.0~1.0 范围内。"""
        from config import AUDIO_BGM_VOLUME_DEFAULT, AUDIO_SFX_VOLUME_DEFAULT
        assert 0.0 <= AUDIO_BGM_VOLUME_DEFAULT <= 1.0
        assert 0.0 <= AUDIO_SFX_VOLUME_DEFAULT <= 1.0

    def test_audio_fade_ms_non_negative(self):
        """测试音频淡出时间为非负数。"""
        from config import AUDIO_BGM_FADE_MS
        assert AUDIO_BGM_FADE_MS >= 0
