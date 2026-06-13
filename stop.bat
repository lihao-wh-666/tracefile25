@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo    Platform Jumper - 停止游戏
echo ========================================
echo.

set "KILLED=0"

for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fo csv /nh ^| findstr /i "python"') do (
    set "PID=%%~p"
    wmic process where "processid=%%~p" get commandline 2>nul | findstr /i "platform_jumper.py" >nul
    if not errorlevel 1 (
        echo [信息] 发现游戏进程 PID=%%~p，正在终止...
        taskkill /f /pid %%~p >nul 2>&1
        if not errorlevel 1 (
            echo [成功] 已终止进程 PID=%%~p
            set "KILLED=1"
        ) else (
            echo [失败] 终止进程 PID=%%~p 失败
        )
    )
)

tasklist /fi "imagename eq python.exe" /fi "windowtitle eq Platform Jumper" /fo csv /nh 2>nul | findstr /r "python.exe" >nul
if not errorlevel 1 (
    for /f "tokens=2" %%p in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq Platform Jumper" /fo csv /nh') do (
        set "PID=%%~p"
        echo [信息] 发现游戏窗口进程 PID=%%~p，正在终止...
        taskkill /f /pid %%~p >nul 2>&1
        if not errorlevel 1 (
            echo [成功] 已终止进程 PID=%%~p
            set "KILLED=1"
        )
    )
)

echo.
if "%KILLED%"=="1" (
    echo [完成] 游戏进程已停止。
) else (
    echo [信息] 未检测到正在运行的游戏进程。
)

endlocal
pause
exit /b 0
