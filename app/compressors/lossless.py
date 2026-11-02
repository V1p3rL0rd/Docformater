import os
import shutil
import time
from pathlib import Path
from typing import Optional

from app.compressors.base import CompressionError, CompressionResult

# Check available backends
try:
    import pikepdf
    HAS_PIKEPDF = True
except ImportError:
    HAS_PIKEPDF = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class LosslessPdfCompressor:
    """
    Performs true lossless PDF compression.
    No image downsampling or lossy recompression is performed.
    Mathematically preserves all text, vectors, and pixels while drastically
    reducing file size through structural optimization, stream deflate,
    object streams packing, and unreferenced object removal.
    """

    def __init__(self):
        pass

    def compress(self, input_file: Path, output_file: Path) -> CompressionResult:
        if not input_file.exists():
            raise CompressionError(f"Input file not found: {input_file}")

        orig_size = input_file.stat().st_size
        start_time = time.time()
        engine_used = "unknown"
        page_count = 0

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Best: pikepdf (QPDF engine)
        if HAS_PIKEPDF:
            try:
                engine_used = "pikepdf (QPDF Lossless Engine)"
                with pikepdf.open(input_file) as pdf:
                    page_count = len(pdf.pages)
                    
                    # Remove unreferenced objects
                    try:
                        pdf.remove_unreferenced_resources()
                    except Exception:
                        pass

                    # Save with maximum lossless stream compression and modern object streams
                    pdf.save(
                        output_file,
                        compress_streams=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate,
                        recompress_flate=True,
                        linearize=True,
                    )
            except Exception as e:
                # If pikepdf failed, attempt fallback
                engine_used = None

        # 2. PyMuPDF (fitz) with garbage collection and deflate
        if (engine_used is None or not HAS_PIKEPDF) and HAS_PYMUPDF:
            try:
                engine_used = "PyMuPDF (Garbage Collection + Deflate)"
                doc = fitz.open(input_file)
                page_count = len(doc)
                doc.save(
                    output_file,
                    garbage=4,          # Deep garbage collection & deduplication
                    deflate=True,        # Deflate streams
                    deflate_images=True, # Lossless deflate for uncompressed images
                    deflate_fonts=True,  # Deflate font tables
                    clean=True,          # Clean & sanitize content syntax
                    linear=True,         # Fast web view
                )
                doc.close()
            except Exception:
                engine_used = None

        # 3. pypdf fallback
        if (engine_used is None or (not HAS_PIKEPDF and not HAS_PYMUPDF)) and HAS_PYPDF:
            try:
                engine_used = "pypdf (Lossless Deflate)"
                reader = pypdf.PdfReader(str(input_file))
                writer = pypdf.PdfWriter()
                page_count = len(reader.pages)

                for page in reader.pages:
                    page.compress_content_streams(level=9)
                    writer.add_page(page)

                # Compress identical duplicate objects
                try:
                    writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
                except Exception:
                    pass

                with open(output_file, "wb") as f_out:
                    writer.write(f_out)
            except Exception as e:
                raise CompressionError(f"Lossless compression failed: {e}")

        if not output_file.exists():
            raise CompressionError("No output file generated during lossless compression.")

        compressed_size = output_file.stat().st_size
        duration = time.time() - start_time

        # If the file was already maximally compressed and adding object streams
        # made it slightly larger or equal, we keep the original
        if compressed_size > orig_size:
            shutil.copy2(input_file, output_file)
            compressed_size = orig_size
            details = "Файл уже был максимально оптимизирован. Размер сохранён."
        else:
            details = f"Сжато алгоритмом {engine_used} без малейшей потери качества."

        saved_bytes = max(0, orig_size - compressed_size)
        saved_percent = round((saved_bytes / orig_size) * 100, 2) if orig_size > 0 else 0.0

        return CompressionResult(
            success=True,
            output_path=output_file,
            original_size=orig_size,
            compressed_size=compressed_size,
            saved_bytes=saved_bytes,
            saved_percent=saved_percent,
            engine_used=engine_used,
            mode="lossless",
            duration_seconds=round(duration, 3),
            page_count=page_count,
            details=details,
        )
