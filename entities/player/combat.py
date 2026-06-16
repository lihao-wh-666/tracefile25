# -*- coding: utf-8 -*-
"""
entities/player/combat.py - 玩家战斗模块

提供玩家角色的近战、远程攻击和弹药管理功能。
作为 Mixin 类使用，与 PlayerBase 和其他 Mixin 组合。
扩展支持武器道具伤害加成和冷却缩减。
"""

import math
import pygame

from config import (
    MELEE_COOLDOWN_FRAMES, MELEE_RANGE, MELEE_ARC_HALF, MELEE_DAMAGE,
    MELEE_DURATION_FRAMES,
    RANGED_COOLDOWN_FRAMES, RANGED_AMMO_MAX, RANGED_AMMO_INITIAL,
    RANGED_PROJECTILE_SPEED, RANGED_RELOAD_FRAMES,
    GUN_RECOIL_FRAMES, MUZZLE_FLASH_DURATION,
    RANGED_DAMAGE,
)

from ..combat import Bullet


class PlayerCombatMixin:
    """
    玩家战斗 Mixin 类。

    提供以下功能:
    - 近战攻击（匕首挥砍）
    - 远程攻击（枪械射击）
    - 弹药管理和换弹
    - 近战攻击判定框计算
    - 战斗状态更新
    - 武器道具：伤害加成、冷却缩减、使用次数消耗
    """

    last_melee_enhanced = False
    last_ranged_enhanced = False

    def start_melee(self):
        """开始近战攻击。"""
        if self.melee_cooldown > 0 or self.melee_active:
            return False

        self.last_melee_enhanced = False
        if self.is_weapon_enhanced():
            self.last_melee_enhanced = True
            self.consume_weapon_use()

        effective_cd = self.get_effective_cooldown(MELEE_COOLDOWN_FRAMES, True)
        self.melee_active = True
        self.melee_timer = MELEE_DURATION_FRAMES
        self.melee_cooldown = effective_cd
        self.melee_hit_done = False
        self.melee_angle = -MELEE_ARC_HALF
        self.weapon_state = "knife"
        if self.on_melee_swing:
            self.on_melee_swing()
        return True

    def get_melee_damage(self):
        """获取当前近战伤害（含武器强化）。"""
        base = MELEE_DAMAGE
        if self.last_melee_enhanced:
            return self.get_effective_melee_damage(base)
        return base

    def start_ranged_shot(self):
        """开始远程射击，返回发射的子弹对象。"""
        if self.ranged_cooldown > 0 or self.reloading:
            return None
        if self.ammo <= 0:
            return None
        self.ammo -= 1

        self.last_ranged_enhanced = False
        if self.is_weapon_enhanced():
            self.last_ranged_enhanced = True
            self.consume_weapon_use()

        effective_cd = self.get_effective_cooldown(RANGED_COOLDOWN_FRAMES, False)
        self.ranged_cooldown = effective_cd

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

        bullet = Bullet(cx + direction * 15, cy, vx, vy)
        if self.last_ranged_enhanced:
            bullet.damage = self.get_effective_ranged_damage(bullet.damage)
            bullet.enhanced = True
        return bullet

    def start_reload(self):
        """开始换弹。"""
        if self.reloading or self.ammo >= RANGED_AMMO_MAX:
            return False
        self.reloading = True
        self.reload_timer = RANGED_RELOAD_FRAMES
        self.weapon_state = "gun"
        if self.on_reload:
            self.on_reload()
        return True

    def get_melee_hitbox(self):
        """获取当前近战攻击的判定框。"""
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
        extra = 6 if self.last_melee_enhanced else 0
        size = 24 + extra
        return pygame.Rect(hit_x - size // 2, hit_y - size // 2, size, size)

    def update_combat(self):
        """更新战斗状态计时器。"""
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

        if self.invuln_timer > 0:
            self.invuln_timer -= 1
            if self.invuln_timer <= 0:
                self.invulnerable = False
