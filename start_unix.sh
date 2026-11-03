#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=========================================================="
echo "        DocFormater — Запуск приложения (Linux / macOS)"
echo "=========================================================="
echo ""

# 1. Проверка Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] python3 не найден в системе!"
    echo "Установите Python 3 (на Ubuntu: sudo apt install python3 python3-venv)"
    exit 1
fi

# 2. Создание venv если отсутствует
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "[1/3] Создание виртуального окружения (.venv)..."
    python3 -m venv .venv
    VENV_DIR=".venv"
else
    VENV_DIR=$([ -d ".venv" ] && echo ".venv" || echo "venv")
fi

# 3. Активация и установка зависимостей
echo "[2/3] Проверка и установка зависимостей..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 4. Запуск сервера
echo ""
echo "[3/3] Запуск веб-сервера DocFormater..."
echo "Адрес веб-интерфейса: http://localhost:8080"
echo "Документация Swagger: http://localhost:8080/docs"
echo ""

# Автоматическое открытие в браузере
if command -v open &> /dev/null; then
    (sleep 1.2 && open http://localhost:8080) &
elif command -v xdg-open &> /dev/null; then
    (sleep 1.2 && xdg-open http://localhost:8080) &
fi

exec python run.py
