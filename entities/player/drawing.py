# -*- coding: utf-8 -*-
"""
entities/player/drawing.py - 玩家绘制模块

提供玩家角色的完整绘制功能，包括身体各部位、武器和特效。
作为 Mixin 类使用，与 PlayerBase 和其他 Mixin 组合。
"""

import math
import pygame

from config import (
    SCREEN_WIDTH,
    SQUASH_INTERPOLATION, SQUASH_ON_CLIMB,
    PLAYER_BODY, PLAYER_DARK, PLAYER_LIGHT, PLAYER_EYE, PLAYER_PUPIL,
    PLAYER_SKIN, PLAYER_SKIN_DARK, PLAYER_SKIN_SHADOW,
    PLAYER_HAT, PLAYER_HAT_DARK, PLAYER_HAT_BAND, PLAYER_HAT_BRIM,
    PLAYER_SHIRT, PLAYER_SHIRT_DARK, PLAYER_SHIRT_LIGHT,
    PLAYER_PANTS, PLAYER_PANTS_DARK,
    PLAYER_SHOES, PLAYER_SHOES_LIGHT,
    PLAYER_BELT, PLAYER_BELT_BUCKLE,
    PLAYER_GLOVE, PLAYER_GLOVE_DARK,
    PLAYER_HAIR, PLAYER_HAIR_DARK, PLAYER_CHEEK,
    MELEE_DURATION_FRAMES, MELEE_ARC_HALF, MELEE_RANGE,
    MELEE_COLOR, MELEE_COLOR_TIP,
    RANGED_RELOAD_FRAMES, RANGED_COLOR,
    KNIFE_BLADE_COLOR, KNIFE_BLADE_HIGHLIGHT, KNIFE_BLADE_SHADOW,
    KNIFE_HANDLE_COLOR, KNIFE_HANDLE_WRAP,
    KNIFE_GUARD_COLOR, KNIFE_GUARD_DARK, KNIFE_LENGTH,
    KNIFE_HANDLE_LENGTH, KNIFE_BLADE_WIDTH,
    KNIFE_SWING_GLOW_COLOR, KNIFE_SLASH_TRAIL_COLOR,
    KNIFE_IMPACT_FLASH_COLOR,
    GUN_BODY_COLOR, GUN_BODY_HIGHLIGHT, GUN_BODY_SHADOW,
    GUN_BARREL_COLOR, GUN_BARREL_HIGHLIGHT,
    GUN_GRIP_COLOR, GUN_GRIP_WRAP, GUN_TRIGGER_COLOR,
    GUN_BODY_LENGTH, GUN_BARREL_LENGTH, GUN_BODY_HEIGHT,
    GUN_RECOIL_FRAMES, GUN_RECOIL_DISTANCE,
    MUZZLE_FLASH_COLOR, MUZZLE_FLASH_OUTER,
    MUZZLE_FLASH_DURATION, MUZZLE_FLASH_SIZE,
    CASING_COLOR, CASING_EJECT_DISTANCE,
    MELEE_SLASH_GLOW_RADIUS, MELEE_SLASH_TRAIL_COUNT,
    MELEE_IMPACT_RING_RADIUS, MELEE_IMPACT_RING_FRAMES,
    MELEE_SCREEN_SHAKE_FRAMES, MELEE_SCREEN_SHAKE_INTENSITY,
    MELEE_SLASH_ARC_COLOR, MELEE_SLASH_ARC_WIDTH,
    MELEE_SLASH_SPARK_COUNT,
)


class PlayerDrawingMixin:
    """
    玩家绘制 Mixin 类。

    提供以下功能:
    - 完整的角色绘制（头部、身体、四肢）
    - 武器绘制（匕首、枪支）
    - 战斗特效绘制（挥砍光晕、枪口火焰）
    - 动画状态处理（跑步、攀爬、跳跃挤压）
    """

    def draw(self, surface, camera_x):
        """
        绘制玩家角色（像素风格冒险者）。

        角色结构（从上到下）：
        1. 帽子（红色棒球帽）
        2. 头发（两侧棕色）
        3. 脸部（肤色，带眼睛、脸颊）
        4. 身体（蓝色衬衫 + 棕色腰带）
        5. 手臂（持武器）
        6. 腿（深蓝色裤子 + 棕色鞋子）

        Args:
            surface: 目标绘制 Surface
            camera_x: 相机水平偏移量
        """
        sx = self.x - camera_x
        sy = self.y

        if self.climbing:
            self.squash_stretch += (
                SQUASH_ON_CLIMB - self.squash_stretch
            ) * SQUASH_INTERPOLATION

        stretch_x = 1 / self.squash_stretch
        stretch_y = self.squash_stretch

        cx = sx + self.width / 2
        cy = sy + self.height / 2

        if self.climbing:
            sway = math.sin(self.climb_anim) * 2
            cx += sway

        direction = 1 if self.facing_right else -1

        head_y = sy + 8
        head_r = 7
        head_cx = cx

        neck_y = head_y + head_r + 2

        body_top = neck_y + 3
        body_bottom = sy + self.height - 10
        body_left = cx - 9
        body_right = cx + 9
        body_w = body_right - body_left

        belt_y = body_top + 11
        belt_h = 3

        pants_top = belt_y + belt_h
        pants_bottom = sy + self.height - 6

        shoe_top = pants_bottom
        shoe_bottom = sy + self.height

        if self.on_ground and abs(self.vx) > 0.5:
            leg_swing = math.sin(self.run_anim) * 4
            leg1_off = leg_swing
            leg2_off = -leg_swing
        else:
            leg1_off = 0
            leg2_off = 0

        if not self.on_ground and self.vy < 0:
            leg1_off = -1
            leg2_off = 2

        left_leg_x = cx - 4 + leg1_off * 0.5
        right_leg_x = cx + 4 + leg2_off * 0.5

        arm_shoulder_y = body_top + 4
        front_arm_x = body_right + 2
        back_arm_x = body_left - 2

        front_arm_offset_x = 0
        back_arm_offset_x = 0

        if self.climbing:
            climb_arm = math.sin(self.climb_anim * 2) * 5
            front_arm_y = arm_shoulder_y + climb_arm
            back_arm_y = arm_shoulder_y - climb_arm
        else:
            front_arm_y = arm_shoulder_y
            back_arm_y = arm_shoulder_y
            if self.on_ground and abs(self.vx) > 0.5:
                arm_swing_y = math.sin(self.run_anim + math.pi) * 3
                arm_swing_x = math.sin(self.run_anim + math.pi) * 2
                front_arm_y += arm_swing_y
                front_arm_offset_x = -arm_swing_x * direction
                back_arm_y -= arm_swing_y
                back_arm_offset_x = arm_swing_x * direction

        self._draw_back_arm(surface, back_arm_x + back_arm_offset_x, back_arm_y, direction)

        self._draw_legs(surface, left_leg_x, right_leg_x, pants_top, pants_bottom, shoe_top, shoe_bottom)

        self._draw_body(surface, body_left, body_right, body_top, body_bottom, belt_y, belt_h, cx)

        self._draw_head(surface, head_cx, head_y, head_r, direction)

        knife_hand_x = front_arm_x + front_arm_offset_x + 2
        knife_hand_y = front_arm_y + 5
        base_angle = 0 if self.facing_right else math.pi

        self._draw_front_arm(surface, front_arm_x, front_arm_y, knife_hand_x, knife_hand_y, direction)

        if self.weapon_state == "knife":
            if self.melee_active:
                progress = 1.0 - self.melee_timer / MELEE_DURATION_FRAMES
                swing_start = base_angle + math.radians(-MELEE_ARC_HALF * 0.55)
                swing_end = base_angle + math.radians(MELEE_ARC_HALF * 0.55)
                knife_angle = swing_start + (swing_end - swing_start) * progress
                self._draw_knife(surface, knife_hand_x, knife_hand_y, knife_angle, camera_x)
                self._draw_melee_effects(surface, camera_x, None, progress, base_angle, direction)
            else:
                rest_angle = math.radians(direction * 30)
                knife_angle = base_angle + rest_angle
                self._draw_knife(surface, knife_hand_x, knife_hand_y, knife_angle, camera_x)

        if not self.climbing and self.weapon_state == "gun":
            if self.melee_active:
                gun_angle = base_angle + math.radians(direction * 60)
                self._draw_gun(surface, knife_hand_x, knife_hand_y + 4, gun_angle, direction, camera_x)
            else:
                gun_angle = base_angle + math.radians(direction * 10)
                self._draw_gun(surface, knife_hand_x, knife_hand_y, gun_angle, direction, camera_x)

        if self.muzzle_flash_timer > 0 and not self.climbing and self.weapon_state == "gun":
            if self.melee_active:
                muzzle_angle = base_angle + math.radians(direction * 60)
            else:
                muzzle_angle = base_angle + math.radians(direction * 10)
            self._draw_muzzle_flash(surface, camera_x, None, direction,
                                    knife_hand_x, knife_hand_y, muzzle_angle)

        if self.reloading:
            reload_progress = 1.0 - self.reload_timer / RANGED_RELOAD_FRAMES
            rcx = self.x + self.width / 2 - camera_x
            rcy = self.y - 10
            arc_radius = 8
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * reload_progress
            if reload_progress > 0.01:
                rect = pygame.Rect(rcx - arc_radius, rcy - arc_radius,
                                   arc_radius * 2, arc_radius * 2)
                pygame.draw.arc(surface, RANGED_COLOR, rect, start_angle, end_angle, 2)

    def _draw_head(self, surface, cx, top_y, radius, direction):
        """绘制玩家头部（帽子、头发、脸部、眼睛）。"""
        head_cy = top_y + radius

        hair_color = PLAYER_HAIR
        hair_dark = PLAYER_HAIR_DARK
        hat_color = PLAYER_HAT
        hat_dark = PLAYER_HAT_DARK
        hat_brim = PLAYER_HAT_BRIM
        hat_band = PLAYER_HAT_BAND

        face_color = PLAYER_SKIN
        face_shadow = PLAYER_SKIN_SHADOW

        pygame.draw.circle(surface, face_color, (int(cx), int(head_cy)), radius)

        shadow_side = cx - radius if direction > 0 else cx + radius
        shadow_rect = pygame.Rect(
            shadow_side - 2 if direction > 0 else shadow_side,
            top_y + 2,
            3,
            radius * 2 - 3,
        )
        pygame.draw.rect(surface, face_shadow, shadow_rect)

        hair_top_y = top_y - 2
        hair_left_x = cx - radius + 1
        hair_right_x = cx + radius - 1
        hair_points = [
            (int(hair_left_x), int(top_y + 2)),
            (int(cx - 3), int(hair_top_y)),
            (int(cx + 3), int(hair_top_y)),
            (int(hair_right_x), int(top_y + 2)),
        ]
        pygame.draw.polygon(surface, hair_color, hair_points)
        pygame.draw.line(surface, hair_dark,
                         (int(hair_left_x), int(top_y + 3)),
                         (int(hair_left_x + 1), int(hair_top_y + 2)), 1)
        pygame.draw.line(surface, hair_dark,
                         (int(hair_right_x), int(top_y + 3)),
                         (int(hair_right_x - 1), int(hair_top_y + 2)), 1)

        hat_top_y = hair_top_y - 6
        hat_left = cx - radius - 1
        hat_right = cx + radius + 1
        hat_height = 8

        hat_body_points = [
            (int(hat_left + 1), int(hair_top_y)),
            (int(hat_left + 2), int(hat_top_y + 2)),
            (int(cx - 2), int(hat_top_y)),
            (int(cx + 2), int(hat_top_y)),
            (int(hat_right - 2), int(hat_top_y + 2)),
            (int(hat_right - 1), int(hair_top_y)),
        ]
        pygame.draw.polygon(surface, hat_color, hat_body_points)

        band_y = hair_top_y - 1
        pygame.draw.rect(surface, hat_band,
                         (int(hat_left), int(band_y), int(hat_right - hat_left), 2))

        brim_front_x = cx + direction * (radius + 5)
        brim_back_x = cx - direction * (radius - 1)
        brim_y = hair_top_y + 1
        pygame.draw.line(surface, hat_brim,
                         (int(brim_back_x), int(brim_y)),
                         (int(brim_front_x), int(brim_y)), 3)
        pygame.draw.line(surface, hat_dark,
                         (int(brim_back_x), int(brim_y + 2)),
                         (int(brim_front_x), int(brim_y + 2)), 1)

        pygame.draw.line(surface, hat_dark,
                         (int(hat_left + 2), int(hat_top_y + 3)),
                         (int(hat_left + 3), int(hair_top_y)), 1)
        pygame.draw.line(surface, hat_dark,
                         (int(hat_right - 2), int(hat_top_y + 3)),
                         (int(hat_right - 3), int(hair_top_y)), 1)

        eye_y = head_cy - 1
        eye_spacing = 4
        eye_r = 2

        eye_offset = direction * 1

        left_eye_x = cx - eye_spacing + eye_offset
        right_eye_x = cx + eye_spacing + eye_offset

        if self.eye_blink > 0:
            pygame.draw.line(surface, PLAYER_PUPIL,
                             (int(left_eye_x - eye_r), int(eye_y)),
                             (int(left_eye_x + eye_r), int(eye_y)), 1)
            pygame.draw.line(surface, PLAYER_PUPIL,
                             (int(right_eye_x - eye_r), int(eye_y)),
                             (int(right_eye_x + eye_r), int(eye_y)), 1)
        else:
            pygame.draw.circle(surface, PLAYER_EYE, (int(left_eye_x), int(eye_y)), eye_r)
            pygame.draw.circle(surface, PLAYER_EYE, (int(right_eye_x), int(eye_y)), eye_r)
            pygame.draw.circle(surface, PLAYER_PUPIL,
                               (int(left_eye_x + direction * 1), int(eye_y)), 1)
            pygame.draw.circle(surface, PLAYER_PUPIL,
                               (int(right_eye_x + direction * 1), int(eye_y)), 1)

        cheek_y = eye_y + 4
        cheek_x_off = 6
        pygame.draw.circle(surface, PLAYER_CHEEK,
                           (int(cx - cheek_x_off), int(cheek_y)), 2)
        pygame.draw.circle(surface, PLAYER_CHEEK,
                           (int(cx + cheek_x_off), int(cheek_y)), 2)

    def _draw_body(self, surface, left, right, top, bottom, belt_y, belt_h, cx):
        """绘制玩家身体（衬衫、腰带）。"""
        shirt_color = PLAYER_SHIRT
        shirt_dark = PLAYER_SHIRT_DARK
        shirt_light = PLAYER_SHIRT_LIGHT
        belt_color = PLAYER_BELT
        buckle_color = PLAYER_BELT_BUCKLE

        body_points = [
            (int(left + 1), int(top)),
            (int(left + 2), int(bottom)),
            (int(right - 2), int(bottom)),
            (int(right - 1), int(top)),
        ]
        pygame.draw.polygon(surface, shirt_color, body_points)

        shadow_x = left if self.facing_right else right
        shadow_w = 3
        pygame.draw.rect(surface, shirt_dark,
                         (int(shadow_x - 1 if not self.facing_right else shadow_x),
                          int(top + 1),
                          shadow_w,
                          int(bottom - top - 1)))

        highlight_x = right if self.facing_right else left
        pygame.draw.rect(surface, shirt_light,
                         (int(highlight_x - 1 if self.facing_right else highlight_x),
                          int(top + 2),
                          2,
                          int(bottom - top - 4)))

        pygame.draw.rect(surface, belt_color,
                         (int(left), int(belt_y), int(right - left), belt_h))
        buckle_w = 4
        pygame.draw.rect(surface, buckle_color,
                         (int(cx - buckle_w / 2), int(belt_y - 1), buckle_w, belt_h + 2))
        pygame.draw.line(surface, (180, 150, 60),
                         (int(cx - buckle_w / 2 + 1), int(belt_y + 1)),
                         (int(cx + buckle_w / 2 - 1), int(belt_y + 1)), 1)

    def _draw_legs(self, surface, left_x, right_x, top, bottom, shoe_top, shoe_bottom):
        """绘制玩家腿部（裤子、鞋子）。"""
        pants_color = PLAYER_PANTS
        pants_dark = PLAYER_PANTS_DARK
        shoe_color = PLAYER_SHOES
        shoe_light = PLAYER_SHOES_LIGHT

        leg_w = 5

        left_leg_rect = pygame.Rect(int(left_x - leg_w / 2), int(top), leg_w, int(bottom - top))
        right_leg_rect = pygame.Rect(int(right_x - leg_w / 2), int(top), leg_w, int(bottom - top))
        pygame.draw.rect(surface, pants_color, left_leg_rect)
        pygame.draw.rect(surface, pants_color, right_leg_rect)

        pygame.draw.rect(surface, pants_dark,
                         (int(left_x - leg_w / 2), int(top), 1, int(bottom - top)))
        pygame.draw.rect(surface, pants_dark,
                         (int(right_x - leg_w / 2), int(top), 1, int(bottom - top)))

        shoe_h = shoe_bottom - shoe_top
        left_shoe_rect = pygame.Rect(int(left_x - 4), int(shoe_top), 8, shoe_h)
        right_shoe_rect = pygame.Rect(int(right_x - 4), int(shoe_top), 8, shoe_h)
        pygame.draw.rect(surface, shoe_color, left_shoe_rect, border_radius=1)
        pygame.draw.rect(surface, shoe_color, right_shoe_rect, border_radius=1)

        pygame.draw.rect(surface, shoe_light,
                         (int(left_x - 3), int(shoe_top + 1), 3, 1))
        pygame.draw.rect(surface, shoe_light,
                         (int(right_x - 3), int(shoe_top + 1), 3, 1))

    def _draw_back_arm(self, surface, x, y, direction):
        """绘制玩家后臂。"""
        sleeve_color = PLAYER_SHIRT_DARK
        glove_color = PLAYER_GLOVE_DARK

        arm_len = 8
        arm_end_y = y + arm_len

        pygame.draw.line(surface, sleeve_color,
                         (int(x), int(y)),
                         (int(x), int(arm_end_y - 2)), 3)

        pygame.draw.circle(surface, glove_color,
                           (int(x), int(arm_end_y)), 3)

    def _draw_front_arm(self, surface, shoulder_x, shoulder_y, hand_x, hand_y, direction):
        """绘制玩家前臂。"""
        sleeve_color = PLAYER_SHIRT
        glove_color = PLAYER_GLOVE
        glove_dark = PLAYER_GLOVE_DARK

        mid_x = (shoulder_x + hand_x) / 2
        mid_y = (shoulder_y + hand_y) / 2 + 2

        pygame.draw.line(surface, sleeve_color,
                         (int(shoulder_x), int(shoulder_y)),
                         (int(mid_x), int(mid_y)), 4)
        pygame.draw.line(surface, glove_color,
                         (int(mid_x), int(mid_y)),
                         (int(hand_x), int(hand_y - 2)), 3)

        pygame.draw.circle(surface, glove_color,
                           (int(hand_x), int(hand_y)), 4)
        pygame.draw.circle(surface, glove_dark,
                           (int(hand_x - direction * 1), int(hand_y + 1)), 2)

    def _draw_knife(self, surface, hand_x, hand_y, angle, camera_x):
        """绘制匕首武器。"""
        hx = hand_x
        hy = hand_y
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        perp_x = -sin_a
        perp_y = cos_a

        handle_end_x = hx + cos_a * KNIFE_HANDLE_LENGTH
        handle_end_y = hy + sin_a * KNIFE_HANDLE_LENGTH

        handle_w = 4
        handle_poly = [
            (int(hx + perp_x * handle_w), int(hy + perp_y * handle_w)),
            (int(hx - perp_x * handle_w), int(hy - perp_y * handle_w)),
            (int(handle_end_x - perp_x * (handle_w - 0.5)), int(handle_end_y - perp_y * (handle_w - 0.5))),
            (int(handle_end_x + perp_x * (handle_w - 0.5)), int(handle_end_y + perp_y * (handle_w - 0.5))),
        ]
        pygame.draw.polygon(surface, KNIFE_HANDLE_COLOR, handle_poly)

        for i in range(3):
            wrap_t = (i + 1) / 4
            wx = hx + cos_a * KNIFE_HANDLE_LENGTH * wrap_t
            wy = hy + sin_a * KNIFE_HANDLE_LENGTH * wrap_t
            w_w = handle_w - (wrap_t * 0.5)
            pygame.draw.line(surface, KNIFE_HANDLE_WRAP,
                             (int(wx + perp_x * w_w), int(wy + perp_y * w_w)),
                             (int(wx - perp_x * w_w), int(wy - perp_y * w_w)), 1)

        pommel_x = hx - cos_a * 1
        pommel_y = hy - sin_a * 1
        pygame.draw.circle(surface, KNIFE_GUARD_COLOR,
                           (int(pommel_x), int(pommel_y)), 3)
        pygame.draw.circle(surface, KNIFE_GUARD_DARK,
                           (int(pommel_x - perp_x * 1), int(pommel_y - perp_y * 1)), 1)

        guard_w = 7
        guard_h = 2
        guard_center_x = handle_end_x + cos_a * 1
        guard_center_y = handle_end_y + sin_a * 1
        guard_poly = [
            (int(guard_center_x - perp_x * guard_w - cos_a * guard_h),
             int(guard_center_y - perp_y * guard_w - sin_a * guard_h)),
            (int(guard_center_x - perp_x * guard_w + cos_a * guard_h),
             int(guard_center_y - perp_y * guard_w + sin_a * guard_h)),
            (int(guard_center_x + perp_x * guard_w + cos_a * guard_h),
             int(guard_center_y + perp_y * guard_w + sin_a * guard_h)),
            (int(guard_center_x + perp_x * guard_w - cos_a * guard_h),
             int(guard_center_y + perp_y * guard_w - sin_a * guard_h)),
        ]
        pygame.draw.polygon(surface, KNIFE_GUARD_DARK, guard_poly)
        pygame.draw.line(surface, KNIFE_GUARD_COLOR,
                         (int(guard_center_x - perp_x * (guard_w - 1)),
                          int(guard_center_y - perp_y * (guard_w - 1))),
                         (int(guard_center_x + perp_x * (guard_w - 1)),
                          int(guard_center_y + perp_y * (guard_w - 1))), 2)

        blade_base_x = guard_center_x + cos_a * 2
        blade_base_y = guard_center_y + sin_a * 2
        blade_tip_x = blade_base_x + cos_a * KNIFE_LENGTH
        blade_tip_y = blade_base_y + sin_a * KNIFE_LENGTH

        bw = KNIFE_BLADE_WIDTH
        mid_t = 0.65
        mid_x = blade_base_x + cos_a * KNIFE_LENGTH * mid_t
        mid_y = blade_base_y + sin_a * KNIFE_LENGTH * mid_t

        blade_poly = [
            (int(blade_base_x + perp_x * bw), int(blade_base_y + perp_y * bw)),
            (int(mid_x + perp_x * bw * 0.85), int(mid_y + perp_y * bw * 0.85)),
            (int(blade_tip_x), int(blade_tip_y)),
            (int(mid_x - perp_x * bw * 0.5), int(mid_y - perp_y * bw * 0.5)),
            (int(blade_base_x - perp_x * bw * 0.8), int(blade_base_y - perp_y * bw * 0.8)),
        ]
        pygame.draw.polygon(surface, KNIFE_BLADE_COLOR, blade_poly)

        edge_pts = [
            (int(blade_base_x + perp_x * bw), int(blade_base_y + perp_y * bw)),
            (int(mid_x + perp_x * (bw * 0.4)), int(mid_y + perp_y * (bw * 0.4))),
            (int(blade_tip_x + perp_x * 0.5), int(blade_tip_y + perp_y * 0.5)),
        ]
        pygame.draw.polygon(surface, KNIFE_BLADE_HIGHLIGHT, edge_pts)

        spine_pts = [
            (int(blade_base_x - perp_x * bw * 0.6), int(blade_base_y - perp_y * bw * 0.6)),
            (int(mid_x - perp_x * bw * 0.3), int(mid_y - perp_y * bw * 0.3)),
            (int(blade_tip_x - perp_x * 0.3), int(blade_tip_y - perp_y * 0.3)),
        ]
        pygame.draw.lines(surface, KNIFE_BLADE_SHADOW, False, spine_pts, 1)

        fuller_start = blade_base_x + cos_a * 3
        fuller_start_y = blade_base_y + sin_a * 3
        fuller_end = blade_base_x + cos_a * (KNIFE_LENGTH * 0.6)
        fuller_end_y = blade_base_y + sin_a * (KNIFE_LENGTH * 0.6)
        pygame.draw.line(surface, KNIFE_BLADE_SHADOW,
                         (int(fuller_start + perp_x * 1.5), int(fuller_start_y + perp_y * 1.5)),
                         (int(fuller_end + perp_x * 1), int(fuller_end_y + perp_y * 1)), 1)
        pygame.draw.line(surface, KNIFE_BLADE_HIGHLIGHT,
                         (int(fuller_start - perp_x * 1), int(fuller_start_y - perp_y * 1)),
                         (int(fuller_end - perp_x * 0.5), int(fuller_end_y - perp_y * 0.5)), 1)

    def _draw_gun(self, surface, hand_x, hand_y, gun_angle, player_direction, camera_x):
        """绘制枪支武器。"""
        gx = hand_x
        gy = hand_y

        recoil_offset = 0
        if self.ranged_shot_timer > 0:
            recoil_t = self.ranged_shot_timer / GUN_RECOIL_FRAMES
            recoil_mag = GUN_RECOIL_DISTANCE * (1.0 - recoil_t)
            recoil_offset = -recoil_mag * math.cos(gun_angle)

        cos_a = math.cos(gun_angle)
        sin_a = math.sin(gun_angle)
        perp_x = -sin_a
        perp_y = cos_a

        body_start_x = gx + recoil_offset
        body_start_y = gy
        body_end_x = body_start_x + cos_a * GUN_BODY_LENGTH
        body_end_y = body_start_y + sin_a * GUN_BODY_LENGTH

        bh = GUN_BODY_HEIGHT / 2
        body_poly = [
            (int(body_start_x + perp_x * bh), int(body_start_y + perp_y * bh)),
            (int(body_start_x - perp_x * bh), int(body_start_y - perp_y * bh)),
            (int(body_end_x - perp_x * bh), int(body_end_y - perp_y * bh)),
            (int(body_end_x + perp_x * bh), int(body_end_y + perp_y * bh)),
        ]
        pygame.draw.polygon(surface, GUN_BODY_COLOR, body_poly)

        slide_top = [
            (int(body_start_x + perp_x * (bh - 0.5)), int(body_start_y + perp_y * (bh - 0.5))),
            (int(body_start_x + perp_x * (bh * 0.3)), int(body_start_y + perp_y * (bh * 0.3))),
            (int(body_end_x + perp_x * (bh * 0.3)), int(body_end_y + perp_y * (bh * 0.3))),
            (int(body_end_x + perp_x * (bh - 1)), int(body_end_y + perp_y * (bh - 1))),
        ]
        pygame.draw.polygon(surface, GUN_BODY_HIGHLIGHT, slide_top)

        shadow_bot = [
            (int(body_start_x - perp_x * (bh - 0.5)), int(body_start_y - perp_y * (bh - 0.5))),
            (int(body_start_x - perp_x * (bh * 0.5)), int(body_start_y - perp_y * (bh * 0.5))),
            (int(body_end_x - perp_x * (bh * 0.5)), int(body_end_y - perp_y * (bh * 0.5))),
            (int(body_end_x - perp_x * (bh - 0.5)), int(body_end_y - perp_y * (bh - 0.5))),
        ]
        pygame.draw.polygon(surface, GUN_BODY_SHADOW, shadow_bot)

        barrel_start_x = body_end_x
        barrel_start_y = body_end_y
        barrel_end_x = barrel_start_x + cos_a * GUN_BARREL_LENGTH
        barrel_end_y = barrel_start_y + sin_a * GUN_BARREL_LENGTH

        barrel_h = 2.5
        barrel_poly = [
            (int(barrel_start_x + perp_x * barrel_h), int(barrel_start_y + perp_y * barrel_h)),
            (int(barrel_start_x - perp_x * barrel_h), int(barrel_start_y - perp_y * barrel_h)),
            (int(barrel_end_x - perp_x * barrel_h), int(barrel_end_y - perp_y * barrel_h)),
            (int(barrel_end_x + perp_x * barrel_h), int(barrel_end_y + perp_y * barrel_h)),
        ]
        pygame.draw.polygon(surface, GUN_BARREL_COLOR, barrel_poly)

        pygame.draw.line(surface, GUN_BARREL_HIGHLIGHT,
                         (int(barrel_start_x + perp_x * (barrel_h - 0.5)), int(barrel_start_y + perp_y * (barrel_h - 0.5))),
                         (int(barrel_end_x + perp_x * (barrel_h - 0.5)), int(barrel_end_y + perp_y * (barrel_h - 0.5))), 1)

        pygame.draw.line(surface, GUN_BODY_SHADOW,
                         (int(barrel_end_x + perp_x * barrel_h), int(barrel_end_y + perp_y * barrel_h)),
                         (int(barrel_end_x - perp_x * barrel_h), int(barrel_end_y - perp_y * barrel_h)), 2)

        grip_top_x = body_start_x + cos_a * 5
        grip_top_y = body_start_y + sin_a * 5
        grip_down = perp_x * 9, perp_y * 9
        grip_bottom_x = grip_top_x + grip_down[0]
        grip_bottom_y = grip_top_y + grip_down[1]

        grip_tilt = cos_a * 2, sin_a * 2
        grip_poly = [
            (int(grip_top_x - perp_x * 3 + grip_tilt[0]), int(grip_top_y - perp_y * 3 + grip_tilt[1])),
            (int(grip_top_x + perp_x * 3 - grip_tilt[0] * 0.5), int(grip_top_y + perp_y * 3 - grip_tilt[1] * 0.5)),
            (int(grip_bottom_x + perp_x * 3 + grip_tilt[0]), int(grip_bottom_y + perp_y * 3 + grip_tilt[1])),
            (int(grip_bottom_x - perp_x * 3 - grip_tilt[0] * 0.5), int(grip_bottom_y - perp_y * 3 - grip_tilt[1] * 0.5)),
        ]
        pygame.draw.polygon(surface, GUN_GRIP_COLOR, grip_poly)

        for i in range(4):
            wrap_t = i / 4
            wx = grip_top_x + (grip_bottom_x - grip_top_x) * wrap_t
            wy = grip_top_y + (grip_bottom_y - grip_top_y) * wrap_t
            pygame.draw.line(surface, GUN_GRIP_WRAP,
                             (int(wx - perp_x * 2 + cos_a * (1 - wrap_t * 2)),
                              int(wy - perp_y * 2 + sin_a * (1 - wrap_t * 2))),
                             (int(wx + perp_x * 2 + cos_a * (1 - wrap_t * 2)),
                              int(wy + perp_y * 2 + sin_a * (1 - wrap_t * 2))), 1)

        trigger_guard_x = body_start_x + cos_a * 8
        trigger_guard_y = body_start_y + sin_a * 8
        tg_end_x = trigger_guard_x + perp_x * 5
        tg_end_y = trigger_guard_y + perp_y * 5
        pygame.draw.line(surface, GUN_TRIGGER_COLOR,
                         (int(trigger_guard_x), int(trigger_guard_y)),
                         (int(tg_end_x), int(tg_end_y)), 2)
        trigger_mid_x = trigger_guard_x + perp_x * 2
        trigger_mid_y = trigger_guard_y + perp_y * 2
        pygame.draw.line(surface, GUN_TRIGGER_COLOR,
                         (int(trigger_mid_x + cos_a * 1.5), int(trigger_mid_y + sin_a * 1.5)),
                         (int(trigger_mid_x - cos_a * 1.5), int(trigger_mid_y - sin_a * 1.5)), 2)

        sight_x = body_start_x + cos_a * 6
        sight_y = body_start_y + sin_a * 6
        pygame.draw.rect(surface, GUN_BODY_HIGHLIGHT,
                         (int(sight_x - 1), int(sight_y + perp_y * bh - 2), 3, 2))

        front_sight_x = barrel_end_x - cos_a * 3
        front_sight_y = barrel_end_y - sin_a * 3
        pygame.draw.line(surface, GUN_BODY_HIGHLIGHT,
                         (int(front_sight_x), int(front_sight_y + perp_y * barrel_h - 1)),
                         (int(front_sight_x - cos_a * 2), int(front_sight_y + perp_y * barrel_h + 1)), 2)

        mag_x = body_start_x + cos_a * 10
        mag_y = body_start_y + sin_a * 10
        mag_h = 6
        mag_w = 3
        mag_poly = [
            (int(mag_x - perp_x * mag_w + cos_a * 1), int(mag_y - perp_y * mag_w + sin_a * 1)),
            (int(mag_x + perp_x * mag_w - cos_a * 0.5), int(mag_y + perp_y * mag_w - sin_a * 0.5)),
            (int(mag_x + perp_x * (mag_w - 0.5) + perp_x * mag_h - cos_a * 1),
             int(mag_y + perp_y * (mag_w - 0.5) + perp_y * mag_h - sin_a * 1)),
            (int(mag_x - perp_x * (mag_w - 0.5) + perp_x * mag_h + cos_a * 0.5),
             int(mag_y - perp_y * (mag_w - 0.5) + perp_y * mag_h + sin_a * 0.5)),
        ]
        pygame.draw.polygon(surface, GUN_BODY_SHADOW, mag_poly)
        pygame.draw.line(surface, GUN_BODY_HIGHLIGHT,
                         (int(mag_x - perp_x * (mag_w - 1) + perp_x * 1),
                          int(mag_y - perp_y * (mag_w - 1) + perp_y * 1)),
                         (int(mag_x - perp_x * (mag_w - 1) + perp_x * (mag_h - 1)),
                          int(mag_y - perp_y * (mag_w - 1) + perp_y * (mag_h - 1))), 1)

    def _draw_melee_effects(self, surface, camera_x, body_rect, progress, base_angle, direction):
        """绘制近战攻击特效（挥砍光晕、轨迹、火花）。"""
        pcx = self.x + self.width / 2 - camera_x
        pcy = self.y + self.height * 0.5

        swing_start = base_angle + math.radians(-MELEE_ARC_HALF * 0.7)
        swing_end = base_angle + math.radians(MELEE_ARC_HALF * 0.7)
        current_angle = swing_start + (swing_end - swing_start) * progress

        full_arc = MELEE_RANGE + 15
        glow_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        glow_cx = full_arc
        glow_cy = full_arc
        glow_r = min(full_arc - 1, MELEE_SLASH_GLOW_RADIUS)
        glow_intensity = max(0, 1 - abs(progress - 0.5) * 2)
        for r in range(glow_r, 0, -6):
            a = int(70 * glow_intensity * (r / glow_r))
            pygame.draw.circle(glow_surf, (*KNIFE_SWING_GLOW_COLOR, a),
                               (glow_cx, glow_cy), r)
        surface.blit(glow_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        arc_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        start_deg_adj = math.degrees(swing_start)
        end_deg_adj = math.degrees(swing_end)
        current_deg = start_deg_adj + (end_deg_adj - start_deg_adj) * progress

        for i in range(MELEE_SLASH_TRAIL_COUNT):
            t = i / MELEE_SLASH_TRAIL_COUNT
            trail_deg = start_deg_adj + (current_deg - start_deg_adj) * t
            trail_rad = math.radians(trail_deg)
            trail_len = (MELEE_RANGE + 5) * (0.4 + 0.6 * (1 - t))
            te_x = glow_cx + math.cos(trail_rad) * trail_len
            te_y = glow_cy + math.sin(trail_rad) * trail_len
            alpha = int(200 * (1 - t) * glow_intensity * 1.2)
            if alpha > 5:
                line_width = max(1, int(6 * (1 - t * 0.5)))
                pygame.draw.line(arc_surf, (*KNIFE_SLASH_TRAIL_COLOR, min(255, alpha)),
                                 (int(glow_cx), int(glow_cy)),
                                 (int(te_x), int(te_y)), line_width)
        surface.blit(arc_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        big_arc_surf = pygame.Surface((full_arc * 2, full_arc * 2), pygame.SRCALPHA)
        arc_segments = 24
        arc_angle_span = (end_deg_adj - start_deg_adj)
        for i in range(arc_segments):
            t = i / arc_segments
            if t > progress + 0.02:
                break
            a_deg = start_deg_adj + arc_angle_span * t
            a_rad = math.radians(a_deg)
            tx = glow_cx + math.cos(a_rad) * (MELEE_RANGE + 5)
            ty = glow_cy + math.sin(a_rad) * (MELEE_RANGE + 5)
            dist_from_cur = abs(t - progress)
            seg_alpha = int(220 * max(0, 1 - dist_from_cur * 3))
            if seg_alpha > 10:
                pygame.draw.line(big_arc_surf,
                                 (*MELEE_SLASH_ARC_COLOR, min(255, seg_alpha)),
                                 (int(glow_cx), int(glow_cy)),
                                 (int(tx), int(ty)), MELEE_SLASH_ARC_WIDTH)
        surface.blit(big_arc_surf, (int(pcx - glow_cx), int(pcy - glow_cy)))

        cur_rad = math.radians(current_deg)
        tip_x = pcx + math.cos(cur_rad) * (MELEE_RANGE + 5)
        tip_y = pcy + math.sin(cur_rad) * (MELEE_RANGE + 5)

        tip_glow_r = 10
        tip_surf = pygame.Surface((tip_glow_r * 2, tip_glow_r * 2), pygame.SRCALPHA)
        for r in range(tip_glow_r, 0, -3):
            a = int(180 * glow_intensity * (r / tip_glow_r))
            pygame.draw.circle(tip_surf, (*MELEE_COLOR_TIP, a),
                               (tip_glow_r, tip_glow_r), r)
        surface.blit(tip_surf, (int(tip_x - tip_glow_r), int(tip_y - tip_glow_r)))

        pygame.draw.circle(surface, MELEE_COLOR_TIP, (int(tip_x), int(tip_y)), 6)
        pygame.draw.circle(surface, (255, 255, 255), (int(tip_x), int(tip_y)), 3)

        if progress > 0.35 and progress < 0.75:
            impact_center_x = tip_x
            impact_center_y = tip_y
            imp_t = (progress - 0.35) / 0.4
            ring_r = int(4 + MELEE_IMPACT_RING_RADIUS * imp_t)
            ring_alpha = int(240 * max(0, 1 - imp_t))
            if ring_alpha > 0:
                for w in range(4, 0, -1):
                    line_a = int(ring_alpha * (w / 4))
                    if line_a > 0:
                        pygame.draw.circle(surface,
                                           (*KNIFE_IMPACT_FLASH_COLOR, line_a),
                                           (int(impact_center_x), int(impact_center_y)),
                                           ring_r, w)

            if imp_t < 0.3:
                flash_alpha = int(255 * (1 - imp_t / 0.3))
                flash_r = int(14 * (1 - imp_t / 0.3)) + 2
                for r in range(flash_r, 0, -3):
                    a = int(flash_alpha * (r / flash_r))
                    pygame.draw.circle(surface, (255, 240, 180, a),
                                       (int(impact_center_x), int(impact_center_y)), r)

            spark_n = MELEE_SLASH_SPARK_COUNT
            for i in range(spark_n):
                sa = cur_rad + math.radians(-30 + (60 / (spark_n - 1)) * i)
                sl = (8 + imp_t * 16) * (0.6 + 0.4 * ((i % 3) / 2))
                sx = impact_center_x + math.cos(sa) * sl
                sy = impact_center_y + math.sin(sa) * sl
                s_alpha = int(220 * max(0, 1 - imp_t))
                if s_alpha > 10:
                    pygame.draw.line(surface,
                                     (*MELEE_SLASH_ARC_COLOR, s_alpha),
                                     (int(impact_center_x + math.cos(sa) * 2),
                                      int(impact_center_y + math.sin(sa) * 2)),
                                     (int(sx), int(sy)),
                                     max(1, int(3 * (1 - imp_t))))

    def _draw_muzzle_flash(self, surface, camera_x, body_rect, direction, gun_hand_x=None, gun_hand_y=None, gun_angle=None):
        """绘制枪口火焰特效。"""
        if gun_angle is None:
            gun_angle = 0.0 if self.facing_right else math.pi
            gun_angle += math.radians(direction * 3)
        cos_a = math.cos(gun_angle)
        sin_a = math.sin(gun_angle)
        perp_x = -sin_a
        perp_y = cos_a

        if gun_hand_x is None or gun_hand_y is None:
            body_edge_x = self.x + self.width / 2 + direction * 11
            gun_hand_x = body_edge_x - camera_x
            gun_hand_y = self.y + 35

        recoil_offset = 0
        if self.ranged_shot_timer > 0:
            recoil_t = self.ranged_shot_timer / GUN_RECOIL_FRAMES
            recoil_mag = GUN_RECOIL_DISTANCE * (1.0 - recoil_t)
            recoil_offset = -recoil_mag * cos_a

        body_start_x = gun_hand_x + recoil_offset
        barrel_end_x = body_start_x + cos_a * (GUN_BODY_LENGTH + GUN_BARREL_LENGTH)
        barrel_end_y = gun_hand_y + sin_a * (GUN_BODY_LENGTH + GUN_BARREL_LENGTH)

        flash_t = self.muzzle_flash_timer / MUZZLE_FLASH_DURATION
        flash_mag = flash_t
        flash_size = int(MUZZLE_FLASH_SIZE * (0.4 + 0.6 * flash_mag))

        if flash_size < 2:
            return

        cx = barrel_end_x + cos_a * (flash_size * 0.3)
        cy = barrel_end_y + sin_a * (flash_size * 0.3)

        outer_surf = pygame.Surface((flash_size * 4, flash_size * 4), pygame.SRCALPHA)
        ocx = flash_size * 2
        ocy = flash_size * 2
        big_r = flash_size * 1.8
        for r in range(int(big_r), 0, -3):
            a = int(90 * flash_mag * (r / big_r))
            pygame.draw.circle(outer_surf, (*MUZZLE_FLASH_OUTER, a), (ocx, ocy), r)
        surface.blit(outer_surf, (int(cx - ocx), int(cy - ocy)))

        flash_surf = pygame.Surface((flash_size * 3, flash_size * 3), pygame.SRCALPHA)
        fcx = flash_size * 1.5
        fcy = flash_size * 1.5

        star_pts = 8
        for i in range(star_pts):
            a = gun_angle + math.radians((360 / star_pts) * i)
            spike_len = flash_size * (0.7 + 0.6 * math.sin(i * 2.3 + flash_t * 20))
            sx = fcx + math.cos(a) * spike_len
            sy = fcy + math.sin(a) * spike_len
            a_val = int(220 * flash_mag)
            pygame.draw.line(flash_surf, (*MUZZLE_FLASH_COLOR, a_val),
                             (int(fcx), int(fcy)),
                             (int(sx), int(sy)), max(1, int(4 * flash_mag)))
            thick_a = a + math.radians(180 / star_pts)
            thick_len = flash_size * 0.5
            tx = fcx + math.cos(thick_a) * thick_len
            ty = fcy + math.sin(thick_a) * thick_len
            pygame.draw.line(flash_surf, (*MUZZLE_FLASH_OUTER, a_val),
                             (int(fcx), int(fcy)),
                             (int(tx), int(ty)), max(1, int(2 * flash_mag)))

        inner_r = flash_size * 0.8
        for r in range(int(inner_r), 0, -2):
            a = int(200 * flash_mag * (r / inner_r))
            pygame.draw.circle(flash_surf, (*MUZZLE_FLASH_COLOR, a),
                               (int(fcx), int(fcy)), r)
        white_r = flash_size * 0.35
        for r in range(max(1, int(white_r)), 0, -1):
            a = int(255 * flash_mag)
            pygame.draw.circle(flash_surf, (255, 255, 255, a),
                               (int(fcx), int(fcy)), r)
        surface.blit(flash_surf, (int(cx - fcx), int(cy - fcy)))

        beam_len = flash_size * 3
        beam_end_x = cx + cos_a * beam_len
        beam_end_y = cy + sin_a * beam_len
        beam_alpha = int(180 * flash_mag)
        for w in range(5, 0, -1):
            b_alpha = int(beam_alpha * (w / 5) * 0.6)
            pygame.draw.line(surface,
                             (*MUZZLE_FLASH_COLOR, b_alpha),
                             (int(cx), int(cy)),
                             (int(beam_end_x), int(beam_end_y)), w)

        barrel_dir_x = cos_a
        barrel_dir_y = sin_a
        casing_dir_x = perp_x * direction * 0.7 + barrel_dir_x * 0.3
        casing_dir_y = perp_y * direction * 0.7 + barrel_dir_y * 0.3
        casing_dist = CASING_EJECT_DISTANCE * (1 - flash_t)
        if casing_dist > 1:
            cas_x = barrel_end_x + cos_a * 5 + casing_dir_x * casing_dist
            cas_y = barrel_end_y + sin_a * 5 + casing_dir_y * casing_dist
            cas_rot = math.radians(360 * (1 - flash_t) + 45)
            cas_cos = math.cos(cas_rot)
            cas_sin = math.sin(cas_rot)
            cas_size = 3
            cas_poly = [
                (int(cas_x + cas_cos * cas_size - cas_sin * cas_size * 0.4),
                 int(cas_y + cas_sin * cas_size + cas_cos * cas_size * 0.4)),
                (int(cas_x + cas_cos * cas_size + cas_sin * cas_size * 0.4),
                 int(cas_y + cas_sin * cas_size - cas_cos * cas_size * 0.4)),
                (int(cas_x - cas_cos * cas_size + cas_sin * cas_size * 0.4),
                 int(cas_y - cas_sin * cas_size - cas_cos * cas_size * 0.4)),
                (int(cas_x - cas_cos * cas_size - cas_sin * cas_size * 0.4),
                 int(cas_y - cas_sin * cas_size + cas_cos * cas_size * 0.4)),
            ]
            c_alpha = int(220 * flash_mag)
            casing_surf = pygame.Surface((cas_size * 4, cas_size * 4), pygame.SRCALPHA)
            local_cx = cas_size * 2
            local_cy = cas_size * 2
            local_poly = [(int(p[0] - cas_x + local_cx), int(p[1] - cas_y + local_cy)) for p in cas_poly]
            pygame.draw.polygon(casing_surf, (*CASING_COLOR, c_alpha), local_poly)
            surface.blit(casing_surf, (int(cas_x - local_cx), int(cas_y - local_cy)))
