# -*- coding: utf-8 -*-
"""
core/background.py - 背景绘制模块

负责游戏背景元素的预渲染和绘制。
"""

import math
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    MOUNTAIN_COLOR, MOUNTAIN_SNOW_COLOR,
    CLOUD_COUNT, CLOUD_SEED,
    MOUNTAIN_COUNT, MOUNTAIN_SEED,
)


class BackgroundManager:
    """
    背景管理器。

    负责:
    - 天空渐变预渲染
    - 星空预渲染
    - 云朵数据构建和预渲染
    - 山脉数据构建
    - 所有背景元素的绘制
    """

    def __init__(self, game):
        self.game = game

    def build_sky_surface(self, sky_top, sky_bottom):
        """
        预渲染天空渐变 Surface。

        Args:
            sky_top: 天空顶部渐变颜色
            sky_bottom: 天空底部渐变颜色

        Returns:
            预渲染完成的天空 Surface
        """
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        r1, g1, b1 = sky_top
        r2, g2, b2 = sky_bottom
        dr = r2 - r1
        dg = g2 - g1
        db = b2 - b1
        inv_height = 1.0 / SCREEN_HEIGHT
        for y in range(SCREEN_HEIGHT):
            t = y * inv_height
            color = (
                int(r1 + dr * t),
                int(g1 + dg * t),
                int(b1 + db * t),
            )
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
        return surface

    def build_stars_surface(self, star_count, star_seed):
        """
        预渲染星空 Surface。

        星星随机分布在天空中，大小和亮度各不相同。
        部分星星带有闪烁效果。

        Args:
            star_count: 星星数量
            star_seed: 随机种子

        Returns:
            预渲染完成带透明度的星空 Surface，若 star_count 为 0 返回 None
        """
        if star_count <= 0:
            return None

        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        rng = random.Random(star_seed)
        for _ in range(star_count):
            sx = rng.randint(0, SCREEN_WIDTH)
            sy = rng.randint(0, int(SCREEN_HEIGHT * 0.65))
            size = rng.choice([1, 1, 1, 2, 2, 3])
            brightness = rng.randint(150, 255)
            color = (brightness, brightness, min(255, brightness + 30), brightness)
            if size == 1:
                surface.set_at((sx, sy), color)
            else:
                pygame.draw.circle(surface, color, (sx, sy), size)
        return surface

    def build_clouds(self, cloud_color, alpha_inner, alpha_outer):
        """
        构建并预渲染云朵数据。

        云朵固定在屏幕空间，仅水平缓慢飘移，不随相机移动。

        Args:
            cloud_color: 云朵颜色
            alpha_inner: 内层透明度
            alpha_outer: 外层透明度

        Returns:
            云朵字典列表
        """
        clouds = []
        rng = random.Random(CLOUD_SEED)
        for _ in range(CLOUD_COUNT):
            w = rng.randint(60, 140)
            h = rng.randint(25, 50)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(
                surf,
                (*cloud_color, alpha_inner),
                (0, h // 4, w, h // 2),
            )
            pygame.draw.ellipse(
                surf,
                (*cloud_color, alpha_outer),
                (w // 4, 0, w // 2, h),
            )
            clouds.append(
                {
                    "x": rng.uniform(0, SCREEN_WIDTH),
                    "y": rng.randint(20, 180),
                    "w": w,
                    "h": h,
                    "speed": rng.uniform(0.05, 0.2),
                    "surface": surf,
                }
            )
        return clouds

    def build_mountains(self):
        """
        构建背景山脉数据。

        山脉固定在屏幕空间，不随相机移动。

        Returns:
            山脉字典列表，每座山包含 x, w, h 信息
        """
        mountains = []
        rng = random.Random(MOUNTAIN_SEED)
        for _ in range(MOUNTAIN_COUNT):
            mountains.append(
                {
                    "x": rng.randint(-50, SCREEN_WIDTH + 50),
                    "h": rng.randint(80, 200),
                    "w": rng.randint(150, 300),
                }
            )
        return mountains

    def draw_sky(self, screen, sky_surface):
        """绘制预渲染的天空渐变背景。"""
        screen.blit(sky_surface, (0, 0))

    def draw_stars(self, screen, stars_surface, tick):
        """绘制预渲染的星空背景，附带闪烁动画。"""
        if stars_surface is None:
            return

        twinkle = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        twinkle.blit(stars_surface, (0, 0))

        rng = random.Random(tick // 6)
        for _ in range(8):
            sx = rng.randint(0, SCREEN_WIDTH)
            sy = rng.randint(0, int(SCREEN_HEIGHT * 0.65))
            pygame.draw.circle(twinkle, (255, 255, 255, 200), (sx, sy), 2)

        screen.blit(twinkle, (0, 0))

    def draw_sun(self, screen, level_config, tick):
        """绘制太阳，含光晕和射线效果。"""
        if not level_config or not level_config.has_sun:
            return

        cfg = level_config
        sx = int(SCREEN_WIDTH * cfg.sun_pos[0])
        sy = int(SCREEN_HEIGHT * cfg.sun_pos[1])
        color = cfg.sun_color

        for r in range(60, 30, -8):
            alpha = max(10, 40 - (60 - r) * 2)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, alpha), (r, r), r)
            screen.blit(glow, (sx - r, sy - r))

        for i in range(12):
            angle = math.radians(i * 30 + tick * 0.3)
            length = 45 + math.sin(tick * 0.05 + i) * 10
            ex = sx + int(math.cos(angle) * length)
            ey = sy + int(math.sin(angle) * length)
            pygame.draw.line(screen, color, (sx, sy), (ex, ey), 2)

        pygame.draw.circle(screen, color, (sx, sy), 25)
        lighter = tuple(min(255, c + 60) for c in color)
        pygame.draw.circle(screen, lighter, (sx - 5, sy - 5), 12)

    def draw_moon(self, screen, level_config):
        """绘制月亮，含光晕和月牙效果。"""
        if not level_config or not level_config.has_moon:
            return

        cfg = level_config
        mx = int(SCREEN_WIDTH * cfg.moon_pos[0])
        my = int(SCREEN_HEIGHT * cfg.moon_pos[1])
        color = cfg.moon_color

        for r in range(50, 25, -6):
            alpha = max(8, 30 - (50 - r) * 2)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*color, alpha), (r, r), r)
            screen.blit(glow, (mx - r, my - r))

        pygame.draw.circle(screen, color, (mx, my), 22)

        shadow_color = level_config.sky_top
        pygame.draw.circle(screen, shadow_color, (mx + 8, my - 4), 18)

    def draw_mountains(self, screen, bg_mountains, level_config):
        """
        绘制远景山脉，固定在屏幕空间不随相机移动。

        每座山绘制山身三角形和山顶积雪小三角。
        """
        base_y = SCREEN_HEIGHT - 40
        mountain_color = level_config.mountain_color if level_config else MOUNTAIN_COLOR
        snow_color = level_config.mountain_snow_color if level_config else MOUNTAIN_SNOW_COLOR
        for m in bg_mountains:
            mx = m["x"]
            w = m["w"]
            h = m["h"]
            half_w = w / 2
            top_y = base_y - h
            snow_offset = w * 0.12
            snow_height = h * 0.2

            points = [
                (mx, base_y),
                (mx + half_w, top_y),
                (mx + w, base_y),
            ]
            pygame.draw.polygon(screen, mountain_color, points)

            snow_points = [
                (mx + half_w, top_y),
                (mx + half_w - snow_offset, top_y + snow_height),
                (mx + half_w + snow_offset, top_y + snow_height),
            ]
            pygame.draw.polygon(screen, snow_color, snow_points)

    def draw_clouds(self, screen, clouds):
        """
        绘制云朵，固定在屏幕空间缓慢飘移，不随相机移动。
        """
        for c in clouds:
            c["x"] += c["speed"]
            if c["x"] > SCREEN_WIDTH + c["w"]:
                c["x"] = -c["w"]
            cx = c["x"]
            if -c["w"] < cx < SCREEN_WIDTH + c["w"]:
                screen.blit(c["surface"], (int(cx), int(c["y"])))
