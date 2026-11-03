@echo off
chcp 65001 >nul
title Перезапуск DocFormater

cd /d "%~dp0"

echo Освобождение порта 8080...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8080" ^| findstr "LISTENING"') do (
    echo Завершение процесса PID: %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo Порт освобожден. Перезапуск...
start start_windows.bat
