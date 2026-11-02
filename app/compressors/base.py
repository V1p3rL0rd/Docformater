from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class CompressionError(Exception):
    """Exception raised when PDF compression fails."""
    pass


@dataclass
class CompressionResult:
    """Detailed result of PDF compression."""
    success: bool
    output_path: Path
    original_size: int
    compressed_size: int
    saved_bytes: int
    saved_percent: float
    engine_used: str
    mode: str
    duration_seconds: float
    page_count: int
    details: Optional[str] = None
