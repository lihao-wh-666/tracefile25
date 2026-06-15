# -*- coding: utf-8 -*-
"""
test_menus.py - 菜单系统模块测试

测试范围:
- GameState 枚举常量
- Button 按钮组件（鼠标/键盘事件/绘制）
- Slider 滑块组件（菜单内）
- StorageManager 持久化（设置/存档/排行榜）
- MenuManager 菜单状态管理
"""

import os
import sys
import json
import pytest
import tempfile
import shutil

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from menus import (
    GameState,
    Button,
    Slider,
    StorageManager,
    MenuManager,
    get_chinese_font,
)


@pytest.fixture(scope="session")
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def temp_save_dir(monkeypatch):
    """临时保存目录夹具。"""
    tmpdir = tempfile.mkdtemp()
    fake_home = tmpdir

    def fake_expanduser(path):
        if path == "~":
            return fake_home
        return os.path.join(fake_home, path[2:]) if path.startswith("~/") else path

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestGameState:
    """GameState 枚举测试。"""

    def test_state_values_exist(self):
        """测试所有状态常量存在。"""
        assert GameState.MAIN_MENU == "main_menu"
        assert GameState.SETTINGS_MENU == "settings_menu"
        assert GameState.PAUSED == "paused"
        assert GameState.GAME_OVER == "game_over"
        assert GameState.LEADERBOARD == "leaderboard"
        assert GameState.PLAYING == "playing"
        assert GameState.TRANSITIONING == "transitioning"
        assert GameState.LOADING == "loading"

    def test_states_unique(self):
        """测试所有状态值互不相同。"""
        states = [
            GameState.MAIN_MENU, GameState.SETTINGS_MENU,
            GameState.PAUSED, GameState.GAME_OVER,
            GameState.LEADERBOARD, GameState.PLAYING,
            GameState.TRANSITIONING, GameState.LOADING,
        ]
        assert len(states) == len(set(states))


class TestButton:
    """Button 按钮组件测试。"""

    def test_init(self):
        """测试按钮初始化。"""
        called = []

        def cb():
            called.append(True)

        btn = Button(10, 20, 100, 40, "Test", callback=cb, enabled=True)
        assert btn.rect.x == 10
        assert btn.rect.y == 20
        assert btn.rect.width == 100
        assert btn.rect.height == 40
        assert btn.text == "Test"
        assert btn.callback is cb
        assert btn.enabled is True
        assert btn.selected is False
        assert btn.hover is False

    def test_init_defaults(self):
        """测试按钮默认参数。"""
        btn = Button(0, 0, 50, 30, "OK")
        assert btn.callback is None
        assert btn.enabled is True

    def test_mouse_motion_hover(self):
        """测试鼠标移动更新悬停状态。"""
        btn = Button(0, 0, 100, 50, "T")
        event = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (50, 25)})
        btn.handle_event(event)
        assert btn.hover is True
        event2 = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (200, 200)})
        btn.handle_event(event2)
        assert btn.hover is False

    def test_mouse_click_triggers_callback(self):
        """测试鼠标点击触发回调。"""
        calls = []

        def cb():
            calls.append(1)

        btn = Button(0, 0, 100, 50, "T", callback=cb)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (50, 25)})
        triggered = btn.handle_event(event)
        assert triggered is True
        assert len(calls) == 1
        assert btn._click_anim > 0

    def test_mouse_click_outside_no_trigger(self):
        """测试按钮外点击不触发。"""
        calls = []

        def cb():
            calls.append(1)

        btn = Button(0, 0, 100, 50, "T", callback=cb)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (200, 200)})
        triggered = btn.handle_event(event)
        assert triggered is False
        assert len(calls) == 0

    def test_disabled_click_no_trigger(self):
        """测试禁用按钮点击不触发。"""
        calls = []
        btn = Button(0, 0, 100, 50, "T", callback=lambda: calls.append(1), enabled=False)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (50, 25)})
        triggered = btn.handle_event(event)
        assert triggered is False
        assert len(calls) == 0

    def test_keyboard_enter_selected(self):
        """测试选中状态下 Enter 触发。"""
        calls = []
        btn = Button(0, 0, 100, 50, "T", callback=lambda: calls.append(1))
        btn.selected = True
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        triggered = btn.handle_event(event)
        assert triggered is True
        assert len(calls) == 1

    def test_keyboard_space_selected(self):
        """测试选中状态下 Space 触发。"""
        calls = []
        btn = Button(0, 0, 100, 50, "T", callback=lambda: calls.append(1))
        btn.selected = True
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE})
        triggered = btn.handle_event(event)
        assert triggered is True
        assert len(calls) == 1

    def test_keyboard_not_selected_no_trigger(self):
        """测试非选中状态按键不触发。"""
        calls = []
        btn = Button(0, 0, 100, 50, "T", callback=lambda: calls.append(1))
        btn.selected = False
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
        triggered = btn.handle_event(event)
        assert triggered is False
        assert len(calls) == 0

    def test_right_click_ignored(self):
        """测试右键点击被忽略。"""
        calls = []
        btn = Button(0, 0, 100, 50, "T", callback=lambda: calls.append(1))
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (50, 25)})
        triggered = btn.handle_event(event)
        assert triggered is False
        assert len(calls) == 0

    def test_draw_no_crash(self, pygame_session):
        """测试绘制不崩溃。"""
        btn = Button(10, 10, 100, 40, "Test")
        font = get_chinese_font(16)
        surf = pygame.Surface((300, 200))
        btn.draw(surf, font)
        btn.hover = True
        btn.draw(surf, font)
        btn.selected = True
        btn.hover = False
        btn.draw(surf, font)
        btn.enabled = False
        btn.draw(surf, font)


class TestMenuSlider:
    """菜单 Slider 滑块测试。"""

    def test_init(self):
        """测试滑块初始化。"""
        slider = Slider(50, 100, 200, 10, 0.4, "音量")
        assert slider.x == 50
        assert slider.y == 100
        assert slider.width == 200
        assert slider.height == 10
        assert abs(slider.value - 0.4) < 0.001
        assert slider.label == "音量"
        assert slider.dragging is False

    def test_init_clamp(self):
        """测试初始值被钳制。"""
        slider = Slider(0, 0, 100, 10, 5.0)
        assert abs(slider.value - 1.0) < 0.001

    def test_handle_mouse_down(self):
        """测试鼠标按下。"""
        slider = Slider(100, 100, 200, 10, 0.0)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (200, 105)})
        changed = slider.handle_event(event)
        assert slider.dragging is True
        assert changed is True
        assert abs(slider.value - 0.5) < 0.01

    def test_handle_mouse_up(self):
        """测试鼠标释放。"""
        slider = Slider(0, 0, 100, 10, 0.5)
        slider.dragging = True
        event = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1})
        slider.handle_event(event)
        assert slider.dragging is False

    def test_handle_mouse_drag(self):
        """测试拖拽移动。"""
        slider = Slider(0, 0, 200, 10, 0.0)
        slider.dragging = True
        event = pygame.event.Event(
            pygame.MOUSEMOTION, {"pos": (100, 5)})
        changed = slider.handle_event(event)
        assert changed is True
        assert abs(slider.value - 0.5) < 0.01

    def test_keyboard_left_right(self):
        """测试键盘左右调节（hover时）。"""
        slider = Slider(0, 0, 100, 10, 0.5)
        slider.hover = True
        event_l = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT})
        for _ in range(5):
            slider.handle_event(event_l)
        assert slider.value < 0.5

        event_r = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT})
        start = slider.value
        for _ in range(10):
            slider.handle_event(event_r)
        assert slider.value > start

    def test_draw_no_crash(self, pygame_session):
        """测试绘制不崩溃。"""
        slider = Slider(20, 50, 200, 10, 0.6, "Test")
        font = get_chinese_font(14)
        surf = pygame.Surface((400, 150))
        slider.draw(surf, font)
        slider.dragging = True
        slider.draw(surf, font)


class TestStorageManager:
    """StorageManager 持久化管理测试。"""

    def test_directory_created(self, temp_save_dir):
        """测试保存目录自动创建。"""
        sm = StorageManager()
        assert os.path.exists(sm.save_dir)
        assert ".platform_jumper" in sm.save_dir

    def test_save_and_load_settings(self, temp_save_dir):
        """测试保存和加载设置。"""
        sm = StorageManager()
        settings = {
            "bgm_volume": 0.5,
            "sfx_volume": 0.7,
            "graphics_quality": "medium",
            "control_mode": "keyboard",
            "fullscreen": False,
        }
        sm.save_settings(settings)
        loaded = sm.load_settings()
        assert loaded["bgm_volume"] == 0.5
        assert loaded["sfx_volume"] == 0.7
        assert loaded["graphics_quality"] == "medium"
        assert loaded["fullscreen"] is False

    def test_load_settings_defaults_when_missing(self, temp_save_dir):
        """测试无设置文件时返回默认。"""
        sm = StorageManager()
        settings = sm.load_settings()
        from config import AUDIO_BGM_VOLUME_DEFAULT, AUDIO_SFX_VOLUME_DEFAULT
        assert settings["bgm_volume"] == AUDIO_BGM_VOLUME_DEFAULT
        assert settings["sfx_volume"] == AUDIO_SFX_VOLUME_DEFAULT
        assert settings["graphics_quality"] == "high"
        assert settings["control_mode"] == "keyboard"
        assert settings["fullscreen"] is False

    def test_load_settings_partial(self, temp_save_dir):
        """测试加载时合并已有设置。"""
        sm = StorageManager()
        sm.save_settings({"bgm_volume": 0.1})
        loaded = sm.load_settings()
        assert loaded["bgm_volume"] == 0.1
        from config import AUDIO_SFX_VOLUME_DEFAULT
        assert loaded["sfx_volume"] == AUDIO_SFX_VOLUME_DEFAULT

    def test_save_and_load_game(self, temp_save_dir):
        """测试保存和加载存档。"""
        sm = StorageManager()
        game_data = {"score": 500, "level": 2, "spawn_x": 100, "spawn_y": 300}
        sm.save_game(game_data)
        assert sm.has_save_game() is True
        loaded = sm.load_game()
        assert loaded is not None
        assert loaded["score"] == 500
        assert loaded["level"] == 2
        assert loaded["spawn_x"] == 100
        assert "timestamp" in loaded

    def test_load_game_when_missing(self, temp_save_dir):
        """测试无存档时返回None。"""
        sm = StorageManager()
        assert sm.has_save_game() is False
        assert sm.load_game() is None

    def test_corrupted_settings_file(self, temp_save_dir):
        """测试损坏的设置文件回退默认。"""
        sm = StorageManager()
        with open(sm.settings_file, "w") as f:
            f.write("{ invalid json !!")
        loaded = sm.load_settings()
        from config import AUDIO_BGM_VOLUME_DEFAULT
        assert loaded["bgm_volume"] == AUDIO_BGM_VOLUME_DEFAULT

    def test_corrupted_savegame_file(self, temp_save_dir):
        """测试损坏的存档返回None。"""
        sm = StorageManager()
        with open(sm.savegame_file, "w") as f:
            f.write("not json")
        assert sm.load_game() is None

    def test_add_leaderboard_entry(self, temp_save_dir):
        """测试添加排行榜条目。"""
        sm = StorageManager()
        rank = sm.add_leaderboard_entry("Alice", 1000)
        assert rank == 1
        entries = sm.get_leaderboard()
        assert len(entries) == 1
        assert entries[0]["name"] == "Alice"
        assert entries[0]["score"] == 1000
        assert "date" in entries[0]

    def test_leaderboard_sorted_descending(self, temp_save_dir):
        """测试排行榜按得分降序。"""
        sm = StorageManager()
        sm.add_leaderboard_entry("A", 100)
        sm.add_leaderboard_entry("B", 500)
        sm.add_leaderboard_entry("C", 300)
        entries = sm.get_leaderboard()
        assert [e["score"] for e in entries] == [500, 300, 100]

    def test_leaderboard_limits_10(self, temp_save_dir):
        """测试排行榜最多保留10条。"""
        sm = StorageManager()
        for i in range(15):
            sm.add_leaderboard_entry(f"Player{i}", i * 100)
        entries = sm.get_leaderboard()
        assert len(entries) == 10
        assert entries[0]["score"] == 1400
        assert entries[-1]["score"] == 500

    def test_get_high_score(self, temp_save_dir):
        """测试获取最高分。"""
        sm = StorageManager()
        assert sm.get_high_score() == 0
        sm.add_leaderboard_entry("P1", 800)
        sm.add_leaderboard_entry("P2", 1200)
        assert sm.get_high_score() == 1200

    def test_corrupted_leaderboard(self, temp_save_dir):
        """测试损坏的排行榜返回空。"""
        sm = StorageManager()
        with open(sm.leaderboard_file, "w") as f:
            f.write("garbage")
        assert sm.get_leaderboard() == []
        assert sm.get_high_score() == 0


class TestMenuManager:
    """MenuManager核心逻辑测试。"""

    def _make_mock_game(self, temp_save_dir):
        """创建MockGame用于MenuManager测试。"""
        from audio.manager import AudioManager
        game = type('MockGame', (), {})()
        game.audio = AudioManager()
        game.current_level = 0
        game.score = 0
        game._load_level = lambda *a, **kw: None
        return game

    def test_menu_manager_initialization(self, temp_save_dir):
        """测试菜单管理器初始化。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        assert mm.game is game
        assert mm.current_state == GameState.MAIN_MENU
        assert mm.previous_state is None
        assert GameState.MAIN_MENU in mm.menus
        assert GameState.SETTINGS_MENU in mm.menus
        assert GameState.PAUSED in mm.menus
        assert GameState.GAME_OVER in mm.menus
        assert GameState.LEADERBOARD in mm.menus

    def test_set_state_updates_previous(self, temp_save_dir):
        """测试状态切换保存前一状态。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        old_state = mm.current_state
        mm.set_state(GameState.PAUSED)
        assert mm.previous_state == old_state
        assert mm.current_state == GameState.PAUSED

    def test_set_state_to_leaderboard_refresh(self, temp_save_dir):
        """测试进入排行榜时刷新数据。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.storage.add_leaderboard_entry("T1", 100)
        mm.set_state(GameState.LEADERBOARD)
        assert mm.current_state == GameState.LEADERBOARD

    def test_is_menu_active_true(self, temp_save_dir):
        """测试在菜单状态时返回True。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        assert mm.is_menu_active() is True

    def test_is_menu_active_false_when_playing(self, temp_save_dir):
        """测试在PLAYING状态时返回False。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.PLAYING)
        assert mm.is_menu_active() is False

    def test_is_menu_active_false_when_transitioning(self, temp_save_dir):
        """测试过渡状态不被当作菜单。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.TRANSITIONING)
        assert mm.is_menu_active() is False

    def test_handle_event_in_menu_state(self, temp_save_dir):
        """测试菜单状态下事件分发。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.MAIN_MENU)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        result = mm.handle_event(event)
        assert isinstance(result, bool)

    def test_handle_event_in_playing_ignored(self, temp_save_dir):
        """测试PLAYING状态下事件不被菜单处理。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.PLAYING)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        result = mm.handle_event(event)
        assert result is False

    def test_update_in_menu_state(self, temp_save_dir):
        """测试菜单状态下update不崩溃。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.MAIN_MENU)
        mm.update()
        assert True

    def test_update_in_playing_no_crash(self, temp_save_dir):
        """测试PLAYING状态下update不崩溃。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.PLAYING)
        mm.update()
        assert True

    def test_draw_in_menu_state(self, temp_save_dir, pygame_session):
        """测试菜单状态下draw不崩溃。"""
        from menus import get_chinese_font
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.set_state(GameState.MAIN_MENU)
        screen = pygame.Surface((800, 640))
        big_font = get_chinese_font(36)
        normal_font = get_chinese_font(20)
        small_font = get_chinese_font(16)
        mm.draw(screen, big_font, normal_font, small_font)
        assert True

    def test_start_new_game_resets(self, temp_save_dir):
        """测试启动新游戏时重置分数和关卡。"""
        game = self._make_mock_game(temp_save_dir)
        game.score = 999
        game.current_level = 2
        mm = MenuManager(game)
        mm.start_new_game()
        assert game.score == 0
        assert game.current_level == 0

    def test_trigger_game_over_sets_state(self, temp_save_dir):
        """测试触发游戏结束设置正确状态。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.trigger_game_over(500)
        assert mm.current_state == GameState.GAME_OVER

    def test_trigger_game_over_sets_score(self, temp_save_dir):
        """测试游戏结束设置分数。"""
        game = self._make_mock_game(temp_save_dir)
        mm = MenuManager(game)
        mm.trigger_game_over(1234)
        game_over_menu = mm.menus[GameState.GAME_OVER]
        assert game_over_menu.final_score == 1234
