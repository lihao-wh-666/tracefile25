"""
core.py - 游戏核心模块

包含 Game 主类，负责：
- 游戏状态管理（分数、相机、粒子池等）
- 多关卡切换机制（加载界面、过渡动画、数据重置）
- 传送门交互与区域/跨关卡跳转
- 关卡数据构建
- 输入事件处理与健康检查模拟输入
- 游戏主循环（更新 → 渲染 → 计时）
- 背景层绘制（天空、山脉、云朵）
- HUD 绘制
- 碰撞检测（金币收集、传送门触发）

性能优化:
- 天空渐变预渲染为 Surface（避免每帧 640+ 次画线）
- 云朵预渲染为带透明度的 Surface（避免每帧重复创建 Surface 与绘制椭圆）
"""

import sys
import random
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, HEADLESS, HEALTHCHECK,
    HEALTHCHECK_MAX_FRAMES,
    SKY_TOP, SKY_BOTTOM, WHITE, BLACK,
    MOUNTAIN_COLOR, MOUNTAIN_SNOW_COLOR,
    CLOUD_COLOR, CLOUD_ALPHA_INNER, CLOUD_ALPHA_OUTER,
    CLOUD_COUNT, CLOUD_SEED,
    MOUNTAIN_COUNT, MOUNTAIN_SEED,
    PARTICLE_COLORS, DUST_PARTICLE_COLORS, PORTAL_PARTICLE_COLORS,
    COIN_COLOR, COIN_DARK, COIN_COLLECT_SCORE,
    CAMERA_LERP, CAMERA_TARGET_RATIO,
    LEVEL_WIDTH, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    TRANSITION_DURATION_FRAMES, TRANSITION_COLOR,
    LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT,
    LOADING_BAR_BG, LOADING_BAR_FG, LOADING_TEXT_COLOR,
    TOTAL_LEVELS,
)

from entities import Particle, Coin, Platform, Player, Ladder, Portal
from levels import get_level_config, LEVEL_BUILDERS


class GameState:
    """游戏状态枚举类。"""
    PLAYING = "playing"
    TRANSITIONING = "transitioning"
    LOADING = "loading"


class Game:
    """
    游戏主控制器，管理整个游戏生命周期。

    状态属性:
        screen: 主显示 Surface
        clock: pygame 时钟，用于控制帧率
        tick: 全局帧计数器
        score: 游戏得分（金币 * 10）
        particles: 活跃粒子列表
        camera_x: 相机水平滚动偏移
        platforms: 所有平台列表
        coins: 所有金币列表
        ladders: 所有梯子列表
        portals: 所有传送门列表
        player: 玩家对象
        font: 小字体（HUD）
        big_font: 大字体（标题等）
        clouds: 云朵数据 + 预渲染 Surface 列表
        bg_mountains: 背景山脉数据列表
        _sky_surface: 预渲染的天空渐变 Surface（性能优化）
        current_level: 当前关卡编号
        game_state: 当前游戏状态（playing/transitioning/loading）
        transition_frame: 过渡动画帧计数器
        transition_phase: 过渡阶段（0=淡出，1=加载，2=淡入）
        pending_level: 待加载的目标关卡编号
        pending_spawn: 待加载的目标出生点 (x, y)
        level_config: 当前关卡配置对象
        loading_progress: 加载进度 0.0~1.0
    """

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Platform Jumper")
        self.clock = pygame.time.Clock()
        self.tick = 0
        self.score = 0
        self.particles = []
        self.camera_x = 0

        self.platforms = []
        self.coins = []
        self.ladders = []
        self.portals = []

        self.current_level = 0
        self.game_state = GameState.LOADING
        self.transition_frame = 0
        self.transition_phase = 0
        self.pending_level = 0
        self.pending_spawn = (PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.level_config = None
        self.loading_progress = 0.0

        self.player = Player(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 52)
        self.title_font = pygame.font.Font(None, 72)

        self._sky_surface = None
        self.clouds = []
        self.bg_mountains = []

        self._load_level(0, PLAYER_SPAWN_X, PLAYER_SPAWN_Y, immediate=True)

    def _build_sky_surface(self, sky_top, sky_bottom):
        """
        预渲染天空渐变 Surface。

        优化原因：原代码每帧循环 SCREEN_HEIGHT 次绘制水平线，
        在 60FPS 下每秒执行 38400+ 次 pygame.draw.line。
        改为启动时一次性构建渐变 Surface，每帧仅 blit 一次。

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

    def _build_clouds(self):
        """
        构建并预渲染云朵数据。

        每个云朵包含：
        - x, y: 世界坐标与垂直位置
        - w, h: 尺寸
        - speed: 水平飘移速度
        - surface: 预渲染的带透明度云朵图像

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
                (*CLOUD_COLOR, CLOUD_ALPHA_INNER),
                (0, h // 4, w, h // 2),
            )
            pygame.draw.ellipse(
                surf,
                (*CLOUD_COLOR, CLOUD_ALPHA_OUTER),
                (w // 4, 0, w // 2, h),
            )
            clouds.append(
                {
                    "x": rng.randint(-200, 3200),
                    "y": rng.randint(20, 180),
                    "w": w,
                    "h": h,
                    "speed": rng.uniform(0.1, 0.4),
                    "surface": surf,
                }
            )
        return clouds

    def _build_mountains(self):
        """
        构建背景山脉数据。

        Returns:
            山脉字典列表，每座山包含 x, w, h 信息
        """
        mountains = []
        rng = random.Random(MOUNTAIN_SEED)
        for _ in range(MOUNTAIN_COUNT):
            mountains.append(
                {
                    "x": rng.randint(-100, 3200),
                    "h": rng.randint(80, 200),
                    "w": rng.randint(150, 300),
                }
            )
        return mountains

    def _build_level(self, level_config):
        """
        根据关卡配置构建关卡数据。

        Args:
            level_config: LevelConfig 关卡配置对象
        """
        self.platforms = []
        self.coins = []
        self.ladders = []
        self.portals = []

        for x, y, w, h in level_config.ground_specs:
            self.platforms.append(Platform(x, y, w, h, is_ground=True))

        for x, y, w, h in level_config.floating_specs:
            self.platforms.append(Platform(x, y, w, h))

        for x, y in level_config.coin_positions:
            self.coins.append(Coin(x, y))

        for x, y, h in level_config.ladder_specs:
            self.ladders.append(Ladder(x, y, h))

        for spec in level_config.portal_specs:
            if len(spec) == 6:
                x, y, target_level, tx, ty, required_coins = spec
            else:
                x, y, target_level, tx, ty = spec
                required_coins = 0
            self.portals.append(Portal(x, y, target_level, tx, ty, required_coins))

    def _load_level(self, level_id, spawn_x, spawn_y, immediate=False):
        """
        加载指定关卡，重置所有游戏数据。

        处理流程:
        1. 获取关卡配置
        2. 构建平台、金币、梯子、传送门
        3. 重建玩家对象（重置出生点）
        4. 重建天空渐变背景（根据关卡主题色）
        5. 重置相机、粒子、得分类数据
        6. 如果非立即加载，进入淡入阶段

        Args:
            level_id: 目标关卡编号
            spawn_x, spawn_y: 玩家出生坐标
            immediate: 是否立即加载（跳过过渡动画）
        """
        self.level_config = get_level_config(level_id)
        self.current_level = level_id
        self._build_level(self.level_config)

        self.player = Player(spawn_x, spawn_y)
        self.player.start_x = spawn_x
        self.player.start_y = spawn_y

        self._sky_surface = self._build_sky_surface(
            self.level_config.sky_top, self.level_config.sky_bottom
        )
        self.clouds = self._build_clouds()
        self.bg_mountains = self._build_mountains()

        self.camera_x = 0
        self.particles = []

        if immediate:
            self.game_state = GameState.PLAYING
            self.transition_phase = 0
            self.transition_frame = 0
        else:
            self.game_state = GameState.TRANSITIONING
            self.transition_phase = 2
            self.transition_frame = 0

    def _start_transition(self, target_level, target_x, target_y):
        """
        启动关卡切换过渡流程。

        阶段:
        - phase 0: 淡出当前画面
        - phase 1: 加载新关卡数据 + 显示加载界面
        - phase 2: 淡入新画面

        Args:
            target_level: 目标关卡编号（-1 表示同关卡内传送）
            target_x, target_y: 目标出生坐标
        """
        self.game_state = GameState.TRANSITIONING
        self.transition_phase = 0
        self.transition_frame = 0

        if target_level == -1:
            self.pending_level = self.current_level
        else:
            self.pending_level = target_level % len(LEVEL_BUILDERS)
        self.pending_spawn = (target_x, target_y)

        self._spawn_particles(
            self.player.x + self.player.width / 2,
            self.player.y + self.player.height / 2,
            count=20,
            colors=PORTAL_PARTICLE_COLORS,
            spread=5,
            life=30,
            size=5,
        )

    def _update_transition(self):
        """
        更新过渡动画状态机。

        每阶段持续 TRANSITION_DURATION_FRAMES 帧，
        阶段 1（加载）时同步更新加载进度条动画。
        """
        self.transition_frame += 1
        half_duration = TRANSITION_DURATION_FRAMES // 2

        if self.transition_phase == 0:
            if self.transition_frame >= half_duration:
                self.transition_phase = 1
                self.transition_frame = 0
                self.game_state = GameState.LOADING
                self.loading_progress = 0.0

        elif self.transition_phase == 1:
            self.loading_progress = min(1.0, self.transition_frame / half_duration)
            if self.transition_frame >= half_duration:
                spawn_x, spawn_y = self.pending_spawn
                self._load_level(self.pending_level, spawn_x, spawn_y, immediate=False)

        elif self.transition_phase == 2:
            if self.transition_frame >= half_duration:
                self.game_state = GameState.PLAYING
                self.transition_phase = 0
                self.transition_frame = 0

    def _spawn_particles(
        self, x, y, count, colors=PARTICLE_COLORS,
        spread=3, life=20, size=3
    ):
        """
        在指定位置生成一批粒子。

        粒子参数均为随机区间：
        - vx: [-spread, spread]
        - vy: [-spread*1.5, -0.5]（向上偏）
        - life: [life//2, life]
        - size: [1, size]

        Args:
            x, y: 发射中心坐标
            count: 生成数量
            colors: 可选颜色列表
            spread: 速度散布范围
            life: 最大生命周期帧数
            size: 最大粒子半径
        """
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread * 1.5, -0.5)
            color = random.choice(colors)
            l = random.randint(life // 2, life)
            s = random.randint(1, size)
            self.particles.append(Particle(x, y, vx, vy, color, l, s))

    def _update_camera(self):
        """
        更新相机位置。

        使用线性插值（LERP）实现平滑跟随，
        目标位置为玩家左侧 1/3 屏幕处。
        相机被限制在 [0, LEVEL_WIDTH - SCREEN_WIDTH] 范围内。
        """
        target_x = self.player.x - SCREEN_WIDTH / CAMERA_TARGET_RATIO
        self.camera_x += (target_x - self.camera_x) * CAMERA_LERP
        self.camera_x = max(0, min(self.camera_x, LEVEL_WIDTH - SCREEN_WIDTH))

    def _draw_sky(self):
        """绘制预渲染的天空渐变背景。"""
        self.screen.blit(self._sky_surface, (0, 0))

    def _draw_mountains(self):
        """
        绘制远景山脉，应用 0.3 视差因子。

        每座山绘制：
        - 山身三角形（使用关卡主题色）
        - 山顶积雪小三角（使用关卡主题色）
        """
        base_y = SCREEN_HEIGHT - 40
        mountain_color = self.level_config.mountain_color if self.level_config else MOUNTAIN_COLOR
        snow_color = self.level_config.mountain_snow_color if self.level_config else MOUNTAIN_SNOW_COLOR
        for m in self.bg_mountains:
            mx = m["x"] - self.camera_x * 0.3
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
            pygame.draw.polygon(self.screen, mountain_color, points)

            snow_points = [
                (mx + half_w, top_y),
                (mx + half_w - snow_offset, top_y + snow_height),
                (mx + half_w + snow_offset, top_y + snow_height),
            ]
            pygame.draw.polygon(self.screen, snow_color, snow_points)

    def _draw_clouds(self):
        """
        绘制云朵，应用 0.5 视差因子并水平循环飘移。

        使用预渲染 Surface 直接 blit，避免每帧重建图形。
        """
        for c in self.clouds:
            c["x"] += c["speed"]
            if c["x"] > 3200:
                c["x"] = -200
            cx = c["x"] - self.camera_x * 0.5
            if -c["w"] < cx < SCREEN_WIDTH + c["w"]:
                self.screen.blit(c["surface"], (int(cx), int(c["y"])))

    def _check_coins(self):
        """
        检测玩家与金币的碰撞。

        当玩家矩形与未收集金币重叠时：
        - 标记为已收集并启动收集动画
        - 增加 10 分
        - 生成金币粒子特效
        """
        player_rect = self.player.get_rect()
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                coin.collect_anim = 15
                self.score += COIN_COLLECT_SCORE
                self._spawn_particles(
                    coin.x,
                    coin.y,
                    8,
                    colors=[COIN_COLOR, COIN_DARK, (255, 255, 200)],
                    spread=4,
                    life=15,
                    size=4,
                )

    def _check_portals(self):
        """
        检测玩家与传送门的交互。

        当玩家进入已激活传送门范围时：
        - 触发传送门冷却
        - 启动关卡/区域切换过渡流程
        - 生成传送粒子特效
        """
        player_rect = self.player.get_rect()
        for portal in self.portals:
            if portal.can_trigger(player_rect, self.score):
                portal.trigger()
                self._start_transition(
                    portal.target_level,
                    portal.target_x,
                    portal.target_y,
                )
                px = portal.x + portal.width / 2
                py = portal.y + portal.height / 2
                self._spawn_particles(
                    px, py,
                    count=15,
                    colors=PORTAL_PARTICLE_COLORS,
                    spread=4,
                    life=25,
                    size=4,
                )
                break

    def _draw_hud(self):
        """
        绘制抬头显示（HUD）。

        左上角：金币得分（带阴影效果）
        中上：当前关卡名称
        右上角：操作提示
        """
        coin_text = self.font.render(f"Coins: {self.score}", True, WHITE)
        shadow_text = self.font.render(f"Coins: {self.score}", True, BLACK)
        self.screen.blit(shadow_text, (22, 17))
        self.screen.blit(coin_text, (20, 15))

        if self.level_config:
            level_num = self.current_level + 1
            level_text = self.font.render(
                f"Level {level_num}/{TOTAL_LEVELS}: {self.level_config.name}",
                True, WHITE,
            )
            level_shadow = self.font.render(
                f"Level {level_num}/{TOTAL_LEVELS}: {self.level_config.name}",
                True, BLACK,
            )
            text_x = (SCREEN_WIDTH - level_text.get_width()) // 2
            self.screen.blit(level_shadow, (text_x + 2, 17))
            self.screen.blit(level_text, (text_x, 15))

        hint = self.font.render(
            "Arrows/WASD: Move   Space: Jump   Up/Down: Ladder   Enter Portal: Teleport",
            True, (50, 50, 80),
        )
        self.screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 15, 15))

    def _draw_transition(self):
        """绘制过渡动画遮罩层（淡出/淡入）。"""
        half_duration = TRANSITION_DURATION_FRAMES // 2
        if self.transition_phase == 0:
            alpha = int(255 * self.transition_frame / half_duration)
        elif self.transition_phase == 2:
            alpha = int(255 * (1 - self.transition_frame / half_duration))
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*TRANSITION_COLOR, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_loading_screen(self):
        """
        绘制加载界面。

        包含:
        - 关卡名称标题
        - 关卡描述文本
        - 加载进度条
        - 进度百分比文本
        """
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(TRANSITION_COLOR)
        self.screen.blit(overlay, (0, 0))

        target_config = get_level_config(self.pending_level)
        level_num = self.pending_level + 1

        title = self.title_font.render(f"Level {level_num}", True, LOADING_TEXT_COLOR)
        title_x = (SCREEN_WIDTH - title.get_width()) // 2
        self.screen.blit(title, (title_x, SCREEN_HEIGHT // 2 - 140))

        name = self.big_font.render(target_config.name, True, LOADING_TEXT_COLOR)
        name_x = (SCREEN_WIDTH - name.get_width()) // 2
        self.screen.blit(name, (name_x, SCREEN_HEIGHT // 2 - 70))

        desc = self.font.render(target_config.description, True, (200, 200, 220))
        desc_x = (SCREEN_WIDTH - desc.get_width()) // 2
        self.screen.blit(desc, (desc_x, SCREEN_HEIGHT // 2 - 20))

        bar_x = (SCREEN_WIDTH - LOADING_BAR_WIDTH) // 2
        bar_y = SCREEN_HEIGHT // 2 + 40
        pygame.draw.rect(
            self.screen, LOADING_BAR_BG,
            (bar_x, bar_y, LOADING_BAR_WIDTH, LOADING_BAR_HEIGHT),
            border_radius=10,
        )

        fill_width = int(LOADING_BAR_WIDTH * self.loading_progress)
        if fill_width > 0:
            pygame.draw.rect(
                self.screen, LOADING_BAR_FG,
                (bar_x, bar_y, fill_width, LOADING_BAR_HEIGHT),
                border_radius=10,
            )

        pct = int(self.loading_progress * 100)
        pct_text = self.font.render(f"Loading... {pct}%", True, LOADING_TEXT_COLOR)
        pct_x = (SCREEN_WIDTH - pct_text.get_width()) // 2
        self.screen.blit(pct_text, (pct_x, bar_y + LOADING_BAR_HEIGHT + 15))

    def _build_healthcheck_keys(self):
        """
        构建健康检查模式下的模拟按键对象。

        模拟自动向右移动并周期性跳跃，以便无窗口环境下
        自动验证游戏逻辑运行正常。

        Returns:
            支持下标访问的模拟按键字典对象
        """
        sim_keys = {
            pygame.K_RIGHT: True,
            pygame.K_SPACE: self.tick % 120 < 10,
            pygame.K_UP: self.tick % 200 < 30,
            pygame.K_DOWN: self.tick % 200 >= 30 and self.tick % 200 < 60,
            pygame.K_LEFT: False,
            pygame.K_a: False,
            pygame.K_d: True,
            pygame.K_w: False,
            pygame.K_s: False,
        }

        class _KeyProxy:
            def __getitem__(self, key):
                return sim_keys.get(key, False)

        return _KeyProxy()

    def _handle_events(self):
        """
        处理 pygame 事件队列。

        Returns:
            bool: True 表示游戏应继续运行，False 表示请求退出
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
        return True

    def _update_world(self, keys):
        """
        更新游戏世界状态（逻辑帧）。

        处理流程:
        1. 更新玩家，记录落地状态变化
        2. 刚落地时生成落地尘土
        3. 地面高速移动时生成跑步尘土
        4. 检测金币收集
        5. 更新金币动画
        6. 检测传送门触发
        7. 更新传送门状态
        8. 更新粒子池（过滤死亡粒子 + 位置更新）
        9. 更新相机位置

        Args:
            keys: 按键状态（真实或模拟）
        """
        old_on_ground = self.player.on_ground
        self.player.update(keys, self.platforms, self.ladders)

        if self.player.died:
            self.score = 0
            for coin in self.coins:
                coin.collected = False
                coin.collect_anim = 0
            self.player.died = False

        if self.player.on_ground and not old_on_ground and self.player.vy == 0:
            self._spawn_particles(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height,
                count=6,
                spread=3,
                life=15,
                size=3,
            )

        if (
            self.player.on_ground
            and abs(self.player.vx) > 3
            and self.tick % 4 == 0
        ):
            self._spawn_particles(
                self.player.x + self.player.width / 2,
                self.player.y + self.player.height,
                count=2,
                colors=DUST_PARTICLE_COLORS,
                spread=2,
                life=10,
                size=2,
            )

        self._check_coins()

        for coin in self.coins:
            coin.update()

        self._check_portals()

        for portal in self.portals:
            portal.update(self.score)

        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        self._update_camera()

    def _render(self):
        """
        渲染整个场景（渲染帧）。

        绘制顺序（从远到近）:
        1. 天空渐变（最底层）
        2. 远景山脉（0.3 视差）
        3. 云朵（0.5 视差）
        4. 所有平台
        5. 所有梯子
        6. 所有金币
        7. 所有传送门
        8. 粒子特效
        9. 玩家
        10. HUD（最顶层，屏幕空间）

        特殊状态:
        - LOADING: 绘制加载界面覆盖层
        - TRANSITIONING: 绘制过渡遮罩
        """
        self._draw_sky()
        self._draw_mountains()
        self._draw_clouds()

        for plat in self.platforms:
            plat.draw(self.screen, self.camera_x)

        for ladder in self.ladders:
            ladder.draw(self.screen, self.camera_x)

        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.tick)

        for portal in self.portals:
            portal.draw(self.screen, self.camera_x, self.tick)

        for p in self.particles:
            p.draw(self.screen, self.camera_x)

        self.player.draw(self.screen, self.camera_x)

        self._draw_hud()

        if self.game_state == GameState.LOADING:
            self._draw_loading_screen()
        elif self.game_state == GameState.TRANSITIONING:
            self._draw_transition()

    def run(self):
        """
        游戏主循环入口。

        每帧执行顺序:
        1. 帧计数器自增
        2. 健康检查模式下检查是否达到最大帧数
        3. 处理事件（退出条件）
        4. 获取真实按键或构建模拟按键
        5. 根据游戏状态更新（PLAYING: 更新世界 / TRANSITIONING: 更新过渡）
        6. 渲染画面
        7. 交换缓冲 + 帧率控制

        非 HEADLESS 模式下才执行 display.flip，
        两种模式都执行 clock.tick 以保持时间一致性。
        """
        running = True
        while running:
            self.tick += 1

            if HEALTHCHECK and self.tick > HEALTHCHECK_MAX_FRAMES:
                pygame.quit()
                sys.exit(0)

            running = self._handle_events()
            if not running:
                break

            keys = pygame.key.get_pressed()

            if HEADLESS and HEALTHCHECK:
                keys = self._build_healthcheck_keys()

            if self.game_state == GameState.PLAYING:
                self._update_world(keys)
            elif self.game_state in (GameState.TRANSITIONING, GameState.LOADING):
                self._update_transition()

            self._render()

            if not HEADLESS:
                pygame.display.flip()
                self.clock.tick(FPS)
            else:
                self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
