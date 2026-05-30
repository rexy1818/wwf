from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CameraCreate(BaseModel):
    nombre: str
    ubicacion: str

class CameraResponse(BaseModel):
    id: str
    nombre: str
    ubicacion: str
    fecha_creacion: datetime
    ruta_storage: str

class VideoUpload(BaseModel):
    camera_id: str

class DetectionResult(BaseModel):
    video: str
    especie: str
    confianza: float
    fecha: str
    hora: str
    frame: int
    ruta_evidencia: str

class ProcessingResult(BaseModel):
    videos_procesados: int
    animales_detectados: int
    especies_encontradas: List[str]
    ruta_excel: str
    total_evidencias: int
    detecciones: List[DetectionResult]