import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import video_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Monitoreo de Fauna",
    description=(
        "API para procesar videos de camaras trampa con Google SpeciesNet oficial, "
        "OCR sobre la banda inferior impresa en la imagen, organizacion por camara "
        "y generacion de Excel por Camera ID."
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_analysis.router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Error no manejado: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


@app.get("/", tags=["health"])
async def root():
    return {
        "message": "Sistema de Monitoreo de Fauna - API Activa",
        "version": "3.0.0",
        "status": "healthy",
        "endpoints": {
            "upload": "/analyze/upload",
            "batch": "/analyze/upload/batch",
            "results": "/analyze/results/{video_id}",
            "list": "/analyze/list",
            "stats": "/analyze/stats",
            "excel": "/analyze/excel/{camera_id}",
            "file": "/analyze/file/{camera_id}/{species}/{filename}",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["health"])
async def health_check():
    results_path = Path("Resultados")
    video_analysis_path = Path("video_analysis")
    results_path.mkdir(exist_ok=True)
    video_analysis_path.mkdir(exist_ok=True)
    return {
        "status": "healthy",
        "results_available": results_path.exists(),
        "video_analysis_available": video_analysis_path.exists(),
        "speciesnet_flow": True,
    }


if __name__ == "__main__":
    Path("Resultados").mkdir(exist_ok=True)
    Path("video_analysis").mkdir(exist_ok=True)
    logger.info("Iniciando Sistema de Monitoreo de Fauna")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
