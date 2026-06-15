# -*- coding: utf-8 -*-
"""
core/particles.py - 粒子系统模块

负责游戏粒子效果的管理、更新和绘制。
"""

import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GRAVITY, FRICTION,
)


class ParticleManager:
    """
    粒子管理器。

    负责:
    - 粒子效果的创建（跳跃、落地、攻击、死亡等）
    - 粒子的物理更新
    - 粒子的生命周期管理
    - 粒子的绘制
    """

    def __init__(self, game):
        self.game = game

    def spawn_jump_dust(self, x, y, facing):
        """生成跳跃尘土粒子。"""
        from entities import Particle

        for _ in range(8):
            self.game.particles.append(
                Particle(
                    x,
                    y,
                    -facing * (2 + self.game.rng.random() * 3),
                    -self.game.rng.random() * 3,
                    (200, 200, 180),
                    15 + self.game.rng.randint(0, 10),
                )
            )

    def spawn_land_dust(self, x, y):
        """生成落地尘土粒子。"""
        from entities import Particle

        for _ in range(12):
            vx = (self.game.rng.random() - 0.5) * 6
            vy = -self.game.rng.random() * 2
            self.game.particles.append(
                Particle(
                    x, y, vx, vy,
                    (180, 180, 160),
                    20 + self.game.rng.randint(0, 15),
                )
            )

    def spawn_coin_sparkle(self, x, y):
        """生成金币收集闪光粒子。"""
        from entities import Particle

        for _ in range(15):
            angle = self.game.rng.random() * math.pi * 2
            speed = 1 + self.game.rng.random() * 4
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = self.game.rng.choice(
                [(255, 235, 59), (255, 202, 40), (255, 255, 150), (255, 183, 77)]
            )
            self.game.particles.append(
                Particle(
                    x, y, vx, vy,
                    color,
                    25 + self.game.rng.randint(0, 15),
                    size=self.game.rng.randint(2, 4),
                )
            )

    def spawn_death_effect(self, x, y, color=(255, 0, 0)):
        """生成死亡爆炸粒子效果。"""
        from entities import Particle

        for _ in range(30):
            angle = self.game.rng.random() * math.pi * 2
            speed = 2 + self.game.rng.random() * 6
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2
            c = (
                color[0],
                max(0, color[1] - self.game.rng.randint(0, 80)),
                max(0, color[2] - self.game.rng.randint(0, 80)),
            )
            self.game.particles.append(
                Particle(
                    x, y, vx, vy,
                    c,
                    40 + self.game.rng.randint(0, 30),
                    size=self.game.rng.randint(2, 5),
                )
            )

    def spawn_melee_slash(self, x, y, facing):
        """生成近战斩击特效粒子。"""
        from entities import Particle

        for _ in range(10):
            vx = facing * (3 + self.game.rng.random() * 4)
            vy = -2 + self.game.rng.random() * 4
            self.game.particles.append(
                Particle(
                    x + facing * 15, y,
                    vx, vy,
                    (255, 255, 255),
                    8 + self.game.rng.randint(0, 5),
                    size=2,
                )
            )

    def spawn_muzzle_flash(self, x, y, facing):
        """生成枪口火焰特效粒子。"""
        from entities import Particle

        for _ in range(8):
            angle = self.game.rng.uniform(-0.5, 0.5) * (math.pi / 4)
            if facing < 0:
                angle = math.pi - angle
            speed = 2 + self.game.rng.random() * 5
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = self.game.rng.choice(
                [(255, 200, 50), (255, 150, 0), (255, 255, 200)]
            )
            self.game.particles.append(
                Particle(
                    x, y,
                    vx, vy,
                    color,
                    6 + self.game.rng.randint(0, 4),
                    size=self.game.rng.randint(2, 3),
                )
            )

    def spawn_bullet_impact(self, x, y, normal=0):
        """生成子弹撞击粒子效果。"""
        from entities import Particle

        for _ in range(12):
            vx = normal * (1 + self.game.rng.random() * 3) + (self.game.rng.random() - 0.5) * 4
            vy = -1 + self.game.rng.random() * 3
            color = self.game.rng.choice(
                [(255, 255, 255), (200, 200, 200), (150, 150, 150)]
            )
            self.game.particles.append(
                Particle(
                    x, y,
                    vx, vy,
                    color,
                    10 + self.game.rng.randint(0, 10),
                    size=self.game.rng.randint(1, 3),
                )
            )

    def update_particles(self, particles, platforms, ground_y=None):
        """
        更新所有粒子的物理和生命周期。

        Args:
            particles: 粒子列表
            platforms: 平台列表，用于地面碰撞检测
            ground_y: 可选的地面 Y 坐标
        """
        alive = []
        for p in particles:
            p.life -= 1
            if p.life <= 0:
                continue

            p.vx *= FRICTION
            p.vy += GRAVITY * 0.3
            p.x += p.vx
            p.y += p.vy

            if ground_y is not None and p.y > ground_y:
                p.y = ground_y
                p.vy *= -0.3
                p.vx *= 0.7
                if abs(p.vy) < 0.5:
                    p.vy = 0

            p.y = min(p.y, SCREEN_HEIGHT - 10)
            p.x = max(0, min(p.x, SCREEN_WIDTH * 4))

            alive.append(p)

        return alive

    def draw_particles(self, screen, particles, camera_x):
        """绘制所有可见的粒子。"""
        for p in particles:
            screen_x = int(p.x - camera_x)
            if -10 < screen_x < SCREEN_WIDTH + 10 and 0 < p.y < SCREEN_HEIGHT:
                alpha = int(min(255, p.life * 12))
                if alpha < 1:
                    continue
                color = (
                    min(255, p.color[0]),
                    min(255, p.color[1]),
                    min(255, p.color[2]),
                )
                size = getattr(p, "size", 3)
                pygame.draw.circle(
                    screen,
                    color,
                    (screen_x, int(p.y)),
                    max(1, int(size * (alpha / 255))),
                )
