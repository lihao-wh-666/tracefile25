"""
test_menus.py - 菜单系统单元测试

测试菜单系统的核心功能：
- StorageManager 数据持久化
- Button 组件交互
- Slider 组件交互
- Menu 基类功能
- 所有具体菜单的初始化和状态管理
"""

import os
import sys
import json
import tempfile
import shutil

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["HEADLESS"] = "1"

import pygame
pygame.init()
pygame.display.set_mode((960, 640))

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from menus import (
    GameState, Button, Slider, StorageManager,
    Menu, MainMenu, SettingsMenu, PauseMenu,
    GameOverMenu, LeaderboardMenu, MenuManager,
    get_chinese_font
)


class MockGame:
    """模拟 Game 类用于测试。"""
    def __init__(self):
        self.score = 0
        self.current_level = 0
        self.audio = None
        self.player = type('obj', (object,), {'x': 100, 'y': 400})()

    def _load_level(self, level, x, y, immediate=False):
        pass


def test_storage_manager():
    """测试 StorageManager 数据持久化功能。"""
    print("测试 StorageManager...")

    temp_dir = tempfile.mkdtemp()
    original_home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    os.environ["HOME"] = temp_dir
    os.environ["USERPROFILE"] = temp_dir

    try:
        storage = StorageManager()

        test_settings = {
            "bgm_volume": 0.7,
            "sfx_volume": 0.5,
            "graphics_quality": "medium",
            "control_mode": "keyboard",
            "fullscreen": True,
        }
        storage.save_settings(test_settings)
        loaded = storage.load_settings()
        assert loaded["bgm_volume"] == 0.7
        assert loaded["sfx_volume"] == 0.5
        assert loaded["graphics_quality"] == "medium"
        assert loaded["fullscreen"] == True
        print("  ✓ 设置保存/加载正常")

        assert not storage.has_save_game()
        save_data = {"score": 150, "level": 1, "spawn_x": 200, "spawn_y": 300}
        storage.save_game(save_data)
        assert storage.has_save_game()
        loaded_save = storage.load_game()
        assert loaded_save["score"] == 150
        assert loaded_save["level"] == 1
        print("  ✓ 游戏存档保存/加载正常")

        assert storage.get_high_score() == 0
        rank = storage.add_leaderboard_entry("Player1", 500)
        assert rank == 1
        rank = storage.add_leaderboard_entry("Player2", 300)
        assert rank == 2
        rank = storage.add_leaderboard_entry("Player3", 700)
        assert rank == 1
        assert storage.get_high_score() == 700
        leaderboard = storage.get_leaderboard()
        assert len(leaderboard) == 3
        assert leaderboard[0]["score"] == 700
        assert leaderboard[0]["name"] == "Player3"
        print("  ✓ 排行榜保存/加载正常")

    finally:
        if original_home:
            os.environ["HOME"] = original_home
            os.environ["USERPROFILE"] = original_home
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("  ✓ StorageManager 所有测试通过")


def test_button():
    """测试 Button 组件。"""
    print("\n测试 Button 组件...")

    callback_called = [False]
    def on_click():
        callback_called[0] = True

    btn = Button(100, 100, 200, 50, "测试按钮", on_click)

    assert btn.text == "测试按钮"
    assert btn.enabled == True
    assert btn.rect.x == 100
    assert btn.rect.y == 100

    btn.enabled = False
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (150, 125)})
    assert not btn.handle_event(event)
    assert callback_called[0] == False
    print("  ✓ 禁用状态下不响应点击")

    btn.enabled = True
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (150, 125)})
    assert btn.handle_event(event)
    assert callback_called[0] == True
    print("  ✓ 鼠标点击正常")

    callback_called[0] = False
    btn.selected = True
    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN})
    assert btn.handle_event(event)
    assert callback_called[0] == True
    print("  ✓ 键盘选择正常")

    event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (150, 125)})
    btn.handle_event(event)
    assert btn.hover == True
    print("  ✓ 悬停状态正常")

    print("  ✓ Button 所有测试通过")


def test_slider():
    """测试 Slider 组件。"""
    print("\n测试 Slider 组件...")

    slider = Slider(100, 100, 200, 10, 0.5, "测试")
    assert abs(slider.value - 0.5) < 0.001
    assert slider.label == "测试"

    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': (250, 105)})
    changed = slider.handle_event(event)
    assert changed == True
    assert abs(slider.value - 0.75) < 0.01
    print("  ✓ 鼠标点击定位正常")

    slider.value = 0.5
    slider.dragging = True
    event = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (300, 105)})
    changed = slider.handle_event(event)
    assert changed == True
    assert abs(slider.value - 1.0) < 0.001
    print("  ✓ 拖拽调节正常")

    slider.value = 0.5
    slider.hover = True
    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT})
    changed = slider.handle_event(event)
    assert changed == True
    assert abs(slider.value - 0.45) < 0.001
    print("  ✓ 键盘左右调节正常")

    print("  ✓ Slider 所有测试通过")


def test_menu_base():
    """测试 Menu 基类功能。"""
    print("\n测试 Menu 基类...")

    mock_game = MockGame()
    manager = MenuManager(mock_game)

    menu = Menu(manager, "测试菜单")
    assert menu.title == "测试菜单"
    assert menu.selected_index == 0

    btn1_called = [False]
    btn2_called = [False]
    menu.buttons = [
        Button(0, 0, 0, 0, "按钮1", lambda: btn1_called.__setitem__(0, True)),
        Button(0, 0, 0, 0, "按钮2", lambda: btn2_called.__setitem__(0, True)),
    ]
    menu._layout_buttons()

    assert menu.buttons[0].rect.x > 0
    assert menu.buttons[0].rect.y > 0
    assert menu.buttons[0].selected == True
    assert menu.buttons[1].selected == False
    print("  ✓ 按钮布局正常")

    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN})
    menu.handle_event(event)
    assert menu.selected_index == 1
    assert menu.buttons[1].selected == True
    print("  ✓ 向下导航正常")

    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP})
    menu.handle_event(event)
    assert menu.selected_index == 0
    assert menu.buttons[0].selected == True
    print("  ✓ 向上导航正常")

    event = pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RETURN})
    menu.handle_event(event)
    assert btn1_called[0] == True
    print("  ✓ Enter 键触发正常")

    print("  ✓ Menu 基类所有测试通过")


def test_all_menus():
    """测试所有具体菜单的初始化。"""
    print("\n测试所有具体菜单...")

    mock_game = MockGame()
    manager = MenuManager(mock_game)

    main_menu = MainMenu(manager)
    assert main_menu.title == "平台跳跃"
    assert len(main_menu.buttons) == 5
    print("  ✓ MainMenu 初始化正常")

    settings_menu = SettingsMenu(manager)
    assert settings_menu.title == "游戏设置"
    assert len(settings_menu.buttons) == 4
    assert settings_menu.bgm_slider is not None
    assert settings_menu.sfx_slider is not None
    print("  ✓ SettingsMenu 初始化正常")

    pause_menu = PauseMenu(manager)
    assert pause_menu.title == "游戏暂停"
    assert len(pause_menu.buttons) == 4
    print("  ✓ PauseMenu 初始化正常")

    game_over_menu = GameOverMenu(manager)
    assert game_over_menu.title == "游戏结束"
    assert len(game_over_menu.buttons) == 3
    game_over_menu.set_score(100)
    assert game_over_menu.final_score == 100
    print("  ✓ GameOverMenu 初始化正常")

    leaderboard_menu = LeaderboardMenu(manager)
    assert leaderboard_menu.title == "排行榜"
    assert len(leaderboard_menu.buttons) == 1
    leaderboard_menu.refresh()
    print("  ✓ LeaderboardMenu 初始化正常")

    print("  ✓ 所有菜单初始化测试通过")


def test_menu_manager():
    """测试 MenuManager 状态管理。"""
    print("\n测试 MenuManager...")

    mock_game = MockGame()
    manager = MenuManager(mock_game)

    assert manager.current_state == GameState.MAIN_MENU
    assert manager.is_menu_active() == True
    print("  ✓ 初始状态为主菜单")

    manager.set_state(GameState.SETTINGS_MENU)
    assert manager.current_state == GameState.SETTINGS_MENU
    assert manager.previous_state == GameState.MAIN_MENU
    print("  ✓ 状态切换正常")

    manager.set_state(GameState.PLAYING)
    assert manager.current_state == GameState.PLAYING
    assert manager.is_menu_active() == False
    print("  ✓ 游戏状态切换正常")

    manager.set_state(GameState.PAUSED)
    assert manager.current_state == GameState.PAUSED
    assert manager.is_menu_active() == True
    print("  ✓ 暂停状态切换正常")

    manager.trigger_game_over(200)
    assert manager.current_state == GameState.GAME_OVER
    game_over_menu = manager.menus[GameState.GAME_OVER]
    assert game_over_menu.final_score == 200
    print("  ✓ 游戏结束触发正常")

    print("  ✓ MenuManager 所有测试通过")


def test_state_enum():
    """测试 GameState 枚举。"""
    print("\n测试 GameState 枚举...")

    states = [
        GameState.MAIN_MENU,
        GameState.SETTINGS_MENU,
        GameState.PAUSED,
        GameState.GAME_OVER,
        GameState.LEADERBOARD,
        GameState.PLAYING,
        GameState.TRANSITIONING,
        GameState.LOADING,
    ]

    assert len(set(states)) == len(states)
    for state in states:
        assert isinstance(state, str)
        assert len(state) > 0
    print("  ✓ GameState 枚举值唯一且有效")

    print("  ✓ GameState 所有测试通过")


def test_chinese_font():
    """测试中文字体加载。"""
    print("\n测试中文字体加载...")

    font_small = get_chinese_font(24)
    font_medium = get_chinese_font(36)
    font_large = get_chinese_font(64)

    assert font_small is not None
    assert font_medium is not None
    assert font_large is not None

    test_text = "你好，世界！"
    surf_small = font_small.render(test_text, True, (255, 255, 255))
    surf_medium = font_medium.render(test_text, True, (255, 255, 255))
    surf_large = font_large.render(test_text, True, (255, 255, 255))

    assert surf_small is not None
    assert surf_small.get_width() > 0
    assert surf_large.get_height() > surf_medium.get_height()
    assert surf_medium.get_height() > surf_small.get_height()

    print("  ✓ 小字体渲染正常")
    print("  ✓ 中字体渲染正常")
    print("  ✓ 大字体渲染正常")
    print("  ✓ 字体大小缩放正常")

    print("  ✓ 中文字体所有测试通过")


def main():
    """运行所有测试。"""
    print("=" * 60)
    print("游戏菜单系统单元测试")
    print("=" * 60)

    try:
        test_state_enum()
        test_chinese_font()
        test_storage_manager()
        test_button()
        test_slider()
        test_menu_base()
        test_all_menus()
        test_menu_manager()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
