@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo    平台跳跃 - 游戏启动器
echo ========================================
echo.

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 pygame，正在自动安装...
    pip install pygame
    if errorlevel 1 (
        echo [错误] pygame 安装失败，请手动执行: pip install pygame
        pause
        exit /b 1
    )
    echo [信息] pygame 安装成功！
    echo.
)

echo [信息] 正在启动游戏...
echo.

python "%SCRIPT_DIR%platform_jumper.py"

if errorlevel 1 (
    echo.
    echo [错误] 游戏异常退出！
    pause
)

endlocal
exit /b 0
