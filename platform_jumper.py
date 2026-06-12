import pygame
import sys
import math
import random

pygame.init()

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

GRAVITY = 0.6
JUMP_FORCE = -13.5
MOVE_SPEED = 5
MAX_FALL_SPEED = 15
ACCELERATION = 0.8
FRICTION = 0.82

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_TOP = (100, 180, 255)
SKY_BOTTOM = (200, 230, 255)
GROUND_COLOR = (80, 160, 60)
DIRT_COLOR = (120, 80, 40)
PLATFORM_COLOR = (90, 70, 50)
PLATFORM_TOP_COLOR = (70, 150, 50)
PLATFORM_HIGHLIGHT = (110, 90, 65)

PLAYER_BODY = (60, 120, 220)
PLAYER_DARK = (40, 80, 180)
PLAYER_LIGHT = (100, 160, 255)
PLAYER_EYE = (255, 255, 255)
PLAYER_PUPIL = (30, 30, 30)

COIN_COLOR = (255, 215, 0)
COIN_DARK = (200, 170, 0)

PARTICLE_COLORS = [(255, 255, 200), (255, 220, 100), (200, 200, 255)]


class Particle:
    def __init__(self, x, y, vx, vy, color, life, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= 1

    def draw(self, surface, camera_x):
        if self.life <= 0:
            return
        alpha = self.life / self.max_life
        size = max(1, int(self.size * alpha))
        sx = int(self.x - camera_x)
        sy = int(self.y)
        if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
            pygame.draw.circle(surface, self.color, (sx, sy), size)


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.collected = False
        self.bob_offset = random.random() * math.pi * 2
        self.collect_anim = 0

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def update(self):
        if self.collect_anim > 0:
            self.collect_anim -= 1

    def draw(self, surface, camera_x, tick):
        if self.collected and self.collect_anim <= 0:
            return
        bob_y = math.sin(tick * 0.05 + self.bob_offset) * 4
        sx = int(self.x - camera_x)
        sy = int(self.y + bob_y)
        if self.collected:
            alpha = self.collect_anim / 15
            size = int(self.radius * (2 - alpha))
            pygame.draw.circle(surface, COIN_COLOR, (sx, sy), size)
            return
        stretch = abs(math.sin(tick * 0.08 + self.bob_offset))
        w = max(3, int(self.radius * 2 * stretch))
        h = self.radius * 2
        pygame.draw.ellipse(surface, COIN_DARK, (sx - w // 2, sy - h // 2, w, h))
        inner_w = max(2, w - 4)
        inner_h = h - 4
        if inner_w > 0 and inner_h > 0:
            pygame.draw.ellipse(surface, COIN_COLOR, (sx - inner_w // 2, sy - inner_h // 2, inner_w, inner_h))


class Platform:
    def __init__(self, x, y, width, height, is_ground=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_ground = is_ground
        self.grass_tufts = []
        if not is_ground and height <= 24:
            rng = random.Random(hash((x, y, width)))
            for i in range(max(1, width // 30)):
                gx = rng.randint(4, width - 4)
                self.grass_tufts.append(gx)

    def draw(self, surface, camera_x):
        draw_rect = pygame.Rect(
            self.rect.x - camera_x,
            self.rect.y,
            self.rect.width,
            self.rect.height
        )
        if draw_rect.right < 0 or draw_rect.left > SCREEN_WIDTH:
            return

        if self.is_ground:
            pygame.draw.rect(surface, GROUND_COLOR, draw_rect)
            dirt_rect = pygame.Rect(draw_rect.x, draw_rect.y + 6, draw_rect.width, draw_rect.height - 6)
            pygame.draw.rect(surface, DIRT_COLOR, dirt_rect)
            rng = random.Random(42)
            for i in range(draw_rect.width // 8):
                gx = draw_rect.x + rng.randint(0, draw_rect.width)
                gh = rng.randint(3, 8)
                pygame.draw.line(surface, (60, 140, 40), (gx, draw_rect.y), (gx - 2, draw_rect.y - gh), 2)
                pygame.draw.line(surface, (70, 155, 45), (gx + 2, draw_rect.y), (gx, draw_rect.y - gh + 1), 2)
        else:
            pygame.draw.rect(surface, PLATFORM_COLOR, draw_rect)
            top_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, 6)
            pygame.draw.rect(surface, PLATFORM_TOP_COLOR, top_rect)
            highlight_rect = pygame.Rect(draw_rect.x, draw_rect.y + 6, draw_rect.width, 2)
            pygame.draw.rect(surface, PLATFORM_HIGHLIGHT, highlight_rect)
            for gx in self.grass_tufts:
                base_x = draw_rect.x + gx
                pygame.draw.line(surface, (60, 140, 40), (base_x, draw_rect.y), (base_x - 1, draw_rect.y - 5), 2)
                pygame.draw.line(surface, (80, 165, 50), (base_x + 2, draw_rect.y), (base_x + 3, draw_rect.y - 4), 2)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 28
        self.height = 38
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing_right = True
        self.jump_pressed = False
        self.jump_buffer = 0
        self.coyote_time = 0
        self.squash_stretch = 1.0
        self.target_squash = 1.0
        self.run_anim = 0
        self.eye_blink = 0
        self.blink_timer = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys, platforms):
        move_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -1
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = 1
            self.facing_right = True

        if move_x != 0:
            self.vx += move_x * ACCELERATION
            self.vx = max(-MOVE_SPEED, min(MOVE_SPEED, self.vx))
        else:
            self.vx *= FRICTION
            if abs(self.vx) < 0.1:
                self.vx = 0

        if move_x != 0 and self.on_ground:
            self.run_anim += 0.2
        elif self.on_ground:
            self.run_anim = 0

        want_jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        if want_jump:
            if not self.jump_pressed:
                self.jump_buffer = 8
            self.jump_pressed = True
        else:
            self.jump_pressed = False

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

        if self.on_ground:
            self.coyote_time = 6
        else:
            self.coyote_time = max(0, self.coyote_time - 1)

        if self.jump_buffer > 0 and self.coyote_time > 0:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self.coyote_time = 0
            self.jump_buffer = 0
            self.target_squash = 0.7

        if not want_jump and self.vy < -2:
            self.vy *= 0.85

        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        if self.vy > 0 and not self.on_ground:
            self.target_squash = 1.2
        elif self.on_ground:
            self.target_squash = 1.0

        self.squash_stretch += (self.target_squash - self.squash_stretch) * 0.2

        self.x += self.vx
        self._resolve_horizontal(platforms)

        self.y += self.vy
        was_on_ground = self.on_ground
        self.on_ground = False
        self._resolve_vertical(platforms, was_on_ground)

        if self.x < 0:
            self.x = 0
            self.vx = 0
        if self.x + self.width > 3000:
            self.x = 3000 - self.width
            self.vx = 0

        if self.y > SCREEN_HEIGHT + 100:
            self.x = 100
            self.y = 0
            self.vx = 0
            self.vy = 0

        self.blink_timer += 1
        if self.blink_timer > 180:
            self.eye_blink = 4
            self.blink_timer = 0
        if self.eye_blink > 0:
            self.eye_blink -= 1

    def _resolve_horizontal(self, platforms):
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.x = plat.rect.left - self.width
                elif self.vx < 0:
                    self.x = plat.rect.right
                self.vx = 0
                rect = self.get_rect()

    def _resolve_vertical(self, platforms, was_on_ground):
        rect = self.get_rect()
        for plat in platforms:
            if rect.colliderect(plat.rect):
                if self.vy >= 0:
                    self.y = plat.rect.top - self.height
                    self.vy = 0
                    if not was_on_ground and not self.on_ground:
                        self.target_squash = 1.3
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = plat.rect.bottom
                    self.vy = 0
                rect = self.get_rect()

    def draw(self, surface, camera_x):
        sx = self.x - camera_x
        sy = self.y
        stretch_x = 1 / self.squash_stretch
        stretch_y = self.squash_stretch

        cx = sx + self.width / 2
        cy = sy + self.height / 2

        draw_w = self.width * stretch_x
        draw_h = self.height * stretch_y

        body_rect = pygame.Rect(
            cx - draw_w / 2,
            cy - draw_h / 2 + 2 * (1 - stretch_y),
            draw_w,
            draw_h
        )

        shadow_rect = pygame.Rect(
            body_rect.x + 2,
            body_rect.y + 2,
            body_rect.width,
            body_rect.height
        )
        pygame.draw.rect(surface, PLAYER_DARK, shadow_rect, border_radius=5)
        pygame.draw.rect(surface, PLAYER_BODY, body_rect, border_radius=5)

        highlight_rect = pygame.Rect(
            body_rect.x + 3,
            body_rect.y + 3,
            body_rect.width - 6,
            body_rect.height / 3
        )
        pygame.draw.rect(surface, PLAYER_LIGHT, highlight_rect, border_radius=3)

        if self.on_ground and abs(self.vx) > 0.5:
            leg_offset = math.sin(self.run_anim) * 3
            foot_y = body_rect.bottom
            foot_lx = body_rect.centerx - 5 + leg_offset
            foot_rx = body_rect.centerx + 5 - leg_offset
            pygame.draw.circle(surface, PLAYER_DARK, (int(foot_lx), int(foot_y)), 3)
            pygame.draw.circle(surface, PLAYER_DARK, (int(foot_rx), int(foot_y)), 3)

        eye_y = body_rect.y + body_rect.height * 0.3
        if self.eye_blink > 0:
            blink_y = int(eye_y)
            if self.facing_right:
                pygame.draw.line(surface, PLAYER_PUPIL,
                                 (int(body_rect.centerx + 3), blink_y),
                                 (int(body_rect.centerx + 9), blink_y), 2)
                pygame.draw.line(surface, PLAYER_PUPIL,
                                 (int(body_rect.centerx - 5), blink_y),
                                 (int(body_rect.centerx + 1), blink_y), 2)
            else:
                pygame.draw.line(surface, PLAYER_PUPIL,
                                 (int(body_rect.centerx - 9), blink_y),
                                 (int(body_rect.centerx - 3), blink_y), 2)
                pygame.draw.line(surface, PLAYER_PUPIL,
                                 (int(body_rect.centerx - 1), blink_y),
                                 (int(body_rect.centerx + 5), blink_y), 2)
        else:
            look_offset = 2 if self.facing_right else -2
            if self.facing_right:
                ex1 = body_rect.centerx - 4
                ex2 = body_rect.centerx + 4
            else:
                ex1 = body_rect.centerx - 6
                ex2 = body_rect.centerx + 2
            pygame.draw.circle(surface, PLAYER_EYE, (int(ex1), int(eye_y)), 4)
            pygame.draw.circle(surface, PLAYER_EYE, (int(ex2), int(eye_y)), 4)
            pygame.draw.circle(surface, PLAYER_PUPIL, (int(ex1 + look_offset), int(eye_y)), 2)
            pygame.draw.circle(surface, PLAYER_PUPIL, (int(ex2 + look_offset), int(eye_y)), 2)


class Game:
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

        self.player = Player(100, 400)
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 52)

        self.clouds = []
        rng = random.Random(123)
        for _ in range(12):
            self.clouds.append({
                'x': rng.randint(-200, 3200),
                'y': rng.randint(20, 180),
                'w': rng.randint(60, 140),
                'h': rng.randint(25, 50),
                'speed': rng.uniform(0.1, 0.4)
            })

        self.bg_mountains = []
        rng2 = random.Random(456)
        for _ in range(8):
            self.bg_mountains.append({
                'x': rng2.randint(-100, 3200),
                'h': rng2.randint(80, 200),
                'w': rng2.randint(150, 300)
            })

    def _build_level(self):
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 40, 400, 40, is_ground=True))
        self.platforms.append(Platform(500, SCREEN_HEIGHT - 40, 300, 40, is_ground=True))
        self.platforms.append(Platform(900, SCREEN_HEIGHT - 40, 250, 40, is_ground=True))
        self.platforms.append(Platform(1250, SCREEN_HEIGHT - 40, 400, 40, is_ground=True))
        self.platforms.append(Platform(1800, SCREEN_HEIGHT - 40, 200, 40, is_ground=True))
        self.platforms.append(Platform(2100, SCREEN_HEIGHT - 40, 350, 40, is_ground=True))
        self.platforms.append(Platform(2550, SCREEN_HEIGHT - 40, 450, 40, is_ground=True))

        floating = [
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
        for px, py, pw, ph in floating:
            self.platforms.append(Platform(px, py, pw, ph))

        coin_positions = [
            (200, 450), (360, 380), (540, 320), (720, 400),
            (890, 310), (1040, 230), (1220, 350), (1390, 270),
            (1590, 200), (1740, 320), (1890, 250), (2040, 170),
            (2240, 300), (2440, 220), (2640, 150), (2820, 270),
            (2940, 190),
        ]
        for cx, cy in coin_positions:
            self.coins.append(Coin(cx, cy))

    def _spawn_particles(self, x, y, count, colors=PARTICLE_COLORS, spread=3, life=20, size=3):
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread * 1.5, -0.5)
            color = random.choice(colors)
            l = random.randint(life // 2, life)
            s = random.randint(1, size)
            self.particles.append(Particle(x, y, vx, vy, color, l, s))

    def _update_camera(self):
        target_x = self.player.x - SCREEN_WIDTH / 3
        self.camera_x += (target_x - self.camera_x) * 0.08
        self.camera_x = max(0, min(self.camera_x, 3000 - SCREEN_WIDTH))

    def _draw_sky(self):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
            g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
            b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_mountains(self):
        for m in self.bg_mountains:
            mx = m['x'] - self.camera_x * 0.3
            base_y = SCREEN_HEIGHT - 40
            color = (70, 120, 80)
            points = [
                (mx, base_y),
                (mx + m['w'] / 2, base_y - m['h']),
                (mx + m['w'], base_y)
            ]
            pygame.draw.polygon(self.screen, color, points)
            snow_points = [
                (mx + m['w'] / 2, base_y - m['h']),
                (mx + m['w'] / 2 - m['w'] * 0.12, base_y - m['h'] + m['h'] * 0.2),
                (mx + m['w'] / 2 + m['w'] * 0.12, base_y - m['h'] + m['h'] * 0.2),
            ]
            pygame.draw.polygon(self.screen, (230, 240, 250), snow_points)

    def _draw_clouds(self):
        for c in self.clouds:
            c['x'] += c['speed']
            if c['x'] > 3200:
                c['x'] = -200
            cx = c['x'] - self.camera_x * 0.5
            if -c['w'] < cx < SCREEN_WIDTH + c['w']:
                cloud_surf = pygame.Surface((c['w'], c['h']), pygame.SRCALPHA)
                pygame.draw.ellipse(cloud_surf, (255, 255, 255, 160), (0, c['h'] // 4, c['w'], c['h'] // 2))
                pygame.draw.ellipse(cloud_surf, (255, 255, 255, 180), (c['w'] // 4, 0, c['w'] // 2, c['h']))
                self.screen.blit(cloud_surf, (int(cx), int(c['y'])))

    def _check_coins(self):
        player_rect = self.player.get_rect()
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                coin.collect_anim = 15
                self.score += 10
                self._spawn_particles(coin.x, coin.y, 8,
                                      colors=[COIN_COLOR, COIN_DARK, (255, 255, 200)],
                                      spread=4, life=15, size=4)

    def _draw_hud(self):
        coin_text = self.font.render(f"Coins: {self.score}", True, WHITE)
        shadow_text = self.font.render(f"Coins: {self.score}", True, (0, 0, 0))
        self.screen.blit(shadow_text, (22, 17))
        self.screen.blit(coin_text, (20, 15))

        hint = self.font.render("Arrow/WASD: Move   Space: Jump", True, (50, 50, 80))
        self.screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 15, 15))

    def run(self):
        running = True
        while running:
            self.tick += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            keys = pygame.key.get_pressed()

            old_on_ground = self.player.on_ground
            self.player.update(keys, self.platforms)

            if self.player.on_ground and not old_on_ground and self.player.vy == 0:
                self._spawn_particles(
                    self.player.x + self.player.width / 2,
                    self.player.y + self.player.height,
                    count=6, spread=3, life=15, size=3
                )

            if self.player.on_ground and abs(self.player.vx) > 3 and self.tick % 4 == 0:
                self._spawn_particles(
                    self.player.x + self.player.width / 2,
                    self.player.y + self.player.height,
                    count=2, colors=[(180, 170, 150)], spread=2, life=10, size=2
                )

            self._check_coins()

            for coin in self.coins:
                coin.update()

            self.particles = [p for p in self.particles if p.life > 0]
            for p in self.particles:
                p.update()

            self._update_camera()

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

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
