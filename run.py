import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import HOST, PORT


def open_browser(url: str):
    """Opens default browser after short delay to let server start."""
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    import uvicorn

    server_url = f"http://{'127.0.0.1' if HOST in ('0.0.0.0', '') else HOST}:{PORT}"
    docs_url = f"{server_url}/docs"

    print("=" * 60)
    print(f"  DocFormater — Office & PDF Processing Studio")
    print(f"  Web Interface: {server_url}")
    print(f"  API Docs (Swagger): {docs_url}")
    print("=" * 60)

    # Launch browser if not in headless or container environment
    if not os.getenv("DOCKER_CONTAINER") and not os.getenv("HEADLESS"):
        threading.Thread(target=open_browser, args=(server_url,), daemon=True).start()

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
