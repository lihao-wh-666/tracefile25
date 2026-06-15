# -*- coding: utf-8 -*-
"""
entities/world.py - 世界元素模块

包含 Platform、Ladder、Portal 等世界交互元素。
"""

import math
import random
import pygame

from config import (
    SCREEN_WIDTH,
    GROUND_COLOR, DIRT_COLOR, PLATFORM_COLOR, PLATFORM_TOP_COLOR,
    PLATFORM_HIGHLIGHT, GRASS_DARK, GRASS_LIGHT, GRASS_TUFT_DARK,
    GRASS_TUFT_LIGHT, PLATFORM_GRASS_SEED,
    LADDER_WIDTH, LADDER_COLOR, LADDER_RUNG_COLOR,
    LADDER_RUNG_SPACING,
    PORTAL_WIDTH, PORTAL_HEIGHT,
    PORTAL_COLOR_INNER, PORTAL_COLOR_OUTER, PORTAL_COLOR_GLOW,
    PORTAL_ACTIVATION_COINS, PORTAL_COOLDOWN_FRAMES,
)


class Platform:
    """
    平台对象，支持地面和浮动两种类型。

    属性:
        rect: 平台碰撞矩形
        is_ground: 是否为地面平台（绘制样式不同）
        grass_tufts: 浮动平台草束位置列表（地面平台每帧随机生成）
    """

    def __init__(self, x, y, width, height, is_ground=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_ground = is_ground
        self.grass_tufts = []

        if not is_ground and height <= 24:
            rng = random.Random(hash((x, y, width)))
            for _ in range(max(1, width // 30)):
                gx = rng.randint(4, width - 4)
                self.grass_tufts.append(gx)

    def draw(self, surface, camera_x, level_config=None):
        """
        绘制平台。

        地面平台：草地顶层 + 泥土下层 + 随机草束
        浮动平台：木板主体 + 草地顶层 + 亮边 + 预设草束

        支持通过 level_config 传入关卡配色覆盖默认颜色。

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移量
            level_config: 关卡配置对象（可选，提供关卡配色）
        """
        draw_rect = pygame.Rect(
            self.rect.x - camera_x,
            self.rect.y,
            self.rect.width,
            self.rect.height,
        )

        if draw_rect.right < 0 or draw_rect.left > SCREEN_WIDTH:
            return

        if level_config:
            ground_col = level_config.ground_color
            dirt_col = level_config.dirt_color
            plat_col = level_config.platform_color
            plat_top_col = level_config.platform_top_color
        else:
            ground_col = GROUND_COLOR
            dirt_col = DIRT_COLOR
            plat_col = PLATFORM_COLOR
            plat_top_col = PLATFORM_TOP_COLOR

        if self.is_ground:
            pygame.draw.rect(surface, ground_col, draw_rect)
            dirt_rect = pygame.Rect(
                draw_rect.x,
                draw_rect.y + 6,
                draw_rect.width,
                draw_rect.height - 6,
            )
            pygame.draw.rect(surface, dirt_col, dirt_rect)

            rng = random.Random(PLATFORM_GRASS_SEED)
            for _ in range(draw_rect.width // 8):
                gx = draw_rect.x + rng.randint(0, draw_rect.width)
                gh = rng.randint(3, 8)
                pygame.draw.line(
                    surface,
                    GRASS_DARK,
                    (gx, draw_rect.y),
                    (gx - 2, draw_rect.y - gh),
                    2,
                )
                pygame.draw.line(
                    surface,
                    GRASS_LIGHT,
                    (gx + 2, draw_rect.y),
                    (gx, draw_rect.y - gh + 1),
                    2,
                )
        else:
            pygame.draw.rect(surface, plat_col, draw_rect)

            top_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 6)
            pygame.draw.rect(surface, plat_top_col, top_rect)

            highlight_rect = pygame.Rect(
                draw_rect.x, draw_rect.y + 6, draw_rect.width, 2
            )
            pygame.draw.rect(surface, PLATFORM_HIGHLIGHT, highlight_rect)

            for gx in self.grass_tufts:
                base_x = draw_rect.x + gx
                pygame.draw.line(
                    surface,
                    GRASS_TUFT_DARK,
                    (base_x, draw_rect.y),
                    (base_x - 1, draw_rect.y - 5),
                    2,
                )
                pygame.draw.line(
                    surface,
                    GRASS_TUFT_LIGHT,
                    (base_x + 2, draw_rect.y),
                    (base_x + 3, draw_rect.y - 4),
                    2,
                )


class Ladder:
    """
    梯子对象，允许玩家上下攀爬。

    属性:
        x: 梯子左侧 x 坐标
        y: 梯子顶部 y 坐标
        width: 梯子宽度
        height: 梯子总高度
        rect: 碰撞检测用矩形
    """

    def __init__(self, x, y, height):
        self.x = x
        self.y = y
        self.width = LADDER_WIDTH
        self.height = height
        self.rect = pygame.Rect(x, y, self.width, height)

    def update(self):
        """梯子不需要每帧更新。"""
        pass

    def draw(self, surface, camera_x):
        sx = int(self.x - camera_x)
        sy = int(self.y)

        if sx + self.width < 0 or sx > SCREEN_WIDTH:
            return

        pygame.draw.rect(
            surface,
            LADDER_COLOR,
            (sx, sy, 4, self.height),
        )
        pygame.draw.rect(
            surface,
            LADDER_COLOR,
            (sx + self.width - 4, sy, 4, self.height),
        )

        rung_y = sy
        while rung_y < sy + self.height:
            pygame.draw.line(
                surface,
                LADDER_RUNG_COLOR,
                (sx + 3, rung_y),
                (sx + self.width - 4, rung_y),
                3,
            )
            rung_y += LADDER_RUNG_SPACING


class Portal:
    """
    传送门实体类，实现关卡间或区域间的快速跳转。

    核心特性:
    - 激活条件：可配置收集金币数量作为激活门槛
    - 视觉反馈：未激活时灰暗，激活后发光脉动 + 粒子特效
    - 冷却机制：防止连续触发传送
    - 目标配置：可指定目标关卡编号和目标位置坐标

    属性:
        x, y: 传送门左上角坐标
        target_level: 目标关卡编号（-1 表示同关卡内传送）
        target_x, target_y: 传送后的目标坐标
        required_coins: 激活所需金币数量
        activated: 是否已激活
        cooldown: 冷却计时器（防止连传）
        anim_phase: 动画相位（用于发光脉动）
    """

    def __init__(self, x, y, target_level, target_x, target_y, required_coins=PORTAL_ACTIVATION_COINS):
        self.x = x
        self.y = y
        self.width = PORTAL_WIDTH
        self.height = PORTAL_HEIGHT
        self.target_level = target_level
        self.target_x = target_x
        self.target_y = target_y
        self.required_coins = required_coins
        self.activated = required_coins <= 0
        self.cooldown = 0
        self.anim_phase = 0.0

    def get_rect(self):
        """返回传送门碰撞检测矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, player_score=0):
        """
        更新传送门状态。

        Args:
            player_score: 当前玩家金币/得分，用于判断是否满足激活条件
        """
        if self.cooldown > 0:
            self.cooldown -= 1

        if not self.activated and player_score >= self.required_coins * 10:
            self.activated = True

        self.anim_phase += 0.08

    def can_trigger(self, player_rect, player_score=0):
        """
        检测是否可以触发传送。

        条件:
        1. 玩家矩形与传送门矩形重叠
        2. 传送门已激活（满足金币条件）
        3. 冷却时间已过

        Args:
            player_rect: 玩家碰撞矩形
            player_score: 当前玩家得分

        Returns:
            bool: 是否可以触发传送
        """
        if not self.activated and player_score >= self.required_coins * 10:
            self.activated = True
        if not self.activated:
            return False
        if self.cooldown > 0:
            return False
        return self.get_rect().colliderect(player_rect)

    def trigger(self):
        """触发传送，启动冷却计时。"""
        self.cooldown = PORTAL_COOLDOWN_FRAMES

    def draw(self, surface, camera_x, tick):
        """
        绘制传送门。

        未激活状态：灰暗半透明椭圆
        激活状态：多层椭圆叠加发光脉动效果 + 粒子光点

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移
            tick: 全局帧计数器
        """
        sx = int(self.x - camera_x)
        sy = int(self.y)
        cx = sx + self.width // 2
        cy = sy + self.height // 2

        if sx + self.width < -50 or sx > SCREEN_WIDTH + 50:
            return

        if not self.activated:
            r1, g1, b1 = PORTAL_COLOR_OUTER
            dim_color = (r1 // 3, g1 // 3, b1 // 3)
            pygame.draw.ellipse(
                surface, dim_color,
                (sx, sy, self.width, self.height),
                4
            )
            inner_color = (r1 // 4, g1 // 4, b1 // 4)
            pygame.draw.ellipse(
                surface, inner_color,
                (sx + 8, sy + 8, self.width - 16, self.height - 16)
            )
            return

        pulse = (math.sin(self.anim_phase) + 1) * 0.5

        glow_w = int(self.width * (1.0 + pulse * 0.15))
        glow_h = int(self.height * (1.0 + pulse * 0.1))
        glow_x = cx - glow_w // 2
        glow_y = cy - glow_h // 2
        glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        glow_alpha = int(80 + pulse * 60)
        pygame.draw.ellipse(
            glow_surf,
            (*PORTAL_COLOR_GLOW, glow_alpha),
            (0, 0, glow_w, glow_h)
        )
        surface.blit(glow_surf, (glow_x, glow_y))

        pygame.draw.ellipse(
            surface, PORTAL_COLOR_OUTER,
            (sx, sy, self.width, self.height),
            5
        )

        mid_w = self.width - 10
        mid_h = self.height - 10
        mid_x = sx + 5
        mid_y = sy + 5
        pygame.draw.ellipse(
            surface, PORTAL_COLOR_INNER,
            (mid_x, mid_y, mid_w, mid_h)
        )

        swirl_r = min(self.width, self.height) // 4
        for i in range(3):
            angle = self.anim_phase + i * (math.pi * 2 / 3)
            px = cx + int(math.cos(angle) * swirl_r)
            py = cy + int(math.sin(angle) * swirl_r * 0.7)
            pygame.draw.circle(surface, PORTAL_COLOR_GLOW, (px, py), 3)

        for i in range(2):
            angle = -self.anim_phase * 1.5 + i * math.pi
            px = cx + int(math.cos(angle) * swirl_r * 0.5)
            py = cy + int(math.sin(angle) * swirl_r * 0.5 * 0.7)
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)
