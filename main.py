import os
import sys
import subprocess
import webbrowser
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from api.endpoints import router as api_router
from database.chat_repository import ChatRepository
from core.chat_engine import ChatEngine
from config import MODEL_DIR, DATABASE_PATH, DEFAULT_PORT


BANNER = "\n  LEXIMIND\n"


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def open_browser_after_start(port: int, delay: float = 3.0):
    def _open():
        time.sleep(delay)
        webbrowser.open(f"http://127.0.0.1:{port}")
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chat_engine = ChatEngine(MODEL_DIR)
    app.state.chat_repository = ChatRepository(DATABASE_PATH)
    app.state.model_name = app.state.chat_engine.model_name
    yield


app = FastAPI(
    title="LexiMind",
    description="Chatbot persistente con LLM y SQLite",
    version="1.0.0",
    lifespan=lifespan
)

BASE_DIR = get_base_dir()
FRONTEND_DIR = os.path.join(BASE_DIR, "chat", "dist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok", "model": getattr(app.state, "model_name", "not loaded")}


if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    print("-" * 50)
    if not getattr(sys, 'frozen', False):
        print("[*] Construyendo frontend...")
        frontend_dir = os.path.join(BASE_DIR, "chat")
        pkg_json = os.path.join(frontend_dir, "package.json")
        if os.path.exists(pkg_json) and os.path.exists(os.path.join(frontend_dir, "node_modules")):
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True)
    print(f"[*] Iniciando servidor en el puerto {DEFAULT_PORT}")
    open_browser_after_start(DEFAULT_PORT)
    print("-" * 50)
    print(f"[OK] LexiMind esta listo! Abriendo navegador...")
    print(f"     http://127.0.0.1:{DEFAULT_PORT}")
    print("-" * 50)
    print("     Cierra esta ventana cuando quieras salir\n")
    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT)
