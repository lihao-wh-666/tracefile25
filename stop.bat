@echo off
setlocal

echo ========================================
echo    Platform Jumper - Stop Game
echo ========================================
echo.

set "KILLED=0"

for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh ^| findstr /i "python"') do (
    set "PID=%%~a"
    for /f "delims=" %%b in ('wmic process where "processid=%%~a" get commandline 2^>nul ^| findstr /i "platform_jumper.py"') do (
        echo [INFO] Found game process PID=%%~a, terminating...
        taskkill /f /pid %%~a >nul 2>&1
        if not errorlevel 1 (
            echo [OK] Terminated process PID=%%~a
            set "KILLED=1"
        ) else (
            echo [FAIL] Could not terminate process PID=%%~a
        )
    )
)

for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fi "windowtitle eq Platform Jumper" /fo csv /nh 2^>nul ^| findstr /i "python.exe"') do (
    set "PID=%%~a"
    echo [INFO] Found game window process PID=%%~a, terminating...
    taskkill /f /pid %%~a >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Terminated process PID=%%~a
        set "KILLED=1"
    )
)

echo.
if "%KILLED%"=="1" (
    echo [DONE] Game process stopped.
) else (
    echo [INFO] No running game process detected.
)

echo.
echo Press any key to exit...
pause >nul

endlocal
exit /b 0
