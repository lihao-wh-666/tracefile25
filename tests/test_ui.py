# -*- coding: utf-8 -*-
"""
test_ui.py - UI 模块测试

测试范围:
- get_chinese_font 字体缓存机制
- VolumeSlider 鼠标事件/拖拽/范围限制/绘制
- VolumePanel 显示切换/sync_from_audio_manager/回调事件
"""

import os
import sys
import pytest

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from ui import (
    get_chinese_font,
    VolumeSlider, VolumePanel,
)


@pytest.fixture(scope="session")
def pygame_session():
    pygame.init()
    yield
    pygame.quit()


class TestGetChineseFont:
    """get_chinese_font 字体获取测试。"""

    def test_font_size_variety(self, pygame_session):
        """测试不同字号获取字体。"""
        f16 = get_chinese_font(16)
        f24 = get_chinese_font(24)
        f32 = get_chinese_font(32)
        assert f16 is not None
        assert f24 is not None
        assert f32 is not None
        assert f16.get_height() <= f24.get_height() <= f32.get_height()

    def test_font_cache_same_size(self, pygame_session):
        """测试同字号返回缓存实例。"""
        f_a = get_chinese_font(20)
        f_b = get_chinese_font(20)
        assert f_a is f_b

    def test_font_render_text(self, pygame_session):
        """测试字体能渲染文本。"""
        font = get_chinese_font(20)
        surf = font.render("Test", True, (255, 255, 255))
        assert surf is not None
        assert isinstance(surf, pygame.Surface)
        assert surf.get_width() > 0
        assert surf.get_height() > 0

    def test_font_render_chinese(self, pygame_session):
        """测试字体能渲染中文字符。"""
        font = get_chinese_font(20)
        surf = font.render("测试中文", True, (255, 255, 255))
        assert surf is not None
        assert surf.get_width() > 0


class TestVolumeSlider:
    """VolumeSlider 音量滑块测试。"""

    def test_init_defaults(self):
        """测试初始化默认值。"""
        slider = VolumeSlider(100, 200, 200, 10)
        assert slider.x == 100
        assert slider.y == 200
        assert slider.width == 200
        assert slider.height == 10
        assert abs(slider.value - 0.5) < 0.001
        assert slider.dragging is False

    def test_init_custom_value(self):
        """测试初始化自定义值。"""
        slider = VolumeSlider(0, 0, 150, 8, 0.75)
        assert abs(slider.value - 0.75) < 0.001

    def test_init_clamp_value_low(self):
        """测试初始值超下限被钳制。"""
        slider = VolumeSlider(0, 0, 100, 10, -5.0)
        assert abs(slider.value - 0.0) < 0.001

    def test_init_clamp_value_high(self):
        """测试初始值超上限被钳制。"""
        slider = VolumeSlider(0, 0, 100, 10, 5.0)
        assert abs(slider.value - 1.0) < 0.001

    def test_knob_x_center(self):
        """测试旋钮位置计算。"""
        slider = VolumeSlider(100, 0, 200, 10, 0.0)
        assert slider._knob_x() == 100
        slider2 = VolumeSlider(100, 0, 200, 10, 1.0)
        assert slider2._knob_x() == 300
        slider3 = VolumeSlider(100, 0, 200, 10, 0.5)
        assert slider3._knob_x() == 200

    def test_knob_rect(self):
        """测试旋钮矩形。"""
        slider = VolumeSlider(0, 100, 200, 10, 0.5)
        rect = slider._knob_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width > 0
        assert rect.height > 0

    def test_track_rect(self):
        """测试轨道矩形。"""
        slider = VolumeSlider(50, 80, 150, 10, 0.5)
        rect = slider._track_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.x == 50
        assert rect.width == 150

    def test_set_value_normal(self):
        """测试 set_value 正常设置。"""
        slider = VolumeSlider(0, 0, 100, 10)
        slider.set_value(0.3)
        assert abs(slider.value - 0.3) < 0.001

    def test_set_value_clamp(self):
        """测试 set_value 钳制范围。"""
        slider = VolumeSlider(0, 0, 100, 10)
        slider.set_value(-1.0)
        assert abs(slider.value - 0.0) < 0.001
        slider.set_value(2.0)
        assert abs(slider.value - 1.0) < 0.001

    def test_handle_mouse_down_on_track(self):
        """测试鼠标按下在轨道上。"""
        slider = VolumeSlider(100, 100, 200, 10, 0.5)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (150, 105)})
        changed = slider.handle_event(event)
        assert slider.dragging is True
        assert changed is True
        expected = (150 - 100) / 200
        assert abs(slider.value - expected) < 0.01

    def test_handle_mouse_down_outside(self):
        """测试鼠标按下在轨道外。"""
        slider = VolumeSlider(100, 100, 200, 10, 0.5)
        old_value = slider.value
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (50, 105)})
        changed = slider.handle_event(event)
        assert slider.dragging is False
        assert changed is False
        assert slider.value == old_value

    def test_handle_mouse_up(self):
        """测试鼠标释放结束拖拽。"""
        slider = VolumeSlider(0, 0, 100, 10, 0.5)
        slider.dragging = True
        event = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1})
        changed = slider.handle_event(event)
        assert slider.dragging is False
        assert changed is False

    def test_handle_mouse_motion_dragging(self):
        """测试拖拽时鼠标移动。"""
        slider = VolumeSlider(100, 100, 200, 10, 0.0)
        slider.dragging = True
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (200, 105)})
        changed = slider.handle_event(event)
        assert changed is True
        assert abs(slider.value - 0.5) < 0.01

    def test_handle_mouse_motion_drag_clamp(self):
        """测试拖拽时超范围被钳制。"""
        slider = VolumeSlider(100, 100, 200, 10, 0.5)
        slider.dragging = True
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (50, 105)})
        slider.handle_event(event)
        assert abs(slider.value - 0.0) < 0.001

        event2 = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (500, 105)})
        slider.handle_event(event2)
        assert abs(slider.value - 1.0) < 0.001

    def test_handle_mouse_motion_not_dragging_hover(self):
        """测试非拖拽时鼠标移动只更新hover。"""
        slider = VolumeSlider(100, 100, 200, 10, 0.5)
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (150, 105)})
        changed = slider.handle_event(event)
        assert changed is False
        assert slider._hover is True

    def test_handle_non_mouse_event(self):
        """测试非鼠标事件无变化。"""
        slider = VolumeSlider(0, 0, 100, 10, 0.5)
        old_val = slider.value
        old_drag = slider.dragging
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a})
        changed = slider.handle_event(event)
        assert changed is False
        assert slider.value == old_val
        assert slider.dragging == old_drag

    def test_draw_no_crash(self, pygame_session):
        """测试绘制不崩溃。"""
        slider = VolumeSlider(50, 50, 200, 10, 0.6)
        font = get_chinese_font(16)
        surf = pygame.Surface((400, 200))
        slider.draw(surf, font)
        slider.dragging = True
        slider.draw(surf, font)
        slider._hover = True
        slider.dragging = False
        slider.draw(surf, font)


class TestVolumePanel:
    """VolumePanel 音量调节面板测试。"""

    def test_init_visible(self):
        """测试初始化默认隐藏。"""
        panel = VolumePanel()
        assert panel.visible is False

    def test_init_sliders_exist(self):
        """测试初始化创建两个滑块。"""
        panel = VolumePanel()
        assert panel.bgm_slider is not None
        assert panel.sfx_slider is not None
        assert abs(panel.bgm_slider.value - 0.6) < 0.001
        assert abs(panel.sfx_slider.value - 0.8) < 0.001

    def test_init_with_audio_manager(self):
        """测试使用 audio_manager 初始化滑块值。"""
        class FakeAudio:
            bgm_volume = 0.3
            sfx_volume = 0.4

        panel = VolumePanel(audio_manager=FakeAudio())
        assert abs(panel.bgm_slider.value - 0.3) < 0.001
        assert abs(panel.sfx_slider.value - 0.4) < 0.001

    def test_toggle(self):
        """测试切换显示。"""
        panel = VolumePanel()
        assert panel.visible is False
        panel.toggle()
        assert panel.visible is True
        panel.toggle()
        assert panel.visible is False

    def test_show_hide(self):
        """测试显式显示/隐藏。"""
        panel = VolumePanel()
        panel.show()
        assert panel.visible is True
        panel.hide()
        assert panel.visible is False

    def test_handle_event_when_hidden(self):
        """测试隐藏时事件处理不生效。"""
        panel = VolumePanel()
        panel.visible = False
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": (0, 0)})
        old_bgm = panel.bgm_slider.value
        panel.handle_event(event)
        assert panel.bgm_slider.value == old_bgm

    def test_sync_from_audio_manager(self):
        """测试从 AudioManager 同步。"""
        class FakeAudio:
            bgm_volume = 0.2
            sfx_volume = 0.9

        panel = VolumePanel()
        panel._audio_manager = FakeAudio()
        panel.sync_from_audio_manager()
        assert abs(panel.bgm_slider.value - 0.2) < 0.001
        assert abs(panel.sfx_slider.value - 0.9) < 0.001

    def test_callback_bgm_change_callback(self):
        """测试 BGM 滑块回调。"""
        panel = VolumePanel()
        panel.visible = True
        callback_values = []

        def on_bgm(val):
            callback_values.append(val)

        panel.on_bgm_change = on_bgm
        slider = panel.bgm_slider
        slider.dragging = True
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (slider.x + 50, slider.y + 5)})
        panel.handle_event(event)
        assert len(callback_values) > 0

    def test_callback_sfx_change_callback(self):
        """测试 SFX 滑块回调。"""
        panel = VolumePanel()
        panel.visible = True
        callback_values = []

        def on_sfx(val):
            callback_values.append(val)

        panel.on_sfx_change = on_sfx
        slider = panel.sfx_slider
        slider.dragging = True
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            {"pos": (slider.x + 80, slider.y + 5)})
        panel.handle_event(event)
        assert len(callback_values) > 0

    def test_draw_visible(self, pygame_session):
        """测试绘制（可见时）。"""
        panel = VolumePanel()
        panel.visible = True
        big_font = get_chinese_font(20)
        small_font = get_chinese_font(14)
        surf = pygame.Surface((500, 300))
        panel.draw(surf, big_font, small_font)
        panel.visible = False
        panel.draw(surf, big_font, small_font)
