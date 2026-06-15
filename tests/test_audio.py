# -*- coding: utf-8 -*-
"""
test_audio.py - 音频管理器测试

测试范围:
- AudioManager 初始化（HEADLESS 模式降级）
- 音量设置与钳制
- BGM/SFX 播放状态接口
- 常量定义完整性
"""

import os
import sys
import pytest

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from audio import AudioManager


@pytest.fixture(scope="session")
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


class TestAudioManager:
    """AudioManager 音频管理器测试。"""

    def test_sfx_constants_exist(self):
        """测试 SFX 常量定义。"""
        assert AudioManager.SFX_JUMP == "jump"
        assert AudioManager.SFX_DOUBLE_JUMP == "double_jump"
        assert AudioManager.SFX_LAND == "land"
        assert AudioManager.SFX_COIN == "coin"
        assert AudioManager.SFX_PORTAL == "portal"
        assert AudioManager.SFX_DEATH == "death"
        assert AudioManager.SFX_MENU_CLICK == "menu_click"
        assert AudioManager.SFX_LEVEL_COMPLETE == "level_complete"
        assert AudioManager.SFX_MELEE_SWING == "melee_swing"
        assert AudioManager.SFX_RANGED_SHOT == "ranged_shot"
        assert AudioManager.SFX_HIT_IMPACT == "hit_impact"
        assert AudioManager.SFX_ENEMY_HIT == "enemy_hit"
        assert AudioManager.SFX_RELOAD == "reload"
        assert AudioManager.SFX_AMMO_PICKUP == "ammo_pickup"

    def test_init_headless_mode(self, pygame_session):
        """测试 HEADLESS 模式初始化。"""
        am = AudioManager()
        assert am.enabled is False
        assert am._mixer_initialized is False
        from config import AUDIO_BGM_VOLUME_DEFAULT, AUDIO_SFX_VOLUME_DEFAULT
        assert am.bgm_volume == AUDIO_BGM_VOLUME_DEFAULT
        assert am.sfx_volume == AUDIO_SFX_VOLUME_DEFAULT
        assert am._current_bgm_name is None

    def test_set_bgm_volume_clamp(self, pygame_session):
        """测试 BGM 音量钳制。"""
        am = AudioManager()
        am.set_bgm_volume(0.5)
        assert abs(am.bgm_volume - 0.5) < 0.001
        am.set_bgm_volume(-1.0)
        assert abs(am.bgm_volume - 0.0) < 0.001
        am.set_bgm_volume(2.0)
        assert abs(am.bgm_volume - 1.0) < 0.001
        am.set_bgm_volume(0.0)
        assert abs(am.bgm_volume - 0.0) < 0.001
        am.set_bgm_volume(1.0)
        assert abs(am.bgm_volume - 1.0) < 0.001

    def test_set_sfx_volume_clamp(self, pygame_session):
        """测试 SFX 音量钳制。"""
        am = AudioManager()
        am.set_sfx_volume(0.7)
        assert abs(am.sfx_volume - 0.7) < 0.001
        am.set_sfx_volume(-5.0)
        assert abs(am.sfx_volume - 0.0) < 0.001
        am.set_sfx_volume(10.0)
        assert abs(am.sfx_volume - 1.0) < 0.001

    def test_is_bgm_playing_headless(self, pygame_session):
        """测试 HEADLESS 模式下无 BGM 播放。"""
        am = AudioManager()
        assert am.is_bgm_playing() is False

    def test_play_bgm_headless_no_op(self, pygame_session):
        """测试 HEADLESS 模式下播放 BGM 不报错。"""
        am = AudioManager()
        try:
            am.play_bgm("level_0")
            am.play_bgm("level_1", loops=3)
            am.play_bgm("nonexistent")
        except Exception as e:
            pytest.fail(f"play_bgm raised unexpectedly: {e}")

    def test_play_sfx_headless_no_op(self, pygame_session):
        """测试 HEADLESS 模式下播放 SFX 不报错。"""
        am = AudioManager()
        try:
            am.play_sfx(AudioManager.SFX_JUMP)
            am.play_sfx(AudioManager.SFX_COIN)
            am.play_sfx("nonexistent_sfx")
        except Exception as e:
            pytest.fail(f"play_sfx raised unexpectedly: {e}")

    def test_pause_resume_stop_bgm_headless(self, pygame_session):
        """测试 HEADLESS 模式下 BGM 控制不报错。"""
        am = AudioManager()
        try:
            am.pause_bgm()
            am.resume_bgm()
            am.stop_bgm()
            am.stop_bgm(fade=False)
        except Exception as e:
            pytest.fail(f"BGM control raised unexpectedly: {e}")

    def test_stop_all_sfx_headless(self, pygame_session):
        """测试 HEADLESS 模式下停止所有 SFX 不报错。"""
        am = AudioManager()
        try:
            am.stop_all_sfx()
        except Exception as e:
            pytest.fail(f"stop_all_sfx raised unexpectedly: {e}")

    def test_shutdown_headless(self, pygame_session):
        """测试 HEADLESS 模式下关闭不报错。"""
        am = AudioManager()
        try:
            am.shutdown()
        except Exception as e:
            pytest.fail(f"shutdown raised unexpectedly: {e}")
