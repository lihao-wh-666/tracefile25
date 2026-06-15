# -*- coding: utf-8 -*-
"""
test_state.py - 游戏状态管理模块测试

测试范围:
- StateManager 初始化
- start_transition 过渡启动
- update_transition 三阶段状态机
- draw_transition 遮罩层透明度计算
- 关卡内传送 vs 跨关卡传送
"""

import os
import sys
import pytest

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from menus import GameState
from core.state import StateManager


@pytest.fixture(scope="session")
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


class MockPlayer:
    """模拟玩家。"""
    def __init__(self):
        self.x = 100
        self.y = 200
        self.width = 32
        self.height = 48


class MockMenuManager:
    """模拟菜单管理器。"""
    def __init__(self):
        self.current_state = GameState.MAIN_MENU
    
    def set_state(self, new_state):
        self.current_state = new_state


class MockGame:
    """模拟 Game 主类。"""
    def __init__(self):
        self.game_state = GameState.MAIN_MENU
        self.current_level = 0
        self.player = MockPlayer()
        self.portal_particle_colors = [(100, 200, 255)]
        self.particles = []
        self.level_config = None
        self.camera_x = 0
        self.menu_manager = MockMenuManager()

    def _spawn_particles(self, x, y, count=10, colors=None, spread=3, life=20, size=3):
        for _ in range(count):
            self.particles.append({"x": x, "y": y, "life": life})

    def _load_level(self, level_id, spawn_x, spawn_y, immediate=False):
        self.current_level = level_id
        self.player.x = spawn_x
        self.player.y = spawn_y


@pytest.fixture
def state_manager():
    """StateManager 夹具。"""
    game = MockGame()
    sm = StateManager(game)
    return sm, game


class TestStateManager:
    """StateManager 状态管理器测试。"""

    def test_init(self, state_manager):
        """测试初始化。"""
        sm, game = state_manager
        assert sm.game is game
        assert sm.transition_frame == 0
        assert sm.transition_phase == 0
        assert sm.pending_level == 0
        assert sm.pending_spawn == (0, 0)
        assert abs(sm.loading_progress - 0.0) < 0.001

    def test_start_transition_same_level(self, state_manager):
        """测试同关卡内传送（target_level=-1）。"""
        sm, game = state_manager
        game.current_level = 1
        sm.start_transition(target_level=-1, target_x=500, target_y=200)
        assert game.game_state == GameState.TRANSITIONING
        assert sm.transition_phase == 0
        assert sm.transition_frame == 0
        assert sm.pending_level == 1
        assert sm.pending_spawn == (500, 200)
        assert len(game.particles) > 0

    def test_start_transition_cross_level(self, state_manager):
        """测试跨关卡传送。"""
        sm, game = state_manager
        game.current_level = 0
        sm.start_transition(target_level=2, target_x=100, target_y=400)
        assert game.game_state == GameState.TRANSITIONING
        assert sm.pending_level == 2 % 3
        assert sm.pending_spawn == (100, 400)

    def test_start_transition_level_wraparound(self, state_manager):
        """测试关卡编号循环取模。"""
        sm, game = state_manager
        sm.start_transition(target_level=5, target_x=10, target_y=20)
        assert sm.pending_level == 5 % 3
        sm.start_transition(target_level=-2, target_x=10, target_y=20)
        assert sm.pending_level == (-2) % 3

    def test_transition_phase_0_fadeout(self, state_manager):
        """测试过渡阶段0（淡出）。"""
        sm, game = state_manager
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        for i in range(half - 1):
            sm.update_transition()
        assert sm.transition_phase == 0
        assert sm.transition_frame == half - 1

    def test_transition_phase_0_to_1(self, state_manager):
        """测试阶段0到1切换。"""
        sm, game = state_manager
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        for _ in range(half):
            sm.update_transition()
        assert sm.transition_phase == 1
        assert sm.transition_frame == 0
        assert game.game_state == GameState.LOADING
        assert abs(sm.loading_progress - 0.0) < 0.001

    def test_transition_phase_1_loading(self, state_manager):
        """测试过渡阶段1（加载进度）。"""
        sm, game = state_manager
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        for _ in range(half):
            sm.update_transition()
        for i in range(half - 1):
            sm.update_transition()
        progress_before = sm.loading_progress
        assert progress_before < 1.0
        assert sm.transition_phase == 1

    def test_transition_phase_1_to_2(self, state_manager):
        """测试阶段1到2切换时加载关卡。"""
        sm, game = state_manager
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        from config import TRANSITION_DURATION_FRAMES
        full = TRANSITION_DURATION_FRAMES
        for _ in range(full):
            sm.update_transition()
        assert game.current_level == 1
        assert game.player.x == 100
        assert game.player.y == 200
        assert sm.transition_phase == 2

    def test_transition_phase_2_fadein(self, state_manager):
        """测试过渡阶段2（淡入）。"""
        sm, game = state_manager
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        full = TRANSITION_DURATION_FRAMES
        for _ in range(full + half - 2):
            sm.update_transition()
        assert sm.transition_phase == 2

    def test_transition_phase_2_to_playing(self, state_manager):
        """测试阶段2结束进入PLAYING状态。"""
        sm, game = state_manager
        sm.start_transition(target_level=2, target_x=200, target_y=300)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        full = TRANSITION_DURATION_FRAMES
        for _ in range(full + half + 1):
            sm.update_transition()
        assert game.game_state == GameState.PLAYING
        assert sm.transition_phase == 0

    def test_draw_transition_no_crash(self, state_manager, pygame_session):
        """测试绘制过渡不崩溃。"""
        sm, game = state_manager
        screen = pygame.Surface((800, 600))
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        sm.start_transition(target_level=1, target_x=100, target_y=200)
        sm.draw_transition(screen)
        for _ in range(half):
            sm.update_transition()
        sm.draw_transition(screen)
        for _ in range(half):
            sm.update_transition()
        sm.draw_transition(screen)
        for _ in range(half):
            sm.update_transition()
        sm.draw_transition(screen)
        assert True

    def test_draw_loading_screen_no_crash(self, state_manager, pygame_session):
        """测试绘制加载界面不崩溃。"""
        sm, game = state_manager
        screen = pygame.Surface((800, 600))
        from menus import get_chinese_font
        title_font = get_chinese_font(36)
        big_font = get_chinese_font(28)
        font = get_chinese_font(18)
        from config import TRANSITION_DURATION_FRAMES
        half = TRANSITION_DURATION_FRAMES // 2
        sm.start_transition(target_level=0, target_x=100, target_y=200)
        for _ in range(half):
            sm.update_transition()
        sm.loading_progress = 0.5
        sm.draw_loading_screen(screen, title_font, big_font, font)
        sm.loading_progress = 1.0
        sm.draw_loading_screen(screen, title_font, big_font, font)
        assert True
