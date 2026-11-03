@echo off
chcp 65001 >nul
title DocFormater Studio

echo ==========================================================
echo        DocFormater — Запуск приложения (Windows)
echo ==========================================================
echo.

cd /d "%~dp0"

:: 1. Проверка наличия Python в системе
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    goto :PYTHON_FOUND
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    goto :PYTHON_FOUND
)

echo [ОШИБКА] Python не обнаружен в вашей системе!
echo.
echo Установите Python 3.10, 3.11 или 3.12:
echo 1) Через winget в PowerShell:
echo    winget install Python.Python.3.12
echo 2) Или скачайте установщик с сайта: https://www.python.org/downloads/
echo    ОБЯЗАТЕЛЬНО отметьте галочку: "Add python.exe to PATH"
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [1/3] Python обнаружен: %PYTHON_CMD%

:: 2. Создание виртуального окружения при необходимости
if not exist ".venv" (
    if not exist "venv" (
        echo [2/3] Создание виртуального окружения (.venv)...
        %PYTHON_CMD% -m venv .venv
        if %ERRORLEVEL% neq 0 (
            echo [ОШИБКА] Не удалось создать виртуальное окружение.
            pause
            exit /b 1
        )
    )
)

:: Определение папки venv
set VENV_DIR=.venv
if exist "venv\Scripts\activate.bat" set VENV_DIR=venv

echo [3/3] Активация окружения и проверка зависимостей...
call %VENV_DIR%\Scripts\activate.bat

python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo ==========================================================
echo  Сервер запущен!
echo  Адрес веб-интерфейса: http://localhost:8080
echo  Документация Swagger: http://localhost:8080/docs
echo ==========================================================
echo.

python run.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ВНИМАНИЕ] Сервер остановлен с ошибкой.
    pause
)
