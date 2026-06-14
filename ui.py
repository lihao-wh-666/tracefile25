# -*- coding: utf-8 -*-
"""
ui.py - 游戏 UI 组件模块

提供音量调节面板等可交互 UI 组件，包括：
- VolumePanel: 包含背景音乐和音效音量滑块的调节面板
  - 支持鼠标拖拽调节音量
  - 实时显示音量百分比
  - 显示/隐藏切换（按 V 键）
  - 视觉反馈：滑块填充、高亮、悬停效果
"""

import os
import pygame

from config import (
    VOLUME_PANEL_X, VOLUME_PANEL_Y,
    VOLUME_PANEL_WIDTH, VOLUME_PANEL_HEIGHT,
    VOLUME_SLIDER_WIDTH, VOLUME_SLIDER_HEIGHT,
    VOLUME_SLIDER_KNOB_SIZE,
    VOLUME_PANEL_BG, VOLUME_PANEL_BORDER,
    VOLUME_SLIDER_BG, VOLUME_SLIDER_FG,
    VOLUME_SLIDER_KNOB, VOLUME_TEXT_COLOR,
)


_FONT_CACHE = {}


def get_chinese_font(size):
    """
    获取支持中文显示的字体。

    优先使用 TTF 格式字体（避免 TTC 集合字体在 pygame 中的渲染问题），
    使用字体缓存避免重复加载同一字体。
    """
    cache_key = size
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simsun.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                break
            except (pygame.error, OSError):
                continue

    if font is None:
        font = pygame.font.Font(None, size)

    _FONT_CACHE[cache_key] = font
    return font


class VolumeSlider:
    """
    单个音量滑块组件。

    属性:
        x, y: 滑块左上角屏幕坐标
        width: 轨道总宽度
        height: 轨道高度
        value: 当前音量值 0.0~1.0
        dragging: 是否正在被鼠标拖拽
    """

    def __init__(self, x, y, width, height, initial_value=0.5):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = max(0.0, min(1.0, float(initial_value)))
        self.dragging = False
        self.knob_size = VOLUME_SLIDER_KNOB_SIZE
        self._hover = False

    def _knob_x(self):
        """计算滑块旋钮当前的中心 x 坐标。"""
        return self.x + int(self.value * self.width)

    def _knob_rect(self):
        """获取滑块旋钮的碰撞矩形。"""
        kx = self._knob_x()
        half = self.knob_size // 2
        return pygame.Rect(
            kx - half,
            self.y + self.height // 2 - half,
            self.knob_size,
            self.knob_size,
        )

    def _track_rect(self):
        """获取滑块轨道的碰撞矩形（包含较大的命中区域）。"""
        return pygame.Rect(
            self.x,
            self.y + self.height // 2 - self.knob_size // 2,
            self.width,
            self.knob_size,
        )

    def handle_event(self, event):
        """
        处理鼠标事件，更新滑块状态。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 是否有值变化
        """
        changed = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self._track_rect().collidepoint(mouse_pos):
                self.dragging = True
                new_val = (mouse_pos[0] - self.x) / self.width
                new_val = max(0.0, min(1.0, new_val))
                if abs(new_val - self.value) > 0.001:
                    self.value = new_val
                    changed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self._hover = self._track_rect().collidepoint(mouse_pos)
            if self.dragging:
                new_val = (mouse_pos[0] - self.x) / self.width
                new_val = max(0.0, min(1.0, new_val))
                if abs(new_val - self.value) > 0.001:
                    self.value = new_val
                    changed = True

        return changed

    def set_value(self, value):
        """设置音量值。"""
        self.value = max(0.0, min(1.0, float(value)))

    def draw(self, surface, font):
        """
        绘制音量滑块。

        Args:
            surface: 目标绘制 Surface
            font: 用于绘制百分比文本的字体
        """
        track_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, VOLUME_SLIDER_BG, track_rect, border_radius=5)

        fill_width = int(self.width * self.value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.x, self.y, fill_width, self.height)
            pygame.draw.rect(surface, VOLUME_SLIDER_FG, fill_rect, border_radius=5)

        knob_x = self._knob_x()
        knob_y = self.y + self.height // 2
        half = self.knob_size // 2

        if self.dragging or self._hover:
            glow_surf = pygame.Surface(
                (self.knob_size + 8, self.knob_size + 8), pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow_surf,
                (*VOLUME_SLIDER_FG, 120),
                (self.knob_size // 2 + 4, self.knob_size // 2 + 4),
                self.knob_size // 2 + 4,
            )
            surface.blit(glow_surf, (knob_x - half - 4, knob_y - half - 4))

        pygame.draw.circle(
            surface, VOLUME_SLIDER_KNOB, (knob_x, knob_y), half
        )
        pygame.draw.circle(
            surface, VOLUME_SLIDER_FG, (knob_x, knob_y), half, 2
        )

        pct = int(self.value * 100)
        pct_text = font.render(f"{pct}%", True, VOLUME_TEXT_COLOR)
        text_x = self.x + self.width + 15
        text_y = self.y + self.height // 2 - pct_text.get_height() // 2
        surface.blit(pct_text, (text_x, text_y))


class VolumePanel:
    """
    音量调节面板，包含背景音乐和音效两个独立滑块。

    属性:
        visible: 面板是否显示
        bgm_slider: 背景音乐音量滑块
        sfx_slider: 音效音量滑块
        on_bgm_change: 背景音乐音量变化回调函数
        on_sfx_change: 音效音量变化回调函数
    """

    def __init__(self, audio_manager=None):
        self.visible = False
        self.x = VOLUME_PANEL_X
        self.y = VOLUME_PANEL_Y
        self.width = VOLUME_PANEL_WIDTH
        self.height = VOLUME_PANEL_HEIGHT

        slider_x = self.x + 50
        slider_w = VOLUME_SLIDER_WIDTH
        slider_h = VOLUME_SLIDER_HEIGHT

        bgm_initial = 0.6
        sfx_initial = 0.8
        if audio_manager:
            bgm_initial = audio_manager.bgm_volume
            sfx_initial = audio_manager.sfx_volume

        self.bgm_slider = VolumeSlider(
            slider_x, self.y + 55, slider_w, slider_h, bgm_initial
        )
        self.sfx_slider = VolumeSlider(
            slider_x, self.y + 100, slider_w, slider_h, sfx_initial
        )

        self.on_bgm_change = None
        self.on_sfx_change = None
        self._audio_manager = audio_manager

    def toggle(self):
        """切换面板的显示/隐藏状态。"""
        self.visible = not self.visible
        if self._audio_manager and self.visible:
            self._audio_manager.play_sfx("menu_click")

    def show(self):
        """显示面板。"""
        self.visible = True

    def hide(self):
        """隐藏面板。"""
        self.visible = False

    def handle_event(self, event):
        """
        处理面板相关的鼠标事件。

        Args:
            event: pygame 事件对象
        """
        if not self.visible:
            return

        if self.bgm_slider.handle_event(event):
            if self.on_bgm_change:
                self.on_bgm_change(self.bgm_slider.value)

        if self.sfx_slider.handle_event(event):
            if self.on_sfx_change:
                self.on_sfx_change(self.sfx_slider.value)

    def sync_from_audio_manager(self):
        """从 AudioManager 同步当前音量值到滑块。"""
        if self._audio_manager:
            self.bgm_slider.set_value(self._audio_manager.bgm_volume)
            self.sfx_slider.set_value(self._audio_manager.sfx_volume)

    def draw(self, surface, font, small_font):
        """
        绘制音量调节面板。

        Args:
            surface: 目标绘制 Surface
            font: 标题字体
            small_font: 标签字体
        """
        if not self.visible:
            return

        panel_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surf, VOLUME_PANEL_BG,
            (0, 0, self.width, self.height),
            border_radius=10,
        )
        pygame.draw.rect(
            panel_surf, VOLUME_PANEL_BORDER,
            (0, 0, self.width, self.height),
            width=2, border_radius=10,
        )
        surface.blit(panel_surf, (self.x, self.y))

        title = font.render("音频设置  [V]", True, VOLUME_TEXT_COLOR)
        title_x = self.x + (self.width - title.get_width()) // 2
        surface.blit(title, (title_x, self.y + 12))

        bgm_label = small_font.render("音乐:", True, VOLUME_TEXT_COLOR)
        surface.blit(bgm_label, (self.x + 15, self.y + 48))

        sfx_label = small_font.render("音效:", True, VOLUME_TEXT_COLOR)
        surface.blit(sfx_label, (self.x + 15, self.y + 93))

        self.bgm_slider.draw(surface, small_font)
        self.sfx_slider.draw(surface, small_font)

        hint = small_font.render("拖动滑块调节音量", True,
                                 (180, 180, 220))
        hint_x = self.x + (self.width - hint.get_width()) // 2
        surface.blit(hint, (hint_x, self.y + self.height - 25))
