# -*- coding: utf-8 -*-
"""
config.py - 游戏配置模块

集中管理所有环境变量读取、游戏常量和颜色配置，
便于统一修改和维护。

数值配置可从 game_config.json 外部文件加载，
修改数值无需改动代码。
"""

import os
import sys
import json
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


def _strip_json_comments(text):
    """
    剥离 JSON 文本中的 // 行注释，支持独立行注释和行内注释。
    
    会正确跳过字符串内部的 // （如 URL），不会被误删。
    
    Args:
        text: 原始 JSON 文本
        
    Returns:
        str: 剥离注释后的 JSON 文本
    """
    result = []
    i = 0
    length = len(text)
    while i < length:
        if text[i] == '"':
            in_string = True
            result.append(text[i])
            i += 1
            while i < length and in_string:
                if text[i] == '\\' and i + 1 < length:
                    result.append(text[i])
                    result.append(text[i + 1])
                    i += 2
                elif text[i] == '"':
                    result.append(text[i])
                    i += 1
                    in_string = False
                else:
                    result.append(text[i])
                    i += 1
        elif text[i] == '/' and i + 1 < length and text[i + 1] == '/':
            while i < length and text[i] != '\n':
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def _load_game_config():
    """
    从 game_config.json 加载游戏配置。
    
    支持 // 行注释，方便阅读和修改。
    如果文件不存在或加载失败，返回空字典，
    所有配置将使用代码中的默认值。
    
    Returns:
        dict: 解析后的配置字典
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
        return json.loads(_strip_json_comments(raw))
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return {}


_GAME_CONFIG = _load_game_config()


def _cfg(path, default):
    """
    从 JSON 配置中获取值，路径用点号分隔。
    
    例如: _cfg("player.speed", 5) 对应 JSON 中 {"player": {"speed": 5}}
    
    Args:
        path: 配置路径，用点号分隔
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    keys = path.split(".")
    val = _GAME_CONFIG
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return default
    return val


HEADLESS = get_env_bool("HEADLESS", False)
HEALTHCHECK = get_env_bool("HEALTHCHECK", False)
HEALTHCHECK_MAX_FRAMES = get_env_int("HEALTHCHECK_MAX_FRAMES", 300)


if HEADLESS:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

SCREEN_WIDTH = get_env_int("SCREEN_WIDTH", _cfg("screen.width", 960))
SCREEN_HEIGHT = get_env_int("SCREEN_HEIGHT", _cfg("screen.height", 640))
FPS = get_env_int("FPS", _cfg("screen.fps", 60))

LEVEL_WIDTH = _cfg("level.width", 3000)
PLAYER_SPAWN_X = _cfg("player.spawn_x", 100)
PLAYER_SPAWN_Y = _cfg("player.spawn_y", 400)
FALL_RESPAWN_Y = SCREEN_HEIGHT + _cfg("player.fall_respawn_y_offset", 100)

GRAVITY = _cfg("physics.gravity", 0.6)
JUMP_FORCE = _cfg("physics.jump_force", -13.5)
MOVE_SPEED = _cfg("physics.move_speed", 5)
MAX_FALL_SPEED = _cfg("physics.max_fall_speed", 15)
ACCELERATION = _cfg("physics.acceleration", 0.8)
FRICTION = _cfg("physics.friction", 0.82)

JUMP_BUFFER_FRAMES = _cfg("physics.jump_buffer_frames", 8)
COYOTE_TIME_FRAMES = _cfg("physics.coyote_time_frames", 6)
SHORT_JUMP_MULTIPLIER = _cfg("physics.short_jump_multiplier", 0.85)
SHORT_JUMP_THRESHOLD = _cfg("physics.short_jump_threshold", -2)

MAX_JUMP_COUNT = _cfg("physics.max_jump_count", 3)
MULTI_JUMP_FORCE = _cfg("physics.multi_jump_force", -11.0)
MULTI_JUMP_INTERVAL_FRAMES = _cfg("physics.multi_jump_interval_frames", 8)

LADDER_WIDTH = _cfg("ladder.width", 24)
LADDER_COLOR = (160, 120, 60)
LADDER_RUNG_COLOR = (140, 100, 40)
LADDER_RUNG_SPACING = _cfg("ladder.rung_spacing", 20)
CLIMB_SPEED = _cfg("ladder.climb_speed", 3)
SQUASH_ON_CLIMB = _cfg("ladder.squash_on_climb", 0.9)

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

PLAYER_SKIN = (255, 220, 180)
PLAYER_SKIN_DARK = (235, 195, 155)
PLAYER_SKIN_SHADOW = (210, 170, 130)
PLAYER_HAT = (210, 50, 50)
PLAYER_HAT_DARK = (170, 30, 30)
PLAYER_HAT_BAND = (100, 20, 20)
PLAYER_HAT_BRIM = (150, 35, 35)
PLAYER_SHIRT = (70, 140, 220)
PLAYER_SHIRT_DARK = (50, 105, 180)
PLAYER_SHIRT_LIGHT = (110, 180, 245)
PLAYER_PANTS = (55, 55, 90)
PLAYER_PANTS_DARK = (40, 40, 70)
PLAYER_SHOES = (45, 35, 30)
PLAYER_SHOES_LIGHT = (65, 50, 45)
PLAYER_BELT = (105, 75, 45)
PLAYER_BELT_BUCKLE = (230, 195, 90)
PLAYER_GLOVE = (90, 80, 70)
PLAYER_GLOVE_DARK = (60, 50, 45)
PLAYER_HAIR = (70, 50, 35)
PLAYER_HAIR_DARK = (50, 35, 25)
PLAYER_CHEEK = (255, 160, 160)

COIN_COLOR = (255, 215, 0)
COIN_DARK = (200, 170, 0)
COIN_COLLECT_SCORE = _cfg("coin.collect_score", 10)

PARTICLE_COLORS = [(255, 255, 200), (255, 220, 100), (200, 200, 255)]
DUST_PARTICLE_COLORS = [(180, 170, 150)]

CLOUD_COUNT = _cfg("background.cloud_count", 12)
CLOUD_COLOR = (255, 255, 255)
CLOUD_ALPHA_INNER = _cfg("background.cloud_alpha_inner", 160)
CLOUD_ALPHA_OUTER = _cfg("background.cloud_alpha_outer", 180)
CLOUD_SEED = _cfg("background.cloud_seed", 123)

MOUNTAIN_COUNT = _cfg("background.mountain_count", 8)
MOUNTAIN_COLOR = (70, 120, 80)
MOUNTAIN_SNOW_COLOR = (230, 240, 250)
MOUNTAIN_SEED = _cfg("background.mountain_seed", 456)

SQUASH_INTERPOLATION = _cfg("animation.squash_interpolation", 0.2)
SQUASH_ON_JUMP = _cfg("animation.squash_on_jump", 0.7)
SQUASH_ON_FALL = _cfg("animation.squash_on_fall", 1.2)
SQUASH_ON_LAND = _cfg("animation.squash_on_land", 1.3)
SQUASH_NORMAL = _cfg("animation.squash_normal", 1.0)

RUN_ANIM_SPEED = _cfg("animation.run_anim_speed", 0.2)
BLINK_INTERVAL = _cfg("animation.blink_interval", 180)
BLINK_DURATION = _cfg("animation.blink_duration", 4)

COIN_BOB_AMPLITUDE = _cfg("coin.bob_amplitude", 4)
COIN_COLLECT_ANIM = _cfg("coin.collect_anim_frames", 15)

PLATFORM_GRASS_SEED = _cfg("background.platform_grass_seed", 42)

CAMERA_LERP = _cfg("camera.lerp", 0.08)
CAMERA_TARGET_RATIO = _cfg("camera.target_ratio", 3)

PORTAL_WIDTH = _cfg("portal.width", 60)
PORTAL_HEIGHT = _cfg("portal.height", 90)
PORTAL_COLOR_INNER = (100, 200, 255)
PORTAL_COLOR_OUTER = (150, 230, 255)
PORTAL_COLOR_GLOW = (200, 240, 255)
PORTAL_PARTICLE_COLORS = [(100, 200, 255), (150, 230, 255), (200, 240, 255)]
PORTAL_ACTIVATION_COINS = _cfg("portal.activation_coins", 0)
PORTAL_COOLDOWN_FRAMES = _cfg("portal.cooldown_frames", 60)

TRANSITION_DURATION_FRAMES = _cfg("transition.duration_frames", 45)
TRANSITION_COLOR = (0, 0, 0)
LOADING_BAR_WIDTH = _cfg("transition.loading_bar_width", 400)
LOADING_BAR_HEIGHT = _cfg("transition.loading_bar_height", 20)
LOADING_BAR_BG = (60, 60, 80)
LOADING_BAR_FG = (100, 200, 255)
LOADING_TEXT_COLOR = (255, 255, 255)

TOTAL_LEVELS = _cfg("level.total_levels", 3)

AUDIO_SAMPLE_RATE = _cfg("audio.sample_rate", 44100)
AUDIO_BGM_VOLUME_DEFAULT = _cfg("audio.bgm_volume_default", 0.6)
AUDIO_SFX_VOLUME_DEFAULT = _cfg("audio.sfx_volume_default", 0.8)
AUDIO_BGM_FADE_MS = _cfg("audio.bgm_fade_ms", 300)

VOLUME_PANEL_X = _cfg("volume_panel.x", 20)
VOLUME_PANEL_Y = _cfg("volume_panel.y", 50)
VOLUME_PANEL_WIDTH = _cfg("volume_panel.width", 280)
VOLUME_PANEL_HEIGHT = _cfg("volume_panel.height", 150)
VOLUME_SLIDER_WIDTH = _cfg("volume_panel.slider_width", 200)
VOLUME_SLIDER_HEIGHT = _cfg("volume_panel.slider_height", 10)
VOLUME_SLIDER_KNOB_SIZE = _cfg("volume_panel.slider_knob_size", 16)
VOLUME_PANEL_BG = (40, 40, 60, 220)
VOLUME_PANEL_BORDER = (100, 150, 255)
VOLUME_SLIDER_BG = (60, 60, 80)
VOLUME_SLIDER_FG = (100, 200, 255)
VOLUME_SLIDER_KNOB = (200, 230, 255)
VOLUME_TEXT_COLOR = (255, 255, 255)

SHOW_VOLUME_PANEL_KEY = pygame.K_v

PATROL_ENEMY_WIDTH = _cfg("enemies.patrol.width", 32)
PATROL_ENEMY_HEIGHT = _cfg("enemies.patrol.height", 32)
PATROL_ENEMY_SPEED = _cfg("enemies.patrol.speed", 1.5)
PATROL_ENEMY_DETECTION_RANGE = _cfg("enemies.patrol.detection_range", 150)
PATROL_ENEMY_ALERT_SPEED_MULTIPLIER = _cfg("enemies.patrol.alert_speed_multiplier", 1.8)
PATROL_ENEMY_COLOR = (180, 60, 60)
PATROL_ENEMY_DARK = (140, 40, 40)
PATROL_ENEMY_LIGHT = (220, 100, 100)
PATROL_ENEMY_EYE = (255, 255, 100)
PATROL_ENEMY_PUPIL = (180, 50, 0)
PATROL_ENEMY_ALERT_COLOR = (255, 200, 0)

CHASE_ENEMY_WIDTH = _cfg("enemies.chase.width", 28)
CHASE_ENEMY_HEIGHT = _cfg("enemies.chase.height", 36)
CHASE_ENEMY_SPEED = _cfg("enemies.chase.speed", 2.5)
CHASE_ENEMY_CHASE_RANGE = _cfg("enemies.chase.chase_range", 200)
CHASE_ENEMY_GIVE_UP_RANGE = _cfg("enemies.chase.give_up_range", 280)
CHASE_ENEMY_COLOR = (120, 80, 160)
CHASE_ENEMY_DARK = (80, 50, 120)
CHASE_ENEMY_LIGHT = (160, 120, 200)
CHASE_ENEMY_EYE = (255, 100, 255)
CHASE_ENEMY_PUPIL = (100, 0, 100)
CHASE_ENEMY_GLOW_COLOR = (200, 100, 255)

PATROL_ENEMY_HP = _cfg("enemies.patrol.hp", 3)
CHASE_ENEMY_HP = _cfg("enemies.chase.hp", 2)

ENEMY_PARTICLE_COLORS = [(255, 100, 100), (255, 200, 100), (200, 100, 255)]

MELEE_COOLDOWN_FRAMES = _cfg("combat.melee.cooldown_frames", 20)
MELEE_RANGE = _cfg("combat.melee.range", 55)
MELEE_ARC_HALF = _cfg("combat.melee.arc_half", 60)
MELEE_DAMAGE = _cfg("combat.melee.damage", 2)
MELEE_DURATION_FRAMES = _cfg("combat.melee.duration_frames", 12)
MELEE_HIT_FRAME = _cfg("combat.melee.hit_frame", 4)
MELEE_COLOR = (220, 220, 255)
MELEE_COLOR_TIP = (255, 255, 255)
MELEE_SWING_PARTICLE_COLORS = [(200, 220, 255), (220, 240, 255), (255, 255, 255)]

RANGED_COOLDOWN_FRAMES = _cfg("combat.ranged.cooldown_frames", 15)
RANGED_AMMO_MAX = _cfg("combat.ranged.ammo_max", 30)
RANGED_AMMO_INITIAL = _cfg("combat.ranged.ammo_initial", 30)
RANGED_PROJECTILE_SPEED = _cfg("combat.ranged.projectile_speed", 12)
RANGED_PROJECTILE_SIZE = _cfg("combat.ranged.projectile_size", 4)
RANGED_DAMAGE = _cfg("combat.ranged.damage", 1)
RANGED_GRAVITY = _cfg("combat.ranged.gravity", 0.08)
RANGED_MAX_DISTANCE = _cfg("combat.ranged.max_distance", 600)
RANGED_RELOAD_FRAMES = _cfg("combat.ranged.reload_frames", 90)
RANGED_COLOR = (255, 255, 100)
RANGED_COLOR_TRAIL = (255, 200, 50)
RANGED_HIT_PARTICLE_COLORS = [(255, 255, 100), (255, 200, 50), (255, 150, 30)]
RANGED_MUZZLE_PARTICLE_COLORS = [(255, 255, 200), (255, 220, 100)]
RANGED_AMMO_PICKUP_AMOUNT = _cfg("combat.ranged.ammo_pickup_amount", 10)
AMMO_PICKUP_COLOR = (255, 255, 100)
AMMO_PICKUP_DARK = (200, 200, 50)

COMBAT_HIT_PARTICLE_COLORS = [(255, 100, 100), (255, 200, 100), (255, 255, 200)]
ENEMY_KNOCKBACK_SPEED = _cfg("enemies.knockback_speed", 6)
ENEMY_KNOCKBACK_DURATION = _cfg("enemies.knockback_duration", 10)

KNIFE_BLADE_COLOR = (220, 225, 240)
KNIFE_BLADE_HIGHLIGHT = (255, 255, 255)
KNIFE_BLADE_SHADOW = (140, 145, 165)
KNIFE_HANDLE_COLOR = (110, 75, 45)
KNIFE_HANDLE_WRAP = (160, 115, 65)
KNIFE_GUARD_COLOR = (210, 175, 80)
KNIFE_GUARD_DARK = (160, 130, 50)
KNIFE_LENGTH = _cfg("weapon_visual.knife.length", 22)
KNIFE_HANDLE_LENGTH = _cfg("weapon_visual.knife.handle_length", 9)
KNIFE_BLADE_WIDTH = _cfg("weapon_visual.knife.blade_width", 4)
KNIFE_SWING_GLOW_COLOR = (160, 200, 255)
KNIFE_SLASH_TRAIL_COLOR = (230, 240, 255)
KNIFE_IMPACT_FLASH_COLOR = (255, 255, 255)

GUN_BODY_COLOR = (55, 58, 68)
GUN_BODY_HIGHLIGHT = (95, 100, 115)
GUN_BODY_SHADOW = (35, 38, 48)
GUN_BARREL_COLOR = (40, 42, 50)
GUN_BARREL_HIGHLIGHT = (70, 75, 90)
GUN_GRIP_COLOR = (100, 70, 45)
GUN_GRIP_WRAP = (135, 95, 60)
GUN_TRIGGER_COLOR = (30, 30, 35)
GUN_BODY_LENGTH = _cfg("weapon_visual.gun.body_length", 24)
GUN_BARREL_LENGTH = _cfg("weapon_visual.gun.barrel_length", 16)
GUN_BODY_HEIGHT = _cfg("weapon_visual.gun.body_height", 8)
GUN_RECOIL_FRAMES = _cfg("weapon_visual.gun.recoil_frames", 8)
GUN_RECOIL_DISTANCE = _cfg("weapon_visual.gun.recoil_distance", 6)
MUZZLE_FLASH_COLOR = (255, 255, 200)
MUZZLE_FLASH_OUTER = (255, 180, 60)
MUZZLE_FLASH_DURATION = _cfg("weapon_visual.gun.muzzle_flash_duration", 6)
MUZZLE_FLASH_SIZE = _cfg("weapon_visual.gun.muzzle_flash_size", 20)
CASING_COLOR = (220, 180, 90)
CASING_EJECT_DISTANCE = _cfg("weapon_visual.gun.casing_eject_distance", 25)

MELEE_SLASH_GLOW_RADIUS = _cfg("combat.melee.slash_glow_radius", 40)
MELEE_SLASH_TRAIL_COUNT = _cfg("combat.melee.slash_trail_count", 10)
MELEE_IMPACT_RING_RADIUS = _cfg("combat.melee.impact_ring_radius", 28)
MELEE_IMPACT_RING_FRAMES = _cfg("combat.melee.impact_ring_frames", 12)
MELEE_SCREEN_SHAKE_FRAMES = _cfg("combat.melee.screen_shake_frames", 4)
MELEE_SCREEN_SHAKE_INTENSITY = _cfg("combat.melee.screen_shake_intensity", 3)
MELEE_SLASH_ARC_COLOR = (255, 240, 200)
MELEE_SLASH_ARC_WIDTH = _cfg("combat.melee.slash_arc_width", 5)
MELEE_SLASH_SPARK_COUNT = _cfg("combat.melee.slash_spark_count", 8)

SPEED_BOOST_BASE_MULTIPLIER = _cfg("powerups.speed_boost.base_multiplier", 1.5)
SPEED_BOOST_DURATION_FRAMES = _cfg("powerups.speed_boost.duration_frames", 480)
SPEED_BOOST_COOLDOWN_FRAMES = _cfg("powerups.speed_boost.cooldown_frames", 900)
SPEED_BOOST_COLOR = (0, 200, 255)
SPEED_BOOST_DARK = (0, 150, 200)
SPEED_BOOST_GLOW = (100, 230, 255)
SPEED_BOOST_TRAIL_COLORS = [(0, 200, 255), (100, 230, 255), (200, 245, 255)]
SPEED_BOOST_MAX_UPGRADE_LEVEL = _cfg("powerups.speed_boost.max_upgrade_level", 3)
SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT = _cfg("powerups.speed_boost.upgrade_multiplier_increment", 0.2)
SPEED_BOOST_UPGRADE_DURATION_INCREMENT = _cfg("powerups.speed_boost.upgrade_duration_increment", 120)

SHIELD_BASE_VALUE = _cfg("powerups.shield.base_value", 3)
SHIELD_DURATION_FRAMES = _cfg("powerups.shield.duration_frames", 720)
SHIELD_COOLDOWN_FRAMES = _cfg("powerups.shield.cooldown_frames", 1200)
SHIELD_COLOR = (0, 220, 120)
SHIELD_DARK = (0, 170, 90)
SHIELD_GLOW = (100, 255, 180)
SHIELD_BORDER = (0, 140, 70)
SHIELD_PARTICLE_COLORS = [(0, 220, 120), (100, 255, 180), (150, 255, 200)]
SHIELD_MAX_UPGRADE_LEVEL = _cfg("powerups.shield.max_upgrade_level", 3)
SHIELD_UPGRADE_VALUE_INCREMENT = _cfg("powerups.shield.upgrade_value_increment", 1)
SHIELD_UPGRADE_DURATION_INCREMENT = _cfg("powerups.shield.upgrade_duration_increment", 180)

WEAPON_BASE_DAMAGE_BONUS = _cfg("powerups.weapon.base_damage_bonus", 1)
WEAPON_BASE_FIRE_RATE_MULTIPLIER = _cfg("powerups.weapon.base_fire_rate_multiplier", 0.7)
WEAPON_USES_MAX = _cfg("powerups.weapon.uses_max", 20)
WEAPON_COOLDOWN_FRAMES = _cfg("powerups.weapon.cooldown_frames", 60)
WEAPON_COLOR = (255, 100, 50)
WEAPON_DARK = (200, 70, 30)
WEAPON_GLOW = (255, 150, 100)
WEAPON_SPARK_COLORS = [(255, 100, 50), (255, 150, 100), (255, 200, 150), (255, 255, 200)]
WEAPON_MAX_UPGRADE_LEVEL = _cfg("powerups.weapon.max_upgrade_level", 3)
WEAPON_UPGRADE_DAMAGE_INCREMENT = _cfg("powerups.weapon.upgrade_damage_increment", 1)
WEAPON_UPGRADE_USES_INCREMENT = _cfg("powerups.weapon.upgrade_uses_increment", 10)
WEAPON_TYPES = ["power_knife", "rapid_gun", "blast_shotgun"]
WEAPON_CURRENT_KEY = pygame.K_q

POWERUP_PICKUP_RADIUS = _cfg("powerups.pickup_radius", 14)
POWERUP_BOB_AMPLITUDE = _cfg("powerups.bob_amplitude", 5)
POWERUP_PICKUP_ANIM_FRAMES = _cfg("powerups.pickup_anim_frames", 20)
POWERUP_SAVE_FILE = "powerups_save.json"

HUD_POWERUP_ICON_SIZE = _cfg("hud.powerup_icon_size", 48)
HUD_POWERUP_ICON_MARGIN = _cfg("hud.powerup_icon_margin", 10)
HUD_POWERUP_START_X = _cfg("hud.powerup_start_x", 20)
HUD_POWERUP_START_Y_OFFSET = _cfg("hud.powerup_start_y_offset", 20)
HUD_POWERUP_BAR_HEIGHT = _cfg("hud.powerup_bar_height", 6)
HUD_POWERUP_BAR_BG = (50, 50, 70)
HUD_POWERUP_TEXT_COLOR = (255, 255, 255)
HUD_POWERUP_TOOLTIP_BG = (20, 30, 50, 230)
HUD_POWERUP_TOOLTIP_BORDER = (100, 200, 255)
HUD_POWERUP_TOOLTIP_TEXT = (255, 255, 255)
HUD_POWERUP_TRANSITION_FRAMES = _cfg("hud.powerup_transition_frames", 18)
HUD_POWERUP_HOVER_SCALE = _cfg("hud.powerup_hover_scale", 1.15)
HUD_POWERUP_GRAYSCALE_ALPHA = _cfg("hud.powerup_grayscale_alpha", 0.85)

SHIELD_COLOR_GLOW = (150, 255, 210)

FRAGILE_CRACK_DELAY_FRAMES = int(_cfg("fragile_platform.crack_delay_seconds", 2.0) * FPS)
FRAGILE_RESPAWN_COOLDOWN_FRAMES = int(_cfg("fragile_platform.respawn_cooldown_seconds", 2.0) * FPS)
FRAGILE_WARNING_FLASH_INTERVAL = _cfg("fragile_platform.warning_flash_interval_frames", 6)
FRAGILE_BREAK_ANIMATION_FRAMES = _cfg("fragile_platform.break_animation_frames", 15)
FRAGILE_PARTICLE_COUNT = _cfg("fragile_platform.particle_count", 12)

FRAGILE_PLATFORM_COLOR = (180, 140, 90)
FRAGILE_PLATFORM_TOP_COLOR = (210, 170, 110)
FRAGILE_PLATFORM_CRACK_COLOR = (120, 80, 50)
FRAGILE_PLATFORM_WARNING_COLOR = (255, 180, 60)
FRAGILE_PLATFORM_GHOST_COLOR = (160, 160, 180)
FRAGILE_PARTICLE_COLORS = [(180, 140, 90), (210, 170, 110), (140, 100, 60)]

FRAME_COUNTER = 0


_KEY_NAME_MAP = {}


def _build_key_name_map():
    """构建按键名称到 pygame 常量的映射表。"""
    for name in dir(pygame):
        if name.startswith("K_"):
            key_name = name[2:].lower()
            _KEY_NAME_MAP[key_name] = getattr(pygame, name)
    _KEY_NAME_MAP["space"] = pygame.K_SPACE
    _KEY_NAME_MAP[" "] = pygame.K_SPACE


_build_key_name_map()


def parse_key_name(key_name):
    """
    将按键名称字符串解析为 pygame 按键常量。

    支持的名称格式:
    - 单个字符: "a", "b", "1", "2"
    - 特殊按键: "space", "up", "down", "left", "right",
                "enter", "escape", "shift", "ctrl", "alt",
                "f1", "f2", 等

    Args:
        key_name: 按键名称字符串（不区分大小写）

    Returns:
        int: pygame 按键常量，解析失败返回 None
    """
    if key_name is None:
        return None
    key_name = key_name.strip().lower()
    if len(key_name) == 1:
        return _KEY_NAME_MAP.get(key_name)
    return _KEY_NAME_MAP.get(key_name)


def key_name_to_display(key_name):
    """
    将按键名称转换为用户友好的显示名称。

    Args:
        key_name: 按键名称字符串

    Returns:
        str: 用户友好的显示名称
    """
    if not key_name:
        return "未设置"
    key_name = key_name.strip().lower()
    display_map = {
        "space": "空格",
        "up": "↑",
        "down": "↓",
        "left": "←",
        "right": "→",
        "enter": "回车",
        "return": "回车",
        "escape": "ESC",
        "shift": "Shift",
        "ctrl": "Ctrl",
        "alt": "Alt",
        "tab": "Tab",
        "backspace": "退格",
        "delete": "删除",
    }
    if key_name in display_map:
        return display_map[key_name]
    if len(key_name) == 1:
        return key_name.upper()
    return key_name.upper()


def pygame_key_to_name(key_constant):
    """
    将 pygame 按键常量转换为按键名称字符串。

    Args:
        key_constant: pygame 按键常量（如 pygame.K_SPACE）

    Returns:
        str: 按键名称字符串，未知按键返回 None
    """
    for name, value in _KEY_NAME_MAP.items():
        if value == key_constant:
            return name
    return None


DEFAULT_KEY_JUMP = "space"
DEFAULT_KEY_MELEE = "j"
DEFAULT_KEY_SHOOT = "k"

KEY_JUMP_NAME = _cfg("controls.jump", DEFAULT_KEY_JUMP)
KEY_MELEE_NAME = _cfg("controls.melee", DEFAULT_KEY_MELEE)
KEY_SHOOT_NAME = _cfg("controls.shoot", DEFAULT_KEY_SHOOT)

KEY_JUMP = parse_key_name(KEY_JUMP_NAME) or pygame.K_SPACE
KEY_MELEE = parse_key_name(KEY_MELEE_NAME) or pygame.K_j
KEY_SHOOT = parse_key_name(KEY_SHOOT_NAME) or pygame.K_k


def update_key_bindings(jump_name=None, melee_name=None, shoot_name=None):
    """
    运行时更新按键绑定。

    当用户在设置中修改按键后调用此函数，动态更新全局按键常量。

    Args:
        jump_name: 跳跃按键名称（None 表示不修改）
        melee_name: 近战按键名称（None 表示不修改）
        shoot_name: 射击按键名称（None 表示不修改）
    """
    global KEY_JUMP_NAME, KEY_MELEE_NAME, KEY_SHOOT_NAME
    global KEY_JUMP, KEY_MELEE, KEY_SHOOT

    if jump_name is not None:
        KEY_JUMP_NAME = jump_name
        KEY_JUMP = parse_key_name(jump_name) or pygame.K_SPACE

    if melee_name is not None:
        KEY_MELEE_NAME = melee_name
        KEY_MELEE = parse_key_name(melee_name) or pygame.K_j

    if shoot_name is not None:
        KEY_SHOOT_NAME = shoot_name
        KEY_SHOOT = parse_key_name(shoot_name) or pygame.K_k
