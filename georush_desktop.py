"""GEORUSH one-click Windows desktop launcher.

Starts/uses Ollama silently, ensures the configured local model exists,
starts the GEORUSH FastAPI backend, and opens the desktop UI.
"""
import os
import sys
import time
import socket
import threading
import traceback
import tempfile
import shutil
import subprocess
from pathlib import Path

import httpx
import uvicorn
import webview
from ollama_manager import stop_all as stop_all_ollama

HOST = "127.0.0.1"
PORT = int(os.getenv("GEORUSH_PORT", "8000"))
OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
STARTUP_TIMEOUT = int(os.getenv("GEORUSH_STARTUP_TIMEOUT", "120"))

ollama_process = None
GEORUSH_VERSION = "1.0.0"
LOG_FILE = Path(tempfile.gettempdir()) / "georush-launcher.log"


def log_path():
    return str(LOG_FILE)


def write_log(message):
    try:
        LOG_FILE.write_text(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n", encoding="utf-8")
    except Exception:
        pass


def prepare_ollama_for_georush():
    # Never inherit a system/background Ollama server. GEORUSH owns its runtime.
    stop_all_ollama()



def wait_for_port(timeout=STARTUP_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection((HOST, PORT), timeout=0.4):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def start_api():
    try:
        import main
        config = uvicorn.Config(
            main.app,
            host=HOST,
            port=PORT,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        server.run()
    except Exception as exc:
        write_log(f"GEORUSH API startup failed: {exc!r}")


def cleanup():
    try:
        stop_all_ollama()
    except Exception:
        pass


def startup():
    # Kill any Ollama service left by Windows/Ollama Desktop.
    # The API will start a GEORUSH-owned Ollama server lazily when Audit/AI is used.
    prepare_ollama_for_georush()

    thread = threading.Thread(target=start_api, daemon=True)
    thread.start()
    if not wait_for_port():
        raise RuntimeError(
            "GEORUSH API could not start.\n\n"
            f"Startup log: {log_path()}"
        )


def main():
    try:
        startup()
        webview.create_window(
            f"GEORUSH SEO v{GEORUSH_VERSION}",
            f"http://{HOST}:{PORT}/",
            width=1440,
            height=900,
            min_size=(1100, 700),
            resizable=True,
            background_color="#0b1118",
            text_select=True,
        )
        webview.start()
    except Exception as exc:
        write_log(f"Launcher error: {exc!r}")
        # If running from a terminal, make the error visible; packaged EXE users
        # can inspect the temp log instead.
        if sys.stdout:
            try:
                print(str(exc))
            except Exception:
                pass
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
