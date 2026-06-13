@echo off
chcp 65001 >nul
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo    Platform Jumper - 平台跳跃游戏启动
echo ========================================
echo.

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到 pygame，正在自动安装...
    pip install pygame
    if errorlevel 1 (
        echo [错误] pygame 安装失败，请手动执行: pip install pygame
        pause
        exit /b 1
    )
    echo [信息] pygame 安装完成。
    echo.
)

echo [信息] 启动游戏中...
echo.

start "Platform Jumper" python "%SCRIPT_DIR%platform_jumper.py"

timeout /t 2 >nul

tasklist /fi "imagename eq python.exe" /fi "windowtitle eq Platform Jumper" | find "python.exe" >nul
if errorlevel 1 (
    echo [警告] 未检测到独立窗口，尝试以当前进程启动...
    python "%SCRIPT_DIR%platform_jumper.py"
) else (
    echo [成功] 游戏已启动！
    echo.
    echo 操作说明:
    echo   ← → 或 A D  - 左右移动
    echo   空格 / ↑ / W - 跳跃（按住跳更高）
    echo   ESC          - 退出游戏
)

endlocal
exit /b 0
