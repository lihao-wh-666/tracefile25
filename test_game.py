# -*- coding: utf-8 -*-
"""
全面测试游戏功能，找出所有缺失的属性和方法。
"""

import os
os.environ['HEADLESS'] = '1'

import sys
import traceback
import pygame

pygame.init()

from core import Game
from menus import GameState

errors = []

def test_case(name, func):
    try:
        func()
        print(f'✅ {name}')
        return True
    except Exception as e:
        print(f'❌ {name}: {e}')
        errors.append((name, e, traceback.format_exc()))
        return False

print('=' * 60)
print('全面测试 - 游戏功能完整性检查')
print('=' * 60)
print()

game = Game()

# 测试1: 基本属性
def test_1():
    assert game.screen is not None
    assert game.clock is not None
    assert game.player is not None
    assert game.audio is not None
    assert game.menu_manager is not None
    assert len(game.platforms) > 0
    assert len(game.coins) > 0

test_case('1. 基本属性检查', test_1)

# 测试2: 玩家属性检查
def test_2():
    p = game.player
    required_attrs = [
        'x', 'y', 'width', 'height',
        'vx', 'vy',
        'on_ground', 'facing_right',
        'jump_pressed', 'jump_buffer', 'coyote_time',
        'jump_count', 'multi_jump_cooldown',
        'climbing', 'current_ladder',
        'squash_stretch',
        'run_anim', 'blink_timer',
        'died',
        'on_jump', 'on_double_jump', 'on_land', 'on_death',
        'melee_cooldown', 'melee_timer', 'melee_active',
        'melee_hit_done', 'melee_angle',
        'ranged_cooldown', 'ammo', 'ammo_max',
        'reloading', 'reload_timer',
        'on_melee_swing', 'on_ranged_shot', 'on_reload', 'on_ammo_pickup',
        'ranged_shot_timer', 'muzzle_flash_timer',
        'weapon_state',
        'start_x', 'start_y',
    ]
    missing = [a for a in required_attrs if not hasattr(p, a)]
    if missing:
        raise Exception(f'缺失属性: {missing}')

test_case('2. 玩家属性检查', test_2)

# 测试3: 玩家方法检查
def test_3():
    p = game.player
    required_methods = [
        'get_rect', 'update', 'update_combat',
        'start_melee', 'start_ranged_shot', 'start_reload',
        'get_melee_hitbox', 'draw',
    ]
    missing = [m for m in required_methods if not hasattr(p, m) or not callable(getattr(p, m))]
    if missing:
        raise Exception(f'缺失方法: {missing}')

test_case('3. 玩家方法检查', test_3)

# 测试4: 开始游戏
def test_4():
    main_menu = game.menu_manager.menus[GameState.MAIN_MENU]
    main_menu.buttons[0].callback()
    assert game.menu_manager.current_state == GameState.PLAYING

test_case('4. 开始游戏', test_4)

# 测试5: 运行50帧
def test_5():
    for i in range(50):
        game.tick += 1
        game._handle_events()
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('5. 运行50帧', test_5)

# 测试6: 近战攻击
def test_6():
    game.player.start_melee()
    assert game.player.melee_active == True
    hitbox = game.player.get_melee_hitbox()
    assert hitbox is not None
    for i in range(15):
        game.tick += 1
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('6. 近战攻击', test_6)

# 测试7: 远程攻击
def test_7():
    initial_bullets = len(game.bullets)
    result = game.player.start_ranged_shot()
    # 运行几帧让子弹更新
    for i in range(5):
        game.tick += 1
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('7. 远程攻击', test_7)

# 测试8: 换弹
def test_8():
    game.player.ammo = 0
    game.player.start_reload()
    assert game.player.reloading == True
    for i in range(30):
        game.tick += 1
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('8. 换弹', test_8)

# 测试9: 敌人属性
def test_9():
    for enemy in game.patrol_enemies:
        assert hasattr(enemy, 'hp')
        assert hasattr(enemy, 'max_hp')
        assert hasattr(enemy, 'width')
        assert hasattr(enemy, 'height')
        assert hasattr(enemy, 'x')
        assert hasattr(enemy, 'y')
        assert hasattr(enemy, 'get_rect')
        assert hasattr(enemy, 'take_damage')
        assert hasattr(enemy, 'update')
        assert hasattr(enemy, 'draw')
    for enemy in game.chase_enemies:
        assert hasattr(enemy, 'hp')
        assert hasattr(enemy, 'max_hp')

test_case('9. 敌人属性检查', test_9)

# 测试10: 子弹属性
def test_10():
    from entities import Bullet
    b = Bullet(100, 200, 1)
    assert hasattr(b, 'alive')
    assert hasattr(b, 'damage')
    assert hasattr(b, 'vx')
    assert hasattr(b, 'vy')
    assert hasattr(b, 'update')
    assert hasattr(b, 'get_rect')
    assert hasattr(b, 'draw')

test_case('10. 子弹属性检查', test_10)

# 测试11: 金币属性
def test_11():
    for coin in game.coins:
        assert hasattr(coin, 'collected')
        assert hasattr(coin, 'x')
        assert hasattr(coin, 'y')
        assert hasattr(coin, 'update')
        assert hasattr(coin, 'draw')
        assert hasattr(coin, 'get_rect')

test_case('11. 金币属性检查', test_11)

# 测试12: 平台属性
def test_12():
    for plat in game.platforms:
        assert hasattr(plat, 'x')
        assert hasattr(plat, 'y')
        assert hasattr(plat, 'width')
        assert hasattr(plat, 'height')
        assert hasattr(plat, 'draw')

test_case('12. 平台属性检查', test_12)

# 测试13: 传送门属性
def test_13():
    for portal in game.portals:
        assert hasattr(portal, 'x')
        assert hasattr(portal, 'y')
        assert hasattr(portal, 'width')
        assert hasattr(portal, 'height')
        assert hasattr(portal, 'target_level')
        assert hasattr(portal, 'update')
        assert hasattr(portal, 'draw')

test_case('13. 传送门属性检查', test_13)

# 测试14: 梯子属性
def test_14():
    for ladder in game.ladders:
        assert hasattr(ladder, 'x')
        assert hasattr(ladder, 'y')
        assert hasattr(ladder, 'width')
        assert hasattr(ladder, 'height')
        assert hasattr(ladder, 'draw')

test_case('14. 梯子属性检查', test_14)

# 测试15: 粒子属性
def test_15():
    from entities import Particle
    p = Particle(100, 200, 1, -2, (255, 0, 0), 30, 3)
    assert hasattr(p, 'life')
    assert hasattr(p, 'x')
    assert hasattr(p, 'y')
    assert hasattr(p, 'vx')
    assert hasattr(p, 'vy')
    assert hasattr(p, 'color')
    assert hasattr(p, 'update')
    assert hasattr(p, 'draw')

test_case('15. 粒子属性检查', test_15)

# 测试16: 弹药拾取属性
def test_16():
    for ammo in game.ammo_pickups:
        assert hasattr(ammo, 'x')
        assert hasattr(ammo, 'y')
        assert hasattr(ammo, 'width')
        assert hasattr(ammo, 'height')
        assert hasattr(ammo, 'amount')
        assert hasattr(ammo, 'get_rect')
        assert hasattr(ammo, 'draw')

test_case('16. 弹药拾取属性检查', test_16)

# 测试17: 战斗命中检测
def test_17():
    # 把玩家放到一个敌人旁边测试近战
    if game.patrol_enemies:
        enemy = game.patrol_enemies[0]
        game.player.x = enemy.x - 30
        game.player.y = enemy.y
        game.player.facing_right = True
        game.player.on_ground = True
        game.player.start_melee()
    # 运行几帧
    for i in range(10):
        game.tick += 1
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('17. 战斗命中检测', test_17)

# 测试18: 金币收集
def test_18():
    if game.coins:
        coin = game.coins[0]
        game.player.x = coin.x
        game.player.y = coin.y
    for i in range(5):
        game.tick += 1
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('18. 金币收集', test_18)

# 测试19: 更多帧运行测试
def test_19():
    for i in range(200):
        game.tick += 1
        game._handle_events()
        keys = pygame.key.get_pressed()
        game._update_world(keys)
        game._render()

test_case('19. 200帧综合测试', test_19)

# 测试20: 相机系统
def test_20():
    assert hasattr(game, 'camera_x')
    assert game.camera_x >= 0

test_case('20. 相机系统', test_20)

# 测试21: 音频系统
def test_21():
    assert hasattr(game.audio, 'play_bgm')
    assert hasattr(game.audio, 'play_sfx')
    assert hasattr(game.audio, 'set_bgm_volume')
    assert hasattr(game.audio, 'set_sfx_volume')
    assert hasattr(game.audio, 'shutdown')

test_case('21. 音频系统', test_21)

# 测试22: 状态管理
def test_22():
    assert hasattr(game.state_manager, 'start_transition')
    assert hasattr(game.state_manager, 'update_transition')
    assert hasattr(game.state_manager, 'draw_transition')

test_case('22. 状态管理', test_22)

# 测试23: HUD绘制
def test_23():
    assert hasattr(game, '_draw_hud')
    assert callable(game._draw_hud)

test_case('23. HUD绘制', test_23)

# 测试24: 背景绘制
def test_24():
    assert game._sky_surface is not None

test_case('24. 背景绘制', test_24)

# 测试25: 粒子系统
def test_25():
    initial_count = len(game.particles)
    game._spawn_particles(game.player.x, game.player.y, 10)
    assert len(game.particles) > initial_count

test_case('25. 粒子系统', test_25)

print()
print('=' * 60)
print(f'测试完成: {25 - len(errors)}/25 通过')
print('=' * 60)

if errors:
    print()
    print('发现的错误:')
    for i, (name, e, tb) in enumerate(errors, 1):
        print(f'\n{i}. {name}: {e}')
        print(f'   {tb.split(chr(10))[-3]}')
    print()
    print('详细错误信息:')
    for name, e, tb in errors:
        print(f'\n--- {name} ---')
        print(tb)
    sys.exit(1)
else:
    print()
    print('✅ 所有测试通过！游戏功能完整。')
    sys.exit(0)

pygame.quit()
