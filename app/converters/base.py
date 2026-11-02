from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConversionError(Exception):
    """Custom exception raised when file conversion fails."""
    pass


@dataclass
class ConversionResult:
    """Result of a document conversion."""
    success: bool
    output_path: Path
    original_size: int
    converted_size: int
    engine_used: str
    duration_seconds: float
    page_count: Optional[int] = None
    warning: Optional[str] = None
