# -*- coding: utf-8 -*-
"""
core 包 - 游戏核心系统

提供游戏的核心功能模块，包括：
- state: 游戏状态管理和过渡动画
- level_loader: 关卡数据加载
- background: 背景元素管理和绘制
- hud: 抬头显示
- particles: 粒子系统
- combat: 战斗系统
- game: 游戏主类

使用示例:
    from core import Game, StateManager
    from core.state import StateManager
    from core.game import Game
"""

from .state import StateManager
from .level_loader import LevelLoader
from .background import BackgroundManager
from .hud import HUDManager
from .particles import ParticleManager
from .combat import CombatManager
from .game import Game

__all__ = [
    "StateManager",
    "LevelLoader",
    "BackgroundManager",
    "HUDManager",
    "ParticleManager",
    "CombatManager",
    "Game",
]
