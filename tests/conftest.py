# -*- coding: utf-8 -*-
"""
conftest.py - pytest 通用测试夹具配置

提供所有测试模块共享的测试夹具，包括：
- pygame 初始化和清理
- 无头模式配置
- 模拟按键状态构造器
- 通用测试数据工厂
"""

import os
import sys
import pytest

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_SPAWN_X, PLAYER_SPAWN_Y


@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    """
    会话级别的 pygame 初始化和清理夹具。

    在所有测试开始前初始化 pygame，测试结束后自动清理。
    使用无头模式避免实际创建窗口和音频设备。
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield screen
    pygame.quit()


@pytest.fixture
def screen(pygame_session):
    """获取当前测试会话的显示 Surface。"""
    return pygame_session


@pytest.fixture
def empty_keys():
    """
    创建一个空的按键状态字典，模拟没有按键按下。

    Returns:
        dict: 所有键值为 False 的字典
    """
    keys = {}
    for k in range(512):
        keys[k] = False
    keys[pygame.K_UP] = False
    keys[pygame.K_DOWN] = False
    keys[pygame.K_LEFT] = False
    keys[pygame.K_RIGHT] = False
    keys[pygame.K_SPACE] = False
    keys[pygame.K_w] = False
    keys[pygame.K_a] = False
    keys[pygame.K_s] = False
    keys[pygame.K_d] = False
    keys[pygame.K_j] = False
    keys[pygame.K_k] = False
    keys[pygame.K_r] = False
    keys[pygame.K_l] = False
    return keys


@pytest.fixture
def make_keys():
    """
    工厂夹具：创建自定义按键状态的工厂函数。

    使用方式:
        def test_example(make_keys):
            keys = make_keys(pygame.K_RIGHT, pygame.K_SPACE)
            # keys[pygame.K_RIGHT] 和 keys[pygame.K_SPACE] 为 True

    Returns:
        function: 接收任意数量按键常量，返回按键状态字典
    """
    def _make_keys(*pressed_keys):
        keys = {}
        for k in range(512):
            keys[k] = False
        keys[pygame.K_UP] = False
        keys[pygame.K_DOWN] = False
        keys[pygame.K_LEFT] = False
        keys[pygame.K_RIGHT] = False
        keys[pygame.K_SPACE] = False
        keys[pygame.K_w] = False
        keys[pygame.K_a] = False
        keys[pygame.K_s] = False
        keys[pygame.K_d] = False
        keys[pygame.K_j] = False
        keys[pygame.K_k] = False
        keys[pygame.K_r] = False
        keys[pygame.K_l] = False
        for k in pressed_keys:
            keys[k] = True
        return keys
    return _make_keys


@pytest.fixture
def make_platform():
    """
    工厂夹具：创建测试用平台对象。

    使用方式:
        def test_example(make_platform):
            plat = make_platform(0, 500, 200, 40, is_ground=True)

    Returns:
        function: 接收 x, y, w, h, is_ground 参数，返回 Platform 对象
    """
    from entities import Platform

    def _make_platform(x, y, w, h, is_ground=False):
        return Platform(x, y, w, h, is_ground)
    return _make_platform


@pytest.fixture
def sample_platforms(make_platform):
    """
    创建一组标准测试用平台，包括地面和浮动平台。"""
    ground = make_platform(0, SCREEN_HEIGHT - 40, 800, 40, is_ground=True)
    float1 = make_platform(200, 480, 120, 20)
    float2 = make_platform(400, 380, 100, 20)
    float3 = make_platform(600, 300, 120, 20)
    return [ground, float1, float2, float3]


@pytest.fixture
def make_player():
    """
    工厂夹具：创建玩家对象。

    Returns:
        function: 接收 x, y 参数，返回 Player 对象
    """
    from entities import Player

    def _make_player(x=PLAYER_SPAWN_X, y=PLAYER_SPAWN_Y):
        player = Player(x, y)
        return player
    return _make_player


@pytest.fixture
def player(make_player):
    """创建一个位于默认出生点的玩家对象。"""
    return make_player()


@pytest.fixture
def make_ladder():
    """
    工厂夹具：创建梯子对象。

    Returns:
        function: 接收 x, y, h 参数，返回 Ladder 对象
    """
    from entities import Ladder

    def _make_ladder(x, y, h):
        return Ladder(x, y, h)
    return _make_ladder


@pytest.fixture
def make_coin():
    """
    工厂夹具：创建金币对象。

    Returns:
        function: 接收 x, y 参数，返回 Coin 对象
    """
    from entities import Coin

    def _make_coin(x, y):
        return Coin(x, y)
    return _make_coin


@pytest.fixture
def make_portal():
    """
    工厂夹具：创建传送门对象。

    Returns:
        function: 创建 Portal 对象
    """
    from entities import Portal

    def _make_portal(x, y, target_level=1, tx=100, ty=400, required=0):
        return Portal(x, y, target_level, tx, ty, required)
    return _make_portal


@pytest.fixture
def make_patrol_enemy():
    """
    工厂夹具：创建巡逻怪对象。

    Returns:
        function: 创建 PatrolEnemy 对象
    """
    from entities import PatrolEnemy

    def _make_patrol(x1=500, y1=500, x2=700, y2=500, loop=False):
        path = [(x1, y1), (x2, y2)]
        return PatrolEnemy(path, loop_mode=loop)
    return _make_patrol


@pytest.fixture
def make_chase_enemy():
    """
    工厂夹具：创建追踪怪对象。

    Returns:
        function: 创建 ChaseEnemy 对象
    """
    from entities import ChaseEnemy

    def _make_chase(x, y):
        return ChaseEnemy(x, y)
    return _make_chase


@pytest.fixture
def make_bullet():
    """
    工厂夹具：创建子弹对象。

    Returns:
        function: 创建 Bullet 对象
    """
    from entities import Bullet

    def _make_bullet(x, y, vx, vy, damage=1):
        return Bullet(x, y, vx, vy, damage=damage)
    return _make_bullet


@pytest.fixture
def make_ammo_pickup():
    """
    工厂夹具：创建弹药拾取物对象。

    Returns:
        function: 创建 AmmoPickup 对象
    """
    from entities import AmmoPickup

    def _make_ammo(x, y, amount=10):
        return AmmoPickup(x, y, amount=amount)
    return _make_ammo


@pytest.fixture
def make_particle():
    """
    工厂夹具：创建粒子对象。

    Returns:
        function: 创建 Particle 对象
    """
    from entities import Particle

    def _make_particle(x, y, vx=0, vy=0, color=(255, 255, 255), life=20, size=3):
        return Particle(x, y, vx, vy, color, life, size)
    return _make_particle


@pytest.fixture
def temp_save_dir(tmp_path, monkeypatch):
    """
    临时保存目录夹具，用于 StorageManager 测试。

    将用户主目录替换为临时目录，测试结束自动清理。
    """
    monkeypatch.setattr(os.path, "expanduser", lambda _: str(tmp_path))
    return tmp_path


@pytest.fixture
def level_0_config():
    """获取第 0 关的关卡配置。"""
    from levels import get_level_config
    return get_level_config(0)


@pytest.fixture
def level_1_config():
    """获取第 1 关的关卡配置。"""
    from levels import get_level_config
    return get_level_config(1)


@pytest.fixture
def level_2_config():
    """获取第 2 关的关卡配置。"""
    from levels import get_level_config
    return get_level_config(2)
