"""GEORUSH-owned Ollama lifecycle manager for Windows.

GEORUSH deliberately owns the local Ollama server lifecycle:
- stop any pre-existing Ollama desktop/server processes at GEORUSH start
- start Ollama only when an audit/AI feature needs it
- use CPU AVX2 by default on low-spec machines
- stop the GEORUSH-started server when the desktop application exits
"""
import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx

HOST = "127.0.0.1"
PORT = int(os.getenv("OLLAMA_PORT", "11434"))
BASE_URL = f"http://{HOST}:{PORT}"
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")
LIBRARY = os.getenv("OLLAMA_LLM_LIBRARY", "cpu_avx2")
STARTUP_TIMEOUT = int(os.getenv("OLLAMA_STARTUP_TIMEOUT", "120"))

_process = None
_started_by_georush = False


def _hidden_kwargs():
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


def executable():
    candidates = [
        shutil.which("ollama"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Ollama", "ollama.exe"),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def _windows_kill_all():
    if os.name != "nt":
        return
    # GEORUSH is intentionally the owner of Ollama on this workstation.
    for image in ("ollama app.exe", "ollama.exe"):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", image],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                **_hidden_kwargs(),
            )
        except Exception:
            pass
    time.sleep(0.8)


def online():
    try:
        r = httpx.get(f"{BASE_URL}/api/tags", timeout=2.5)
        return r.status_code == 200
    except Exception:
        return False


def model_available():
    try:
        r = httpx.get(f"{BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        names = {str(x.get("name", "")) for x in r.json().get("models", [])}
        return MODEL in names
    except Exception:
        return False


def status():
    return {
        "provider": "Ollama",
        "online": online(),
        "model": MODEL,
        "model_available": model_available() if online() else False,
        "managed_by_georush": bool(_started_by_georush),
        "llm_library": LIBRARY,
        "base_url": BASE_URL,
        "local": True,
    }


def stop_all():
    global _process, _started_by_georush
    if _process is not None:
        try:
            _process.terminate()
            _process.wait(timeout=5)
        except Exception:
            try:
                _process.kill()
            except Exception:
                pass
    _process = None
    _started_by_georush = False
    _windows_kill_all()
    return not online()


def start():
    global _process, _started_by_georush
    if online():
        # A reachable server may be a previous/background Ollama instance.
        # GEORUSH must own the runtime, so stop it and recreate it with our env.
        stop_all()

    exe = executable()
    if not exe:
        raise RuntimeError("Ollama executable not found. Install Ollama before using GEORUSH local AI.")

    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"{HOST}:{PORT}"
    env["OLLAMA_LLM_LIBRARY"] = LIBRARY
    env.setdefault("OLLAMA_KEEP_ALIVE", "5m")

    _process = subprocess.Popen(
        [exe, "serve"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        **_hidden_kwargs(),
    )
    _started_by_georush = True

    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        if online():
            return status()
        if _process.poll() is not None:
            raise RuntimeError("GEORUSH Ollama server exited during startup.")
        time.sleep(0.5)
    raise RuntimeError("GEORUSH Ollama server did not become ready within the startup timeout.")


def ensure_model():
    if not online():
        start()
    if model_available():
        return status()

    exe = executable()
    if not exe:
        raise RuntimeError("Ollama executable not found while preparing the GEORUSH model.")
    result = subprocess.run(
        [exe, "pull", MODEL],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=1800,
        **_hidden_kwargs(),
    )
    if result.returncode != 0 or not model_available():
        raise RuntimeError(f"Ollama model '{MODEL}' could not be prepared.")
    return status()
