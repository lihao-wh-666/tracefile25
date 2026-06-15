# -*- coding: utf-8 -*-
"""
audio/manager.py - 音频管理器

统一管理背景音乐和所有音效，提供音量控制接口。
"""

import pygame

from config import (
    HEADLESS,
    AUDIO_SAMPLE_RATE,
    AUDIO_BGM_VOLUME_DEFAULT,
    AUDIO_SFX_VOLUME_DEFAULT,
    AUDIO_BGM_FADE_MS,
)
from audio.bgm import generate_bgm
from audio.sfx import generate_sfx


class AudioManager:
    """
    游戏音频管理器。

    统一管理背景音乐和所有音效，提供音量控制接口。

    属性:
        enabled: 音频系统是否可用
        bgm_volume: 背景音乐音量 0.0~1.0
        sfx_volume: 音效音量 0.0~1.0
    """

    SFX_JUMP = "jump"
    SFX_DOUBLE_JUMP = "double_jump"
    SFX_LAND = "land"
    SFX_COIN = "coin"
    SFX_PORTAL = "portal"
    SFX_DEATH = "death"
    SFX_MENU_CLICK = "menu_click"
    SFX_LEVEL_COMPLETE = "level_complete"
    SFX_MELEE_SWING = "melee_swing"
    SFX_RANGED_SHOT = "ranged_shot"
    SFX_HIT_IMPACT = "hit_impact"
    SFX_ENEMY_HIT = "enemy_hit"
    SFX_RELOAD = "reload"
    SFX_AMMO_PICKUP = "ammo_pickup"

    def __init__(self):
        self.enabled = False
        self._mixer_initialized = False
        self.bgm_volume = AUDIO_BGM_VOLUME_DEFAULT
        self.sfx_volume = AUDIO_SFX_VOLUME_DEFAULT
        self._current_bgm_name = None
        self._bgm_sound = None
        self._bgm_channel = None
        self._sfx_sounds = {}
        self._bgm_cache = {}
        self._sfx_channels = []
        self._max_sfx_channels = 8

        self._initialize()

    def _initialize(self):
        """初始化 pygame.mixer 音频系统，失败时静默降级。"""
        if HEADLESS:
            return

        try:
            pygame.mixer.pre_init(
                frequency=AUDIO_SAMPLE_RATE,
                size=-16,
                channels=1,
                buffer=512,
            )
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_initialized = pygame.mixer.get_init() is not None
        except pygame.error:
            self._mixer_initialized = False

        if not self._mixer_initialized:
            return

        try:
            num_channels = pygame.mixer.get_num_channels()
            if num_channels < self._max_sfx_channels:
                pygame.mixer.set_num_channels(self._max_sfx_channels + 1)
            self._sfx_channels = [
                pygame.mixer.Channel(i)
                for i in range(1, min(self._max_sfx_channels + 1,
                                      pygame.mixer.get_num_channels()))
            ]
            self._bgm_channel = pygame.mixer.Channel(0)
        except (pygame.error, IndexError, OSError):
            self._mixer_initialized = False
            return

        self._build_sound_cache()
        self.enabled = True

    def _build_sound_cache(self):
        """预生成所有音效和背景音乐并缓存。"""
        sfx_names = [
            self.SFX_JUMP,
            self.SFX_DOUBLE_JUMP,
            self.SFX_LAND,
            self.SFX_COIN,
            self.SFX_PORTAL,
            self.SFX_DEATH,
            self.SFX_MENU_CLICK,
            self.SFX_LEVEL_COMPLETE,
            self.SFX_MELEE_SWING,
            self.SFX_RANGED_SHOT,
            self.SFX_HIT_IMPACT,
            self.SFX_ENEMY_HIT,
            self.SFX_RELOAD,
            self.SFX_AMMO_PICKUP,
        ]

        for name in sfx_names:
            try:
                audio_bytes = generate_sfx(name)
                sound = self._bytes_to_sound(audio_bytes)
                if sound:
                    self._sfx_sounds[name] = sound
            except Exception:
                pass

        for i in range(3):
            try:
                audio_bytes, sample_rate = generate_bgm(i)
                sound = self._bytes_to_sound(audio_bytes, sample_rate)
                if sound:
                    self._bgm_cache[f"level_{i}"] = sound
            except Exception:
                pass

    def _bytes_to_sound(self, audio_bytes, sample_rate=None):
        """将原始 PCM 字节数据转换为 pygame.mixer.Sound。"""
        if sample_rate is None:
            sample_rate = AUDIO_SAMPLE_RATE
        try:
            if not audio_bytes:
                return None
            sound = pygame.mixer.Sound(
                buffer=audio_bytes
            )
            return sound
        except (pygame.error, ValueError):
            return None

    def play_bgm(self, name="level_0", loops=-1):
        """
        播放指定背景音乐。

        Args:
            name: 背景音乐名称，如 "level_0", "level_1", "level_2"
            loops: 循环次数，-1 表示无限循环
        """
        if not self.enabled or not self._mixer_initialized:
            return

        if self._current_bgm_name == name and self._bgm_channel.get_busy():
            return

        if name not in self._bgm_cache:
            return

        if self._bgm_channel.get_busy():
            self._bgm_channel.fadeout(AUDIO_BGM_FADE_MS)
            pygame.time.delay(AUDIO_BGM_FADE_MS)

        self._bgm_sound = self._bgm_cache[name]
        self._bgm_sound.set_volume(self.bgm_volume)
        self._bgm_channel.play(self._bgm_sound, loops=loops,
                               fade_ms=AUDIO_BGM_FADE_MS)
        self._current_bgm_name = name

    def pause_bgm(self):
        """暂停当前背景音乐。"""
        if self.enabled and self._bgm_channel:
            self._bgm_channel.pause()

    def resume_bgm(self):
        """继续播放暂停的背景音乐。"""
        if self.enabled and self._bgm_channel:
            self._bgm_channel.unpause()

    def stop_bgm(self, fade=True):
        """
        停止背景音乐播放。

        Args:
            fade: 是否使用淡出效果
        """
        if self.enabled and self._bgm_channel:
            if fade and self._bgm_channel.get_busy():
                self._bgm_channel.fadeout(AUDIO_BGM_FADE_MS)
            else:
                self._bgm_channel.stop()
        self._current_bgm_name = None

    def is_bgm_playing(self):
        """检查背景音乐是否正在播放。"""
        if not self.enabled or not self._bgm_channel:
            return False
        return self._bgm_channel.get_busy()

    def play_sfx(self, name):
        """
        播放指定音效。

        Args:
            name: 音效名称（使用 AudioManager.SFX_* 常量）
        """
        if not self.enabled or not self._mixer_initialized:
            return

        sound = self._sfx_sounds.get(name)
        if sound is None:
            return

        sound.set_volume(self.sfx_volume)
        for ch in self._sfx_channels:
            if not ch.get_busy():
                ch.play(sound)
                return
        self._sfx_channels[0].play(sound)

    def set_bgm_volume(self, volume):
        """
        设置背景音乐音量。

        Args:
            volume: 音量值 0.0~1.0
        """
        volume = max(0.0, min(1.0, float(volume)))
        self.bgm_volume = volume
        if self._bgm_sound:
            self._bgm_sound.set_volume(volume)

    def set_sfx_volume(self, volume):
        """
        设置音效音量。

        Args:
            volume: 音量值 0.0~1.0
        """
        volume = max(0.0, min(1.0, float(volume)))
        self.sfx_volume = volume
        for sound in self._sfx_sounds.values():
            sound.set_volume(volume)

    def stop_all_sfx(self):
        """停止所有正在播放的音效。"""
        if self.enabled:
            for ch in self._sfx_channels:
                ch.stop()

    def shutdown(self):
        """关闭音频系统，释放资源。"""
        if self._mixer_initialized:
            try:
                self.stop_bgm(fade=False)
                self.stop_all_sfx()
            except Exception:
                pass
