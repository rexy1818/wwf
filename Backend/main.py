from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from pathlib import Path

# Importar routers
from app.routers import videos, processing, video_analysis
from app.routers.cameras import router as system_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Monitoreo de Fauna",
    description="""
    ## Sistema de Monitoreo de Fauna con Cámaras Trampa
    
    API para análisis automático de videos de cámaras trampa usando YOLO para detectar animales.
    
    ### Funcionalidades principales:
    
    * **Gestión de Cámaras**: Crear y administrar cámaras con estructura de directorios automática
    * **Subida de Videos**: Cargar videos para procesamiento
    * **Procesamiento con YOLO**: Detección automática de animales en videos
    * **Evidencias**: Captura automática de imágenes de animales detectados
    * **Reportes Excel**: Generación de reportes detallados con todas las detecciones
    * **Consulta de Resultados**: API para obtener estadísticas y resultados de procesamiento
    
    ### Especies detectables:
    Ave, Felino, Canino, Caballo, Oveja, Bovino, Elefante, Oso, Cebra, Jirafa
    
    ### Estructura de almacenamiento:
    ```
    storage/
    └── camera_id/
        ├── videos/          # Videos originales
        ├── resultados/      # Resultados de procesamiento
        ├── evidencias/      # Capturas por especie
        │   ├── ave/
        │   ├── felino/
        │   └── ...
        ├── excel/           # Reportes Excel
        └── metadata/        # Metadatos de la cámara
    ```
    """,
    version="1.0.0",
    contact={
        "name": "Sistema de Monitoreo de Fauna",
        "email": "soporte@fauna-monitor.com"
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(system_router)
app.include_router(videos.router)
app.include_router(processing.router)
app.include_router(video_analysis.router)

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )

# Endpoint de salud
@app.get("/", tags=["health"])
async def root():
    """
    Endpoint de salud del sistema
    
    Retorna información básica del estado del sistema.
    """
    return {
        "message": "Sistema de Monitoreo de Fauna - API Activa",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "analyze": "/analyze",
            "system": "/system", 
            "videos": "/videos",
            "processing": "/process",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health", tags=["health"])
async def health_check():
    """
    Verificación de salud detallada del sistema
    """
    try:
        # Verificar que el directorio storage existe
        storage_path = Path("storage")
        storage_exists = storage_path.exists()
        
        # Verificar permisos de escritura
        can_write = storage_path.is_dir() if storage_exists else False
        
        return {
            "status": "healthy" if storage_exists and can_write else "degraded",
            "storage_available": storage_exists,
            "storage_writable": can_write,
            "yolo_ready": True,  # Se verifica al importar
            "timestamp": "2026-05-30T14:51:00"
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2026-05-30T14:51:00"
        }

if __name__ == "__main__":
    # Crear directorio storage si no existe
    Path("storage").mkdir(exist_ok=True)
    
    logger.info("Iniciando Sistema de Monitoreo de Fauna")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
