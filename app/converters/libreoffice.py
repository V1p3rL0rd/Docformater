import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from app.config import LIBREOFFICE_PATH
from app.converters.base import ConversionError, ConversionResult


def find_libreoffice_binary() -> Optional[str]:
    """
    Search for LibreOffice / soffice binary across common OS installation locations.
    Returns path to executable or None if not found.
    """
    if LIBREOFFICE_PATH and os.path.exists(LIBREOFFICE_PATH):
        return LIBREOFFICE_PATH

    # Check PATH
    for name in ("soffice", "libreoffice", "soffice.bin", "libreoffice.bin"):
        path = shutil.which(name)
        if path:
            return path

    # Check common platform-specific paths
    common_paths = [
        # macOS
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "~/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        # Linux
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/opt/libreoffice/program/soffice",
        "/snap/bin/libreoffice",
        # Windows
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for p in common_paths:
        expanded = Path(p).expanduser().resolve()
        if expanded.exists() and os.access(expanded, os.X_OK):
            return str(expanded)

    return None


class LibreOfficeConverter:
    """Headless LibreOffice document to PDF converter."""

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path or find_libreoffice_binary()

    @property
    def is_available(self) -> bool:
        return self.binary_path is not None and Path(self.binary_path).exists()

    def convert(self, input_file: Path, output_file: Path, timeout: int = 60) -> ConversionResult:
        """
        Convert any LibreOffice-supported document (docx, xlsx, pptx, doc, xls, etc.) to PDF.
        """
        if not self.is_available:
            raise ConversionError("LibreOffice binary not found on this system.")

        if not input_file.exists():
            raise ConversionError(f"Input file does not exist: {input_file}")

        start_time = time.time()
        orig_size = input_file.stat().st_size

        # Create isolated temp directory for outdir and user profile to prevent concurrency locking
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profile_dir = Path(temp_dir) / "lo_profile"
            temp_profile_dir.mkdir(parents=True, exist_ok=True)
            temp_out_dir = Path(temp_dir) / "output"
            temp_out_dir.mkdir(parents=True, exist_ok=True)

            profile_arg = f"-env:UserInstallation=file://{temp_profile_dir.as_posix()}"

            cmd = [
                self.binary_path,
                profile_arg,
                "--headless",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                "--nolockcheck",
                "--nologo",
                "--norestore",
                "--convert-to",
                "pdf",
                "--outdir",
                str(temp_out_dir),
                str(input_file),
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                raise ConversionError(f"LibreOffice conversion timed out after {timeout} seconds.")
            except Exception as e:
                raise ConversionError(f"Failed to execute LibreOffice: {e}")

            if proc.returncode != 0:
                err_msg = proc.stderr.decode("utf-8", errors="replace").strip()
                out_msg = proc.stdout.decode("utf-8", errors="replace").strip()
                raise ConversionError(f"LibreOffice error (exit code {proc.returncode}): {err_msg or out_msg}")

            # LibreOffice names the output file with the same stem and .pdf extension
            expected_pdf_name = f"{input_file.stem}.pdf"
            generated_pdf = temp_out_dir / expected_pdf_name

            if not generated_pdf.exists():
                # In case stem was altered or multiple files produced
                pdf_files = list(temp_out_dir.glob("*.pdf"))
                if pdf_files:
                    generated_pdf = pdf_files[0]
                else:
                    raise ConversionError("LibreOffice completed but no PDF output file was produced.")

            # Move to target output_file
            output_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(generated_pdf, output_file)

        duration = time.time() - start_time
        converted_size = output_file.stat().st_size

        return ConversionResult(
            success=True,
            output_path=output_file,
            original_size=orig_size,
            converted_size=converted_size,
            engine_used="libreoffice",
            duration_seconds=round(duration, 3),
        )
