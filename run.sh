#!/usr/bin/env bash
set -e

# Change to script directory
cd "$(dirname "$0")"

# Check if venv exists
if [ -d "venv" ]; then
    PYTHON="./venv/bin/python"
    UVICORN="./venv/bin/uvicorn"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
    UVICORN="uvicorn"
else
    echo "Python 3 is required but not found."
    exit 1
fi

echo "=========================================================="
echo " Starting DocuFlow Web Application"
echo " Access URL: http://localhost:8000"
echo " Swagger API: http://localhost:8000/docs"
echo "=========================================================="

exec $UVICORN app.main:app --host 0.0.0.0 --port 8000 --reload
