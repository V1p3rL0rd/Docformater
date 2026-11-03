# 📄 DocFormater — Веб-студия конвертации документов и сжатия PDF без потери качества

**DocFormater** — это полнофункциональное современное веб-приложение для конвертации офисных форматов документов (Word, Excel, PowerPoint) в формат PDF, а также профессионального **сжатия PDF файлов без потери качества** (True Lossless).

---

## 🌟 Основные возможности

### 1. 🔄 Конвертация офисных документов в PDF
* **Документы Microsoft Word:** `.docx`, `.doc`, `.odt`, `.rtf`, `.txt`.
* **Электронные таблицы Microsoft Excel:** `.xlsx`, `.xls`, `.ods`, `.csv`.
* **Презентации:** `.pptx`, `.ppt`, `.odp`.
* **Двойной движок конвертации:**
  * **LibreOffice Headless Engine** (рекомендуемый для Docker / серверов): 100% сохранение оригинальной верстки, таблиц, встроенных диаграмм, колонтитулов и макро-разметки. Поддерживает параллельные конвертации за счет изолированных профилей пользователей (`-env:UserInstallation`).
  * **Встроенный Native Python Engine** (`python-docx`, `openpyxl`, `reportlab`): позволяет конвертировать `.docx`, `.xlsx`, `.csv` и `.txt` даже в легковесных средах без установленного LibreOffice.

### 2. 🗜️ Сжатие PDF без потери качества (True Lossless)
В отличие от примитивных онлайн-сервисов, снижающих качество картинок до размытия, в DocFormater реализовано настоящее сжатие без потери качества:
* **Объединение в объектные потоки (Object Streams / PDF 1.5+):** сотни разрозненных текстовых и структурных объектов PDF объединяются в единые непрерывные потоки zlib/deflate.
* **Максимальная компрессия FlateDecode (Level 9):** перепаковка содержимого страниц и встроенных шрифтов.
* **Глубокая чистка мусора (Dead Objects / Orphan Cleanup):** удаление неиспользуемых дескрипторов, устаревших слоев редактирования, дублирующихся шрифтов и избыточных метаданных.
* **Deduplication:** автоматическое обнаружение дубликатов встроенных потоков и замена их на единые ссылки.
* **Линеаризация (Fast Web View):** реструктуризация файла для мгновенного отображения страниц при открытии в браузере.

#### Доступные режимы сжатия в интерфейсе:
1. **«Строго без потерь» (Lossless):**
   * Сохранение исходных пикселей 1 в 1 (математически неизменные растровые и векторные данные).
   * Идеально для чертежей, договоров, отчетов, векторной графики.
2. **«Умное (Визуально неотличимое)» (Smart Visually Lossless):**
   * Текст и вектор остаются абсолютно четкими.
   * Если в документе обнаружены тяжелые сканы или фотографии сверхвысокого разрешения (более 300–600 DPI), они оптимизируются до полиграфических 200 DPI с качеством JPEG 88–90%.
3. **«Максимальное» (High Compression):**
   * Для отправки по почте и в мессенджерах (150 DPI, качество 70%).

### 3. ⚡ Режим «Конвертер + Сжатие в 1 клик»
Позволяет загрузить `.docx` или `.xlsx` файл, конвертировать его в PDF и сразу же оптимизировать размер на выходе.

### 4. 🎨 Современный веб-интерфейс
* Drag-and-drop загрузка файлов с определением форматов.
* Индикаторы экономии места: исходный размер, итоговый размер, процент сжатия и затраченное время.
* Мгновенное скачивание готового файла.
* Автоматическая очистка временных файлов с сервера (по умолчанию через 60 минут).
* Интерактивная документация Swagger API (`/docs`).

---

## 🚀 Быстрый запуск

### Вариант 1: Запуск через Docker (Рекомендуется)

Docker-образ содержит Ubuntu/Debian, Python 3.12, LibreOffice headless со всеми международными шрифтами, Ghostscript и qpdf.

```bash
# Клонируйте репозиторий и перейдите в папку
cd /Users/vianor/GITHUB/docformater

# Сборка и запуск контейнера
docker compose up --build
```

После старта откройте в браузере: **`http://localhost:8000`**

---

### Вариант 2: Локальный запуск (macOS / Linux / Windows)

#### 1. Создание виртуального окружения и установка зависимостей:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Запуск приложения:
```bash
./run.sh
# или напрямую:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Приложение доступно по адресу: **`http://localhost:8000`**

> **Примечание:** Для 100% точной верстки сложных файлов `.doc` и `.xls` на локальном компьютере рекомендуется иметь установленный LibreOffice (`brew install --cask libreoffice` на macOS или `sudo apt install libreoffice` на Ubuntu). Если LibreOffice не установлен, DocFormater автоматически переключится на встроенный Python-движок (`python-docx` + `openpyxl` + `reportlab`).

---

## 📡 REST API Документация

DocFormater предоставляет простой и удобный REST API. Полная интерактивная спецификация Swagger доступна по адресу `http://localhost:8000/docs`.

### 1. Статус системы
```http
GET /api/status
```
Возвращает информацию о доступных движках конвертации и сжатия.

### 2. Конвертация документа в PDF
```http
POST /api/convert
Content-Type: multipart/form-data
```
Параметры:
* `file`: файл (`.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.csv`, `.txt` и т.д.)

**Пример запроса через curl:**
```bash
curl -X POST "http://localhost:8000/api/convert" \
     -F "file=@sample_contract.docx"
```

**Ответ JSON:**
```json
{
  "success": true,
  "file_id": "93b2a543-34e1-4560-84a1-8d26c19a4e8d",
  "original_filename": "sample_contract.docx",
  "download_filename": "sample_contract.pdf",
  "original_size": 37211,
  "converted_size": 2301,
  "engine_used": "native_python_docx",
  "duration_seconds": 0.02,
  "download_url": "/api/download/93b2a543-34e1-4560-84a1-8d26c19a4e8d.pdf?filename=sample_contract.pdf"
}
```

### 3. Сжатие PDF
```http
POST /api/compress
Content-Type: multipart/form-data
```
Параметры:
* `file`: PDF файл (`.pdf`)
* `mode`: `lossless` (по умолчанию), `smart_lossless` или `high`

**Пример запроса через curl:**
```bash
curl -X POST "http://localhost:8000/api/compress" \
     -F "file=@presentation.pdf" \
     -F "mode=lossless"
```

**Ответ JSON:**
```json
{
  "success": true,
  "original_size": 15420000,
  "compressed_size": 4210000,
  "saved_bytes": 11210000,
  "saved_percent": 72.7,
  "engine_used": "pikepdf (QPDF Lossless Engine)",
  "mode": "lossless",
  "download_url": "/api/download/..."
}
```

### 4. Конвертация и сжатие в 1 запрос
```http
POST /api/convert-and-compress
Content-Type: multipart/form-data
```

---

## 📂 Структура проекта

```
docformater/
├── app/
│   ├── api/                     # Вспомогательные схемы и валидация
│   ├── compressors/             # Движки сжатия PDF
│   │   ├── base.py              # Интерфейсы и структуры данных
│   │   ├── lossless.py          # Lossless сжатие (QPDF/pikepdf, pypdf, MuPDF)
│   │   ├── smart.py             # Visually lossless & High compression (Pillow)
│   │   └── manager.py           # Маршрутизатор режимов сжатия
│   ├── converters/              # Движки конвертации документов в PDF
│   │   ├── base.py              # Интерфейсы
│   │   ├── libreoffice.py       # Headless LibreOffice CLI с изоляцией профилей
│   │   ├── docx_converter.py    # Native Python DOCX -> PDF
│   │   ├── excel_converter.py   # Native Python XLSX/CSV -> PDF
│   │   └── manager.py           # Автовыбор лучшего доступного конвертера
│   ├── services/
│   │   ├── storage.py           # Хранилище, проверка размеров и безопасность
│   │   └── cleaner.py           # Фоновая очистка временных файлов
│   ├── static/                  # Веб-интерфейс (SPA)
│   │   ├── css/style.css        # Современный стек стилей
│   │   ├── js/app.js            # Логика Drag-and-Drop, запросов и метрик
│   │   └── index.html           # Разметка веб-приложения
│   ├── config.py                # Конфигурация сервиса
│   └── main.py                  # FastAPI приложение и эндпоинты
├── tests/                       # Автоматические тесты
│   ├── test_converter.py        # Тестирование конвертации Word и Excel
│   ├── test_compressor.py       # Тестирование сжатия без потерь
│   ├── test_api.py              # Тестирование REST API
│   └── generate_test_samples.py # Генератор тестовых образцов
├── sample_files/                # Образцы файлов для проверки
├── Dockerfile                   # Docker контейнер с LibreOffice и шрифтами
├── docker-compose.yml           # Compose манифест для мгновенного запуска
├── requirements.txt             # Зависимости Python
├── run.sh                       # Скрипт быстрого запуска
└── README.md                    # Документация проекта
```

---

## 🧪 Запуск тестов

Для проверки работоспособности всех модулей выполните:

```bash
# Тестирование конвертеров
PYTHONPATH=. ./venv/bin/python tests/test_converter.py

# Тестирование сжатия PDF
PYTHONPATH=. ./venv/bin/python tests/test_compressor.py

# Тестирование REST API
PYTHONPATH=. ./venv/bin/python tests/test_api.py
```

Все тесты проходят без ошибок:
```
Ran 3 tests in 0.034s - OK (test_converter.py)
Ran 3 tests in 0.084s - OK (test_compressor.py)
Ran 5 tests in 0.108s - OK (test_api.py)
```

---

## 🔒 Безопасность и хранение данных

* **Изоляция:** Каждый загружаемый файл сохраняется под случайным UUID4 без сохранения небезопасных путей файловой системы.
* **Защита от переполнения диска:** Исходный файл удаляется сразу после обработки, а готовый PDF автоматически удаляется через 60 минут фоновой задачей.
* **Лимиты:** Максимальный размер загружаемого файла по умолчанию ограничен 100 МБ (настраивается переменной окружения `MAX_FILE_SIZE_MB`).
