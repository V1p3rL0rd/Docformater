FROM python:3.12-slim-bookworm

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LIBREOFFICE_PATH=/usr/bin/soffice

# Install LibreOffice headless, Ghostscript, qpdf, and extensive font packages for flawless rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    libreoffice-core \
    ghostscript \
    qpdf \
    poppler-utils \
    fonts-dejavu \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-liberation2 \
    fonts-noto-core \
    fonts-noto-cjk \
    fontconfig \
    ca-certificates \
    curl \
    && fc-cache -f -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app

# Ensure storage directories exist with appropriate permissions
RUN mkdir -p /app/storage/uploads /app/storage/outputs && \
    chmod -R 777 /app/storage

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/status || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
