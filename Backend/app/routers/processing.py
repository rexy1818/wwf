from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, List, Optional
import logging

from app.schemas.camera import ProcessingResult
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["processing"])

# Instancia del servicio
processing_service = ProcessingService()

@router.post("/camera/{camera_id}", response_model=Dict[str, Any])
async def process_camera_videos(
    camera_id: str,
    interval_seconds: Optional[int] = Query(5, ge=1, le=60, description="Intervalo en segundos entre frames extraídos"),
    confidence_threshold: Optional[float] = Query(0.5, ge=0.1, le=1.0, description="Umbral de confianza mínimo para detecciones")
):
    """
    Procesar todos los videos de una cámara con YOLO para detectar animales
    
    - **camera_id**: ID de la cámara a procesar
    - **interval_seconds**: Intervalo en segundos entre frames (default: 5, rango: 1-60)
    - **confidence_threshold**: Umbral de confianza mínimo (default: 0.5, rango: 0.1-1.0)
    
    **Proceso realizado:**
    1. Recorre todos los videos de la cámara
    2. Extrae frames cada N segundos
    3. Analiza frames con YOLO para detectar animales
    4. Guarda evidencias automáticamente por especie
    5. Genera reporte Excel con todas las detecciones
    
    **Especies detectables:** ave, felino, canino, caballo, oveja, bovino, elefante, oso, cebra, jirafa
    
    ⏱️ **Nota**: El procesamiento puede tomar varios minutos dependiendo del número y tamaño de videos.
    """
    try:
        logger.info(f"Iniciando procesamiento de cámara {camera_id}")
        
        result = await processing_service.process_camera_videos(
            camera_id=camera_id,
            interval_seconds=interval_seconds,
            confidence_threshold=confidence_threshold
        )
        
        logger.info(f"Procesamiento completado para cámara {camera_id}: {result['animales_detectados']} detecciones")
        return result
    
    except ValueError as e:
        logger.warning(f"Error de validación procesando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error procesando cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en procesamiento: {str(e)}"
        )

@router.get("/camera/{camera_id}/results", response_model=Dict[str, Any])
async def get_processing_results(camera_id: str):
    """
    Obtener resultados del último procesamiento de una cámara
    
    - **camera_id**: ID de la cámara
    
    Retorna:
    - Número de videos procesados
    - Total de animales detectados
    - Especies encontradas
    - Ruta del reporte Excel
    - Lista de detecciones
    """
    try:
        results = processing_service.get_processing_results(camera_id)
        logger.info(f"Resultados obtenidos para cámara {camera_id}")
        return results
    
    except ValueError as e:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo resultados de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resultados: {str(e)}"
        )

@router.get("/camera/{camera_id}/history", response_model=List[Dict[str, Any]])
async def get_processing_history(camera_id: str):
    """
    Obtener historial de procesamientos de una cámara
    
    - **camera_id**: ID de la cámara
    
    Retorna lista de todos los procesamientos realizados con metadatos básicos.
    """
    try:
        history = processing_service.get_processing_history(camera_id)
        logger.info(f"Historial obtenido para cámara {camera_id}: {len(history)} procesamientos")
        return history
    
    except Exception as e:
        logger.error(f"Error obteniendo historial de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial: {str(e)}"
        )