# -*- coding: utf-8 -*-
"""
entities/items.py - 可收集物品模块

包含 Particle、Coin、AmmoPickup 等物品类。
"""

import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COIN_COLOR, COIN_DARK, COIN_COLLECT_ANIM, COIN_BOB_AMPLITUDE,
    RANGED_AMMO_PICKUP_AMOUNT, AMMO_PICKUP_COLOR, AMMO_PICKUP_DARK,
)


class Particle:
    """
    粒子对象，用于各种视觉特效。

    属性:
        x, y: 粒子位置坐标
        vx, vy: 粒子速度向量
        color: 粒子颜色 RGB 元组
        life: 剩余生命周期帧数
        max_life: 初始总帧数（用于透明度插值）
        size: 粒子基础半径
    """

    def __init__(self, x, y, vx, vy, color, life, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        """更新粒子位置和生命周期，模拟重力效果。"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surface, camera_x):
        """
        在屏幕上绘制粒子，透明度随生命周期衰减。

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移量
        """
        if self.life <= 0:
            return

        alpha = self.life / self.max_life
        size = max(1, int(self.size * alpha))
        sx = int(self.x - camera_x)
        sy = int(self.y)

        if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
            pygame.draw.circle(surface, self.color, (sx, sy), size)


class Coin:
    """
    可收集金币对象，具有上下浮动动画和收集特效。

    属性:
        x, y: 金币中心坐标
        radius: 金币半径
        collected: 是否已被收集
        bob_offset: 浮动动画相位偏移（避免所有金币同步）
        collect_anim: 收集动画剩余帧数
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.collected = False
        self.bob_offset = random.random() * math.pi * 2
        self.collect_anim = 0

    def get_rect(self):
        """返回用于碰撞检测的矩形区域。"""
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )

    def update(self):
        """更新收集动画计时器。"""
        if self.collect_anim > 0:
            self.collect_anim -= 1

    def draw(self, surface, camera_x, tick):
        """
        绘制金币，包含上下浮动和旋转效果。

        未收集时：使用椭圆水平压缩模拟旋转，正弦函数模拟浮动
        收集后：逐渐放大并淡出

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移量
            tick: 全局帧计数器（用于动画计算）
        """
        if self.collected and self.collect_anim <= 0:
            return

        bob_y = math.sin(tick * 0.05 + self.bob_offset) * COIN_BOB_AMPLITUDE
        sx = int(self.x - camera_x)
        sy = int(self.y + bob_y)

        if self.collected:
            alpha = self.collect_anim / COIN_COLLECT_ANIM
            size = int(self.radius * (2 - alpha))
            pygame.draw.circle(surface, COIN_COLOR, (sx, sy), size)
            return

        stretch = abs(math.sin(tick * 0.08 + self.bob_offset))
        w = max(3, int(self.radius * 2 * stretch))
        h = self.radius * 2

        pygame.draw.ellipse(surface, COIN_DARK, (sx - w // 2, sy - h // 2, w, h))

        inner_w = max(2, w - 4)
        inner_h = h - 4
        if inner_w > 0 and inner_h > 0:
            pygame.draw.ellipse(
                surface,
                COIN_COLOR,
                (sx - inner_w // 2, sy - inner_h // 2, inner_w, inner_h),
            )


class AmmoPickup:
    """
    弹药拾取物，玩家接触后恢复弹药。

    属性:
        x, y: 弹药拾取物中心坐标
        collected: 是否已被拾取
        bob_offset: 浮动动画相位偏移
    """

    def __init__(self, x, y, amount=RANGED_AMMO_PICKUP_AMOUNT):
        self.x = x
        self.y = y
        self.radius = 8
        self.amount = amount
        self.collected = False
        self.bob_offset = random.random() * math.pi * 2

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )

    def draw(self, surface, camera_x, tick):
        if self.collected:
            return

        bob_y = math.sin(tick * 0.06 + self.bob_offset) * 4
        sx = int(self.x - camera_x)
        sy = int(self.y + bob_y)

        if sx + self.radius < -20 or sx - self.radius > SCREEN_WIDTH + 20:
            return

        pygame.draw.circle(surface, AMMO_PICKUP_DARK, (sx + 1, sy + 1), self.radius)
        pygame.draw.circle(surface, AMMO_PICKUP_COLOR, (sx, sy), self.radius)

        pygame.draw.rect(surface, AMMO_PICKUP_DARK, (sx - 2, sy - 4, 4, 8))
        pygame.draw.rect(surface, AMMO_PICKUP_DARK, (sx - 4, sy - 2, 8, 4))
