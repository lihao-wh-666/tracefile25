# -*- coding: utf-8 -*-
"""
audio/bgm.py - 背景音乐生成器

为每个关卡生成程序化背景音乐。
"""

from config import AUDIO_SAMPLE_RATE
from audio.generators import generate_melody, mix_audio
from audio.notes import NOTE_FREQ


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

    melody_data = generate_melody(melody, tempo=132, volume=0.25, waveform="triangle")
    bass_data = generate_melody(bass, tempo=66, volume=0.2, waveform="sine")

    mixed = mix_audio(melody_data, bass_data)
    return mixed, AUDIO_SAMPLE_RATE


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

    melody_data = generate_melody(melody, tempo=100, volume=0.28, waveform="sine")
    bass_data = generate_melody(bass, tempo=50, volume=0.22, waveform="triangle")

    mixed = mix_audio(melody_data, bass_data)
    return mixed, AUDIO_SAMPLE_RATE


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

    melody_data = generate_melody(melody, tempo=80, volume=0.25, waveform="sine")
    bass_data = generate_melody(bass, tempo=40, volume=0.2, waveform="triangle")

    mixed = mix_audio(melody_data, bass_data)
    return mixed, AUDIO_SAMPLE_RATE


BGM_GENERATORS = [_make_bgm_level0, _make_bgm_level1, _make_bgm_level2]


def generate_bgm(level_id):
    """
    根据关卡编号生成背景音乐。

    Args:
        level_id: 关卡编号（0, 1, 2）

    Returns:
        tuple: (audio_bytes, sample_rate)
    """
    level_id = level_id % len(BGM_GENERATORS)
    return BGM_GENERATORS[level_id]()
