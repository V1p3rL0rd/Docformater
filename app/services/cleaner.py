import time
import logging
from pathlib import Path
from app.config import UPLOAD_DIR, OUTPUT_DIR, FILE_RETENTION_MINUTES

logger = logging.getLogger("docformater.cleaner")


def cleanup_expired_files(retention_minutes: int = FILE_RETENTION_MINUTES) -> int:
    """
    Deletes files older than retention_minutes from uploads and outputs directories.
    Returns the count of deleted files.
    """
    now = time.time()
    cutoff_time = now - (retention_minutes * 60)
    deleted_count = 0

    for directory in (UPLOAD_DIR, OUTPUT_DIR):
        if not directory.exists():
            continue
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete expired file {file_path}: {e}")

    return deleted_count
