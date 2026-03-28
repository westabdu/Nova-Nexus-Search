"""
start.py - Nova Nexus Search başlatma scripti.
Backend (FastAPI) ve Frontend (Flet) uygulamalarını birlikte başlatır.
"""
import subprocess
import sys
import os
import time
import threading

# Projenin kök dizinini Python modül arama yoluna ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Alt süreçler için PYTHONPATH ortam değişkenini ayarla
env = os.environ.copy()
existing_pp = env.get("PYTHONPATH", "")
env["PYTHONPATH"] = BASE_DIR + (os.pathsep + existing_pp if existing_pp else "")

def run_backend():
    print("🚀 Backend başlatılıyor (FastAPI:8000)...")
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ],
        cwd=BASE_DIR,
        env=env,
    )

def run_frontend():
    print("🖥️  Frontend başlatılıyor (Flet UI)...")
    time.sleep(3)  # Backend'in önce ayağa kalkmasını bekle
    subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "frontend", "main.py")],
        cwd=BASE_DIR,
        env=env,
    )

if __name__ == "__main__":
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()

    # Frontend ana thread'de çalışır (Flet GUI için gerekli)
    run_frontend()

