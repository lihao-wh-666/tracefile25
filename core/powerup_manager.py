# -*- coding: utf-8 -*-
"""
core/powerup_manager.py - 道具管理器模块

提供统一的道具管理接口，支持：
- 道具获取 (acquire)
- 道具使用/激活 (use)
- 道具升级 (upgrade)
- 道具销毁 (remove)
- 数据持久化 (save / load)
- 反馈机制（UI提示、粒子、音效回调）
"""

import os
from typing import Dict, List, Optional, Any, Callable

from config import POWERUP_SAVE_FILE

from entities.powerups import (
    PowerupBase,
    PowerupType,
    PowerupState,
    SpeedBoostPowerup,
    ShieldPowerup,
    WeaponPowerup,
    PowerupPickup,
    create_powerup_from_type,
    create_powerup_from_dict,
)


class PowerupManager:
    """
    道具管理器。

    统一管理玩家拥有的三种道具，提供 CRUD 接口和持久化支持。
    通过 on_* 回调与游戏主循环集成，触发 UI/音效/粒子反馈。
    """

    def __init__(self, game=None):
        self.game = game

        self._inventory: Dict[PowerupType, PowerupBase] = {
            PowerupType.SPEED_BOOST: SpeedBoostPowerup(),
            PowerupType.SHIELD: ShieldPowerup(),
            PowerupType.WEAPON: WeaponPowerup(),
        }

        self.world_pickups: List[PowerupPickup] = []

        self.notification_text: str = ""
        self.notification_timer: int = 0
        self.NOTIFICATION_DURATION: int = 120

        self.on_powerup_acquired: Optional[Callable[[PowerupType], None]] = None
        self.on_powerup_activated: Optional[Callable[[PowerupType], None]] = None
        self.on_powerup_deactivated: Optional[Callable[[PowerupType], None]] = None
        self.on_powerup_upgraded: Optional[Callable[[PowerupType], None]] = None
        self.on_powerup_removed: Optional[Callable[[PowerupType], None]] = None
        self.on_notification: Optional[Callable[[str], None]] = None

        self._bind_inventory_callbacks()

    def _bind_inventory_callbacks(self):
        """为每个道具绑定状态变更回调。"""

        def make_activate_cb(t: PowerupType):
            def _cb():
                if self.on_powerup_activated:
                    self.on_powerup_activated(t)
            return _cb

        def make_deactivate_cb(t: PowerupType):
            def _cb():
                if self.on_powerup_deactivated:
                    self.on_powerup_deactivated(t)
            return _cb

        def make_upgrade_cb(t: PowerupType):
            def _cb():
                if self.on_powerup_upgraded:
                    self.on_powerup_upgraded(t)
            return _cb

        for t, p in self._inventory.items():
            p.on_activate = make_activate_cb(t)
            p.on_deactivate = make_deactivate_cb(t)
            p.on_upgrade = make_upgrade_cb(t)

    # ---------- 基础查询接口 ----------

    @property
    def all_powerups(self) -> List[PowerupBase]:
        """返回所有道具列表（按类型枚举顺序）。"""
        return [self._inventory[t] for t in PowerupType]

    def get_powerup(self, powerup_type: PowerupType) -> Optional[PowerupBase]:
        """根据类型获取道具实例，不存在返回 None。"""
        return self._inventory.get(powerup_type)

    def speed_boost(self) -> SpeedBoostPowerup:
        return self._inventory[PowerupType.SPEED_BOOST]

    def shield(self) -> ShieldPowerup:
        return self._inventory[PowerupType.SHIELD]

    def weapon(self) -> WeaponPowerup:
        return self._inventory[PowerupType.WEAPON]

    # ---------- 获取 / 收集 ----------

    def acquire_powerup(self, powerup_type: PowerupType) -> bool:
        """
        获取（收集）一个道具。

        若玩家尚未拥有该道具则标记为已获得（level=1）；
        若已拥有则自动执行一次升级（若未到满级）；满级则补充资源。
        """
        existing = self._inventory.get(powerup_type)
        if existing is None:
            self._inventory[powerup_type] = create_powerup_from_type(powerup_type)
            self._bind_single_callback(powerup_type)
            existing = self._inventory[powerup_type]
            existing.acquired = True
            self._trigger_upgrade_callback_if_any(powerup_type)
        elif not existing.acquired:
            existing.acquired = True
            self._trigger_upgrade_callback_if_any(powerup_type)
        else:
            if existing.level < existing.MAX_LEVEL:
                existing.upgrade()
            else:
                if isinstance(existing, WeaponPowerup):
                    existing.uses_remaining = min(
                        existing.uses_remaining + existing.max_uses // 2,
                        existing.max_uses * 2,
                    )
                elif isinstance(existing, ShieldPowerup):
                    if not existing.is_active:
                        existing.shield_value = existing.max_shield_value

        self._show_notification(
            f"获得道具: {self._inventory[powerup_type].display_name}"
        )
        if self.on_powerup_acquired:
            self.on_powerup_acquired(powerup_type)
        return True

    def _trigger_upgrade_callback_if_any(self, powerup_type: PowerupType):
        """如果绑定了通用升级回调则触发。"""
        cb = getattr(self, "on_any_upgrade", None)
        if callable(cb):
            cb(powerup_type)

    def _bind_single_callback(self, powerup_type: PowerupType):
        p = self._inventory[powerup_type]
        t = powerup_type
        p.on_activate = lambda: (
            self.on_powerup_activated(t) if self.on_powerup_activated else None
        )
        p.on_deactivate = lambda: (
            self.on_powerup_deactivated(t) if self.on_powerup_deactivated else None
        )
        p.on_upgrade = lambda: (
            self.on_powerup_upgraded(t) if self.on_powerup_upgraded else None
        )

    # ---------- 使用 / 激活 ----------

    def use_powerup(self, powerup_type: PowerupType) -> bool:
        """使用（激活）指定类型道具。"""
        p = self._inventory.get(powerup_type)
        if p is None:
            return False
        return p.activate()

    def use_speed_boost(self) -> bool:
        return self.use_powerup(PowerupType.SPEED_BOOST)

    def use_shield(self) -> bool:
        return self.use_powerup(PowerupType.SHIELD)

    def use_weapon(self) -> bool:
        return self.use_powerup(PowerupType.WEAPON)

    # ---------- 升级 ----------

    def upgrade_powerup(self, powerup_type: PowerupType) -> bool:
        """升级指定类型道具。"""
        p = self._inventory.get(powerup_type)
        if p is None:
            return False
        ok = p.upgrade()
        if ok:
            self._show_notification(
                f"道具升级: {p.display_name}"
            )
        return ok

    # ---------- 销毁 ----------

    def remove_powerup(self, powerup_type: PowerupType) -> bool:
        """销毁（重置）指定类型道具，保留槽位。"""
        if powerup_type not in self._inventory:
            return False
        p = self._inventory[powerup_type]
        p.force_deactivate()
        p.reset()
        p.acquired = False
        self._inventory[powerup_type] = create_powerup_from_type(powerup_type)
        self._bind_single_callback(powerup_type)
        if self.on_powerup_removed:
            self.on_powerup_removed(powerup_type)
        return True

    def reset_all(self):
        """重置所有道具到初始状态（等级归1、状态清0）。"""
        for p in self._inventory.values():
            p.reset()

    # ---------- 更新 ----------

    def update(self):
        """更新所有道具计时器和世界拾取物动画。"""
        for p in self._inventory.values():
            p.update()

        for pickup in self.world_pickups:
            pickup.update()

        if self.notification_timer > 0:
            self.notification_timer -= 1

    # ---------- 世界拾取物 ----------

    def spawn_pickup(self, x: float, y: float, powerup_type: PowerupType) -> PowerupPickup:
        """在世界指定位置生成一个道具拾取物。"""
        pickup = PowerupPickup(x, y, powerup_type)
        self.world_pickups.append(pickup)
        return pickup

    def clear_world_pickups(self):
        """清空所有世界拾取物。"""
        self.world_pickups.clear()

    def collect_pickup(self, pickup: PowerupPickup) -> bool:
        """玩家收集一个世界拾取物。"""
        if pickup.collected:
            return False
        pickup.collected = True
        pickup.collect_anim = pickup.max_collect_anim
        self.acquire_powerup(pickup.powerup_type)
        return True

    # ---------- 通知 ----------

    def _show_notification(self, text: str):
        """显示 UI 通知。"""
        self.notification_text = text
        self.notification_timer = self.NOTIFICATION_DURATION
        if self.on_notification:
            self.on_notification(text)

    @property
    def has_notification(self) -> bool:
        return self.notification_timer > 0

    @property
    def notification_alpha(self) -> float:
        """通知的透明度系数 (0.0 ~ 1.0)。"""
        if self.notification_timer <= 0:
            return 0.0
        fade = min(self.notification_timer, 30) / 30.0
        return min(1.0, fade)

    # ---------- 持久化 ----------

    def to_dict(self) -> Dict[str, Any]:
        """序列化所有道具状态为字典。"""
        return {
            "inventory": {
                t.value: p.to_dict() for t, p in self._inventory.items()
            },
            "version": "1.0",
        }

    def load_dict(self, data: Dict[str, Any]) -> bool:
        """从字典反序列化恢复道具状态。"""
        try:
            inv = data.get("inventory", {})
            for type_name, item_data in inv.items():
                try:
                    t = PowerupType(type_name)
                except ValueError:
                    continue
                restored = create_powerup_from_dict(item_data)
                self._inventory[t] = restored
                self._bind_single_callback(t)
            return True
        except Exception:
            return False

    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """保存到本地 JSON 文件。"""
        from core.save_load import saveData
        path = file_path or self._default_save_path()
        result = saveData(path, self.to_dict())
        return result.success

    def load_from_file(self, file_path: Optional[str] = None) -> bool:
        """从本地 JSON 文件加载。"""
        from core.save_load import loadData
        path = file_path or self._default_save_path()
        result = loadData(path)
        if not result.success:
            return False
        return self.load_dict(result.data)

    def _default_save_path(self) -> str:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "saves", POWERUP_SAVE_FILE)
