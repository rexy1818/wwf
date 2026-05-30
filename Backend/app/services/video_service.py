import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging
from fastapi import UploadFile

from app.utils.file_manager import FileManager
from app.services.camera_service import CameraService

logger = logging.getLogger(__name__)

class VideoService:
    def __init__(self):
        self.file_manager = FileManager()
        self.camera_service = CameraService()
        
        # Formatos de video soportados
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    
    async def upload_video(self, camera_id: str, file: UploadFile) -> Dict[str, Any]:
        """
        Subir un video a una cámara específica
        Args:
            camera_id: ID de la cámara
            file: Archivo de video subido
        Returns:
            Información del video subido
        """
        try:
            # Verificar que la cámara existe
            if not self.camera_service.camera_exists(camera_id):
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            # Verificar formato del archivo
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Formato no soportado: {file_extension}. Formatos válidos: {', '.join(self.supported_formats)}")
            
            # Obtener ruta de videos de la cámara
            videos_path = self.file_manager.get_videos_path(camera_id)
            
            # Generar nombre único para el archivo
            safe_filename = self._sanitize_filename(file.filename)
            video_path = videos_path / safe_filename
            
            # Verificar si el archivo ya existe
            counter = 1
            original_path = video_path
            while video_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                video_path = videos_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Guardar el archivo
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Obtener información del archivo
            file_size = video_path.stat().st_size
            
            logger.info(f"Video subido: {video_path} ({file_size} bytes)")
            
            return {
                'filename': video_path.name,
                'original_filename': file.filename,
                'file_path': str(video_path),
                'file_size': file_size,
                'camera_id': camera_id,
                'status': 'uploaded'
            }
        
        except Exception as e:
            logger.error(f"Error subiendo video: {e}")
            raise
    
    def list_videos(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Listar todos los videos de una cámara
        Args:
            camera_id: ID de la cámara
        Returns:
            Lista de videos
        """
        try:
            # Verificar que la cámara existe
            if not self.camera_service.camera_exists(camera_id):
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            videos_path = self.file_manager.get_videos_path(camera_id)
            videos = []
            
            if videos_path.exists():
                for video_file in videos_path.iterdir():
                    if video_file.is_file() and video_file.suffix.lower() in self.supported_formats:
                        file_stats = video_file.stat()
                        videos.append({
                            'filename': video_file.name,
                            'file_path': str(video_file),
                            'file_size': file_stats.st_size,
                            'created_at': file_stats.st_ctime,
                            'modified_at': file_stats.st_mtime
                        })
            
            logger.info(f"Encontrados {len(videos)} videos para cámara {camera_id}")
            return videos
        
        except Exception as e:
            logger.error(f"Error listando videos de cámara {camera_id}: {e}")
            raise
    
    def get_video_info(self, camera_id: str, filename: str) -> Dict[str, Any]:
        """
        Obtener información de un video específico
        Args:
            camera_id: ID de la cámara
            filename: Nombre del archivo de video
        Returns:
            Información del video
        """
        try:
            videos_path = self.file_manager.get_videos_path(camera_id)
            video_path = videos_path / filename
            
            if not video_path.exists():
                raise ValueError(f"Video no encontrado: {filename}")
            
            file_stats = video_path.stat()
            
            return {
                'filename': video_path.name,
                'file_path': str(video_path),
                'file_size': file_stats.st_size,
                'created_at': file_stats.st_ctime,
                'modified_at': file_stats.st_mtime,
                'camera_id': camera_id
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo info de video {filename}: {e}")
            raise
    
    def delete_video(self, camera_id: str, filename: str) -> bool:
        """
        Eliminar un video
        Args:
            camera_id: ID de la cámara
            filename: Nombre del archivo de video
        Returns:
            True si se eliminó correctamente
        """
        try:
            videos_path = self.file_manager.get_videos_path(camera_id)
            video_path = videos_path / filename
            
            if not video_path.exists():
                raise ValueError(f"Video no encontrado: {filename}")
            
            video_path.unlink()
            logger.info(f"Video eliminado: {video_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error eliminando video {filename}: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Limpiar nombre de archivo para evitar problemas
        Args:
            filename: Nombre original del archivo
        Returns:
            Nombre limpio del archivo
        """
        # Caracteres no permitidos en nombres de archivo
        invalid_chars = '<>:"/\\|?*'
        
        # Reemplazar caracteres inválidos
        clean_name = filename
        for char in invalid_chars:
            clean_name = clean_name.replace(char, '_')
        
        # Limitar longitud
        if len(clean_name) > 255:
            name_part = Path(clean_name).stem[:200]
            extension = Path(clean_name).suffix
            clean_name = f"{name_part}{extension}"
        
        return clean_name