"""
core.py - 游戏核心模块

包含 Game 主类，负责：
- 游戏状态管理（分数、相机、粒子池等）
- 关卡数据构建
- 输入事件处理与健康检查模拟输入
- 游戏主循环（更新 → 渲染 → 计时）
- 背景层绘制（天空、山脉、云朵）
- HUD 绘制
- 碰撞检测（金币收集）

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
    PARTICLE_COLORS, DUST_PARTICLE_COLORS,
    COIN_COLOR, COIN_DARK, COIN_COLLECT_SCORE,
    CAMERA_LERP, CAMERA_TARGET_RATIO,
    LEVEL_WIDTH, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
)

from entities import Particle, Coin, Platform, Player


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
        player: 玩家对象
        font: 小字体（HUD）
        big_font: 大字体（标题等）
        clouds: 云朵数据 + 预渲染 Surface 列表
        bg_mountains: 背景山脉数据列表
        _sky_surface: 预渲染的天空渐变 Surface（性能优化）
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
        self._build_level()

        self.player = Player(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 52)

        self._sky_surface = self._build_sky_surface()
        self.clouds = self._build_clouds()
        self.bg_mountains = self._build_mountains()

    def _build_sky_surface(self):
        """
        预渲染天空渐变 Surface。
        
        优化原因：原代码每帧循环 SCREEN_HEIGHT 次绘制水平线，
        在 60FPS 下每秒执行 38400+ 次 pygame.draw.line。
        改为启动时一次性构建渐变 Surface，每帧仅 blit 一次。
        
        Returns:
            预渲染完成的天空 Surface
        """
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        r1, g1, b1 = SKY_TOP
        r2, g2, b2 = SKY_BOTTOM
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

    def _build_level(self):
        """
        构建关卡数据，包括地面平台、浮动平台和金币位置。
        
        地面平台：7 段大小不一的地面
        浮动平台：17 个按阶梯分布的浮空平台
        金币：17 枚对应平台位置的金币
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
        for x, y, w, h in ground_specs:
            self.platforms.append(Platform(x, y, w, h, is_ground=True))

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
        for x, y, w, h in floating_specs:
            self.platforms.append(Platform(x, y, w, h))

        coin_positions = [
            (200, 450), (360, 380), (540, 320), (720, 400),
            (890, 310), (1040, 230), (1220, 350), (1390, 270),
            (1590, 200), (1740, 320), (1890, 250), (2040, 170),
            (2240, 300), (2440, 220), (2640, 150), (2820, 270),
            (2940, 190),
        ]
        for x, y in coin_positions:
            self.coins.append(Coin(x, y))

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
        - 绿色山身三角形
        - 山顶白色积雪小三角
        """
        base_y = SCREEN_HEIGHT - 40
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
            pygame.draw.polygon(self.screen, MOUNTAIN_COLOR, points)

            snow_points = [
                (mx + half_w, top_y),
                (mx + half_w - snow_offset, top_y + snow_height),
                (mx + half_w + snow_offset, top_y + snow_height),
            ]
            pygame.draw.polygon(self.screen, MOUNTAIN_SNOW_COLOR, snow_points)

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

    def _draw_hud(self):
        """
        绘制抬头显示（HUD）。
        
        左上角：金币得分（带阴影效果）
        右上角：操作提示
        """
        coin_text = self.font.render(f"Coins: {self.score}", True, WHITE)
        shadow_text = self.font.render(f"Coins: {self.score}", True, BLACK)
        self.screen.blit(shadow_text, (22, 17))
        self.screen.blit(coin_text, (20, 15))

        hint = self.font.render(
            "Arrow/WASD: Move   Space: Jump", True, (50, 50, 80)
        )
        self.screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 15, 15))

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
            pygame.K_UP: False,
            pygame.K_LEFT: False,
            pygame.K_a: False,
            pygame.K_d: True,
            pygame.K_w: False,
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
        6. 更新粒子池（过滤死亡粒子 + 位置更新）
        7. 更新相机位置
        
        Args:
            keys: 按键状态（真实或模拟）
        """
        old_on_ground = self.player.on_ground
        self.player.update(keys, self.platforms)

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
        5. 所有金币
        6. 粒子特效
        7. 玩家
        8. HUD（最顶层，屏幕空间）
        """
        self._draw_sky()
        self._draw_mountains()
        self._draw_clouds()

        for plat in self.platforms:
            plat.draw(self.screen, self.camera_x)

        for coin in self.coins:
            coin.draw(self.screen, self.camera_x, self.tick)

        for p in self.particles:
            p.draw(self.screen, self.camera_x)

        self.player.draw(self.screen, self.camera_x)

        self._draw_hud()

    def run(self):
        """
        游戏主循环入口。
        
        每帧执行顺序:
        1. 帧计数器自增
        2. 健康检查模式下检查是否达到最大帧数
        3. 处理事件（退出条件）
        4. 获取真实按键或构建模拟按键
        5. 更新世界逻辑
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

            self._update_world(keys)
            self._render()

            if not HEADLESS:
                pygame.display.flip()
                self.clock.tick(FPS)
            else:
                self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
