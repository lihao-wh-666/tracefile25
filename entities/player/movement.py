# -*- coding: utf-8 -*-
"""
entities/player/movement.py - 玩家移动模块

提供玩家角色的移动、跳跃、攀爬和碰撞解析功能。
作为 Mixin 类使用，与 PlayerBase 和其他 Mixin 组合。
"""

import math
import pygame

from config import (
    GRAVITY, MAX_FALL_SPEED, ACCELERATION, FRICTION,
    MOVE_SPEED,
    JUMP_BUFFER_FRAMES, COYOTE_TIME_FRAMES, SHORT_JUMP_MULTIPLIER,
    SHORT_JUMP_THRESHOLD,
    SQUASH_INTERPOLATION, SQUASH_ON_JUMP, SQUASH_ON_FALL,
    SQUASH_ON_LAND, SQUASH_NORMAL, SQUASH_ON_CLIMB,
    RUN_ANIM_SPEED, BLINK_INTERVAL, BLINK_DURATION,
    LEVEL_WIDTH, FALL_RESPAWN_Y,
    MAX_JUMP_COUNT, MULTI_JUMP_FORCE, MULTI_JUMP_INTERVAL_FRAMES,
    CLIMB_SPEED,
)

from ..base import resolve_horizontal_collision, resolve_vertical_collision


class PlayerMovementMixin:
    """
    玩家移动 Mixin 类。

    提供以下功能:
    - 水平移动（加速度 + 摩擦力）
    - 跳跃系统（跳跃缓冲 + 土狼时间 + 多段跳 + 短跳）
    - 梯子攀爬系统
    - 碰撞解析（水平/垂直分离）
    - 边界限制和掉落重生
    """

    def update(self, keys, platforms, ladders=None):
        """
        更新玩家状态（每帧调用）。

        处理流程:
        1. 更新多段跳冷却计时器
        2. 检测梯子交互，处理攀爬进入/退出
        3. 攀爬模式下处理上下移动和脱离
        4. 读取水平方向输入，应用加速度/摩擦力
        5. 读取跳跃输入，管理跳跃缓冲
        6. 更新土狼时间
        7. 执行跳跃（地面跳 / 空中多段跳）
        8. 应用短跳逻辑和重力
        9. 更新挤压拉伸动画目标
        10. 先水平移动 + 碰撞，再垂直移动 + 碰撞
        11. 边界限制 + 掉落重生
        12. 眨眼计时器

        Args:
            keys: pygame.key.get_pressed() 返回的按键状态序列
            platforms: 所有平台对象列表
            ladders: 所有梯子对象列表（可选）
        """
        if ladders is None:
            ladders = []

        self.update_combat()

        if self.multi_jump_cooldown > 0:
            self.multi_jump_cooldown -= 1

        climb_up = keys[pygame.K_UP] or keys[pygame.K_w]
        climb_down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        climb_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        climb_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if not self.climbing:
            self._try_enter_ladder(ladders, climb_up, climb_down)

        if self.climbing:
            self._update_climbing(climb_up, climb_down, climb_left, climb_right, platforms, ladders)
        else:
            self._update_normal(keys, platforms, climb_up)

        if self.x < 0:
            self.x = 0
            self.vx = 0
        if self.x + self.width > LEVEL_WIDTH:
            self.x = LEVEL_WIDTH - self.width
            self.vx = 0

        if self.y > FALL_RESPAWN_Y:
            self.died = True
            if self.on_death:
                self.on_death()
            self.x = self.start_x
            self.y = 0
            self.vx = 0
            self.vy = 0
            self.climbing = False
            self.current_ladder = None
            self.jump_count = 0

        self.blink_timer += 1
        if self.blink_timer > BLINK_INTERVAL:
            self.eye_blink = BLINK_DURATION
            self.blink_timer = 0
        if self.eye_blink > 0:
            self.eye_blink -= 1

    def _try_enter_ladder(self, ladders, climb_up, climb_down):
        """尝试进入梯子攀爬状态。"""
        player_rect = self.get_rect()
        cx = self.x + self.width / 2
        for ladder in ladders:
            on_top = (
                abs((self.y + self.height) - ladder.y) <= 2
                and cx >= ladder.x
                and cx <= ladder.x + ladder.width
            )
            if (player_rect.colliderect(ladder.rect) or on_top) and (climb_up or climb_down):
                self.climbing = True
                self.current_ladder = ladder
                ladder_cx = ladder.x + ladder.width / 2
                self.x = ladder_cx - self.width / 2
                self.vx = 0
                self.vy = 0
                self.jump_count = 0
                self.coyote_time = 0
                self.jump_buffer = 0
                self.target_squash = SQUASH_ON_CLIMB
                if on_top and climb_down:
                    self.y = ladder.y
                break

    def _update_climbing(self, climb_up, climb_down, climb_left, climb_right, platforms, ladders):
        """更新攀爬状态下的玩家行为。"""
        want_jump = pygame.key.get_pressed()[pygame.K_SPACE]

        if climb_left or climb_right:
            self.climbing = False
            self.current_ladder = None
            if climb_left:
                self.vx = -MOVE_SPEED * 0.8
                self.facing_right = False
            else:
                self.vx = MOVE_SPEED * 0.8
                self.facing_right = True
            self.on_ground = False
            return

        if want_jump and not self.jump_pressed:
            self.climbing = False
            self.current_ladder = None
            self.vy = JUMP_FORCE
            self.jump_count = 1
            self.on_ground = False
            self.jump_pressed = True
            self.target_squash = SQUASH_ON_JUMP
            if self.on_jump:
                self.on_jump()
            return

        self.vy = 0
        self.vx = 0

        if climb_up:
            self.vy = -CLIMB_SPEED
            self.climb_anim += 0.15
        elif climb_down:
            self.vy = CLIMB_SPEED
            self.climb_anim += 0.15

        self.y += self.vy

        ladder = self.current_ladder
        if ladder is not None:
            if self.y < ladder.y - self.height:
                self.y = ladder.y - self.height
                self.climbing = False
                self.current_ladder = None
                self.on_ground = False
                self.vy = 0
                self._resolve_vertical(platforms, False)
                return

        if self.current_ladder is not None:
            filtered = [p for p in platforms if not self.current_ladder.rect.colliderect(p.rect)]
        else:
            filtered = platforms

        self._resolve_vertical(filtered, self.on_ground)

        player_rect = self.get_rect()
        still_on_ladder = False
        if self.current_ladder is not None:
            if player_rect.colliderect(self.current_ladder.rect):
                still_on_ladder = True

        if not still_on_ladder:
            self.climbing = False
            self.current_ladder = None
            self._resolve_vertical(platforms, self.on_ground)

        if not climb_up and not climb_down:
            self.climb_anim += 0.02

        self.target_squash = SQUASH_ON_CLIMB

    def _update_normal(self, keys, platforms, climb_up):
        """
        更新正常（非攀爬）状态。

        包含完整的水平移动、多段跳、重力、碰撞逻辑。
        """
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1
            self.facing_right = True

        if move_x != 0:
            self.vx += move_x * ACCELERATION
            self.vx = max(-MOVE_SPEED, min(MOVE_SPEED, self.vx))
        else:
            self.vx *= FRICTION
            if abs(self.vx) < 0.1:
                self.vx = 0

        if move_x != 0 and self.on_ground:
            self.run_anim += RUN_ANIM_SPEED
        elif self.on_ground:
            self.run_anim = 0

        want_jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        if want_jump:
            if not self.jump_pressed:
                self.jump_buffer = JUMP_BUFFER_FRAMES
            self.jump_pressed = True
        else:
            self.jump_pressed = False

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

        if self.on_ground:
            self.coyote_time = COYOTE_TIME_FRAMES
            self.jump_count = 0
        else:
            self.coyote_time = max(0, self.coyote_time - 1)

        if self.jump_buffer > 0 and self.coyote_time > 0 and self.jump_count == 0:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self.coyote_time = 0
            self.jump_buffer = 0
            self.jump_count = 1
            self.target_squash = SQUASH_ON_JUMP
            if self.on_jump:
                self.on_jump()
        elif self.jump_buffer > 0 and not self.on_ground and self.jump_count > 0:
            if (self.jump_count < MAX_JUMP_COUNT
                    and self.multi_jump_cooldown <= 0):
                self.vy = MULTI_JUMP_FORCE
                self.jump_buffer = 0
                self.jump_count += 1
                self.multi_jump_cooldown = MULTI_JUMP_INTERVAL_FRAMES
                self.target_squash = SQUASH_ON_JUMP
                if self.on_double_jump:
                    self.on_double_jump()

        if not want_jump and self.vy < SHORT_JUMP_THRESHOLD:
            self.vy *= SHORT_JUMP_MULTIPLIER

        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        if self.vy > 0 and not self.on_ground:
            self.target_squash = SQUASH_ON_FALL
        elif self.on_ground:
            self.target_squash = SQUASH_NORMAL

        self.squash_stretch += (
            self.target_squash - self.squash_stretch
        ) * SQUASH_INTERPOLATION

        self.x += self.vx
        self._resolve_horizontal(platforms)

        self.y += self.vy
        was_on_ground = self.on_ground
        self.on_ground = False
        self._resolve_vertical(platforms, was_on_ground)

    def _resolve_horizontal(self, platforms):
        """
        水平方向碰撞解析。

        简单 AABB 碰撞：根据移动方向将玩家推回平台边界，并清零水平速度。
        每次修改位置后重新获取碰撞矩形，避免连续重叠问题。

        Args:
            platforms: 所有平台对象列表
        """
        resolve_horizontal_collision(self, platforms)

    def _resolve_vertical(self, platforms, was_on_ground):
        """
        垂直方向碰撞解析。

        向下碰撞（落地）：吸附到平台顶部，触发落地挤压效果，标记着地
        向上碰撞（撞头）：吸附到平台底部

        Args:
            platforms: 所有平台对象列表
            was_on_ground: 上一帧是否着地（用于判断是否触发新落地特效）
        """
        on_ground, landed = resolve_vertical_collision(self, platforms, was_on_ground)
        self.on_ground = on_ground
        if landed:
            self.target_squash = SQUASH_ON_LAND
            if self.on_land:
                self.on_land()
