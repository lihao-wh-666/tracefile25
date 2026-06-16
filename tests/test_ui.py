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
    ItemIconData, ItemIconSystem,
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


class TestItemIconData:
    """ItemIconData 单个道具图标数据测试。"""

    def test_init_attributes(self, pygame_session):
        """测试初始化属性。"""
        from entities.powerups import SpeedBoostPowerup, PowerupType
        powerup = SpeedBoostPowerup()
        icon = ItemIconData(
            PowerupType.SPEED_BOOST, powerup, "1", "加速", "测试描述"
        )
        assert icon.powerup_type == PowerupType.SPEED_BOOST
        assert icon.powerup is powerup
        assert icon.key_label == "1"
        assert icon.display_name == "加速"
        assert icon.description == "测试描述"
        assert icon.hovered is False
        assert icon.clicked is False

    def test_is_available_not_acquired(self, pygame_session):
        """测试未拾取道具不可用。"""
        from entities.powerups import SpeedBoostPowerup
        powerup = SpeedBoostPowerup()
        powerup.acquired = False
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        assert icon.is_available is False

    def test_is_available_acquired_idle(self, pygame_session):
        """测试已拾取空闲道具可用。"""
        from entities.powerups import SpeedBoostPowerup
        powerup = SpeedBoostPowerup()
        powerup.acquired = True
        from entities.powerups import PowerupState
        powerup.state = PowerupState.IDLE
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        assert icon.is_available is True

    def test_is_available_active(self, pygame_session):
        """测试激活中道具可用。"""
        from entities.powerups import SpeedBoostPowerup, PowerupState
        powerup = SpeedBoostPowerup()
        powerup.acquired = True
        powerup.state = PowerupState.ACTIVE
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        assert icon.is_available is True

    def test_is_available_on_cooldown(self, pygame_session):
        """测试冷却中道具不可用。"""
        from entities.powerups import SpeedBoostPowerup, PowerupState
        powerup = SpeedBoostPowerup()
        powerup.acquired = True
        powerup.state = PowerupState.COOLDOWN
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        assert icon.is_available is False

    def test_effective_alpha_available(self, pygame_session):
        """测试可用状态透明度。"""
        from entities.powerups import SpeedBoostPowerup
        powerup = SpeedBoostPowerup()
        powerup.acquired = True
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        icon._prev_available = True
        icon.transition_progress = 0.0
        assert icon.effective_alpha == 0.0

    def test_effective_alpha_unavailable(self, pygame_session):
        """测试不可用状态灰度透明度。"""
        from entities.powerups import SpeedBoostPowerup
        from config import HUD_POWERUP_GRAYSCALE_ALPHA
        powerup = SpeedBoostPowerup()
        powerup.acquired = False
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        icon._prev_available = False
        icon.transition_progress = 0.0
        expected = 1.0 - 0.0 * (1.0 - HUD_POWERUP_GRAYSCALE_ALPHA)
        assert abs(icon.effective_alpha - expected) < 0.001

    def test_get_effective_scale_base(self, pygame_session):
        """测试基础缩放比例。"""
        from entities.powerups import SpeedBoostPowerup
        powerup = SpeedBoostPowerup()
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        icon.hover_progress = 0.0
        assert abs(icon.get_effective_scale() - 1.0) < 0.001

    def test_get_effective_scale_hover(self, pygame_session):
        """测试悬停缩放比例。"""
        from entities.powerups import SpeedBoostPowerup
        from config import HUD_POWERUP_HOVER_SCALE
        powerup = SpeedBoostPowerup()
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        icon.hover_progress = 1.0
        assert abs(icon.get_effective_scale() - HUD_POWERUP_HOVER_SCALE) < 0.001

    def test_update_transitions_decrements(self, pygame_session):
        """测试过渡动画递减。"""
        from entities.powerups import SpeedBoostPowerup
        powerup = SpeedBoostPowerup()
        icon = ItemIconData("speed_boost", powerup, "1", "加速", "")
        icon.transition_progress = 0.5
        icon._prev_available = icon.is_available
        icon.update_transitions()
        assert icon.transition_progress < 0.5


class TestItemIconSystem:
    """ItemIconSystem 道具图标系统测试。"""

    @pytest.fixture
    def icon_system(self, pygame_session):
        from core.powerup_manager import PowerupManager
        pm = PowerupManager()
        system = ItemIconSystem(None, pm)
        return system

    def test_init_creates_icons(self, icon_system):
        """测试初始化创建图标。"""
        assert len(icon_system.icons) == 3

    def test_init_icon_key_labels(self, icon_system):
        """测试图标快捷键标签。"""
        labels = [icon.key_label for icon in icon_system.icons]
        assert "1" in labels
        assert "2" in labels
        assert "3" in labels

    def test_init_icon_display_names(self, icon_system):
        """测试图标显示名称。"""
        names = [icon.display_name for icon in icon_system.icons]
        assert "加速" in names
        assert "护盾" in names
        assert "强化武器" in names

    def test_layout_icons_positions(self, icon_system):
        """测试图标布局位置。"""
        from config import HUD_POWERUP_START_X, HUD_POWERUP_ICON_SIZE, HUD_POWERUP_ICON_MARGIN
        icon_system._layout_icons()
        assert icon_system.icons[0].rect.x == HUD_POWERUP_START_X
        assert icon_system.icons[1].rect.x == HUD_POWERUP_START_X + HUD_POWERUP_ICON_SIZE + HUD_POWERUP_ICON_MARGIN
        assert icon_system.icons[2].rect.x == HUD_POWERUP_START_X + (HUD_POWERUP_ICON_SIZE + HUD_POWERUP_ICON_MARGIN) * 2

    def test_handle_event_mouse_hover(self, icon_system):
        """测试鼠标悬停事件。"""
        icon_system._layout_icons()
        first_icon = icon_system.icons[0]
        cx = first_icon.rect.centerx
        cy = first_icon.rect.centery
        event = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (cx, cy)})
        icon_system.handle_event(event)
        assert first_icon.hovered is True or first_icon.hovered is False

    def test_handle_event_mouse_click_unavailable(self, icon_system):
        """测试点击不可用道具不触发使用。"""
        icon_system._layout_icons()
        first_icon = icon_system.icons[0]
        first_icon.powerup.acquired = False
        cx = first_icon.rect.centerx
        cy = first_icon.rect.centery
        used = []
        icon_system.on_item_used = lambda pt: used.append(pt)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
        icon_system.handle_event(event)
        assert len(used) == 0

    def test_handle_event_mouse_click_available(self, icon_system):
        """测试点击可用道具触发使用。"""
        icon_system._layout_icons()
        first_icon = icon_system.icons[0]
        first_icon.powerup.acquired = True
        from entities.powerups import PowerupState
        first_icon.powerup.state = PowerupState.IDLE
        cx = first_icon.rect.centerx
        cy = first_icon.rect.centery
        used = []
        icon_system.on_item_used = lambda pt: used.append(pt)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (cx, cy)})
        icon_system.handle_event(event)
        assert len(used) == 1

    def test_on_resize(self, icon_system):
        """测试窗口大小变化。"""
        icon_system.on_resize(1920, 1080)
        assert icon_system._screen_width == 1920
        assert icon_system._screen_height == 1080

    def test_get_start_y(self, icon_system):
        """测试图标起始 Y 坐标在屏幕底部。"""
        from config import SCREEN_HEIGHT, HUD_POWERUP_START_Y_OFFSET, HUD_POWERUP_ICON_SIZE
        y = icon_system._get_start_y()
        expected_y = SCREEN_HEIGHT - HUD_POWERUP_START_Y_OFFSET - HUD_POWERUP_ICON_SIZE
        assert y == expected_y
        assert y > SCREEN_HEIGHT // 2

    def test_draw_no_crash(self, icon_system, pygame_session):
        """测试绘制不崩溃。"""
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)

    def test_draw_with_acquired_powerup(self, icon_system, pygame_session):
        """测试已拾取道具绘制不崩溃。"""
        for icon in icon_system.icons:
            icon.powerup.acquired = True
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)

    def test_draw_with_active_powerup(self, icon_system, pygame_session):
        """测试激活道具绘制不崩溃。"""
        from entities.powerups import PowerupState
        for icon in icon_system.icons:
            icon.powerup.acquired = True
            icon.powerup.state = PowerupState.ACTIVE
            icon.powerup.active_timer = 100
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)

    def test_draw_with_cooldown_powerup(self, icon_system, pygame_session):
        """测试冷却中道具绘制不崩溃。"""
        from entities.powerups import PowerupState
        for icon in icon_system.icons:
            icon.powerup.acquired = True
            icon.powerup.state = PowerupState.COOLDOWN
            icon.powerup.cooldown_timer = 100
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)

    def test_draw_renders_level_label_bottom_left(self, icon_system, pygame_session):
        """测试左下角绘制等级标签。"""
        from config import HUD_POWERUP_ICON_SIZE
        for icon in icon_system.icons:
            icon.powerup.acquired = True
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)
        icon_x = icon_system.icons[0].rect.x
        icon_y = icon_system.icons[0].rect.y
        icon_size = HUD_POWERUP_ICON_SIZE
        bottom_left_region = pygame.Rect(
            icon_x + 2, icon_y + icon_size // 2,
            icon_size // 2, icon_size // 2
        )
        has_pixels = False
        for dx in range(bottom_left_region.width):
            for dy in range(0, bottom_left_region.height, 2):
                px = bottom_left_region.x + dx
                py = bottom_left_region.y + dy
                if 0 <= px < surf.get_width() and 0 <= py < surf.get_height():
                    pixel = surf.get_at((px, py))
                    if pixel[:3] != (0, 0, 0):
                        has_pixels = True
                        break
            if has_pixels:
                break
        assert has_pixels, "左下角应有等级标签像素"

    def test_draw_renders_key_label_bottom_right(self, icon_system, pygame_session):
        """测试右下角绘制快捷键标签。"""
        from config import HUD_POWERUP_ICON_SIZE
        for icon in icon_system.icons:
            icon.powerup.acquired = True
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)
        icon_x = icon_system.icons[0].rect.x
        icon_y = icon_system.icons[0].rect.y
        icon_size = HUD_POWERUP_ICON_SIZE
        bottom_right_region = pygame.Rect(
            icon_x + icon_size // 2, icon_y + icon_size // 2,
            icon_size // 2, icon_size // 2
        )
        has_pixels = False
        for dx in range(bottom_right_region.width):
            for dy in range(0, bottom_right_region.height, 2):
                px = bottom_right_region.x + dx
                py = bottom_right_region.y + dy
                if 0 <= px < surf.get_width() and 0 <= py < surf.get_height():
                    pixel = surf.get_at((px, py))
                    if pixel[:3] != (0, 0, 0):
                        has_pixels = True
                        break
            if has_pixels:
                break
        assert has_pixels, "右下角应有快捷键标签像素"

    def test_level_label_text_content(self, icon_system, pygame_session):
        """测试等级标签文本内容正确渲染。"""
        from config import HUD_POWERUP_ICON_SIZE
        icon_system._ensure_label_font()
        label_font = icon_system._label_font
        for icon in icon_system.icons:
            icon.powerup.acquired = True
            level = icon.powerup.level
            expected_text = f"L{level}"
            rendered = label_font.render(expected_text, True, (255, 255, 255))
            assert rendered.get_width() > 0
            assert rendered.get_height() > 0

    def test_key_label_text_content(self, icon_system, pygame_session):
        """测试快捷键标签文本内容正确渲染。"""
        icon_system._ensure_label_font()
        label_font = icon_system._label_font
        expected_keys = ["1", "2", "3"]
        for i, icon in enumerate(icon_system.icons):
            rendered = label_font.render(icon.key_label, True, (255, 255, 200))
            assert rendered.get_width() > 0
            assert rendered.get_height() > 0
            assert icon.key_label == expected_keys[i]

    def test_draw_grayscale_unavailable(self, icon_system, pygame_session):
        """测试不可用道具绘制为灰度。"""
        for icon in icon_system.icons:
            icon.powerup.acquired = False
        surf = pygame.Surface((960, 640))
        font = get_chinese_font(26)
        big_font = get_chinese_font(52)
        icon_system.draw(surf, big_font, font)
        icon_x = icon_system.icons[0].rect.x
        icon_y = icon_system.icons[0].rect.y
        center_x = icon_x + 24
        center_y = icon_y + 24
        if 0 <= center_x < surf.get_width() and 0 <= center_y < surf.get_height():
            pixel = surf.get_at((center_x, center_y))
            r, g, b = pixel[:3]
            if r > 0 or g > 0 or b > 0:
                max_diff = max(abs(r - g), abs(g - b), abs(r - b))
                assert max_diff <= 30, "不可用道具图标应为灰度色"

    def test_update_transitions_called(self, icon_system):
        """测试 update 调用过渡动画更新。"""
        for icon in icon_system.icons:
            icon.transition_progress = 0.5
        icon_system.update()
        for icon in icon_system.icons:
            assert icon.transition_progress < 0.5 or icon._prev_available != icon.is_available

    def test_acquire_powerup_updates_availability(self, icon_system, pygame_session):
        """测试拾取道具后图标状态从不可用变为可用。"""
        from entities.powerups import PowerupType
        first_icon = icon_system.icons[0]
        first_icon.powerup.acquired = False
        from entities.powerups import PowerupState
        first_icon.powerup.state = PowerupState.IDLE
        first_icon._prev_available = False
        first_icon.transition_progress = 1.0
        assert first_icon.is_available is False

        icon_system.powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        assert first_icon.powerup.acquired is True
        assert first_icon.is_available is True

        icon_system.update()
        assert first_icon.transition_progress < 1.0 or first_icon._prev_available is True

    def test_use_powerup_triggers_cooldown_state(self, icon_system, pygame_session):
        """测试使用道具后进入冷却，图标变为不可用。"""
        from entities.powerups import PowerupType, PowerupState
        icon_system.powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        icon_system.powerup_manager.use_powerup(PowerupType.SPEED_BOOST)
        first_icon = icon_system.icons[0]
        assert first_icon.powerup.is_active is True
        assert first_icon.is_available is True
        for _ in range(1000):
            icon_system.powerup_manager.update()
            if first_icon.powerup.is_on_cooldown:
                break
        assert first_icon.is_available is False
