# -*- coding: utf-8 -*-
"""
core/combat.py - 战斗系统模块

负责游戏中所有战斗相关的碰撞检测和伤害处理。
"""

import pygame

from config import (
    COIN_COLLECT_SCORE,
    RANGED_DAMAGE as BULLET_DAMAGE, MELEE_DAMAGE,
)

PATROL_ENEMY_KILL_SCORE = 50
CHASE_ENEMY_KILL_SCORE = 100
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 38


class CombatManager:
    """
    战斗管理器。

    负责:
    - 近战攻击碰撞检测
    - 子弹碰撞检测
    - 敌人伤害处理
    - 金币收集
    - 弹药拾取
    - 传送门交互
    - 敌人碰撞伤害
    """

    def __init__(self, game):
        self.game = game

    def check_coin_collection(self):
        """检测玩家与金币的碰撞，收集金币并加分。"""
        player_rect = self.game.player.get_rect()
        remaining = []
        for coin in self.game.coins:
            coin.update()
            if coin.collected:
                continue
            coin_rect = pygame.Rect(coin.x, coin.y, coin.w, coin.h)
            if player_rect.colliderect(coin_rect):
                coin.collected = True
                self.game.score += COIN_COLLECT_SCORE
                self.game.particle_manager.spawn_coin_sparkle(
                    coin.x + coin.w / 2, coin.y + coin.h / 2
                )
                self.game.audio.play_sfx("coin")
            else:
                remaining.append(coin)
        self.game.coins = remaining

    def check_ammo_pickup(self):
        """检测玩家与弹药包的碰撞，补充弹药。"""
        player_rect = self.game.player.get_rect()
        remaining = []
        for ammo in self.game.ammo_pickups:
            ammo_rect = pygame.Rect(ammo.x, ammo.y, ammo.w, ammo.h)
            if player_rect.colliderect(ammo_rect):
                self.game.player.ammo = min(
                    self.game.player.ammo + ammo.amount,
                    self.game.player.ammo_max,
                )
                self.game.audio.play_sfx("reload")
            else:
                remaining.append(ammo)
        self.game.ammo_pickups = remaining

    def check_portal_interaction(self, keys):
        """检测玩家与传送门的交互，处理关卡切换。"""
        if not keys[pygame.K_e] and not keys[pygame.K_UP]:
            return False

        player_rect = self.game.player.get_rect()
        for portal in self.game.portals:
            portal_rect = pygame.Rect(portal.x, portal.y, portal.w, portal.h)
            if player_rect.colliderect(portal_rect):
                if self.game.score >= portal.required_coins:
                    self.game.state_manager.start_transition()
                    self.game._pending_level = {
                        "level_id": portal.target_level,
                        "spawn_x": portal.target_x,
                        "spawn_y": portal.target_y,
                    }
                    self.game.audio.play_sfx("portal")
                    return True
                else:
                    pass
        return False

    def check_melee_hit(self):
        """检测玩家近战攻击是否命中敌人。"""
        if not self.game.player.melee_active:
            return

        hitbox = self.game.player.get_melee_hitbox()
        for enemy in self.game.patrol_enemies:
            if enemy.is_dead:
                continue
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
            if hitbox.colliderect(enemy_rect):
                self._damage_enemy(enemy, MELEE_DAMAGE, self.game.player.facing)

        for enemy in self.game.chase_enemies:
            if enemy.is_dead:
                continue
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
            if hitbox.colliderect(enemy_rect):
                self._damage_enemy(enemy, MELEE_DAMAGE, self.game.player.facing)

    def check_bullet_collisions(self):
        """检测子弹与敌人、平台的碰撞。"""
        remaining_bullets = []
        for bullet in self.game.bullets:
            bullet.update(self.game.platforms)
            if bullet.dead:
                continue

            bullet_rect = pygame.Rect(
                bullet.x - bullet.radius,
                bullet.y - bullet.radius,
                bullet.radius * 2,
                bullet.radius * 2,
            )

            hit = False
            for enemy in self.game.patrol_enemies:
                if enemy.is_dead:
                    continue
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
                if bullet_rect.colliderect(enemy_rect):
                    self._damage_enemy(enemy, BULLET_DAMAGE, bullet.vx)
                    self.game.particle_manager.spawn_bullet_impact(
                        bullet.x, bullet.y, -bullet.direction
                    )
                    self.game.audio.play_sfx("hit_enemy")
                    hit = True
                    break

            if not hit:
                for enemy in self.game.chase_enemies:
                    if enemy.is_dead:
                        continue
                    enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
                    if bullet_rect.colliderect(enemy_rect):
                        self._damage_enemy(enemy, BULLET_DAMAGE, bullet.vx)
                        self.game.particle_manager.spawn_bullet_impact(
                            bullet.x, bullet.y, -bullet.direction
                        )
                        self.game.audio.play_sfx("hit_enemy")
                        hit = True
                        break

            if not hit:
                remaining_bullets.append(bullet)

        self.game.bullets = remaining_bullets

    def check_enemy_collision(self):
        """检测玩家与敌人的碰撞，处理玩家受伤。"""
        if self.game.player.invulnerable:
            return

        player_rect = self.game.player.get_rect()

        for enemy in self.game.patrol_enemies:
            if enemy.is_dead:
                continue
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
            if player_rect.colliderect(enemy_rect):
                self._player_hit(enemy)
                return

        for enemy in self.game.chase_enemies:
            if enemy.is_dead:
                continue
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.w, enemy.h)
            if player_rect.colliderect(enemy_rect):
                self._player_hit(enemy)
                return

    def _damage_enemy(self, enemy, damage, knockback_direction):
        """对敌人造成伤害并应用击退。"""
        enemy.health -= damage
        enemy.hit_flash = 10
        enemy.vx = knockback_direction * 4
        enemy.vy = -4

        if enemy.health <= 0:
            enemy.is_dead = True
            self.game.particle_manager.spawn_death_effect(
                enemy.x + enemy.w / 2,
                enemy.y + enemy.h / 2,
                color=(139, 69, 19),
            )
            enemy_type = type(enemy).__name__
            if "Patrol" in enemy_type:
                self.game.score += PATROL_ENEMY_KILL_SCORE
            else:
                self.game.score += CHASE_ENEMY_KILL_SCORE
            self.game.audio.play_sfx("enemy_death")
        else:
            self.game.audio.play_sfx("hit_enemy")

    def _player_hit(self, enemy):
        """处理玩家被敌人击中。"""
        self.game.player.invulnerable = True
        self.game.player.invuln_timer = 60

        dx = self.game.player.x - enemy.x
        self.game.player.vx = 5 if dx > 0 else -5
        self.game.player.vy = -8

        self.game.particle_manager.spawn_death_effect(
            self.game.player.x + PLAYER_WIDTH / 2,
            self.game.player.y + PLAYER_HEIGHT / 2,
            color=(255, 0, 0),
        )
        self.game.audio.play_sfx("player_death")

        self.game.player.x = self.game.player.start_x
        self.game.player.y = self.game.player.start_y
        self.game.player.vx = 0
        self.game.player.vy = 0
