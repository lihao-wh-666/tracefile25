# -*- coding: utf-8 -*-
import os
import sys
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
pygame.init()
pygame.display.set_mode((960, 640))

from core.powerup_manager import PowerupManager
from ui import ItemIconSystem, get_chinese_font
from entities.powerups import PowerupType, PowerupState
from config import HUD_POWERUP_GRAYSCALE_ALPHA

print(f"HUD_POWERUP_GRAYSCALE_ALPHA = {HUD_POWERUP_GRAYSCALE_ALPHA}")

pm = PowerupManager()
system = ItemIconSystem(None, pm)

# 模拟测试：设置 acquired = False
for icon in system.icons:
    icon.powerup.acquired = False

print("\n=== 所有图标状态 ===")
for i, icon in enumerate(system.icons):
    print(f"图标 {i} ({icon.display_name}):")
    p = icon.powerup
    print(f"  ptype: {p.TYPE}")
    print(f"  acquired: {p.acquired}")
    print(f"  state: {p.state}")
    print(f"  can_activate: {p.can_activate}")
    print(f"  is_active: {p.is_active}")
    print(f"  is_available: {icon.is_available}")
    print(f"  transition_progress: {icon.transition_progress}")
    print(f"  effective_alpha: {icon.effective_alpha}")

# 绘制
surf = pygame.Surface((960, 640))
font = get_chinese_font(26)
big_font = get_chinese_font(52)

# 先布局
system.on_resize(960, 640)
system.draw(surf, big_font, font)

# 取第一个图标的中心像素
icon = system.icons[0]
icon_x = icon.rect.x
icon_y = icon.rect.y
center_x = icon_x + 24
center_y = icon_y + 24
print(f"\n图标位置: ({icon_x}, {icon_y}), 中心: ({center_x}, {center_y})")

if 0 <= center_x < surf.get_width() and 0 <= center_y < surf.get_height():
    pixel = surf.get_at((center_x, center_y))
    r, g, b = pixel[:3]
    print(f"像素颜色: ({r}, {g}, {b})")
    if r > 0 or g > 0 or b > 0:
        max_diff = max(abs(r - g), abs(g - b), abs(r - b))
        print(f"max_diff: {max_diff}")
else:
    print("像素超出范围")

pygame.quit()
