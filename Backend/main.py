from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.videos import router as videos_router

app = FastAPI(
    title="WWF Animal Detection API",
    version="1.0.0"
)

# Permitir React (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Exponer carpeta storage
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
        "status": "OK"
    }