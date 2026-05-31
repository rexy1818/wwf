import cv2
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
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
    Analizador de video con deteccion animal, clasificacion de especie y OCR.
    """
    def __init__(self):
        self.metadata_extractor = VideoMetadataExtractor()
        self.yolo_detector = ImprovedYOLODetector()
        self.classifier = SmartSpeciesClassifier()
        self.ocr_extractor = OCRExtractor()

    def analyze_video_smart(self, video_path: str, output_dir: str = "video_analysis/analysis", video_id: str = None) -> Dict[str, Any]:
        try:
            video_name = Path(video_path).stem
            video_id = video_id or str(uuid.uuid4())[:8]

            logger.info("Iniciando analisis inteligente: %s", video_name)
            metadata = self._extract_enhanced_metadata(video_path)

            analysis_dir = Path(output_dir) / f"{video_name}_{video_id}"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            detections = self.yolo_detector.process_video_enhanced(
                video_path,
                str(analysis_dir),
                metadata,
            )

            smart_detections = []
            camera_id = metadata.get('camara_id', 'UNKNOWN_CAM')
            storage_base = Path("storage") / camera_id / "evidencias"

            for det in detections:
                frame = cv2.imread(det.get('ruta_evidencia', ''))
                if frame is not None:
                    smart_detections.append(self.classifier.classify_species_intelligently(det, frame))
                else:
                    smart_detections.append(det)

            final_detections = self.classifier.validate_detection_context(smart_detections, metadata)

            for det in final_detections:
                frame = cv2.imread(det.get('ruta_evidencia', ''))
                if frame is None:
                    continue

                species = det.get('especie') or det.get('species') or 'desconocido'
                species_dir = storage_base / species
                species_dir.mkdir(parents=True, exist_ok=True)

                frame_number = det.get('frame_numero', 'unknown')
                timestamp = str(det.get('timestamp_video', '0')).replace('.', '_')
                evidence_name = f"{species}_{video_id}_frame_{frame_number}_t_{timestamp}s.jpg"
                evidence_path = species_dir / evidence_name
                cv2.imwrite(str(evidence_path), frame)
                det['ruta_evidencia_final'] = str(evidence_path)
                logger.info("Evidencia guardada en: %s", evidence_path)

            stats = self._generate_enhanced_statistics(final_detections)
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
                    'contextual_validation',
                ],
                'metadata': metadata,
                'detecciones': final_detections,
                'estadisticas': stats,
                'analysis_dir': str(analysis_dir),
                'procesado_en': datetime.now().isoformat(),
            }

            with open(analysis_dir / "analysis_result.json", 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            logger.info("Analisis completado. Especies: %s", stats['especies_encontradas'])
            return result
        except Exception as e:
            logger.error("Error en analisis inteligente: %s", e)
            raise

    def _extract_enhanced_metadata(self, video_path: str) -> Dict[str, Any]:
        try:
            metadata = self.metadata_extractor.extract_metadata(video_path)
            ocr_data = {}
            try:
                ocr_data = self.ocr_extractor.extract_text_from_video(video_path)
            except Exception as e:
                logger.warning("OCR no disponible para %s: %s", video_path, e)

            ocr_camera_id = ocr_data.get('camera_id')
            camera_id = ocr_camera_id if self._is_plausible_camera_id(ocr_camera_id) else self._extract_camera_id(video_path, metadata)

            if ocr_data.get('fecha') and ocr_data.get('hora'):
                fecha_video = ocr_data['fecha']
                hora_video = ocr_data['hora']
                try:
                    datetime_obj = datetime.strptime(f"{fecha_video} {hora_video}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)
            else:
                fecha_video, hora_video, datetime_obj = self.metadata_extractor.get_video_datetime(metadata)

            return {
                'filename': metadata['filename'],
                'file_size': metadata['file_size'],
                'duration': metadata['duration'],
                'fps': metadata['fps'],
                'resolution': f"{metadata['width']}x{metadata['height']}",
                'fecha_video': fecha_video,
                'hora_video': hora_video,
                'temperatura': ocr_data.get('temperatura'),
                'camara_id': camera_id,
                'timestamp_original': datetime_obj.isoformat() if datetime_obj else None,
            }
        except Exception as e:
            logger.error("Error metadatos: %s", e)
            return {'filename': Path(video_path).name}

    def _extract_camera_id(self, video_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        path = Path(video_path)
        parent_match = re.search(r'camara[-_\s]*(\w+)', path.parent.name, re.IGNORECASE)
        if parent_match:
            return parent_match.group(1)

        filename = re.sub(r'^[0-9a-f]{8}-[0-9a-f]{3}_', '', path.stem, flags=re.IGNORECASE)
        patterns = [
            r'\bCAM[-_\s]*(\w+)\b',
            r'\bCAMERA[-_\s]*(\w+)\b',
            r'\b(\w+)[-_\s]*CAM\b',
            r'\bID[-_\s]*(\w+)\b',
            r'\bTRAP[-_\s]*(\w+)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, filename.upper())
            if match and self._is_plausible_camera_id(match.group(1)):
                return match.group(1)
        return "UNKNOWN"

    def _is_plausible_camera_id(self, camera_id: Optional[str]) -> bool:
        if not camera_id:
            return False
        normalized = re.sub(r'[^A-Z0-9_-]', '', str(camera_id).upper())
        if len(normalized) < 2 or len(normalized) > 20:
            return False
        return any(ch.isdigit() for ch in normalized) or len(normalized) >= 3

    def _generate_enhanced_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not detections:
            return {
                'total_animales': 0,
                'especies_encontradas': [],
                'confianza_promedio': 0,
                'correcciones_aplicadas': 0,
                'calidad_promedio': 0,
            }

        species_count = {}
        confidences = []
        qualities = []
        corrections = 0

        for detection in detections:
            species = detection.get('especie') or detection.get('species') or 'unknown'
            species_count[species] = species_count.get(species, 0) + 1
            confidences.append(detection.get('confianza') or detection.get('confidence') or 0)
            qualities.append(detection.get('calidad') or detection.get('quality_score') or 0)
            if detection.get('correction_applied'):
                corrections += 1

        return {
            'total_animales': len(detections),
            'especies_encontradas': list(species_count.keys()),
            'detecciones_por_especie': species_count,
            'confianza_promedio': round(sum(confidences) / len(confidences), 3),
            'calidad_promedio': round(sum(qualities) / len(qualities), 3),
            'correcciones_aplicadas': corrections,
            'porcentaje_correcciones': round((corrections / len(detections)) * 100, 1) if detections else 0,
        }

    def generate_excel_report(self, analysis_results: List[Dict[str, Any]], output_file: str = None) -> str:
        import pandas as pd

        if not output_file:
            output_file = f"fauna_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        all_data = []
        for result in analysis_results:
            metadata = result.get('metadata', {})
            for detection in result.get('detecciones', []):
                all_data.append({
                    'video_name': result.get('video_name'),
                    'camara_id': metadata.get('camara_id'),
                    'fecha_video': metadata.get('fecha_video'),
                    'hora_video': metadata.get('hora_video'),
                    'temperatura': metadata.get('temperatura'),
                    'especie': detection.get('especie') or detection.get('species'),
                    'confianza': detection.get('confianza') or detection.get('confidence'),
                    'calidad': detection.get('calidad') or detection.get('quality_score'),
                    'frame_numero': detection.get('frame_numero'),
                    'timestamp_video': detection.get('timestamp_video'),
                    'ruta_evidencia': detection.get('ruta_evidencia_final') or detection.get('ruta_evidencia'),
                    'correccion': "SI" if detection.get('correction_applied') else "NO",
                })

        if all_data:
            df = pd.DataFrame(all_data)
            df.to_excel(output_file, index=False)
            return output_file
        return ""
