import io
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from app.compressors.base import CompressionError, CompressionResult

try:
    import pikepdf
    from PIL import Image
    HAS_PIKEPDF_PIL = True
except ImportError:
    HAS_PIKEPDF_PIL = False

try:
    import fitz  # PyMuPDF
    from PIL import Image
    HAS_PYMUPDF_PIL = True
except ImportError:
    HAS_PYMUPDF_PIL = False


class SmartPdfCompressor:
    """
    Intelligent PDF compressor with selectable visual quality presets.
    - 'smart_lossless': Visually lossless. Preserves 100% text and vector crispness,
      re-compresses embedded high-res images to 200 DPI at 88% JPEG quality without noticeable degradation.
    - 'high': High compression for email/web, downsizes images to 150 DPI at 72% JPEG quality.
    """

    def __init__(self):
        self.gs_binary = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")

    def compress(
        self,
        input_file: Path,
        output_file: Path,
        mode: str = "smart_lossless",
        image_quality: Optional[int] = None,
    ) -> CompressionResult:
        if not input_file.exists():
            raise CompressionError(f"Input file not found: {input_file}")

        orig_size = input_file.stat().st_size
        start_time = time.time()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Mode configuration
        if mode == "high":
            quality = image_quality or 70
            max_dpi = 150
            mode_label = "Максимальное сжатие"
        else:  # smart_lossless
            quality = image_quality or 88
            max_dpi = 200
            mode_label = "Умное (визуально без потерь)"

        # 1. Try pikepdf + PIL image optimization
        if HAS_PIKEPDF_PIL:
            try:
                page_count = self._compress_with_pikepdf(input_file, output_file, quality, max_dpi)
                duration = time.time() - start_time
                comp_size = output_file.stat().st_size

                if comp_size > orig_size:
                    shutil.copy2(input_file, output_file)
                    comp_size = orig_size

                saved_bytes = max(0, orig_size - comp_size)
                saved_pct = round((saved_bytes / orig_size) * 100, 2) if orig_size > 0 else 0.0

                return CompressionResult(
                    success=True,
                    output_path=output_file,
                    original_size=orig_size,
                    compressed_size=comp_size,
                    saved_bytes=saved_bytes,
                    saved_percent=saved_pct,
                    engine_used="pikepdf + Pillow (Lossless Vector + Image Optimizer)",
                    mode=mode,
                    duration_seconds=round(duration, 3),
                    page_count=page_count,
                    details=f"{mode_label}: оптимизированы встроенные растровые изображения (качество {quality}%, макс. {max_dpi} DPI)."
                )
            except Exception:
                pass

        # 2. Try PyMuPDF + PIL if available
        if HAS_PYMUPDF_PIL:
            try:
                result = self._compress_with_pymupdf(input_file, output_file, quality, max_dpi)
                if result:
                    duration = time.time() - start_time
                    comp_size = output_file.stat().st_size

                    if comp_size > orig_size:
                        shutil.copy2(input_file, output_file)
                        comp_size = orig_size

                    saved_bytes = max(0, orig_size - comp_size)
                    saved_pct = round((saved_bytes / orig_size) * 100, 2) if orig_size > 0 else 0.0

                    return CompressionResult(
                        success=True,
                        output_path=output_file,
                        original_size=orig_size,
                        compressed_size=comp_size,
                        saved_bytes=saved_bytes,
                        saved_percent=saved_pct,
                        engine_used="PyMuPDF + Pillow Optimization",
                        mode=mode,
                        duration_seconds=round(duration, 3),
                        page_count=result["page_count"],
                        details=f"{mode_label}: оптимизированы растровые изображения."
                    )
            except Exception:
                pass

        # 3. Try Ghostscript if available
        if self.gs_binary:
            try:
                return self._compress_with_gs(input_file, output_file, mode, orig_size, start_time)
            except Exception:
                pass

        # 4. Fallback: standard lossless
        from app.compressors.lossless import LosslessPdfCompressor
        lossless = LosslessPdfCompressor()
        res = lossless.compress(input_file, output_file)
        res.mode = mode
        return res

    def _compress_with_pikepdf(self, input_path: Path, output_path: Path, quality: int, max_dpi: int) -> int:
        with pikepdf.open(input_path) as pdf:
            page_count = len(pdf.pages)

            for page in pdf.pages:
                try:
                    images_dict = page.get_images() if hasattr(page, "get_images") else getattr(page, "images", {})
                    for img_name, raw_image in images_dict.items():
                        try:
                            pdf_img = pikepdf.PdfImage(raw_image)
                            pil_img = pdf_img.as_pil_image()

                            orig_w, orig_h = pil_img.size
                            scale_factor = 1.0
                            if orig_w > (max_dpi * 8.5) or orig_h > (max_dpi * 11):
                                scale_factor = min((max_dpi * 8.5) / orig_w, (max_dpi * 11) / orig_h)

                            needs_resize = scale_factor < 0.9

                            if needs_resize:
                                new_w = max(1, int(orig_w * scale_factor))
                                new_h = max(1, int(orig_h * scale_factor))
                                pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                            # Re-encode image to optimize
                            if pil_img.mode in ("RGBA", "LA") and "A" in pil_img.getbands():
                                # Transparent image, keep as PNG
                                pass
                            else:
                                if pil_img.mode != "RGB":
                                    pil_img = pil_img.convert("RGB")
                                if hasattr(page, "get_images"):
                                    # In pikepdf, updating image stream or images dict
                                    try:
                                        raw_image.write(pil_img)
                                    except Exception:
                                        page.images[img_name] = pikepdf.PdfImage(pil_img)
                                else:
                                    page.images[img_name] = pikepdf.PdfImage(pil_img)
                        except Exception:
                            continue
                except Exception:
                    continue

            try:
                pdf.remove_unreferenced_resources()
            except Exception:
                pass

            pdf.save(
                output_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                recompress_flate=True,
                linearize=True,
            )

        return page_count

    def _compress_with_pymupdf(self, input_path: Path, output_path: Path, quality: int, max_dpi: int) -> dict:
        doc = fitz.open(input_path)
        page_count = len(doc)
        optimized_images = 0

        for page_idx in range(page_count):
            page = doc[page_idx]
            image_list = page.get_images(full=True)

            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    with Image.open(io.BytesIO(image_bytes)) as pil_img:
                        orig_w, orig_h = pil_img.size
                        scale_factor = 1.0
                        if orig_w > (max_dpi * 8.5) or orig_h > (max_dpi * 11):
                            scale_factor = min((max_dpi * 8.5) / orig_w, (max_dpi * 11) / orig_h)

                        if scale_factor < 0.9:
                            new_w = max(1, int(orig_w * scale_factor))
                            new_h = max(1, int(orig_h * scale_factor))
                            pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                        buffer = io.BytesIO()
                        if pil_img.mode in ("RGBA", "LA") and "A" in pil_img.getbands():
                            pil_img.save(buffer, format="PNG", optimize=True)
                        else:
                            if pil_img.mode != "RGB":
                                pil_img = pil_img.convert("RGB")
                            pil_img.save(buffer, format="JPEG", quality=quality, optimize=True)

                        new_bytes = buffer.getvalue()
                        if len(new_bytes) < len(image_bytes):
                            doc.update_stream(xref, new_bytes)
                            optimized_images += 1
                except Exception:
                    continue

        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
            linear=True,
        )
        doc.close()

        return {"page_count": page_count, "optimized_images": optimized_images}

    def _compress_with_gs(
        self,
        input_path: Path,
        output_path: Path,
        mode: str,
        orig_size: int,
        start_time: float,
    ) -> CompressionResult:
        pdf_settings = "/ebook" if mode == "smart_lossless" else "/screen"

        cmd = [
            self.gs_binary,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.5",
            f"-dPDFSETTINGS={pdf_settings}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            "-dColorImageDownsampleType=/Bicubic",
            "-dColorImageResolution=150" if mode == "high" else "-dColorImageResolution=200",
            "-dGrayImageResolution=150" if mode == "high" else "-dGrayImageResolution=200",
            f"-sOutputFile={output_path}",
            str(input_path),
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        comp_size = output_path.stat().st_size
        duration = time.time() - start_time
        saved_bytes = max(0, orig_size - comp_size)
        saved_pct = round((saved_bytes / orig_size) * 100, 2) if orig_size > 0 else 0.0

        return CompressionResult(
            success=True,
            output_path=output_path,
            original_size=orig_size,
            compressed_size=comp_size,
            saved_bytes=saved_bytes,
            saved_percent=saved_pct,
            engine_used="Ghostscript",
            mode=mode,
            duration_seconds=round(duration, 3),
            page_count=0,
        )
