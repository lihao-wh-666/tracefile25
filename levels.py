"""
levels.py - 多关卡数据定义模块

集中管理所有关卡的配置数据，包括：
- 关卡名称、描述
- 地面平台和浮动平台布局
- 金币位置
- 梯子位置
- 传送门配置（同关卡区域传送 / 跨关卡传送）
- 玩家出生点
- 背景风格配置（天空颜色、山脉颜色等）
"""

from config import SCREEN_HEIGHT, PLAYER_SPAWN_X, PLAYER_SPAWN_Y


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
        sky_top: 天空顶部渐变颜色
        sky_bottom: 天空底部渐变颜色
        mountain_color: 山脉主体颜色
        mountain_snow_color: 山脉积雪颜色
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
        sky_top=(100, 180, 255),
        sky_bottom=(200, 230, 255),
        mountain_color=(70, 120, 80),
        mountain_snow_color=(230, 240, 250),
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
        self.sky_top = sky_top
        self.sky_bottom = sky_bottom
        self.mountain_color = mountain_color
        self.mountain_snow_color = mountain_snow_color


def build_level_0():
    """
    构建第 1 关：翠绿草原。

    设计特点:
    - 经典草地平台跳跃入门关卡
    - 包含 2 个同关卡区域传送门
    - 关卡末尾传送门进入第 2 关
    """
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
        (950, SCREEN_HEIGHT - 40 - 90, -1, 1820, SCREEN_HEIGHT - 40 - 38, 0),
        (2200, SCREEN_HEIGHT - 40 - 90, -1, 560, SCREEN_HEIGHT - 40 - 38, 0),
        (2900, 130, 1, 100, 400, 0),
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
        sky_top=(100, 180, 255),
        sky_bottom=(200, 230, 255),
        mountain_color=(70, 120, 80),
        mountain_snow_color=(230, 240, 250),
    )


def build_level_1():
    """
    构建第 2 关：日落沙丘。

    设计特点:
    - 暖色调沙漠风格
    - 更复杂的平台布局
    - 需要收集 5 枚金币激活终点传送门
    - 包含同关卡快速传送
    """
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
        (850, SCREEN_HEIGHT - 40 - 90, -1, 1880, SCREEN_HEIGHT - 40 - 38, 0),
        (2900, 130, 2, 100, 400, 5),
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
        sky_top=(255, 150, 80),
        sky_bottom=(255, 210, 160),
        mountain_color=(180, 100, 60),
        mountain_snow_color=(255, 220, 180),
    )


def build_level_2():
    """
    构建第 3 关：星空之巅。

    设计特点:
    - 夜晚星空风格，冷色调
    - 最高难度的平台布局
    - 需要收集 10 枚金币激活最终传送门
    - 包含多个同关卡传送捷径
    """
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
        (750, SCREEN_HEIGHT - 40 - 90, -1, 1600, SCREEN_HEIGHT - 40 - 38, 0),
        (1920, SCREEN_HEIGHT - 40 - 90, -1, 420, SCREEN_HEIGHT - 40 - 38, 0),
        (2900, 0, 0, 100, 400, 10),
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
        sky_top=(20, 20, 80),
        sky_bottom=(60, 40, 120),
        mountain_color=(40, 30, 80),
        mountain_snow_color=(200, 200, 255),
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
