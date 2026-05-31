import cv2
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
import json

from app.utils.video_metadata import VideoMetadataExtractor
from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.smart_species_classifier import SmartSpeciesClassifier
from app.utils.ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)

class EnhancedVideoAnalyzer:
    """
    Analizador de video de nueva generación (v2.0)
    Integra detección YOLO mejorada, clasificación inteligente y OCR.
    """
    def __init__(self):
        self.metadata_extractor = VideoMetadataExtractor()
        self.yolo_detector = ImprovedYOLODetector()
        self.classifier = SmartSpeciesClassifier()
        self.ocr_extractor = OCRExtractor()
    
    def analyze_video_smart(self, video_path: str, output_dir: str = "video_analysis/analysis") -> Dict[str, Any]:
        """
        Análisis inteligente completo del video
        """
        try:
            video_name = Path(video_path).stem
            video_id = str(uuid.uuid4())[:8]
            
            logger.info(f"🚀 Iniciando ANÁLISIS INTELIGENTE: {video_name}")
            
            # 1. Extraer metadatos mejorados (OCR + Archivo)
            metadata = self._extract_enhanced_metadata(video_path)
            
            # 2. Crear directorios
            analysis_dir = Path(output_dir) / f"{video_name}_{video_id}"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            
            # 3. Procesamiento YOLO Mejorado
            detections = self.yolo_detector.process_video_enhanced(
                video_path, 
                str(analysis_dir),
                metadata
            )
            
            # 4. Clasificación Inteligente y Guardado de Evidencias
            smart_detections = []
            camera_id = metadata.get('camara_id', 'UNKNOWN_CAM')
            storage_base = Path("storage") / camera_id / "evidencias"
            
            for det in detections:
                frame = cv2.imread(det['ruta_evidencia'])
                if frame is not None:
                    # Clasificar biológicamente (Jaguar, Agouti, Venado, etc.)
                    smart_det = self.classifier.classify_species_intelligently(det, frame)
                    
                    # Definir ruta de almacenamiento final organizada
                    esp = smart_det.get('especie') or smart_det.get('species', 'desconocido')
                    especie_dir = storage_base / esp
                    especie_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Guardar evidencia en su carpeta final
                    evidence_filename = Path(det['ruta_evidencia']).name
                    new_evidence_name = f"{esp}_{video_id}_{evidence_filename}"
                    new_evidence_path = especie_dir / new_evidence_name
                    cv2.imwrite(str(new_evidence_path), frame)
                    
                    smart_det['ruta_evidencia_final'] = str(new_evidence_path)
                    smart_detections.append(smart_det)
                    
                    logger.info(f"📁 Evidencia guardada en: {new_evidence_path}")
                else:
                    smart_detections.append(det)
            
            # 5. Validación Contextual
            final_detections = self.classifier.validate_detection_context(smart_detections, metadata)
            
            # 6. Generar Estadísticas
            stats = self._generate_enhanced_statistics(final_detections)
            
            # 7. Resultado Final
            result = {
                'video_id': video_id,
                'video_name': video_name,
                'status': 'success',
                'analyzer_version': '2.0-enhanced',
                'detector_version': 'enhanced_v2.0',
                'features': [
                    'improved_yolo_detection',
                    'smart_species_classification',
                    'enhanced_frame_selection',
                    'contextual_validation'
                ],
                'metadata': metadata,
                'detecciones': final_detections,
                'estadisticas': stats,
                'analysis_dir': str(analysis_dir),
                'procesado_en': datetime.now().isoformat()
            }
            
            # Guardar JSON de resultados
            with open(analysis_dir / "analysis_result.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
            logger.info(f"✅ Análisis inteligente completado. Especies: {stats['especies_encontradas']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en análisis inteligente: {e}")
            raise

    def _extract_enhanced_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extraer metadatos combinando OCR y metadatos de archivo"""
        try:
            metadata = self.metadata_extractor.extract_metadata(video_path)
            ocr_data = {}
            try:
                ocr_data = self.ocr_extractor.extract_text_from_video(video_path)
            except:
                pass
            
            camera_id = ocr_data.get('camera_id') or self._extract_camera_id(video_path, metadata)
            
            if ocr_data.get('fecha') and ocr_data.get('hora'):
                fecha_video = ocr_data['fecha']
                hora_video = ocr_data['hora']
                try:
                    datetime_obj = datetime.strptime(f"{fecha_video} {hora_video}", "%Y-%m-%d %H:%M:%S")
                except:
                    fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)
            else:
                fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)
            
            enhanced_metadata = {
                'filename': metadata['filename'],
                'file_size': metadata['file_size'],
                'duration': metadata['duration'],
                'fps': metadata['fps'],
                'resolution': f"{metadata['width']}x{metadata['height']}",
                'fecha_video': fecha_video,
                'hora_video': hora_video,
                'temperatura': ocr_data.get('temperatura'),
                'camara_id': camera_id,
                'timestamp_original': datetime_obj.isoformat() if datetime_obj else None
            }
            return enhanced_metadata
        except Exception as e:
            logger.error(f"Error metadatos: {e}")
            return {'filename': Path(video_path).name}

    def _extract_camera_id(self, video_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        filename = Path(video_path).stem
        patterns = [r'CAM(\d+)', r'CAMERA_(\w+)', r'(\w+)_CAM', r'ID(\d+)', r'TRAP(\d+)', r'([A-Z]\d+)']
        for pattern in patterns:
            match = re.search(pattern, filename.upper())
            if match: return match.group(1)
        return "UNKNOWN"

    def _generate_enhanced_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar estadísticas normalizando nombres de campos"""
        if not detections:
            return {
                'total_animales': 0, 'especies_encontradas': [], 
                'confianza_promedio': 0, 'correcciones_aplicadas': 0, 'calidad_promedio': 0
            }
            
        especies = {}
        confidencias = []
        calidades = []
        correcciones = 0
        
        for d in detections:
            esp = d.get('especie') or d.get('species') or "unknown"
            especies[esp] = especies.get(esp, 0) + 1
            
            conf = d.get('confianza') or d.get('confidence') or 0
            confidencias.append(conf)
            
            cal = d.get('calidad') or d.get('quality_score') or 0
            calidades.append(cal)
            
            if d.get('correction_applied'):
                correcciones += 1
            
        return {
            'total_animales': len(detections),
            'especies_encontradas': list(especies.keys()),
            'detecciones_por_especie': especies,
            'confianza_promedio': round(sum(confidencias) / len(confidencias), 3),
            'calidad_promedio': round(sum(calidades) / len(calidades), 3),
            'correcciones_aplicadas': correcciones,
            'porcentaje_correcciones': round((correcciones / len(detections)) * 100, 1) if detections else 0
        }

    def generate_excel_report(self, analysis_results: List[Dict[str, Any]], output_file: str = None) -> str:
        """Generar reporte Excel compatible"""
        import pandas as pd
        if not output_file:
            output_file = f"fauna_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        all_data = []
        for res in analysis_results:
            for det in res.get('detecciones', []):
                all_data.append({
                    'video_name': res.get('video_name'),
                    'camara_id': res.get('metadata', {}).get('camara_id'),
                    'especie': det.get('especie') or det.get('species'),
                    'confianza': det.get('confianza') or det.get('confidence'),
                    'calidad': det.get('calidad') or det.get('quality_score'),
                    'correccion': "SÍ" if det.get('correction_applied') else "NO"
                })
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_excel(output_file, index=False)
            return output_file
        return ""
