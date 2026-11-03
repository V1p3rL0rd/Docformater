// DocFormater Frontend Application Logic
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const tabs = document.querySelectorAll(".tab-btn");
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const selectedFileCard = document.getElementById("selected-file-card");
  const fileNameDisplay = document.getElementById("file-name");
  const fileSizeDisplay = document.getElementById("file-size");
  const removeFileBtn = document.getElementById("remove-file-btn");
  const compressionOptions = document.getElementById("compression-options");
  const reverseOptions = document.getElementById("reverse-options");
  const actionBtn = document.getElementById("action-btn");
  const actionBtnText = document.getElementById("action-btn-text");

  const uploadView = document.getElementById("upload-view");
  const processingView = document.getElementById("processing-view");
  const processingText = document.getElementById("processing-text");
  const resultView = document.getElementById("result-view");

  const statOrigSize = document.getElementById("stat-orig-size");
  const statFinalSize = document.getElementById("stat-final-size");
  const statSaved = document.getElementById("stat-saved");
  const statDuration = document.getElementById("stat-duration");
  const engineDetails = document.getElementById("engine-details");
  const downloadLink = document.getElementById("download-link");
  const resetBtn = document.getElementById("reset-btn");
  const toast = document.getElementById("toast");
  const systemStatusBadge = document.getElementById("system-status-badge");

  // State
  let currentTab = "convert"; // 'convert' | 'compress' | 'combo'
  let selectedFile = null;

  // File accept configuration per tab
  const tabConfigs = {
    convert: {
      accept: ".doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.rtf,.txt,.csv",
      title: "Перетащите файл Word, Excel или презентацию",
      subtitle: "Поддерживаются: DOC, DOCX, XLS, XLSX, PPT, PPTX, CSV, TXT",
      btnText: "Конвертировать в PDF",
      showCompressionOptions: false,
      showReverseOptions: false,
    },
    reverse: {
      accept: ".pdf",
      title: "Перетащите PDF файл для конвертации в Word или Excel",
      subtitle: "Поддерживаются файлы .PDF с текстом, таблицами и графикой",
      btnText: "Конвертировать из PDF",
      showCompressionOptions: false,
      showReverseOptions: true,
    },
    compress: {
      accept: ".pdf",
      title: "Перетащите PDF файл для сжатия",
      subtitle: "Поддерживаются файлы .PDF любого размера",
      btnText: "Сжать PDF",
      showCompressionOptions: true,
      showReverseOptions: false,
    },
    combo: {
      accept: ".doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,.rtf,.txt,.csv",
      title: "Перетащите документ для конвертации и сжатия",
      subtitle: "Сконвертирует в PDF и сразу сожмет без потери качества",
      btnText: "Конвертировать и сжать",
      showCompressionOptions: true,
      showReverseOptions: false,
    },
  };

  // Check backend status
  fetchSystemStatus();

  // Tab switching
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentTab = tab.dataset.tab;
      applyTabConfig();
      resetFileSelection();
    });
  });

  function applyTabConfig() {
    const config = tabConfigs[currentTab];
    fileInput.accept = config.accept;
    document.getElementById("dropzone-title").textContent = config.title;
    document.getElementById("dropzone-subtitle").textContent = config.subtitle;
    actionBtnText.textContent = config.btnText;
    compressionOptions.style.display = config.showCompressionOptions ? "block" : "none";
    reverseOptions.style.display = config.showReverseOptions ? "block" : "none";
  }

  // File drag & drop
  ["dragenter", "dragover"].forEach((event) => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((event) => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  dropzone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", () => {
    resetFileSelection();
  });

  function handleFileSelected(file) {
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = formatBytes(file.size);
    selectedFileCard.style.display = "flex";
    actionBtn.disabled = false;
  }

  function resetFileSelection() {
    selectedFile = null;
    fileInput.value = "";
    selectedFileCard.style.display = "none";
    actionBtn.disabled = true;
  }

  // Submit Processing
  actionBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    showView("processing");

    const formData = new FormData();
    formData.append("file", selectedFile);

    let endpoint = "/api/convert";
    if (currentTab === "reverse") {
      endpoint = "/api/convert-from-pdf";
      const targetFormat = document.querySelector('input[name="reverse_format"]:checked')?.value || "docx";
      formData.append("target_format", targetFormat);
      processingText.textContent = `Конвертация PDF в ${targetFormat.toUpperCase()}...`;
    } else if (currentTab === "compress") {
      endpoint = "/api/compress";
      const selectedMode = document.querySelector('input[name="compression_mode"]:checked')?.value || "lossless";
      formData.append("mode", selectedMode);
      processingText.textContent = "Оптимизация и сжатие структуры PDF...";
    } else if (currentTab === "combo") {
      endpoint = "/api/convert-and-compress";
      const selectedMode = document.querySelector('input[name="compression_mode"]:checked')?.value || "lossless";
      formData.append("mode", selectedMode);
      processingText.textContent = "Конвертация в PDF и оптимизация потоков...";
    } else {
      processingText.textContent = "Конвертация документа в PDF...";
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Произошла ошибка при обработке файла.");
      }

      showResults(data);
    } catch (err) {
      showError(err.message);
      showView("upload");
    }
  });

  function showResults(data) {
    showView("result");

    if (currentTab === "convert") {
      statOrigSize.textContent = formatBytes(data.original_size);
      statFinalSize.textContent = formatBytes(data.converted_size);
      statSaved.textContent = "Готово";
      statSaved.className = "stat-value";
      statDuration.textContent = `${data.duration_seconds} с`;
      engineDetails.innerHTML = `<strong>Движок конвертации:</strong> ${data.engine_used} ${data.warning ? `<br><span style="color:var(--warning)">⚠️ ${data.warning}</span>` : ""}`;
    } else if (currentTab === "reverse") {
      statOrigSize.textContent = formatBytes(data.original_size);
      statFinalSize.textContent = formatBytes(data.converted_size);
      statSaved.textContent = data.target_format.toUpperCase();
      statSaved.className = "stat-value stat-saved";
      statDuration.textContent = `${data.duration_seconds} с`;
      engineDetails.innerHTML = `<strong>Движок обратной конвертации:</strong> ${data.engine_used}<br><strong>Целевой формат:</strong> .${data.target_format.toUpperCase()}`;
    } else if (currentTab === "compress") {
      statOrigSize.textContent = formatBytes(data.original_size);
      statFinalSize.textContent = formatBytes(data.compressed_size);
      statSaved.textContent = `-${data.saved_percent}%`;
      statSaved.className = "stat-value stat-saved";
      statDuration.textContent = `${data.duration_seconds} с`;
      engineDetails.innerHTML = `<strong>Алгоритм:</strong> ${data.engine_used} (${data.mode})<br>${data.details || ""}`;
    } else {
      // combo
      statOrigSize.textContent = formatBytes(data.original_size);
      statFinalSize.textContent = formatBytes(data.final_size);
      statSaved.textContent = `-${data.saved_percent}%`;
      statSaved.className = "stat-value stat-saved";
      statDuration.textContent = "Быстро";
      engineDetails.innerHTML = `<strong>Конвертация:</strong> ${data.conversion_engine}<br><strong>Сжатие:</strong> ${data.compression_engine}`;
    }

    downloadLink.href = data.download_url;
    downloadLink.download = data.download_filename;
  }

  resetBtn.addEventListener("click", () => {
    resetFileSelection();
    showView("upload");
  });

  function showView(view) {
    uploadView.style.display = view === "upload" ? "block" : "none";
    processingView.style.display = view === "processing" ? "block" : "none";
    resultView.style.display = view === "result" ? "block" : "none";
  }

  function showError(msg) {
    toast.textContent = msg;
    toast.style.display = "block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 5000);
  }

  function formatBytes(bytes, decimals = 1) {
    if (!bytes || bytes === 0) return "0 Б";
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["Б", "КБ", "МБ", "ГБ"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }

  async function fetchSystemStatus() {
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        const loAvailable = data.converter?.libreoffice_available;
        const qpdfAvailable = data.compressor?.pikepdf_available || data.compressor?.pymupdf_available;

        let statusText = "Сервис готов";
        if (loAvailable) {
          statusText += " (LibreOffice + Lossless Engine)";
        } else {
          statusText += " (Python Native + Lossless Engine)";
        }
        systemStatusBadge.innerHTML = `<span class="status-indicator"></span> ${statusText}`;
      }
    } catch {
      systemStatusBadge.innerHTML = `<span class="status-indicator" style="background-color:var(--warning)"></span> Локальный режим`;
    }
  }
});
