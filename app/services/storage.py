import shutil
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

from app.config import UPLOAD_DIR, OUTPUT_DIR, MAX_FILE_SIZE_BYTES


class StorageService:
    """Manages file storage, temporary paths, and uploads."""

    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.output_dir = OUTPUT_DIR

    async def save_upload(self, file: UploadFile) -> Tuple[str, Path, str]:
        """
        Saves an uploaded file to storage.
        Returns (file_id, saved_path, original_filename).
        """
        file_id = str(uuid.uuid4())
        original_name = file.filename or "document"
        suffix = Path(original_name).suffix.lower()
        
        # Safe storage filename
        stored_filename = f"{file_id}{suffix}"
        target_path = self.upload_dir / stored_filename

        total_bytes = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(target_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    # Cleanup before raising
                    if target_path.exists():
                        target_path.unlink()
                    raise ValueError(f"File size exceeds maximum allowed limit ({MAX_FILE_SIZE_BYTES // (1024*1024)} MB)")
                buffer.write(chunk)

        return file_id, target_path, original_name

    def get_output_path(self, file_id: str, suffix: str = ".pdf") -> Path:
        """Returns the destination path for processed files."""
        return self.output_dir / f"{file_id}{suffix}"

    def get_download_path(self, filename: str) -> Path:
        """Resolves file path in output storage."""
        # Sanitize filename against directory traversal
        safe_name = Path(filename).name
        target = self.output_dir / safe_name
        return target
