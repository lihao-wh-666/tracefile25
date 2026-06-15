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
    PLAYER_SKIN, PLAYER_SKIN_DARK, PLAYER_SKIN_SHADOW,
    PLAYER_HAT, PLAYER_HAT_DARK, PLAYER_HAT_BAND, PLAYER_HAT_BRIM,
    PLAYER_SHIRT, PLAYER_SHIRT_DARK, PLAYER_SHIRT_LIGHT,
    PLAYER_PANTS, PLAYER_PANTS_DARK,
    PLAYER_SHOES, PLAYER_SHOES_LIGHT,
    PLAYER_BELT, PLAYER_BELT_BUCKLE,
    PLAYER_GLOVE, PLAYER_GLOVE_DARK,
    PLAYER_HAIR, PLAYER_HAIR_DARK, PLAYER_CHEEK,
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
    MELEE_COOLDOWN_FRAMES, MELEE_RANGE, MELEE_ARC_HALF, MELEE_DAMAGE,
    MELEE_DURATION_FRAMES, MELEE_HIT_FRAME, MELEE_COLOR, MELEE_COLOR_TIP,
    RANGED_COOLDOWN_FRAMES, RANGED_AMMO_MAX, RANGED_AMMO_INITIAL,
    RANGED_PROJECTILE_SPEED, RANGED_PROJECTILE_SIZE, RANGED_DAMAGE,
    RANGED_GRAVITY, RANGED_MAX_DISTANCE, RANGED_RELOAD_FRAMES,
    RANGED_COLOR, RANGED_COLOR_TRAIL,
    RANGED_AMMO_PICKUP_AMOUNT, AMMO_PICKUP_COLOR, AMMO_PICKUP_DARK,
    ENEMY_KNOCKBACK_SPEED, ENEMY_KNOCKBACK_DURATION,
    PATROL_ENEMY_HP, CHASE_ENEMY_HP,
    KNIFE_BLADE_COLOR, KNIFE_BLADE_HIGHLIGHT, KNIFE_BLADE_SHADOW,
    KNIFE_HANDLE_COLOR, KNIFE_HANDLE_WRAP,
    KNIFE_GUARD_COLOR, KNIFE_GUARD_DARK, KNIFE_LENGTH,
    KNIFE_HANDLE_LENGTH, KNIFE_BLADE_WIDTH,
    KNIFE_SWING_GLOW_COLOR, KNIFE_SLASH_TRAIL_COLOR,
    KNIFE_IMPACT_FLASH_COLOR,
    GUN_BODY_COLOR, GUN_BODY_HIGHLIGHT, GUN_BODY_SHADOW,
    GUN_BARREL_COLOR, GUN_BARREL_HIGHLIGHT,
    GUN_GRIP_COLOR, GUN_GRIP_WRAP, GUN_TRIGGER_COLOR,
    GUN_BODY_LENGTH, GUN_BARREL_LENGTH, GUN_BODY_HEIGHT,
    GUN_RECOIL_FRAMES, GUN_RECOIL_DISTANCE,
    MUZZLE_FLASH_COLOR, MUZZLE_FLASH_OUTER,
    MUZZLE_FLASH_DURATION, MUZZLE_FLASH_SIZE,
    CASING_COLOR, CASING_EJECT_DISTANCE,
    MELEE_SLASH_GLOW_RADIUS, MELEE_SLASH_TRAIL_COUNT,
    MELEE_IMPACT_RING_RADIUS, MELEE_IMPACT_RING_FRAMES,
    MELEE_SCREEN_SHAKE_FRAMES, MELEE_SCREEN_SHAKE_INTENSITY,
    MELEE_SLASH_ARC_COLOR, MELEE_SLASH_ARC_WIDTH,
    MELEE_SLASH_SPARK_COUNT,
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

        self.melee_cooldown = 0
        self.melee_timer = 0
        self.melee_active = False
        self.melee_hit_done = False
        self.melee_angle = 0.0

        self.ranged_cooldown = 0
        self.ammo = RANGED_AMMO_INITIAL
        self.reloading = False
        self.reload_timer = 0

        self.on_melee_swing = None
        self.on_ranged_shot = None
        self.on_reload = None
        self.on_ammo_pickup = None

        self.ranged_shot_timer = 0
        self.muzzle_flash_timer = 0

        self.weapon_state = "none"

    def get_rect(self):
        """返回玩家碰撞矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def start_melee(self):
        if self.melee_cooldown > 0 or self.melee_active:
            return False
        self.melee_active = True
        self.melee_timer = MELEE_DURATION_FRAMES
        self.melee_cooldown = MELEE_COOLDOWN_FRAMES
        self.melee_hit_done = False
        self.melee_angle = -MELEE_ARC_HALF
        self.weapon_state = "knife"
        if self.on_melee_swing:
            self.on_melee_swing()
        return True

    def start_ranged_shot(self):
        if self.ranged_cooldown > 0 or self.reloading:
            return None
        if self.ammo <= 0:
            return None
        self.ammo -= 1
        self.ranged_cooldown = RANGED_COOLDOWN_FRAMES

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        direction = 1 if self.facing_right else -1
        vx = RANGED_PROJECTILE_SPEED * direction
        vy = -1.0

        self.weapon_state = "gun"

        if self.on_ranged_shot:
            self.on_ranged_shot()

        self.ranged_shot_timer = GUN_RECOIL_FRAMES
        self.muzzle_flash_timer = MUZZLE_FLASH_DURATION

        return Bullet(cx + direction * 15, cy, vx, vy)

    def start_reload(self):
        if self.reloading or self.ammo >= RANGED_AMMO_MAX:
            return False
        self.reloading = True
        self.reload_timer = RANGED_RELOAD_FRAMES
        self.weapon_state = "gun"
        if self.on_reload:
            self.on_reload()
        return True

    def get_melee_hitbox(self):
        if not self.melee_active:
            return None
        progress = 1.0 - self.melee_timer / MELEE_DURATION_FRAMES
        current_angle = -MELEE_ARC_HALF + progress * MELEE_ARC_HALF * 2
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        direction = 1 if self.facing_right else -1
        base_angle = 0 if self.facing_right else math.pi
        rad = math.radians(current_angle) * direction + base_angle
        hit_x = cx + math.cos(rad) * MELEE_RANGE
        hit_y = cy + math.sin(rad) * MELEE_RANGE
        return pygame.Rect(hit_x - 12, hit_y - 12, 24, 24)

    def update_combat(self):
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1

        if self.melee_active:
            self.melee_timer -= 1
            progress = 1.0 - self.melee_timer / MELEE_DURATION_FRAMES
            self.melee_angle = -MELEE_ARC_HALF + progress * MELEE_ARC_HALF * 2
            if self.melee_timer <= 0:
                self.melee_active = False
                self.melee_hit_done = False

        if self.ranged_cooldown > 0:
            self.ranged_cooldown -= 1

        if self.ranged_shot_timer > 0:
            self.ranged_shot_timer -= 1
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= 1

        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo = RANGED_AMMO_MAX
                self.reloading = False

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
        绘制玩家角色（像素风格冒险者）。

        角色结构（从上到下）：
        1. 帽子（红色棒球帽）
        2. 头发（两侧棕色）
        3. 脸部（肤色，带眼睛、脸颊）
        4. 身体（蓝色衬衫 + 棕色腰带）
        5. 手臂（持武器）
        6. 腿（深蓝色裤子 + 棕色鞋子）

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

        direction = 1 if self.facing_right else -1

        head_y = sy + 8
        head_r = 7
        head_cx = cx

        neck_y = head_y + head_r + 2

        body_top = neck_y + 3
        body_bottom = sy + self.height - 10
        body_left = cx - 9
        body_right = cx + 9
        body_w = body_right - body_left

        belt_y = body_top + 11
        belt_h = 3

        pants_top = belt_y + belt_h
        pants_bottom = sy + self.height - 6

        shoe_top = pants_bottom
        shoe_bottom = sy + self.height

        if self.on_ground and abs(self.vx) > 0.5:
            leg_swing = math.sin(self.run_anim) * 4
            leg1_off = leg_swing
            leg2_off = -leg_swing
        else:
            leg1_off = 0
            leg2_off = 0

        if not self.on_ground and self.vy < 0:
            leg1_off = -1
            leg2_off = 2

        left_leg_x = cx - 4 + leg1_off * 0.5
        right_leg_x = cx + 4 + leg2_off * 0.5

        arm_shoulder_y = body_top + 4
        front_arm_x = body_right + 2
        back_arm_x = body_left - 2

        front_arm_offset_x = 0
        back_arm_offset_x = 0

        if self.climbing:
            climb_arm = math.sin(self.climb_anim * 2) * 5
            front_arm_y = arm_shoulder_y + climb_arm
            back_arm_y = arm_shoulder_y - climb_arm
        else:
            front_arm_y = arm_shoulder_y
            back_arm_y = arm_shoulder_y
            if self.on_ground and abs(self.vx) > 0.5:
                arm_swing_y = math.sin(self.run_anim + math.pi) * 3
                arm_swing_x = math.sin(self.run_anim + math.pi) * 2
                front_arm_y += arm_swing_y
                front_arm_offset_x = -arm_swing_x * direction
                back_arm_y -= arm_swing_y
                back_arm_offset_x = arm_swing_x * direction

        self._draw_back_arm(surface, back_arm_x + back_arm_offset_x, back_arm_y, direction)

        self._draw_legs(surface, left_leg_x, right_leg_x, pants_top, pants_bottom, shoe_top, shoe_bottom)

        self._draw_body(surface, body_left, body_right, body_top, body_bottom, belt_y, belt_h, cx)

        self._draw_head(surface, head_cx, head_y, head_r, direction)

        knife_hand_x = front_arm_x + front_arm_offset_x + 2
        knife_hand_y = front_arm_y + 5
        base_angle = 0 if self.facing_right else math.pi

        self._draw_front_arm(surface, front_arm_x, front_arm_y, knife_hand_x, knife_hand_y, direction)

        if self.weapon_state == "knife":
            if self.melee_active:
                progress = 1.0 - self.melee_timer / MELEE_DURATION_FRAMES
                swing_start = base_angle + math.radians(-MELEE_ARC_HALF * 0.55)
                swing_end = base_angle + math.radians(MELEE_ARC_HALF * 0.55)
                knife_angle = swing_start + (swing_end - swing_start) * progress
                self._draw_knife(surface, knife_hand_x, knife_hand_y, knife_angle, camera_x)
                self._draw_melee_effects(surface, camera_x, None, progress, base_angle, direction)
            else:
                rest_angle = math.radians(direction * 30)
                knife_angle = base_angle + rest_angle
                self._draw_knife(surface, knife_hand_x, knife_hand_y, knife_angle, camera_x)

        if not self.climbing and self.weapon_state == "gun":
            if self.melee_active:
                gun_angle = base_angle + math.radians(direction * 60)
                self._draw_gun(surface, knife_hand_x, knife_hand_y + 4, gun_angle, direction, camera_x)
            else:
                gun_angle = base_angle + math.radians(direction * 10)
                self._draw_gun(surface, knife_hand_x, knife_hand_y, gun_angle, direction, camera_x)

        if self.muzzle_flash_timer > 0 and not self.climbing and self.weapon_state == "gun":
            if self.melee_active:
                muzzle_angle = base_angle + math.radians(direction * 60)
            else:
                muzzle_angle = base_angle + math.radians(direction * 10)
            self._draw_muzzle_flash(surface, camera_x, None, direction,
                                    knife_hand_x, knife_hand_y, muzzle_angle)

        if self.reloading:
            reload_progress = 1.0 - self.reload_timer / RANGED_RELOAD_FRAMES
            rcx = self.x + self.width / 2 - camera_x
            rcy = self.y - 10
            arc_radius = 8
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * reload_progress
            if reload_progress > 0.01:
                rect = pygame.Rect(rcx - arc_radius, rcy - arc_radius,
                                   arc_radius * 2, arc_radius * 2)
                pygame.draw.arc(surface, RANGED_COLOR, rect, start_angle, end_angle, 2)

    def _draw_head(self, surface, cx, top_y, radius, direction):
        head_cy = top_y + radius

        hair_color = PLAYER_HAIR
        hair_dark = PLAYER_HAIR_DARK
        hat_color = PLAYER_HAT
        hat_dark = PLAYER_HAT_DARK
        hat_brim = PLAYER_HAT_BRIM
        hat_band = PLAYER_HAT_BAND

        face_color = PLAYER_SKIN
        face_shadow = PLAYER_SKIN_SHADOW

        pygame.draw.circle(surface, face_color, (int(cx), int(head_cy)), radius)

        shadow_side = cx - radius if direction > 0 else cx + radius
        shadow_rect = pygame.Rect(
            shadow_side - 2 if direction > 0 else shadow_side,
            top_y + 2,
            3,
            radius * 2 - 3,
        )
        pygame.draw.rect(surface, face_shadow, shadow_rect)

        hair_top_y = top_y - 2
        hair_left_x = cx - radius + 1
        hair_right_x = cx + radius - 1
        hair_points = [
            (int(hair_left_x), int(top_y + 2)),
            (int(cx - 3), int(hair_top_y)),
            (int(cx + 3), int(hair_top_y)),
            (int(hair_right_x), int(top_y + 2)),
        ]
        pygame.draw.polygon(surface, hair_color, hair_points)
        pygame.draw.line(surface, hair_dark,
                         (int(hair_left_x), int(top_y + 3)),
                         (int(hair_left_x + 1), int(hair_top_y + 2)), 1)
        pygame.draw.line(surface, hair_dark,
                         (int(hair_right_x), int(top_y + 3)),
                         (int(hair_right_x - 1), int(hair_top_y + 2)), 1)

        hat_top_y = hair_top_y - 6
        hat_left = cx - radius - 1
        hat_right = cx + radius + 1
        hat_height = 8

        hat_body_points = [
            (int(hat_left + 1), int(hair_top_y)),
            (int(hat_left + 2), int(hat_top_y + 2)),
            (int(cx - 2), int(hat_top_y)),
            (int(cx + 2), int(hat_top_y)),
            (int(hat_right - 2), int(hat_top_y + 2)),
            (int(hat_right - 1), int(hair_top_y)),
        ]
        pygame.draw.polygon(surface, hat_color, hat_body_points)

        band_y = hair_top_y - 1
        pygame.draw.rect(surface, hat_band,
                         (int(hat_left), int(band_y), int(hat_right - hat_left), 2))

        brim_front_x = cx + direction * (radius + 5)
        brim_back_x = cx - direction * (radius - 1)
        brim_y = hair_top_y + 1
        pygame.draw.line(surface, hat_brim,
                         (int(brim_back_x), int(brim_y)),
                         (int(brim_front_x), int(brim_y)), 3)
        pygame.draw.line(surface, hat_dark,
                         (int(brim_back_x), int(brim_y + 2)),
                         (int(brim_front_x), int(brim_y + 2)), 1)

        pygame.draw.line(surface, hat_dark,
                         (int(hat_left + 2), int(hat_top_y + 3)),
                         (int(hat_left + 3), int(hair_top_y)), 1)
        pygame.draw.line(surface, hat_dark,
                         (int(hat_right - 2), int(hat_top_y + 3)),
                         (int(hat_right - 3), int(hair_top_y)), 1)

        eye_y = head_cy - 1
        eye_spacing = 4
        eye_r = 2

        eye_offset = direction * 1

        left_eye_x = cx - eye_spacing + eye_offset
        right_eye_x = cx + eye_spacing + eye_offset

        if self.eye_blink > 0:
            pygame.draw.line(surface, PLAYER_PUPIL,
                             (int(left_eye_x - eye_r), int(eye_y)),
                             (int(left_eye_x + eye_r), int(eye_y)), 1)
            pygame.draw.line(surface, PLAYER_PUPIL,
                             (int(right_eye_x - eye_r), int(eye_y)),
                             (int(right_eye_x + eye_r), int(eye_y)), 1)
        else:
            pygame.draw.circle(surface, PLAYER_EYE, (int(left_eye_x), int(eye_y)), eye_r)
            pygame.draw.circle(surface, PLAYER_EYE, (int(right_eye_x), int(eye_y)), eye_r)
            pygame.draw.circle(surface, PLAYER_PUPIL,
                               (int(left_eye_x + direction * 1), int(eye_y)), 1)
            pygame.draw.circle(surface, PLAYER_PUPIL,
                               (int(right_eye_x + direction * 1), int(eye_y)), 1)

        cheek_y = eye_y + 4
        cheek_x_off = 6
        pygame.draw.circle(surface, PLAYER_CHEEK,
                           (int(cx - cheek_x_off), int(cheek_y)), 2)
        pygame.draw.circle(surface, PLAYER_CHEEK,
                           (int(cx + cheek_x_off), int(cheek_y)), 2)

    def _draw_body(self, surface, left, right, top, bottom, belt_y, belt_h, cx):
        shirt_color = PLAYER_SHIRT
        shirt_dark = PLAYER_SHIRT_DARK
        shirt_light = PLAYER_SHIRT_LIGHT
        belt_color = PLAYER_BELT
        buckle_color = PLAYER_BELT_BUCKLE

        body_points = [
            (int(left + 1), int(top)),
            (int(left + 2), int(bottom)),
            (int(right - 2), int(bottom)),
            (int(right - 1), int(top)),
        ]
        pygame.draw.polygon(surface, shirt_color, body_points)

        shadow_x = left if self.facing_right else right
        shadow_w = 3
        pygame.draw.rect(surface, shirt_dark,
                         (int(shadow_x - 1 if not self.facing_right else shadow_x),
                          int(top + 1),
                          shadow_w,
                          int(bottom - top - 1)))

        highlight_x = right if self.facing_right else left
        pygame.draw.rect(surface, shirt_light,
                         (int(highlight_x - 1 if self.facing_right else highlight_x),
                          int(top + 2),
                          2,
                          int(bottom - top - 4)))

        pygame.draw.rect(surface, belt_color,
                         (int(left), int(belt_y), int(right - left), belt_h))
        buckle_w = 4
        pygame.draw.rect(surface, buckle_color,
                         (int(cx - buckle_w / 2), int(belt_y - 1), buckle_w, belt_h + 2))
        pygame.draw.line(surface, (180, 150, 60),
                         (int(cx - buckle_w / 2 + 1), int(belt_y + 1)),
                         (int(cx + buckle_w / 2 - 1), int(belt_y + 1)), 1)

    def _draw_legs(self, surface, left_x, right_x, top, bottom, shoe_top, shoe_bottom):
        pants_color = PLAYER_PANTS
        pants_dark = PLAYER_PANTS_DARK
        shoe_color = PLAYER_SHOES
        shoe_light = PLAYER_SHOES_LIGHT

        leg_w = 5

        left_leg_rect = pygame.Rect(int(left_x - leg_w / 2), int(top), leg_w, int(bottom - top))
        right_leg_rect = pygame.Rect(int(right_x - leg_w / 2), int(top), leg_w, int(bottom - top))
        pygame.draw.rect(surface, pants_color, left_leg_rect)
        pygame.draw.rect(surface, pants_color, right_leg_rect)

        pygame.draw.rect(surface, pants_dark,
                         (int(left_x - leg_w / 2), int(top), 1, int(bottom - top)))
        pygame.draw.rect(surface, pants_dark,
                         (int(right_x - leg_w / 2), int(top), 1, int(bottom - top)))

        shoe_h = shoe_bottom - shoe_top
        left_shoe_rect = pygame.Rect(int(left_x - 4), int(shoe_top), 8, shoe_h)
        right_shoe_rect = pygame.Rect(int(right_x - 4), int(shoe_top), 8, shoe_h)
        pygame.draw.rect(surface, shoe_color, left_shoe_rect, border_radius=1)
        pygame.draw.rect(surface, shoe_color, right_shoe_rect, border_radius=1)

        pygame.draw.rect(surface, shoe_light,
                         (int(left_x - 3), int(shoe_top + 1), 3, 1))
        pygame.draw.rect(surface, shoe_light,
                         (int(right_x - 3), int(shoe_top + 1), 3, 1))

    def _draw_back_arm(self, surface, x, y, direction):
        sleeve_color = PLAYER_SHIRT_DARK
        glove_color = PLAYER_GLOVE_DARK

        arm_len = 8
        arm_end_y = y + arm_len

        pygame.draw.line(surface, sleeve_color,
                         (int(x), int(y)),
                         (int(x), int(arm_end_y - 2)), 3)

        pygame.draw.circle(surface, glove_color,
                           (int(x), int(arm_end_y)), 3)

    def _draw_front_arm(self, surface, shoulder_x, shoulder_y, hand_x, hand_y, direction):
        sleeve_color = PLAYER_SHIRT
        glove_color = PLAYER_GLOVE
        glove_dark = PLAYER_GLOVE_DARK

        mid_x = (shoulder_x + hand_x) / 2
        mid_y = (shoulder_y + hand_y) / 2 + 2

        pygame.draw.line(surface, sleeve_color,
                         (int(shoulder_x), int(shoulder_y)),
                         (int(mid_x), int(mid_y)), 4)
        pygame.draw.line(surface, glove_color,
                         (int(mid_x), int(mid_y)),
                         (int(hand_x), int(hand_y - 2)), 3)

        pygame.draw.circle(surface, glove_color,
                           (int(hand_x), int(hand_y)), 4)
        pygame.draw.circle(surface, glove_dark,
                           (int(hand_x - direction * 1), int(hand_y + 1)), 2)

    def _draw_knife(self, surface, hand_x, hand_y, angle, camera_x):
        hx = hand_x
        hy = hand_y
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        perp_x = -sin_a
        perp_y = cos_a

        handle_end_x = hx + cos_a * KNIFE_HANDLE_LENGTH
        handle_end_y = hy + sin_a * KNIFE_HANDLE_LENGTH

        handle_w = 4
        handle_poly = [
            (int(hx + perp_x * handle_w), int(hy + perp_y * handle_w)),
            (int(hx - perp_x * handle_w), int(hy - perp_y * handle_w)),
            (int(handle_end_x - perp_x * (handle_w - 0.5)), int(handle_end_y - perp_y * (handle_w - 0.5))),
            (int(handle_end_x + perp_x * (handle_w - 0.5)), int(handle_end_y + perp_y * (handle_w - 0.5))),
        ]
        pygame.draw.polygon(surface, KNIFE_HANDLE_COLOR, handle_poly)

        for i in range(3):
            wrap_t = (i + 1) / 4
            wx = hx + cos_a * KNIFE_HANDLE_LENGTH * wrap_t
            wy = hy + sin_a * KNIFE_HANDLE_LENGTH * wrap_t
            w_w = handle_w - (wrap_t * 0.5)
            pygame.draw.line(surface, KNIFE_HANDLE_WRAP,
                             (int(wx + perp_x * w_w), int(wy + perp_y * w_w)),
                             (int(wx - perp_x * w_w), int(wy - perp_y * w_w)), 1)

        pommel_x = hx - cos_a * 1
        pommel_y = hy - sin_a * 1
        pygame.draw.circle(surface, KNIFE_GUARD_COLOR,
                           (int(pommel_x), int(pommel_y)), 3)
        pygame.draw.circle(surface, KNIFE_GUARD_DARK,
                           (int(pommel_x - perp_x * 1), int(pommel_y - perp_y * 1)), 1)

        guard_w = 7
        guard_h = 2
        guard_center_x = handle_end_x + cos_a * 1
        guard_center_y = handle_end_y + sin_a * 1
        guard_poly = [
            (int(guard_center_x - perp_x * guard_w - cos_a * guard_h),
             int(guard_center_y - perp_y * guard_w - sin_a * guard_h)),
            (int(guard_center_x - perp_x * guard_w + cos_a * guard_h),
             int(guard_center_y - perp_y * guard_w + sin_a * guard_h)),
            (int(guard_center_x + perp_x * guard_w + cos_a * guard_h),
             int(guard_center_y + perp_y * guard_w + sin_a * guard_h)),
            (int(guard_center_x + perp_x * guard_w - cos_a * guard_h),
             int(guard_center_y + perp_y * guard_w - sin_a * guard_h)),
        ]
        pygame.draw.polygon(surface, KNIFE_GUARD_DARK, guard_poly)
        pygame.draw.line(surface, KNIFE_GUARD_COLOR,
                         (int(guard_center_x - perp_x * (guard_w - 1)),
                          int(guard_center_y - perp_y * (guard_w - 1))),
                         (int(guard_center_x + perp_x * (guard_w - 1)),
                          int(guard_center_y + perp_y * (guard_w - 1))), 2)

        blade_base_x = guard_center_x + cos_a * 2
        blade_base_y = guard_center_y + sin_a * 2
        blade_tip_x = blade_base_x + cos_a * KNIFE_LENGTH
        blade_tip_y = blade_base_y + sin_a * KNIFE_LENGTH

        bw = KNIFE_BLADE_WIDTH
        mid_t = 0.65
        mid_x = blade_base_x + cos_a * KNIFE_LENGTH * mid_t
        mid_y = blade_base_y + sin_a * KNIFE_LENGTH * mid_t

        blade_poly = [
            (int(blade_base_x + perp_x * bw), int(blade_base_y + perp_y * bw)),
            (int(mid_x + perp_x * bw * 0.85), int(mid_y + perp_y * bw * 0.85)),
            (int(blade_tip_x), int(blade_tip_y)),
            (int(mid_x - perp_x * bw * 0.5), int(mid_y - perp_y * bw * 0.5)),
            (int(blade_base_x - perp_x * bw * 0.8), int(blade_base_y - perp_y * bw * 0.8)),
        ]
        pygame.draw.polygon(surface, KNIFE_BLADE_COLOR, blade_poly)

        edge_pts = [
            (int(blade_base_x + perp_x * bw), int(blade_base_y + perp_y * bw)),
            (int(mid_x + perp_x * (bw * 0.4)), int(mid_y + perp_y * (bw * 0.4))),
            (int(blade_tip_x + perp_x * 0.5), int(blade_tip_y + perp_y * 0.5)),
        ]
        pygame.draw.polygon(surface, KNIFE_BLADE_HIGHLIGHT, edge_pts)

        spine_pts = [
            (int(blade_base_x - perp_x * bw * 0.6), int(blade_base_y - perp_y * bw * 0.6)),
            (int(mid_x - perp_x * bw * 0.3), int(mid_y - perp_y * bw * 0.3)),
            (int(blade_tip_x - perp_x * 0.3), int(blade_tip_y - perp_y * 0.3)),
        ]
        pygame.draw.lines(surface, KNIFE_BLADE_SHADOW, False, spine_pts, 1)

        fuller_start = blade_base_x + cos_a * 3
        fuller_start_y = blade_base_y + sin_a * 3
        fuller_end = blade_base_x + cos_a * (KNIFE_LENGTH * 0.6)
        fuller_end_y = blade_base_y + sin_a * (KNIFE_LENGTH * 0.6)
        pygame.draw.line(surface, KNIFE_BLADE_SHADOW,
                         (int(fuller_start + perp_x * 1.5), int(fuller_start_y + perp_y * 1.5)),
                         (int(fuller_end + perp_x * 1), int(fuller_end_y + perp_y * 1)), 1)
        pygame.draw.line(surface, KNIFE_BLADE_HIGHLIGHT,
                         (int(fuller_start - perp_x * 1), int(fuller_start_y - perp_y * 1)),
                         (int(fuller_end - perp_x * 0.5), int(fuller_end_y - perp_y * 0.5)), 1)

    def _draw_gun(self, surface, hand_x, hand_y, gun_angle, player_direction, camera_x):
        gx = hand_x
        gy = hand_y

        recoil_offset = 0
        if self.ranged_shot_timer > 0:
            recoil_t = self.ranged_shot_timer / GUN_RECOIL_FRAMES
            recoil_mag = GUN_RECOIL_DISTANCE * (1.0 - recoil_t)
            recoil_offset = -recoil_mag * math.cos(gun_angle)

        cos_a = math.cos(gun_angle)
        sin_a = math.sin(gun_angle)
        perp_x = -sin_a
        perp_y = cos_a

        body_start_x = gx + recoil_offset
        body_start_y = gy
        body_end_x = body_start_x + cos_a * GUN_BODY_LENGTH
        body_end_y = body_start_y + sin_a * GUN_BODY_LENGTH

        bh = GUN_BODY_HEIGHT / 2
        body_poly = [
            (int(body_start_x + perp_x * bh), int(body_start_y + perp_y * bh)),
            (int(body_start_x - perp_x * bh), int(body_start_y - perp_y * bh)),
            (int(body_end_x - perp_x * bh), int(body_end_y - perp_y * bh)),
            (int(body_end_x + perp_x * bh), int(body_end_y + perp_y * bh)),
        ]
        pygame.draw.polygon(surface, GUN_BODY_COLOR, body_poly)

        slide_top = [
            (int(body_start_x + perp_x * (bh - 0.5)), int(body_start_y + perp_y * (bh - 0.5))),
            (int(body_start_x + perp_x * (bh * 0.3)), int(body_start_y + perp_y * (bh * 0.3))),
            (int(body_end_x + perp_x * (bh * 0.3)), int(body_end_y + perp_y * (bh * 0.3))),
            (int(body_end_x + perp_x * (bh - 1)), int(body_end_y + perp_y * (bh - 1))),
        ]
        pygame.draw.polygon(surface, GUN_BODY_HIGHLIGHT, slide_top)

        shadow_bot = [
            (int(body_start_x - perp_x * (bh - 0.5)), int(body_start_y - perp_y * (bh - 0.5))),
            (int(body_start_x - perp_x * (bh * 0.5)), int(body_start_y - perp_y * (bh * 0.5))),
            (int(body_end_x - perp_x * (bh * 0.5)), int(body_end_y - perp_y * (bh * 0.5))),
            (int(body_end_x - perp_x * (bh - 0.5)), int(body_end_y - perp_y * (bh - 0.5))),
        ]
        pygame.draw.polygon(surface, GUN_BODY_SHADOW, shadow_bot)

        barrel_start_x = body_end_x
        barrel_start_y = body_end_y
        barrel_end_x = barrel_start_x + cos_a * GUN_BARREL_LENGTH
        barrel_end_y = barrel_start_y + sin_a * GUN_BARREL_LENGTH

        barrel_h = 2.5
        barrel_poly = [
            (int(barrel_start_x + perp_x * barrel_h), int(barrel_start_y + perp_y * barrel_h)),
            (int(barrel_start_x - perp_x * barrel_h), int(barrel_start_y - perp_y * barrel_h)),
            (int(barrel_end_x - perp_x * barrel_h), int(barrel_end_y - perp_y * barrel_h)),
            (int(barrel_end_x + perp_x * barrel_h), int(barrel_end_y + perp_y * barrel_h)),
        ]
        pygame.draw.polygon(surface, GUN_BARREL_COLOR, barrel_poly)

        pygame.draw.line(surface, GUN_BARREL_HIGHLIGHT,
                         (int(barrel_start_x + perp_x * (barrel_h - 0.5)), int(barrel_start_y + perp_y * (barrel_h - 0.5))),
                         (int(barrel_end_x + perp_x * (barrel_h - 0.5)), int(barrel_end_y + perp_y * (barrel_h - 0.5))), 1)

        pygame.draw.line(surface, GUN_BODY_SHADOW,
                         (int(barrel_end_x + perp_x * barrel_h), int(barrel_end_y + perp_y * barrel_h)),
                         (int(barrel_end_x - perp_x * barrel_h), int(barrel_end_y - perp_y * barrel_h)), 2)

        grip_top_x = body_start_x + cos_a * 5
        grip_top_y = body_start_y + sin_a * 5
        grip_down = perp_x * 9, perp_y * 9
        grip_bottom_x = grip_top_x + grip_down[0]
        grip_bottom_y = grip_top_y + grip_down[1]

        grip_tilt = cos_a * 2, sin_a * 2
        grip_poly = [
            (int(grip_top_x - perp_x * 3 + grip_tilt[0]), int(grip_top_y - perp_y * 3 + grip_tilt[1])),
            (int(grip_top_x + perp_x * 3 - grip_tilt[0] * 0.5), int(grip_top_y + perp_y * 3 - grip_tilt[1] * 0.5)),
            (int(grip_bottom_x + perp_x * 3 + grip_tilt[0]), int(grip_bottom_y + perp_y * 3 + grip_tilt[1])),
            (int(grip_bottom_x - perp_x * 3 - grip_tilt[0] * 0.5), int(grip_bottom_y - perp_y * 3 - grip_tilt[1] * 0.5)),
        ]
        pygame.draw.polygon(surface, GUN_GRIP_COLOR, grip_poly)

        for i in range(4):
            wrap_t = i / 4
            wx = grip_top_x + (grip_bottom_x - grip_top_x) * wrap_t
            wy = grip_top_y + (grip_bottom_y - grip_top_y) * wrap_t
            pygame.draw.line(surface, GUN_GRIP_WRAP,
                             (int(wx - perp_x * 2 + cos_a * (1 - wrap_t * 2)),
                              int(wy - perp_y * 2 + sin_a * (1 - wrap_t * 2))),
                             (int(wx + perp_x * 2 + cos_a * (1 - wrap_t * 2)),
                              int(wy + perp_y * 2 + sin_a * (1 - wrap_t * 2))), 1)

        trigger_guard_x = body_start_x + cos_a * 8
        trigger_guard_y = body_start_y + sin_a * 8
        tg_end_x = trigger_guard_x + perp_x * 5
        tg_end_y = trigger_guard_y + perp_y * 5
        pygame.draw.line(surface, GUN_TRIGGER_COLOR,
                         (int(trigger_guard_x), int(trigger_guard_y)),
                         (int(tg_end_x), int(tg_end_y)), 2)
        trigger_mid_x = trigger_guard_x + perp_x * 2
        trigger_mid_y = trigger_guard_y + perp_y * 2
        pygame.draw.line(surface, GUN_TRIGGER_COLOR,
                         (int(trigger_mid_x + cos_a * 1.5), int(trigger_mid_y + sin_a * 1.5)),
                         (int(trigger_mid_x - cos_a * 1.5), int(trigger_mid_y - sin_a * 1.5)), 2)

        sight_x = body_start_x + cos_a * 6
        sight_y = body_start_y + sin_a * 6
        pygame.draw.rect(surface, GUN_BODY_HIGHLIGHT,
                         (int(sight_x - 1), int(sight_y + perp_y * bh - 2), 3, 2))

        front_sight_x = barrel_end_x - cos_a * 3
        front_sight_y = barrel_end_y - sin_a * 3
        pygame.draw.line(surface, GUN_BODY_HIGHLIGHT,
                         (int(front_sight_x), int(front_sight_y + perp_y * barrel_h - 1)),
                         (int(front_sight_x - cos_a * 2), int(front_sight_y + perp_y * barrel_h + 1)), 2)

        mag_x = body_start_x + cos_a * 10
        mag_y = body_start_y + sin_a * 10
        mag_h = 6
        mag_w = 3
        mag_poly = [
            (int(mag_x - perp_x * mag_w + cos_a * 1), int(mag_y - perp_y * mag_w + sin_a * 1)),
            (int(mag_x + perp_x * mag_w - cos_a * 0.5), int(mag_y + perp_y * mag_w - sin_a * 0.5)),
            (int(mag_x + perp_x * (mag_w - 0.5) + perp_x * mag_h - cos_a * 1),
             int(mag_y + perp_y * (mag_w - 0.5) + perp_y * mag_h - sin_a * 1)),
            (int(mag_x - perp_x * (mag_w - 0.5) + perp_x * mag_h + cos_a * 0.5),
             int(mag_y - perp_y * (mag_w - 0.5) + perp_y * mag_h + sin_a * 0.5)),
        ]
        pygame.draw.polygon(surface, GUN_BODY_SHADOW, mag_poly)
        pygame.draw.line(surface, GUN_BODY_HIGHLIGHT,
                         (int(mag_x - perp_x * (mag_w - 1) + perp_x * 1),
                          int(mag_y - perp_y * (mag_w - 1) + perp_y * 1)),
                         (int(mag_x - perp_x * (mag_w - 1) + perp_x * (mag_h - 1)),
                          int(mag_y - perp_y * (mag_w - 1) + perp_y * (mag_h - 1))), 1)

    def _draw_melee_effects(self, surface, camera_x, body_rect, progress, base_angle, direction):
        pcx = self.x + self.width / 2 - camera_x
        pcy = self.y + self.height * 0.5

        swing_start = base_angle + math.radians(-MELEE_ARC_HALF * 0.7)
        swing_end = base_angle + math.radians(MELEE_ARC_HALF * 0.7)
        current_angle = swing_start + (swing_end - swing_start) * progress

        full_arc = MELEE_RANGE + 15
        glow_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        glow_cx = full_arc
        glow_cy = full_arc
        glow_r = min(full_arc - 1, MELEE_SLASH_GLOW_RADIUS)
        glow_intensity = max(0, 1 - abs(progress - 0.5) * 2)
        for r in range(glow_r, 0, -6):
            a = int(70 * glow_intensity * (r / glow_r))
            pygame.draw.circle(glow_surf, (*KNIFE_SWING_GLOW_COLOR, a),
                               (glow_cx, glow_cy), r)
        surface.blit(glow_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        arc_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        start_deg_adj = math.degrees(swing_start)
        end_deg_adj = math.degrees(swing_end)
        current_deg = start_deg_adj + (end_deg_adj - start_deg_adj) * progress

        for i in range(MELEE_SLASH_TRAIL_COUNT):
            t = i / MELEE_SLASH_TRAIL_COUNT
            trail_deg = start_deg_adj + (current_deg - start_deg_adj) * t
            trail_rad = math.radians(trail_deg)
            trail_len = (MELEE_RANGE + 5) * (0.4 + 0.6 * (1 - t))
            te_x = glow_cx + math.cos(trail_rad) * trail_len
            te_y = glow_cy + math.sin(trail_rad) * trail_len
            alpha = int(200 * (1 - t) * glow_intensity * 1.2)
            if alpha > 5:
                line_width = max(1, int(6 * (1 - t * 0.5)))
                pygame.draw.line(arc_surf, (*KNIFE_SLASH_TRAIL_COLOR, min(255, alpha)),
                                 (int(glow_cx), int(glow_cy)),
                                 (int(te_x), int(te_y)), line_width)
        surface.blit(arc_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        big_arc_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        arc_segments = 24
        arc_angle_span = (end_deg_adj - start_deg_adj)
        for i in range(arc_segments):
            t = i / arc_segments
            if t > progress + 0.02:
                break
            a_deg = start_deg_adj + arc_angle_span * t
            a_rad = math.radians(a_deg)
            tx = glow_cx + math.cos(a_rad) * (MELEE_RANGE + 5)
            ty = glow_cy + math.sin(a_rad) * (MELEE_RANGE + 5)
            dist_from_cur = abs(t - progress)
            seg_alpha = int(220 * max(0, 1 - dist_from_cur * 3))
            if seg_alpha > 10:
                pygame.draw.line(big_arc_surf,
                                 (*MELEE_SLASH_ARC_COLOR, min(255, seg_alpha)),
                                 (int(glow_cx), int(glow_cy)),
                                 (int(tx), int(ty)), MELEE_SLASH_ARC_WIDTH)
        surface.blit(big_arc_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        cur_rad = math.radians(current_deg)
        tip_x = pcx + math.cos(cur_rad) * (MELEE_RANGE + 5)
        tip_y = pcy + math.sin(cur_rad) * (MELEE_RANGE + 5)

        tip_glow_r = 10
        tip_surf = pygame.Surface((tip_glow_r * 2, tip_glow_r * 2), pygame.SRCALPHA)
        for r in range(tip_glow_r, 0, -3):
            a = int(180 * glow_intensity * (r / tip_glow_r))
            pygame.draw.circle(tip_surf, (*MELEE_COLOR_TIP, a),
                               (tip_glow_r, tip_glow_r), r)
        surface.blit(tip_surf, (int(tip_x - tip_glow_r), int(tip_y - tip_glow_r)))

        pygame.draw.circle(surface, MELEE_COLOR_TIP, (int(tip_x), int(tip_y)), 6)
        pygame.draw.circle(surface, (255, 255, 255), (int(tip_x), int(tip_y)), 3)

        if progress > 0.35 and progress < 0.75:
            impact_center_x = tip_x
            impact_center_y = tip_y
            imp_t = (progress - 0.35) / 0.4
            ring_r = int(4 + MELEE_IMPACT_RING_RADIUS * imp_t)
            ring_alpha = int(240 * max(0, 1 - imp_t))
            if ring_alpha > 0:
                for w in range(4, 0, -1):
                    line_a = int(ring_alpha * (w / 4))
                    if line_a > 0:
                        pygame.draw.circle(surface,
                                           (*KNIFE_IMPACT_FLASH_COLOR, line_a),
                                           (int(impact_center_x), int(impact_center_y)),
                                           ring_r, w)

            if imp_t < 0.3:
                flash_alpha = int(255 * (1 - imp_t / 0.3))
                flash_r = int(14 * (1 - imp_t / 0.3)) + 2
                for r in range(flash_r, 0, -3):
                    a = int(flash_alpha * (r / flash_r))
                    pygame.draw.circle(surface, (255, 240, 180, a),
                                       (int(impact_center_x), int(impact_center_y)), r)

            spark_n = MELEE_SLASH_SPARK_COUNT
            for i in range(spark_n):
                sa = cur_rad + math.radians(-30 + (60 / (spark_n - 1)) * i)
                sl = (8 + imp_t * 16) * (0.6 + 0.4 * ((i % 3) / 2))
                sx = impact_center_x + math.cos(sa) * sl
                sy = impact_center_y + math.sin(sa) * sl
                s_alpha = int(220 * max(0, 1 - imp_t))
                if s_alpha > 10:
                    pygame.draw.line(surface,
                                     (*MELEE_SLASH_ARC_COLOR, s_alpha),
                                     (int(impact_center_x + math.cos(sa) * 2),
                                      int(impact_center_y + math.sin(sa) * 2)),
                                     (int(sx), int(sy)),
                                     max(1, int(3 * (1 - imp_t))))

    def _draw_muzzle_flash(self, surface, camera_x, body_rect, direction, gun_hand_x=None, gun_hand_y=None, gun_angle=None):
        if gun_angle is None:
            gun_angle = 0.0 if self.facing_right else math.pi
            gun_angle += math.radians(direction * 3)
        cos_a = math.cos(gun_angle)
        sin_a = math.sin(gun_angle)
        perp_x = -sin_a
        perp_y = cos_a

        if gun_hand_x is None or gun_hand_y is None:
            body_edge_x = self.x + self.width / 2 + direction * 11
            gun_hand_x = body_edge_x - camera_x
            gun_hand_y = self.y + 35

        recoil_offset = 0
        if self.ranged_shot_timer > 0:
            recoil_t = self.ranged_shot_timer / GUN_RECOIL_FRAMES
            recoil_mag = GUN_RECOIL_DISTANCE * (1.0 - recoil_t)
            recoil_offset = -recoil_mag * cos_a

        body_start_x = gun_hand_x + recoil_offset
        barrel_end_x = body_start_x + cos_a * (GUN_BODY_LENGTH + GUN_BARREL_LENGTH)
        barrel_end_y = gun_hand_y + sin_a * (GUN_BODY_LENGTH + GUN_BARREL_LENGTH)

        flash_t = self.muzzle_flash_timer / MUZZLE_FLASH_DURATION
        flash_mag = flash_t
        flash_size = int(MUZZLE_FLASH_SIZE * (0.4 + 0.6 * flash_mag))

        if flash_size < 2:
            return

        cx = barrel_end_x + cos_a * (flash_size * 0.3)
        cy = barrel_end_y + sin_a * (flash_size * 0.3)

        outer_surf = pygame.Surface((flash_size * 4, flash_size * 4), pygame.SRCALPHA)
        ocx = flash_size * 2
        ocy = flash_size * 2
        big_r = flash_size * 1.8
        for r in range(int(big_r), 0, -3):
            a = int(90 * flash_mag * (r / big_r))
            pygame.draw.circle(outer_surf, (*MUZZLE_FLASH_OUTER, a), (ocx, ocy), r)
        surface.blit(outer_surf, (int(cx - ocx), int(cy - ocy)))

        flash_surf = pygame.Surface((flash_size * 3, flash_size * 3), pygame.SRCALPHA)
        fcx = flash_size * 1.5
        fcy = flash_size * 1.5

        star_pts = 8
        for i in range(star_pts):
            a = gun_angle + math.radians((360 / star_pts) * i)
            spike_len = flash_size * (0.7 + 0.6 * math.sin(i * 2.3 + flash_t * 20))
            sx = fcx + math.cos(a) * spike_len
            sy = fcy + math.sin(a) * spike_len
            a_val = int(220 * flash_mag)
            pygame.draw.line(flash_surf, (*MUZZLE_FLASH_COLOR, a_val),
                             (int(fcx), int(fcy)),
                             (int(sx), int(sy)), max(1, int(4 * flash_mag)))
            thick_a = a + math.radians(180 / star_pts)
            thick_len = flash_size * 0.5
            tx = fcx + math.cos(thick_a) * thick_len
            ty = fcy + math.sin(thick_a) * thick_len
            pygame.draw.line(flash_surf, (*MUZZLE_FLASH_OUTER, a_val),
                             (int(fcx), int(fcy)),
                             (int(tx), int(ty)), max(1, int(2 * flash_mag)))

        inner_r = flash_size * 0.8
        for r in range(int(inner_r), 0, -2):
            a = int(200 * flash_mag * (r / inner_r))
            pygame.draw.circle(flash_surf, (*MUZZLE_FLASH_COLOR, a),
                               (int(fcx), int(fcy)), r)
        white_r = flash_size * 0.35
        for r in range(max(1, int(white_r)), 0, -1):
            a = int(255 * flash_mag)
            pygame.draw.circle(flash_surf, (255, 255, 255, a),
                               (int(fcx), int(fcy)), r)
        surface.blit(flash_surf, (int(cx - fcx), int(cy - fcy)))

        beam_len = flash_size * 3
        beam_end_x = cx + cos_a * beam_len
        beam_end_y = cy + sin_a * beam_len
        beam_alpha = int(180 * flash_mag)
        for w in range(5, 0, -1):
            b_alpha = int(beam_alpha * (w / 5) * 0.6)
            pygame.draw.line(surface,
                             (*MUZZLE_FLASH_COLOR, b_alpha),
                             (int(cx), int(cy)),
                             (int(beam_end_x), int(beam_end_y)), w)

        barrel_dir_x = cos_a
        barrel_dir_y = sin_a
        casing_dir_x = perp_x * direction * 0.7 + barrel_dir_x * 0.3
        casing_dir_y = perp_y * direction * 0.7 + barrel_dir_y * 0.3
        casing_dist = CASING_EJECT_DISTANCE * (1 - flash_t)
        if casing_dist > 1:
            cas_x = barrel_end_x + cos_a * 5 + casing_dir_x * casing_dist
            cas_y = barrel_end_y + sin_a * 5 + casing_dir_y * casing_dist
            cas_rot = math.radians(360 * (1 - flash_t) + 45)
            cas_cos = math.cos(cas_rot)
            cas_sin = math.sin(cas_rot)
            cas_size = 3
            cas_poly = [
                (int(cas_x + cas_cos * cas_size - cas_sin * cas_size * 0.4),
                 int(cas_y + cas_sin * cas_size + cas_cos * cas_size * 0.4)),
                (int(cas_x + cas_cos * cas_size + cas_sin * cas_size * 0.4),
                 int(cas_y + cas_sin * cas_size - cas_cos * cas_size * 0.4)),
                (int(cas_x - cas_cos * cas_size + cas_sin * cas_size * 0.4),
                 int(cas_y - cas_sin * cas_size - cas_cos * cas_size * 0.4)),
                (int(cas_x - cas_cos * cas_size - cas_sin * cas_size * 0.4),
                 int(cas_y - cas_sin * cas_size + cas_cos * cas_size * 0.4)),
            ]
            c_alpha = int(220 * flash_mag)
            casing_surf = pygame.Surface((cas_size * 4, cas_size * 4), pygame.SRCALPHA)
            local_cx = cas_size * 2
            local_cy = cas_size * 2
            local_poly = [(int(p[0] - cas_x + local_cx), int(p[1] - cas_y + local_cy)) for p in cas_poly]
            pygame.draw.polygon(casing_surf, (*CASING_COLOR, c_alpha), local_poly)
            surface.blit(casing_surf, (int(cas_x - local_cx), int(cas_y - local_cy)))


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
            self._resolve_horizontal(platforms)
            self._resolve_vertical(platforms)
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

        self._resolve_horizontal(platforms)
        self._resolve_vertical(platforms)

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

    def _resolve_horizontal(self, platforms):
        """水平方向碰撞解析。"""
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.x = plat.rect.left - self.width
                elif self.vx < 0:
                    self.x = plat.rect.right
                self.vx = 0
                self._advance_target()
                rect = self.get_rect()

    def _resolve_vertical(self, platforms):
        """垂直方向碰撞解析。"""
        rect = self.get_rect()
        was_on_ground = self.on_ground
        self.on_ground = False

        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vy >= 0:
                    self.y = plat.rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = plat.rect.bottom
                    self.vy = 0
                rect = self.get_rect()

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
            if self.x + self.width > LEVEL_WIDTH:
                self.x = LEVEL_WIDTH - self.width
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
        if self.x + self.width > LEVEL_WIDTH:
            self.x = LEVEL_WIDTH - self.width

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
