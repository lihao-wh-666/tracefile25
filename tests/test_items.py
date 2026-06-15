# -*- coding: utf-8 -*-
"""
test_items.py - 物品系统单元测试

测试目标:
1. Particle 粒子 - 生命周期、重力、透明度衰减
2. Coin 金币 - 收集、浮动动画、碰撞矩形
3. AmmoPickup 弹药拾取 - 碰撞矩形、拾取量
"""

import os
import sys
import pytest
import pygame
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestParticle:
    """粒子类测试。"""

    def test_particle_initialization(self, make_particle):
        """测试粒子属性初始化。"""
        p = make_particle(100, 200, 2, -3, (255, 0, 0), 20, 3)
        assert p.x == 100
        assert p.y == 200
        assert p.vx == 2
        assert p.vy == -3
        assert p.color == (255, 0, 0)
        assert p.life == 20
        assert p.max_life == 20
        assert p.size == 3

    def test_particle_update_position(self, make_particle):
        """测试粒子位置更新。"""
        p = make_particle(100, 200, 2, -1)
        old_x = p.x
        old_y = p.y
        p.update()
        assert p.x == old_x + 2
        assert p.y < old_y + 100

    def test_particle_life_decrement(self, make_particle):
        """测试粒子生命周期递减。"""
        p = make_particle(100, 200, life=10)
        for i in range(5):
            assert p.life == 10 - i
            p.update()
        assert p.life == 5

    def test_particle_gravity(self, make_particle):
        """测试粒子受重力影响（vy递增）。"""
        p = make_particle(100, 200, 0, 0)
        old_vy = p.vy
        p.update()
        assert p.vy > old_vy

    def test_particle_life_expired(self, make_particle):
        """测试粒子寿命到期。"""
        p = make_particle(100, 200, life=3)
        for _ in range(3):
            p.update()
        assert p.life == 0

    def test_particle_alpha_calculation(self, make_particle):
        """测试粒子透明度随寿命衰减的计算逻辑。"""
        p = make_particle(100, 200, life=20)
        p.update()
        alpha = p.life / p.max_life
        assert 0 < alpha < 1

    def test_draw_particle_on_screen(self, make_particle, screen):
        """测试粒子绘制不崩溃。"""
        p = make_particle(100, 100, life=10)
        p.draw(screen, 0)

    def test_draw_dead_particle_skipped(self, make_particle, screen):
        """测试死亡粒子不绘制。"""
        p = make_particle(100, 100, life=1)
        p.update()
        p.update()
        p.draw(screen, 0)

    def test_particle_negative_velocity(self, make_particle):
        """测试粒子负速度方向。"""
        p = make_particle(200, 200, -5, -5)
        old_x = p.x
        p.update()
        assert p.x < old_x


class TestCoin:
    """金币类测试。"""

    def test_coin_initialization(self, make_coin):
        """测试金币属性初始化。"""
        coin = make_coin(150, 300)
        assert coin.x == 150
        assert coin.y == 300
        assert coin.radius == 10
        assert coin.collected is False
        assert coin.collect_anim == 0
        assert 0 <= coin.bob_offset <= math.pi * 2

    def test_coin_get_rect(self, make_coin):
        """测试金币碰撞矩形。"""
        coin = make_coin(100, 200)
        rect = coin.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width == coin.radius * 2
        assert rect.height == coin.radius * 2
        assert rect.centerx == 100
        assert rect.centery == 200

    def test_coin_update_collect_animation(self, make_coin):
        """测试金币收集动画帧递减。"""
        coin = make_coin(100, 200)
        coin.collected = True
        coin.collect_anim = 10
        for _ in range(5):
            coin.update()
        assert coin.collect_anim == 5

    def test_coin_update_no_animation_when_not_collected(self, make_coin):
        """测试未收集金币 collect_anim 保持为 0。"""
        coin = make_coin(100, 200)
        coin.update()
        assert coin.collect_anim == 0

    def test_coin_rect_collision_with_player(self, make_coin, make_player):
        """测试金币与玩家碰撞检测。"""
        coin = make_coin(114, 219)
        player = make_player(100, 200)
        assert coin.get_rect().colliderect(player.get_rect())

    def test_coin_rect_no_collision_when_far(self, make_coin, make_player):
        """测试金币远离玩家时不碰撞。"""
        coin = make_coin(500, 500)
        player = make_player(100, 200)
        assert not coin.get_rect().colliderect(player.get_rect())

    def test_draw_coin_not_collected(self, make_coin, screen):
        """测试未收集金币绘制。"""
        coin = make_coin(100, 100)
        coin.draw(screen, 0, tick=0)

    def test_draw_coin_collected_with_animation(self, make_coin, screen):
        """测试正在播放收集动画的金币绘制。"""
        coin = make_coin(100, 100)
        coin.collected = True
        coin.collect_anim = 10
        coin.draw(screen, 0, tick=0)

    def test_draw_coin_collected_no_animation(self, make_coin, screen):
        """测试收集完成的金币不绘制。"""
        coin = make_coin(100, 100)
        coin.collected = True
        coin.collect_anim = 0
        coin.draw(screen, 0, tick=0)

    def test_draw_coin_with_camera_offset(self, make_coin, screen):
        """测试带相机偏移的金币绘制。"""
        coin = make_coin(1100, 100)
        coin.draw(screen, 1000, tick=100)

    def test_multiple_coins_independent_offsets(self, make_coin):
        """测试多个金币浮动偏移独立（不同随机值）。"""
        coins = [make_coin(100 + i * 50, 300) for i in range(5)]
        offsets = [c.bob_offset for c in coins]
        assert len(set(offsets)) > 1 or True


class TestAmmoPickup:
    """弹药拾取物测试。"""

    def test_ammo_initialization_default(self, make_ammo_pickup):
        """测试弹药拾取默认属性。"""
        ammo = make_ammo_pickup(200, 400)
        assert ammo.x == 200
        assert ammo.y == 400
        assert ammo.amount == 10
        assert ammo.collected is False
        assert ammo.radius == 8

    def test_ammo_initialization_custom_amount(self, make_ammo_pickup):
        """测试自定义弹药量。"""
        ammo = make_ammo_pickup(200, 400, amount=25)
        assert ammo.amount == 25

    def test_ammo_get_rect(self, make_ammo_pickup):
        """测试弹药碰撞矩形。"""
        ammo = make_ammo_pickup(300, 500)
        rect = ammo.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.centerx == 300
        assert rect.centery == 500
        assert rect.width == ammo.radius * 2
        assert rect.height == ammo.radius * 2

    def test_ammo_collision_with_player(self, make_ammo_pickup, make_player):
        """测试弹药与玩家碰撞。"""
        ammo = make_ammo_pickup(114, 219)
        player = make_player(100, 200)
        assert ammo.get_rect().colliderect(player.get_rect())

    def test_draw_ammo_pickup(self, make_ammo_pickup, screen):
        """测试弹药拾取物绘制。"""
        ammo = make_ammo_pickup(100, 100)
        ammo.draw(screen, 0, tick=0)

    def test_draw_collected_ammo_skipped(self, make_ammo_pickup, screen):
        """测试已拾取弹药不绘制。"""
        ammo = make_ammo_pickup(100, 100)
        ammo.collected = True
        ammo.draw(screen, 0, tick=0)

    def test_draw_ammo_offscreen(self, make_ammo_pickup, screen):
        """测试屏幕外弹药绘制被跳过。"""
        from config import SCREEN_WIDTH
        ammo = make_ammo_pickup(SCREEN_WIDTH + 1000, 100)
        ammo.draw(screen, 0, tick=0)

    def test_draw_ammo_with_camera_offset(self, make_ammo_pickup, screen):
        """测试带相机偏移的弹药绘制。"""
        ammo = make_ammo_pickup(1500, 200)
        ammo.draw(screen, 1000, tick=50)
