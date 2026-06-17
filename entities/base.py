# -*- coding: utf-8 -*-
"""
entities/base.py - 实体基础模块

提供实体类的基础工具和通用功能。
"""

import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class BaseEntity:
    """
    所有游戏实体的基类。

    定义了基本的接口和通用方法。
    """

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_rect(self):
        """返回碰撞检测矩形。"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, *args, **kwargs):
        """更新实体状态。子类必须实现此方法。"""
        raise NotImplementedError("Subclasses must implement update()")

    def draw(self, surface, camera_x, *args, **kwargs):
        """绘制实体。子类必须实现此方法。"""
        raise NotImplementedError("Subclasses must implement draw()")

    def is_visible(self, camera_x):
        """检查实体是否在屏幕可见范围内。"""
        sx = self.x - camera_x
        return (sx + self.width > -50 and sx < SCREEN_WIDTH + 50)


def _platform_is_solid(plat):
    """
    判断平台是否具有实体碰撞。

    普通 Platform 始终为实体；FragilePlatform 仅在 SOLID/CRACKING 状态为实体。
    """
    if hasattr(plat, "is_solid"):
        return plat.is_solid()
    return True


def resolve_horizontal_collision(entity, platforms):
    """
    水平方向碰撞解析。

    简单 AABB 碰撞：根据移动方向将实体推回平台边界，并清零水平速度。
    自动跳过当前处于非实体状态的易碎平台。

    Args:
        entity: 实体对象，必须有 x, y, width, height, vx 属性
        platforms: 所有平台对象列表

    Returns:
        bool: 是否发生了碰撞
    """
    collided = False
    rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
    for plat in platforms:
        if not _platform_is_solid(plat):
            continue
        if rect.colliderect(plat.rect):
            if entity.vx > 0:
                entity.x = plat.rect.left - entity.width
            elif entity.vx < 0:
                entity.x = plat.rect.right
            entity.vx = 0
            rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
            collided = True
    return collided


def resolve_vertical_collision(entity, platforms, was_on_ground=False):
    """
    垂直方向碰撞解析。

    向下碰撞（落地）：吸附到平台顶部，触发落地挤压效果，标记着地
    向上碰撞（撞头）：吸附到平台底部
    自动跳过当前处于非实体状态的易碎平台。

    Args:
        entity: 实体对象，必须有 x, y, width, height, vy 属性
        platforms: 所有平台对象列表
        was_on_ground: 上一帧是否着地（用于判断是否触发新落地特效）

    Returns:
        tuple: (on_ground, landed) - 是否在地面，是否刚刚落地
    """
    on_ground = False
    landed = False
    rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
    for plat in platforms:
        if not _platform_is_solid(plat):
            continue
        if rect.colliderect(plat.rect):
            if entity.vy >= 0:
                entity.y = plat.rect.top - entity.height
                entity.vy = 0
                if not was_on_ground and not on_ground:
                    landed = True
                on_ground = True
            elif entity.vy < 0:
                entity.y = plat.rect.bottom
                entity.vy = 0
            rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
    return on_ground, landed
