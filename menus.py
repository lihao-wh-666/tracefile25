# -*- coding: utf-8 -*-
"""
menus.py - 游戏菜单系统模块

提供完整的游戏菜单系统，包括：
- Button: 可交互按钮组件，支持键盘/鼠标导航和悬停效果
- Menu: 基类菜单，提供统一的布局、绘制和事件处理
- MainMenu: 主菜单（开始游戏、加载游戏、游戏教程、排行榜、设置、退出）
- SettingsMenu: 设置菜单（音量、画质、控制方式）
- PauseMenu: 暂停菜单（继续游戏、返回主菜单、重新开始）
- GameOverMenu: 游戏结束菜单（得分展示、重新挑战）
- LeaderboardMenu: 排行榜菜单（排名、昵称、得分）
- SaveNameInputMenu: 保存时输入存档名称的菜单
- StorageManager: 本地数据持久化管理（设置、存档、排行榜）
- MenuManager: 菜单状态管理器，负责菜单切换和游戏状态协调

注意：TutorialMenu 教程菜单已迁移至 tutorial.py 模块
"""

import os
import json
import sys
import ctypes
import pygame
from datetime import datetime

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, BLACK,
    AUDIO_BGM_VOLUME_DEFAULT, AUDIO_SFX_VOLUME_DEFAULT,
)
from audio import AudioManager


def switch_to_english_keyboard():
    """在 Windows 上将输入法切换为英文键盘布局。"""
    if sys.platform != "win32":
        return
    try:
        HKL_ENGLISH = 0x04090409
        ctypes.windll.user32.ActivateKeyboardLayout(HKL_ENGLISH, 0)
    except Exception:
        pass


_FONT_CACHE = {}


def get_chinese_font(size):
    """
    获取支持中文显示的字体。

    优先使用 TTF 格式字体（避免 TTC 集合字体在 pygame 中的渲染问题），
    使用字体缓存避免重复加载同一字体。

    支持平台：
    - Windows: 黑体 simhei.ttf、微软雅黑 msyh.ttc、宋体 simsun.ttc
    - macOS: PingFang 苹方
    - Linux: 文泉驿微米黑、Noto Sans CJK

    Args:
        size: 字体大小

    Returns:
        pygame.font.Font: 支持中文的字体对象
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


MENU_BG_COLOR = (20, 20, 40)
MENU_PANEL_BG = (40, 40, 70, 240)
MENU_PANEL_BORDER = (100, 150, 255)
MENU_TITLE_COLOR = (255, 255, 255)
MENU_TEXT_COLOR = (220, 220, 240)
MENU_HINT_COLOR = (150, 150, 180)

BUTTON_BG = (60, 80, 140)
BUTTON_BG_HOVER = (80, 120, 200)
BUTTON_BG_SELECTED = (100, 150, 255)
BUTTON_BG_DISABLED = (50, 50, 70)
BUTTON_BORDER = (150, 200, 255)
BUTTON_TEXT = (255, 255, 255)
BUTTON_TEXT_DISABLED = (120, 120, 140)

SLIDER_BG = (30, 30, 50)
SLIDER_FG = (100, 200, 255)
SLIDER_KNOB = (200, 230, 255)


class GameState:
    """游戏状态枚举类。"""
    MAIN_MENU = "main_menu"
    SETTINGS_MENU = "settings_menu"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    LEADERBOARD = "leaderboard"
    TUTORIAL = "tutorial"
    PLAYING = "playing"
    TRANSITIONING = "transitioning"
    LOADING = "loading"
    SAVE_LIST = "save_list"
    SAVE_NAME_INPUT = "save_name_input"


class Button:
    """
    可交互按钮组件。

    支持键盘导航（上下箭头选择、Enter确认）和鼠标交互，
    具有悬停、选中、禁用等视觉状态。

    属性:
        rect: 按钮碰撞矩形
        text: 按钮显示文本
        callback: 点击回调函数
        enabled: 是否启用
        selected: 是否被选中（键盘导航）
        hover: 鼠标是否悬停
    """

    def __init__(self, x, y, width, height, text, callback=None, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.enabled = enabled
        self.selected = False
        self.hover = False
        self._click_anim = 0

    def handle_event(self, event):
        """
        处理按钮事件。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 是否触发了按钮点击
        """
        if not self.enabled:
            return False

        triggered = False

        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._click_anim = 5
                triggered = True
                if self.callback:
                    self.callback()

        elif event.type == pygame.KEYDOWN and self.selected:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._click_anim = 5
                triggered = True
                if self.callback:
                    self.callback()

        return triggered

    def draw(self, surface, font):
        """
        绘制按钮。

        Args:
            surface: 目标绘制 Surface
            font: 文本字体
        """
        if self._click_anim > 0:
            self._click_anim -= 1

        if not self.enabled:
            bg_color = BUTTON_BG_DISABLED
            text_color = BUTTON_TEXT_DISABLED
        elif self.selected:
            bg_color = BUTTON_BG_SELECTED
            text_color = BUTTON_TEXT
        elif self.hover:
            bg_color = BUTTON_BG_HOVER
            text_color = BUTTON_TEXT
        else:
            bg_color = BUTTON_BG
            text_color = BUTTON_TEXT

        offset = 2 if self._click_anim > 0 else 0
        draw_rect = self.rect.copy()
        draw_rect.y += offset

        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=8)
        pygame.draw.rect(surface, BUTTON_BORDER, draw_rect, width=2, border_radius=8)

        if self.selected:
            glow_surf = pygame.Surface(
                (draw_rect.width + 12, draw_rect.height + 12), pygame.SRCALPHA
            )
            pygame.draw.rect(
                glow_surf,
                (*BUTTON_BORDER, 80),
                (6, 6, draw_rect.width, draw_rect.height),
                border_radius=10,
            )
            surface.blit(glow_surf, (draw_rect.x - 6, draw_rect.y - 6))

        text_surf = font.render(self.text, True, text_color)
        text_x = draw_rect.x + (draw_rect.width - text_surf.get_width()) // 2
        text_y = draw_rect.y + (draw_rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (text_x, text_y))


class Slider:
    """
    滑块组件，用于数值调节（如音量设置）。

    属性:
        x, y: 滑块左上角坐标
        width: 轨道宽度
        height: 轨道高度
        value: 当前值 0.0~1.0
        label: 滑块标签文本
        dragging: 是否正在拖拽
    """

    def __init__(self, x, y, width, height, initial_value=0.5, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.value = max(0.0, min(1.0, float(initial_value)))
        self.label = label
        self.dragging = False
        self.hover = False
        self.knob_size = 20

    def _knob_x(self):
        """计算滑块旋钮的 x 坐标。"""
        return self.x + int(self.value * self.width)

    def _track_rect(self):
        """获取轨道的碰撞矩形（扩大命中区域）。"""
        return pygame.Rect(
            self.x,
            self.y + self.height // 2 - self.knob_size // 2,
            self.width,
            self.knob_size,
        )

    def handle_event(self, event):
        """
        处理滑块事件。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 值是否发生变化
        """
        changed = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._track_rect().collidepoint(event.pos):
                self.dragging = True
                new_val = (event.pos[0] - self.x) / self.width
                new_val = max(0.0, min(1.0, new_val))
                if abs(new_val - self.value) > 0.001:
                    self.value = new_val
                    changed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            self.hover = self._track_rect().collidepoint(event.pos)
            if self.dragging:
                new_val = (event.pos[0] - self.x) / self.width
                new_val = max(0.0, min(1.0, new_val))
                if abs(new_val - self.value) > 0.001:
                    self.value = new_val
                    changed = True

        elif event.type == pygame.KEYDOWN:
            if self.hover or hasattr(self, 'selected') and self.selected:
                if event.key == pygame.K_LEFT:
                    self.value = max(0.0, self.value - 0.05)
                    changed = True
                elif event.key == pygame.K_RIGHT:
                    self.value = min(1.0, self.value + 0.05)
                    changed = True

        return changed

    def draw(self, surface, font):
        """
        绘制滑块。

        Args:
            surface: 目标绘制 Surface
            font: 标签字体
        """
        if self.label:
            label_surf = font.render(self.label, True, MENU_TEXT_COLOR)
            surface.blit(label_surf, (self.x, self.y - 25))

        track_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, SLIDER_BG, track_rect, border_radius=5)

        fill_width = int(self.width * self.value)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.x, self.y, fill_width, self.height)
            pygame.draw.rect(surface, SLIDER_FG, fill_rect, border_radius=5)

        knob_x = self._knob_x()
        knob_y = self.y + self.height // 2
        half = self.knob_size // 2

        if self.dragging or self.hover:
            glow_surf = pygame.Surface(
                (self.knob_size + 10, self.knob_size + 10), pygame.SRCALPHA
            )
            pygame.draw.circle(
                glow_surf,
                (*SLIDER_FG, 120),
                (half + 5, half + 5),
                half + 5,
            )
            surface.blit(glow_surf, (knob_x - half - 5, knob_y - half - 5))

        pygame.draw.circle(surface, SLIDER_KNOB, (knob_x, knob_y), half)
        pygame.draw.circle(surface, SLIDER_FG, (knob_x, knob_y), half, 2)

        pct_text = font.render(f"{int(self.value * 100)}%", True, MENU_TEXT_COLOR)
        surface.blit(pct_text, (self.x + self.width + 15, self.y - 5))


class StorageManager:
    """
    本地数据持久化管理器。

    负责存储和加载：
    - 游戏设置（音量、画质、控制方式）
    - 游戏存档（当前进度、得分），支持多个命名存档
    - 排行榜数据（玩家昵称、得分、时间戳）

    数据以 JSON 格式存储在用户目录下的 .platform_jumper 文件夹中。
    """

    def __init__(self):
        self.save_dir = os.path.join(
            os.path.expanduser("~"), ".platform_jumper"
        )
        self.saves_subdir = os.path.join(self.save_dir, "saves")
        self.settings_file = os.path.join(self.save_dir, "settings.json")
        self.savegame_file = os.path.join(self.save_dir, "savegame.json")
        self.leaderboard_file = os.path.join(self.save_dir, "leaderboard.json")
        self._ensure_save_dir()

    def _ensure_save_dir(self):
        """确保保存目录存在。"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        if not os.path.exists(self.saves_subdir):
            os.makedirs(self.saves_subdir)

    def _sanitize_filename(self, name):
        """
        清理文件名，移除非法字符。

        Args:
            name: 原始存档名称

        Returns:
            str: 清理后的安全文件名
        """
        invalid_chars = '<>:"/\\|?*'
        safe_name = ''.join(c for c in name if c not in invalid_chars).strip()
        return safe_name if safe_name else "未命名"

    def _get_save_path(self, save_name):
        """获取指定名称的存档文件路径。"""
        safe_name = self._sanitize_filename(save_name)
        return os.path.join(self.saves_subdir, f"{safe_name}.json")

    def save_settings(self, settings):
        """
        保存游戏设置。

        Args:
            settings: 包含设置项的字典
        """
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def load_settings(self):
        """
        加载游戏设置。

        Returns:
            dict: 设置字典，若文件不存在则返回默认设置
        """
        default_settings = {
            "bgm_volume": AUDIO_BGM_VOLUME_DEFAULT,
            "sfx_volume": AUDIO_SFX_VOLUME_DEFAULT,
            "graphics_quality": "high",
            "control_mode": "keyboard",
            "fullscreen": False,
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    default_settings.update(settings)
        except (IOError, json.JSONDecodeError):
            pass
        return default_settings

    def save_game(self, game_data):
        """
        保存游戏进度（兼容旧版单存档接口）。

        Args:
            game_data: 包含游戏状态的字典
        """
        save_data = {
            "timestamp": datetime.now().isoformat(),
            **game_data
        }
        try:
            with open(self.savegame_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def load_game(self):
        """
        加载游戏进度（兼容旧版单存档接口）。

        Returns:
            dict: 游戏数据字典，若不存在存档则返回 None
        """
        try:
            if os.path.exists(self.savegame_file):
                with open(self.savegame_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return None

    def has_save_game(self):
        """
        检查是否存在存档（兼容旧版接口，检查任意存档是否存在）。

        Returns:
            bool: 是否存在存档
        """
        if os.path.exists(self.savegame_file):
            return True
        return len(self.list_saves()) > 0

    def list_saves(self):
        """
        列出所有命名存档，按修改时间倒序排列。

        Returns:
            list: 存档信息列表，每项包含 name, timestamp, level, score 等
        """
        saves = []
        try:
            if os.path.isdir(self.saves_subdir):
                for filename in os.listdir(self.saves_subdir):
                    if filename.endswith('.json'):
                        save_name = filename[:-5]
                        file_path = os.path.join(self.saves_subdir, filename)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            mtime = os.path.getmtime(file_path)
                            saves.append({
                                "name": save_name,
                                "timestamp": data.get("timestamp", ""),
                                "level": data.get("level", 0),
                                "score": data.get("score", 0),
                                "mtime": mtime,
                            })
                        except (IOError, json.JSONDecodeError):
                            continue
        except OSError:
            pass
        saves.sort(key=lambda x: x.get("mtime", 0), reverse=True)
        return saves

    def save_named_game(self, save_name, game_data):
        """
        保存命名存档。

        Args:
            save_name: 存档名称
            game_data: 游戏状态字典

        Returns:
            bool: 是否保存成功
        """
        save_data = {
            "name": save_name,
            "timestamp": datetime.now().isoformat(),
            **game_data
        }
        file_path = self._get_save_path(save_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def load_named_game(self, save_name):
        """
        加载命名存档。

        Args:
            save_name: 存档名称

        Returns:
            dict: 游戏数据字典，若不存在则返回 None
        """
        file_path = self._get_save_path(save_name)
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return None

    def delete_save(self, save_name):
        """
        删除指定名称的存档。

        Args:
            save_name: 存档名称

        Returns:
            bool: 是否删除成功
        """
        file_path = self._get_save_path(save_name)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except OSError:
            pass
        return False

    def save_exists(self, save_name):
        """
        检查指定名称的存档是否存在。

        Args:
            save_name: 存档名称

        Returns:
            bool: 是否存在
        """
        return os.path.exists(self._get_save_path(save_name))

    def add_leaderboard_entry(self, name, score):
        """
        添加排行榜条目。

        Args:
            name: 玩家昵称
            score: 得分

        Returns:
            int: 新条目的排名（1-based）
        """
        entries = self.get_leaderboard()
        new_entry = {
            "name": name,
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        entries.append(new_entry)
        entries.sort(key=lambda x: x["score"], reverse=True)
        entries = entries[:10]

        try:
            with open(self.leaderboard_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

        rank = entries.index(new_entry) + 1 if new_entry in entries else -1
        return rank

    def get_leaderboard(self):
        """
        获取排行榜数据。

        Returns:
            list: 按得分降序排列的排行榜条目列表
        """
        try:
            if os.path.exists(self.leaderboard_file):
                with open(self.leaderboard_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError):
            pass
        return []

    def get_high_score(self):
        """
        获取最高得分。

        Returns:
            int: 最高得分，若无数据则返回 0
        """
        entries = self.get_leaderboard()
        if entries:
            return entries[0]["score"]
        return 0


class Menu:
    """
    基类菜单，提供统一的布局、绘制和事件处理。

    所有具体菜单类都继承自此基类，共享：
    - 半透明背景面板
    - 标题绘制
    - 按钮键盘导航（上下箭头、Enter）
    - 统一的视觉风格

    属性:
        manager: MenuManager 引用
        title: 菜单标题
        buttons: 按钮列表
        selected_index: 当前选中按钮索引（键盘导航）
        audio: AudioManager 引用
    """

    def __init__(self, manager, title=""):
        self.manager = manager
        self.title = title
        self.buttons = []
        self.selected_index = 0
        self.audio = manager.audio if manager else None
        self.panel_width = 500
        self.panel_height = 500
        self._panel_x = (SCREEN_WIDTH - self.panel_width) // 2
        self._panel_y = (SCREEN_HEIGHT - self.panel_height) // 2

    def _layout_buttons(self, button_width=280, button_height=45, spacing=15):
        """
        自动垂直布局按钮。

        Args:
            button_width: 按钮宽度
            button_height: 按钮高度
            spacing: 按钮间距
        """
        total_height = len(self.buttons) * button_height + (len(self.buttons) - 1) * spacing
        start_y = self._panel_y + self.panel_height // 2 - total_height // 2 + 20
        start_x = self._panel_x + (self.panel_width - button_width) // 2

        for i, btn in enumerate(self.buttons):
            btn.rect.x = start_x
            btn.rect.y = start_y + i * (button_height + spacing)
            btn.rect.width = button_width
            btn.rect.height = button_height
            btn.selected = (i == self.selected_index)

    def _update_selection(self, index):
        """更新选中的按钮索引。"""
        if 0 <= index < len(self.buttons):
            for i, btn in enumerate(self.buttons):
                btn.selected = (i == index)
            self.selected_index = index

    def handle_event(self, event):
        """
        处理菜单事件。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 事件是否被处理
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if self.buttons:
                    new_index = (self.selected_index - 1) % len(self.buttons)
                    while new_index != self.selected_index and not self.buttons[new_index].enabled:
                        new_index = (new_index - 1) % len(self.buttons)
                    self._update_selection(new_index)
                    self._play_menu_sound()
                return True

            elif event.key == pygame.K_DOWN:
                if self.buttons:
                    new_index = (self.selected_index + 1) % len(self.buttons)
                    while new_index != self.selected_index and not self.buttons[new_index].enabled:
                        new_index = (new_index + 1) % len(self.buttons)
                    self._update_selection(new_index)
                    self._play_menu_sound()
                return True

            elif event.key == pygame.K_ESCAPE:
                self.on_escape()
                return True

        for i, btn in enumerate(self.buttons):
            if btn.handle_event(event):
                if btn.rect.collidepoint(pygame.mouse.get_pos()):
                    self._update_selection(i)
                self._play_click_sound()
                return True

        return False

    def _play_menu_sound(self):
        """播放菜单导航音效。"""
        if self.audio:
            self.audio.play_sfx(AudioManager.SFX_MENU_CLICK)

    def _play_click_sound(self):
        """播放菜单点击音效。"""
        if self.audio:
            self.audio.play_sfx(AudioManager.SFX_MENU_CLICK)

    def on_escape(self):
        """ESC 键按下时的回调，子类可重写。"""
        pass

    def update(self):
        """更新菜单状态，子类可重写。"""
        pass

    def draw_background(self, surface):
        """
        绘制菜单背景。

        Args:
            surface: 目标绘制 Surface
        """
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

    def draw_panel(self, surface):
        """
        绘制菜单面板。

        Args:
            surface: 目标绘制 Surface
        """
        panel_surf = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        pygame.draw.rect(
            panel_surf, MENU_PANEL_BG,
            (0, 0, self.panel_width, self.panel_height),
            border_radius=15,
        )
        pygame.draw.rect(
            panel_surf, MENU_PANEL_BORDER,
            (0, 0, self.panel_width, self.panel_height),
            width=3, border_radius=15,
        )
        surface.blit(panel_surf, (self._panel_x, self._panel_y))

    def draw_title(self, surface, font):
        """
        绘制菜单标题。

        Args:
            surface: 目标绘制 Surface
            font: 标题字体
        """
        if self.title:
            title_surf = font.render(self.title, True, MENU_TITLE_COLOR)
            title_x = self._panel_x + (self.panel_width - title_surf.get_width()) // 2
            title_y = self._panel_y + 35
            surface.blit(title_surf, (title_x, title_y))

    def draw(self, surface, big_font, normal_font, small_font):
        """
        绘制完整菜单。

        Args:
            surface: 目标绘制 Surface
            big_font: 大字体（标题）
            normal_font: 普通字体（按钮）
            small_font: 小字体（提示）
        """
        self.draw_background(surface)
        self.draw_panel(surface)
        self.draw_title(surface, big_font)

        for btn in self.buttons:
            btn.draw(surface, normal_font)

        hint = small_font.render(
            "↑↓ 导航   Enter 选择   ESC 返回",
            True, MENU_HINT_COLOR
        )
        hint_x = self._panel_x + (self.panel_width - hint.get_width()) // 2
        surface.blit(hint, (hint_x, self._panel_y + self.panel_height - 30))


class MainMenu(Menu):
    """
    主菜单。

    功能按钮：
    - 开始游戏：启动新游戏
    - 加载游戏：从存档继续游戏
    - 排行榜：查看排行榜
    - 设置：打开设置菜单
    - 退出游戏：退出程序
    """

    def __init__(self, manager):
        super().__init__(manager, "平台跳跃")
        self.panel_height = 520

        self.buttons = [
            Button(0, 0, 0, 0, "开始游戏", self._on_start_game),
            Button(0, 0, 0, 0, "加载游戏", self._on_load_game,
                   enabled=self.manager.storage.has_save_game()),
            Button(0, 0, 0, 0, "游戏教程", self._on_tutorial),
            Button(0, 0, 0, 0, "排行榜", self._on_leaderboard),
            Button(0, 0, 0, 0, "设置", self._on_settings),
            Button(0, 0, 0, 0, "退出游戏", self._on_quit),
        ]

        self._layout_buttons()
        self._title_font = get_chinese_font(64)
        self._subtitle_font = get_chinese_font(28)

    def refresh_save_button(self):
        """刷新加载游戏按钮的启用状态。"""
        self.buttons[1].enabled = self.manager.storage.has_save_game()

    def _on_start_game(self):
        """开始新游戏。"""
        self.manager.game.score = 0
        self.manager.game.current_level = 0
        self.manager.start_new_game()
        self.manager.set_state(GameState.PLAYING)

    def _on_load_game(self):
        """打开存档列表菜单。"""
        save_list_menu = self.manager.menus.get(GameState.SAVE_LIST)
        if save_list_menu:
            save_list_menu.refresh()
        self.manager.set_state(GameState.SAVE_LIST)

    def _on_tutorial(self):
        """打开游戏教程。"""
        self.manager.set_state(GameState.TUTORIAL)

    def _on_leaderboard(self):
        """打开排行榜。"""
        self.manager.set_state(GameState.LEADERBOARD)

    def _on_settings(self):
        """打开设置。"""
        self.manager.set_state(GameState.SETTINGS_MENU)

    def _on_quit(self):
        """退出游戏。"""
        self.manager.quit_game()

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制主菜单，包含额外的装饰元素。"""
        super().draw(surface, big_font, normal_font, small_font)

        subtitle = self._subtitle_font.render(
            "跳跃，收集，探索！", True, (180, 200, 255)
        )
        sub_x = self._panel_x + (self.panel_width - subtitle.get_width()) // 2
        surface.blit(subtitle, (sub_x, self._panel_y + 95))

        version = small_font.render("v1.0.0", True, MENU_HINT_COLOR)
        surface.blit(version, (self._panel_x + 20, self._panel_y + self.panel_height - 30))


class SettingsMenu(Menu):
    """
    设置菜单。

    配置选项：
    - 背景音乐音量滑块
    - 音效音量滑块
    - 画质设置（低/中/高）
    - 控制方式（键盘/手柄）
    - 全屏模式开关
    """

    def __init__(self, manager):
        super().__init__(manager, "游戏设置")
        self.panel_height = 580

        settings = manager.storage.load_settings()
        self.bgm_volume = settings.get("bgm_volume", AUDIO_BGM_VOLUME_DEFAULT)
        self.sfx_volume = settings.get("sfx_volume", AUDIO_SFX_VOLUME_DEFAULT)
        self.graphics_quality = settings.get("graphics_quality", "high")
        self.control_mode = settings.get("control_mode", "keyboard")
        self.fullscreen = settings.get("fullscreen", False)

        self.bgm_slider = Slider(
            self._panel_x + 80, self._panel_y + 130,
            280, 10, self.bgm_volume, "背景音乐"
        )
        self.sfx_slider = Slider(
            self._panel_x + 80, self._panel_y + 210,
            280, 10, self.sfx_volume, "音效音量"
        )

        self.quality_options = ["低", "中", "高"]
        self.quality_values = ["low", "medium", "high"]
        self.quality_index = self.quality_values.index(self.graphics_quality)
        self.control_options = ["键盘", "手柄"]
        self.control_values = ["keyboard", "gamepad"]
        self.control_index = self.control_values.index(self.control_mode)

        self.buttons = [
            Button(0, 0, 0, 0, f"画质: {self.quality_options[self.quality_index]}",
                   self._cycle_quality),
            Button(0, 0, 0, 0, f"控制: {self.control_options[self.control_index]}",
                   self._cycle_control),
            Button(0, 0, 0, 0, f"全屏: {'开' if self.fullscreen else '关'}",
                   self._toggle_fullscreen),
            Button(0, 0, 0, 0, "保存并返回", self._on_save_and_back),
        ]

        self._layout_buttons(button_width=280, button_height=40, spacing=12)
        for i, btn in enumerate(self.buttons):
            btn.rect.y = self._panel_y + 290 + i * 52

    def _cycle_quality(self):
        """循环切换画质选项。"""
        self.quality_index = (self.quality_index + 1) % len(self.quality_options)
        self.graphics_quality = self.quality_values[self.quality_index]
        self.buttons[0].text = f"画质: {self.quality_options[self.quality_index]}"

    def _cycle_control(self):
        """循环切换控制方式。"""
        self.control_index = (self.control_index + 1) % len(self.control_options)
        self.control_mode = self.control_values[self.control_index]
        self.buttons[1].text = f"控制: {self.control_options[self.control_index]}"

    def _toggle_fullscreen(self):
        """切换全屏模式。"""
        self.fullscreen = not self.fullscreen
        self.buttons[2].text = f"全屏: {'开' if self.fullscreen else '关'}"

    def _on_save_and_back(self):
        """保存设置并返回。"""
        settings = {
            "bgm_volume": self.bgm_volume,
            "sfx_volume": self.sfx_volume,
            "graphics_quality": self.graphics_quality,
            "control_mode": self.control_mode,
            "fullscreen": self.fullscreen,
        }
        self.manager.storage.save_settings(settings)

        if self.manager.game.audio:
            self.manager.game.audio.set_bgm_volume(self.bgm_volume)
            self.manager.game.audio.set_sfx_volume(self.sfx_volume)

        self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回主菜单。"""
        self._on_save_and_back()

    def handle_event(self, event):
        """处理设置菜单事件，包括滑块。"""
        if self.bgm_slider.handle_event(event):
            self.bgm_volume = self.bgm_slider.value
            if self.manager.game.audio:
                self.manager.game.audio.set_bgm_volume(self.bgm_volume)

        if self.sfx_slider.handle_event(event):
            self.sfx_volume = self.sfx_slider.value
            if self.manager.game.audio:
                self.manager.game.audio.set_sfx_volume(self.sfx_volume)

        return super().handle_event(event)

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制设置菜单，包含滑块。"""
        super().draw(surface, big_font, normal_font, small_font)

        self.bgm_slider.draw(surface, normal_font)
        self.sfx_slider.draw(surface, normal_font)


class PauseMenu(Menu):
    """
    暂停菜单。

    功能按钮：
    - 继续游戏：返回游戏
    - 保存游戏：保存当前进度
    - 重新开始：重新开始当前关卡
    - 返回主菜单：退出到主菜单
    """

    def __init__(self, manager):
        super().__init__(manager, "游戏暂停")
        self.panel_height = 420

        self.buttons = [
            Button(0, 0, 0, 0, "继续游戏", self._on_resume),
            Button(0, 0, 0, 0, "保存游戏", self._on_save),
            Button(0, 0, 0, 0, "重新开始", self._on_restart),
            Button(0, 0, 0, 0, "返回主菜单", self._on_main_menu),
        ]

        self._layout_buttons()

    def _on_resume(self):
        """继续游戏。"""
        self.manager.set_state(GameState.PLAYING)

    def _on_save(self):
        """保存游戏，打开命名输入菜单。"""
        save_name_input = self.manager.menus.get(GameState.SAVE_NAME_INPUT)
        if save_name_input:
            save_name_input.reset()
        self.manager.set_state(GameState.SAVE_NAME_INPUT)

    def _on_restart(self):
        """重新开始当前关卡。"""
        from config import PLAYER_SPAWN_X, PLAYER_SPAWN_Y
        self.manager.game._load_level(
            self.manager.game.current_level,
            PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
            immediate=True
        )
        self.manager.set_state(GameState.PLAYING)

    def _on_main_menu(self):
        """返回主菜单。"""
        self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 继续游戏。"""
        self._on_resume()


class GameOverMenu(Menu):
    """
    游戏结束菜单。

    显示内容：
    - 本局得分
    - 历史最高得分
    - 玩家昵称输入（如果进入排行榜）
    - 重新挑战按钮
    - 返回主菜单按钮
    """

    def __init__(self, manager):
        super().__init__(manager, "游戏结束")
        self.panel_height = 520

        self.final_score = 0
        self.high_score = 0
        self.is_new_high_score = False
        self.player_name = ""
        self.name_input_active = False
        self.name_max_length = 12

        self.buttons = [
            Button(0, 0, 0, 0, "提交得分", self._on_submit_score),
            Button(0, 0, 0, 0, "重新挑战", self._on_retry),
            Button(0, 0, 0, 0, "返回主菜单", self._on_main_menu),
        ]

        self._layout_buttons()
        for i, btn in enumerate(self.buttons):
            btn.rect.y = self._panel_y + 340 + i * 55

        self._title_font = get_chinese_font(56)
        self._score_font = get_chinese_font(42)
        self._small_font = get_chinese_font(26)

    def set_score(self, score):
        """
        设置本局得分并检查是否创造新纪录。

        Args:
            score: 本局得分
        """
        self.final_score = score
        self.high_score = self.manager.storage.get_high_score()
        self.is_new_high_score = score > self.high_score and score > 0
        self.player_name = ""
        self.name_input_active = self.is_new_high_score
        self.buttons[0].enabled = self.is_new_high_score

    def _on_submit_score(self):
        """提交得分到排行榜。"""
        if self.player_name.strip():
            rank = self.manager.storage.add_leaderboard_entry(
                self.player_name.strip(), self.final_score
            )
            self.name_input_active = False
            self.buttons[0].enabled = False
            self.high_score = self.manager.storage.get_high_score()
            self.is_new_high_score = False

    def _on_retry(self):
        """重新挑战。"""
        from config import PLAYER_SPAWN_X, PLAYER_SPAWN_Y
        self.manager.game.score = 0
        self.manager.game._load_level(
            0, PLAYER_SPAWN_X, PLAYER_SPAWN_Y, immediate=True
        )
        self.manager.set_state(GameState.PLAYING)

    def _on_main_menu(self):
        """返回主菜单。"""
        self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回主菜单。"""
        self._on_main_menu()

    def handle_event(self, event):
        """处理游戏结束菜单事件，包括昵称输入。"""
        if self.name_input_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
                return True
            elif event.key == pygame.K_RETURN:
                self._on_submit_score()
                return True
            elif len(self.player_name) < self.name_max_length:
                char = event.unicode
                if char.isprintable() and not char.isspace():
                    self.player_name += char
                    return True

        return super().handle_event(event)

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制游戏结束菜单，包含得分展示和昵称输入。"""
        super().draw(surface, big_font, normal_font, small_font)

        center_x = SCREEN_WIDTH // 2

        if self.is_new_high_score:
            new_record = self._small_font.render(
                "★ 新纪录！★", True, (255, 215, 0)
            )
            surface.blit(
                new_record,
                (center_x - new_record.get_width() // 2, self._panel_y + 90)
            )

        score_label = self._small_font.render("本局得分", True, MENU_TEXT_COLOR)
        surface.blit(
            score_label,
            (center_x - score_label.get_width() // 2, self._panel_y + 130)
        )

        score_text = self._score_font.render(
            f"{self.final_score}", True, (100, 200, 255)
        )
        surface.blit(
            score_text,
            (center_x - score_text.get_width() // 2, self._panel_y + 160)
        )

        high_label = self._small_font.render("最高得分", True, MENU_TEXT_COLOR)
        surface.blit(
            high_label,
            (center_x - high_label.get_width() // 2, self._panel_y + 215)
        )

        high_text = self._score_font.render(
            f"{self.high_score}", True, (255, 215, 0)
        )
        surface.blit(
            high_text,
            (center_x - high_text.get_width() // 2, self._panel_y + 245)
        )

        if self.name_input_active:
            name_label = self._small_font.render(
                "输入昵称:", True, MENU_TEXT_COLOR
            )
            surface.blit(
                name_label,
                (center_x - 120, self._panel_y + 295)
            )

            input_rect = pygame.Rect(center_x - 40, self._panel_y + 290, 160, 32)
            pygame.draw.rect(surface, (30, 30, 50), input_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 200, 255), input_rect, width=2, border_radius=5)

            display_name = self.player_name
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                display_name += "|"

            name_text = normal_font.render(display_name, True, MENU_TEXT_COLOR)
            surface.blit(name_text, (input_rect.x + 8, input_rect.y + 3))


class LeaderboardMenu(Menu):
    """
    排行榜菜单。

    显示内容：
    - 排名（1-10）
    - 玩家昵称
    - 得分
    - 获得日期
    """

    def __init__(self, manager):
        super().__init__(manager, "排行榜")
        self.panel_height = 560
        self.entries = []

        self.buttons = [
            Button(0, 0, 0, 0, "返回主菜单", self._on_back),
        ]

        self._layout_buttons(button_width=200, button_height=40)
        self.buttons[0].rect.y = self._panel_y + self.panel_height - 70
        self.buttons[0].rect.x = self._panel_x + (self.panel_width - 200) // 2

        self._rank_font = get_chinese_font(24)
        self._header_font = get_chinese_font(28)

    def refresh(self):
        """刷新排行榜数据。"""
        self.entries = self.manager.storage.get_leaderboard()

    def _on_back(self):
        """返回主菜单。"""
        self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回主菜单。"""
        self._on_back()

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制排行榜菜单，包含排名列表。"""
        super().draw(surface, big_font, normal_font, small_font)

        header_y = self._panel_y + 90
        col1_x = self._panel_x + 40
        col2_x = self._panel_x + 100
        col3_x = self._panel_x + 280
        col4_x = self._panel_x + 400

        headers = ["排名", "昵称", "得分", "日期"]
        header_x = [col1_x, col2_x, col3_x, col4_x]
        for i, h in enumerate(headers):
            text = self._header_font.render(h, True, (180, 200, 255))
            surface.blit(text, (header_x[i], header_y))

        pygame.draw.line(
            surface, (100, 150, 255),
            (self._panel_x + 30, header_y + 30),
            (self._panel_x + self.panel_width - 30, header_y + 30),
            2
        )

        if not self.entries:
            no_data = self._rank_font.render(
                "暂无记录，快去创造历史吧！", True, MENU_HINT_COLOR
            )
            surface.blit(
                no_data,
                (self._panel_x + (self.panel_width - no_data.get_width()) // 2,
                 self._panel_y + 250)
            )
        else:
            for i, entry in enumerate(self.entries[:10]):
                row_y = header_y + 45 + i * 32

                if i == 0:
                    rank_color = (255, 215, 0)
                elif i == 1:
                    rank_color = (192, 192, 192)
                elif i == 2:
                    rank_color = (205, 127, 50)
                else:
                    rank_color = MENU_TEXT_COLOR

                rank_text = self._rank_font.render(f"{i + 1}", True, rank_color)
                surface.blit(rank_text, (col1_x, row_y))

                name_text = self._rank_font.render(
                    entry.get("name", ""), True, MENU_TEXT_COLOR
                )
                surface.blit(name_text, (col2_x, row_y))

                score_text = self._rank_font.render(
                    str(entry.get("score", 0)), True, (100, 200, 255)
                )
                surface.blit(score_text, (col3_x, row_y))

                date_text = self._rank_font.render(
                    entry.get("date", ""), True, MENU_HINT_COLOR
                )
                surface.blit(date_text, (col4_x, row_y))


class SaveNameInputMenu(Menu):
    """
    保存时输入存档名称的菜单。

    功能：
    - 文本输入框用于输入存档名称
    - 确认保存按钮
    - 取消按钮
    - 如果存档已存在，会提示覆盖确认
    """

    def __init__(self, manager):
        super().__init__(manager, "保存游戏")
        self.panel_height = 380
        self.save_name = ""
        self.name_max_length = 20
        self.input_active = True
        self.confirm_overwrite = False
        self.pending_save_name = ""

        self.buttons = [
            Button(0, 0, 0, 0, "保存", self._on_save),
            Button(0, 0, 0, 0, "取消", self._on_cancel),
        ]

        self._layout_buttons(button_width=180, button_height=40, spacing=15)
        self.buttons[0].rect.x = self._panel_x + 70
        self.buttons[0].rect.y = self._panel_y + self.panel_height - 100
        self.buttons[1].rect.x = self._panel_x + self.panel_width - 250
        self.buttons[1].rect.y = self._panel_y + self.panel_height - 100

        self._hint_font = get_chinese_font(24)

    def reset(self):
        """重置输入状态。"""
        self.save_name = ""
        self.input_active = True
        self.confirm_overwrite = False
        self.pending_save_name = ""
        self.selected_index = 0
        self._update_selection(0)

    def _on_save(self):
        """确认保存按钮回调。"""
        name = self.save_name.strip()
        if not name:
            name = "未命名"

        if self.manager.storage.save_exists(name) and not self.confirm_overwrite:
            self.pending_save_name = name
            self.confirm_overwrite = True
            self.buttons[0].text = "确认覆盖"
            return

        game_data = {
            "score": self.manager.game.score,
            "level": self.manager.game.current_level,
            "spawn_x": self.manager.game.player.x,
            "spawn_y": self.manager.game.player.y,
        }
        self.manager.storage.save_named_game(name, game_data)

        self.confirm_overwrite = False
        self.pending_save_name = ""
        self.buttons[0].text = "保存"

        self.manager.set_state(GameState.PAUSED)

    def _on_cancel(self):
        """取消按钮回调。"""
        self.confirm_overwrite = False
        self.pending_save_name = ""
        self.buttons[0].text = "保存"
        if self.manager.previous_state == GameState.PAUSED:
            self.manager.set_state(GameState.PAUSED)
        else:
            self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回。"""
        self._on_cancel()

    def handle_event(self, event):
        """处理输入菜单事件，包括文本输入。"""
        if self.input_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.save_name = self.save_name[:-1]
                return True
            elif event.key == pygame.K_RETURN:
                if self.confirm_overwrite:
                    self._on_save()
                else:
                    self._on_save()
                return True
            elif len(self.save_name) < self.name_max_length:
                char = event.unicode
                if char.isprintable():
                    self.save_name += char
                    self.confirm_overwrite = False
                    self.buttons[0].text = "保存"
                    return True

        return super().handle_event(event)

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制保存名称输入菜单。"""
        super().draw(surface, big_font, normal_font, small_font)

        center_x = SCREEN_WIDTH // 2
        input_y = self._panel_y + 140

        label = normal_font.render("存档名称:", True, MENU_TEXT_COLOR)
        surface.blit(label, (center_x - 180, input_y))

        input_rect = pygame.Rect(center_x - 60, input_y - 5, 240, 36)
        pygame.draw.rect(surface, (30, 30, 50), input_rect, border_radius=5)
        pygame.draw.rect(surface, (100, 200, 255), input_rect, width=2, border_radius=5)

        display_name = self.save_name
        if self.input_active and (pygame.time.get_ticks() // 500) % 2 == 0:
            display_name += "|"

        name_text = normal_font.render(display_name, True, MENU_TEXT_COLOR)
        surface.blit(name_text, (input_rect.x + 8, input_rect.y + 4))

        hint = self._hint_font.render(
            f"最多 {self.name_max_length} 个字符", True, MENU_HINT_COLOR
        )
        surface.blit(hint, (center_x - 60, input_y + 40))

        if self.confirm_overwrite:
            warn = self._hint_font.render(
                f"存档 '{self.pending_save_name}' 已存在，确定覆盖？",
                True, (255, 200, 100)
            )
            surface.blit(
                warn,
                (center_x - warn.get_width() // 2, input_y + 75)
            )


class SaveListMenu(Menu):
    """
    存档列表菜单。

    功能：
    - 显示所有存档列表（名称、关卡、得分、保存时间）
    - 选择并加载存档
    - 删除存档（带确认）
    - 支持鼠标和键盘导航
    - 可配置为"加载模式"或"选择模式"
    """

    def __init__(self, manager, mode="load"):
        super().__init__(manager, "选择存档")
        self.panel_height = 560
        self.mode = mode
        self.saves = []
        self.selected_save_index = 0
        self.delete_confirm_index = -1
        self.scroll_offset = 0
        self.max_visible = 5

        self.buttons = [
            Button(0, 0, 0, 0, "加载", self._on_load),
            Button(0, 0, 0, 0, "删除", self._on_delete),
            Button(0, 0, 0, 0, "返回", self._on_back),
        ]

        self._layout_buttons(button_width=140, button_height=38, spacing=10)
        btn_start_y = self._panel_y + self.panel_height - 70
        self.buttons[0].rect.x = self._panel_x + 50
        self.buttons[0].rect.y = btn_start_y
        self.buttons[1].rect.x = self._panel_x + self.panel_width // 2 - 70
        self.buttons[1].rect.y = btn_start_y
        self.buttons[2].rect.x = self._panel_x + self.panel_width - 190
        self.buttons[2].rect.y = btn_start_y

        self._save_name_font = get_chinese_font(24)
        self._save_info_font = get_chinese_font(20)
        self._header_font = get_chinese_font(22)

    def refresh(self):
        """刷新存档列表。"""
        self.saves = self.manager.storage.list_saves()
        self.selected_save_index = 0
        self.delete_confirm_index = -1
        self.scroll_offset = 0
        self._update_buttons_state()

    def _update_buttons_state(self):
        """更新按钮启用状态。"""
        has_saves = len(self.saves) > 0
        self.buttons[0].enabled = has_saves
        self.buttons[1].enabled = has_saves

    def _on_load(self):
        """加载选中的存档。"""
        if not self.saves or self.selected_save_index >= len(self.saves):
            return

        save_name = self.saves[self.selected_save_index]["name"]
        save_data = self.manager.storage.load_named_game(save_name)

        if save_data:
            self.manager.game.score = save_data.get("score", 0)
            self.manager.game.current_level = save_data.get("level", 0)
            spawn_x = save_data.get("spawn_x", 100)
            spawn_y = save_data.get("spawn_y", 400)
            self.manager.game._load_level(
                self.manager.game.current_level, spawn_x, spawn_y, immediate=True
            )
            self.manager.set_state(GameState.PLAYING)

    def _on_delete(self):
        """删除选中的存档。"""
        if not self.saves or self.selected_save_index >= len(self.saves):
            return

        if self.delete_confirm_index == self.selected_save_index:
            save_name = self.saves[self.selected_save_index]["name"]
            self.manager.storage.delete_save(save_name)
            self.refresh()

            main_menu = self.manager.menus.get(GameState.MAIN_MENU)
            if main_menu:
                main_menu.refresh_save_button()
        else:
            self.delete_confirm_index = self.selected_save_index

    def _on_back(self):
        """返回上一级菜单。"""
        self.delete_confirm_index = -1
        if self.manager.previous_state == GameState.PAUSED:
            self.manager.set_state(GameState.PAUSED)
        else:
            self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回。"""
        self._on_back()

    def handle_event(self, event):
        """处理存档列表菜单事件。"""
        if event.type == pygame.KEYDOWN and self.saves:
            if event.key == pygame.K_UP:
                self._select_previous()
                self._play_menu_sound()
                return True
            elif event.key == pygame.K_DOWN:
                self._select_next()
                self._play_menu_sound()
                return True
            elif event.key == pygame.K_RETURN:
                if self.delete_confirm_index == self.selected_save_index:
                    self._on_delete()
                else:
                    self._on_load()
                return True
            elif event.key == pygame.K_DELETE or event.key == pygame.K_d:
                self._on_delete()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._check_save_click(event.pos):
                return True

        return super().handle_event(event)

    def _select_previous(self):
        """选择上一个存档。"""
        if self.saves:
            self.selected_save_index = (self.selected_save_index - 1) % len(self.saves)
            self.delete_confirm_index = -1
            self._adjust_scroll()

    def _select_next(self):
        """选择下一个存档。"""
        if self.saves:
            self.selected_save_index = (self.selected_save_index + 1) % len(self.saves)
            self.delete_confirm_index = -1
            self._adjust_scroll()

    def _adjust_scroll(self):
        """调整滚动偏移以确保选中项可见。"""
        if self.selected_save_index < self.scroll_offset:
            self.scroll_offset = self.selected_save_index
        elif self.selected_save_index >= self.scroll_offset + self.max_visible:
            self.scroll_offset = self.selected_save_index - self.max_visible + 1

    def _check_save_click(self, pos):
        """检查是否点击了某个存档项。"""
        list_x = self._panel_x + 30
        list_y = self._panel_y + 90
        item_height = 60

        for i in range(self.max_visible):
            save_idx = self.scroll_offset + i
            if save_idx >= len(self.saves):
                break

            item_rect = pygame.Rect(list_x, list_y + i * item_height, self.panel_width - 60, item_height - 8)
            if item_rect.collidepoint(pos):
                self.selected_save_index = save_idx
                self.delete_confirm_index = -1
                return True

        return False

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制存档列表菜单。"""
        super().draw(surface, big_font, normal_font, small_font)

        list_x = self._panel_x + 30
        list_y = self._panel_y + 90
        item_height = 60
        list_width = self.panel_width - 60

        header_bg = pygame.Rect(list_x, list_y - 30, list_width, 28)
        pygame.draw.rect(surface, (50, 50, 90), header_bg, border_radius=5)

        name_header = self._header_font.render("存档名称", True, (180, 200, 255))
        surface.blit(name_header, (list_x + 10, list_y - 27))

        level_header = self._header_font.render("关卡", True, (180, 200, 255))
        surface.blit(level_header, (list_x + 220, list_y - 27))

        score_header = self._header_font.render("得分", True, (180, 200, 255))
        surface.blit(score_header, (list_x + 300, list_y - 27))

        if not self.saves:
            no_data = self._save_info_font.render(
                "暂无存档", True, MENU_HINT_COLOR
            )
            surface.blit(
                no_data,
                (list_x + (list_width - no_data.get_width()) // 2,
                 list_y + 80)
            )
            return

        for i in range(self.max_visible):
            save_idx = self.scroll_offset + i
            if save_idx >= len(self.saves):
                break

            save = self.saves[save_idx]
            is_selected = save_idx == self.selected_save_index
            is_delete_confirm = save_idx == self.delete_confirm_index

            item_y = list_y + i * item_height
            item_rect = pygame.Rect(list_x, item_y, list_width, item_height - 8)

            if is_selected:
                pygame.draw.rect(surface, (80, 120, 200), item_rect, border_radius=6)
                pygame.draw.rect(surface, BUTTON_BORDER, item_rect, width=2, border_radius=6)
            else:
                pygame.draw.rect(surface, (45, 45, 75), item_rect, border_radius=6)

            name_text = self._save_name_font.render(
                save["name"], True, MENU_TITLE_COLOR
            )
            surface.blit(name_text, (list_x + 12, item_y + 6))

            level_text = self._save_info_font.render(
                f"第 {save.get('level', 0) + 1} 关", True, MENU_TEXT_COLOR
            )
            surface.blit(level_text, (list_x + 220, item_y + 10))

            score_text = self._save_info_font.render(
                str(save.get("score", 0)), True, (100, 200, 255)
            )
            surface.blit(score_text, (list_x + 300, item_y + 10))

            time_text = self._save_info_font.render(
                save.get("timestamp", "")[:16].replace("T", " "),
                True, MENU_HINT_COLOR
            )
            surface.blit(time_text, (list_x + 12, item_y + 32))

            if is_delete_confirm:
                confirm_text = self._save_info_font.render(
                    "按删除键或再次点击确认删除", True, (255, 150, 100)
                )
                surface.blit(
                    confirm_text,
                    (list_x + list_width - confirm_text.get_width() - 10, item_y + 32)
                )

        if len(self.saves) > self.max_visible:
            scroll_x = list_x + list_width + 5
            scroll_bg = pygame.Rect(scroll_x, list_y, 6, self.max_visible * item_height - 8)
            pygame.draw.rect(surface, (40, 40, 70), scroll_bg, border_radius=3)

            total = len(self.saves)
            thumb_height = int((self.max_visible / total) * (self.max_visible * item_height - 8))
            thumb_y = list_y + int((self.scroll_offset / total) * (self.max_visible * item_height - 8))
            scroll_thumb = pygame.Rect(scroll_x, thumb_y, 6, max(thumb_height, 10))
            pygame.draw.rect(surface, (100, 150, 200), scroll_thumb, border_radius=3)


class MenuManager:
    """
    菜单状态管理器。

    负责：
    - 管理所有菜单实例
    - 处理游戏状态切换
    - 协调菜单与游戏逻辑的交互
    - 事件分发和渲染调度

    属性:
        game: Game 主类引用
        audio: AudioManager 引用
        storage: StorageManager 实例
        current_state: 当前游戏状态
        menus: 所有菜单实例字典
    """

    def __init__(self, game):
        self.game = game
        self.audio = game.audio if hasattr(game, 'audio') else None
        self.storage = StorageManager()
        self.current_state = GameState.MAIN_MENU
        self.previous_state = None

        from tutorial import TutorialMenu

        self.menus = {
            GameState.MAIN_MENU: MainMenu(self),
            GameState.SETTINGS_MENU: SettingsMenu(self),
            GameState.PAUSED: PauseMenu(self),
            GameState.GAME_OVER: GameOverMenu(self),
            GameState.LEADERBOARD: LeaderboardMenu(self),
            GameState.TUTORIAL: TutorialMenu(self),
            GameState.SAVE_LIST: SaveListMenu(self),
            GameState.SAVE_NAME_INPUT: SaveNameInputMenu(self),
        }

        self._apply_saved_settings()

    def _apply_saved_settings(self):
        """应用保存的设置。"""
        settings = self.storage.load_settings()
        if self.audio:
            self.audio.set_bgm_volume(settings.get("bgm_volume", AUDIO_BGM_VOLUME_DEFAULT))
            self.audio.set_sfx_volume(settings.get("sfx_volume", AUDIO_SFX_VOLUME_DEFAULT))

    def set_state(self, new_state):
        """
        切换游戏状态。

        Args:
            new_state: 目标状态（GameState 枚举）
        """
        self.previous_state = self.current_state
        self.current_state = new_state

        if new_state in self.menus or new_state == GameState.PLAYING:
            switch_to_english_keyboard()

        if new_state == GameState.PLAYING:
            if self.audio and not self.audio.is_bgm_playing():
                self.game.audio.play_bgm(f"level_{self.game.current_level % 3}")

        elif new_state == GameState.PAUSED:
            if self.audio:
                self.audio.pause_bgm()

        elif new_state == GameState.MAIN_MENU:
            main_menu = self.menus[GameState.MAIN_MENU]
            main_menu.refresh_save_button()
            main_menu.selected_index = 0
            main_menu._update_selection(0)
            if self.audio:
                self.audio.resume_bgm()
                self.game.audio.play_bgm("level_0")

        elif new_state == GameState.LEADERBOARD:
            self.menus[GameState.LEADERBOARD].refresh()

        elif new_state == GameState.TUTORIAL:
            self.menus[GameState.TUTORIAL].reset_state()

        if new_state in self.menus:
            menu = self.menus[new_state]
            menu.selected_index = 0
            for i, btn in enumerate(menu.buttons):
                btn.selected = (i == 0)

    def start_new_game(self):
        """启动新游戏。"""
        from config import PLAYER_SPAWN_X, PLAYER_SPAWN_Y
        self.game.score = 0
        self.game.current_level = 0
        self.game._load_level(0, PLAYER_SPAWN_X, PLAYER_SPAWN_Y, immediate=True)

    def trigger_game_over(self, score):
        """
        触发游戏结束。

        Args:
            score: 本局得分
        """
        self.menus[GameState.GAME_OVER].set_score(score)
        self.set_state(GameState.GAME_OVER)
        if self.audio:
            self.audio.play_sfx(AudioManager.SFX_DEATH)
            self.audio.stop_bgm()

    def quit_game(self):
        """退出游戏。"""
        if self.audio:
            self.audio.shutdown()
        pygame.quit()
        import sys
        sys.exit(0)

    def handle_event(self, event):
        """
        处理全局事件，分发给当前活动菜单。

        Args:
            event: pygame 事件对象

        Returns:
            bool: 事件是否被处理
        """
        if self.current_state in self.menus:
            return self.menus[self.current_state].handle_event(event)
        return False

    def update(self):
        """更新当前活动菜单。"""
        if self.current_state in self.menus:
            self.menus[self.current_state].update()

    def draw(self, surface, big_font, normal_font, small_font):
        """
        绘制当前活动菜单。

        Args:
            surface: 目标绘制 Surface
            big_font: 大字体
            normal_font: 普通字体
            small_font: 小字体
        """
        if self.current_state in self.menus:
            self.menus[self.current_state].draw(
                surface, big_font, normal_font, small_font
            )

    def is_menu_active(self):
        """
        检查当前是否处于菜单状态。

        Returns:
            bool: 是否在菜单中
        """
        return self.current_state in self.menus


from tutorial import TutorialMenu  # noqa: E402

__all__ = [
    "Button",
    "Menu",
    "GameState",
    "MainMenu",
    "SettingsMenu",
    "PauseMenu",
    "GameOverMenu",
    "LeaderboardMenu",
    "TutorialMenu",
    "SaveListMenu",
    "SaveNameInputMenu",
    "StorageManager",
    "MenuManager",
    "get_chinese_font",
    "MENU_BG_COLOR",
    "MENU_PANEL_COLOR",
    "MENU_PANEL_BORDER",
    "MENU_TITLE_COLOR",
    "MENU_TEXT_COLOR",
    "MENU_HINT_COLOR",
    "BUTTON_BG",
    "BUTTON_BG_HOVER",
    "BUTTON_BG_SELECTED",
    "BUTTON_BG_DISABLED",
    "BUTTON_BORDER",
    "BUTTON_TEXT",
    "BUTTON_TEXT_DISABLED",
    "SLIDER_BG",
    "SLIDER_FG",
    "SLIDER_KNOB",
]
