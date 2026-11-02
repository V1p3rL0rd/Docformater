import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    BASE_DIR,
    STATIC_DIR,
    FILE_RETENTION_MINUTES,
    SUPPORTED_OFFICE_EXTENSIONS,
    SUPPORTED_COMPRESS_EXTENSIONS,
    HOST,
    PORT,
)
from app.converters.base import ConversionError
from app.converters.manager import ConversionManager
from app.compressors.base import CompressionError
from app.compressors.manager import CompressionManager
from app.services.cleaner import cleanup_expired_files
from app.services.storage import StorageService


# Background periodic cleanup loop
async def periodic_cleanup_task():
    while True:
        try:
            cleaned = cleanup_expired_files(FILE_RETENTION_MINUTES)
            if cleaned > 0:
                print(f"[Cleanup] Removed {cleaned} expired temporary files.")
        except Exception as e:
            print(f"[Cleanup Error] {e}")
        await asyncio.sleep(600)  # every 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: trigger initial cleanup & launch background task
    cleanup_expired_files(FILE_RETENTION_MINUTES)
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    yield
    # Shutdown
    cleanup_task.cancel()


app = FastAPI(
    title="DocuFlow - PDF & Office Processing Studio",
    description="Веб-сервис для конвертации офисных документов (Word, Excel) в PDF и сжатия PDF файлов без потери качества.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
storage_service = StorageService()
conversion_manager = ConversionManager()
compression_manager = CompressionManager()


# ---------------- API Endpoints ---------------- #

@app.get("/api/status")
async def get_system_status():
    """Returns engine availability and supported operations."""
    return {
        "status": "online",
        "converter": conversion_manager.get_status(),
        "compressor": compression_manager.get_status(),
        "retention_minutes": FILE_RETENTION_MINUTES,
    }


@app.post("/api/convert")
async def convert_document(file: UploadFile = File(...)):
    """
    Convert an office document (DOC, DOCX, XLS, XLSX, PPT, PPTX, etc.) to PDF.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is empty.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_OFFICE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат: {suffix}. Поддерживаются: {', '.join(sorted(SUPPORTED_OFFICE_EXTENSIONS))}"
        )

    try:
        file_id, upload_path, original_filename = await storage_service.save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=413, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {e}")

    output_pdf_path = storage_service.get_output_path(file_id, suffix=".pdf")

    try:
        result = conversion_manager.convert_to_pdf(upload_path, output_pdf_path)
    except ConversionError as ce:
        raise HTTPException(status_code=422, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка конвертации: {e}")
    finally:
        # Cleanup uploaded source file immediately to save disk
        if upload_path.exists():
            try:
                upload_path.unlink()
            except Exception:
                pass

    pdf_stem = Path(original_filename).stem
    download_filename = f"{pdf_stem}.pdf"

    return {
        "success": True,
        "file_id": file_id,
        "original_filename": original_filename,
        "download_filename": download_filename,
        "original_size": result.original_size,
        "converted_size": result.converted_size,
        "engine_used": result.engine_used,
        "duration_seconds": result.duration_seconds,
        "warning": result.warning,
        "download_url": f"/api/download/{output_pdf_path.name}?filename={quote(download_filename)}",
    }


@app.post("/api/compress")
async def compress_pdf_file(
    file: UploadFile = File(...),
    mode: str = Form("lossless"),
    quality: int = Form(None),
):
    """
    Compress a PDF file with lossless, smart_lossless, or high compression modes.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is empty.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_COMPRESS_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Для сжатия принимаются только файлы формата PDF (.pdf)."
        )

    try:
        file_id, upload_path, original_filename = await storage_service.save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=413, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {e}")

    output_pdf_path = storage_service.get_output_path(file_id, suffix=".pdf")

    try:
        result = compression_manager.compress_pdf(
            upload_path,
            output_pdf_path,
            mode=mode,
            quality=quality,
        )
    except CompressionError as ce:
        raise HTTPException(status_code=422, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сжатия: {e}")
    finally:
        if upload_path.exists():
            try:
                upload_path.unlink()
            except Exception:
                pass

    pdf_stem = Path(original_filename).stem
    download_filename = f"{pdf_stem}_compressed.pdf"

    return {
        "success": True,
        "file_id": file_id,
        "original_filename": original_filename,
        "download_filename": download_filename,
        "original_size": result.original_size,
        "compressed_size": result.compressed_size,
        "saved_bytes": result.saved_bytes,
        "saved_percent": result.saved_percent,
        "engine_used": result.engine_used,
        "mode": result.mode,
        "duration_seconds": result.duration_seconds,
        "details": result.details,
        "download_url": f"/api/download/{output_pdf_path.name}?filename={quote(download_filename)}",
    }


@app.post("/api/convert-and-compress")
async def convert_and_compress(
    file: UploadFile = File(...),
    mode: str = Form("lossless"),
):
    """
    Combined pipeline: Converts office document to PDF, then optimizes/compresses the result.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is empty.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_OFFICE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат: {suffix}")

    try:
        file_id, upload_path, original_filename = await storage_service.save_upload(file)
    except ValueError as ve:
        raise HTTPException(status_code=413, detail=str(ve))

    intermediate_pdf = storage_service.get_output_path(f"{file_id}_raw", suffix=".pdf")
    final_pdf = storage_service.get_output_path(file_id, suffix=".pdf")

    try:
        # Step 1: Convert
        conv_result = conversion_manager.convert_to_pdf(upload_path, intermediate_pdf)

        # Step 2: Compress
        comp_result = compression_manager.compress_pdf(
            intermediate_pdf,
            final_pdf,
            mode=mode,
        )
    except (ConversionError, CompressionError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {e}")
    finally:
        for p in (upload_path, intermediate_pdf):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

    pdf_stem = Path(original_filename).stem
    download_filename = f"{pdf_stem}_optimized.pdf"

    return {
        "success": True,
        "file_id": file_id,
        "original_filename": original_filename,
        "download_filename": download_filename,
        "original_size": conv_result.original_size,
        "raw_pdf_size": conv_result.converted_size,
        "final_size": comp_result.compressed_size,
        "saved_percent": comp_result.saved_percent,
        "conversion_engine": conv_result.engine_used,
        "compression_engine": comp_result.engine_used,
        "mode": comp_result.mode,
        "download_url": f"/api/download/{final_pdf.name}?filename={quote(download_filename)}",
    }


@app.get("/api/download/{stored_filename}")
async def download_file(stored_filename: str, filename: str = None):
    """
    Download a converted or compressed file.
    """
    target = storage_service.get_download_path(stored_filename)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Файл не найден или срок его хранения истёк.")

    download_name = filename or target.name
    return FileResponse(
        path=str(target),
        filename=download_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


# Mount static files and index
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"message": "Frontend not ready yet. Access API docs at /docs"})
    return FileResponse(str(index_file))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
