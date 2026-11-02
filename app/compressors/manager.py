from pathlib import Path
from typing import Dict, Any, Optional

from app.compressors.base import CompressionError, CompressionResult
from app.compressors.lossless import LosslessPdfCompressor, HAS_PIKEPDF, HAS_PYMUPDF, HAS_PYPDF
from app.compressors.smart import SmartPdfCompressor


class CompressionManager:
    """Orchestrates PDF compression across modes: 'lossless', 'smart_lossless', 'high'."""

    def __init__(self):
        self.lossless_compressor = LosslessPdfCompressor()
        self.smart_compressor = SmartPdfCompressor()

    def get_status(self) -> Dict[str, Any]:
        return {
            "pikepdf_available": HAS_PIKEPDF,
            "pymupdf_available": HAS_PYMUPDF,
            "pypdf_available": HAS_PYPDF,
            "ghostscript_available": self.smart_compressor.gs_binary is not None,
            "modes_supported": [
                {
                    "id": "lossless",
                    "title": "Без потери качества (Lossless)",
                    "description": "100% сохранение исходных пикселей. Оптимизация структуры PDF, сжатие потоков Flate/zlib, объединение Object Streams и удаление мусора.",
                    "recommended_for": "Векторные документы, чертежи, юридические договоры, отчеты"
                },
                {
                    "id": "smart_lossless",
                    "title": "Умное сжатие (Визуально без потерь)",
                    "description": "Идеальный баланс. Текст и вектор остаются безупречными, а встроенные тяжелые сканы и фото оптимизируются без видимого ухудшения.",
                    "recommended_for": "Отсканированные документы, презентации, буклеты"
                },
                {
                    "id": "high",
                    "title": "Максимальное сжатие",
                    "description": "Максимальное уменьшение размера для отправки по почте, мессенджерам или загрузки в порталы с жестким лимитом размера.",
                    "recommended_for": "Отправка по Email, мессенджерам, архивация"
                }
            ]
        }

    def compress_pdf(
        self,
        input_path: Path,
        output_path: Path,
        mode: str = "lossless",
        quality: Optional[int] = None
    ) -> CompressionResult:
        if not input_path.exists():
            raise CompressionError(f"Input file not found: {input_path}")

        mode = (mode or "lossless").lower()

        if mode == "lossless":
            return self.lossless_compressor.compress(input_path, output_path)
        elif mode in ("smart_lossless", "smart", "balanced"):
            return self.smart_compressor.compress(input_path, output_path, mode="smart_lossless", image_quality=quality)
        elif mode in ("high", "max", "extreme"):
            return self.smart_compressor.compress(input_path, output_path, mode="high", image_quality=quality)
        else:
            raise CompressionError(f"Unknown compression mode: {mode}. Allowed: lossless, smart_lossless, high")
