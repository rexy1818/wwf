from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VideoUploadRequest(BaseModel):
    pass  # No necesita parámetros, todo se extrae del video

class VideoMetadata(BaseModel):
    filename: str
    file_size: int
    duration: float
    fps: float
    resolution: str
    fecha_video: Optional[str]
    hora_video: Optional[str]
    ubicacion_gps: Optional[str]
    temperatura: Optional[float]  # Si está disponible en metadatos
    camara_id: Optional[str]  # Extraído del nombre o metadatos
    camara_marca: Optional[str]
    camara_modelo: Optional[str]

class AnimalDetection(BaseModel):
    especie: str
    confianza: float
    frame_numero: int
    timestamp_video: float
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    ruta_evidencia: str

class VideoAnalysisResult(BaseModel):
    video_id: str
    metadata: VideoMetadata
    detecciones: List[AnimalDetection]
    total_animales: int
    especies_encontradas: List[str]
    ruta_excel: str
    procesado_en: datetime

class VideoListResponse(BaseModel):
    videos: List[VideoAnalysisResult]
    total_videos: int
    total_detecciones: int
    especies_unicas: List[str]