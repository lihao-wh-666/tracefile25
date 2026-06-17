# -*- coding: utf-8 -*-
"""
游戏教程模块。

包含 TutorialMenu 教程菜单类，提供：
- 多页分步教学，涵盖所有游戏机制
- 每一页包含动画演示（模拟游戏录屏效果）
- 支持自动播放和手动翻页
- 显示操作按键提示
"""

import math
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from menus import (
    Menu,
    Button,
    GameState,
    MENU_PANEL_BORDER,
    MENU_TEXT_COLOR,
    MENU_HINT_COLOR,
    BUTTON_BORDER,
    get_chinese_font,
)

__all__ = ["TutorialMenu"]


class TutorialMenu(Menu):
    """
    教程菜单。

    功能：
    - 多页分步教学，涵盖所有游戏机制
    - 每一页包含动画演示（模拟游戏录屏效果）
    - 支持自动播放和手动翻页
    - 显示操作按键提示

    教程页面内容：
    1. 基础移动
    2. 跳跃与多段跳
    3. 攀爬梯子
    4. 收集金币
    5. 近战攻击
    6. 远程射击与换弹
    7. 道具系统
    8. 敌人与战斗
    9. 传送门与关卡
    """

    TUTORIAL_PAGES = [
        {
            "title": "基础移动",
            "subtitle": "使用方向键或 A/D 键左右移动",
            "keys": [("← / A", "向左移动"), ("→ / D", "向右移动")],
            "description": [
                "角色会自动加速和减速，",
                "移动流畅自然。",
            ],
            "demo": "movement",
        },
        {
            "title": "跳跃与多段跳",
            "subtitle": "使用空格、↑ 或 W 键跳跃",
            "keys": [("空格 / ↑ / W", "跳跃（最多 3 段跳）")],
            "description": [
                "在空中可以再次跳跃，",
                "最多支持三段跳！",
                "长按跳跃键可以跳得更高。",
            ],
            "demo": "jumping",
        },
        {
            "title": "攀爬梯子",
            "subtitle": "在梯子上按 ↑↓ 或 W/S 攀爬",
            "keys": [("↑ / W", "向上爬"), ("↓ / S", "向下爬")],
            "description": [
                "靠近梯子时会自动抓住，",
                "按跳跃键可以从梯子上起跳。",
            ],
            "demo": "climbing",
        },
        {
            "title": "收集金币",
            "subtitle": "触碰金币即可收集",
            "keys": [],
            "description": [
                "每个金币价值 10 分，",
                "收集足够的金币可以激活传送门！",
            ],
            "demo": "coins",
        },
        {
            "title": "近战攻击",
            "subtitle": "按 J 键挥砍",
            "keys": [("J", "近战挥砍")],
            "description": [
                "挥砍有短暂的冷却时间，",
                "可以击退敌人并造成伤害。",
            ],
            "demo": "melee",
        },
        {
            "title": "远程射击与换弹",
            "subtitle": "按 K 键射击，按 R 键换弹",
            "keys": [("K", "射击"), ("R", "换弹")],
            "description": [
                "子弹有重力会下坠，",
                "弹药耗尽后记得换弹！",
            ],
            "demo": "ranged",
        },
        {
            "title": "道具系统",
            "subtitle": "拾取道具并使用强化能力",
            "keys": [
                ("1", "使用加速"),
                ("2", "使用护盾"),
                ("3", "使用强化武器"),
                ("Q", "切换武器类型"),
            ],
            "description": [
                "击败敌人有几率掉落道具，",
                "合理使用道具可以轻松过关！",
            ],
            "demo": "powerups",
        },
        {
            "title": "敌人与战斗",
            "subtitle": "巡逻怪和追踪怪",
            "keys": [("J", "近战"), ("K", "远程")],
            "description": [
                "红色巡逻怪：在平台上来回巡逻",
                "紫色追踪怪：发现你会追上来",
                "击败敌人可获得分数和道具掉落。",
            ],
            "demo": "combat",
        },
        {
            "title": "传送门与关卡",
            "subtitle": "收集金币激活传送门进入下一关",
            "keys": [],
            "description": [
                "走到激活的传送门上即可传送到下一关。",
                "游戏共有 3 个关卡，祝你好运！",
            ],
            "demo": "portal",
        },
    ]

    def __init__(self, manager):
        super().__init__(manager, "游戏教程")
        self.panel_width = 800
        self.panel_height = 600
        self._panel_x = (SCREEN_WIDTH - self.panel_width) // 2
        self._panel_y = (SCREEN_HEIGHT - self.panel_height) // 2

        self.current_page = 0
        self.auto_play = False
        self.auto_play_timer = 0
        self.AUTO_PLAY_INTERVAL = 300
        self.anim_tick = 0

        self.buttons = [
            Button(0, 0, 0, 0, "上一页", self._on_prev),
            Button(0, 0, 0, 0, "自动播放", self._on_toggle_auto),
            Button(0, 0, 0, 0, "下一页", self._on_next),
            Button(0, 0, 0, 0, "返回主菜单", self._on_back),
        ]

        btn_width = 140
        btn_height = 40
        spacing = 15
        total_width = 4 * btn_width + 3 * spacing
        start_x = self._panel_x + (self.panel_width - total_width) // 2
        btn_y = self._panel_y + self.panel_height - 70

        for i, btn in enumerate(self.buttons):
            btn.rect.x = start_x + i * (btn_width + spacing)
            btn.rect.y = btn_y
            btn.rect.width = btn_width
            btn.rect.height = btn_height
            btn.selected = (i == self.selected_index)

        self._demo_font = get_chinese_font(20)
        self._desc_font = get_chinese_font(22)
        self._key_font = get_chinese_font(20)
        self._page_font = get_chinese_font(20)

        self._update_buttons_state()

    def _update_buttons_state(self):
        """更新导航按钮的启用状态。"""
        self.buttons[0].enabled = self.current_page > 0
        self.buttons[2].enabled = self.current_page < len(self.TUTORIAL_PAGES) - 1
        self.buttons[1].text = "停止播放" if self.auto_play else "自动播放"

    def reset_state(self):
        """重置教程状态。"""
        self.current_page = 0
        self.anim_tick = 0
        self.auto_play = False
        self.auto_play_timer = 0
        self._update_buttons_state()

    def _on_prev(self):
        """上一页。"""
        if self.current_page > 0:
            self.current_page -= 1
            self.anim_tick = 0
            self._update_buttons_state()

    def _on_next(self):
        """下一页。"""
        if self.current_page < len(self.TUTORIAL_PAGES) - 1:
            self.current_page += 1
            self.anim_tick = 0
            self._update_buttons_state()

    def _on_toggle_auto(self):
        """切换自动播放。"""
        self.auto_play = not self.auto_play
        self.auto_play_timer = 0
        self._update_buttons_state()

    def _on_back(self):
        """返回主菜单。"""
        self.auto_play = False
        self.manager.set_state(GameState.MAIN_MENU)

    def on_escape(self):
        """ESC 返回主菜单。"""
        self._on_back()

    def update(self):
        """更新教程动画状态。"""
        self.anim_tick += 1

        if self.auto_play:
            self.auto_play_timer += 1
            if self.auto_play_timer >= self.AUTO_PLAY_INTERVAL:
                self.auto_play_timer = 0
                if self.current_page < len(self.TUTORIAL_PAGES) - 1:
                    self.current_page += 1
                    self.anim_tick = 0
                    self._update_buttons_state()
                else:
                    self.auto_play = False
                    self._update_buttons_state()

    def handle_event(self, event):
        """处理教程菜单事件，支持左右方向键翻页。"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._on_prev()
                self._play_menu_sound()
                return True
            elif event.key == pygame.K_RIGHT:
                self._on_next()
                self._play_menu_sound()
                return True
            elif event.key == pygame.K_SPACE:
                self._on_toggle_auto()
                self._play_menu_sound()
                return True

        return super().handle_event(event)

    def _draw_demo_area(self, surface):
        """绘制动画演示区域（模拟游戏录屏）。"""
        demo_x = self._panel_x + 40
        demo_y = self._panel_y + 100
        demo_w = self.panel_width - 80
        demo_h = 260

        bg_rect = pygame.Rect(demo_x, demo_y, demo_w, demo_h)
        pygame.draw.rect(surface, (30, 40, 60), bg_rect, border_radius=10)
        pygame.draw.rect(surface, MENU_PANEL_BORDER, bg_rect, width=2, border_radius=10)

        page = self.TUTORIAL_PAGES[self.current_page]
        demo_type = page["demo"]
        t = self.anim_tick

        if demo_type == "movement":
            self._draw_demo_movement(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "jumping":
            self._draw_demo_jumping(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "climbing":
            self._draw_demo_climbing(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "coins":
            self._draw_demo_coins(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "melee":
            self._draw_demo_melee(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "ranged":
            self._draw_demo_ranged(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "powerups":
            self._draw_demo_powerups(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "combat":
            self._draw_demo_combat(surface, demo_x, demo_y, demo_w, demo_h, t)
        elif demo_type == "portal":
            self._draw_demo_portal(surface, demo_x, demo_y, demo_w, demo_h, t)

    def _draw_ground(self, surface, x, y, w, h, ground_y):
        """绘制地面。"""
        pygame.draw.rect(surface, (80, 160, 60), (x, y + ground_y, w, h - ground_y))
        pygame.draw.rect(surface, (70, 140, 40), (x, y + ground_y, w, 6))

    def _draw_player(self, surface, cx, cy, facing_right=True, squash=1.0, stretch=1.0):
        """绘制简化版玩家角色。"""
        body_w = int(24 * stretch)
        body_h = int(32 * squash)
        body_x = cx - body_w // 2
        body_y = cy - body_h

        pygame.draw.rect(surface, (70, 140, 220), (body_x, body_y + 8, body_w, body_h - 14), border_radius=4)
        pygame.draw.rect(surface, (40, 80, 180), (body_x, body_y + body_h - 10, body_w, 10), border_radius=2)

        head_r = 10
        head_y = body_y + 4
        pygame.draw.circle(surface, (255, 220, 180), (cx, head_y), head_r)
        pygame.draw.circle(surface, (210, 50, 50), (cx, head_y - 4), head_r - 2)

        eye_x = cx + (3 if facing_right else -3)
        pygame.draw.circle(surface, (30, 30, 30), (eye_x, head_y), 2)

        shoe_w = body_w // 2 + 2
        shoe_h = 6
        shoe_y = body_y + body_h - 4
        pygame.draw.rect(surface, (45, 35, 30), (body_x - 1, shoe_y, shoe_w, shoe_h), border_radius=2)
        pygame.draw.rect(surface, (45, 35, 30), (body_x + body_w - shoe_w + 1, shoe_y, shoe_w, shoe_h), border_radius=2)

    def _draw_demo_movement(self, surface, x, y, w, h, t):
        """演示：基础移动。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        period = 180
        phase = t % period
        if phase < period // 2:
            px = x + 80 + int(phase * (w - 160) / (period // 2))
            facing = True
        else:
            px = x + w - 80 - int((phase - period // 2) * (w - 160) / (period // 2))
            facing = False

        py = y + ground_y
        self._draw_player(surface, px, py, facing)

        arrow_y = y + ground_y + 30
        if facing:
            arrow_text = "→ → →"
            arrow_color = (100, 200, 255)
        else:
            arrow_text = "← ← ←"
            arrow_color = (100, 200, 255)
        arrow_surf = self._demo_font.render(arrow_text, True, arrow_color)
        surface.blit(arrow_surf, (px - arrow_surf.get_width() // 2, arrow_y))

    def _draw_demo_jumping(self, surface, x, y, w, h, t):
        """演示：跳跃与多段跳。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        cycle = 240
        phase = t % cycle
        px = x + w // 2

        jump_count = 0
        if phase < 60:
            jump_phase = phase
            jump_count = 1
        elif phase < 120:
            jump_phase = phase - 60
            jump_count = 2
        elif phase < 180:
            jump_phase = phase - 120
            jump_count = 3
        else:
            jump_phase = phase - 180
            jump_count = 0

        if jump_count > 0:
            progress = jump_phase / 60
            jump_height = 120 * jump_count
            py = y + ground_y - int(jump_height * 4 * progress * (1 - progress))
            squash = 0.9 if progress < 0.5 else 1.1
            stretch = 1.1 if progress < 0.5 else 0.9
        else:
            progress = jump_phase / 60
            py = y + ground_y
            squash = 1.2 - 0.2 * progress
            stretch = 0.9 + 0.1 * progress

        self._draw_player(surface, px, py, True, squash, stretch)

        if jump_count > 0:
            for i in range(jump_count):
                ring_y = y + ground_y - 20 - i * 35
                ring_alpha = max(0, 255 - (t % 60) * 4)
                ring_surf = pygame.Surface((40, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(ring_surf, (100, 200, 255, ring_alpha), (0, 0, 40, 20), 2)
                surface.blit(ring_surf, (px - 20, ring_y))

        jump_text = f"第 {jump_count} 段跳" if jump_count > 0 else "落地"
        text_surf = self._demo_font.render(jump_text, True, (255, 215, 0))
        surface.blit(text_surf, (x + w - text_surf.get_width() - 20, y + 20))

    def _draw_demo_climbing(self, surface, x, y, w, h, t):
        """演示：攀爬梯子。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        ladder_x = x + w // 2 - 12
        ladder_top = y + 30
        ladder_bottom = y + ground_y

        pygame.draw.rect(surface, (160, 120, 60), (ladder_x, ladder_top, 4, ladder_bottom - ladder_top))
        pygame.draw.rect(surface, (160, 120, 60), (ladder_x + 20, ladder_top, 4, ladder_bottom - ladder_top))
        for rung_y in range(ladder_top + 10, ladder_bottom, 20):
            pygame.draw.rect(surface, (140, 100, 40), (ladder_x, rung_y, 24, 4))

        cycle = 180
        phase = t % cycle
        if phase < 90:
            py = ladder_bottom - int(phase * (ladder_bottom - ladder_top - 40) / 90)
        else:
            py = ladder_top + 20 + int((phase - 90) * (ladder_bottom - ladder_top - 40) / 90)

        px = ladder_x + 12
        self._draw_player(surface, px, py + 32, True)

        arrow = "↑" if phase < 90 else "↓"
        arrow_surf = self._demo_font.render(arrow * 3, True, (100, 255, 180))
        surface.blit(arrow_surf, (ladder_x - 40, py))

    def _draw_demo_coins(self, surface, x, y, w, h, t):
        """演示：收集金币。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        coin_positions = [
            (x + 150, y + ground_y - 60),
            (x + 280, y + ground_y - 100),
            (x + 410, y + ground_y - 60),
            (x + 540, y + ground_y - 120),
        ]

        collected = set()
        cycle = 240
        player_x = x + 80 + int((t % cycle) * (w - 160) / cycle)
        player_y = y + ground_y

        for i, (cx, cy) in enumerate(coin_positions):
            arrive_time = (cx - x - 80) * cycle / (w - 160)
            if (t % cycle) > arrive_time:
                collected.add(i)

        for i, (cx, cy) in enumerate(coin_positions):
            if i in collected:
                collect_phase = (t % cycle) - ((cx - x - 80) * cycle / (w - 160))
                if collect_phase < 30:
                    scale = 1 + collect_phase * 0.05
                    alpha = max(0, 255 - int(collect_phase * 8.5))
                    coin_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                    coin_r = int(12 * scale)
                    pygame.draw.circle(coin_surf, (255, 215, 0, alpha), (15, 15), coin_r)
                    pygame.draw.circle(coin_surf, (200, 170, 0, alpha), (15, 15), coin_r, 2)
                    surface.blit(coin_surf, (cx - 15, cy - 15))

                    score_surf = self._demo_font.render("+10", True, (255, 215, 0))
                    score_y = cy - 30 - collect_phase
                    score_alpha = max(0, 255 - int(collect_phase * 8.5))
                    score_bg = pygame.Surface(score_surf.get_size(), pygame.SRCALPHA)
                    score_bg.blit(score_surf, (0, 0))
                    score_bg.set_alpha(score_alpha)
                    surface.blit(score_bg, (cx - score_surf.get_width() // 2, score_y))
            else:
                bob = math.sin(t * 0.08 + i) * 4
                coin_y = cy + bob
                pygame.draw.circle(surface, (255, 215, 0), (cx, coin_y), 12)
                pygame.draw.circle(surface, (200, 170, 0), (cx, coin_y), 12, 2)
                shine = 6 + int(math.sin(t * 0.15 + i) * 2)
                pygame.draw.circle(surface, (255, 255, 200), (cx - 3, coin_y - 3), shine)

        self._draw_player(surface, player_x, player_y, True)

    def _draw_demo_melee(self, surface, x, y, w, h, t):
        """演示：近战攻击。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        player_x = x + 200
        player_y = y + ground_y
        self._draw_player(surface, player_x, player_y, True)

        cycle = 60
        swing_phase = t % cycle
        if swing_phase < 20:
            swing_progress = swing_phase / 20
            swing_angle = -math.pi / 3 + swing_progress * math.pi * 0.8
            arc_start = -70
            arc_end = int(swing_angle * 180 / math.pi)

            slash_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            for ang in range(arc_start, arc_end, 5):
                rad = math.radians(ang)
                r1, r2 = 30, 55
                alpha = max(0, 255 - abs(ang + 30) * 3)
                x1 = 60 + int(math.cos(rad) * r1)
                y1 = 60 + int(math.sin(rad) * r1)
                x2 = 60 + int(math.cos(rad) * r2)
                y2 = 60 + int(math.sin(rad) * r2)
                pygame.draw.line(slash_surf, (255, 240, 200, alpha), (x1, y1), (x2, y2), 4)
            surface.blit(slash_surf, (player_x - 10, player_y - 100))

        enemy_x = x + 380
        enemy_y = y + ground_y
        if swing_phase < 20 and t % 120 < 60:
            knockback = int(swing_phase * 2)
            enemy_draw_x = enemy_x + knockback
            flash = max(0, 255 - swing_phase * 12)
            enemy_color = (255, 100 + flash // 3, 100 + flash // 3)
        else:
            enemy_draw_x = enemy_x
            enemy_color = (180, 60, 60)

        patrol_phase = (t // 3) % 100
        if patrol_phase < 50:
            enemy_draw_x -= patrol_phase
        else:
            enemy_draw_x -= (100 - patrol_phase)

        pygame.draw.rect(surface, enemy_color, (enemy_draw_x - 16, enemy_y - 32, 32, 32), border_radius=4)
        pygame.draw.circle(surface, (255, 255, 100), (enemy_draw_x - 5, enemy_y - 22), 4)
        pygame.draw.circle(surface, (255, 255, 100), (enemy_draw_x + 5, enemy_y - 22), 4)
        pygame.draw.circle(surface, (180, 50, 0), (enemy_draw_x - 5, enemy_y - 22), 2)
        pygame.draw.circle(surface, (180, 50, 0), (enemy_draw_x + 5, enemy_y - 22), 2)

        key_surf = self._demo_font.render("[ J ]", True, (255, 200, 100))
        surface.blit(key_surf, (player_x - key_surf.get_width() // 2, player_y - 130))

    def _draw_demo_ranged(self, surface, x, y, w, h, t):
        """演示：远程射击与换弹。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        player_x = x + 150
        player_y = y + ground_y
        self._draw_player(surface, player_x, player_y, True)

        pygame.draw.rect(surface, (55, 58, 68), (player_x + 10, player_y - 26, 24, 8), border_radius=2)
        pygame.draw.rect(surface, (40, 42, 50), (player_x + 30, player_y - 24, 16, 5), border_radius=2)

        cycle = 90
        phase = t % cycle
        if phase < 5:
            flash_size = int(18 * (1 - phase / 5))
            flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 200, 200), (flash_size, flash_size), flash_size)
            pygame.draw.circle(flash_surf, (255, 180, 60, 150), (flash_size, flash_size), flash_size - 3)
            surface.blit(flash_surf, (player_x + 40, player_y - 30 - flash_size // 2))

        if phase < 45:
            bullet_x = player_x + 46 + phase * 12
            bullet_y = player_y - 22 + (phase ** 2) * 0.02
            pygame.draw.circle(surface, (255, 255, 100), (int(bullet_x), int(bullet_y)), 5)
            pygame.draw.circle(surface, (255, 200, 50), (int(bullet_x), int(bullet_y)), 5, 1)
            for i in range(3):
                trail_x = bullet_x - i * 8
                trail_alpha = max(0, 200 - i * 60)
                trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (255, 200, 50, trail_alpha), (4, 4), 3 - i)
                surface.blit(trail_surf, (int(trail_x), int(bullet_y) - 4))

        enemy_x = x + 550
        enemy_y = y + ground_y
        if phase < 45 and 500 < player_x + 46 + phase * 12 < 620:
            hit_phase = phase - 38
            if hit_phase > 0:
                flash = max(0, 255 - hit_phase * 40)
                enemy_color = (255, 100 + flash // 4, 100 + flash // 4)
            else:
                enemy_color = (120, 80, 160)
        else:
            enemy_color = (120, 80, 160)

        chase_offset = math.sin(t * 0.04) * 20
        pygame.draw.ellipse(surface, enemy_color, (enemy_x + chase_offset - 14, enemy_y - 36, 28, 36))
        pygame.draw.circle(surface, (255, 100, 255), (enemy_x + chase_offset - 5, enemy_y - 26), 4)
        pygame.draw.circle(surface, (255, 100, 255), (enemy_x + chase_offset + 5, enemy_y - 26), 4)

        ammo_count = 30 - (t // 90) % 10
        if (t // 90) % 10 == 9 and phase > 45:
            reload_text = "换弹中..."
            reload_color = (255, 150, 100)
        else:
            reload_text = f"弹药: {ammo_count}/30"
            reload_color = (100, 200, 255)
        ammo_surf = self._demo_font.render(reload_text, True, reload_color)
        surface.blit(ammo_surf, (x + w - ammo_surf.get_width() - 20, y + 20))

        key_surf = self._demo_font.render("[ K ] 射击   [ R ] 换弹", True, (255, 200, 100))
        surface.blit(key_surf, (player_x - key_surf.get_width() // 2, player_y - 80))

    def _draw_demo_powerups(self, surface, x, y, w, h, t):
        """演示：道具系统。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        player_x = x + w // 2
        player_y = y + ground_y

        powerup_info = [
            ((0, 200, 255), (100, 230, 255), x + 150, "加速", "1"),
            ((0, 220, 120), (100, 255, 180), x + 300, "护盾", "2"),
            ((255, 100, 50), (255, 150, 100), x + 450, "强化武器", "3"),
            ((255, 200, 50), (255, 230, 100), x + 600, "切换武器", "Q"),
        ]

        for i, (color, glow, px, name, key) in enumerate(powerup_info):
            bob = math.sin(t * 0.08 + i) * 5
            py = y + ground_y - 90 + bob

            glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            glow_radius = 24 + int(math.sin(t * 0.1 + i) * 3)
            pygame.draw.circle(glow_surf, (*glow, 60), (30, 30), glow_radius)
            surface.blit(glow_surf, (px - 30, py - 30))

            pygame.draw.rect(surface, color, (px - 16, py - 16, 32, 32), border_radius=6)
            pygame.draw.rect(surface, glow, (px - 16, py - 16, 32, 32), width=2, border_radius=6)

            if "加速" in name:
                pts = [(px - 8, py - 5), (px, py), (px + 8, py + 5)]
                for ptx, pty in pts:
                    pygame.draw.circle(surface, glow, (ptx, pty), 4)
            elif "护盾" in name:
                for ang in range(0, 360, 45):
                    rad = math.radians(ang - 90)
                    sx = px + int(math.cos(rad) * 10)
                    sy = py + int(math.sin(rad) * 9)
                    pygame.draw.circle(surface, glow, (sx, sy), 3)
            elif "强化" in name:
                pts = [(px - 8, py + 8), (px, py), (px + 8, py - 8)]
                for ptx, pty in pts:
                    pygame.draw.circle(surface, glow, (ptx, pty), 4)
            elif "切换" in name:
                pygame.draw.polygon(surface, glow, [
                    (px - 10, py), (px, py - 8), (px + 10, py), (px, py + 8)
                ])

            name_surf = self._demo_font.render(name, True, MENU_TEXT_COLOR)
            surface.blit(name_surf, (px - name_surf.get_width() // 2, py + 20))

            key_bg_x = px + 14
            key_bg_y = py - 24
            pygame.draw.rect(surface, (*color, 180), (key_bg_x, key_bg_y, 20, 20), border_radius=3)
            key_surf = self._demo_font.render(key, True, (255, 255, 200))
            surface.blit(key_surf, (key_bg_x + (20 - key_surf.get_width()) // 2,
                                     key_bg_y + (20 - key_surf.get_height()) // 2))

        self._draw_player(surface, player_x, player_y, True)

    def _draw_demo_combat(self, surface, x, y, w, h, t):
        """演示：敌人与战斗。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        player_x = x + w // 2
        player_y = y + ground_y
        self._draw_player(surface, player_x, player_y, True)

        patrol_x = x + 150
        patrol_phase = (t // 3) % 160
        if patrol_phase < 80:
            patrol_x += patrol_phase
        else:
            patrol_x += (160 - patrol_phase)
        patrol_facing = patrol_phase < 80

        pygame.draw.rect(surface, (180, 60, 60), (patrol_x - 16, player_y - 32, 32, 32), border_radius=4)
        pygame.draw.rect(surface, (140, 40, 40), (patrol_x - 16, player_y - 10, 32, 10), border_radius=2)
        eye_offset = 3 if patrol_facing else -3
        pygame.draw.circle(surface, (255, 255, 100), (patrol_x - 5 + eye_offset, player_y - 22), 4)
        pygame.draw.circle(surface, (255, 255, 100), (patrol_x + 5 + eye_offset, player_y - 22), 4)
        pygame.draw.circle(surface, (180, 50, 0), (patrol_x - 5 + eye_offset, player_y - 22), 2)
        pygame.draw.circle(surface, (180, 50, 0), (patrol_x + 5 + eye_offset, player_y - 22), 2)

        patrol_label = self._demo_font.render("巡逻怪", True, (255, 150, 150))
        surface.blit(patrol_label, (patrol_x - patrol_label.get_width() // 2, player_y - 52))

        chase_x = x + w - 150
        chase_dx = player_x - chase_x
        chase_move = max(-2, min(2, chase_dx * 0.01))
        chase_x += chase_move + math.sin(t * 0.05) * 0.5

        chase_glow = pygame.Surface((60, 70), pygame.SRCALPHA)
        glow_phase = (math.sin(t * 0.15) + 1) * 0.5
        pygame.draw.ellipse(chase_glow, (200, 100, 255, int(40 + glow_phase * 40)), (5, 5, 50, 60))
        surface.blit(chase_glow, (chase_x - 30, player_y - 66))

        pygame.draw.ellipse(surface, (120, 80, 160), (chase_x - 14, player_y - 36, 28, 36))
        pygame.draw.ellipse(surface, (80, 50, 120), (chase_x - 14, player_y - 12, 28, 12))
        pygame.draw.circle(surface, (255, 100, 255), (chase_x - 5, player_y - 26), 4)
        pygame.draw.circle(surface, (255, 100, 255), (chase_x + 5, player_y - 26), 4)
        pygame.draw.circle(surface, (100, 0, 100), (chase_x - 5, player_y - 26), 2)
        pygame.draw.circle(surface, (100, 0, 100), (chase_x + 5, player_y - 26), 2)

        chase_label = self._demo_font.render("追踪怪", True, (200, 150, 255))
        surface.blit(chase_label, (chase_x - chase_label.get_width() // 2, player_y - 56))

    def _draw_demo_portal(self, surface, x, y, w, h, t):
        """演示：传送门与关卡。"""
        ground_y = h - 50
        self._draw_ground(surface, x, y, w, h, ground_y)

        portal_x = x + w - 180
        portal_y = y + ground_y - 90
        portal_w = 60
        portal_h = 90

        coins_needed = 0
        coins_collected = (t // 30) % 6
        activated = coins_collected >= coins_needed

        for i in range(5):
            coin_x = x + 100 + i * 60
            coin_y = y + ground_y - 80
            if i < coins_collected:
                collect_alpha = max(0, 255 - ((t // 30) % 30) * 8) if i == coins_collected - 1 and (t % 30) < 30 else 0
                if collect_alpha > 0:
                    coin_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(coin_surf, (255, 215, 0, collect_alpha), (15, 15), 12)
                    surface.blit(coin_surf, (coin_x - 15, coin_y - 15))
            else:
                bob = math.sin(t * 0.08 + i) * 4
                pygame.draw.circle(surface, (255, 215, 0), (coin_x, coin_y + bob), 12)
                pygame.draw.circle(surface, (200, 170, 0), (coin_x, coin_y + bob), 12, 2)

        portal_cx = portal_x + portal_w // 2
        portal_cy = portal_y + portal_h // 2

        if activated:
            for layer in range(3):
                radius = 30 + layer * 8 + int(math.sin(t * 0.1 + layer) * 4)
                alpha = 120 - layer * 30
                glow_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                color_layer = (
                    100 + layer * 50,
                    200 + layer * 15,
                    255,
                )
                pygame.draw.ellipse(
                    glow_surf,
                    (*color_layer, alpha),
                    (5, 5, radius * 2, radius * 2)
                )
                surface.blit(glow_surf, (portal_cx - radius - 5, portal_cy - radius - 5))

            for i in range(6):
                angle = t * 0.05 + i * math.pi / 3
                pr = 25 + int(math.sin(t * 0.08 + i) * 6)
                px = portal_cx + int(math.cos(angle) * pr * 0.6)
                py = portal_cy + int(math.sin(angle) * pr)
                p_alpha = max(0, min(255, 200 - int(math.sin(t * 0.1 + i) * 100)))
                p_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (150, 230, 255, p_alpha), (5, 5), 3)
                surface.blit(p_surf, (px - 5, py - 5))

        pygame.draw.ellipse(
            surface,
            (150, 230, 255) if activated else (80, 80, 100),
            (portal_x, portal_y, portal_w, portal_h),
            width=3
        )
        inner_color = (100, 200, 255) if activated else (60, 60, 80)
        pygame.draw.ellipse(surface, inner_color, (portal_x + 6, portal_y + 6, portal_w - 12, portal_h - 12))

        if activated:
            swirl_color = (200, 240, 255)
            for i in range(3):
                swirl_angle = t * 0.12 + i * math.pi * 2 / 3
                swirl_r = 15 + i * 5
                sx = portal_cx + int(math.cos(swirl_angle) * swirl_r * 0.5)
                sy = portal_cy + int(math.sin(swirl_angle) * swirl_r)
                pygame.draw.circle(surface, swirl_color, (sx, sy), 4 - i)

        player_cycle = 180
        player_phase = t % player_cycle
        if player_phase < 120:
            player_x = x + 80 + int(player_phase * (portal_x - x - 120) / 120)
        else:
            player_x = portal_x - 40
        player_y_draw = y + ground_y

        if player_phase > 140 and activated:
            alpha = max(0, 255 - int((player_phase - 140) * 6))
            if alpha > 0:
                surface.set_clip(pygame.Rect(player_x - 30, player_y_draw - 60, 60, 60))
                self._draw_player(surface, player_x, player_y_draw, True)
                surface.set_clip(None)

        if player_phase <= 140 or not activated:
            self._draw_player(surface, player_x, player_y_draw, True)

        portal_text = "已激活！" if activated else f"需要 {coins_needed} 金币"
        portal_color = (100, 255, 200) if activated else (180, 180, 180)
        text_surf = self._demo_font.render(portal_text, True, portal_color)
        surface.blit(text_surf, (portal_cx - text_surf.get_width() // 2, portal_y - 30))

        coin_text = f"金币: {coins_collected}"
        coin_surf = self._demo_font.render(coin_text, True, (255, 215, 0))
        surface.blit(coin_surf, (x + 20, y + 20))

    def _draw_description(self, surface):
        """绘制当前页面的描述文字和按键提示。"""
        page = self.TUTORIAL_PAGES[self.current_page]

        info_x = self._panel_x + 40
        info_y = self._panel_y + 380
        info_w = self.panel_width - 80

        subtitle_surf = self._desc_font.render(page["subtitle"], True, (180, 200, 255))
        surface.blit(subtitle_surf, (info_x, info_y))

        desc_y = info_y + 35
        for line in page["description"]:
            line_surf = self._desc_font.render(line, True, MENU_TEXT_COLOR)
            surface.blit(line_surf, (info_x, desc_y))
            desc_y += 28

        if page["keys"]:
            key_y = desc_y + 10
            key_label = self._key_font.render("操作按键：", True, (255, 200, 100))
            surface.blit(key_label, (info_x, key_y))
            key_y += 28

            for key_name, key_desc in page["keys"]:
                key_bg_w = 80
                key_bg_h = 26
                pygame.draw.rect(
                    surface,
                    (80, 100, 160),
                    (info_x, key_y, key_bg_w, key_bg_h),
                    border_radius=4
                )
                pygame.draw.rect(
                    surface,
                    BUTTON_BORDER,
                    (info_x, key_y, key_bg_w, key_bg_h),
                    width=2,
                    border_radius=4
                )
                key_name_surf = self._key_font.render(key_name, True, (255, 255, 200))
                surface.blit(
                    key_name_surf,
                    (info_x + (key_bg_w - key_name_surf.get_width()) // 2,
                     key_y + (key_bg_h - key_name_surf.get_height()) // 2)
                )

                desc_surf = self._key_font.render(f"  {key_desc}", True, MENU_TEXT_COLOR)
                surface.blit(desc_surf, (info_x + key_bg_w + 8, key_y + 3))

                key_y += 34

    def draw(self, surface, big_font, normal_font, small_font):
        """绘制教程菜单。"""
        self.draw_background(surface)
        self.draw_panel(surface)
        self.draw_title(surface, big_font)

        page = self.TUTORIAL_PAGES[self.current_page]
        subtitle_font = get_chinese_font(28)
        page_title_surf = subtitle_font.render(page["title"], True, (255, 215, 0))
        title_x = self._panel_x + (self.panel_width - page_title_surf.get_width()) // 2
        surface.blit(page_title_surf, (title_x, self._panel_y + 70))

        self._draw_demo_area(surface)
        self._draw_description(surface)

        for btn in self.buttons:
            btn.draw(surface, normal_font)

        page_text = f"第 {self.current_page + 1} / {len(self.TUTORIAL_PAGES)} 页"
        page_surf = self._page_font.render(page_text, True, MENU_HINT_COLOR)
        surface.blit(page_surf, (
            self._panel_x + self.panel_width - page_surf.get_width() - 20,
            self._panel_y + self.panel_height - 30
        ))

        if self.auto_play:
            auto_text = f"▶ 自动播放中... {self.AUTO_PLAY_INTERVAL - self.auto_play_timer}"
            auto_color = (100, 255, 180)
        else:
            auto_text = "按 空格 自动播放   ← → 翻页"
            auto_color = MENU_HINT_COLOR
        auto_surf = self._page_font.render(auto_text, True, auto_color)
        surface.blit(auto_surf, (self._panel_x + 20, self._panel_y + self.panel_height - 30))
