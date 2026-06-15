# -*- coding: utf-8 -*-
"""
entities/player/__init__.py - 玩家模块导出

通过 Mixin 模式组合完整的 Player 类。
"""

from .base import PlayerBase
from .movement import PlayerMovementMixin
from .combat import PlayerCombatMixin
from .drawing import PlayerDrawingMixin


class Player(PlayerBase, PlayerMovementMixin, PlayerCombatMixin, PlayerDrawingMixin):
    """
    玩家角色类，通过 Mixin 模式组合实现。

    核心特性:
    - 物理：加速度 + 摩擦力的平滑移动
    - 跳跃：跳跃缓冲 + 土狼时间（增加操作容错）
    - 多段跳：空中连续跳跃，可配置最大次数和力度
    - 攀爬：与梯子交互的上下攀爬控制
    - 短跳：松开跳跃键时减速（可控制跳跃高度）
    - 视觉：挤压拉伸、跑步动画、攀爬动画、随机眨眼
    - 碰撞：水平/垂直分离解析，防止穿墙
    - 战斗：近战匕首挥砍 + 远程枪械射击
    - 音频回调：跳跃、落地、多段跳、死亡事件触发
    """

    def __init__(self, x, y):
        super().__init__(x, y)


__all__ = ["Player"]
