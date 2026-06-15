# -*- coding: utf-8 -*-
"""
entities/__init__.py - 实体模块导出

统一导出所有游戏实体类，保持向后兼容性。
"""

from .base import BaseEntity, resolve_horizontal_collision, resolve_vertical_collision
from .items import Particle, Coin, AmmoPickup
from .world import Platform, Ladder, Portal
from .enemies import PatrolEnemy, ChaseEnemy
from .combat import Bullet
from .player import Player

__all__ = [
    "BaseEntity",
    "resolve_horizontal_collision",
    "resolve_vertical_collision",
    "Particle",
    "Coin",
    "AmmoPickup",
    "Platform",
    "Ladder",
    "Portal",
    "PatrolEnemy",
    "ChaseEnemy",
    "Bullet",
    "Player",
]
