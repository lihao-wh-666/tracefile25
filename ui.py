# -*- coding: utf-8 -*-
"""
ui.py - 游戏 UI 组件模块

提供音量调节面板等可交互 UI 组件，包括：
- VolumePanel: 包含背景音乐和音效音量滑块的调节面板
  - 支持鼠标拖拽调节音量
  - 实时显示音量百分比
  - 显示/隐藏切换（按 V 键）
  - 视觉反馈：滑块填充、高亮、悬停效果
- ItemIconSystem: 左下角道具图标显示系统
  - 图标状态：灰色不可用 / 亮色可用
  - 水平排列布局，自适应屏幕分辨率
  - 鼠标悬停显示提示框，点击使用道具
  - 0.3秒平滑过渡动画
"""

import os
import math
import pygame

from config import (
    VOLUME_PANEL_X, VOLUME_PANEL_Y,
    VOLUME_PANEL_WIDTH, VOLUME_PANEL_HEIGHT,
    VOLUME_SLIDER_WIDTH, VOLUME_SLIDER_HEIGHT,
    VOLUME_SLIDER_KNOB_SIZE,
    VOLUME_PANEL_BG, VOLUME_PANEL_BORDER,
    VOLUME_SLIDER_BG, VOLUME_SLIDER_FG,
    VOLUME_SLIDER_KNOB, VOLUME_TEXT_COLOR,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    HUD_POWERUP_ICON_SIZE,
    HUD_POWERUP_ICON_MARGIN,
    HUD_POWERUP_START_X,
    HUD_POWERUP_START_Y_OFFSET,
    HUD_POWERUP_BAR_HEIGHT,
    HUD_POWERUP_BAR_BG,
    HUD_POWERUP_TEXT_COLOR,
    HUD_POWERUP_TOOLTIP_BG,
    HUD_POWERUP_TOOLTIP_BORDER,
    HUD_POWERUP_TOOLTIP_TEXT,
    HUD_POWERUP_TRANSITION_FRAMES,
    HUD_POWERUP_HOVER_SCALE,
    HUD_POWERUP_GRAYSCALE_ALPHA,
    SPEED_BOOST_COLOR, SPEED_BOOST_DARK, SPEED_BOOST_GLOW,
    SHIELD_COLOR, SHIELD_DARK, SHIELD_GLOW,
    WEAPON_COLOR, WEAPON_DARK, WEAPON_GLOW,
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


class ItemIconData:
    """单个道具图标数据。"""

    def __init__(self, powerup_type, powerup_manager, key_label, display_name, description):
        self.powerup_type = powerup_type
        self.powerup_manager = powerup_manager
        self.key_label = key_label
        self.display_name = display_name
        self.description = description
        self._prev_available = False
        self.transition_progress = 1.0
        self.hover_progress = 0.0
        self.rect = pygame.Rect(0, 0, HUD_POWERUP_ICON_SIZE, HUD_POWERUP_ICON_SIZE)
        self.hovered = False
        self.clicked = False
        self.pulse_phase = 0.0

    @property
    def powerup(self):
        return self.powerup_manager.get_powerup(self.powerup_type)

    def update_transitions(self):
        """更新过渡动画状态。"""
        is_available = self.powerup.can_activate or self.powerup.is_active
        target_transition = 1.0 if is_available else 0.0
        if self._prev_available != is_available:
            self.transition_progress = 1.0 - self.transition_progress
            self._prev_available = is_available
        self.transition_progress = max(0.0, self.transition_progress - 1.0 / HUD_POWERUP_TRANSITION_FRAMES)

        target_hover = 1.0 if self.hovered and is_available else 0.0
        self.hover_progress += (target_hover - self.hover_progress) * 0.25

        self.pulse_phase += 0.15

    @property
    def is_available(self):
        return self.powerup.can_activate or self.powerup.is_active

    @property
    def effective_alpha(self):
        t = self.transition_progress
        if self.is_available:
            return t * (1.0 - 0.0) + 0.0
        else:
            return 1.0 - t * (1.0 - HUD_POWERUP_GRAYSCALE_ALPHA)

    def get_effective_scale(self):
        base_scale = 1.0 + self.hover_progress * (HUD_POWERUP_HOVER_SCALE - 1.0)
        if self.is_available and self.powerup.is_active:
            pulse = 0.03 * math.sin(self.pulse_phase)
            base_scale += pulse
        return base_scale


class ItemIconSystem:
    """
    道具图标显示系统。

    位于屏幕左下角，水平排列显示所有道具图标。
    支持：
    - 灰色不可用状态 / 亮色可用状态
    - 鼠标悬停放大 + 提示框
    - 点击使用道具
    - 0.3秒平滑过渡动画
    - 响应式布局适配
    """

    _LABEL_FONT_SIZE = 18

    def __init__(self, game, powerup_manager):
        self.game = game
        self.powerup_manager = powerup_manager
        self.icons = []
        self._screen_width = SCREEN_WIDTH
        self._screen_height = SCREEN_HEIGHT
        self._label_font = None
        self._init_icons()
        self.on_item_used = None

    def _ensure_label_font(self):
        if self._label_font is None:
            self._label_font = get_chinese_font(self._LABEL_FONT_SIZE)

    def _init_icons(self):
        """初始化道具图标列表。"""
        from entities.powerups import PowerupType

        icon_info = [
            (PowerupType.SPEED_BOOST, "1", "加速",
             "提升移动速度，持续一段时间后进入冷却"),
            (PowerupType.SHIELD, "2", "护盾",
             "提供护盾吸收伤害，护盾耗尽或时间结束后失效"),
            (PowerupType.WEAPON, "3", "强化武器",
             "提升攻击力和射速，使用一定次数后失效"),
        ]

        self.icons = []
        for ptype, key, name, desc in icon_info:
            icon = ItemIconData(ptype, self.powerup_manager, key, name, desc)
            icon._prev_available = icon.powerup.can_activate or icon.powerup.is_active
            icon.transition_progress = 0.0
            self.icons.append(icon)

    def on_resize(self, width, height):
        """响应屏幕尺寸变化。"""
        self._screen_width = width
        self._screen_height = height

    def _get_start_y(self):
        """计算图标区域的起始 Y 坐标（距离底部）。"""
        return self._screen_height - HUD_POWERUP_START_Y_OFFSET - HUD_POWERUP_ICON_SIZE

    def _layout_icons(self):
        """计算所有图标的位置。"""
        x = HUD_POWERUP_START_X
        y = self._get_start_y()
        size = HUD_POWERUP_ICON_SIZE
        margin = HUD_POWERUP_ICON_MARGIN

        for icon in self.icons:
            icon.rect.topleft = (x, y)
            x += size + margin

    def handle_event(self, event):
        """
        处理鼠标事件。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 是否处理了事件
        """
        handled = False

        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for icon in self.icons:
                icon.hovered = icon.rect.collidepoint(mouse_pos) and icon.is_available

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            for icon in self.icons:
                if icon.rect.collidepoint(mouse_pos):
                    icon.clicked = True
                    if icon.is_available and self.on_item_used:
                        self.powerup_manager.use_powerup(icon.powerup_type)
                        self.on_item_used(icon.powerup_type)
                    handled = True
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for icon in self.icons:
                icon.clicked = False

        return handled

    def update(self):
        """更新所有图标状态。"""
        for icon in self.icons:
            icon.update_transitions()

    def _get_colors(self, icon):
        """获取道具对应的颜色。"""
        from entities.powerups import PowerupType, SpeedBoostPowerup, ShieldPowerup, WeaponPowerup

        if isinstance(icon.powerup, SpeedBoostPowerup):
            return SPEED_BOOST_COLOR, SPEED_BOOST_DARK, SPEED_BOOST_GLOW
        elif isinstance(icon.powerup, ShieldPowerup):
            return SHIELD_COLOR, SHIELD_DARK, SHIELD_GLOW
        elif isinstance(icon.powerup, WeaponPowerup):
            return WEAPON_COLOR, WEAPON_DARK, WEAPON_GLOW
        return (200, 200, 200), (150, 150, 150), (255, 255, 255)

    def _get_symbol_points(self, icon, cx, cy, size):
        """获取道具符号的绘制点。"""
        from entities.powerups import SpeedBoostPowerup, ShieldPowerup, WeaponPowerup

        if isinstance(icon.powerup, SpeedBoostPowerup):
            s = size // 3
            return [
                (cx - s, cy - s // 2),
                (cx, cy),
                (cx + s, cy + s // 2),
            ]
        elif isinstance(icon.powerup, ShieldPowerup):
            s = size // 3
            pts = []
            for angle_deg in range(0, 360, 45):
                a = math.radians(angle_deg - 90)
                pts.append((cx + int(math.cos(a) * s), cy + int(math.sin(a) * s * 0.9)))
            return pts
        elif isinstance(icon.powerup, WeaponPowerup):
            s = size // 3
            return [
                (cx - s, cy + s),
                (cx, cy),
                (cx + s, cy - s),
                (cx - s + 3, cy + s - 3),
                (cx + s - 3, cy - s + 3),
            ]
        return []

    def _apply_grayscale(self, color, alpha):
        """将颜色转换为灰度。"""
        gray = int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
        r = int(gray * alpha + color[0] * (1 - alpha))
        g = int(gray * alpha + color[1] * (1 - alpha))
        b = int(gray * alpha + color[2] * (1 - alpha))
        return (r, g, b)

    def _draw_icon(self, surface, icon, font):
        """绘制单个道具图标。"""
        from entities.powerups import SpeedBoostPowerup, ShieldPowerup, WeaponPowerup
        self._ensure_label_font()
        label_font = self._label_font

        size = HUD_POWERUP_ICON_SIZE
        scale = icon.get_effective_scale()
        draw_size = int(size * scale)
        x, y = icon.rect.topleft

        main_c, dark_c, glow_c = self._get_colors(icon)

        if not icon.is_available:
            alpha = icon.effective_alpha
            main_c = self._apply_grayscale(main_c, alpha)
            dark_c = self._apply_grayscale(dark_c, alpha)
            glow_c = self._apply_grayscale(glow_c, alpha)

        offset = (size - draw_size) // 2

        if icon.is_available and icon.hovered:
            glow_size = draw_size + 8
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                (*glow_c, 80),
                (0, 0, glow_size, glow_size),
                border_radius=8,
            )
            surface.blit(glow_surf, (x + (size - glow_size) // 2, y + (size - glow_size) // 2))

        bg_alpha = 200 if icon.is_available else 100
        bg_surf = pygame.Surface((draw_size, draw_size), pygame.SRCALPHA)
        pygame.draw.rect(
            bg_surf,
            (*dark_c, bg_alpha),
            (0, 0, draw_size, draw_size),
            border_radius=8,
        )
        border_c = main_c if icon.is_available else (120, 120, 120)
        pygame.draw.rect(
            bg_surf,
            border_c,
            (0, 0, draw_size, draw_size),
            width=2, border_radius=8,
        )

        if icon.powerup.is_active:
            tick = self.game.tick if self.game else 0
            pulse = 0.5 + 0.5 * math.sin(tick * 0.15)
            glow_alpha = int(50 + 30 * pulse)
            active_glow = pygame.Surface((draw_size, draw_size), pygame.SRCALPHA)
            pygame.draw.rect(
                active_glow,
                (*glow_c, glow_alpha),
                (3, 3, draw_size - 6, draw_size - 6),
                border_radius=6,
            )
            bg_surf.blit(active_glow, (0, 0))

        sym_surf = pygame.Surface((draw_size, draw_size), pygame.SRCALPHA)
        sym_color = glow_c if icon.is_available else (150, 150, 150)
        sym_pts = self._get_symbol_points(icon, draw_size // 2, draw_size // 2, draw_size)
        for pt in sym_pts:
            pygame.draw.circle(sym_surf, sym_color, pt, max(2, draw_size // 12))
        bg_surf.blit(sym_surf, (0, 0))

        p = icon.powerup
        if hasattr(p, 'shield_ratio') or hasattr(p, 'uses_ratio') or p.is_active or p.is_on_cooldown:
            bar_y = draw_size - HUD_POWERUP_BAR_HEIGHT - 18
            bar_w = draw_size - 8
            if hasattr(p, 'shield_ratio') and p.is_active:
                ratio = p.shield_ratio
                fg = SHIELD_GLOW
            elif hasattr(p, 'uses_ratio'):
                ratio = p.uses_ratio
                if isinstance(p, SpeedBoostPowerup):
                    fg = SPEED_BOOST_GLOW
                elif isinstance(p, ShieldPowerup):
                    fg = SHIELD_GLOW
                else:
                    fg = WEAPON_GLOW
            else:
                ratio = p.progress_ratio
                fg = glow_c if p.is_active else (120, 120, 140)
            if not icon.is_available:
                fg = self._apply_grayscale(fg, icon.effective_alpha)
            self._draw_bar_on_surf(
                bg_surf, 4, bar_y, bar_w, HUD_POWERUP_BAR_HEIGHT,
                ratio, fg, HUD_POWERUP_BAR_BG,
            )

        lvl_c = HUD_POWERUP_TEXT_COLOR if icon.is_available else (120, 120, 120)
        lvl_text = label_font.render(f"L{p.level}", True, lvl_c)
        bg_surf.blit(lvl_text, (4, draw_size - lvl_text.get_height() - 3))

        key_bg_size = label_font.get_height() + 2
        key_bg_x = draw_size - key_bg_size - 2
        key_bg_y = draw_size - key_bg_size - 2
        if icon.is_available:
            key_bg_color = (*main_c, 140)
        else:
            key_bg_color = (80, 80, 80, 140)
        pygame.draw.rect(
            bg_surf, key_bg_color,
            (key_bg_x, key_bg_y, key_bg_size, key_bg_size),
            border_radius=3,
        )
        key_c = (255, 255, 200) if icon.is_available else (120, 120, 120)
        key_surf = label_font.render(icon.key_label, True, key_c)
        kw = key_surf.get_width()
        kh = key_surf.get_height()
        bg_surf.blit(key_surf, (key_bg_x + (key_bg_size - kw) // 2, key_bg_y + (key_bg_size - kh) // 2))

        surface.blit(bg_surf, (x + offset, y + offset))

    def _draw_bar_on_surf(self, surf, x, y, w, h, ratio, fg_color, bg_color):
        """在 Surface 上绘制进度条。"""
        pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=2)
        fill_w = max(1, int(w * max(0.0, min(1.0, ratio))))
        pygame.draw.rect(surf, fg_color, (x, y, fill_w, h), border_radius=2)

    def _draw_tooltip(self, surface, icon, font, small_font, mouse_pos):
        """绘制道具提示框。"""
        pad_x = mouse_pos[0] + 15
        pad_y = mouse_pos[1] - 10

        title_text = font.render(icon.display_name, True, HUD_POWERUP_TOOLTIP_TEXT)
        desc_lines = self._wrap_text(icon.description, small_font, 220)

        line_widths = [small_font.render(line, True, (255, 255, 255)).get_width() for line in desc_lines]
        max_desc_w = max(line_widths) if line_widths else 0
        max_w = max(title_text.get_width(), max_desc_w)
        total_h = title_text.get_height() + 8 + len(desc_lines) * (small_font.get_height() + 2)

        box_w = max_w + 20
        box_h = total_h + 20

        if pad_x + box_w > self._screen_width - 10:
            pad_x = mouse_pos[0] - box_w - 15
        if pad_y - box_h < 10:
            pad_y = mouse_pos[1] + 20

        tooltip_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(
            tooltip_surf,
            HUD_POWERUP_TOOLTIP_BG,
            (0, 0, box_w, box_h),
            border_radius=8,
        )
        pygame.draw.rect(
            tooltip_surf,
            HUD_POWERUP_TOOLTIP_BORDER,
            (0, 0, box_w, box_h),
            width=2, border_radius=8,
        )

        tooltip_surf.blit(title_text, (10, 10))

        y_offset = title_text.get_height() + 18
        for line in desc_lines:
            line_surf = small_font.render(line, True, HUD_POWERUP_TOOLTIP_TEXT)
            tooltip_surf.blit(line_surf, (10, y_offset))
            y_offset += small_font.get_height() + 2

        surface.blit(tooltip_surf, (pad_x, pad_y))

    def _wrap_text(self, text, font, max_width):
        """将文本按宽度换行。"""
        words = text.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def draw(self, surface, font, small_font):
        """
        绘制所有道具图标和提示框。

        Args:
            surface: 目标绘制 Surface
            font: 标题字体
            small_font: 描述字体
        """
        self._layout_icons()

        for icon in self.icons:
            self._draw_icon(surface, icon, small_font)

        mouse_pos = pygame.mouse.get_pos()
        for icon in self.icons:
            if icon.hovered and icon.is_available:
                self._draw_tooltip(surface, icon, font, small_font, mouse_pos)
                break
