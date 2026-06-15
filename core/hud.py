# -*- coding: utf-8 -*-
"""
core/hud.py - HUD绘制模块

负责游戏抬头显示（HUD）的绘制。
"""

import pygame

from config import (
    SCREEN_WIDTH,
    WHITE, BLACK,
    COIN_COLLECT_SCORE,
    TOTAL_LEVELS,
    RANGED_AMMO_MAX,
    SHOW_VOLUME_PANEL_KEY,
)


class HUDManager:
    """
    HUD管理器。

    负责:
    - 金币/得分显示
    - 关卡信息显示
    - 弹药显示
    - 操作提示显示
    """

    def __init__(self, game):
        self.game = game

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
            "[V] 音频设置",
            True, (80, 80, 120) if not self.game.volume_panel.visible else (100, 200, 255),
        )
        screen.blit(audio_hint, (SCREEN_WIDTH - audio_hint.get_width() - 15, 40))
