import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging

from app.utils.file_manager import FileManager
from app.utils.video_metadata import VideoMetadataExtractor
from app.services.camera_service import CameraService

logger = logging.getLogger(__name__)

class VideoLoaderService:
    def __init__(self):
        self.file_manager = FileManager()
        self.camera_service = CameraService()
        self.metadata_extractor = VideoMetadataExtractor()
        
        # Formatos de video soportados
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    
    def load_videos_from_camera_folder(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Cargar todos los videos desde la carpeta de la cámara especificada
        Args:
            camera_id: ID de la cámara
        Returns:
            Lista de videos cargados con sus metadatos
        """
        try:
            # Obtener información de la cámara
            camera_info = self.camera_service.get_camera(camera_id)
            source_folder = Path(camera_info['ruta_videos'])
            
            if not source_folder.exists():
                raise ValueError(f"La carpeta de videos no existe: {source_folder}")
            
            # Obtener ruta de destino en storage
            videos_storage_path = self.file_manager.get_videos_path(camera_id)
            
            # Buscar todos los videos en la carpeta
            video_files = []
            for ext in self.supported_formats:
                video_files.extend(source_folder.glob(f"*{ext}"))
                video_files.extend(source_folder.glob(f"*{ext.upper()}"))
            
            loaded_videos = []
            
            for video_file in video_files:
                try:
                    # Copiar video al storage si no existe
                    dest_path = videos_storage_path / video_file.name
                    
                    if not dest_path.exists():
                        logger.info(f"Copiando video: {video_file.name}")
                        shutil.copy2(video_file, dest_path)
                    
                    # Extraer metadatos del video
                    metadata = self.metadata_extractor.extract_metadata(str(dest_path))
                    
                    video_info = {
                        'filename': video_file.name,
                        'original_path': str(video_file),
                        'storage_path': str(dest_path),
                        'file_size': metadata['file_size'],
                        'duration': metadata['duration'],
                        'fps': metadata['fps'],
                        'resolution': f"{metadata['width']}x{metadata['height']}",
                        'creation_date': metadata.get('creation_date'),
                        'timestamp_original': metadata.get('timestamp_original'),
                        'gps_coordinates': metadata.get('gps_coordinates'),
                        'camera_make': metadata.get('camera_make'),
                        'camera_model': metadata.get('camera_model'),
                        'status': 'loaded'
                    }
                    
                    loaded_videos.append(video_info)
                    logger.info(f"Video cargado: {video_file.name}")
                
                except Exception as e:
                    logger.error(f"Error cargando video {video_file.name}: {e}")
                    continue
            
            logger.info(f"Cargados {len(loaded_videos)} videos para cámara {camera_id}")
            return loaded_videos
        
        except Exception as e:
            logger.error(f"Error cargando videos de cámara {camera_id}: {e}")
            raise
    
    def get_videos_in_camera_folder(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Listar videos disponibles en la carpeta de la cámara (sin copiar)
        Args:
            camera_id: ID de la cámara
        Returns:
            Lista de videos disponibles
        """
        try:
            # Obtener información de la cámara
            camera_info = self.camera_service.get_camera(camera_id)
            source_folder = Path(camera_info['ruta_videos'])
            
            if not source_folder.exists():
                raise ValueError(f"La carpeta de videos no existe: {source_folder}")
            
            # Buscar todos los videos en la carpeta
            video_files = []
            for ext in self.supported_formats:
                video_files.extend(source_folder.glob(f"*{ext}"))
                video_files.extend(source_folder.glob(f"*{ext.upper()}"))
            
            videos_info = []
            
            for video_file in video_files:
                try:
                    # Extraer metadatos básicos
                    metadata = self.metadata_extractor.extract_metadata(str(video_file))
                    
                    video_info = {
                        'filename': video_file.name,
                        'path': str(video_file),
                        'file_size': metadata['file_size'],
                        'duration': metadata['duration'],
                        'fps': metadata['fps'],
                        'resolution': f"{metadata['width']}x{metadata['height']}",
                        'creation_date': metadata.get('creation_date'),
                        'timestamp_original': metadata.get('timestamp_original'),
                        'gps_coordinates': metadata.get('gps_coordinates')
                    }
                    
                    videos_info.append(video_info)
                
                except Exception as e:
                    logger.warning(f"Error obteniendo info de video {video_file.name}: {e}")
                    continue
            
            return videos_info
        
        except Exception as e:
            logger.error(f"Error listando videos de cámara {camera_id}: {e}")
            raise