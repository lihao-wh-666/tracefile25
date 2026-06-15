# -*- coding: utf-8 -*-
"""
entities/player/base.py - 玩家基类模块

定义玩家角色的基础属性和接口。
"""

import pygame

from config import (
    MOVE_SPEED,
    JUMP_FORCE, GRAVITY, MAX_FALL_SPEED,
    JUMP_BUFFER_FRAMES, COYOTE_TIME_FRAMES, SHORT_JUMP_MULTIPLIER,
    SHORT_JUMP_THRESHOLD,
    SQUASH_INTERPOLATION, SQUASH_ON_JUMP, SQUASH_ON_FALL,
    SQUASH_ON_LAND, SQUASH_NORMAL, SQUASH_ON_CLIMB,
    RUN_ANIM_SPEED, BLINK_INTERVAL, BLINK_DURATION,
    LEVEL_WIDTH, FALL_RESPAWN_Y,
    MAX_JUMP_COUNT, MULTI_JUMP_FORCE, MULTI_JUMP_INTERVAL_FRAMES,
    LADDER_WIDTH, CLIMB_SPEED,
    MELEE_COOLDOWN_FRAMES, MELEE_DURATION_FRAMES, MELEE_ARC_HALF,
    RANGED_COOLDOWN_FRAMES, RANGED_AMMO_MAX, RANGED_AMMO_INITIAL,
    RANGED_PROJECTILE_SPEED, RANGED_RELOAD_FRAMES,
    GUN_RECOIL_FRAMES, MUZZLE_FLASH_DURATION,
)

from ..combat import Bullet


class PlayerBase:
    """
    玩家角色基类，定义所有属性和基础接口。

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
        self.ammo_max = RANGED_AMMO_MAX
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
