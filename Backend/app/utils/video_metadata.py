import cv2
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import subprocess
import json

logger = logging.getLogger(__name__)

class VideoMetadataExtractor:
    def __init__(self):
        pass
    
    def extract_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Extraer metadatos completos de un video
        Args:
            video_path: Ruta del archivo de video
        Returns:
            Diccionario con metadatos del video
        """
        metadata = {
            'filename': Path(video_path).name,
            'file_path': video_path,
            'file_size': 0,
            'duration': 0,
            'fps': 0,
            'width': 0,
            'height': 0,
            'creation_date': None,
            'modification_date': None,
            'gps_coordinates': None,
            'camera_make': None,
            'camera_model': None,
            'timestamp_original': None
        }
        
        try:
            # Obtener información básica del archivo
            if os.path.exists(video_path):
                stat = os.stat(video_path)
                metadata['file_size'] = stat.st_size
                metadata['creation_date'] = datetime.fromtimestamp(stat.st_ctime)
                metadata['modification_date'] = datetime.fromtimestamp(stat.st_mtime)
            
            # Extraer metadatos con OpenCV
            self._extract_opencv_metadata(video_path, metadata)
            
            # Intentar extraer metadatos EXIF con ffprobe si está disponible
            self._extract_ffprobe_metadata(video_path, metadata)
            
            # Extraer fecha del nombre del archivo si sigue un patrón común
            self._extract_date_from_filename(video_path, metadata)
            
        except Exception as e:
            logger.error(f"Error extrayendo metadatos de {video_path}: {e}")
        
        return metadata
    
    def _extract_opencv_metadata(self, video_path: str, metadata: Dict[str, Any]) -> None:
        """Extraer metadatos básicos con OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                # Propiedades básicas del video
                metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
                metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Calcular duración
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if metadata['fps'] > 0:
                    metadata['duration'] = frame_count / metadata['fps']
                
                cap.release()
                logger.debug(f"Metadatos OpenCV extraídos para {video_path}")
        
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos OpenCV de {video_path}: {e}")
    
    def _extract_ffprobe_metadata(self, video_path: str, metadata: Dict[str, Any]) -> None:
        """Extraer metadatos detallados con ffprobe si está disponible"""
        try:
            # Comando ffprobe para extraer metadatos
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extraer metadatos del formato
                if 'format' in data and 'tags' in data['format']:
                    tags = data['format']['tags']
                    
                    # Buscar fecha de creación en diferentes campos
                    creation_fields = ['creation_time', 'date', 'DATE', 'com.apple.quicktime.creationdate']
                    for field in creation_fields:
                        if field in tags:
                            try:
                                # Parsear diferentes formatos de fecha
                                date_str = tags[field]
                                metadata['timestamp_original'] = self._parse_date_string(date_str)
                                break
                            except:
                                continue
                    
                    # Extraer información de la cámara
                    if 'make' in tags:
                        metadata['camera_make'] = tags['make']
                    if 'model' in tags:
                        metadata['camera_model'] = tags['model']
                    
                    # Buscar coordenadas GPS
                    gps_fields = ['location', 'com.apple.quicktime.location.ISO6709']
                    for field in gps_fields:
                        if field in tags:
                            metadata['gps_coordinates'] = tags[field]
                            break
                
                logger.debug(f"Metadatos ffprobe extraídos para {video_path}")
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout extrayendo metadatos ffprobe de {video_path}")
        except FileNotFoundError:
            logger.debug("ffprobe no disponible, usando solo metadatos básicos")
        except Exception as e:
            logger.warning(f"Error extrayendo metadatos ffprobe de {video_path}: {e}")
    
    def _extract_date_from_filename(self, video_path: str, metadata: Dict[str, Any]) -> None:
        """Extraer fecha del nombre del archivo si sigue patrones comunes"""
        try:
            filename = Path(video_path).stem
            
            # Patrones comunes de nombres de archivo de cámaras trampa
            import re
            
            # Patrón: YYYYMMDD_HHMMSS
            pattern1 = r'(\d{8})_(\d{6})'
            match = re.search(pattern1, filename)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                try:
                    parsed_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    if not metadata['timestamp_original']:
                        metadata['timestamp_original'] = parsed_date
                    return
                except:
                    pass
            
            # Patrón: YYYY-MM-DD_HH-MM-SS
            pattern2 = r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})'
            match = re.search(pattern2, filename)
            if match:
                date_str = match.group(1)
                time_str = match.group(2).replace('-', ':')
                try:
                    parsed_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                    if not metadata['timestamp_original']:
                        metadata['timestamp_original'] = parsed_date
                    return
                except:
                    pass
            
            # Patrón: IMG_YYYYMMDD_HHMMSS
            pattern3 = r'IMG_(\d{8})_(\d{6})'
            match = re.search(pattern3, filename)
            if match:
                date_str = match.group(1)
                time_str = match.group(2)
                try:
                    parsed_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    if not metadata['timestamp_original']:
                        metadata['timestamp_original'] = parsed_date
                    return
                except:
                    pass
        
        except Exception as e:
            logger.debug(f"No se pudo extraer fecha del nombre del archivo {video_path}: {e}")
    
    def _parse_date_string(self, date_str: str) -> datetime:
        """Parsear diferentes formatos de fecha"""
        # Formatos comunes de fecha en metadatos de video
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
            "%Y-%m-%dT%H:%M:%SZ",     # ISO format
            "%Y-%m-%d %H:%M:%S",      # Standard format
            "%Y:%m:%d %H:%M:%S",      # EXIF format
            "%Y-%m-%dT%H:%M:%S%z",    # ISO with timezone
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Si no se puede parsear, usar la fecha actual
        raise ValueError(f"No se pudo parsear la fecha: {date_str}")
    
    def get_video_datetime(self, metadata: Dict[str, Any]) -> tuple:
        """
        Obtener fecha y hora del video priorizando diferentes fuentes
        Returns:
            tuple: (fecha_str, hora_str, datetime_obj)
        """
        # Prioridad: timestamp_original > creation_date > modification_date
        dt = None
        
        if metadata.get('timestamp_original'):
            dt = metadata['timestamp_original']
        elif metadata.get('creation_date'):
            dt = metadata['creation_date']
        elif metadata.get('modification_date'):
            dt = metadata['modification_date']
        else:
            dt = datetime.now()
        
        fecha_str = dt.strftime('%Y-%m-%d')
        hora_str = dt.strftime('%H:%M:%S')
        
        return fecha_str, hora_str, dt
    
    def format_gps_coordinates(self, gps_string: Optional[str]) -> Optional[str]:
        """
        Formatear coordenadas GPS a un formato legible
        Args:
            gps_string: String con coordenadas GPS en formato ISO6709 o similar
        Returns:
            String formateado con coordenadas o None
        """
        if not gps_string:
            return None
        
        try:
            # Ejemplo de formato ISO6709: +40.7589-073.9851+000.000/
            import re
            
            # Patrón para coordenadas ISO6709
            pattern = r'([+-]\d+\.\d+)([+-]\d+\.\d+)'
            match = re.search(pattern, gps_string)
            
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                return f"{lat:.6f}, {lon:.6f}"
            
            return gps_string  # Devolver original si no se puede parsear
        
        except Exception as e:
            logger.debug(f"Error formateando coordenadas GPS {gps_string}: {e}")
            return gps_string