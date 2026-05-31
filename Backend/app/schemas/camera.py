from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CameraCreate(BaseModel):
    nombre: str
    ruta_videos: str  # Ruta donde están los videos de la cámara

class CameraResponse(BaseModel):
    id: str
    nombre: str
    ruta_videos: str  # Ruta donde están los videos
    fecha_creacion: datetime
    ruta_storage: str

class VideoUpload(BaseModel):
    camera_id: str

class DetectionResult(BaseModel):
    video: str
    especie: str
    confianza: float
    fecha_video: str  # Fecha extraída de metadatos del video
    hora_video: str   # Hora extraída de metadatos del video
    ubicacion_gps: Optional[str]  # Coordenadas GPS si están disponibles
    frame: int
    ruta_evidencia: str
    timestamp_video: Optional[str]  # Timestamp original del video

class ProcessingResult(BaseModel):
    videos_procesados: int
    animales_detectados: int
    especies_encontradas: List[str]
    ruta_excel: str
    total_evidencias: int
    detecciones: List[DetectionResult]