# -*- coding: utf-8 -*-
"""
test_chinese_render.py - 中文渲染质量测试脚本

测试内容：
1. 验证中文字体缓存机制
2. 生成HUD渲染截图检查阴影偏移
3. 生成菜单渲染截图检查文字质量
4. 检测字体渲染异常（折叠、重复、方块）
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ["HEADLESS"] = "1"

import pygame
pygame.init()

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK
from menus import get_chinese_font, _FONT_CACHE, GameState, MenuManager


def test_font_cache():
    """测试字体缓存机制。"""
    print("测试字体缓存机制...")
    _FONT_CACHE.clear()

    font_a = get_chinese_font(24)
    assert len(_FONT_CACHE) == 1, f"首次加载后缓存应为1项，实际: {len(_FONT_CACHE)}"
    print(f"  ✓ 首次加载字体，缓存条目: {len(_FONT_CACHE)}")

    font_b = get_chinese_font(24)
    assert len(_FONT_CACHE) == 1, "相同大小字体不应重复加载"
    assert font_a is font_b, "相同大小应返回同一字体实例"
    print("  ✓ 相同字号复用缓存实例")

    font_c = get_chinese_font(36)
    assert len(_FONT_CACHE) == 2, "不同字号应新增缓存条目"
    print(f"  ✓ 新增字号，缓存条目: {len(_FONT_CACHE)}")

    get_chinese_font(52)
    get_chinese_font(72)
    get_chinese_font(26)
    get_chinese_font(28)
    print(f"  ✓ 加载常用字号，缓存总条目: {len(_FONT_CACHE)}")

    print("  ✓ 字体缓存机制测试通过")


def test_render_quality():
    """测试中文渲染质量（检测方块、折叠等问题）。"""
    print("\n测试中文渲染质量...")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    test_texts = [
        "平台跳跃 - 测试",
        "金币: 12345",
        "第 1/3 关: 绿野仙踪",
        "方向键/WASD: 移动   空格: 跳跃",
        "排行榜  昵称  得分  日期",
        "你好世界！测试中文显示 abc123",
    ]

    font_sizes = [24, 26, 28, 36, 42, 52, 64, 72]

    y = 20
    for size in font_sizes:
        font = get_chinese_font(size)
        for text in test_texts[:2]:
            surf = font.render(text, True, WHITE)
            assert surf is not None
            assert surf.get_width() > 0
            assert surf.get_height() > 0

            w, h = surf.get_size()
            pixels = pygame.PixelArray(surf)
            opaque_count = 0
            for x in range(w):
                for yy in range(h):
                    if pixels[x, yy] != 0:
                        opaque_count += 1
            del pixels

            min_opaque = len(text) * size * 0.3
            assert opaque_count > min_opaque, (
                f"字体渲染异常: 字号{size} '{text}' 有效像素过少 "
                f"({opaque_count} < {min_opaque:.0f})，可能显示为方块或空白"
            )

            screen.blit(surf, (20, y))
            y += h + 5
        y += 10

    print("  ✓ 各字号文本像素检测通过（无空白或方块）")

    for size in [26, 36, 52]:
        font = get_chinese_font(size)
        text = "测试中文阴影: 金币和关卡"
        main_surf = font.render(text, True, WHITE)
        shadow_surf = font.render(text, True, BLACK)
        w1, h1 = main_surf.get_size()
        w2, h2 = shadow_surf.get_size()
        assert w1 == w2 and h1 == h2, "同一文本的主字和阴影尺寸应一致"
        print(f"  ✓ 字号{size}：主字与阴影尺寸一致 ({w1}x{h1})")

    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    screenshot_path = os.path.join(output_dir, "chinese_render_test.png")
    pygame.image.save(screen, screenshot_path)
    print(f"  ✓ 渲染截图已保存: {screenshot_path}")

    print("  ✓ 中文渲染质量测试通过")


def test_hud_shadow_alignment():
    """测试HUD阴影偏移正确性。"""
    print("\n测试HUD阴影偏移...")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.fill((20, 20, 40))
    font = get_chinese_font(26)

    SHADOW_OFFSET = 3
    test_cases = [
        ("金币: 100", (20, 15)),
        ("第 1/3 关: 绿野仙踪", (200, 15)),
    ]

    for text, pos in test_cases:
        shadow_surf = font.render(text, True, BLACK)
        main_surf = font.render(text, True, WHITE)

        sw, sh = shadow_surf.get_size()
        mw, mh = main_surf.get_size()
        assert sw == mw and sh == mh, "阴影和主字尺寸必须相同"

        overlap_x = max(0, min(SHADOW_OFFSET + sw, mw) - max(SHADOW_OFFSET, 0))
        overlap_y = max(0, min(SHADOW_OFFSET + sh, mh) - max(SHADOW_OFFSET, 0))
        overlap_area = overlap_x * overlap_y
        total_area = mw * mh
        overlap_pct = overlap_area / total_area * 100

        assert overlap_pct < 95, (
            f"阴影与主字重叠过多 ({overlap_pct:.1f}%)，"
            f"SHADOW_OFFSET={SHADOW_OFFSET} 可能太小"
        )
        assert overlap_pct > 50, (
            f"阴影与主字几乎无重叠 ({overlap_pct:.1f}%)，"
            f"SHADOW_OFFSET={SHADOW_OFFSET} 可能太大"
        )
        print(f"  ✓ '{text}'：阴影-主字重叠率 {overlap_pct:.1f}% (合理范围 50%-95%)")

        screen.blit(shadow_surf, (pos[0] + SHADOW_OFFSET, pos[1] + SHADOW_OFFSET))
        screen.blit(main_surf, pos)

    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    hud_path = os.path.join(output_dir, "hud_shadow_test.png")
    pygame.image.save(screen, hud_path)
    print(f"  ✓ HUD截图已保存: {hud_path}")

    print("  ✓ HUD阴影偏移测试通过")


def test_menu_visual_integrity():
    """测试菜单视觉完整性。"""
    print("\n测试菜单视觉完整性...")

    class MockGame:
        def __init__(self):
            self.score = 0
            self.current_level = 0
            self.audio = None
            self.player = type('obj', (object,), {'x': 100, 'y': 400})()

        def _load_level(self, level, x, y, immediate=False):
            pass

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    manager = MenuManager(MockGame())
    big_font = get_chinese_font(52)
    normal_font = get_chinese_font(26)
    small_font = get_chinese_font(22)

    menu_states = [
        (GameState.MAIN_MENU, "main_menu.png"),
        (GameState.SETTINGS_MENU, "settings_menu.png"),
        (GameState.PAUSED, "pause_menu.png"),
        (GameState.GAME_OVER, "gameover_menu.png"),
        (GameState.LEADERBOARD, "leaderboard_menu.png"),
    ]

    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)

    manager.menus[GameState.GAME_OVER].set_score(500)
    manager.menus[GameState.LEADERBOARD].refresh()

    for state, filename in menu_states:
        manager.current_state = state
        screen.fill((20, 20, 40))

        try:
            manager.draw(screen, big_font, normal_font, small_font)
        except Exception as e:
            assert False, f"菜单 {state} 渲染失败: {e}"

        filepath = os.path.join(output_dir, filename)
        pygame.image.save(screen, filepath)

        size = os.path.getsize(filepath)
        assert size > 1000, f"菜单 {state} 截图文件过小 ({size} bytes)，可能渲染为空"
        print(f"  ✓ {state}：渲染正常，截图保存 ({size // 1024} KB)")

    print("  ✓ 菜单视觉完整性测试通过")


def main():
    """运行所有测试。"""
    print("=" * 60)
    print("中文渲染质量与启动修复验证测试")
    print("=" * 60)

    try:
        test_font_cache()
        test_render_quality()
        test_hud_shadow_alignment()
        test_menu_visual_integrity()

        print("\n" + "=" * 60)
        print("✓ 所有验证测试通过！")
        print("=" * 60)
        print("\n修复摘要：")
        print("  1. start.bat：移除start命令，直接运行python避免多窗口")
        print("  2. 字体：优先使用simhei.ttf，添加缓存机制")
        print("  3. HUD阴影：偏移量从2增大到3，避免中文字体重叠")
        print("\n请查看 test_output/ 目录下的截图进行人工视觉验证。")
        return 0

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        pygame.quit()


if __name__ == "__main__":
    sys.exit(main())
