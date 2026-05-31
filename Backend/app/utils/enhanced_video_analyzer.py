import cv2
import re
import logging
import os
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
    """Analizador de video con deteccion animal, clasificacion de especie y OCR."""

    def __init__(self):
        self.metadata_extractor = VideoMetadataExtractor()
        self.yolo_detector = ImprovedYOLODetector()
        self.classifier = SmartSpeciesClassifier()
        self.ocr_extractor = OCRExtractor()
        self.results_base = Path("Resultados")

    def analyze_video_smart(self, video_path: str, output_dir: str = "video_analysis/analysis", video_id: str = None) -> Dict[str, Any]:
        try:
            video_name = Path(video_path).stem
            video_id = video_id or str(uuid.uuid4())[:8]

            logger.info("Iniciando analisis inteligente: %s", video_name)
            metadata = self._extract_enhanced_metadata(video_path)

            analysis_dir = Path(output_dir) / f"{video_name}_{video_id}"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            detections = self.yolo_detector.process_video_enhanced(video_path, str(analysis_dir), metadata)

            smart_detections = []
            for det in detections:
                frame = cv2.imread(det.get("ruta_evidencia", ""))
                if frame is not None:
                    det = self.classifier.classify_species_intelligently(det, frame)
                    frame_ocr = self.ocr_extractor.extract_text_from_frame_band(
                        frame,
                        float(det.get("timestamp_video", 0) or 0),
                    )
                    self._apply_ocr_to_detection(det, frame_ocr, metadata)
                smart_detections.append(det)

            # 1. Validación de contexto inicial (eliminar duplicados temporales cercanos)
            temp_detections = self.classifier.validate_detection_context(smart_detections, metadata)
            
            # 2. Normalización de especies antes de la selección final
            for det in temp_detections:
                det["especie_final"] = self._normalize_species(det.get("especie") or det.get("species"))

            # 3. SELECCIÓN FINAL (Mejora Quirúrgica): Máximo 3 por especie_final, 1 con bbox
            species_groups = {}
            for det in temp_detections:
                sp = det["especie_final"]
                species_groups.setdefault(sp, []).append(det)
            
            final_detections = []
            for sp, group in species_groups.items():
                # Ordenar por confianza y calidad
                group.sort(key=lambda x: (float(x.get("confianza", 0)) * float(x.get("calidad", 0.5))), reverse=True)
                
                # Tomar solo las 3 mejores
                top_3 = group[:3]
                
                # Marcar la mejor para tener bounding box
                for i, det in enumerate(top_3):
                    det["has_bounding_box"] = (i == 0)
                    det["photo_rank"] = i + 1
                    det["photo_type"] = "with_bbox" if i == 0 else "clean"
                
                final_detections.extend(top_3)

            # 4. Proceso de guardado final respetando la selección
            for index, det in enumerate(final_detections, start=1):
                ruta_original = det.get("ruta_evidencia", "")
                if not ruta_original or not Path(ruta_original).exists():
                    continue

                species = det["especie_final"]
                camera_id = self._sanitize_token(det.get("camera_id") or metadata.get("camara_id") or "UNKNOWN")
                date_value = det.get("fecha") or metadata.get("fecha_video")
                time_value = det.get("hora") or metadata.get("hora_video")
                
                # Mantener el tipo de foto (bbox o clean)
                suffix = "_bbox" if det.get("has_bounding_box") else "_clean"
                stamp = self._build_capture_stamp(date_value, time_value, index)

                species_dir = self.results_base / camera_id / species
                species_dir.mkdir(parents=True, exist_ok=True)
                
                evidence_name = f"{species}_{camera_id}_{stamp}{suffix}.jpg"
                evidence_path = species_dir / evidence_name
                
                # Si necesita bounding box, lo generamos aquí mismo para asegurar que los metadatos estén correctos
                if det.get("has_bounding_box"):
                    frame = cv2.imread(ruta_original)
                    if frame is not None:
                        # Usar el detector para dibujar (centralizando la lógica visual)
                        from app.utils.improved_yolo_detector import ImprovedYOLODetector
                        # Preparamos los datos para el dibujo
                        draw_det = {
                            "species": species,
                            "confidence": det.get("confianza", 0),
                            "bbox": det.get("bbox")
                        }
                        # El detector tiene la lógica de dibujo
                        roi_with_bbox = self.yolo_detector._add_professional_bounding_box(
                            frame, draw_det, det.get("bbox"), (0, 0), metadata
                        )
                        cv2.imwrite(str(evidence_path), roi_with_bbox)
                    else:
                        import shutil
                        shutil.copy2(ruta_original, evidence_path)
                else:
                    import shutil
                    shutil.copy2(ruta_original, evidence_path)

                det["especie"] = species
                det["species"] = species
                det["camera_id"] = camera_id
                det["nombre_archivo"] = evidence_name
                det["ruta_evidencia_final"] = str(evidence_path)
                logger.info(f"✅ Evidencia final ({suffix}) guardada en: {evidence_path}")

            excel_files = self._write_camera_excels(final_detections)
            stats = self._generate_enhanced_statistics(final_detections)
            result = {
                "video_id": video_id,
                "video_name": video_name,
                "status": "success",
                "analyzer_version": "2.1-controlled-fixes",
                "detector_version": "enhanced_v2.0",
                "features": [
                    "improved_yolo_detection",
                    "smart_species_classification",
                    "bottom_band_ocr",
                    "per_camera_results",
                ],
                "metadata": metadata,
                "detecciones": final_detections,
                "estadisticas": stats,
                "excel_files": excel_files,
                "analysis_dir": str(analysis_dir),
                "procesado_en": datetime.now().isoformat(),
            }

            with open(analysis_dir / "analysis_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            logger.info("Analisis completado. Especies: %s", stats["especies_encontradas"])
            return result
        except Exception as e:
            logger.error("Error en analisis inteligente: %s", e)
            raise

    def _extract_enhanced_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extraer datos tecnicos y OCR inicial sin usar EXIF para fecha/camara."""
        try:
            metadata = self._extract_video_technical_metadata(video_path)
            ocr_data = {}
            try:
                ocr_data = self.ocr_extractor.extract_text_from_video(video_path)
            except Exception as e:
                logger.warning("OCR no disponible para %s: %s", video_path, e)

            ocr_camera_id = ocr_data.get("camera_id")
            camera_id = ocr_camera_id if self._is_plausible_camera_id(ocr_camera_id) else "UNKNOWN"

            return {
                "filename": metadata.get("filename", Path(video_path).name),
                "file_size": metadata.get("file_size", 0),
                "duration": metadata.get("duration", 0),
                "fps": metadata.get("fps", 0),
                "resolution": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
                "fecha_video": ocr_data.get("fecha"),
                "hora_video": ocr_data.get("hora"),
                "temperatura": ocr_data.get("temperatura"),
                "camara_id": camera_id,
                "timestamp_original": None,
                "ocr_info": {
                    "frames_procesados": ocr_data.get("frames_procesados", 0),
                    "texto_detectado": bool(ocr_data.get("raw_extractions")),
                },
            }
        except Exception as e:
            logger.error("Error metadatos: %s", e)
            return {"filename": Path(video_path).name, "camara_id": "UNKNOWN"}

    def _apply_ocr_to_detection(self, detection: Dict[str, Any], ocr_data: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        camera_id = ocr_data.get("camera_id") if ocr_data else None
        if not self._is_plausible_camera_id(camera_id):
            camera_id = metadata.get("camara_id")
        detection["camera_id"] = camera_id or "UNKNOWN"
        detection["fecha"] = (ocr_data or {}).get("fecha") or metadata.get("fecha_video")
        detection["hora"] = (ocr_data or {}).get("hora") or metadata.get("hora_video")
        detection["temperatura_c"] = (ocr_data or {}).get("temperatura", metadata.get("temperatura"))
        detection["ocr_raw_text"] = (ocr_data or {}).get("raw_text", [])

    def _extract_video_technical_metadata(self, video_path: str) -> Dict[str, Any]:
        metadata = {
            "filename": Path(video_path).name,
            "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
            "duration": 0,
            "fps": 0,
            "width": 0,
            "height": 0,
        }
        cap = cv2.VideoCapture(video_path)
        try:
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                metadata["fps"] = fps or 0
                metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                metadata["duration"] = frame_count / fps if fps and fps > 0 else 0
        finally:
            cap.release()
        return metadata

    def _extract_camera_id(self, video_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        path = Path(video_path)
        parent_match = re.search(r"camara[-_\s]*(\w+)", path.parent.name, re.IGNORECASE)
        if parent_match:
            return parent_match.group(1)
        return "UNKNOWN"

    def _is_plausible_camera_id(self, camera_id: Optional[str]) -> bool:
        if not camera_id:
            return False
        normalized = re.sub(r"[^A-Z0-9_-]", "", str(camera_id).upper())
        if len(normalized) < 2 or len(normalized) > 20:
            return False
        return any(ch.isdigit() for ch in normalized) or len(normalized) >= 3

    def _normalize_species(self, species: Optional[str]) -> str:
        value = (species or "").strip().lower()
        # Mapeo extendido para SpeciesNet
        aliases = {
            "jaguar": "Jaguar",
            "panthera onca": "Jaguar",
            "puma": "Puma",
            "puma concolor": "Puma",
            "ocelot": "Ocelote",
            "ocelote": "Ocelote",
            "leopardus pardalis": "Ocelote",
            "tapir": "Tapir",
            "danta": "Tapir",
            "tapirus": "Tapir",
            "tapirus terrestris": "Tapir",
            "deer": "Venado",
            "venado": "Venado",
            "odocoileus": "Venado",
            "mazama": "Venado",
            "agouti": "Agouti",
            "dasyprocta": "Agouti",
            "pecari": "Pecari",
            "tayassu": "Pecari",
            "oso": "Oso",
            "bear": "Oso",
            "tremarctos": "Oso",
            "ave": "Ave",
            "bird": "Ave",
            "vaca": "Vaca",
            "cow": "Vaca",
            "bos taurus": "Vaca"
        }
        
        # Buscar en el mapa de alias
        for key, display_name in aliases.items():
            if key in value:
                return display_name
                
        return value.capitalize() if value else "Otros"

    def _sanitize_token(self, value: Any) -> str:
        token = re.sub(r"[^A-Za-z0-9_-]", "_", str(value or "UNKNOWN").strip())
        return token or "UNKNOWN"

    def _build_capture_stamp(self, date_value: Optional[str], time_value: Optional[str], fallback_index: int) -> str:
        if date_value and time_value:
            return f"{date_value.replace('-', '')}_{time_value.replace(':', '')}"
        return f"UNKNOWN_{fallback_index:04d}"

    def _generate_enhanced_statistics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not detections:
            return {
                "total_animales": 0,
                "especies_encontradas": [],
                "confianza_promedio": 0,
                "correcciones_aplicadas": 0,
                "calidad_promedio": 0,
            }

        species_count = {}
        confidences = []
        qualities = []
        corrections = 0
        for detection in detections:
            species = detection.get("especie") or detection.get("species") or "Otros"
            species_count[species] = species_count.get(species, 0) + 1
            confidences.append(detection.get("confianza") or detection.get("confidence") or 0)
            qualities.append(detection.get("calidad") or detection.get("quality_score") or 0)
            if detection.get("correction_applied"):
                corrections += 1

        return {
            "total_animales": len(detections),
            "especies_encontradas": list(species_count.keys()),
            "detecciones_por_especie": species_count,
            "confianza_promedio": round(sum(confidences) / len(confidences), 3),
            "calidad_promedio": round(sum(qualities) / len(qualities), 3),
            "correcciones_aplicadas": corrections,
            "porcentaje_correcciones": round((corrections / len(detections)) * 100, 1),
        }

    def _write_camera_excels(self, detections: List[Dict[str, Any]]) -> Dict[str, str]:
        import pandas as pd

        rows_by_camera: Dict[str, List[Dict[str, Any]]] = {}
        for detection in detections:
            camera_id = self._sanitize_token(detection.get("camera_id") or "UNKNOWN")
            rows_by_camera.setdefault(camera_id, []).append(self._excel_row(detection))

        excel_files = {}
        for camera_id, rows in rows_by_camera.items():
            camera_dir = self.results_base / camera_id
            camera_dir.mkdir(parents=True, exist_ok=True)
            excel_path = camera_dir / f"excel_{camera_id}.xlsx"
            pd.DataFrame(rows, columns=self._excel_columns()).to_excel(excel_path, index=False)
            excel_files[camera_id] = str(excel_path)
        return excel_files

    def _excel_columns(self) -> List[str]:
        return [
            "Camera ID",
            "Especie",
            "Fecha",
            "Hora",
            "Temperatura °C",
            "Nombre archivo",
            "Ruta archivo",
            "Confianza clasificación",
        ]

    def _excel_row(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "Camera ID": detection.get("camera_id"),
            "Especie": detection.get("especie"),
            "Fecha": detection.get("fecha"),
            "Hora": detection.get("hora"),
            "Temperatura °C": detection.get("temperatura_c"),
            "Nombre archivo": detection.get("nombre_archivo"),
            "Ruta archivo": detection.get("ruta_evidencia_final") or detection.get("ruta_evidencia"),
            "Confianza clasificación": detection.get("confianza") or detection.get("confidence"),
        }

    def generate_excel_report(self, analysis_results: List[Dict[str, Any]], output_file: str = None) -> str:
        detections = []
        for result in analysis_results:
            detections.extend(result.get("detecciones", []))
        excel_files = self._write_camera_excels(detections)
        if output_file:
            import pandas as pd

            rows = [self._excel_row(detection) for detection in detections]
            pd.DataFrame(rows, columns=self._excel_columns()).to_excel(output_file, index=False)
            return output_file
        return next(iter(excel_files.values()), "")
