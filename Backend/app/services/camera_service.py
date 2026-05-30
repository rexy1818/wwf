import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import logging

from app.utils.file_manager import FileManager
from app.schemas.camera import CameraCreate, CameraResponse

logger = logging.getLogger(__name__)

class CameraService:
    def __init__(self):
        self.file_manager = FileManager()
    
    def create_camera(self, camera_data: CameraCreate) -> CameraResponse:
        """
        Crear una nueva cámara con su estructura de directorios
        Args:
            camera_data: Datos de la cámara a crear
        Returns:
            Información de la cámara creada
        """
        try:
            # Generar ID único para la cámara
            camera_id = self._generate_camera_id(camera_data.nombre)
            
            # Crear estructura de directorios
            camera_path = self.file_manager.create_camera_structure(camera_id)
            
            # Crear metadatos de la cámara
            metadata = {
                'id': camera_id,
                'nombre': camera_data.nombre,
                'ubicacion': camera_data.ubicacion,
                'fecha_creacion': datetime.now(),
                'ruta_storage': camera_path,
                'videos_procesados': 0,
                'total_detecciones': 0
            }
            
            # Guardar metadatos
            self.file_manager.save_camera_metadata(camera_id, metadata)
            
            logger.info(f"Cámara creada: {camera_id} - {camera_data.nombre}")
            
            return CameraResponse(
                id=camera_id,
                nombre=camera_data.nombre,
                ubicacion=camera_data.ubicacion,
                fecha_creacion=metadata['fecha_creacion'],
                ruta_storage=camera_path
            )
        
        except Exception as e:
            logger.error(f"Error creando cámara: {e}")
            raise
    
    def get_camera(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtener información de una cámara
        Args:
            camera_id: ID de la cámara
        Returns:
            Información de la cámara
        """
        try:
            metadata = self.file_manager.get_camera_metadata(camera_id)
            if not metadata:
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error obteniendo cámara {camera_id}: {e}")
            raise
    
    def list_cameras(self) -> List[Dict[str, Any]]:
        """
        Listar todas las cámaras disponibles
        Returns:
            Lista de cámaras
        """
        try:
            cameras = []
            camera_ids = self.file_manager.list_cameras()
            
            for camera_id in camera_ids:
                try:
                    metadata = self.file_manager.get_camera_metadata(camera_id)
                    cameras.append(metadata)
                except Exception as e:
                    logger.warning(f"Error cargando cámara {camera_id}: {e}")
            
            return cameras
        
        except Exception as e:
            logger.error(f"Error listando cámaras: {e}")
            raise
    
    def update_camera_stats(self, camera_id: str, videos_procesados: int = None, 
                           total_detecciones: int = None) -> None:
        """
        Actualizar estadísticas de una cámara
        Args:
            camera_id: ID de la cámara
            videos_procesados: Número de videos procesados
            total_detecciones: Total de detecciones
        """
        try:
            metadata = self.file_manager.get_camera_metadata(camera_id)
            if not metadata:
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            if videos_procesados is not None:
                metadata['videos_procesados'] = videos_procesados
            
            if total_detecciones is not None:
                metadata['total_detecciones'] = total_detecciones
            
            metadata['ultima_actualizacion'] = datetime.now()
            
            self.file_manager.save_camera_metadata(camera_id, metadata)
            logger.info(f"Estadísticas actualizadas para cámara {camera_id}")
        
        except Exception as e:
            logger.error(f"Error actualizando estadísticas de cámara {camera_id}: {e}")
            raise
    
    def _generate_camera_id(self, nombre: str) -> str:
        """
        Generar ID único para la cámara basado en el nombre
        Args:
            nombre: Nombre de la cámara
        Returns:
            ID único de la cámara
        """
        # Limpiar nombre para usar como parte del ID
        clean_name = "".join(c.lower() if c.isalnum() else "_" for c in nombre)
        clean_name = clean_name.strip("_")
        
        # Generar ID único
        unique_id = str(uuid.uuid4())[:8]
        camera_id = f"{clean_name}_{unique_id}"
        
        return camera_id
    
    def camera_exists(self, camera_id: str) -> bool:
        """
        Verificar si una cámara existe
        Args:
            camera_id: ID de la cámara
        Returns:
            True si existe, False en caso contrario
        """
        try:
            metadata = self.file_manager.get_camera_metadata(camera_id)
            return bool(metadata)
        except:
            return False