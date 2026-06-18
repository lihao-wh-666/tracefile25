# -*- coding: utf-8 -*-
import os
import sys
import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pygame.init()
pygame.display.set_mode((1, 1))

from core.powerup_manager import PowerupManager
from ui import ItemIconSystem, get_chinese_font
from entities.powerups import PowerupType

pm = PowerupManager()
system = ItemIconSystem(None, pm)

print("=== 初始状态 ===")
for i, icon in enumerate(system.icons):
    print(f"图标 {i}:")
    print(f"  acquired: {icon.powerup.acquired}")
    print(f"  can_activate: {icon.powerup.can_activate}")
    print(f"  is_active: {icon.powerup.is_active}")
    print(f"  is_available: {icon.is_available}")
    print(f"  transition_progress: {icon.transition_progress}")
    print(f"  effective_alpha: {icon.effective_alpha}")
    print(f"  uses_remaining: {icon.powerup.uses_remaining}")
    print(f"  max_uses: {icon.powerup.max_uses}")

print("\n=== 设置 acquired=False 后 ===")
for icon in system.icons:
    icon.powerup.acquired = False

for i, icon in enumerate(system.icons):
    print(f"图标 {i}:")
    print(f"  acquired: {icon.powerup.acquired}")
    print(f"  can_activate: {icon.powerup.can_activate}")
    print(f"  is_active: {icon.powerup.is_active}")
    print(f"  is_available: {icon.is_available}")
    print(f"  transition_progress: {icon.transition_progress}")
    print(f"  effective_alpha: {icon.effective_alpha}")

print("\n=== 尝试手动计算像素颜色 ===")
from config import SPEED_BOOST_COLOR
icon = system.icons[0]
alpha = icon.effective_alpha
print(f"SPEED_BOOST_COLOR: {SPEED_BOOST_COLOR}")
print(f"alpha: {alpha}")

gray = int(0.299 * SPEED_BOOST_COLOR[0] + 0.587 * SPEED_BOOST_COLOR[1] + 0.114 * SPEED_BOOST_COLOR[2])
print(f"gray value: {gray}")
r = int(gray * alpha + SPEED_BOOST_COLOR[0] * (1 - alpha))
g = int(gray * alpha + SPEED_BOOST_COLOR[1] * (1 - alpha))
b = int(gray * alpha + SPEED_BOOST_COLOR[2] * (1 - alpha))
print(f"result color: ({r}, {g}, {b})")
print(f"max_diff: {max(abs(r - g), abs(g - b), abs(r - b))}")

pygame.quit()
