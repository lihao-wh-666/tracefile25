@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ========================================
echo    Platform Jumper - Game Launcher
echo ========================================
echo.

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [WARN] pygame not detected, installing automatically...
    pip install pygame
    if errorlevel 1 (
        echo [ERROR] Failed to install pygame. Please run: pip install pygame
        pause
        exit /b 1
    )
    echo [INFO] pygame installed successfully.
    echo.
)

echo [INFO] Starting game...
echo.

start "Platform Jumper" python "%SCRIPT_DIR%platform_jumper.py"

timeout /t 2 /nobreak >nul

tasklist /fi "imagename eq python.exe" /fi "windowtitle eq Platform Jumper" | find "python.exe" >nul
if errorlevel 1 (
    echo [WARN] No separate window detected, launching in current process...
    python "%SCRIPT_DIR%platform_jumper.py"
) else (
    echo [OK] Game started successfully!
    echo.
    echo Controls:
    echo   Left/Right Arrow or A/D  - Move
    echo   Space / Up Arrow / W     - Jump (hold for higher jump)
    echo   ESC                      - Quit
)

endlocal
exit /b 0
