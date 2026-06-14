# -*- coding: utf-8 -*-
"""
entities.py - 游戏实体模块

定义游戏中的所有可交互对象，包括：
- Particle: 粒子效果（落地烟尘、收集特效等）
- Coin: 可收集金币
- Platform: 平台（地面和浮动平台）
- Player: 玩家角色
"""

import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, JUMP_FORCE, MOVE_SPEED,
    MAX_FALL_SPEED, ACCELERATION, FRICTION,
    PLAYER_BODY, PLAYER_DARK, PLAYER_LIGHT, PLAYER_EYE, PLAYER_PUPIL,
    COIN_COLOR, COIN_DARK, COIN_COLLECT_ANIM, COIN_BOB_AMPLITUDE,
    GROUND_COLOR, DIRT_COLOR, PLATFORM_COLOR, PLATFORM_TOP_COLOR,
    PLATFORM_HIGHLIGHT, GRASS_DARK, GRASS_LIGHT, GRASS_TUFT_DARK,
    GRASS_TUFT_LIGHT, PLATFORM_GRASS_SEED,
    JUMP_BUFFER_FRAMES, COYOTE_TIME_FRAMES, SHORT_JUMP_MULTIPLIER,
    SHORT_JUMP_THRESHOLD,
    SQUASH_INTERPOLATION, SQUASH_ON_JUMP, SQUASH_ON_FALL,
    SQUASH_ON_LAND, SQUASH_NORMAL, SQUASH_ON_CLIMB,
    RUN_ANIM_SPEED, BLINK_INTERVAL, BLINK_DURATION,
    LEVEL_WIDTH, FALL_RESPAWN_Y,
    MAX_JUMP_COUNT, MULTI_JUMP_FORCE, MULTI_JUMP_INTERVAL_FRAMES,
    LADDER_WIDTH, LADDER_COLOR, LADDER_RUNG_COLOR,
    LADDER_RUNG_SPACING, CLIMB_SPEED,
    PORTAL_WIDTH, PORTAL_HEIGHT,
    PORTAL_COLOR_INNER, PORTAL_COLOR_OUTER, PORTAL_COLOR_GLOW,
    PORTAL_ACTIVATION_COINS, PORTAL_COOLDOWN_FRAMES,
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


class Player:
    """
    玩家角色类，处理输入、物理运动、碰撞和动画。

    核心特性:
    - 物理：加速度 + 摩擦力的平滑移动
    - 跳跃：跳跃缓冲 + 土狼时间（增加操作容错）
    - 多段跳：空中连续跳跃，可配置最大次数和力度
    - 攀爬：与梯子交互的上下攀爬控制
    - 短跳：松开跳跃键时减速（可控制跳跃高度）
    - 视觉：挤压拉伸、跑步动画、攀爬动画、随机眨眼
    - 碰撞：水平/垂直分离解析，防止穿墙
    - 音频回调：跳跃、落地、多段跳、死亡事件触发
    """

    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y

        self.x = x
        self.y = y
        self.width = 28
        self.height = 38

        self.vx = 0
        self.vy = 0

        self.on_ground = False
        self.facing_right = True

        self.jump_pressed = False
        self.jump_buffer = 0
        self.coyote_time = 0

        self.jump_count = 0
        self.multi_jump_cooldown = 0

        self.climbing = False
        self.current_ladder = None
        self.climb_anim = 0

        self.squash_stretch = 1.0
        self.target_squash = 1.0

        self.run_anim = 0
        self.eye_blink = 0
        self.blink_timer = 0
        self.died = False

        self.on_jump = None
        self.on_double_jump = None
        self.on_land = None
        self.on_death = None

    def get_rect(self):
        """返回玩家碰撞矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

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
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.x = plat.rect.left - self.width
                elif self.vx < 0:
                    self.x = plat.rect.right
                self.vx = 0
                rect = self.get_rect()

    def _resolve_vertical(self, platforms, was_on_ground):
        """
        垂直方向碰撞解析。
        
        向下碰撞（落地）：吸附到平台顶部，触发落地挤压效果，标记着地
        向上碰撞（撞头）：吸附到平台底部
        
        Args:
            platforms: 所有平台对象列表
            was_on_ground: 上一帧是否着地（用于判断是否触发新落地特效）
        """
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vy >= 0:
                    self.y = plat.rect.top - self.height
                    self.vy = 0
                    if not was_on_ground and not self.on_ground:
                        self.target_squash = SQUASH_ON_LAND
                        if self.on_land:
                            self.on_land()
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = plat.rect.bottom
                    self.vy = 0
                rect = self.get_rect()

    def draw(self, surface, camera_x):
        """
        绘制玩家角色。

        包含以下视觉层次：
        1. 阴影（偏移深色背景）
        2. 身体主色 + 顶部高光
        3. 脚部（仅跑步时）
        4. 手臂（攀爬时显示交替摆臂动画）
        5. 眼睛（含眨眼动画和朝向偏移）

        整体应用挤压拉伸变换模拟卡通弹性。
        攀爬状态下身体会有微妙的左右摆动。

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移量
        """
        sx = self.x - camera_x
        sy = self.y

        if self.climbing:
            self.squash_stretch += (
                SQUASH_ON_CLIMB - self.squash_stretch
            ) * SQUASH_INTERPOLATION

        stretch_x = 1 / self.squash_stretch
        stretch_y = self.squash_stretch

        cx = sx + self.width / 2
        cy = sy + self.height / 2

        if self.climbing:
            sway = math.sin(self.climb_anim) * 2
            cx += sway

        draw_w = self.width * stretch_x
        draw_h = self.height * stretch_y

        body_rect = pygame.Rect(
            cx - draw_w / 2,
            cy - draw_h / 2 + 2 * (1 - stretch_y),
            draw_w,
            draw_h,
        )

        shadow_rect = pygame.Rect(
            body_rect.x + 2,
            body_rect.y + 2,
            body_rect.width,
            body_rect.height,
        )
        pygame.draw.rect(surface, PLAYER_DARK, shadow_rect, border_radius=5)
        pygame.draw.rect(surface, PLAYER_BODY, body_rect, border_radius=5)

        highlight_rect = pygame.Rect(
            body_rect.x + 3,
            body_rect.y + 3,
            body_rect.width - 6,
            body_rect.height / 3,
        )
        pygame.draw.rect(surface, PLAYER_LIGHT, highlight_rect, border_radius=3)

        if self.climbing:
            arm_swing = math.sin(self.climb_anim * 2) * 6
            arm_y_top = body_rect.y + body_rect.height * 0.3
            arm_y_bot = body_rect.y + body_rect.height * 0.7
            left_arm_x = body_rect.centerx - draw_w / 2 - 3
            right_arm_x = body_rect.centerx + draw_w / 2 + 3
            pygame.draw.line(
                surface,
                PLAYER_DARK,
                (int(left_arm_x), int(arm_y_top - arm_swing)),
                (int(left_arm_x), int(arm_y_bot - arm_swing)),
                3,
            )
            pygame.draw.line(
                surface,
                PLAYER_DARK,
                (int(right_arm_x), int(arm_y_top + arm_swing)),
                (int(right_arm_x), int(arm_y_bot + arm_swing)),
                3,
            )
        elif self.on_ground and abs(self.vx) > 0.5:
            leg_offset = math.sin(self.run_anim) * 3
            foot_y = body_rect.bottom
            foot_lx = body_rect.centerx - 5 + leg_offset
            foot_rx = body_rect.centerx + 5 - leg_offset
            pygame.draw.circle(surface, PLAYER_DARK, (int(foot_lx), int(foot_y)), 3)
            pygame.draw.circle(surface, PLAYER_DARK, (int(foot_rx), int(foot_y)), 3)

        eye_y = body_rect.y + body_rect.height * 0.3

        if self.eye_blink > 0:
            blink_y = int(eye_y)
            if self.facing_right:
                pygame.draw.line(
                    surface,
                    PLAYER_PUPIL,
                    (int(body_rect.centerx + 3), blink_y),
                    (int(body_rect.centerx + 9), blink_y),
                    2,
                )
                pygame.draw.line(
                    surface,
                    PLAYER_PUPIL,
                    (int(body_rect.centerx - 5), blink_y),
                    (int(body_rect.centerx + 1), blink_y),
                    2,
                )
            else:
                pygame.draw.line(
                    surface,
                    PLAYER_PUPIL,
                    (int(body_rect.centerx - 9), blink_y),
                    (int(body_rect.centerx - 3), blink_y),
                    2,
                )
                pygame.draw.line(
                    surface,
                    PLAYER_PUPIL,
                    (int(body_rect.centerx - 1), blink_y),
                    (int(body_rect.centerx + 5), blink_y),
                    2,
                )
        else:
            look_offset = 2 if self.facing_right else -2
            if self.facing_right:
                ex1 = body_rect.centerx - 4
                ex2 = body_rect.centerx + 4
            else:
                ex1 = body_rect.centerx - 6
                ex2 = body_rect.centerx + 2

            pygame.draw.circle(surface, PLAYER_EYE, (int(ex1), int(eye_y)), 4)
            pygame.draw.circle(surface, PLAYER_EYE, (int(ex2), int(eye_y)), 4)
            pygame.draw.circle(
                surface, PLAYER_PUPIL, (int(ex1 + look_offset), int(eye_y)), 2
            )
            pygame.draw.circle(
                surface, PLAYER_PUPIL, (int(ex2 + look_offset), int(eye_y)), 2
            )


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
