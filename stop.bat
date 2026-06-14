@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
setlocal

echo ========================================
echo    平台跳跃 - 停止游戏
echo ========================================
echo.

set "KILLED=0"

for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh ^| findstr /i "python"') do (
    set "PID=%%~a"
    for /f "delims=" %%b in ('wmic process where "processid=%%~a" get commandline 2^>nul ^| findstr /i "platform_jumper.py"') do (
        echo [信息] 找到游戏进程 PID=%%~a，正在终止...
        taskkill /f /pid %%~a >nul 2>&1
        if not errorlevel 1 (
            echo [成功] 已终止进程 PID=%%~a
            set "KILLED=1"
        ) else (
            echo [失败] 无法终止进程 PID=%%~a
        )
    )
)

echo.
if "%KILLED%"=="1" (
    echo [完成] 游戏进程已停止。
) else (
    echo [信息] 未检测到运行中的游戏进程。
)

echo.
echo 按任意键退出...
pause >nul

endlocal
exit /b 0
