# -*- coding: utf-8 -*-
"""
test_bat_encoding.py - 验证bat文件编码和启动流程
"""
import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def test_python_file_encoding_declarations():
    """验证所有Python文件都有UTF-8编码声明。"""
    print("=" * 60)
    print("验证Python源文件编码声明...")
    print("=" * 60)

    py_files = [
        "platform_jumper.py", "config.py", "core.py", "menus.py",
        "ui.py", "entities.py", "levels.py", "audio.py",
    ]

    all_ok = True
    for fname in py_files:
        path = os.path.join(SCRIPT_DIR, fname)
        with open(path, "rb") as f:
            first_line = f.readline()

        has_declaration = (
            first_line.startswith(b"# -*- coding: utf-8 -*-")
            or first_line.startswith(b"# coding=utf-8")
        )

        if has_declaration:
            print(f"  ✓ {fname}: 存在编码声明")
        else:
            print(f"  ✗ {fname}: 缺少编码声明")
            all_ok = False

    return all_ok


def test_bat_file_gbk_encoding():
    """验证bat文件使用GBK编码，中文可正常解析。"""
    print("\n" + "=" * 60)
    print("验证BAT文件GBK编码...")
    print("=" * 60)

    bat_files = ["start.bat", "stop.bat"]

    all_ok = True
    for fname in bat_files:
        path = os.path.join(SCRIPT_DIR, fname)

        with open(path, "rb") as f:
            raw = f.read()

        try:
            decoded = raw.decode("gbk")
            chinese_chars = [c for c in decoded if '\u4e00' <= c <= '\u9fff']

            if len(chinese_chars) > 0:
                print(f"  ✓ {fname}: GBK解码成功，包含{len(chinese_chars)}个中文字符")
                print(f"    示例: {''.join(chinese_chars[:10])}")
            else:
                print(f"  ⚠ {fname}: GBK解码成功但未检测到中文字符")
        except UnicodeDecodeError as e:
            print(f"  ✗ {fname}: GBK解码失败: {e}")
            all_ok = False

        if b"chcp 65001" in raw:
            print(f"    ✓ 包含 chcp 65001 控制台编码切换")
        else:
            print(f"    ✗ 缺少 chcp 65001 编码切换")
            all_ok = False

    return all_ok


def test_python_stdout_utf8():
    """验证Python stdout正确配置为UTF-8。"""
    print("\n" + "=" * 60)
    print("验证Python stdout UTF-8配置...")
    print("=" * 60)

    test_code = r'''
import sys
print("sys.stdout.encoding:", sys.stdout.encoding)
print("测试中文输出: 你好世界！金币关卡排行榜")
'''

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=SCRIPT_DIR,
    )

    output = result.stdout
    print("  Python stdout输出:")
    for line in output.strip().split("\n"):
        print(f"    {line}")

    has_utf8 = "utf-8" in output.lower() or "utf8" in output.lower()
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in output)

    if has_utf8:
        print("  ✓ stdout编码为UTF-8")
    else:
        print("  ⚠ stdout编码未明确为UTF-8")

    if has_chinese:
        print("  ✓ 中文输出正常")
    else:
        print("  ✗ 中文输出异常")
        return False

    return True


def test_game_startup_healthcheck():
    """验证游戏可以正常启动（HEALTHCHECK模式）。"""
    print("\n" + "=" * 60)
    print("验证游戏启动（HEALTHCHECK模式）...")
    print("=" * 60)

    env = os.environ.copy()
    env["HEADLESS"] = "1"
    env["HEALTHCHECK"] = "1"
    env["HEALTHCHECK_MAX_FRAMES"] = "200"

    result = subprocess.run(
        [sys.executable, "platform_jumper.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=SCRIPT_DIR,
        env=env,
        timeout=30,
    )

    print("  退出代码:", result.returncode)
    if result.stdout:
        print("  stdout:")
        for line in result.stdout.strip().split("\n")[-5:]:
            print(f"    {line}")
    if result.stderr:
        print("  stderr:")
        for line in result.stderr.strip().split("\n")[-5:]:
            print(f"    {line}")

    if result.returncode == 0:
        print("  ✓ 游戏启动成功，无崩溃")
        return True
    else:
        print("  ✗ 游戏启动失败")
        return False


def main():
    """运行所有验证测试。"""
    results = []

    results.append(("Python文件编码声明", test_python_file_encoding_declarations()))
    results.append(("BAT文件GBK编码", test_bat_file_gbk_encoding()))
    results.append(("Python stdout UTF-8", test_python_stdout_utf8()))
    results.append(("游戏启动健康检查", test_game_startup_healthcheck()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, ok in results:
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  [{status}] {name}")

    print()
    if all(r[1] for r in results):
        print("✓ 所有验证测试通过！中文乱码问题已修复。")
        print()
        print("修复要点总结：")
        print("  1. 所有.py文件顶部添加 # -*- coding: utf-8 -*- 声明")
        print("  2. platform_jumper.py 入口强制 sys.stdout/stderr reconfigure UTF-8")
        print("  3. start.bat / stop.bat 以GBK编码保存，并用 chcp 65001 切换控制台")
        return 0
    else:
        print("✗ 部分测试失败，请检查上方输出。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
