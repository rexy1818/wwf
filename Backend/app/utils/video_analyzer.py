import cv2
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import subprocess
import json
import uuid

from app.utils.video_metadata import VideoMetadataExtractor
from app.utils.yolo_detector import YOLODetector
from app.utils.ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    def __init__(self):
        self.metadata_extractor = VideoMetadataExtractor()
        self.yolo_detector = YOLODetector()
        self.ocr_extractor = OCRExtractor()
    
    def analyze_video(self, video_path: str, output_dir: str = "analysis_results") -> Dict[str, Any]:
        """
        Analizar un video completo: metadatos + detección de animales
        Args:
            video_path: Ruta del video a analizar
            output_dir: Directorio donde guardar resultados
        Returns:
            Diccionario con todos los resultados del análisis
        """
        try:
            video_name = Path(video_path).stem
            video_id = str(uuid.uuid4())[:8]
            
            logger.info(f"Iniciando análisis de video: {video_name}")
            
            # 1. Extraer metadatos del video
            metadata = self._extract_enhanced_metadata(video_path)
            
            # 2. Crear directorios de salida
            analysis_dir = Path(output_dir) / f"{video_name}_{video_id}"
            evidencias_dir = analysis_dir / "evidencias"
            evidencias_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Procesar video con YOLO
            detections = self._process_video_with_yolo(video_path, evidencias_dir, metadata)
            
            # 4. Generar estadísticas
            stats = self._generate_statistics(detections)
            
            # 5. Crear resultado completo
            result = {
                'video_id': video_id,
                'video_name': video_name,
                'video_path': video_path,
                'metadata': metadata,
                'detecciones': detections,
                'estadisticas': stats,
                'analysis_dir': str(analysis_dir),
                'procesado_en': datetime.now().isoformat()
            }
            
            # 6. Guardar resultado en JSON
            result_file = analysis_dir / "analysis_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Análisis completado: {len(detections)} detecciones encontradas")
            return result
        
        except Exception as e:
            logger.error(f"Error analizando video {video_path}: {e}")
            raise
    
    def _extract_enhanced_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extraer metadatos mejorados del video"""
        try:
            # Metadatos básicos del archivo
            metadata = self.metadata_extractor.extract_metadata(video_path)
            
            # Extraer información del texto superpuesto usando OCR
            logger.info(f"Extrayendo texto superpuesto con OCR de {video_path}")
            ocr_data = self.ocr_extractor.extract_text_from_video(video_path)
            
            # Priorizar información del OCR sobre metadatos del archivo
            camera_id = ocr_data.get('camera_id') or self._extract_camera_id(video_path, metadata)
            
            # Usar fecha/hora del OCR si está disponible, sino usar metadatos del archivo
            if ocr_data.get('fecha') and ocr_data.get('hora'):
                fecha_video = ocr_data['fecha']
                hora_video = ocr_data['hora']
                try:
                    datetime_obj = datetime.strptime(f"{fecha_video} {hora_video}", "%Y-%m-%d %H:%M:%S")
                except:
                    # Fallback a metadatos del archivo
                    fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)
            else:
                fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)
            
            # Usar temperatura del OCR
            temperatura = ocr_data.get('temperatura')
            
            # Formatear GPS de metadatos del archivo
            gps_coords = self.metadata_extractor.format_gps_coordinates(metadata.get('gps_coordinates'))
            
            enhanced_metadata = {
                'filename': metadata['filename'],
                'file_size': metadata['file_size'],
                'duration': metadata['duration'],
                'fps': metadata['fps'],
                'resolution': f"{metadata['width']}x{metadata['height']}",
                'fecha_video': fecha_video,
                'hora_video': hora_video,
                'ubicacion_gps': gps_coords,
                'temperatura': temperatura,
                'camara_id': camera_id,
                'camara_marca': metadata.get('camera_make'),
                'camara_modelo': metadata.get('camera_model'),
                'timestamp_original': datetime_obj.isoformat() if datetime_obj else None,
                'ocr_info': {
                    'frames_procesados': ocr_data.get('frames_procesados', 0),
                    'texto_detectado': len(ocr_data.get('raw_extractions', [])) > 0
                }
            }
            
            logger.info(f"Metadatos extraídos - Cámara: {camera_id}, Fecha: {fecha_video}, Hora: {hora_video}, Temp: {temperatura}°C")
            return enhanced_metadata
        
        except Exception as e:
            logger.error(f"Error extrayendo metadatos mejorados: {e}")
            raise
    
    def _extract_camera_id(self, video_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Extraer ID de cámara del nombre del archivo o metadatos"""
        try:
            filename = Path(video_path).stem
            
            # Patrones comunes para ID de cámara en nombres de archivo
            patterns = [
                r'CAM(\d+)',           # CAM001, CAM123
                r'CAMERA_(\w+)',       # CAMERA_A1, CAMERA_NORTH
                r'(\w+)_CAM',          # SITE1_CAM, FOREST_CAM
                r'ID(\d+)',            # ID001, ID123
                r'TRAP(\d+)',          # TRAP001, TRAP123
                r'([A-Z]\d+)',         # A1, B2, C3
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename.upper())
                if match:
                    return match.group(1)
            
            # Si no encuentra patrón, usar parte del nombre del archivo
            # Ejemplo: "WhatsApp Video 2026-05-30" -> "WHATSAPP"
            words = filename.upper().split()
            if words:
                return words[0][:10]  # Primeras 10 letras de la primera palabra
            
            return "UNKNOWN"
        
        except Exception as e:
            logger.debug(f"Error extrayendo camera ID: {e}")
            return "UNKNOWN"
    
    def _extract_temperature(self, metadata: Dict[str, Any]) -> Optional[float]:
        """Extraer temperatura de metadatos si está disponible"""
        try:
            # Buscar temperatura en diferentes campos de metadatos
            temp_fields = ['temperature', 'temp', 'ambient_temperature', 'sensor_temp']
            
            for field in temp_fields:
                if field in metadata and metadata[field] is not None:
                    try:
                        return float(metadata[field])
                    except (ValueError, TypeError):
                        continue
            
            return None
        
        except Exception as e:
            logger.debug(f"Error extrayendo temperatura: {e}")
            return None
    
    def _process_video_with_yolo(self, video_path: str, evidencias_dir: Path, 
                                metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesar video con YOLO para detectar animales"""
        try:
            detections = []
            video_name = Path(video_path).stem
            
            # Extraer frames cada 5 segundos
            frames = self.yolo_detector.extract_frames(video_path, interval_seconds=5)
            
            for frame, frame_number, timestamp in frames:
                # Detectar animales en el frame
                yolo_detections = self.yolo_detector.detect_animals(frame, confidence_threshold=0.5)
                
                for detection in yolo_detections:
                    species = detection['species']
                    confidence = detection['confidence']
                    bbox = detection['bbox']
                    
                    # Crear directorio para la especie
                    species_dir = evidencias_dir / species
                    species_dir.mkdir(exist_ok=True)
                    
                    # Generar nombre de evidencia
                    evidence_name = f"{species}_{video_name}_frame_{frame_number}_{int(timestamp)}.jpg"
                    evidence_path = species_dir / evidence_name
                    
                    # Guardar evidencia
                    self.yolo_detector.save_evidence(frame, detection, species_dir, evidence_name, metadata)
                    
                    # Crear registro de detección
                    detection_record = {
                        'especie': species,
                        'confianza': round(confidence, 3),
                        'frame_numero': frame_number,
                        'timestamp_video': round(timestamp, 2),
                        'bbox_x': bbox[0],
                        'bbox_y': bbox[1],
                        'bbox_width': bbox[2] - bbox[0],
                        'bbox_height': bbox[3] - bbox[1],
                        'ruta_evidencia': str(evidence_path),
                        'fecha_video': metadata.get('fecha_video'),
                        'hora_video': metadata.get('hora_video'),
                        'camara_id': metadata.get('camara_id'),
                        'ubicacion_gps': metadata.get('ubicacion_gps'),
                        'temperatura': metadata.get('temperatura')
                    }
                    
                    detections.append(detection_record)
                    logger.info(f"Detectado: {species} (confianza: {confidence:.3f}) en frame {frame_number}")
            
            return detections
        
        except Exception as e:
            logger.error(f"Error procesando video con YOLO: {e}")
            raise
    
    def _generate_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar estadísticas de las detecciones"""
        try:
            if not detections:
                return {
                    'total_animales': 0,
                    'especies_encontradas': [],
                    'detecciones_por_especie': {},
                    'confianza_promedio': 0,
                    'frames_con_detecciones': 0
                }
            
            # Contar especies
            especies = {}
            confidencias = []
            frames_unicos = set()
            
            for detection in detections:
                especie = detection['especie']
                especies[especie] = especies.get(especie, 0) + 1
                confidencias.append(detection['confianza'])
                frames_unicos.add(detection['frame_numero'])
            
            return {
                'total_animales': len(detections),
                'especies_encontradas': list(especies.keys()),
                'detecciones_por_especie': especies,
                'confianza_promedio': round(sum(confidencias) / len(confidencias), 3),
                'frames_con_detecciones': len(frames_unicos)
            }
        
        except Exception as e:
            logger.error(f"Error generando estadísticas: {e}")
            return {}
    
    def generate_excel_report(self, analysis_results: List[Dict[str, Any]], 
                            output_file: str = None) -> str:
        """Generar reporte Excel con todos los análisis incluyendo referencias a imágenes"""
        try:
            import pandas as pd
            from datetime import datetime
            
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"fauna_analysis_report_{timestamp}.xlsx"
            
            # Preparar datos para Excel
            all_detections = []
            video_summary = []
            
            for result in analysis_results:
                video_info = {
                    'video_id': result['video_id'],
                    'video_name': result['video_name'],
                    'camara_id': result['metadata'].get('camara_id'),
                    'fecha_video': result['metadata'].get('fecha_video'),
                    'hora_video': result['metadata'].get('hora_video'),
                    'ubicacion_gps': result['metadata'].get('ubicacion_gps'),
                    'temperatura': result['metadata'].get('temperatura'),
                    'duracion': result['metadata'].get('duration'),
                    'resolucion': result['metadata'].get('resolution'),
                    'total_detecciones': result['estadisticas'].get('total_animales', 0),
                    'especies_encontradas': ', '.join(result['estadisticas'].get('especies_encontradas', [])),
                    'confianza_promedio': result['estadisticas'].get('confianza_promedio', 0)
                }
                video_summary.append(video_info)
                
                # Agregar detecciones individuales
                for detection in result['detecciones']:
                    detection_row = {
                        'video_id': result['video_id'],
                        'video_name': result['video_name'],
                        'camara_id': detection.get('camara_id'),
                        'fecha_video': detection.get('fecha_video'),
                        'hora_video': detection.get('hora_video'),
                        'temperatura': detection.get('temperatura'),
                        'especie': detection['especie'],
                        'confianza': detection['confianza'],
                        'frame_numero': detection['frame_numero'],
                        'timestamp_video': detection['timestamp_video'],
                        'bbox_x': detection['bbox_x'],
                        'bbox_y': detection['bbox_y'],
                        'bbox_width': detection['bbox_width'],
                        'bbox_height': detection['bbox_height'],
                        'ruta_evidencia': detection['ruta_evidencia'],
                        'ruta_evidencia_limpia': detection['ruta_evidencia'].replace('.jpg', '_clean.jpg'),
                        'tamaño_animal': f"{detection['bbox_width']}x{detection['bbox_height']} px"
                    }
                    all_detections.append(detection_row)
            
            # Crear archivo Excel
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Hoja 1: Resumen por video
                if video_summary:
                    df_summary = pd.DataFrame(video_summary)
                    df_summary.to_excel(writer, sheet_name='Resumen_Videos', index=False)
                
                # Hoja 2: Todas las detecciones con rutas de imágenes
                if all_detections:
                    df_detections = pd.DataFrame(all_detections)
                    df_detections.to_excel(writer, sheet_name='Detecciones_Completas', index=False)
                
                # Hoja 3: Estadísticas por especie
                if all_detections:
                    df_species = df_detections.groupby('especie').agg({
                        'video_id': 'nunique',
                        'confianza': ['count', 'mean', 'max', 'min'],
                        'temperatura': 'mean',
                        'bbox_width': 'mean',
                        'bbox_height': 'mean'
                    }).round(3)
                    df_species.columns = [
                        'Videos_Unicos', 'Total_Detecciones', 'Confianza_Promedio', 
                        'Confianza_Maxima', 'Confianza_Minima', 'Temperatura_Promedio',
                        'Ancho_Promedio_px', 'Alto_Promedio_px'
                    ]
                    df_species.to_excel(writer, sheet_name='Estadisticas_Especies')
                
                # Hoja 4: Resumen de evidencias fotográficas
                if all_detections:
                    df_evidencias = df_detections[['especie', 'camara_id', 'fecha_video', 'ruta_evidencia', 'confianza']].copy()
                    df_evidencias['nombre_archivo'] = df_evidencias['ruta_evidencia'].apply(lambda x: Path(x).name if x else '')
                    df_evidencias.to_excel(writer, sheet_name='Evidencias_Fotograficas', index=False)
            
            logger.info(f"Reporte Excel generado: {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error generando reporte Excel: {e}")
            raise