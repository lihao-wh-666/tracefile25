# -*- coding: utf-8 -*-
"""
entities/enemies.py - 敌人模块

包含 PatrolEnemy 和 ChaseEnemy 敌人类。
"""

import math
import pygame

from config import (
    SCREEN_WIDTH,
    GRAVITY, MAX_FALL_SPEED,
    PATROL_ENEMY_WIDTH, PATROL_ENEMY_HEIGHT,
    PATROL_ENEMY_SPEED, PATROL_ENEMY_DETECTION_RANGE,
    PATROL_ENEMY_ALERT_SPEED_MULTIPLIER,
    PATROL_ENEMY_COLOR, PATROL_ENEMY_DARK, PATROL_ENEMY_LIGHT,
    PATROL_ENEMY_EYE, PATROL_ENEMY_PUPIL, PATROL_ENEMY_ALERT_COLOR,
    CHASE_ENEMY_WIDTH, CHASE_ENEMY_HEIGHT,
    CHASE_ENEMY_SPEED, CHASE_ENEMY_CHASE_RANGE,
    CHASE_ENEMY_GIVE_UP_RANGE,
    CHASE_ENEMY_COLOR, CHASE_ENEMY_DARK, CHASE_ENEMY_LIGHT,
    CHASE_ENEMY_EYE, CHASE_ENEMY_PUPIL, CHASE_ENEMY_GLOW_COLOR,
    ENEMY_KNOCKBACK_SPEED, ENEMY_KNOCKBACK_DURATION,
    PATROL_ENEMY_HP, CHASE_ENEMY_HP,
)
from entities.base import resolve_horizontal_collision, resolve_vertical_collision


class PatrolEnemy:
    """
    巡逻怪敌人，沿预设路径点巡逻，检测到玩家时进入警戒状态。

    核心特性:
    - 路径巡逻：在预设路径点之间自动移动
    - 折返/循环：可配置为折返模式或循环模式
    - 警戒状态：检测范围内发现玩家时加速并改变颜色
    - 重力与平台碰撞：与平台系统交互

    属性:
        x, y: 敌人左上角坐标
        width, height: 敌人尺寸
        vx, vy: 速度向量
        path_points: 巡逻路径点列表 [(x, y), ...]
        current_target: 当前目标路径点索引
        loop_mode: True=循环模式, False=折返模式
        direction: 巡逻方向 (1=正向, -1=反向，仅折返模式)
        alert: 是否处于警戒状态
        on_ground: 是否在地面上
        facing_right: 朝向
        anim_phase: 动画相位
    """

    def __init__(self, path_points, loop_mode=True):
        self.path_points = path_points
        self.loop_mode = loop_mode
        self.current_target = 1 if len(path_points) > 1 else 0
        self.direction = 1

        start_x, start_y = path_points[0]
        self.x = start_x
        self.y = start_y
        self.width = PATROL_ENEMY_WIDTH
        self.height = PATROL_ENEMY_HEIGHT

        self.vx = 0
        self.vy = 0

        self.alert = False
        self.on_ground = False
        self.facing_right = True
        self.anim_phase = 0.0
        self.alert_flash = 0

        self.hp = PATROL_ENEMY_HP
        self.max_hp = PATROL_ENEMY_HP
        self.knockback_timer = 0
        self.knockback_vx = 0
        self.hit_flash = 0

    def get_rect(self):
        """返回碰撞检测矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, damage, knockback_direction):
        self.hp -= damage
        self.knockback_timer = ENEMY_KNOCKBACK_DURATION
        self.knockback_vx = knockback_direction * ENEMY_KNOCKBACK_SPEED
        self.hit_flash = 6
        if self.hp <= 0:
            return True
        return False

    def _distance_to_player(self, player):
        ex = self.x + self.width / 2
        ey = self.y + self.height / 2
        px = player.x + player.width / 2
        py = player.y + player.height / 2
        return math.sqrt((ex - px) ** 2 + (ey - py) ** 2)

    def _advance_target(self):
        """移动到下一个路径点。"""
        if self.loop_mode:
            self.current_target = (self.current_target + 1) % len(self.path_points)
        else:
            next_idx = self.current_target + self.direction
            if next_idx >= len(self.path_points) or next_idx < 0:
                self.direction *= -1
                self.current_target += self.direction
            else:
                self.current_target = next_idx

    def update(self, platforms, player):
        """
        更新巡逻怪状态。

        Args:
            platforms: 平台列表
            player: 玩家对象
        """
        self.anim_phase += 0.15

        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.x += self.knockback_vx
            self.knockback_vx *= 0.85
            self.vy += GRAVITY
            if self.vy > MAX_FALL_SPEED:
                self.vy = MAX_FALL_SPEED
            self.y += self.vy
            resolve_horizontal_collision(self, platforms)
            resolve_vertical_collision(self, platforms)
            return

        dist = self._distance_to_player(player)
        was_alert = self.alert
        self.alert = dist < PATROL_ENEMY_DETECTION_RANGE

        if self.alert and not was_alert:
            self.alert_flash = 10
        if self.alert_flash > 0:
            self.alert_flash -= 1

        speed = PATROL_ENEMY_SPEED
        if self.alert:
            speed *= PATROL_ENEMY_ALERT_SPEED_MULTIPLIER

        target_x, target_y = self.path_points[self.current_target]
        dx = target_x - self.x
        dist_to_target = abs(dx)

        if dist_to_target < speed:
            self.x = target_x
            self._advance_target()
        else:
            self.vx = (1 if dx > 0 else -1) * speed
            self.x += self.vx

        if self.vx > 0.1:
            self.facing_right = True
        elif self.vx < -0.1:
            self.facing_right = False

        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED
        self.y += self.vy

        resolve_horizontal_collision(self, platforms)
        self.on_ground, _ = resolve_vertical_collision(self, platforms)

    def draw(self, surface, camera_x):
        """
        绘制巡逻怪。

        正常状态：红色方块造型，带黄色眼睛
        警戒状态：闪烁警告色，眼睛变亮
        """
        sx = int(self.x - camera_x)
        sy = int(self.y)

        if sx + self.width < -50 or sx > SCREEN_WIDTH + 50:
            return

        body_color = PATROL_ENEMY_COLOR
        dark_color = PATROL_ENEMY_DARK
        light_color = PATROL_ENEMY_LIGHT

        if self.alert and self.alert_flash > 0 and self.alert_flash % 4 < 2:
            body_color = PATROL_ENEMY_ALERT_COLOR
            dark_color = (200, 160, 0)
            light_color = (255, 230, 100)

        if self.hit_flash > 0 and self.hit_flash % 2 == 0:
            body_color = (255, 255, 255)
            dark_color = (200, 200, 200)
            light_color = (255, 255, 255)

        bounce = math.sin(self.anim_phase) * 2 if self.on_ground else 0
        draw_y = sy + bounce

        shadow_rect = pygame.Rect(
            sx + 2, draw_y + 2, self.width, self.height
        )
        pygame.draw.rect(surface, dark_color, shadow_rect, border_radius=4)

        body_rect = pygame.Rect(sx, draw_y, self.width, self.height)
        pygame.draw.rect(surface, body_color, body_rect, border_radius=4)

        highlight_rect = pygame.Rect(
            sx + 3, draw_y + 3, self.width - 6, self.height // 3
        )
        pygame.draw.rect(surface, light_color, highlight_rect, border_radius=2)

        spike_y = draw_y - 4
        spike_w = 6
        for i in range(3):
            sx_spike = sx + 4 + i * 10
            points = [
                (sx_spike, draw_y),
                (sx_spike + spike_w // 2, spike_y),
                (sx_spike + spike_w, draw_y),
            ]
            pygame.draw.polygon(surface, dark_color, points)

        eye_y = draw_y + self.height * 0.35
        if self.facing_right:
            ex1 = sx + self.width * 0.3
            ex2 = sx + self.width * 0.65
            pupil_offset = 2
        else:
            ex1 = sx + self.width * 0.35
            ex2 = sx + self.width * 0.7
            pupil_offset = -2

        eye_color = PATROL_ENEMY_EYE if not self.alert else (255, 255, 50)
        pupil_color = PATROL_ENEMY_PUPIL

        pygame.draw.circle(surface, eye_color, (int(ex1), int(eye_y)), 4)
        pygame.draw.circle(surface, eye_color, (int(ex2), int(eye_y)), 4)
        pygame.draw.circle(
            surface, pupil_color, (int(ex1 + pupil_offset), int(eye_y)), 2
        )
        pygame.draw.circle(
            surface, pupil_color, (int(ex2 + pupil_offset), int(eye_y)), 2
        )

        if self.alert:
            exclamation_y = draw_y - 18
            exclamation_x = sx + self.width // 2
            pygame.draw.rect(
                surface, PATROL_ENEMY_ALERT_COLOR,
                (exclamation_x - 2, exclamation_y - 6, 4, 8)
            )
            pygame.draw.circle(
                surface, PATROL_ENEMY_ALERT_COLOR,
                (exclamation_x, exclamation_y + 4), 2
            )

        if self.hp < self.max_hp:
            hp_bar_w = self.width
            hp_bar_h = 4
            hp_x = sx
            hp_y = draw_y - 8
            pygame.draw.rect(surface, (80, 0, 0), (hp_x, hp_y, hp_bar_w, hp_bar_h))
            fill_w = int(hp_bar_w * self.hp / self.max_hp)
            if fill_w > 0:
                pygame.draw.rect(surface, (255, 60, 60), (hp_x, hp_y, fill_w, hp_bar_h))


class ChaseEnemy:
    """
    追踪怪敌人，主动追踪范围内的玩家。

    核心特性:
    - 玩家检测：在追踪范围内检测到玩家后开始追踪
    - 动态追踪：根据玩家位置调整移动方向
    - 放弃追踪：玩家超出放弃范围后停止追踪
    - 悬浮动画：身体上下浮动的幽灵造型
    - 发光效果：追踪时发出紫色光晕

    属性:
        x, y: 敌人左上角坐标
        width, height: 敌人尺寸
        vx, vy: 速度向量
        chase_speed: 追踪速度
        chase_range: 开始追踪的范围
        give_up_range: 放弃追踪的范围
        chasing: 是否正在追踪
        facing_right: 朝向
        anim_phase: 动画相位
        glow_phase: 光晕动画相位
    """

    def __init__(self, x, y):
        from config import LEVEL_WIDTH
        self.x = x
        self.y = y
        self.width = CHASE_ENEMY_WIDTH
        self.height = CHASE_ENEMY_HEIGHT

        self.vx = 0
        self.vy = 0

        self.chase_speed = CHASE_ENEMY_SPEED
        self.chase_range = CHASE_ENEMY_CHASE_RANGE
        self.give_up_range = CHASE_ENEMY_GIVE_UP_RANGE

        self.chasing = False
        self.facing_right = True
        self.anim_phase = 0.0
        self.glow_phase = 0.0

        self._float_offset = 0
        self._base_y = y

        self.hp = CHASE_ENEMY_HP
        self.max_hp = CHASE_ENEMY_HP
        self.knockback_timer = 0
        self.knockback_vx = 0
        self.knockback_vy = 0
        self.hit_flash = 0
        self._level_width = LEVEL_WIDTH

    def get_rect(self):
        """返回碰撞检测矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, damage, knockback_direction):
        self.hp -= damage
        self.knockback_timer = ENEMY_KNOCKBACK_DURATION
        self.knockback_vx = knockback_direction * ENEMY_KNOCKBACK_SPEED
        self.knockback_vy = -3
        self.hit_flash = 6
        if self.hp <= 0:
            return True
        return False

    def _distance_to_player(self, player):
        """计算到玩家的距离。"""
        ex = self.x + self.width / 2
        ey = self.y + self.height / 2
        px = player.x + player.width / 2
        py = player.y + player.height / 2
        return math.sqrt((ex - px) ** 2 + (ey - py) ** 2)

    def update(self, player):
        """
        更新追踪怪状态。

        Args:
            player: 玩家对象
        """
        self.anim_phase += 0.1
        self.glow_phase += 0.08

        if self.hit_flash > 0:
            self.hit_flash -= 1

        self._float_offset = math.sin(self.anim_phase) * 4

        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.x += self.knockback_vx
            self.y += self.knockback_vy
            self.knockback_vx *= 0.85
            self.knockback_vy *= 0.85
            if self.x < 0:
                self.x = 0
            if self.x + self.width > self._level_width:
                self.x = self._level_width - self.width
            return

        dist = self._distance_to_player(player)

        if not self.chasing and dist < self.chase_range:
            self.chasing = True
        elif self.chasing and dist > self.give_up_range:
            self.chasing = False

        if self.chasing:
            ex = self.x + self.width / 2
            ey = self.y + self.height / 2
            px = player.x + player.width / 2
            py = player.y + player.height / 2

            dx = px - ex
            dy = py - ey
            dist_vec = math.sqrt(dx * dx + dy * dy)

            if dist_vec > 0:
                self.vx = (dx / dist_vec) * self.chase_speed
                self.vy = (dy / dist_vec) * self.chase_speed * 0.6

            self.x += self.vx
            self.y += self.vy

            if self.vx > 0.1:
                self.facing_right = True
            elif self.vx < -0.1:
                self.facing_right = False
        else:
            self.vx *= 0.95
            self.vy *= 0.95
            self.x += self.vx
            self.y += self.vy + math.sin(self.anim_phase * 0.5) * 0.3

        if self.x < 0:
            self.x = 0
        if self.x + self.width > self._level_width:
            self.x = self._level_width - self.width

    def draw(self, surface, camera_x):
        """
        绘制追踪怪。

        幽灵造型：半透明身体，波浪形底部，发光眼睛
        追踪状态：身体发光，眼睛变大，速度加快
        """
        sx = int(self.x - camera_x)
        sy = int(self.y + self._float_offset)

        if sx + self.width < -50 or sx > SCREEN_WIDTH + 50:
            return

        if self.chasing:
            glow_pulse = (math.sin(self.glow_phase) + 1) * 0.5
            glow_size = int(self.width * (1.5 + glow_pulse * 0.3))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            glow_alpha = int(60 + glow_pulse * 40)
            pygame.draw.circle(
                glow_surf,
                (*CHASE_ENEMY_GLOW_COLOR, glow_alpha),
                (glow_size, glow_size),
                glow_size,
            )
            surface.blit(
                glow_surf,
                (sx + self.width // 2 - glow_size, sy + self.height // 2 - glow_size),
            )

        body_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        body_color = CHASE_ENEMY_COLOR
        dark_color = CHASE_ENEMY_DARK
        light_color = CHASE_ENEMY_LIGHT

        if self.chasing:
            body_color = tuple(min(255, c + 30) for c in CHASE_ENEMY_COLOR)

        if self.hit_flash > 0 and self.hit_flash % 2 == 0:
            body_color = (255, 255, 255)
            dark_color = (200, 200, 200)
            light_color = (255, 255, 255)

        points = []
        wave_count = 4
        wave_amp = 3
        bottom_y = self.height - 4
        for i in range(wave_count + 1):
            wx = i * (self.width / wave_count)
            wy = bottom_y + math.sin(self.anim_phase + i * 0.8) * wave_amp
            points.append((wx, wy))

        points.append((self.width, 10))
        points.append((self.width * 0.7, 2))
        points.append((self.width * 0.5, 0))
        points.append((self.width * 0.3, 2))
        points.append((0, 10))

        pygame.draw.polygon(body_surf, (*dark_color, 180), points)

        inner_points = [(p[0] + 2, p[1] + 2) for p in points[:wave_count + 1]]
        inner_points.append((self.width - 4, 12))
        inner_points.append((self.width * 0.7 - 1, 4))
        inner_points.append((self.width * 0.5, 2))
        inner_points.append((self.width * 0.3 + 1, 4))
        inner_points.append((4, 12))

        pygame.draw.polygon(body_surf, (*body_color, 200), inner_points)

        highlight_rect = pygame.Rect(
            4, 6, self.width - 12, self.height // 4
        )
        pygame.draw.ellipse(body_surf, (*light_color, 150), highlight_rect)

        surface.blit(body_surf, (sx, sy))

        eye_y = sy + self.height * 0.35
        eye_size = 5 if not self.chasing else 7

        if self.facing_right:
            ex1 = sx + self.width * 0.3
            ex2 = sx + self.width * 0.65
            pupil_offset = 2
        else:
            ex1 = sx + self.width * 0.35
            ex2 = sx + self.width * 0.7
            pupil_offset = -2

        eye_color = CHASE_ENEMY_EYE
        pupil_color = CHASE_ENEMY_PUPIL

        if self.chasing:
            eye_glow = pygame.Surface((eye_size * 4, eye_size * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                eye_glow, (*CHASE_ENEMY_GLOW_COLOR, 100),
                (eye_size * 2, eye_size * 2), eye_size * 2
            )
            surface.blit(eye_glow, (int(ex1) - eye_size * 2, int(eye_y) - eye_size * 2))
            surface.blit(eye_glow, (int(ex2) - eye_size * 2, int(eye_y) - eye_size * 2))

        pygame.draw.circle(surface, eye_color, (int(ex1), int(eye_y)), eye_size)
        pygame.draw.circle(surface, eye_color, (int(ex2), int(eye_y)), eye_size)
        pygame.draw.circle(
            surface, pupil_color,
            (int(ex1 + pupil_offset), int(eye_y)), max(2, eye_size - 3)
        )
        pygame.draw.circle(
            surface, pupil_color,
            (int(ex2 + pupil_offset), int(eye_y)), max(2, eye_size - 3)
        )

        tail_x = sx - 8 if self.facing_right else sx + self.width + 8
        tail_dir = 1 if self.facing_right else -1
        for i in range(3):
            t_y = sy + self.height * 0.4 + i * 6
            t_size = 4 - i
            alpha = 150 - i * 40
            tail_surf = pygame.Surface((t_size * 2, t_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                tail_surf,
                (*CHASE_ENEMY_LIGHT, alpha),
                (t_size, t_size), t_size
            )
            tx = tail_x - i * 6 * tail_dir
            surface.blit(tail_surf, (tx - t_size, int(t_y) - t_size))

        if self.hp < self.max_hp:
            hp_bar_w = self.width
            hp_bar_h = 4
            hp_x = sx
            hp_y = int(sy) - 8
            pygame.draw.rect(surface, (80, 0, 0), (hp_x, hp_y, hp_bar_w, hp_bar_h))
            fill_w = int(hp_bar_w * self.hp / self.max_hp)
            if fill_w > 0:
                pygame.draw.rect(surface, (255, 60, 255), (hp_x, hp_y, fill_w, hp_bar_h))
