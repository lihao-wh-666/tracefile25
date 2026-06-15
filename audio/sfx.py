# -*- coding: utf-8 -*-
"""
audio/sfx.py - 音效生成器

生成各种游戏音效：跳跃、落地、收集金币、传送门等。
"""

from audio.generators import generate_tone, generate_melody, generate_chord
from audio.notes import NOTE_FREQ


def _make_sfx_jump():
    """生成跳跃音效：短促上升音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C5"], 0.06), (nf["E5"], 0.08), (nf["G5"], 0.1),
    ]
    return generate_melody(notes, tempo=180, volume=0.4, waveform="square")


def _make_sfx_double_jump():
    """生成二段跳音效：更高的上升音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.05), (nf["G5"], 0.07), (nf["C6"], 0.1),
    ]
    return generate_melody(notes, tempo=200, volume=0.4, waveform="square")


def _make_sfx_land():
    """生成落地音效：短促低音。"""
    return generate_tone(
        frequency=120, duration=0.12, volume=0.45,
        waveform="square", decay=15.0
    )


def _make_sfx_coin():
    """生成金币收集音效：清脆的双音。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.05), (nf["C6"], 0.15),
    ]
    return generate_melody(notes, tempo=240, volume=0.45, waveform="square")


def _make_sfx_portal():
    """生成传送门音效：神秘的和弦滑音。"""
    nf = NOTE_FREQ
    data1 = generate_chord(
        [nf["C5"], nf["E5"], nf["G5"]], 0.1, 0.3, decay=5.0
    )
    data2 = generate_chord(
        [nf["E5"], nf["G5"], nf["C6"]], 0.2, 0.3, decay=5.0
    )
    return data1 + data2


def _make_sfx_death():
    """生成死亡音效：下降的悲哀音调。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E5"], 0.12), (nf["C5"], 0.12), (nf["A4"], 0.15), (nf["E4"], 0.25),
    ]
    return generate_melody(notes, tempo=120, volume=0.45, waveform="sawtooth")


def _make_sfx_menu_click():
    """生成菜单点击音效：清脆的短音。"""
    return generate_tone(
        frequency=880, duration=0.06, volume=0.35,
        waveform="square", decay=20.0
    )


def _make_sfx_melee_swing():
    """生成近战挥砍音效：短促的风声。"""
    nf = NOTE_FREQ
    notes = [
        (nf["G4"], 0.03), (nf["C5"], 0.04), (nf["E5"], 0.05),
    ]
    return generate_melody(notes, tempo=240, volume=0.4, waveform="sawtooth")


def _make_sfx_ranged_shot():
    """生成远程射击音效：短促的爆裂声。"""
    return generate_tone(
        frequency=440, duration=0.08, volume=0.45,
        waveform="square", decay=30.0
    )


def _make_sfx_hit_impact():
    """生成命中反馈音效：沉闷的打击声。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C4"], 0.06), (nf["E4"], 0.08),
    ]
    return generate_melody(notes, tempo=200, volume=0.5, waveform="square")


def _make_sfx_enemy_hit():
    """生成敌人受击音效。"""
    return generate_tone(
        frequency=200, duration=0.1, volume=0.4,
        waveform="sawtooth", decay=20.0
    )


def _make_sfx_reload():
    """生成换弹音效。"""
    nf = NOTE_FREQ
    notes = [
        (nf["E4"], 0.06), (nf["G4"], 0.08), (nf["C5"], 0.1),
    ]
    return generate_melody(notes, tempo=160, volume=0.35, waveform="triangle")


def _make_sfx_ammo_pickup():
    """生成弹药拾取音效。"""
    nf = NOTE_FREQ
    notes = [
        (nf["G5"], 0.05), (nf["C6"], 0.08),
    ]
    return generate_melody(notes, tempo=220, volume=0.4, waveform="square")


def _make_sfx_level_complete():
    """生成关卡完成音效：胜利旋律。"""
    nf = NOTE_FREQ
    notes = [
        (nf["C5"], 0.12), (nf["E5"], 0.12), (nf["G5"], 0.12),
        (nf["C6"], 0.25), (nf["G5"], 0.12), (nf["C6"], 0.35),
    ]
    return generate_melody(notes, tempo=160, volume=0.45, waveform="square")


SFX_GENERATORS = {
    "jump": _make_sfx_jump,
    "double_jump": _make_sfx_double_jump,
    "land": _make_sfx_land,
    "coin": _make_sfx_coin,
    "portal": _make_sfx_portal,
    "death": _make_sfx_death,
    "menu_click": _make_sfx_menu_click,
    "level_complete": _make_sfx_level_complete,
    "melee_swing": _make_sfx_melee_swing,
    "ranged_shot": _make_sfx_ranged_shot,
    "hit_impact": _make_sfx_hit_impact,
    "enemy_hit": _make_sfx_enemy_hit,
    "reload": _make_sfx_reload,
    "ammo_pickup": _make_sfx_ammo_pickup,
}


def generate_sfx(name):
    """
    根据音效名称生成音效数据。

    Args:
        name: 音效名称（如 "jump", "coin"）

    Returns:
        bytes: 16-bit 单声道 PCM 音频数据，或 None 如果音效不存在
    """
    gen = SFX_GENERATORS.get(name)
    if gen is None:
        return None
    try:
        return gen()
    except Exception:
        return None
