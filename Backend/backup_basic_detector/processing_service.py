import asyncio
from pathlib import Path
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

from app.utils.file_manager import FileManager
from app.utils.yolo_detector import YOLODetector
from app.utils.excel_generator import ExcelGenerator
from app.utils.json_storage import json_storage
from app.services.camera_service import CameraService
from app.services.video_loader_service import VideoLoaderService

logger = logging.getLogger(__name__)

class ProcessingService:
    def __init__(self):
        self.file_manager = FileManager()
        self.yolo_detector = YOLODetector()
        self.excel_generator = ExcelGenerator()
        self.camera_service = CameraService()
        self.video_loader_service = VideoLoaderService()
        
        # Configuración de procesamiento
        self.default_interval = 5  # segundos entre frames
        self.default_confidence = 0.5  # umbral de confianza mínimo
        self.max_workers = 2  # número máximo de workers para procesamiento paralelo
    
    async def process_camera_videos(self, camera_id: str, 
                                  interval_seconds: int = None,
                                  confidence_threshold: float = None) -> Dict[str, Any]:
        """
        Procesar todos los videos de una cámara
        Args:
            camera_id: ID de la cámara
            interval_seconds: Intervalo entre frames (default: 5)
            confidence_threshold: Umbral de confianza (default: 0.5)
        Returns:
            Resultados del procesamiento
        """
        try:
            # Verificar que la cámara existe
            if not self.camera_service.camera_exists(camera_id):
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            # Usar valores por defecto si no se especifican
            interval_seconds = interval_seconds or self.default_interval
            confidence_threshold = confidence_threshold or self.default_confidence
            
            logger.info(f"Iniciando procesamiento de cámara {camera_id}")
            
            # Cargar videos desde la carpeta de la cámara
            videos = self.video_loader_service.load_videos_from_camera_folder(camera_id)
            
            if not videos:
                logger.warning(f"No se encontraron videos para procesar en cámara {camera_id}")
                return self._create_empty_result(camera_id)
            
            # Procesar videos
            all_detections = []
            processed_videos = 0
            
            # Usar ThreadPoolExecutor para procesamiento paralelo
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Crear tareas para cada video
                tasks = []
                for video in videos:
                    task = executor.submit(
                        self._process_single_video,
                        video['storage_path'],  # Usar la ruta en storage
                        camera_id,
                        interval_seconds,
                        confidence_threshold
                    )
                    tasks.append((task, video['filename']))
                
                # Recopilar resultados
                for task, video_name in tasks:
                    try:
                        video_detections = task.result()
                        all_detections.extend(video_detections)
                        processed_videos += 1
                        logger.info(f"Video procesado: {video_name} - {len(video_detections)} detecciones")
                    except Exception as e:
                        logger.error(f"Error procesando video {video_name}: {e}")
            
            # Generar reporte Excel
            excel_path = ""
            if all_detections:
                excel_path = self.excel_generator.generate_report(
                    all_detections, camera_id, self.file_manager
                )
            
            # Obtener estadísticas
            stats = self.excel_generator.get_summary_stats(all_detections)
            stats['videos_procesados'] = processed_videos
            
            # Guardar resultados del procesamiento
            self._save_processing_results(camera_id, all_detections, stats)
            
            # Guardar en JSON storage
            json_storage.save_processing_result(camera_id, {
                **stats,
                'ruta_excel': excel_path,
                'configuracion': {
                    'intervalo_segundos': interval_seconds,
                    'umbral_confianza': confidence_threshold
                },
                'detecciones_muestra': all_detections[:5]  # Solo una muestra para no sobrecargar
            })
            
            # Actualizar estadísticas de la cámara
            self.camera_service.update_camera_stats(
                camera_id, 
                videos_procesados=processed_videos,
                total_detecciones=len(all_detections)
            )
            
            # Preparar respuesta
            result = {
                **stats,
                'ruta_excel': excel_path,
                'detecciones': all_detections[:100],  # Limitar a 100 para la respuesta
                'total_detecciones_completas': len(all_detections),
                'configuracion': {
                    'intervalo_segundos': interval_seconds,
                    'umbral_confianza': confidence_threshold
                }
            }
            
            logger.info(f"Procesamiento completado para cámara {camera_id}: {len(all_detections)} detecciones")
            return result
        
        except Exception as e:
            logger.error(f"Error en procesamiento de cámara {camera_id}: {e}")
            raise
    
    def _process_single_video(self, video_path: str, camera_id: str,
                            interval_seconds: int, confidence_threshold: float) -> List[Dict[str, Any]]:
        """
        Procesar un solo video (función para ejecutar en thread)
        Args:
            video_path: Ruta del video
            camera_id: ID de la cámara
            interval_seconds: Intervalo entre frames
            confidence_threshold: Umbral de confianza
        Returns:
            Lista de detecciones del video
        """
        try:
            return self.yolo_detector.process_video(
                video_path, camera_id, self.file_manager,
                interval_seconds, confidence_threshold
            )
        except Exception as e:
            logger.error(f"Error procesando video {video_path}: {e}")
            return []
    
    def get_processing_results(self, camera_id: str) -> Dict[str, Any]:
        """
        Obtener resultados de procesamiento de una cámara
        Args:
            camera_id: ID de la cámara
        Returns:
            Resultados del último procesamiento
        """
        try:
            # Verificar que la cámara existe
            if not self.camera_service.camera_exists(camera_id):
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            # Buscar archivo de resultados
            results_path = self.file_manager.base_path / camera_id / "resultados"
            results_file = results_path / "ultimo_procesamiento.json"
            
            if not results_file.exists():
                logger.warning(f"No se encontraron resultados de procesamiento para cámara {camera_id}")
                return self._create_empty_result(camera_id)
            
            # Cargar resultados
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            return results
        
        except Exception as e:
            logger.error(f"Error obteniendo resultados de cámara {camera_id}: {e}")
            raise
    
    def _save_processing_results(self, camera_id: str, detections: List[Dict[str, Any]], 
                               stats: Dict[str, Any]) -> None:
        """
        Guardar resultados de procesamiento
        Args:
            camera_id: ID de la cámara
            detections: Lista de detecciones
            stats: Estadísticas del procesamiento
        """
        try:
            results_path = self.file_manager.base_path / camera_id / "resultados"
            results_path.mkdir(parents=True, exist_ok=True)
            
            # Preparar datos para guardar
            results_data = {
                **stats,
                'fecha_procesamiento': datetime.now().isoformat(),
                'camera_id': camera_id,
                'detecciones': detections
            }
            
            # Guardar como último procesamiento
            results_file = results_path / "ultimo_procesamiento.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Guardar con timestamp para historial
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            history_file = results_path / f"procesamiento_{timestamp}.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Resultados guardados para cámara {camera_id}")
        
        except Exception as e:
            logger.error(f"Error guardando resultados de cámara {camera_id}: {e}")
    
    def _create_empty_result(self, camera_id: str) -> Dict[str, Any]:
        """
        Crear resultado vacío cuando no hay detecciones
        Args:
            camera_id: ID de la cámara
        Returns:
            Resultado vacío
        """
        return {
            'videos_procesados': 0,
            'animales_detectados': 0,
            'especies_encontradas': [],
            'ruta_excel': '',
            'total_evidencias': 0,
            'detecciones': [],
            'camera_id': camera_id,
            'fecha_procesamiento': datetime.now().isoformat()
        }
    
    def get_processing_history(self, camera_id: str) -> List[Dict[str, Any]]:
        """
        Obtener historial de procesamientos de una cámara
        Args:
            camera_id: ID de la cámara
        Returns:
            Lista de procesamientos históricos
        """
        try:
            results_path = self.file_manager.base_path / camera_id / "resultados"
            
            if not results_path.exists():
                return []
            
            history = []
            for file_path in results_path.glob("procesamiento_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Solo incluir metadatos, no todas las detecciones
                        summary = {
                            'fecha_procesamiento': data.get('fecha_procesamiento'),
                            'videos_procesados': data.get('videos_procesados', 0),
                            'animales_detectados': data.get('animales_detectados', 0),
                            'especies_encontradas': data.get('especies_encontradas', []),
                            'archivo': file_path.name
                        }
                        history.append(summary)
                except Exception as e:
                    logger.warning(f"Error cargando historial {file_path}: {e}")
            
            # Ordenar por fecha descendente
            history.sort(key=lambda x: x.get('fecha_procesamiento', ''), reverse=True)
            return history
        
        except Exception as e:
            logger.error(f"Error obteniendo historial de cámara {camera_id}: {e}")
            return []