import asyncio
import cv2
from pathlib import Path
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

from app.utils.file_manager import FileManager
from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.smart_species_classifier import SmartSpeciesClassifier
from app.utils.excel_generator import ExcelGenerator
from app.utils.json_storage import json_storage
from app.services.camera_service import CameraService
from app.services.video_loader_service import VideoLoaderService

logger = logging.getLogger(__name__)

class ProcessingService:
    def __init__(self):
        self.file_manager = FileManager()
        self.yolo_detector = ImprovedYOLODetector()
        self.classifier = SmartSpeciesClassifier()
        self.excel_generator = ExcelGenerator()
        self.camera_service = CameraService()
        self.video_loader_service = VideoLoaderService()
        
        # Configuración de procesamiento
        self.default_interval = 3  # intervalo inicial mejorado
        self.default_confidence = 0.5  # umbral de confianza mínimo
        self.max_workers = 2  # número máximo de workers para procesamiento paralelo
    
    async def process_camera_videos(self, camera_id: str, 
                                  interval_seconds: int = None,
                                  confidence_threshold: float = None) -> Dict[str, Any]:
        """
        Procesar todos los videos de una cámara con detección mejorada
        """
        try:
            # Verificar que la cámara existe
            if not self.camera_service.camera_exists(camera_id):
                raise ValueError(f"Cámara no encontrada: {camera_id}")
            
            logger.info(f"🚀 Iniciando PROCESAMIENTO INTELIGENTE de cámara {camera_id}")
            
            # Cargar videos
            videos = self.video_loader_service.load_videos_from_camera_folder(camera_id)
            
            if not videos:
                return self._create_empty_result(camera_id)
            
            all_detections = []
            processed_videos = 0
            
            # Procesar cada video con el nuevo motor
            for video in videos:
                try:
                    video_path = video['storage_path']
                    video_name = video['filename']
                    
                    # 1. Detección Mejorada (Algoritmo de selección de mejores frames)
                    detections = self.yolo_detector.process_video_enhanced(
                        video_path, 
                        str(self.file_manager.base_path / camera_id / "resultados"),
                        {'camara_id': camera_id}
                    )
                    
                    # 2. Clasificación Inteligente y Validación
                    smart_detections = []
                    for det in detections:
                        frame = cv2.imread(det['ruta_evidencia'])
                        if frame is not None:
                            smart_det = self.classifier.classify_species_intelligently(det, frame)
                            smart_detections.append(smart_det)
                        else:
                            smart_detections.append(det)
                    
                    # 3. Filtrado contextual
                    final_detections = self.classifier.validate_detection_context(smart_detections)
                    
                    # Adaptar formato para el reporte Excel
                    for det in final_detections:
                        # Asegurar que campos requeridos por ExcelGenerator estén presentes
                        det['video'] = video_name
                        det['especie'] = det.get('species', det.get('especie'))
                        det['confianza'] = det.get('confidence', det.get('confianza'))
                        all_detections.append(det)
                        
                    processed_videos += 1
                    logger.info(f"✅ Video {video_name} procesado: {len(final_detections)} detecciones inteligentes")
                    
                except Exception as e:
                    logger.error(f"Error procesando video {video['filename']}: {e}")
            
            # Generar reporte Excel
            excel_path = ""
            if all_detections:
                excel_path = self.excel_generator.generate_report(
                    all_detections, camera_id, self.file_manager
                )
            
            # Obtener estadísticas
            stats = self.excel_generator.get_summary_stats(all_detections)
            stats['videos_procesados'] = processed_videos
            
            # Guardar y actualizar
            self._save_processing_results(camera_id, all_detections, stats)
            
            # Actualizar estadísticas de la cámara
            self.camera_service.update_camera_stats(
                camera_id, 
                videos_procesados=processed_videos,
                total_detecciones=len(all_detections)
            )
            
            return {
                **stats,
                'ruta_excel': excel_path,
                'total_detecciones_completas': len(all_detections),
                'status': 'success',
                'motor': 'v2.0-enhanced'
            }
            
        except Exception as e:
            logger.error(f"Error en procesamiento inteligente de cámara {camera_id}: {e}")
            raise

    def _process_single_video(self, video_path: str, camera_id: str,
                            interval_seconds: int, confidence_threshold: float) -> List[Dict[str, Any]]:
        # Este método se mantiene por compatibilidad pero se usa la lógica mejorada en process_camera_videos
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
