# -*- coding: utf-8 -*-
"""
entities/powerups.py - 道具系统模块

包含三种核心道具类型：
1. SpeedBoostPowerup - 加速道具（移动速度提升、持续时间、冷却）
2. ShieldPowerup - 护盾道具（伤害吸收、护盾值、持续时间）
3. WeaponPowerup - 武器道具（属性加成、攻击特效、使用次数、切换）

以及世界中的道具拾取物 PowerupPickup。
"""

import math
import random
from enum import Enum
from typing import Optional, Dict, Any, List

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    MOVE_SPEED,
    MELEE_DAMAGE, RANGED_DAMAGE,
    MELEE_COOLDOWN_FRAMES, RANGED_COOLDOWN_FRAMES,
    SPEED_BOOST_BASE_MULTIPLIER, SPEED_BOOST_DURATION_FRAMES,
    SPEED_BOOST_COOLDOWN_FRAMES, SPEED_BOOST_COLOR, SPEED_BOOST_DARK,
    SPEED_BOOST_GLOW, SPEED_BOOST_TRAIL_COLORS,
    SPEED_BOOST_MAX_UPGRADE_LEVEL,
    SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT,
    SPEED_BOOST_UPGRADE_DURATION_INCREMENT,
    SHIELD_BASE_VALUE, SHIELD_DURATION_FRAMES, SHIELD_COOLDOWN_FRAMES,
    SHIELD_COLOR, SHIELD_DARK, SHIELD_GLOW, SHIELD_BORDER,
    SHIELD_PARTICLE_COLORS, SHIELD_MAX_UPGRADE_LEVEL,
    SHIELD_UPGRADE_VALUE_INCREMENT, SHIELD_UPGRADE_DURATION_INCREMENT,
    WEAPON_BASE_DAMAGE_BONUS, WEAPON_BASE_FIRE_RATE_MULTIPLIER,
    WEAPON_USES_MAX, WEAPON_COOLDOWN_FRAMES,
    WEAPON_COLOR, WEAPON_DARK, WEAPON_GLOW, WEAPON_SPARK_COLORS,
    WEAPON_MAX_UPGRADE_LEVEL, WEAPON_UPGRADE_DAMAGE_INCREMENT,
    WEAPON_UPGRADE_USES_INCREMENT, WEAPON_TYPES,
    POWERUP_PICKUP_RADIUS, POWERUP_BOB_AMPLITUDE,
    POWERUP_PICKUP_ANIM_FRAMES,
)


class PowerupType(Enum):
    """道具类型枚举。"""
    SPEED_BOOST = "speed_boost"
    SHIELD = "shield"
    WEAPON = "weapon"


class PowerupState(Enum):
    """道具状态枚举。"""
    IDLE = "idle"
    ACTIVE = "active"
    COOLDOWN = "cooldown"


class PowerupBase:
    """
    道具基类，定义所有道具的通用接口和属性。

    所有具体道具类型都继承此类，实现统一的：
    - 激活 (activate)
    - 更新 (update)
    - 失效 (deactivate)
    - 升级 (upgrade)
    - 重置 (reset)
    - 序列化/反序列化 (to_dict / from_dict)
    """

    TYPE: PowerupType = None
    MAX_LEVEL: int = 3

    def __init__(self, level: int = 1):
        self.level = max(1, min(level, self.MAX_LEVEL))
        self.state = PowerupState.IDLE
        self.active_timer = 0
        self.cooldown_timer = 0
        self.max_duration = 0
        self.max_cooldown = 0
        self.acquired = False
        self.on_activate = None
        self.on_deactivate = None
        self.on_upgrade = None
        self.on_cooldown_end = None

    @property
    def is_active(self) -> bool:
        """道具是否处于激活状态。"""
        return self.state == PowerupState.ACTIVE

    @property
    def is_on_cooldown(self) -> bool:
        """道具是否处于冷却状态。"""
        return self.state == PowerupState.COOLDOWN

    @property
    def can_activate(self) -> bool:
        """道具当前是否可以激活。"""
        return self.state == PowerupState.IDLE

    @property
    def progress_ratio(self) -> float:
        """
        当前进度比例 (0.0 ~ 1.0)。
        - 激活中：剩余持续时间比例
        - 冷却中：剩余冷却时间比例
        - 空闲：1.0
        """
        if self.state == PowerupState.ACTIVE and self.max_duration > 0:
            return self.active_timer / self.max_duration
        if self.state == PowerupState.COOLDOWN and self.max_cooldown > 0:
            return 1.0 - (self.cooldown_timer / self.max_cooldown)
        return 1.0

    def _compute_stats_for_level(self, level: int):
        """根据等级计算具体数值，子类必须重写。"""
        raise NotImplementedError

    def activate(self) -> bool:
        """
        激活道具。

        Returns:
            bool: 是否成功激活
        """
        if not self.acquired:
            return False
        if not self.can_activate:
            return False
        self._compute_stats_for_level(self.level)
        self.state = PowerupState.ACTIVE
        self.active_timer = self.max_duration
        self.cooldown_timer = 0
        if self.on_activate:
            self.on_activate()
        return True

    def update(self):
        """更新道具计时器和状态。"""
        if self.state == PowerupState.ACTIVE:
            self.active_timer -= 1
            if self.active_timer <= 0:
                self._expire()
        elif self.state == PowerupState.COOLDOWN:
            self.cooldown_timer -= 1
            if self.cooldown_timer <= 0:
                self.state = PowerupState.IDLE
                if self.on_cooldown_end:
                    self.on_cooldown_end()

    def _expire(self):
        """道具效果到期，进入冷却。"""
        self.state = PowerupState.COOLDOWN
        self.cooldown_timer = self.max_cooldown
        self.active_timer = 0
        if self.on_deactivate:
            self.on_deactivate()

    def force_deactivate(self):
        """强制使道具失效（不进入冷却）。"""
        if self.state == PowerupState.ACTIVE:
            self.state = PowerupState.IDLE
            self.active_timer = 0
            if self.on_deactivate:
                self.on_deactivate()

    def upgrade(self) -> bool:
        """
        升级道具。

        Returns:
            bool: 是否成功升级
        """
        if self.level >= self.MAX_LEVEL:
            return False
        self.level += 1
        self._compute_stats_for_level(self.level)
        if self.on_upgrade:
            self.on_upgrade()
        return True

    def reset(self):
        """重置道具到初始状态。"""
        self.level = 1
        self.state = PowerupState.IDLE
        self.active_timer = 0
        self.cooldown_timer = 0
        self.acquired = False
        self._compute_stats_for_level(self.level)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于持久化）。"""
        return {
            "type": self.TYPE.value,
            "level": self.level,
            "state": self.state.value,
            "active_timer": self.active_timer,
            "cooldown_timer": self.cooldown_timer,
            "max_duration": self.max_duration,
            "max_cooldown": self.max_cooldown,
            "acquired": self.acquired,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PowerupBase":
        """从字典反序列化。"""
        obj = cls()
        obj.level = data.get("level", 1)
        obj.state = PowerupState(data.get("state", "idle"))
        obj.active_timer = data.get("active_timer", 0)
        obj.cooldown_timer = data.get("cooldown_timer", 0)
        obj.max_duration = data.get("max_duration", 0)
        obj.max_cooldown = data.get("max_cooldown", 0)
        obj.acquired = data.get("acquired", False)
        obj._compute_stats_for_level(obj.level)
        return obj


class SpeedBoostPowerup(PowerupBase):
    """
    加速道具。

    功能:
    - 提升角色移动速度 (speed_multiplier)
    - 持续时间控制 (max_duration)
    - 冷却机制 (max_cooldown)
    - 支持升级：提升加幅比例和持续时间
    - 视觉效果反馈：通过 trail_colors 粒子体现
    """

    TYPE = PowerupType.SPEED_BOOST
    MAX_LEVEL = SPEED_BOOST_MAX_UPGRADE_LEVEL

    def __init__(self, level: int = 1):
        super().__init__(level=level)
        self.speed_multiplier = 1.0
        self.base_move_speed = MOVE_SPEED
        self._compute_stats_for_level(self.level)

    @property
    def duration_frames(self) -> int:
        return self.max_duration

    @property
    def cooldown_frames(self) -> int:
        return self.max_cooldown

    def _compute_stats_for_level(self, level: int):
        lvl = max(1, min(level, self.MAX_LEVEL))
        self.speed_multiplier = (
            SPEED_BOOST_BASE_MULTIPLIER
            + (lvl - 1) * SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT
        )
        self.max_duration = (
            SPEED_BOOST_DURATION_FRAMES
            + (lvl - 1) * SPEED_BOOST_UPGRADE_DURATION_INCREMENT
        )
        self.max_cooldown = SPEED_BOOST_COOLDOWN_FRAMES

    def get_effective_speed(self, base_speed: float) -> float:
        """获取应用道具效果后的实际速度。"""
        if self.is_active:
            return base_speed * self.speed_multiplier
        return base_speed

    @property
    def color(self):
        return SPEED_BOOST_COLOR

    @property
    def trail_colors(self) -> List[tuple]:
        return SPEED_BOOST_TRAIL_COLORS

    @property
    def display_name(self) -> str:
        return f"加速 Lv.{self.level}"


class ShieldPowerup(PowerupBase):
    """
    护盾道具。

    功能:
    - 提供护盾值 (shield_value) 吸收伤害
    - 伤害吸收逻辑：优先扣护盾，护盾为0时道具提前失效
    - 持续时间管理
    - 护盾状态显示：通过 hud_color / border_color
    - 支持升级：增加护盾值和持续时间
    """

    TYPE = PowerupType.SHIELD
    MAX_LEVEL = SHIELD_MAX_UPGRADE_LEVEL

    def __init__(self, level: int = 1):
        super().__init__(level=level)
        self.shield_value = 0
        self.max_shield_value = 0
        self._compute_stats_for_level(self.level)

    @property
    def duration_frames(self) -> int:
        return self.max_duration

    @property
    def cooldown_frames(self) -> int:
        return self.max_cooldown

    def _compute_stats_for_level(self, level: int):
        lvl = max(1, min(level, self.MAX_LEVEL))
        self.max_shield_value = (
            SHIELD_BASE_VALUE + (lvl - 1) * SHIELD_UPGRADE_VALUE_INCREMENT
        )
        if self.shield_value <= 0 or self.shield_value > self.max_shield_value:
            self.shield_value = self.max_shield_value
        self.max_duration = (
            SHIELD_DURATION_FRAMES
            + (lvl - 1) * SHIELD_UPGRADE_DURATION_INCREMENT
        )
        self.max_cooldown = SHIELD_COOLDOWN_FRAMES

    def activate(self) -> bool:
        if super().activate():
            self.shield_value = self.max_shield_value
            return True
        return False

    def absorb_damage(self, damage: int) -> int:
        """
        吸收伤害，返回剩余需要扣除玩家生命的伤害量。

        Args:
            damage: 原始伤害值

        Returns:
            int: 未被吸收、需要玩家承受伤值
        """
        if not self.is_active or damage <= 0:
            return damage

        absorbed = min(self.shield_value, damage)
        self.shield_value -= absorbed
        remaining = damage - absorbed

        if self.shield_value <= 0:
            self._expire()

        return remaining

    @property
    def shield_ratio(self) -> float:
        """护盾值比例 (0.0 ~ 1.0)。"""
        if self.max_shield_value <= 0:
            return 0.0
        return self.shield_value / self.max_shield_value

    @property
    def color(self):
        return SHIELD_COLOR

    @property
    def border_color(self):
        return SHIELD_BORDER

    @property
    def glow_color(self):
        return SHIELD_GLOW

    @property
    def particle_colors(self) -> List[tuple]:
        return SHIELD_PARTICLE_COLORS

    @property
    def display_name(self) -> str:
        return f"护盾 Lv.{self.level}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["shield_value"] = self.shield_value
        d["max_shield_value"] = self.max_shield_value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShieldPowerup":
        obj = super().from_dict(data)
        obj.shield_value = data.get("shield_value", obj.max_shield_value)
        obj.max_shield_value = data.get(
            "max_shield_value", obj.max_shield_value
        )
        return obj


class WeaponPowerup(PowerupBase):
    """
    武器道具。

    功能:
    - 武器属性加成：damage_bonus 加伤害，fire_rate_multiplier 加快冷却
    - 攻击特效触发：通过 spark_colors 体现
    - 使用次数限制：uses_remaining
    - 武器切换逻辑：支持 WEAPON_TYPES 切换
    - 支持升级：增加伤害加成和使用次数
    """

    TYPE = PowerupType.WEAPON
    MAX_LEVEL = WEAPON_MAX_UPGRADE_LEVEL

    def __init__(self, level: int = 1):
        super().__init__(level=level)
        self.damage_bonus = 0
        self.fire_rate_multiplier = 1.0
        self.uses_remaining = 0
        self.max_uses = 0
        self.weapon_type_index = 0
        self.on_switch = None
        self._compute_stats_for_level(self.level)

    @property
    def duration_frames(self) -> int:
        return self.max_duration

    @property
    def cooldown_frames(self) -> int:
        return self.max_cooldown

    @property
    def current_weapon_type(self) -> str:
        return WEAPON_TYPES[self.weapon_type_index]

    @property
    def weapon_type(self) -> str:
        return WEAPON_TYPES[self.weapon_type_index]

    def _compute_stats_for_level(self, level: int):
        lvl = max(1, min(level, self.MAX_LEVEL))
        self.damage_bonus = (
            WEAPON_BASE_DAMAGE_BONUS
            + (lvl - 1) * WEAPON_UPGRADE_DAMAGE_INCREMENT
        )
        self.fire_rate_multiplier = WEAPON_BASE_FIRE_RATE_MULTIPLIER
        self.max_uses = (
            WEAPON_USES_MAX + (lvl - 1) * WEAPON_UPGRADE_USES_INCREMENT
        )
        if self.uses_remaining <= 0 or self.uses_remaining > self.max_uses:
            self.uses_remaining = self.max_uses
        self.max_duration = 0
        self.max_cooldown = WEAPON_COOLDOWN_FRAMES

    def activate(self) -> bool:
        if not self.can_activate:
            return False
        if self.uses_remaining <= 0:
            return False
        self.state = PowerupState.ACTIVE
        self.active_timer = 0
        self.cooldown_timer = 0
        if self.on_activate:
            self.on_activate()
        return True

    def consume_use(self) -> bool:
        """
        消耗一次使用次数。

        Returns:
            bool: 本次攻击是否成功触发了武器强化效果
        """
        if not self.is_active:
            return False
        if self.uses_remaining <= 0:
            self._expire()
            return False

        self.uses_remaining -= 1

        if self.uses_remaining <= 0:
            self._expire()
        else:
            self.state = PowerupState.COOLDOWN
            self.cooldown_timer = self.max_cooldown
        return True

    def switch_weapon_type(self) -> bool:
        """切换武器类型，返回是否切换成功。"""
        self.weapon_type_index = (self.weapon_type_index + 1) % len(WEAPON_TYPES)
        if self.on_switch:
            self.on_switch()
        return True

    @property
    def weapon_type(self) -> str:
        return WEAPON_TYPES[self.weapon_type_index]

    def get_modified_melee_damage(self, base: int) -> int:
        """获取强化后的近战伤害。"""
        if (self.is_active or self.state == PowerupState.COOLDOWN) and self.uses_remaining > 0:
            return base + self.damage_bonus
        return base

    def get_modified_ranged_damage(self, base: int) -> int:
        """获取强化后的远程伤害。"""
        if (self.is_active or self.state == PowerupState.COOLDOWN) and self.uses_remaining > 0:
            return base + self.damage_bonus
        return base

    def get_modified_attack_cooldown(self, base_frames: int, is_melee: bool) -> int:
        """获取缩短后的攻击冷却帧数。"""
        if (self.is_active or self.state == PowerupState.COOLDOWN) and self.uses_remaining > 0:
            return max(1, int(base_frames * self.fire_rate_multiplier))
        return base_frames

    def update(self):
        """武器道具激活状态不自动过期，只冷却。"""
        if self.state == PowerupState.ACTIVE:
            pass
        elif self.state == PowerupState.COOLDOWN:
            self.cooldown_timer -= 1
            if self.cooldown_timer <= 0:
                self.state = PowerupState.IDLE
                if self.on_cooldown_end:
                    self.on_cooldown_end()

    @property
    def uses_ratio(self) -> float:
        """剩余使用次数比例。"""
        if self.max_uses <= 0:
            return 0.0
        return self.uses_remaining / self.max_uses

    @property
    def color(self):
        return WEAPON_COLOR

    @property
    def spark_colors(self) -> List[tuple]:
        return WEAPON_SPARK_COLORS

    @property
    def display_name(self) -> str:
        return f"强化武器 Lv.{self.level}"

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["damage_bonus"] = self.damage_bonus
        d["fire_rate_multiplier"] = self.fire_rate_multiplier
        d["uses_remaining"] = self.uses_remaining
        d["max_uses"] = self.max_uses
        d["weapon_type_index"] = self.weapon_type_index
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeaponPowerup":
        obj = super().from_dict(data)
        obj.damage_bonus = data.get("damage_bonus", obj.damage_bonus)
        obj.fire_rate_multiplier = data.get(
            "fire_rate_multiplier", obj.fire_rate_multiplier
        )
        obj.uses_remaining = data.get("uses_remaining", obj.max_uses)
        obj.max_uses = data.get("max_uses", obj.max_uses)
        obj.weapon_type_index = data.get("weapon_type_index", 0)
        return obj


class PowerupPickup:
    """
    世界中的道具拾取物。

    玩家接触后会将对应道具加入背包。
    """

    def __init__(
        self,
        x: float,
        y: float,
        powerup_type: PowerupType,
    ):
        self.x = x
        self.y = y
        self.powerup_type = powerup_type
        self.ptype = powerup_type
        self.radius = POWERUP_PICKUP_RADIUS
        self.collected = False
        self.bob_offset = random.random() * math.pi * 2
        self.collect_anim = 0
        self.max_collect_anim = POWERUP_PICKUP_ANIM_FRAMES
        self.scale = 1.0
        self.collect_anim_started = False
        self.collect_anim_frames = POWERUP_PICKUP_ANIM_FRAMES
        self._tick = 0
        self.current_bob_y = 0.0

    @property
    def powerup_type(self):
        return self._powerup_type

    @powerup_type.setter
    def powerup_type(self, value):
        self._powerup_type = value
        self.ptype = value

    def get_rect(self):
        """返回碰撞检测矩形。"""
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )

    def particle_colors(self):
        """返回拾取物的粒子颜色列表。"""
        if self.powerup_type == PowerupType.SPEED_BOOST:
            return list(SPEED_BOOST_TRAIL_COLORS)
        elif self.powerup_type == PowerupType.SHIELD:
            return list(SHIELD_PARTICLE_COLORS)
        else:
            return list(WEAPON_SPARK_COLORS)

    def update(self):
        """更新收集动画计时器。"""
        self._tick += 1
        self.current_bob_y = math.sin(
            self._tick * 0.05 + self.bob_offset
        ) * POWERUP_BOB_AMPLITUDE
        if self.collect_anim_started:
            self.collect_anim_frames = max(0, self.collect_anim_frames - 1)
            progress = 1.0 - (
                self.collect_anim_frames / max(1, POWERUP_PICKUP_ANIM_FRAMES)
            )
            self.scale = 1.0 + progress * 0.8
        if self.collect_anim > 0:
            self.collect_anim -= 1

    def _get_colors(self):
        if self.powerup_type == PowerupType.SPEED_BOOST:
            return SPEED_BOOST_COLOR, SPEED_BOOST_DARK, SPEED_BOOST_GLOW
        elif self.powerup_type == PowerupType.SHIELD:
            return SHIELD_COLOR, SHIELD_DARK, SHIELD_GLOW
        else:
            return WEAPON_COLOR, WEAPON_DARK, WEAPON_GLOW

    def _get_symbol(self):
        if self.powerup_type == PowerupType.SPEED_BOOST:
            return "S"
        elif self.powerup_type == PowerupType.SHIELD:
            return "+"
        else:
            return "W"

    def draw(self, surface: pygame.Surface, camera_x: int, tick: int = 0):
        """绘制道具拾取物，含浮动动画和发光效果。"""
        if tick == 0:
            tick = self._tick
        if self.collected and self.collect_anim <= 0 and self.collect_anim_frames <= 0:
            return

        main_c, dark_c, glow_c = self._get_colors()

        bob_y = math.sin(tick * 0.05 + self.bob_offset) * POWERUP_BOB_AMPLITUDE
        sx = int(self.x - camera_x)
        sy = int(self.y + bob_y)

        if self.collected:
            alpha = self.collect_anim / self.max_collect_anim
            size = int(self.radius * (2.5 - alpha * 1.5))
            color = (
                int(main_c[0] * alpha + 255 * (1 - alpha)),
                int(main_c[1] * alpha + 255 * (1 - alpha)),
                int(main_c[2] * alpha + 255 * (1 - alpha)),
            )
            pygame.draw.circle(surface, color, (sx, sy), max(2, size))
            return

        if sx + self.radius < -40 or sx - self.radius > SCREEN_WIDTH + 40:
            return

        glow_r = self.radius + 6 + int(math.sin(tick * 0.08) * 2)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf, (*glow_c, 70), (glow_r, glow_r), glow_r
        )
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        pygame.draw.circle(surface, dark_c, (sx + 2, sy + 2), self.radius)
        pygame.draw.circle(surface, main_c, (sx, sy), self.radius)

        inner_r = self.radius - 4
        if inner_r > 0:
            pygame.draw.circle(surface, glow_c, (sx, sy), inner_r)

        if self.powerup_type == PowerupType.SPEED_BOOST:
            for i, dx in enumerate([-5, 0, 5]):
                pygame.draw.line(
                    surface, dark_c,
                    (sx + dx - 3, sy + 4 - i * 3),
                    (sx + dx + 3, sy + 4 - i * 3), 2
                )
        elif self.powerup_type == PowerupType.SHIELD:
            pygame.draw.polygon(
                surface, dark_c,
                [
                    (sx, sy - 7),
                    (sx + 6, sy - 3),
                    (sx + 6, sy + 4),
                    (sx, sy + 8),
                    (sx - 6, sy + 4),
                    (sx - 6, sy - 3),
                ], 2
            )
        else:
            pygame.draw.line(
                surface, dark_c,
                (sx - 7, sy + 5), (sx + 7, sy - 5), 3
            )
            pygame.draw.rect(
                surface, dark_c, (sx - 2, sy + 2, 4, 6)
            )


POWERUP_TYPE_MAP: Dict[str, type] = {
    PowerupType.SPEED_BOOST.value: SpeedBoostPowerup,
    PowerupType.SHIELD.value: ShieldPowerup,
    PowerupType.WEAPON.value: WeaponPowerup,
}


def create_powerup_from_type(powerup_type: PowerupType) -> PowerupBase:
    """根据枚举类型创建对应道具实例。"""
    cls = POWERUP_TYPE_MAP.get(powerup_type.value)
    if cls is None:
        raise ValueError(f"Unknown powerup type: {powerup_type}")
    return cls()


def create_powerup_from_dict(data: Dict[str, Any]) -> Optional[PowerupBase]:
    """从序列化字典创建道具实例。非法类型返回 None。"""
    type_name = data.get("type")
    cls = POWERUP_TYPE_MAP.get(type_name)
    if cls is None:
        return None
    return cls.from_dict(data)
