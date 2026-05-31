import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.services.video_analysis_service import VideoAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["video-analysis"])
video_analysis_service = VideoAnalysisService()


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_and_analyze_video(file: UploadFile = File(..., description="Video a analizar")):
    """Subir y analizar un video con SpeciesNet oficial y OCR de banda inferior."""
    try:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se proporciono ningun archivo")
        result = await video_analysis_service.upload_and_analyze_video(file, file.filename)
        logger.info("Video analizado con SpeciesNet: %s", file.filename)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Error analizando video: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error analizando video: {exc}")


@router.post("/upload/batch", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_and_analyze_videos(files: List[UploadFile] = File(..., description="Uno o varios videos a analizar")):
    """Subir y analizar multiples videos en una sola peticion."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se proporciono ningun archivo")
    return await video_analysis_service.upload_and_analyze_videos(files)


@router.post("/detection/{video_id}/{detection_index}/extract-ocr", response_model=Dict[str, Any])
async def extract_ocr_for_detection(video_id: str, detection_index: int):
    """Extraer OCR para una detección específica bajo demanda."""
    try:
        return video_analysis_service.extract_ocr_on_demand(video_id, detection_index)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_all_analyses():
    """Listar los analisis almacenados."""
    return video_analysis_service.list_all_analyses()


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_statistics():
    """Obtener estadisticas generales del sistema."""
    return video_analysis_service.get_system_statistics()


@router.post("/report", response_model=Dict[str, str])
async def generate_excel_report(video_ids: Optional[List[str]] = Query(None, description="IDs de videos especificos")):
    """Generar Excel del flujo SpeciesNet/OCR para los videos indicados o todos."""
    try:
        report_file = video_analysis_service.generate_combined_report(video_ids)
        return {
            "message": "Reporte Excel generado exitosamente",
            "filename": report_file,
            "videos_incluidos": str(len(video_ids)) if video_ids else "todos",
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/file/{camera_id}/{species}/{filename}")
async def get_result_image(camera_id: str, species: str, filename: str):
    """Servir una imagen final desde Resultados/CAMERA_ID/Especie."""
    image_path = Path("Resultados") / camera_id / species / filename
    if not image_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Imagen no encontrada: {filename}")
    return FileResponse(path=str(image_path), media_type="image/jpeg", filename=filename)


@router.get("/excel/{camera_id}")
async def get_camera_excel(camera_id: str):
    """Descargar el Excel generado para una camara."""
    excel_path = Path("Resultados") / camera_id / f"excel_{camera_id}.xlsx"
    if not excel_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Excel no encontrado para camara: {camera_id}")
    return FileResponse(
        path=str(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=excel_path.name,
    )
