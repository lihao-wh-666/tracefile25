# -*- coding: utf-8 -*-
"""
audio 包 - 游戏音频系统

提供完整的游戏音频管理，包括：
- 程序化音频生成（音调、和弦、旋律）
- 背景音乐（BGM）的播放、暂停、继续、循环控制
- 多种游戏音效的独立触发
- 背景音乐和音效的独立音量调节
- 优雅的降级处理（无头模式/音频初始化失败时静默）

使用示例:
    from audio import AudioManager

    audio = AudioManager()
    audio.play_bgm("level_0")
    audio.play_sfx(AudioManager.SFX_JUMP)
"""

from audio.manager import AudioManager
from audio.notes import NOTE_FREQ, get_note
from audio.generators import generate_tone, generate_chord, generate_melody, mix_audio
from audio.bgm import generate_bgm, BGM_GENERATORS
from audio.sfx import generate_sfx, SFX_GENERATORS

__all__ = [
    "AudioManager",
    "NOTE_FREQ",
    "get_note",
    "generate_tone",
    "generate_chord",
    "generate_melody",
    "mix_audio",
    "generate_bgm",
    "BGM_GENERATORS",
    "generate_sfx",
    "SFX_GENERATORS",
]
