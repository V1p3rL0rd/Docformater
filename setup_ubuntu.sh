#!/usr/bin/env bash
set -e

# Change to script directory
cd "$(dirname "$0")"

echo "=========================================================="
echo "    DocFormater — Установка окружения (Ubuntu / Debian)"
echo "=========================================================="
echo ""

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "[1/4] Обновление репозиториев apt..."
$SUDO apt-get update

echo "[2/4] Установка Python, LibreOffice, Ghostscript, qpdf и шрифтов..."
$SUDO apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-core \
    ghostscript \
    qpdf \
    poppler-utils \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-core \
    fontconfig \
    curl

echo "[3/4] Создание виртуального окружения Python..."
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    python3 -m venv .venv
    VENV_DIR=".venv"
else
    VENV_DIR=$([ -d ".venv" ] && echo ".venv" || echo "venv")
fi

echo "[4/4] Установка Python-зависимостей..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=========================================================="
echo "  Установка успешно завершена!"
echo "  Для запуска выполните: ./start_unix.sh"
echo "  Либо запустите: source $VENV_DIR/bin/activate && python run.py"
echo "=========================================================="
