# -*- coding: utf-8 -*-
"""
levels.py - 多关卡数据定义模块

集中管理所有关卡的配置数据，包括：
- 关卡名称、描述
- 地面平台和浮动平台布局
- 金币位置
- 梯子位置
- 传送门配置（同关卡区域传送 / 跨关卡传送）
- 玩家出生点
- 背景风格配置（天空颜色、山脉颜色、云朵颜色、装饰元素等）

关卡数据可从 levels.json 外部文件加载，
修改关卡数据无需改动代码。
"""

import os
import json

from config import SCREEN_HEIGHT, SCREEN_WIDTH, PLAYER_SPAWN_X, PLAYER_SPAWN_Y, _strip_json_comments


def _load_levels_config():
    """
    从 levels.json 加载关卡配置。
    
    支持 // 行注释，方便阅读和修改。
    如果文件不存在或加载失败，返回空列表，
    所有关卡将使用代码中的默认值。
    
    Returns:
        list: 关卡配置字典列表
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "levels.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(_strip_json_comments(raw))
        return data.get("levels", [])
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return []


_LEVELS_JSON = _load_levels_config()


def _level_from_json(level_id):
    """
    从 JSON 配置构建 LevelConfig 对象。
    
    Args:
        level_id: 关卡编号
        
    Returns:
        LevelConfig or None: 如果 JSON 中有对应关卡则返回，否则返回 None
    """
    if not _LEVELS_JSON or level_id >= len(_LEVELS_JSON):
        return None
    
    level_data = _LEVELS_JSON[level_id]
    
    def _to_tuple_list(lst):
        return [tuple(item) for item in lst]
    
    def _to_tuple(val):
        return tuple(val)
    
    patrol_specs = []
    for patrol in level_data.get("patrol_enemy_specs", []):
        path_points = _to_tuple_list(patrol.get("path_points", []))
        loop_mode = patrol.get("loop_mode", False)
        patrol_specs.append((path_points, loop_mode))
    
    return LevelConfig(
        level_id=level_data.get("level_id", level_id),
        name=level_data.get("name", f"关卡 {level_id + 1}"),
        description=level_data.get("description", ""),
        spawn_x=level_data.get("spawn_x", PLAYER_SPAWN_X),
        spawn_y=level_data.get("spawn_y", PLAYER_SPAWN_Y),
        ground_specs=_to_tuple_list(level_data.get("ground_specs", [])),
        floating_specs=_to_tuple_list(level_data.get("floating_specs", [])),
        coin_positions=_to_tuple_list(level_data.get("coin_positions", [])),
        ladder_specs=_to_tuple_list(level_data.get("ladder_specs", [])),
        portal_specs=_to_tuple_list(level_data.get("portal_specs", [])),
        patrol_enemy_specs=patrol_specs,
        chase_enemy_specs=_to_tuple_list(level_data.get("chase_enemy_specs", [])),
        ammo_pickup_specs=_to_tuple_list(level_data.get("ammo_pickup_specs", [])),
        sky_top=_to_tuple(level_data.get("sky_top", (100, 180, 255))),
        sky_bottom=_to_tuple(level_data.get("sky_bottom", (200, 230, 255))),
        mountain_color=_to_tuple(level_data.get("mountain_color", (70, 120, 80))),
        mountain_snow_color=_to_tuple(level_data.get("mountain_snow_color", (230, 240, 250))),
        cloud_color=_to_tuple(level_data.get("cloud_color", (255, 255, 255))),
        cloud_alpha_inner=level_data.get("cloud_alpha_inner", 160),
        cloud_alpha_outer=level_data.get("cloud_alpha_outer", 180),
        has_stars=level_data.get("has_stars", False),
        star_count=level_data.get("star_count", 0),
        star_seed=level_data.get("star_seed", 0),
        has_sun=level_data.get("has_sun", False),
        sun_color=_to_tuple(level_data.get("sun_color", (255, 220, 100))),
        sun_pos=_to_tuple(level_data.get("sun_pos", (0.85, 0.15))),
        has_moon=level_data.get("has_moon", False),
        moon_color=_to_tuple(level_data.get("moon_color", (240, 240, 220))),
        moon_pos=_to_tuple(level_data.get("moon_pos", (0.85, 0.12))),
        ground_color=_to_tuple(level_data.get("ground_color", (80, 160, 60))),
        dirt_color=_to_tuple(level_data.get("dirt_color", (120, 80, 40))),
        platform_color=_to_tuple(level_data.get("platform_color", (90, 70, 50))),
        platform_top_color=_to_tuple(level_data.get("platform_top_color", (70, 150, 50))),
    )


class LevelConfig:
    """
    关卡配置数据类。

    封装单个关卡的所有可配置数据，便于 Game 类加载和切换。

    属性:
        level_id: 关卡唯一编号（从 0 开始）
        name: 关卡显示名称
        description: 关卡简短描述
        spawn_x, spawn_y: 玩家初始出生坐标
        ground_specs: 地面平台规格列表 [(x, y, w, h), ...]
        floating_specs: 浮动平台规格列表 [(x, y, w, h), ...]
        coin_positions: 金币坐标列表 [(x, y), ...]
        ladder_specs: 梯子规格列表 [(x, y, h), ...]
        portal_specs: 传送门规格列表 [(x, y, target_level, tx, ty, required_coins), ...]
        patrol_enemy_specs: 巡逻怪规格列表 [(path_points, loop_mode), ...]
        chase_enemy_specs: 追踪怪规格列表 [(x, y), ...]
        sky_top: 天空顶部渐变颜色
        sky_bottom: 天空底部渐变颜色
        mountain_color: 山脉主体颜色
        mountain_snow_color: 山脉积雪颜色
        cloud_color: 云朵颜色
        cloud_alpha_inner: 云朵内部透明度
        cloud_alpha_outer: 云朵外部透明度
        has_stars: 是否绘制星空
        star_count: 星星数量
        star_seed: 星星随机种子
        has_sun: 是否绘制太阳
        sun_color: 太阳颜色
        sun_pos: 太阳屏幕位置 (x_ratio, y_ratio)
        has_moon: 是否绘制月亮
        moon_color: 月亮颜色
        moon_pos: 月亮屏幕位置 (x_ratio, y_ratio)
        ground_color: 地面颜色
        dirt_color: 泥土颜色
        platform_color: 平台颜色
        platform_top_color: 平台顶部颜色
    """

    def __init__(
        self,
        level_id,
        name,
        description,
        spawn_x,
        spawn_y,
        ground_specs,
        floating_specs,
        coin_positions,
        ladder_specs,
        portal_specs,
        patrol_enemy_specs=None,
        chase_enemy_specs=None,
        ammo_pickup_specs=None,
        sky_top=(100, 180, 255),
        sky_bottom=(200, 230, 255),
        mountain_color=(70, 120, 80),
        mountain_snow_color=(230, 240, 250),
        cloud_color=(255, 255, 255),
        cloud_alpha_inner=160,
        cloud_alpha_outer=180,
        has_stars=False,
        star_count=0,
        star_seed=0,
        has_sun=False,
        sun_color=(255, 220, 100),
        sun_pos=(0.85, 0.15),
        has_moon=False,
        moon_color=(240, 240, 220),
        moon_pos=(0.85, 0.12),
        ground_color=(80, 160, 60),
        dirt_color=(120, 80, 40),
        platform_color=(90, 70, 50),
        platform_top_color=(70, 150, 50),
    ):
        self.level_id = level_id
        self.name = name
        self.description = description
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.ground_specs = ground_specs
        self.floating_specs = floating_specs
        self.coin_positions = coin_positions
        self.ladder_specs = ladder_specs
        self.portal_specs = portal_specs
        self.patrol_enemy_specs = patrol_enemy_specs if patrol_enemy_specs is not None else []
        self.chase_enemy_specs = chase_enemy_specs if chase_enemy_specs is not None else []
        self.ammo_pickup_specs = ammo_pickup_specs if ammo_pickup_specs is not None else []
        self.sky_top = sky_top
        self.sky_bottom = sky_bottom
        self.mountain_color = mountain_color
        self.mountain_snow_color = mountain_snow_color
        self.cloud_color = cloud_color
        self.cloud_alpha_inner = cloud_alpha_inner
        self.cloud_alpha_outer = cloud_alpha_outer
        self.has_stars = has_stars
        self.star_count = star_count
        self.star_seed = star_seed
        self.has_sun = has_sun
        self.sun_color = sun_color
        self.sun_pos = sun_pos
        self.has_moon = has_moon
        self.moon_color = moon_color
        self.moon_pos = moon_pos
        self.ground_color = ground_color
        self.dirt_color = dirt_color
        self.platform_color = platform_color
        self.platform_top_color = platform_top_color


def build_level_0():
    """
    构建第 1 关：翠绿草原。

    设计特点:
    - 经典草地平台跳跃入门关卡
    - 传送门 1：传送至高空浮台区域 (x≈2040, 高空)
    - 传送门 2：传送至中段浮台区域 (x≈1390, 中层)
    - 关卡末尾传送门进入第 2 关
    
    优先从 levels.json 加载配置，JSON 中不存在时使用代码默认值。
    """
    json_level = _level_from_json(0)
    if json_level is not None:
        return json_level
    
    ground_specs = [
        (0, SCREEN_HEIGHT - 40, 400, 40),
        (500, SCREEN_HEIGHT - 40, 300, 40),
        (900, SCREEN_HEIGHT - 40, 250, 40),
        (1250, SCREEN_HEIGHT - 40, 400, 40),
        (1800, SCREEN_HEIGHT - 40, 200, 40),
        (2100, SCREEN_HEIGHT - 40, 350, 40),
        (2550, SCREEN_HEIGHT - 40, 450, 40),
    ]
    floating_specs = [
        (150, 480, 100, 20),
        (320, 410, 90, 20),
        (500, 350, 110, 20),
        (680, 430, 80, 20),
        (850, 340, 100, 20),
        (1000, 260, 90, 20),
        (1180, 380, 80, 20),
        (1350, 300, 110, 20),
        (1550, 230, 90, 20),
        (1700, 350, 80, 20),
        (1850, 280, 100, 20),
        (2000, 200, 90, 20),
        (2200, 330, 110, 20),
        (2400, 250, 80, 20),
        (2600, 180, 100, 20),
        (2780, 300, 90, 20),
        (2900, 220, 110, 20),
    ]
    coin_positions = [
        (200, 450), (360, 380), (540, 320), (720, 400),
        (890, 310), (1040, 230), (1220, 350), (1390, 270),
        (1590, 200), (1740, 320), (1890, 250), (2040, 170),
        (2240, 300), (2440, 220), (2640, 150), (2820, 270),
        (2940, 190),
    ]
    ladder_specs = [
        (440, 350, 250),
        (850, 260, 340),
        (1300, 300, 300),
        (1750, 280, 320),
        (2150, 250, 350),
        (2650, 180, 420),
    ]
    portal_specs = [
        (950, SCREEN_HEIGHT - 40 - 90, -1, 1600, 210, 0),
        (2200, SCREEN_HEIGHT - 40 - 90, -1, 2600, 130, 0),
        (2900, 130, 1, 100, 400, 0),
    ]
    patrol_enemy_specs = [
        (
            [(520, SCREEN_HEIGHT - 40 - 32), (780, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(1280, SCREEN_HEIGHT - 40 - 32), (1620, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(2150, SCREEN_HEIGHT - 40 - 32), (2450, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
    ]
    chase_enemy_specs = [
        (1000, 200),
        (2300, 180),
    ]
    ammo_pickup_specs = [
        (700, 400), (1400, 260), (2100, 320), (2700, 170),
    ]
    return LevelConfig(
        level_id=0,
        name="翠绿草原",
        description="第一关：探索广阔的翠绿草原",
        spawn_x=PLAYER_SPAWN_X,
        spawn_y=PLAYER_SPAWN_Y,
        ground_specs=ground_specs,
        floating_specs=floating_specs,
        coin_positions=coin_positions,
        ladder_specs=ladder_specs,
        portal_specs=portal_specs,
        patrol_enemy_specs=patrol_enemy_specs,
        chase_enemy_specs=chase_enemy_specs,
        ammo_pickup_specs=ammo_pickup_specs,
        sky_top=(100, 180, 255),
        sky_bottom=(200, 230, 255),
        mountain_color=(70, 120, 80),
        mountain_snow_color=(230, 240, 250),
        cloud_color=(255, 255, 255),
        cloud_alpha_inner=160,
        cloud_alpha_outer=180,
        has_sun=True,
        sun_color=(255, 230, 100),
        sun_pos=(0.85, 0.12),
        ground_color=(80, 160, 60),
        dirt_color=(120, 80, 40),
        platform_color=(90, 70, 50),
        platform_top_color=(70, 150, 50),
    )


def build_level_1():
    """
    构建第 2 关：日落沙丘。

    设计特点:
    - 暖色调沙漠风格
    - 更复杂的平台布局
    - 传送门 1：传送至高空浮台区域 (x≈1640, 高空)
    - 需要收集 5 枚金币激活终点传送门
    
    优先从 levels.json 加载配置，JSON 中不存在时使用代码默认值。
    """
    json_level = _level_from_json(1)
    if json_level is not None:
        return json_level
    
    ground_specs = [
        (0, SCREEN_HEIGHT - 40, 350, 40),
        (450, SCREEN_HEIGHT - 40, 250, 40),
        (800, SCREEN_HEIGHT - 40, 200, 40),
        (1100, SCREEN_HEIGHT - 40, 300, 40),
        (1500, SCREEN_HEIGHT - 40, 250, 40),
        (1850, SCREEN_HEIGHT - 40, 200, 40),
        (2150, SCREEN_HEIGHT - 40, 300, 40),
        (2550, SCREEN_HEIGHT - 40, 450, 40),
    ]
    floating_specs = [
        (120, 500, 80, 20),
        (260, 420, 90, 20),
        (420, 340, 80, 20),
        (580, 280, 100, 20),
        (760, 380, 90, 20),
        (920, 300, 80, 20),
        (1080, 230, 100, 20),
        (1260, 330, 80, 20),
        (1420, 250, 90, 20),
        (1600, 180, 100, 20),
        (1780, 300, 80, 20),
        (1950, 220, 90, 20),
        (2120, 150, 80, 20),
        (2300, 280, 100, 20),
        (2480, 200, 90, 20),
        (2680, 300, 80, 20),
        (2850, 220, 100, 20),
    ]
    coin_positions = [
        (160, 470), (300, 390), (460, 310), (620, 250),
        (800, 350), (960, 270), (1120, 200), (1300, 300),
        (1460, 220), (1640, 150), (1820, 270), (1990, 190),
        (2160, 120), (2340, 250), (2520, 170), (2720, 270),
        (2890, 190),
    ]
    ladder_specs = [
        (390, 340, 260),
        (750, 280, 320),
        (1150, 230, 370),
        (1550, 180, 420),
        (2000, 220, 380),
        (2500, 200, 400),
    ]
    portal_specs = [
        (850, SCREEN_HEIGHT - 40 - 90, -1, 1640, 142, 0),
        (2900, 130, 2, 100, 400, 5),
    ]
    patrol_enemy_specs = [
        (
            [(470, SCREEN_HEIGHT - 40 - 32), (680, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(1120, SCREEN_HEIGHT - 40 - 32), (1380, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(1880, SCREEN_HEIGHT - 40 - 32), (2400, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(2600, SCREEN_HEIGHT - 40 - 32), (2950, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
    ]
    chase_enemy_specs = [
        (900, 250),
        (1500, 150),
        (2500, 200),
    ]
    ammo_pickup_specs = [
        (600, 350), (1200, 290), (1800, 260), (2500, 170),
    ]
    return LevelConfig(
        level_id=1,
        name="日落沙丘",
        description="第二关：穿越金色的沙漠地带",
        spawn_x=PLAYER_SPAWN_X,
        spawn_y=PLAYER_SPAWN_Y,
        ground_specs=ground_specs,
        floating_specs=floating_specs,
        coin_positions=coin_positions,
        ladder_specs=ladder_specs,
        portal_specs=portal_specs,
        patrol_enemy_specs=patrol_enemy_specs,
        chase_enemy_specs=chase_enemy_specs,
        ammo_pickup_specs=ammo_pickup_specs,
        sky_top=(255, 140, 60),
        sky_bottom=(255, 200, 140),
        mountain_color=(200, 130, 70),
        mountain_snow_color=(255, 220, 170),
        cloud_color=(255, 200, 150),
        cloud_alpha_inner=120,
        cloud_alpha_outer=150,
        has_sun=True,
        sun_color=(255, 180, 50),
        sun_pos=(0.5, 0.18),
        ground_color=(210, 170, 90),
        dirt_color=(180, 140, 70),
        platform_color=(160, 110, 60),
        platform_top_color=(210, 170, 90),
    )


def build_level_2():
    """
    构建第 3 关：星空之巅。

    设计特点:
    - 夜晚星空风格，冷色调
    - 最高难度的平台布局
    - 传送门 1：传送至极高浮台 (x≈1940, 极高空)
    - 传送门 2：传送至中段浮台 (x≈1140, 中层)
    - 需要收集 10 枚金币激活最终传送门
    
    优先从 levels.json 加载配置，JSON 中不存在时使用代码默认值。
    """
    json_level = _level_from_json(2)
    if json_level is not None:
        return json_level
    
    ground_specs = [
        (0, SCREEN_HEIGHT - 40, 300, 40),
        (400, SCREEN_HEIGHT - 40, 200, 40),
        (700, SCREEN_HEIGHT - 40, 180, 40),
        (980, SCREEN_HEIGHT - 40, 220, 40),
        (1300, SCREEN_HEIGHT - 40, 180, 40),
        (1580, SCREEN_HEIGHT - 40, 200, 40),
        (1880, SCREEN_HEIGHT - 40, 250, 40),
        (2230, SCREEN_HEIGHT - 40, 200, 40),
        (2530, SCREEN_HEIGHT - 40, 470, 40),
    ]
    floating_specs = [
        (100, 500, 70, 20),
        (220, 420, 80, 20),
        (360, 340, 70, 20),
        (500, 270, 90, 20),
        (660, 360, 70, 20),
        (800, 280, 80, 20),
        (950, 200, 70, 20),
        (1100, 300, 90, 20),
        (1260, 220, 70, 20),
        (1420, 150, 80, 20),
        (1580, 280, 70, 20),
        (1740, 200, 90, 20),
        (1900, 130, 70, 20),
        (2060, 260, 80, 20),
        (2220, 180, 70, 20),
        (2380, 110, 90, 20),
        (2560, 240, 70, 20),
        (2720, 160, 80, 20),
        (2880, 90, 90, 20),
    ]
    coin_positions = [
        (135, 470), (260, 390), (395, 310), (545, 240),
        (695, 330), (840, 250), (985, 170), (1145, 270),
        (1295, 190), (1460, 120), (1615, 250), (1785, 170),
        (1935, 100), (2100, 230), (2255, 150), (2425, 80),
        (2595, 210), (2760, 130), (2925, 60),
    ]
    ladder_specs = [
        (340, 340, 260),
        (680, 270, 330),
        (1040, 200, 400),
        (1440, 150, 450),
        (1800, 200, 400),
        (2200, 180, 420),
        (2600, 240, 360),
    ]
    portal_specs = [
        (750, SCREEN_HEIGHT - 40 - 90, -1, 1500, 120, 0),
        (1920, SCREEN_HEIGHT - 40 - 90, -1, 2400, 80, 0),
        (2900, 0, 0, 100, 400, 10),
    ]
    patrol_enemy_specs = [
        (
            [(420, SCREEN_HEIGHT - 40 - 32), (680, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(1000, SCREEN_HEIGHT - 40 - 32), (1480, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(1600, SCREEN_HEIGHT - 40 - 32), (2100, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
        (
            [(2250, SCREEN_HEIGHT - 40 - 32), (2950, SCREEN_HEIGHT - 40 - 32)],
            False,
        ),
    ]
    chase_enemy_specs = [
        (700, 280),
        (1300, 180),
        (2000, 150),
        (2700, 200),
    ]
    ammo_pickup_specs = [
        (500, 250), (1000, 270), (1600, 250), (2200, 160), (2800, 130),
    ]
    return LevelConfig(
        level_id=2,
        name="星空之巅",
        description="第三关：攀登神秘的星空之巅",
        spawn_x=PLAYER_SPAWN_X,
        spawn_y=PLAYER_SPAWN_Y,
        ground_specs=ground_specs,
        floating_specs=floating_specs,
        coin_positions=coin_positions,
        ladder_specs=ladder_specs,
        portal_specs=portal_specs,
        patrol_enemy_specs=patrol_enemy_specs,
        chase_enemy_specs=chase_enemy_specs,
        ammo_pickup_specs=ammo_pickup_specs,
        sky_top=(10, 10, 40),
        sky_bottom=(30, 20, 80),
        mountain_color=(30, 20, 60),
        mountain_snow_color=(180, 180, 230),
        cloud_color=(80, 70, 120),
        cloud_alpha_inner=80,
        cloud_alpha_outer=100,
        has_stars=True,
        star_count=80,
        star_seed=789,
        has_moon=True,
        moon_color=(240, 240, 210),
        moon_pos=(0.82, 0.1),
        ground_color=(40, 35, 60),
        dirt_color=(30, 25, 50),
        platform_color=(60, 50, 90),
        platform_top_color=(80, 70, 120),
    )


LEVEL_BUILDERS = [build_level_0, build_level_1, build_level_2]


def get_level_config(level_id):
    """
    根据关卡编号获取关卡配置对象。

    Args:
        level_id: 关卡编号（0 到 TOTAL_LEVELS-1）

    Returns:
        LevelConfig: 对应关卡的配置数据，超出范围时循环返回
    """
    level_id = level_id % len(LEVEL_BUILDERS)
    return LEVEL_BUILDERS[level_id]()
