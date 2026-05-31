from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.videos import router as videos_router

# Aseguramos que la carpeta existe antes de montar
if not os.path.exists("storage"):
    os.makedirs("storage")
    os.makedirs("storage/uploads")
    os.makedirs("storage/best")

app = FastAPI(
    title="WWF Animal Detection API",
    version="1.0.0"
)

# CORS corregido para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exponer carpeta storage
# Esto permite que http://localhost:8000/storage/best/foto.jpg funcione
app.mount(
    "/storage",
    StaticFiles(directory="storage"),
    name="storage"
)

app.include_router(
    videos_router,
    prefix="/videos",
    tags=["Videos"]
)

@app.get("/")
def root():
    return {
        "message": "WWF API Running",
        "status": "OK",
        "gpu_available": False # Informativo ya que usas CPU
    }