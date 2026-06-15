# -*- coding: utf-8 -*-
"""
audio/notes.py - 音符频率定义

提供标准音阶的频率映射表。
"""


NOTE_FREQ = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
    "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C6": 1046.50,
}


def get_note(name, octave_shift=0):
    """
    获取指定音符的频率，支持八度位移。

    Args:
        name: 音符名称（如 "C4"）
        octave_shift: 八度位移（正数升高，负数降低）

    Returns:
        float: 频率值（Hz）
    """
    base_freq = NOTE_FREQ.get(name)
    if base_freq is None:
        return None
    return base_freq * (2 ** octave_shift)
