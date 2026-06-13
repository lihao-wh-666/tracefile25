"""
config.py - 游戏配置模块

集中管理所有环境变量读取、游戏常量和颜色配置，
便于统一修改和维护。
"""

import os
import sys
import math
import random
import pygame


def get_env_int(name, default):
    """
    从环境变量读取整数值。
    
    Args:
        name: 环境变量名称
        default: 读取失败时返回的默认值
        
    Returns:
        解析后的整数值，或默认值
    """
    try:
        return int(os.environ.get(name, default))
    except (ValueError, TypeError):
        return default


def get_env_bool(name, default=False):
    """
    从环境变量读取布尔值。
    
    识别以下字符串（不区分大小写）：
    - True: 1, true, yes, y, on
    - False: 0, false, no, n, off
    
    Args:
        name: 环境变量名称
        default: 读取失败或未匹配时返回的默认值
        
    Returns:
        解析后的布尔值，或默认值
    """
    val = os.environ.get(name, "").strip().lower()
    if val in ("1", "true", "yes", "y", "on"):
        return True
    if val in ("0", "false", "no", "n", "off"):
        return False
    return default


HEADLESS = get_env_bool("HEADLESS", False)
HEALTHCHECK = get_env_bool("HEALTHCHECK", False)
HEALTHCHECK_MAX_FRAMES = get_env_int("HEALTHCHECK_MAX_FRAMES", 300)


if HEADLESS:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

SCREEN_WIDTH = get_env_int("SCREEN_WIDTH", 960)
SCREEN_HEIGHT = get_env_int("SCREEN_HEIGHT", 640)
FPS = get_env_int("FPS", 60)

LEVEL_WIDTH = 3000
PLAYER_SPAWN_X = 100
PLAYER_SPAWN_Y = 400
FALL_RESPAWN_Y = SCREEN_HEIGHT + 100

GRAVITY = 0.6
JUMP_FORCE = -13.5
MOVE_SPEED = 5
MAX_FALL_SPEED = 15
ACCELERATION = 0.8
FRICTION = 0.82

JUMP_BUFFER_FRAMES = 8
COYOTE_TIME_FRAMES = 6
SHORT_JUMP_MULTIPLIER = 0.85
SHORT_JUMP_THRESHOLD = -2

MAX_JUMP_COUNT = 3
MULTI_JUMP_FORCE = -11.0
MULTI_JUMP_INTERVAL_FRAMES = 8

LADDER_WIDTH = 24
LADDER_COLOR = (160, 120, 60)
LADDER_RUNG_COLOR = (140, 100, 40)
LADDER_RUNG_SPACING = 20
CLIMB_SPEED = 3
SQUASH_ON_CLIMB = 0.9

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_TOP = (100, 180, 255)
SKY_BOTTOM = (200, 230, 255)
GROUND_COLOR = (80, 160, 60)
DIRT_COLOR = (120, 80, 40)
PLATFORM_COLOR = (90, 70, 50)
PLATFORM_TOP_COLOR = (70, 150, 50)
PLATFORM_HIGHLIGHT = (110, 90, 65)
GRASS_DARK = (60, 140, 40)
GRASS_LIGHT = (70, 155, 45)
GRASS_TUFT_DARK = (60, 140, 40)
GRASS_TUFT_LIGHT = (80, 165, 50)

PLAYER_BODY = (60, 120, 220)
PLAYER_DARK = (40, 80, 180)
PLAYER_LIGHT = (100, 160, 255)
PLAYER_EYE = (255, 255, 255)
PLAYER_PUPIL = (30, 30, 30)

COIN_COLOR = (255, 215, 0)
COIN_DARK = (200, 170, 0)
COIN_COLLECT_SCORE = 10

PARTICLE_COLORS = [(255, 255, 200), (255, 220, 100), (200, 200, 255)]
DUST_PARTICLE_COLORS = [(180, 170, 150)]

CLOUD_COUNT = 12
CLOUD_COLOR = (255, 255, 255)
CLOUD_ALPHA_INNER = 160
CLOUD_ALPHA_OUTER = 180
CLOUD_SEED = 123

MOUNTAIN_COUNT = 8
MOUNTAIN_COLOR = (70, 120, 80)
MOUNTAIN_SNOW_COLOR = (230, 240, 250)
MOUNTAIN_SEED = 456

SQUASH_INTERPOLATION = 0.2
SQUASH_ON_JUMP = 0.7
SQUASH_ON_FALL = 1.2
SQUASH_ON_LAND = 1.3
SQUASH_NORMAL = 1.0

RUN_ANIM_SPEED = 0.2
BLINK_INTERVAL = 180
BLINK_DURATION = 4

COIN_BOB_AMPLITUDE = 4
COIN_COLLECT_ANIM = 15

PLATFORM_GRASS_SEED = 42

CAMERA_LERP = 0.08
CAMERA_TARGET_RATIO = 3
