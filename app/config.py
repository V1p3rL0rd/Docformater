import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
OUTPUT_DIR = BASE_DIR / "storage" / "outputs"

# Ensure storage directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# File retention in minutes before background auto-cleanup
FILE_RETENTION_MINUTES = int(os.getenv("FILE_RETENTION_MINUTES", "60"))

# Maximum upload file size (default: 100 MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# LibreOffice binary override (optional)
LIBREOFFICE_PATH = os.getenv("LIBREOFFICE_PATH", "")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Allowed extensions
SUPPORTED_OFFICE_EXTENSIONS = {
    ".doc", ".docx", ".odt", ".rtf", ".txt",
    ".xls", ".xlsx", ".ods", ".csv",
    ".ppt", ".pptx", ".odp"
}

SUPPORTED_COMPRESS_EXTENSIONS = {".pdf"}
