# -*- coding: utf-8 -*-
"""
entities/combat.py - 战斗相关实体模块

包含 Bullet 等战斗相关实体。
"""

import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, LEVEL_WIDTH,
    RANGED_DAMAGE,
    RANGED_GRAVITY, RANGED_MAX_DISTANCE,
    RANGED_PROJECTILE_SIZE,
    RANGED_COLOR, RANGED_COLOR_TRAIL,
)


class Bullet:
    """
    远程射击弹丸类，模拟弹道物理飞行。

    属性:
        x, y: 弹丸中心坐标
        vx, vy: 弹丸速度向量
        damage: 伤害值
        distance_traveled: 已飞行距离
        alive: 弹丸是否存活
        trail: 弹道轨迹点列表 [(x, y), ...]
    """

    def __init__(self, x, y, vx, vy, damage=RANGED_DAMAGE):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.distance_traveled = 0.0
        self.alive = True
        self.trail = []
        self.size = RANGED_PROJECTILE_SIZE

    def get_rect(self):
        return pygame.Rect(
            self.x - self.size,
            self.y - self.size,
            self.size * 2,
            self.size * 2,
        )

    def update(self, platforms):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)

        old_x = self.x
        old_y = self.y

        self.x += self.vx
        self.vy += RANGED_GRAVITY
        self.y += self.vy

        dx = self.x - old_x
        dy = self.y - old_y
        self.distance_traveled += math.sqrt(dx * dx + dy * dy)

        if self.distance_traveled > RANGED_MAX_DISTANCE:
            self.alive = False
            return

        if self.x < -50 or self.x > LEVEL_WIDTH + 50:
            self.alive = False
            return
        if self.y > SCREEN_HEIGHT + 50 or self.y < -200:
            self.alive = False
            return

        bullet_rect = self.get_rect()
        for plat in platforms:
            if bullet_rect.colliderect(plat.rect):
                self.alive = False
                return

    def draw(self, surface, camera_x):
        if not self.alive:
            return

        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) if self.trail else 1.0
            tsx = int(tx - camera_x)
            tsy = int(ty)
            trail_size = max(1, int(self.size * alpha * 0.6))
            if 0 <= tsx <= SCREEN_WIDTH and 0 <= tsy <= SCREEN_HEIGHT:
                pygame.draw.circle(surface, RANGED_COLOR_TRAIL, (tsx, tsy), trail_size)

        sx = int(self.x - camera_x)
        sy = int(self.y)

        if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
            glow_surf = pygame.Surface((self.size * 6, self.size * 6), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf,
                (*RANGED_COLOR, 80),
                (self.size * 3, self.size * 3),
                self.size * 3,
            )
            surface.blit(glow_surf, (sx - self.size * 3, sy - self.size * 3))
            pygame.draw.circle(surface, RANGED_COLOR, (sx, sy), self.size)
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(1, self.size - 2))
