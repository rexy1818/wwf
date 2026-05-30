from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Dict, Any
import logging

from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])

# Instancia del servicio
video_service = VideoService()

@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_video(
    camera_id: str = Form(..., description="ID de la cámara donde subir el video"),
    file: UploadFile = File(..., description="Archivo de video a subir")
):
    """
    Subir un video a una cámara específica
    
    - **camera_id**: ID de la cámara donde guardar el video
    - **file**: Archivo de video (formatos soportados: mp4, avi, mov, mkv, wmv, flv, webm)
    
    El video se guarda en: storage/camera_id/videos/
    """
    try:
        # Validar que se subió un archivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionó ningún archivo"
            )
        
        result = await video_service.upload_video(camera_id, file)
        logger.info(f"Video subido exitosamente: {result['filename']} para cámara {camera_id}")
        return result
    
    except ValueError as e:
        logger.warning(f"Error de validación subiendo video: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error subiendo video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo video: {str(e)}"
        )

@router.get("/{camera_id}", response_model=List[Dict[str, Any]])
async def list_videos(camera_id: str):
    """
    Listar todos los videos de una cámara
    
    - **camera_id**: ID de la cámara
    
    Retorna información de todos los videos disponibles para procesamiento.
    """
    try:
        videos = video_service.list_videos(camera_id)
        logger.info(f"Listados {len(videos)} videos para cámara {camera_id}")
        return videos
    
    except ValueError as e:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listando videos de cámara {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando videos: {str(e)}"
        )

@router.get("/{camera_id}/{filename}", response_model=Dict[str, Any])
async def get_video_info(camera_id: str, filename: str):
    """
    Obtener información de un video específico
    
    - **camera_id**: ID de la cámara
    - **filename**: Nombre del archivo de video
    
    Retorna metadatos del video incluyendo tamaño, fechas de creación y modificación.
    """
    try:
        video_info = video_service.get_video_info(camera_id, filename)
        logger.info(f"Información obtenida para video: {filename}")
        return video_info
    
    except ValueError as e:
        logger.warning(f"Video no encontrado: {filename} en cámara {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo info de video {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo información del video: {str(e)}"
        )

@router.delete("/{camera_id}/{filename}", response_model=Dict[str, str])
async def delete_video(camera_id: str, filename: str):
    """
    Eliminar un video específico
    
    - **camera_id**: ID de la cámara
    - **filename**: Nombre del archivo de video a eliminar
    
    ⚠️ **ADVERTENCIA**: Esta operación es irreversible.
    """
    try:
        success = video_service.delete_video(camera_id, filename)
        if success:
            logger.info(f"Video eliminado: {filename} de cámara {camera_id}")
            return {"message": f"Video {filename} eliminado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error eliminando el video"
            )
    
    except ValueError as e:
        logger.warning(f"Video no encontrado para eliminar: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error eliminando video {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando video: {str(e)}"
        )