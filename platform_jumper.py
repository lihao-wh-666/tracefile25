# -*- coding: utf-8 -*-
"""
platform_jumper.py - 平台跳跃游戏主入口

使用前请确保已安装 pygame:
    pip install pygame

启动方式:
    直接运行:  python platform_jumper.py
    脚本启动:  start.bat

操作说明:
    - 方向键 ←/→ 或 A/D  左右移动
    - 空格 / ↑ / W         跳跃（支持多段跳）
    - ↑ / ↓ / W / S        攀爬梯子
    - J                     近战挥砍
    - K                     远程射击
    - R                     换弹
    - ESC                   退出游戏

支持的环境变量:
    HEADLESS=1               无头模式（不显示窗口）
    HEALTHCHECK=1            自动模拟输入进行健康检查
    HEALTHCHECK_MAX_FRAMES=N 健康检查最大帧数（默认 300）
    SCREEN_WIDTH=N           窗口宽度（默认 960）
    SCREEN_HEIGHT=N          窗口高度（默认 640）
    FPS=N                    帧率限制（默认 60）
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pygame

from config import HEADLESS, HEALTHCHECK
from core import Game


def main():
    """初始化 pygame 并启动游戏主循环。"""
    pygame.init()

    if not HEADLESS and not HEALTHCHECK:
        print("平台跳跃 启动成功！")
        print("  操作: ← → 或 A D 移动   空格/↑/W 跳跃   ↑↓攀爬   ESC 暂停/退出")

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
