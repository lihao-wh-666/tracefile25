# -*- coding: utf-8 -*-
"""
test_powerups.py - 道具系统单元测试与集成测试

测试目标:
1. 加速道具 (SpeedBoostPowerup)
   - 属性初始化与升级
   - 速度加成计算
   - 激活/持续时间/冷却状态流转
   - 序列化/反序列化

2. 护盾道具 (ShieldPowerup)
   - 护盾值初始化与升级
   - 伤害吸收逻辑（完全吸收/部分吸收/完全不吸收）
   - 持续时间与冷却
   - 序列化/反序列化

3. 武器道具 (WeaponPowerup)
   - 伤害加成计算
   - 冷却缩减计算
   - 使用次数消耗逻辑
   - 武器切换
   - 序列化/反序列化

4. 统一管理接口 (PowerupManager)
   - 获取/使用/升级/销毁道具
   - 拾取物收集逻辑
   - 状态更新
   - 持久化

5. 道具拾取物 (PowerupPickup)
   - 浮动动画
   - 收集动画
   - 渲染无崩溃

6. 玩家集成测试
   - 玩家速度计算应用加速道具
   - 玩家受击应用护盾吸收
   - 攻击伤害应用武器加成
"""

import os
import sys
import json
import pytest
import pygame
import math
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from entities.powerups import (
    PowerupType, PowerupState,
    PowerupBase,
    SpeedBoostPowerup, ShieldPowerup, WeaponPowerup,
    PowerupPickup,
    create_powerup_from_type, create_powerup_from_dict,
)
from core.powerup_manager import PowerupManager
from config import (
    SPEED_BOOST_BASE_MULTIPLIER, SPEED_BOOST_DURATION_FRAMES,
    SPEED_BOOST_COOLDOWN_FRAMES, SPEED_BOOST_MAX_UPGRADE_LEVEL,
    SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT,
    SPEED_BOOST_UPGRADE_DURATION_INCREMENT,
    SHIELD_BASE_VALUE, SHIELD_DURATION_FRAMES,
    SHIELD_COOLDOWN_FRAMES, SHIELD_MAX_UPGRADE_LEVEL,
    SHIELD_UPGRADE_VALUE_INCREMENT, SHIELD_UPGRADE_DURATION_INCREMENT,
    WEAPON_BASE_DAMAGE_BONUS, WEAPON_BASE_FIRE_RATE_MULTIPLIER,
    WEAPON_USES_MAX, WEAPON_COOLDOWN_FRAMES,
    WEAPON_MAX_UPGRADE_LEVEL, WEAPON_TYPES,
    WEAPON_UPGRADE_DAMAGE_INCREMENT, WEAPON_UPGRADE_USES_INCREMENT,
    MOVE_SPEED, MELEE_DAMAGE, RANGED_DAMAGE,
    MELEE_COOLDOWN_FRAMES, RANGED_COOLDOWN_FRAMES,
    POWERUP_SAVE_FILE,
)


# ---------------------------------------------------------------------------
# 通用测试夹具
# ---------------------------------------------------------------------------

@pytest.fixture
def make_powerup():
    """工厂夹具：按类型创建道具对象。"""
    def _factory(ptype: PowerupType):
        return create_powerup_from_type(ptype)
    return _factory


@pytest.fixture
def speed_boost():
    """创建一个加速道具实例。"""
    return SpeedBoostPowerup()


@pytest.fixture
def shield():
    """创建一个护盾道具实例。"""
    return ShieldPowerup()


@pytest.fixture
def weapon():
    """创建一个武器道具实例。"""
    return WeaponPowerup()


@pytest.fixture
def powerup_manager():
    """创建一个道具管理器（game=None，用于单元测试）。"""
    return PowerupManager(game=None)


@pytest.fixture
def temp_powerup_file(tmp_path, monkeypatch):
    """临时道具存档文件夹具，避免污染真实数据。"""
    save_path = tmp_path / "test_powerups.json"
    monkeypatch.setattr("config.POWERUP_SAVE_FILE", str(save_path))
    return save_path


# ===========================================================================
# 1. 加速道具测试
# ===========================================================================

class TestSpeedBoostPowerup:
    """加速道具单元测试。"""

    def test_initial_state(self, speed_boost):
        """测试初始状态属性。"""
        assert speed_boost.TYPE == PowerupType.SPEED_BOOST
        assert speed_boost.level == 1
        assert speed_boost.state == PowerupState.IDLE
        assert speed_boost.acquired is False
        assert math.isclose(speed_boost.speed_multiplier,
                            SPEED_BOOST_BASE_MULTIPLIER)

    def test_stats_based_on_level(self):
        """测试不同等级的数值计算。"""
        for level in range(1, SPEED_BOOST_MAX_UPGRADE_LEVEL + 1):
            sb = SpeedBoostPowerup(level=level)
            expected_mult = SPEED_BOOST_BASE_MULTIPLIER + \
                SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT * (level - 1)
            expected_dur = SPEED_BOOST_DURATION_FRAMES + \
                SPEED_BOOST_UPGRADE_DURATION_INCREMENT * (level - 1)
            assert math.isclose(sb.speed_multiplier, expected_mult)
            assert sb.duration_frames == expected_dur
            assert sb.cooldown_frames == SPEED_BOOST_COOLDOWN_FRAMES

    def test_cannot_upgrade_past_max(self, speed_boost):
        """测试升级上限。"""
        for i in range(SPEED_BOOST_MAX_UPGRADE_LEVEL - 1):
            assert speed_boost.upgrade() is True
        assert speed_boost.level == SPEED_BOOST_MAX_UPGRADE_LEVEL
        assert speed_boost.upgrade() is False

    def test_activate_requires_acquired(self, speed_boost):
        """未获得的道具无法激活。"""
        speed_boost.acquired = False
        assert speed_boost.activate() is False

    def test_state_flow(self, speed_boost):
        """测试 IDLE -> ACTIVE -> COOLDOWN -> IDLE 状态流转。"""
        speed_boost.acquired = True
        assert speed_boost.state == PowerupState.IDLE
        assert speed_boost.activate() is True
        assert speed_boost.state == PowerupState.ACTIVE
        assert speed_boost.activate() is False

        for _ in range(SPEED_BOOST_DURATION_FRAMES + 10):
            speed_boost.update()
        assert speed_boost.state == PowerupState.COOLDOWN

        for _ in range(SPEED_BOOST_COOLDOWN_FRAMES + 10):
            speed_boost.update()
        assert speed_boost.state == PowerupState.IDLE

    def test_get_effective_speed(self, speed_boost):
        """测试加速后的实际速度计算。"""
        base_speed = 10.0
        inactive_speed = speed_boost.get_effective_speed(base_speed)
        assert math.isclose(inactive_speed, base_speed)

        speed_boost.acquired = True
        speed_boost.activate()
        active_speed = speed_boost.get_effective_speed(base_speed)
        expected = base_speed * SPEED_BOOST_BASE_MULTIPLIER
        assert math.isclose(active_speed, expected)

    def test_serialization_round_trip(self, speed_boost):
        """测试 to_dict / from_dict 往返。"""
        speed_boost.acquired = True
        speed_boost.level = 2
        speed_boost._compute_stats_for_level(2)
        d = speed_boost.to_dict()
        assert d["type"] == PowerupType.SPEED_BOOST.value
        assert d["level"] == 2
        assert d["acquired"] is True

        restored = create_powerup_from_dict(d)
        assert isinstance(restored, SpeedBoostPowerup)
        assert restored.level == 2
        assert restored.acquired is True
        expected_mult = (
            SPEED_BOOST_BASE_MULTIPLIER
            + SPEED_BOOST_UPGRADE_MULTIPLIER_INCREMENT
        )
        assert math.isclose(restored.speed_multiplier, expected_mult)

    def test_callbacks_triggered(self, speed_boost):
        """测试回调触发。"""
        activated = []
        deactivated = []
        speed_boost.on_activate = lambda: activated.append(True)
        speed_boost.on_deactivate = lambda: deactivated.append(True)

        speed_boost.acquired = True
        speed_boost.activate()
        assert len(activated) == 1

        for _ in range(SPEED_BOOST_DURATION_FRAMES + 10):
            speed_boost.update()
        assert len(deactivated) == 1


# ===========================================================================
# 2. 护盾道具测试
# ===========================================================================

class TestShieldPowerup:
    """护盾道具单元测试。"""

    def test_initial_state(self, shield):
        """测试初始状态。"""
        assert shield.TYPE == PowerupType.SHIELD
        assert shield.shield_value == SHIELD_BASE_VALUE
        assert shield.max_shield_value == SHIELD_BASE_VALUE
        assert shield.duration_frames == SHIELD_DURATION_FRAMES

    def test_level_up_increases_value(self):
        """测试升级增加护盾值。"""
        for level in range(1, SHIELD_MAX_UPGRADE_LEVEL + 1):
            sh = ShieldPowerup(level=level)
            expected = SHIELD_BASE_VALUE + \
                SHIELD_UPGRADE_VALUE_INCREMENT * (level - 1)
            assert sh.shield_value == expected
            assert sh.max_shield_value == expected
            assert sh.duration_frames == (
                SHIELD_DURATION_FRAMES +
                SHIELD_UPGRADE_DURATION_INCREMENT * (level - 1)
            )

    def test_absorb_full_damage(self, shield):
        """测试完全吸收伤害（激活状态）。"""
        shield.acquired = True
        shield.activate()
        shield.shield_value = 5
        remaining = shield.absorb_damage(3)
        assert remaining == 0
        assert shield.shield_value == 2

    def test_absorb_partial_damage(self, shield):
        """测试部分吸收，残余伤害返回（激活状态）。"""
        shield.acquired = True
        shield.activate()
        shield.shield_value = 2
        remaining = shield.absorb_damage(5)
        assert remaining == 3
        assert shield.shield_value == 0

    def test_no_shield_no_absorb(self, shield):
        """护盾为空时不吸收（激活状态但值为0）。"""
        shield.acquired = True
        shield.activate()
        shield.shield_value = 0
        remaining = shield.absorb_damage(3)
        assert remaining == 3

    def test_shield_not_active_no_absorb(self, shield):
        """未激活状态下护盾吸收无效果。"""
        shield.state = PowerupState.IDLE
        shield.shield_value = 5
        remaining = shield.absorb_damage(2)
        assert remaining == 2
        assert shield.shield_value == 5

    def test_activate_restores_shield(self, shield):
        """激活时护盾值重置到最大值。"""
        shield.acquired = True
        shield.shield_value = 0
        assert shield.activate() is True
        assert shield.shield_value == shield.max_shield_value

    def test_serialization(self, shield):
        """序列化往返。"""
        shield.acquired = True
        shield.level = 3
        d = shield.to_dict()
        restored = create_powerup_from_dict(d)
        assert isinstance(restored, ShieldPowerup)
        assert restored.level == 3
        assert restored.max_shield_value == shield.max_shield_value


# ===========================================================================
# 3. 武器道具测试
# ===========================================================================

class TestWeaponPowerup:
    """武器道具单元测试。"""

    def test_initial_state(self, weapon):
        """测试初始属性。"""
        assert weapon.TYPE == PowerupType.WEAPON
        assert weapon.damage_bonus == WEAPON_BASE_DAMAGE_BONUS
        assert math.isclose(weapon.fire_rate_multiplier,
                            WEAPON_BASE_FIRE_RATE_MULTIPLIER)
        assert weapon.uses_remaining == WEAPON_USES_MAX
        assert weapon.current_weapon_type == WEAPON_TYPES[0]

    def test_damage_bonus_scales_with_level(self):
        """升级增加伤害加成。"""
        for level in range(1, WEAPON_MAX_UPGRADE_LEVEL + 1):
            wp = WeaponPowerup(level=level)
            expected_bonus = WEAPON_BASE_DAMAGE_BONUS + \
                WEAPON_UPGRADE_DAMAGE_INCREMENT * (level - 1)
            expected_uses = WEAPON_USES_MAX + \
                WEAPON_UPGRADE_USES_INCREMENT * (level - 1)
            assert wp.damage_bonus == expected_bonus
            assert wp.uses_remaining == expected_uses

    def test_modified_melee_damage(self, weapon):
        """近战伤害加成计算（激活时）。"""
        base = MELEE_DAMAGE
        inactive = weapon.get_modified_melee_damage(base)
        assert inactive == base

        weapon.acquired = True
        weapon.activate()
        active = weapon.get_modified_melee_damage(base)
        assert active == base + WEAPON_BASE_DAMAGE_BONUS

    def test_modified_ranged_damage(self, weapon):
        """远程伤害加成。"""
        base = RANGED_DAMAGE
        weapon.acquired = True
        weapon.activate()
        modified = weapon.get_modified_ranged_damage(base)
        assert modified == base + WEAPON_BASE_DAMAGE_BONUS

    def test_attack_cooldown_reduction(self, weapon):
        """冷却缩减计算。"""
        base_melee_cd = MELEE_COOLDOWN_FRAMES
        base_ranged_cd = RANGED_COOLDOWN_FRAMES
        weapon.acquired = True
        weapon.activate()
        assert weapon.get_modified_attack_cooldown(
            base_melee_cd, True
        ) == int(base_melee_cd * WEAPON_BASE_FIRE_RATE_MULTIPLIER)
        assert weapon.get_modified_attack_cooldown(
            base_ranged_cd, False
        ) == int(base_ranged_cd * WEAPON_BASE_FIRE_RATE_MULTIPLIER)

    def test_consume_use(self, weapon):
        """使用次数消耗。"""
        weapon.acquired = True
        weapon.activate()
        initial = weapon.uses_remaining
        assert weapon.consume_use() is True
        assert weapon.uses_remaining == initial - 1

    def test_consume_use_depleted(self, weapon):
        """次数耗尽后不再消耗，也不应用强化。"""
        weapon.acquired = True
        weapon.activate()
        weapon.uses_remaining = 0
        assert weapon.consume_use() is False
        assert weapon.get_modified_melee_damage(MELEE_DAMAGE) == MELEE_DAMAGE

    def test_switch_weapon_type(self, weapon):
        """武器切换。"""
        initial = weapon.current_weapon_type
        switches = []
        weapon.on_switch = lambda: switches.append(True)
        result = weapon.switch_weapon_type()
        assert result is True
        assert weapon.current_weapon_type != initial
        assert len(switches) == 1
        for _ in range(len(WEAPON_TYPES) - 1):
            weapon.switch_weapon_type()
        assert weapon.current_weapon_type == initial

    def test_serialization(self, weapon):
        """序列化往返。"""
        weapon.acquired = True
        weapon.level = 2
        weapon.weapon_type_index = 1
        d = weapon.to_dict()
        restored = create_powerup_from_dict(d)
        assert isinstance(restored, WeaponPowerup)
        assert restored.level == 2
        assert restored.weapon_type_index == 1


# ===========================================================================
# 4. 道具管理器测试
# ===========================================================================

class TestPowerupManager:
    """道具管理器测试。"""

    def test_manager_creates_all_three_types(self, powerup_manager):
        """管理器初始化后创建三种道具。"""
        assert isinstance(powerup_manager.speed_boost(), SpeedBoostPowerup)
        assert isinstance(powerup_manager.shield(), ShieldPowerup)
        assert isinstance(powerup_manager.weapon(), WeaponPowerup)

    def test_acquire_new_powerup(self, powerup_manager):
        """获取新道具。"""
        assert powerup_manager.speed_boost().acquired is False
        result = powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        assert result is True
        assert powerup_manager.speed_boost().acquired is True
        assert powerup_manager.speed_boost().level == 1

    def test_acquire_existing_upgrades(self, powerup_manager):
        """重复获取会升级。"""
        powerup_manager.acquire_powerup(PowerupType.SHIELD)
        for i in range(SHIELD_MAX_UPGRADE_LEVEL - 1):
            assert powerup_manager.acquire_powerup(PowerupType.SHIELD) is True
        assert powerup_manager.shield().level == SHIELD_MAX_UPGRADE_LEVEL
        assert powerup_manager.acquire_powerup(PowerupType.SHIELD) is True
        assert powerup_manager.shield().level == SHIELD_MAX_UPGRADE_LEVEL

    def test_use_powerup(self, powerup_manager):
        """使用道具。"""
        powerup_manager.acquire_powerup(PowerupType.WEAPON)
        result = powerup_manager.use_powerup(PowerupType.WEAPON)
        assert result is True
        assert powerup_manager.weapon().is_active is True

    def test_upgrade_powerup(self, powerup_manager):
        """升级道具。"""
        powerup_manager.acquire_powerup(PowerupType.SHIELD)
        assert powerup_manager.shield().level == 1
        result = powerup_manager.upgrade_powerup(PowerupType.SHIELD)
        assert result is True
        assert powerup_manager.shield().level == 2

    def test_remove_powerup(self, powerup_manager):
        """销毁道具。"""
        powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        result = powerup_manager.remove_powerup(PowerupType.SPEED_BOOST)
        assert result is True
        assert powerup_manager.speed_boost().acquired is False
        assert powerup_manager.speed_boost().level == 1
        assert powerup_manager.speed_boost().state == PowerupState.IDLE

    def test_update_calls_all(self, powerup_manager):
        """update 调用所有道具的 update。"""
        powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        powerup_manager.use_powerup(PowerupType.SPEED_BOOST)
        initial = powerup_manager.speed_boost().active_timer
        for _ in range(10):
            powerup_manager.update()
        assert powerup_manager.speed_boost().active_timer < initial

    def test_save_and_load_round_trip(self, powerup_manager, temp_powerup_file):
        """完整的持久化往返。"""
        powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        powerup_manager.upgrade_powerup(PowerupType.SPEED_BOOST)
        powerup_manager.acquire_powerup(PowerupType.SHIELD)
        powerup_manager.upgrade_powerup(PowerupType.SHIELD)
        powerup_manager.upgrade_powerup(PowerupType.SHIELD)
        powerup_manager.acquire_powerup(PowerupType.WEAPON)
        powerup_manager.weapon().weapon_type_index = 2

        result = powerup_manager.save_to_file(str(temp_powerup_file))
        assert result is True
        assert temp_powerup_file.exists()

        pm2 = PowerupManager(game=None)
        result = pm2.load_from_file(str(temp_powerup_file))
        assert result is True
        assert pm2.speed_boost().level == 2
        assert pm2.shield().level == 3
        assert pm2.weapon().level == 1
        assert pm2.weapon().weapon_type_index == 2
        assert pm2.speed_boost().acquired is True

    def test_collect_pickup(self, powerup_manager):
        """通过拾取物获取道具。"""
        pickup = PowerupPickup(100, 100, PowerupType.SHIELD)
        assert powerup_manager.shield().acquired is False
        powerup_manager.collect_pickup(pickup)
        assert powerup_manager.shield().acquired is True


# ===========================================================================
# 5. 道具拾取物测试
# ===========================================================================

class TestPowerupPickup:
    """道具拾取物测试。"""

    @pytest.mark.parametrize("ptype", [
        PowerupType.SPEED_BOOST,
        PowerupType.SHIELD,
        PowerupType.WEAPON,
    ])
    def test_creation(self, ptype):
        """创建三种类型拾取物。"""
        pickup = PowerupPickup(100, 200, ptype)
        assert pickup.ptype == ptype
        assert pickup.x == 100
        assert pickup.y == 200
        assert pickup.collected is False

    def test_rect_collision(self):
        """碰撞矩形测试。"""
        pickup = PowerupPickup(100, 100, PowerupType.SPEED_BOOST)
        rect = pickup.get_rect()
        assert rect.collidepoint(100, 100)
        assert not rect.collidepoint(999, 999)

    def test_bob_animation(self):
        """浮动动画。"""
        pickup = PowerupPickup(100, 100, PowerupType.SHIELD)
        y0 = pickup.current_bob_y
        for _ in range(30):
            pickup.update()
        y1 = pickup.current_bob_y
        assert abs(y1 - y0) > 1e-6

    def test_collect_animation(self):
        """收集动画。"""
        pickup = PowerupPickup(100, 100, PowerupType.WEAPON)
        pickup.collected = True
        pickup.collect_anim_started = True
        start_scale = pickup.scale
        for _ in range(25):
            pickup.update()
        assert pickup.scale > start_scale
        assert pickup.collect_anim_frames <= 0

    def test_draw_no_crash(self, screen):
        """渲染不崩溃。"""
        for ptype in [PowerupType.SPEED_BOOST, PowerupType.SHIELD,
                      PowerupType.WEAPON]:
            pickup = PowerupPickup(100, 100, ptype)
            pickup.draw(screen, 0)
            pickup.collected = True
            pickup.collect_anim_started = True
            pickup.draw(screen, 0)

    def test_particle_colors(self):
        """每种类型都有独立粒子颜色。"""
        colors = set()
        for ptype in [PowerupType.SPEED_BOOST, PowerupType.SHIELD,
                      PowerupType.WEAPON]:
            colors.add(tuple(PowerupPickup(0, 0, ptype).particle_colors()[0]))
        assert len(colors) == 3


# ===========================================================================
# 6. 玩家集成测试
# ===========================================================================

class TestPlayerPowerupIntegration:
    """玩家 + 道具的集成测试。"""

    def test_player_speed_with_speed_boost(self, player, powerup_manager):
        """玩家通过加速道具获得速度提升。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)

        base_speed = player.get_effective_move_speed()
        assert base_speed == MOVE_SPEED

        powerup_manager.use_powerup(PowerupType.SPEED_BOOST)
        boosted = player.get_effective_move_speed()
        expected = MOVE_SPEED * SPEED_BOOST_BASE_MULTIPLIER
        assert math.isclose(boosted, expected)

    def test_player_shield_absorbs_damage(self, player, powerup_manager):
        """玩家受击先被护盾吸收。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.SHIELD)
        powerup_manager.use_powerup(PowerupType.SHIELD)

        initial_shield = powerup_manager.shield().shield_value
        remaining = player.apply_shield_absorption(1)
        assert remaining == 0
        assert powerup_manager.shield().shield_value == initial_shield - 1

    def test_player_shield_does_not_absorb_when_inactive(
        self, player, powerup_manager
    ):
        """未激活时不吸收。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.SHIELD)
        powerup_manager.shield().state = PowerupState.IDLE
        remaining = player.apply_shield_absorption(5)
        assert remaining == 5
        assert powerup_manager.shield().shield_value == SHIELD_BASE_VALUE

    def test_weapon_enhanced_melee_damage(self, player, powerup_manager):
        """近战伤害应用武器加成。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.WEAPON)

        base = player.get_effective_melee_damage(MELEE_DAMAGE)
        assert base == MELEE_DAMAGE

        powerup_manager.use_powerup(PowerupType.WEAPON)
        player.start_melee()
        assert player.last_melee_enhanced is True
        enhanced = player.get_melee_damage()
        assert enhanced == MELEE_DAMAGE + WEAPON_BASE_DAMAGE_BONUS

    def test_weapon_consume_use_on_attack(self, player, powerup_manager):
        """攻击消耗武器使用次数。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.WEAPON)
        powerup_manager.use_powerup(PowerupType.WEAPON)
        initial_uses = powerup_manager.weapon().uses_remaining
        player.start_melee()
        assert powerup_manager.weapon().uses_remaining == initial_uses - 1

    def test_cooldown_reduction(self, player, powerup_manager):
        """冷却缩减。"""
        player.set_powerup_manager(powerup_manager)
        powerup_manager.acquire_powerup(PowerupType.WEAPON)

        base_melee = player.get_effective_cooldown(MELEE_COOLDOWN_FRAMES, True)
        assert base_melee == MELEE_COOLDOWN_FRAMES

        powerup_manager.use_powerup(PowerupType.WEAPON)
        reduced = player.get_effective_cooldown(MELEE_COOLDOWN_FRAMES, True)
        assert reduced == int(MELEE_COOLDOWN_FRAMES * WEAPON_BASE_FIRE_RATE_MULTIPLIER)

    def test_manager_persists_across_player(
        self, player, powerup_manager
    ):
        """玩家绑定的管理器在多次操作中状态保持一致。"""
        player.set_powerup_manager(powerup_manager)
        assert player.powerup_manager is powerup_manager
        powerup_manager.acquire_powerup(PowerupType.SPEED_BOOST)
        assert player.powerup_manager.speed_boost().acquired is True


# ===========================================================================
# 7. 工厂与基础类测试
# ===========================================================================

class TestFactories:
    """工厂函数与基类测试。"""

    @pytest.mark.parametrize("ptype,expected_cls", [
        (PowerupType.SPEED_BOOST, SpeedBoostPowerup),
        (PowerupType.SHIELD, ShieldPowerup),
        (PowerupType.WEAPON, WeaponPowerup),
    ])
    def test_create_from_type(self, ptype, expected_cls):
        """按类型创建道具。"""
        p = create_powerup_from_type(ptype)
        assert isinstance(p, expected_cls)
        assert p.TYPE == ptype

    @pytest.mark.parametrize("ptype,level", [
        (PowerupType.SPEED_BOOST, 1),
        (PowerupType.SPEED_BOOST, 2),
        (PowerupType.SHIELD, 3),
        (PowerupType.WEAPON, 2),
    ])
    def test_create_from_dict(self, ptype, level):
        """从字典恢复。"""
        original = create_powerup_from_type(ptype)
        for _ in range(level - 1):
            original.upgrade()
        d = original.to_dict()
        restored = create_powerup_from_dict(d)
        assert restored.TYPE == original.TYPE
        assert restored.level == original.level

    def test_base_class_is_abstract(self):
        """基类不可直接使用。"""
        b = PowerupBase()
        with pytest.raises(NotImplementedError):
            b._compute_stats_for_level(1)

    def test_invalid_dict_returns_none(self):
        """非法字典返回 None。"""
        assert create_powerup_from_dict({}) is None
        assert create_powerup_from_dict({"type": "__invalid__"}) is None
