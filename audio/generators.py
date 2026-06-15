# -*- coding: utf-8 -*-
"""
audio/generators.py - 程序化音频生成器

提供底层音频波形生成功能，支持多种波形类型、和弦和旋律。
"""

import math
import struct


def generate_tone(frequency, duration, volume=0.5, sample_rate=44100,
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


def generate_chord(frequencies, duration, volume=0.5, sample_rate=44100,
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


def generate_melody(notes, tempo=120, volume=0.4, sample_rate=44100,
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
            buf += generate_tone(freq, duration, volume, sample_rate,
                                 waveform, decay=3.0)

    return bytes(buf)


def mix_audio(data1, data2, sample_rate=44100):
    """
    混合两个音频数据流。

    Args:
        data1: 第一个音频数据
        data2: 第二个音频数据
        sample_rate: 采样率

    Returns:
        bytes: 混合后的音频数据
    """
    len1 = len(data1)
    len2 = len(data2)
    total = max(len1, len2)
    data1 += b"\x00\x00" * ((total - len1) // 2)
    data2 += b"\x00\x00" * ((total - len2) // 2)

    mixed = bytearray()
    step = 2
    for i in range(0, total, step):
        val1 = struct.unpack("<h", data1[i:i + step])[0]
        val2 = struct.unpack("<h", data2[i:i + step])[0]
        mix = max(-32767, min(32767, (val1 + val2) // 2))
        mixed += struct.pack("<h", mix)
    return bytes(mixed)
