from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging

from app.schemas.camera import CameraCreate, CameraResponse
from app.services.camera_service import CameraService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cameras", tags=["cameras"])

# Instancia del servicio
camera_service = CameraService()

@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(camera_data: CameraCreate):
    """
    Crear una nueva cámara con estructura de directorios automática
    
    - **nombre**: Nombre descriptivo de la cámara
    - **ubicacion**: Ubicación física de la cámara
    
    Al crear la cámara se genera automáticamente:
    - ID único
    - Estructura de directorios (videos, resultados, evidencias, excel, metadata)
    - Archivo de metadatos
    """
    try:
        camera = camera_service.create_camera(camera_data)
        logger.info(f"Cámara creada exitosamente: {camera.id}")
        return camera
    
    except Exception as e:
        logger.error(f"Error creando cámara: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando cámara: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def list_cameras():
    """
    Listar todas las cámaras disponibles
    
    Retorna información básica de todas las cámaras registradas incluyendo:
    - ID y nombre
    - Ubicación
    - Fecha de creación
    - Estadísticas de procesamiento
    """
    try:
        cameras = camera_service.list_cameras()
        logger.info(f"Listadas {len(cameras)} cámaras")
        return cameras
    
    except Exception as e:
        logger.error(f"Error listando cámaras: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando cámaras: {str(e)}"
        )

@router.get("/{camera_id}", response_model=Dict[str, Any])
async def get_camera(camera_id: str):
    """
    Obtener información detallada de una cámara específica
    
    - **camera_id**: ID único de la cámara
    
    Retorna toda la información disponible de la cámara incluyendo metadatos y estadísticas.
    """
    try:
        camera = camera_service.get_camera(camera_id)
        logger.info(f"Información obtenida para cámara: {camera_id}")
        return camera
    
    except ValueError as e:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo cámara: {str(e)}"
        )