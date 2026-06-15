# -*- coding: utf-8 -*-
"""
core/state.py - 游戏状态管理模块

负责游戏状态机和关卡过渡动画。
"""

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TRANSITION_DURATION_FRAMES, TRANSITION_COLOR,
    LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT,
    LOADING_BAR_BG, LOADING_BAR_FG, LOADING_TEXT_COLOR,
    TOTAL_LEVELS,
)

from menus import GameState
from levels import get_level_config


class StateManager:
    """
    游戏状态管理器。

    负责:
    - 游戏状态切换（主菜单、游戏中、暂停、过渡、加载）
    - 关卡过渡动画（淡出/淡入）
    - 加载界面绘制
    """

    def __init__(self, game):
        self.game = game
        self.transition_frame = 0
        self.transition_phase = 0
        self.pending_level = 0
        self.pending_spawn = (0, 0)
        self.loading_progress = 0.0

    def start_transition(self, target_level, target_x, target_y):
        """
        启动关卡切换过渡流程。

        Args:
            target_level: 目标关卡编号（-1 表示同关卡内传送）
            target_x, target_y: 目标出生坐标
        """
        self.game.game_state = GameState.TRANSITIONING
        self.transition_phase = 0
        self.transition_frame = 0

        if target_level == -1:
            self.pending_level = self.game.current_level
        else:
            from levels import LEVEL_BUILDERS
            self.pending_level = target_level % len(LEVEL_BUILDERS)
        self.pending_spawn = (target_x, target_y)

        self.game._spawn_particles(
            self.game.player.x + self.game.player.width / 2,
            self.game.player.y + self.game.player.height / 2,
            count=20,
            colors=self.game.portal_particle_colors,
            spread=5,
            life=30,
            size=5,
        )

    def update_transition(self):
        """更新过渡动画状态机。"""
        self.transition_frame += 1
        half_duration = TRANSITION_DURATION_FRAMES // 2

        if self.transition_phase == 0:
            if self.transition_frame >= half_duration:
                self.transition_phase = 1
                self.transition_frame = 0
                self.game.game_state = GameState.LOADING
                self.loading_progress = 0.0

        elif self.transition_phase == 1:
            self.loading_progress = min(1.0, self.transition_frame / half_duration)
            if self.transition_frame >= half_duration:
                spawn_x, spawn_y = self.pending_spawn
                self.game._load_level(self.pending_level, spawn_x, spawn_y, immediate=False)
                self.transition_phase = 2
                self.transition_frame = 0

        elif self.transition_phase == 2:
            if self.transition_frame >= half_duration:
                self.game.game_state = GameState.PLAYING
                self.transition_phase = 0
                self.transition_frame = 0

    def draw_transition(self, screen):
        """绘制过渡动画遮罩层（淡出/淡入）。"""
        half_duration = TRANSITION_DURATION_FRAMES // 2
        if self.transition_phase == 0:
            alpha = int(255 * self.transition_frame / half_duration)
        elif self.transition_phase == 2:
            alpha = int(255 * (1 - self.transition_frame / half_duration))
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*TRANSITION_COLOR, alpha))
        screen.blit(overlay, (0, 0))

    def draw_loading_screen(self, screen, title_font, big_font, font):
        """绘制加载界面，含关卡名称、描述和进度条。"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(TRANSITION_COLOR)
        screen.blit(overlay, (0, 0))

        target_config = get_level_config(self.pending_level)
        level_num = self.pending_level + 1

        title = title_font.render(f"第 {level_num} 关", True, LOADING_TEXT_COLOR)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        screen.blit(title, (title_x, SCREEN_HEIGHT // 2 - 140))

        name = big_font.render(target_config.name, True, LOADING_TEXT_COLOR)
        name_x = (SCREEN_WIDTH - name.get_width()) // 2
        screen.blit(name, (name_x, SCREEN_HEIGHT // 2 - 70))

        desc = font.render(target_config.description, True, (200, 200, 220))
        desc_x = (SCREEN_WIDTH - desc.get_width()) // 2
        screen.blit(desc, (desc_x, SCREEN_HEIGHT // 2 - 20))

        bar_x = (SCREEN_WIDTH - LOADING_BAR_WIDTH) // 2
        bar_y = SCREEN_HEIGHT // 2 + 40
        pygame.draw.rect(
            screen, LOADING_BAR_BG,
            (bar_x, bar_y, LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT),
            border_radius=10,
        )

        fill_width = int(LOADING_BAR_WIDTH * self.loading_progress)
        if fill_width > 0:
            pygame.draw.rect(
                screen, LOADING_BAR_FG,
                (bar_x, bar_y, fill_width, LOADING_BAR_HEIGHT),
                border_radius=10,
            )

        pct = int(self.loading_progress * 100)
        pct_text = font.render(f"加载中... {pct}%", True, LOADING_TEXT_COLOR)
        pct_x = (SCREEN_WIDTH - pct_text.get_width()) // 2
        screen.blit(pct_text, (pct_x, bar_y + LOADING_BAR_HEIGHT + 15))
