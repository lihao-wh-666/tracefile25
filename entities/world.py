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
    FRAGILE_CRACK_DELAY_FRAMES, FRAGILE_RESPAWN_COOLDOWN_FRAMES,
    FRAGILE_WARNING_FLASH_INTERVAL, FRAGILE_BREAK_ANIMATION_FRAMES,
    FRAGILE_PARTICLE_COUNT,
    FRAGILE_PLATFORM_COLOR, FRAGILE_PLATFORM_TOP_COLOR,
    FRAGILE_PLATFORM_CRACK_COLOR, FRAGILE_PLATFORM_WARNING_COLOR,
    FRAGILE_PLATFORM_GHOST_COLOR, FRAGILE_PARTICLE_COLORS,
    FPS,
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


class FragilePlatformState:
    SOLID = 0
    CRACKING = 1
    BROKEN = 2
    COOLDOWN = 3


class FragilePlatform:
    """
    易碎平台类，实现状态机循环：
      SOLID（完整可踩踏）
        ↓ 玩家踩踏达到 CRACK_DELAY
      CRACKING（预警闪烁）
        ↓ 达到 BREAK_ANIMATION
      BROKEN（碎裂失效，无碰撞）
        ↓ 达到 RESPAWN_COOLDOWN
      COOLDOWN（幽灵轮廓，冷却恢复）
        ↓ 冷却结束
      SOLID（恢复）

    属性:
        rect: 平台碰撞矩形
        state: 当前状态 (FragilePlatformState)
        timer: 各阶段通用计时器（帧）
        stand_timer: 玩家持续踩踏计时器（帧）
        was_standing: 上一帧玩家是否站在平台上
        crack_lines: 碎裂裂纹坐标列表
        break_particles: 碎裂动画过程中产生的粒子数据列表
        spawn_particles_cb: 粒子生成回调函数 (x, y, count, colors)
    """

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.state = FragilePlatformState.SOLID
        self.timer = 0
        self.stand_timer = 0
        self.was_standing = False
        self.crack_lines = []
        self.break_particles = []
        self.spawn_particles_cb = None
        self._flash_counter = 0

    def is_solid(self):
        """返回当前是否具有实体碰撞（可踩踏）。"""
        return self.state in (FragilePlatformState.SOLID, FragilePlatformState.CRACKING)

    def _player_is_standing(self, player_rect):
        """
        检测玩家是否稳定地站在平台顶部。

        判定条件：
        1. 玩家矩形底部与平台顶部距离 <= 2 像素
        2. 水平方向有重叠
        3. 玩家垂直速度 >= 0（非上升中）
        """
        if player_rect is None:
            return False
        horizontal_overlap = (
            player_rect.right > self.rect.left + 2
            and player_rect.left < self.rect.right - 2
        )
        vertical_align = abs((player_rect.bottom) - self.rect.top) <= 3
        return horizontal_overlap and vertical_align

    def _generate_crack_lines(self):
        """生成预警阶段显示的裂纹线条。"""
        self.crack_lines = []
        w, h = self.rect.width, self.rect.height
        rng = random.Random(hash((self.rect.x, self.rect.y, w)))
        num_lines = max(3, w // 20)
        for _ in range(num_lines):
            x_start = rng.randint(4, w - 4)
            y_start = rng.randint(2, h // 2)
            segments = []
            cx, cy = x_start, y_start
            for _ in range(rng.randint(2, 4)):
                nx = cx + rng.randint(-8, 8)
                ny = cy + rng.randint(2, max(3, h // 3))
                nx = max(2, min(w - 2, nx))
                ny = max(2, min(h - 2, ny))
                segments.append((cx, cy, nx, ny))
                cx, cy = nx, ny
            self.crack_lines.extend(segments)

    def _init_break_animation(self):
        """触发碎裂：生成碎裂动画粒子数据并调用粒子回调。"""
        if self.spawn_particles_cb:
            cx = self.rect.x + self.rect.width // 2
            cy = self.rect.y + self.rect.height // 2
            self.spawn_particles_cb(
                cx, cy,
                count=FRAGILE_PARTICLE_COUNT,
                colors=FRAGILE_PARTICLE_COLORS,
                spread=5, life=30, size=4,
            )

        rng = random.Random(hash((self.rect.x, self.rect.y, self.rect.width, "break")))
        num_pieces = max(6, self.rect.width // 12)
        self.break_particles = []
        for _ in range(num_pieces):
            px = self.rect.x + rng.randint(0, self.rect.width)
            py = self.rect.y + rng.randint(0, self.rect.height)
            vx = rng.uniform(-4, 4)
            vy = rng.uniform(-6, -1)
            size = rng.randint(3, 7)
            color_idx = rng.randint(0, len(FRAGILE_PARTICLE_COLORS) - 1)
            self.break_particles.append([px, py, vx, vy, size, color_idx])

    def _update_break_particles(self):
        """更新碎裂碎片的物理运动。"""
        if not self.break_particles:
            return
        gravity = 0.4
        for p in self.break_particles:
            p[3] += gravity
            p[0] += p[2]
            p[1] += p[3]
        self.break_particles = [p for p in self.break_particles if p[1] < self.rect.y + 400]

    def update(self, player_rect=None, player_vy=0):
        """
        每帧更新易碎平台状态机。

        Args:
            player_rect: 玩家碰撞矩形（pygame.Rect），用于检测踩踏
            player_vy: 玩家当前垂直速度，辅助判定落地
        """
        standing = self._player_is_standing(player_rect) if player_rect else False

        if self.state == FragilePlatformState.SOLID:
            if standing:
                self.stand_timer += 1
                if self.stand_timer >= FRAGILE_CRACK_DELAY_FRAMES:
                    self.state = FragilePlatformState.CRACKING
                    self.timer = 0
                    self._generate_crack_lines()
            else:
                self.stand_timer = max(0, self.stand_timer - 2)
            self.was_standing = standing

        elif self.state == FragilePlatformState.CRACKING:
            self.timer += 1
            self._flash_counter += 1
            if self.timer >= FRAGILE_BREAK_ANIMATION_FRAMES:
                self.state = FragilePlatformState.BROKEN
                self.timer = 0
                self._init_break_animation()
            self.was_standing = standing

        elif self.state == FragilePlatformState.BROKEN:
            self.timer += 1
            self._update_break_particles()
            if self.timer >= FRAGILE_BREAK_ANIMATION_FRAMES:
                self.state = FragilePlatformState.COOLDOWN
                self.timer = 0
            self.was_standing = False

        elif self.state == FragilePlatformState.COOLDOWN:
            self.timer += 1
            self._flash_counter += 1
            if self.timer >= FRAGILE_RESPAWN_COOLDOWN_FRAMES:
                self.state = FragilePlatformState.SOLID
                self.timer = 0
                self.stand_timer = 0
                self.crack_lines = []
                self.break_particles = []
            self.was_standing = False

    def draw(self, surface, camera_x, level_config=None):
        """
        根据当前状态绘制易碎平台。

        状态视觉:
        - SOLID:     木质色平台 + 顶部亮边（轻微色调区别于普通平台）
        - CRACKING:  叠加裂纹 + 橙/原色交替闪烁预警
        - BROKEN:    绘制飞溅碎片，平台本身不可见
        - COOLDOWN:  半透明幽灵轮廓 + 呼吸闪烁效果
        """
        draw_x = self.rect.x - camera_x
        draw_rect = pygame.Rect(draw_x, self.rect.y, self.rect.width, self.rect.height)

        if draw_rect.right < -50 or draw_rect.left > SCREEN_WIDTH + 50:
            return

        if level_config:
            plat_col = level_config.platform_color
            plat_top_col = level_config.platform_top_color
        else:
            plat_col = FRAGILE_PLATFORM_COLOR
            plat_top_col = FRAGILE_PLATFORM_TOP_COLOR

        if self.state == FragilePlatformState.SOLID:
            pygame.draw.rect(surface, plat_col, draw_rect)
            top_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 5)
            pygame.draw.rect(surface, plat_top_col, top_rect)
            if self.stand_timer > 0 and FRAGILE_CRACK_DELAY_FRAMES > 0:
                progress = self.stand_timer / FRAGILE_CRACK_DELAY_FRAMES
                if progress > 0.3:
                    bar_w = int(draw_rect.width * progress)
                    bar_rect = pygame.Rect(
                        draw_rect.x, draw_rect.y - 5, bar_w, 3
                    )
                    progress_color = (
                        int(255 * progress),
                        int(200 * (1 - progress)),
                        40,
                    )
                    pygame.draw.rect(surface, progress_color, bar_rect)

        elif self.state == FragilePlatformState.CRACKING:
            flash_on = (self._flash_counter // FRAGILE_WARNING_FLASH_INTERVAL) % 2 == 0
            base_col = FRAGILE_PLATFORM_WARNING_COLOR if flash_on else plat_col
            pygame.draw.rect(surface, base_col, draw_rect)
            top_col = FRAGILE_PLATFORM_WARNING_COLOR if flash_on else plat_top_col
            top_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 5)
            pygame.draw.rect(surface, top_col, top_rect)
            for x1, y1, x2, y2 in self.crack_lines:
                pygame.draw.line(
                    surface, FRAGILE_PLATFORM_CRACK_COLOR,
                    (draw_rect.x + x1, draw_rect.y + y1),
                    (draw_rect.x + x2, draw_rect.y + y2),
                    2,
                )

        elif self.state == FragilePlatformState.BROKEN:
            for (px, py, vx, vy, size, ci) in self.break_particles:
                color = FRAGILE_PARTICLE_COLORS[ci % len(FRAGILE_PARTICLE_COLORS)]
                pygame.draw.rect(
                    surface, color,
                    (int(px - camera_x), int(py), size, size),
                )

        elif self.state == FragilePlatformState.COOLDOWN:
            pulse = (math.sin(self._flash_counter * 0.1) + 1) * 0.5
            alpha = int(60 + pulse * 60)
            ghost_surf = pygame.Surface(
                (draw_rect.width, draw_rect.height), pygame.SRCALPHA
            )
            ghost_r, ghost_g, ghost_b = FRAGILE_PLATFORM_GHOST_COLOR
            pygame.draw.rect(
                ghost_surf, (ghost_r, ghost_g, ghost_b, alpha),
                (0, 0, draw_rect.width, draw_rect.height),
                2,
            )
            surface.blit(ghost_surf, (draw_rect.x, draw_rect.y))
            if FRAGILE_RESPAWN_COOLDOWN_FRAMES > 0:
                progress = 1.0 - (self.timer / FRAGILE_RESPAWN_COOLDOWN_FRAMES)
                bar_w = int(draw_rect.width * progress)
                bar_rect = pygame.Rect(
                    draw_rect.x, draw_rect.y + draw_rect.height + 3, bar_w, 2
                )
                pygame.draw.rect(surface, FRAGILE_PLATFORM_GHOST_COLOR, bar_rect)
