# -*- coding: utf-8 -*-
"""
audio.py - 游戏音频系统模块

提供完整的游戏音频管理，包括：
- 背景音乐（BGM）的播放、暂停、继续、循环控制
- 多种游戏音效的独立触发
- 背景音乐和音效的独立音量调节
- 使用程序化音频生成，无需外部音频文件，确保跨平台兼容性
- 优雅的降级处理（无头模式/音频初始化失败时静默）
"""

import math
import struct
import random
import pygame

from config import (
    HEADLESS,
    AUDIO_SAMPLE_RATE,
    AUDIO_BGM_VOLUME_DEFAULT,
    AUDIO_SFX_VOLUME_DEFAULT,
    AUDIO_BGM_FADE_MS,
)


def _generate_tone(frequency, duration, volume=0.5, sample_rate=44100,
                   waveform="sine", decay=0.0):
    """
    程序化生成单音调音频数据。

    Args:
        frequency: 频率（Hz）
        duration: 持续时间（秒）
        volume: 音量 0.0~1.0
        sample_rate: 采样率
        waveform: 波形类型 "sine", "square", "sawtooth", "triangle"
        decay: 指数衰减系数（0 表示无衰减）

    Returns:
        bytes: 16-bit 单声道 PCM 音频数据
    """
    n_samples = int(duration * sample_rate)
    buf = bytearray()
    amp = int(32767 * volume)

    for i in range(n_samples):
        t = i / sample_rate
        phase = 2.0 * math.pi * frequency * t

        if waveform == "sine":
            sample = math.sin(phase)
        elif waveform == "square":
            sample = 1.0 if math.sin(phase) >= 0 else -1.0
        elif waveform == "sawtooth":
            sample = 2.0 * (t * frequency - math.floor(0.5 + t * frequency))
        elif waveform == "triangle":
            sample = 2.0 * abs(2.0 * (t * frequency - math.floor(t * frequency + 0.5))) - 1.0
        else:
            sample = math.sin(phase)

        if decay > 0:
            sample *= math.exp(-decay * t)

        sample = max(-1.0, min(1.0, sample))
        val = int(amp * sample)
        buf += struct.pack("<h", val)

    return bytes(buf)


def _generate_chord(frequencies, duration, volume=0.5, sample_rate=44100,
                    waveform="sine", decay=0.0):
    """
    生成和弦（多个频率叠加）。

    Args:
        frequencies: 频率列表
        duration: 持续时间（秒）
        volume: 总音量
        sample_rate: 采样率
        waveform: 波形类型
        decay: 衰减系数

    Returns:
        bytes: 16-bit 单声道 PCM 音频数据
    """
    n_samples = int(duration * sample_rate)
    buf = bytearray()
    amp = int(32767 * volume / max(1, len(frequencies)))

    for i in range(n_samples):
        t = i / sample_rate
        mixed = 0.0
        for freq in frequencies:
            phase = 2.0 * math.pi * freq * t
            mixed += math.sin(phase)
        mixed /= len(frequencies)
        if decay > 0:
            mixed *= math.exp(-decay * t)
        mixed = max(-1.0, min(1.0, mixed))
        val = int(amp * mixed)
        buf += struct.pack("<h", val)

    return bytes(buf)


def _generate_melody(notes, tempo=120, volume=0.4, sample_rate=44100,
                     waveform="sine"):
    """
    生成旋律序列。

    Args:
        notes: 音符列表 [(frequency, beats), ...]，frequency=None 表示休止符
        tempo: 每分钟节拍数
        volume: 音量
        sample_rate: 采样率
        waveform: 波形类型

    Returns:
        bytes: 16-bit 单声道 PCM 音频数据
    """
    beat_duration = 60.0 / tempo
    buf = bytearray()

    for freq, beats in notes:
        duration = beats * beat_duration
        if freq is None:
            n_samples = int(duration * sample_rate)
            buf += b"\x00\x00" * n_samples
        else:
            buf += _generate_tone(freq, duration, volume, sample_rate,
                                  waveform, decay=3.0)

    return bytes(buf)


NOTE_FREQ = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
    "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C6": 1046.50,
}


def _make_bgm_level0():
    """生成第1关（翠绿草原）的背景音乐：欢快明亮的 C 大调旋律。"""
    nf = NOTE_FREQ
    melody = [
        (nf["C5"], 0.5), (nf["E5"], 0.5), (nf["G5"], 0.5), (nf["E5"], 0.5),
        (nf["C5"], 0.5), (nf["E5"], 0.5), (nf["G5"], 1.0),
        (nf["A4"], 0.5), (nf["C5"], 0.5), (nf["E5"], 0.5), (nf["C5"], 0.5),
        (nf["A4"], 0.5), (nf["C5"], 0.5), (nf["E5"], 1.0),
        (nf["F5"], 0.5), (nf["A5"], 0.5), (nf["C6"], 0.5), (nf["A5"], 0.5),
        (nf["F5"], 0.5), (nf["E5"], 0.5), (nf["D5"], 0.5), (nf["C5"], 0.5),
        (nf["D5"], 0.5), (nf["E5"], 0.5), (nf["F5"], 0.5), (nf["E5"], 0.5),
        (nf["D5"], 0.5), (nf["C5"], 1.0),
    ]
    bass = [
        (nf["C4"], 1.0), (nf["G4"], 1.0), (nf["A4"], 1.0), (nf["E4"], 1.0),
        (nf["F4"], 1.0), (nf["C4"], 1.0), (nf["G4"], 1.0), (nf["C4"], 1.0),
    ] * 2

    melody_data = _generate_melody(melody, tempo=132, volume=0.25, waveform="triangle")
    bass_data = _generate_melody(bass, tempo=66, volume=0.2, waveform="sine")

    m_len = len(melody_data)
    b_len = len(bass_data)
    total = max(m_len, b_len)
    melody_data += b"\x00\x00" * ((total - m_len) // 2)
    bass_data += b"\x00\x00" * ((total - b_len) // 2)

    mixed = bytearray()
    step = 2
    for i in range(0, total, step):
        m_val = struct.unpack("<h", melody_data[i:i + step])[0]
        b_val = struct.unpack("<h", bass_data[i:i + step])[0]
        mix = max(-32767, min(32767, (m_val + b_val) // 2))
        mixed += struct.pack("<h", mix)
    return bytes(mixed), AUDIO_SAMPLE_RATE


def _make_bgm_level1():
    """生成第2关（日落沙丘）的背景音乐：温暖的沙漠风格。"""
    nf = NOTE_FREQ
    melody = [
        (nf["E5"], 0.75), (nf["D5"], 0.25), (nf["C5"], 0.5), (nf["D5"], 0.5),
        (nf["E5"], 1.0), (nf["E5"], 0.5), (nf["D5"], 0.5),
        (nf["E5"], 0.75), (nf["F5"], 0.25), (nf["G5"], 0.5), (nf["F5"], 0.5),
        (nf["E5"], 1.0), (nf["D5"], 0.5), (nf["C5"], 0.5),
        (nf["D5"], 0.5), (nf["E5"], 0.5), (nf["D5"], 0.5), (nf["C5"], 0.5),
        (nf["A4"], 1.0), (None, 0.5), (nf["C5"], 0.5),
        (nf["D5"], 0.5), (nf["E5"], 0.5), (nf["F5"], 0.5), (nf["E5"], 0.5),
        (nf["D5"], 0.5), (nf["C5"], 1.0),
    ]
    bass = [
        (nf["A4"], 1.0), (nf["E4"], 1.0), (nf["D4"], 1.0), (nf["A4"], 1.0),
        (nf["G4"], 1.0), (nf["D4"], 1.0), (nf["A4"], 1.0), (nf["E4"], 1.0),
    ] * 2

    melody_data = _generate_melody(melody, tempo=100, volume=0.28, waveform="sine")
    bass_data = _generate_melody(bass, tempo=50, volume=0.22, waveform="triangle")

    m_len = len(melody_data)
    b_len = len(bass_data)
    total = max(m_len, b_len)
    melody_data += b"\x00\x00" * ((total - m_len) // 2)
    bass_data += b"\x00\x00" * ((total - b_len) // 2)

    mixed = bytearray()
    step = 2
    for i in range(0, total, step):
        m_val = struct.unpack("<h", melody_data[i:i + step])[0]
        b_val = struct.unpack("<h", bass_data[i:i + step])[0]
        mix = max(-32767, min(32767, (m_val + b_val) // 2))
        mixed += struct.pack("<h", mix)
    return bytes(mixed), AUDIO_SAMPLE_RATE


def _make_bgm_level2():
    """生成第3关（星空之巅）的背景音乐：神秘的夜空氛围。"""
    nf = NOTE_FREQ
    melody = [
        (nf["C5"], 1.0), (nf["E5"], 0.5), (nf["G5"], 0.5),
        (nf["B4"], 1.0), (nf["D5"], 0.5), (nf["F5"], 0.5),
        (nf["A4"], 1.0), (nf["C5"], 0.5), (nf["E5"], 0.5),
        (nf["G4"], 1.0), (nf["B4"], 0.5), (nf["D5"], 0.5),
        (nf["F5"], 0.75), (nf["E5"], 0.25), (nf["D5"], 0.5), (nf["C5"], 0.5),
        (nf["B4"], 1.0), (nf["A4"], 0.5), (nf["G4"], 0.5),
        (nf["A4"], 0.5), (nf["C5"], 0.5), (nf["E5"], 0.5), (nf["G5"], 0.5),
        (nf["A5"], 1.0), (nf["G5"], 0.5), (nf["E5"], 0.5),
        (nf["C5"], 0.5), (nf["D5"], 0.5), (nf["E5"], 0.5), (nf["D5"], 0.5),
        (nf["C5"], 1.5),
    ]
    bass = [
        (nf["C4"], 2.0), (nf["A4"], 2.0), (nf["F4"], 2.0), (nf["G4"], 2.0),
        (nf["E4"], 2.0), (nf["D4"], 2.0), (nf["C4"], 2.0), (nf["G4"], 2.0),
    ]

    melody_data = _generate_melody(melody, tempo=80, volume=0.25, waveform="sine")
    bass_data = _generate_melody(bass, tempo=40, volume=0.2, waveform="triangle")

    m_len = len(melody_data)
    b_len = len(bass_data)
    total = max(m_len, b_len)
    melody_data += b"\x00\x00" * ((total - m_len) // 2)
    bass_data += b"\x00\x00" * ((total - b_len) // 2)

    mixed = bytearray()
    step = 2
    for i in range(0, total, step):
        m_val = struct.unpack("<h", melody_data[i:i + step])[0]
        b_val = struct.unpack("<h", bass_data[i:i + step])[0]
        mix = max(-32767, min(32767, (m_val + b_val) // 2))
        mixed += struct.pack("<h", mix)
    return bytes(mixed), AUDIO_SAMPLE_RATE


def _make_sfx_jump():
    """生成跳跃音效：短促上升音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C5"], 0.06), (nf["E5"], 0.08), (nf["G5"], 0.1),
    ]
    return _generate_melody(notes, tempo=180, volume=0.4, waveform="square")


def _make_sfx_double_jump():
    """生成二段跳音效：更高的上升音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.05), (nf["G5"], 0.07), (nf["C6"], 0.1),
    ]
    return _generate_melody(notes, tempo=200, volume=0.4, waveform="square")


def _make_sfx_land():
    """生成落地音效：短促低音。"""
    return _generate_tone(
        frequency=120, duration=0.12, volume=0.45,
        waveform="square", decay=15.0
    )


def _make_sfx_coin():
    """生成金币收集音效：清脆的双音。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.05), (nf["C6"], 0.15),
    ]
    return _generate_melody(notes, tempo=240, volume=0.45, waveform="square")


def _make_sfx_portal():
    """生成传送门音效：神秘的和弦滑音。"""
    nf = NOTE_FREQ
    data1 = _generate_chord(
        [nf["C5"], nf["E5"], nf["G5"]], 0.1, 0.3, decay=5.0
    )
    data2 = _generate_chord(
        [nf["E5"], nf["G5"], nf["C6"]], 0.2, 0.3, decay=5.0
    )
    return data1 + data2


def _make_sfx_death():
    """生成死亡音效：下降的悲哀音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.12), (nf["C5"], 0.12), (nf["A4"], 0.15), (nf["E4"], 0.25),
    ]
    return _generate_melody(notes, tempo=120, volume=0.45, waveform="sawtooth")


def _make_sfx_menu_click():
    """生成菜单点击音效：清脆的短音。"""
    return _generate_tone(
        frequency=880, duration=0.06, volume=0.35,
        waveform="square", decay=20.0
    )


def _make_sfx_melee_swing():
    """生成近战挥砍音效：短促的风声。"""
    nf = NOTE_FREQ
    notes = [
        (nf["G4"], 0.03), (nf["C5"], 0.04), (nf["E5"], 0.05),
    ]
    return _generate_melody(notes, tempo=240, volume=0.4, waveform="sawtooth")


def _make_sfx_ranged_shot():
    """生成远程射击音效：短促的爆裂声。"""
    return _generate_tone(
        frequency=440, duration=0.08, volume=0.45,
        waveform="square", decay=30.0
    )


def _make_sfx_hit_impact():
    """生成命中反馈音效：沉闷的打击声。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C4"], 0.06), (nf["E4"], 0.08),
    ]
    return _generate_melody(notes, tempo=200, volume=0.5, waveform="square")


def _make_sfx_enemy_hit():
    """生成敌人受击音效。"""
    return _generate_tone(
        frequency=200, duration=0.1, volume=0.4,
        waveform="sawtooth", decay=20.0
    )


def _make_sfx_reload():
    """生成换弹音效。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E4"], 0.06), (nf["G4"], 0.08), (nf["C5"], 0.1),
    ]
    return _generate_melody(notes, tempo=160, volume=0.35, waveform="triangle")


def _make_sfx_ammo_pickup():
    """生成弹药拾取音效。"""
    nf = NOTE_FREQ
    notes = [
        (nf["G5"], 0.05), (nf["C6"], 0.08),
    ]
    return _generate_melody(notes, tempo=220, volume=0.4, waveform="square")


def _make_sfx_level_complete():
    """生成关卡完成音效：胜利旋律。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C5"], 0.12), (nf["E5"], 0.12), (nf["G5"], 0.12),
        (nf["C6"], 0.25), (nf["G5"], 0.12), (nf["C6"], 0.35),
    ]
    return _generate_melody(notes, tempo=160, volume=0.45, waveform="square")


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
        sfx_generators = {
            self.SFX_JUMP: _make_sfx_jump,
            self.SFX_DOUBLE_JUMP: _make_sfx_double_jump,
            self.SFX_LAND: _make_sfx_land,
            self.SFX_COIN: _make_sfx_coin,
            self.SFX_PORTAL: _make_sfx_portal,
            self.SFX_DEATH: _make_sfx_death,
            self.SFX_MENU_CLICK: _make_sfx_menu_click,
            self.SFX_LEVEL_COMPLETE: _make_sfx_level_complete,
            self.SFX_MELEE_SWING: _make_sfx_melee_swing,
            self.SFX_RANGED_SHOT: _make_sfx_ranged_shot,
            self.SFX_HIT_IMPACT: _make_sfx_hit_impact,
            self.SFX_ENEMY_HIT: _make_sfx_enemy_hit,
            self.SFX_RELOAD: _make_sfx_reload,
            self.SFX_AMMO_PICKUP: _make_sfx_ammo_pickup,
        }

        for name, gen in sfx_generators.items():
            try:
                audio_bytes = gen()
                sound = self._bytes_to_sound(audio_bytes)
                if sound:
                    self._sfx_sounds[name] = sound
            except Exception:
                pass

        bgm_generators = [_make_bgm_level0, _make_bgm_level1, _make_bgm_level2]
        for i, gen in enumerate(bgm_generators):
            try:
                audio_bytes, sample_rate = gen()
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
