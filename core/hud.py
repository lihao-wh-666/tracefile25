# -*- coding: utf-8 -*-
"""
core/hud.py - HUD绘制模块

负责游戏抬头显示（HUD）的绘制。
扩展支持道具状态显示、道具通知等。
"""

import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, BLACK,
    COIN_COLLECT_SCORE,
    TOTAL_LEVELS,
    RANGED_AMMO_MAX,
    SHOW_VOLUME_PANEL_KEY,
    HUD_POWERUP_ICON_SIZE,
    HUD_POWERUP_ICON_MARGIN,
    HUD_POWERUP_START_X,
    HUD_POWERUP_START_Y_OFFSET,
    HUD_POWERUP_BAR_HEIGHT,
    HUD_POWERUP_BAR_BG,
    HUD_POWERUP_TEXT_COLOR,
    SPEED_BOOST_COLOR, SPEED_BOOST_DARK, SPEED_BOOST_GLOW,
    SHIELD_COLOR, SHIELD_DARK, SHIELD_GLOW,
    WEAPON_COLOR, WEAPON_DARK, WEAPON_GLOW,
)

from ui import ItemIconSystem
from entities.powerups import (
    PowerupType,
    PowerupState,
    SpeedBoostPowerup,
    ShieldPowerup,
    WeaponPowerup,
)


class HUDManager:
    """
    HUD管理器。

    负责:
    - 金币/得分显示
    - 关卡信息显示
    - 弹药显示
    - 操作提示显示
    - 道具状态图标和进度条
    - 道具获取通知弹窗
    """

    def __init__(self, game):
        self.game = game
        self.item_icon_system = ItemIconSystem(game, game.powerup_manager)
        self.item_icon_system.on_item_used = self._on_item_used

    def _on_item_used(self, powerup_type):
        """道具被使用时的回调。"""
        pass

    def handle_event(self, event):
        """处理鼠标事件，传递给道具图标系统。"""
        return self.item_icon_system.handle_event(event)

    def update(self):
        """更新 HUD 状态。"""
        self.item_icon_system.update()

    def on_resize(self, width, height):
        """响应屏幕尺寸变化。"""
        self.item_icon_system.on_resize(width, height)

    def draw_hud(self, screen, font, big_font):
        """绘制抬头显示（HUD）。"""
        SHADOW_OFFSET = 3

        coin_text = font.render(f"金币: {self.game.score}", True, WHITE)
        shadow_text = font.render(f"金币: {self.game.score}", True, BLACK)
        screen.blit(shadow_text, (20 + SHADOW_OFFSET, 15 + SHADOW_OFFSET))
        screen.blit(coin_text, (20, 15))

        if self.game.level_config:
            level_num = self.game.current_level + 1
            level_text = font.render(
                f"第 {level_num}/{TOTAL_LEVELS} 关: {self.game.level_config.name}",
                True, WHITE,
            )
            level_shadow = font.render(
                f"第 {level_num}/{TOTAL_LEVELS} 关: {self.game.level_config.name}",
                True, BLACK,
            )
            text_x = (SCREEN_WIDTH - level_text.get_width()) // 2
            screen.blit(level_shadow, (text_x + SHADOW_OFFSET, 15 + SHADOW_OFFSET))
            screen.blit(level_text, (text_x, 15))

        hint = font.render(
            "移动:方向键/WASD  跳跃:空格  攀爬:上下  J:近战  K:射击  R:换弹",
            True, (50, 50, 80),
        )
        screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 15, 15))

        ammo_color = (255, 255, 100) if self.game.player.ammo > 5 else (255, 80, 80)
        if self.game.player.reloading:
            ammo_color = (150, 150, 150)
        ammo_text = font.render(
            f"弹药: {self.game.player.ammo}/{RANGED_AMMO_MAX}",
            True, ammo_color,
        )
        ammo_shadow = font.render(
            f"弹药: {self.game.player.ammo}/{RANGED_AMMO_MAX}",
            True, BLACK,
        )
        screen.blit(ammo_shadow, (20 + SHADOW_OFFSET, 40 + SHADOW_OFFSET))
        screen.blit(ammo_text, (20, 40))

        audio_hint = font.render(
            "[V] 音频设置  [1-3]使用道具  [Q]切换武器",
            True, (80, 80, 120) if not self.game.volume_panel.visible else (100, 200, 255),
        )
        screen.blit(audio_hint, (SCREEN_WIDTH - audio_hint.get_width() - 15, 40))

        self.item_icon_system.draw(screen, big_font, font)
        self._draw_powerup_notification(screen, big_font, font)

    def _draw_powerup_status(self, screen, font):
        """在 HUD 左下角绘制三种道具的状态图标和进度条。"""
        pm = getattr(self.game, "powerup_manager", None)
        if pm is None:
            return

        x = HUD_POWERUP_START_X
        y = HUD_POWERUP_START_Y
        size = HUD_POWERUP_ICON_SIZE
        margin = HUD_POWERUP_ICON_MARGIN

        powerups_with_key = [
            (PowerupType.SPEED_BOOST, "1"),
            (PowerupType.SHIELD, "2"),
            (PowerupType.WEAPON, "3"),
        ]

        for ptype, key_label in powerups_with_key:
            p = pm.get_powerup(ptype)
            if p is None:
                continue

            self._draw_powerup_icon(screen, x, y, size, p, key_label, font)
            x += size + margin

    def _draw_powerup_icon(self, screen, x, y, size, powerup, key_label, font):
        """绘制单个道具图标（含背景、进度条、等级和状态）。"""
        is_active = powerup.is_active
        is_cooling = powerup.is_on_cooldown
        disabled = not (powerup.can_activate or is_active or is_cooling)

        if isinstance(powerup, SpeedBoostPowerup):
            main_c = SPEED_BOOST_COLOR
            dark_c = SPEED_BOOST_DARK
            glow_c = SPEED_BOOST_GLOW
            symbol_dots = self._speed_symbol(x, y, size)
        elif isinstance(powerup, ShieldPowerup):
            main_c = SHIELD_COLOR
            dark_c = SHIELD_DARK
            glow_c = SHIELD_GLOW
            symbol_dots = self._shield_symbol(x, y, size)
        else:
            main_c = WEAPON_COLOR
            dark_c = WEAPON_DARK
            glow_c = WEAPON_GLOW
            symbol_dots = self._weapon_symbol(x, y, size)

        bg_alpha = 180
        if disabled:
            bg_alpha = 80

        icon_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        bg_color = (*dark_c, bg_alpha)
        pygame.draw.rect(icon_surf, bg_color, (0, 0, size, size), border_radius=6)

        border_c = main_c if not disabled else (100, 100, 100)
        pygame.draw.rect(icon_surf, border_c, (0, 0, size, size), width=2, border_radius=6)

        if is_active:
            pulse = 0.5 + 0.5 * math.sin(self.game.tick * 0.15)
            glow_alpha = int(60 + 40 * pulse)
            glow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                (*glow_c, glow_alpha),
                (2, 2, size - 4, size - 4),
                border_radius=4,
            )
            icon_surf.blit(glow_surf, (0, 0))

        symbol_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        sym_color = glow_c if not disabled else (150, 150, 150)
        for pt in symbol_dots:
            pygame.draw.circle(symbol_surf, sym_color, pt, max(1, size // 14))
        icon_surf.blit(symbol_surf, (0, 0))

        if isinstance(powerup, ShieldPowerup) and is_active:
            bar_y = size - HUD_POWERUP_BAR_HEIGHT - 4
            self._draw_bar_on_surf(
                icon_surf, 4, bar_y, size - 8, HUD_POWERUP_BAR_HEIGHT,
                powerup.shield_ratio, SHIELD_GLOW, SHIELD_DARK
            )
        elif isinstance(powerup, WeaponPowerup):
            bar_y = size - HUD_POWERUP_BAR_HEIGHT - 4
            self._draw_bar_on_surf(
                icon_surf, 4, bar_y, size - 8, HUD_POWERUP_BAR_HEIGHT,
                powerup.uses_ratio, WEAPON_GLOW, WEAPON_DARK
            )
        else:
            if is_active or is_cooling:
                bar_y = size - HUD_POWERUP_BAR_HEIGHT - 4
                ratio = powerup.progress_ratio
                bar_color = glow_c if is_active else (120, 120, 140)
                self._draw_bar_on_surf(
                    icon_surf, 4, bar_y, size - 8, HUD_POWERUP_BAR_HEIGHT,
                    ratio, bar_color, HUD_POWERUP_BAR_BG
                )

        lvl_c = HUD_POWERUP_TEXT_COLOR if not disabled else (120, 120, 120)
        lvl_text = font.render(f"L{powerup.level}", True, lvl_c)
        icon_surf.blit(lvl_text, (3, 2))

        key_c = (255, 255, 200) if not disabled else (120, 120, 120)
        key_surf = font.render(key_label, True, key_c)
        kw = key_surf.get_width()
        kh = key_surf.get_height()
        icon_surf.blit(key_surf, (size - kw - 3, size - kh - 3))

        screen.blit(icon_surf, (x, y))

    def _draw_bar_on_surf(self, surf, x, y, w, h, ratio, fg_color, bg_color):
        """在指定 Surface 上绘制进度条。"""
        pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=2)
        fill_w = max(1, int(w * max(0.0, min(1.0, ratio))))
        pygame.draw.rect(surf, fg_color, (x, y, fill_w, h), border_radius=2)

    def _speed_symbol(self, x, y, size):
        """加速道具符号：三条向右的速度线。"""
        cx = x + size // 2
        cy = y + size // 2
        s = size // 3
        return [
            (cx - s, cy - s // 2),
            (cx, cy),
            (cx + s, cy + s // 2),
        ]

    def _shield_symbol(self, x, y, size):
        """护盾道具符号：盾形多边形点阵。"""
        cx = x + size // 2
        cy = y + size // 2
        s = size // 3
        pts = []
        for angle_deg in range(0, 360, 45):
            a = math.radians(angle_deg - 90)
            pts.append((cx + int(math.cos(a) * s), cy + int(math.sin(a) * s * 0.9)))
        return pts

    def _weapon_symbol(self, x, y, size):
        """武器道具符号：交叉剑形点阵。"""
        cx = x + size // 2
        cy = y + size // 2
        s = size // 3
        return [
            (cx - s, cy + s),
            (cx, cy),
            (cx + s, cy - s),
            (cx - s + 3, cy + s - 3),
            (cx + s - 3, cy - s + 3),
        ]

    def _draw_powerup_notification(self, screen, big_font, font):
        """绘制道具获取/升级通知（从顶部滑入）。"""
        pm = getattr(self.game, "powerup_manager", None)
        if pm is None:
            return
        if not pm.has_notification:
            return

        alpha = pm.notification_alpha
        if alpha <= 0:
            return

        text = pm.notification_text
        pad = 16
        text_surf = font.render(text, True, HUD_POWERUP_TEXT_COLOR)
        tw = text_surf.get_width()
        th = text_surf.get_height()

        box_w = tw + pad * 2
        box_h = th + pad
        bx = (SCREEN_WIDTH - box_w) // 2

        total_dur = pm.NOTIFICATION_DURATION
        t = 1.0 - (pm.notification_timer / total_dur)
        if t < 0.15:
            slide = (t / 0.15)
            by = int(-box_h + box_h * slide)
        elif t > 0.85:
            slide = 1.0 - ((t - 0.85) / 0.15)
            by = int(-box_h + box_h * slide)
        else:
            by = 0

        by += 90

        if alpha < 1.0:
            box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            a = int(220 * alpha)
            pygame.draw.rect(
                box_surf, (20, 30, 50, a), (0, 0, box_w, box_h), border_radius=8
            )
            pygame.draw.rect(
                box_surf, (100, 200, 255, a), (0, 0, box_w, box_h),
                width=2, border_radius=8
            )
            text_alpha_surf = text_surf.copy()
            text_alpha_surf.set_alpha(int(255 * alpha))
            box_surf.blit(text_alpha_surf, (pad, (box_h - th) // 2))
            screen.blit(box_surf, (bx, by))
        else:
            pygame.draw.rect(
                screen, (20, 30, 50, 220), (bx, by, box_w, box_h), border_radius=8
            )
            pygame.draw.rect(
                screen, (100, 200, 255), (bx, by, box_w, box_h),
                width=2, border_radius=8
            )
            screen.blit(text_surf, (bx + pad, by + (box_h - th) // 2))
