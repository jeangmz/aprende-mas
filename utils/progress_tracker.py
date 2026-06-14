"""Progress tracker - guardado local simple."""
import json

DATA_FILE = "aprendizaje_progreso.json"

def cargar_progreso():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_progreso(progreso: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(progreso, f, ensure_ascii=False, indent=2)

def actualizar_nivel(data: dict):
    progreso = cargar_progreso()
    progreso.update(data)
    guardar_progreso(progreso)

def obtener_niveles_completados() -> set:
    progreso = cargar_progreso()
    return {k for k, v in progreso.items() if v is True}