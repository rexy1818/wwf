import json
import logging
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2

from app.utils.ocr_extractor import OCRExtractor
from app.utils.speciesnet_detector import SpeciesNetDetector

logger = logging.getLogger(__name__)


class EnhancedVideoAnalyzer:
    """Flujo activo: SpeciesNet oficial, OCR de banda inferior, carpetas y Excel por camara."""

    def __init__(self) -> None:
        self.detector = SpeciesNetDetector()
        self.ocr_extractor = OCRExtractor()
        self.results_base = Path("Resultados")

    def analyze_video_smart(
        self,
        video_path: str,
        output_dir: str = "video_analysis/analysis",
        video_id: str = None,
    ) -> Dict[str, Any]:
        try:
            video_name = Path(video_path).stem
            video_id = video_id or str(uuid.uuid4())[:8]
            analysis_dir = Path(output_dir) / f"{video_name}_{video_id}"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Analizando video con SpeciesNet: %s", video_name)
            metadata = self._extract_enhanced_metadata(video_path)
            detections = self.detector.process_video(video_path)

            final_detections = self._select_final_detections(detections)

            self._save_final_evidence(final_detections, metadata)

            excel_files = self._write_camera_excels(final_detections)
            stats = self._generate_enhanced_statistics(final_detections)
            result = {
                "video_id": video_id,
                "video_name": video_name,
                "status": "success",
                "analyzer_version": "3.0-speciesnet-official-nodemand",
                "detector_version": "Google_SpeciesNet_v4.0.2a",
                "features": [
                    "speciesnet_official",
                    "on_demand_ocr",
                    "per_camera_results",
                    "per_camera_excel",
                ],
                "metadata": metadata,
                "detecciones": final_detections,
                "estadisticas": stats,
                "excel_files": excel_files,
                "analysis_dir": str(analysis_dir),
                "procesado_en": datetime.now().isoformat(),
            }

            with open(analysis_dir / "analysis_result.json", "w", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, ensure_ascii=False, default=str)

            logger.info("Analisis completado (deteccion solo). Especies: %s", stats["especies_encontradas"])
            return result
        except Exception as exc:
            logger.error("Error en analisis de video: %s", exc)
            raise

    def extract_ocr_for_detection(
        self, detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extraer OCR para una detección específica bajo demanda, sin usar metadata."""
        frame = cv2.imread(detection.get("ruta_evidencia", ""))
        ocr_data = {}
        if frame is not None:
            ocr_data = self.ocr_extractor.extract_text_from_frame_band(
                frame,
                float(detection.get("timestamp_video", 0) or 0),
            )
            self._apply_ocr_to_detection(detection, ocr_data)
        return ocr_data

    def _extract_enhanced_metadata(self, video_path: str) -> Dict[str, Any]:
        metadata = self._extract_video_technical_metadata(video_path)
        return {
            "filename": metadata.get("filename", Path(video_path).name),
            "file_size": metadata.get("file_size", 0),
            "duration": metadata.get("duration", 0),
            "fps": metadata.get("fps", 0),
            "resolution": f"{metadata.get('width', 0)}x{metadata.get('height', 0)}",
            "fecha_video": None,
            "hora_video": None,
            "temperatura": None,
            "camara_id": "UNKNOWN",
            "timestamp_original": None,
            "ocr_info": {
                "frames_procesados": 0,
                "texto_detectado": False,
            },
        }

    def _apply_ocr_to_detection(
        self,
        detection: Dict[str, Any],
        ocr_data: Dict[str, Any],
    ) -> None:
        """Aplicar OCR extraído a la detección, ignorando metadata externa."""
        detection["camera_id"] = (ocr_data or {}).get("camera_id") or "UNKNOWN"
        detection["fecha"] = (ocr_data or {}).get("fecha")
        detection["hora"] = (ocr_data or {}).get("hora")
        detection["temperatura_c"] = (ocr_data or {}).get("temperatura")
        detection["ocr_raw_text"] = (ocr_data or {}).get("raw_text", [])

    def _select_final_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped = self._dedupe_detections(detections)
        species_groups: Dict[str, List[Dict[str, Any]]] = {}

        for detection in deduped:
            species = self._normalize_species(detection.get("especie") or detection.get("species"))
            detection["especie_final"] = species
            species_groups.setdefault(species, []).append(detection)

        has_specific_species = any(species != "Otros" for species in species_groups)
        if has_specific_species and "Otros" in species_groups:
            species_groups["Otros"] = [
                detection
                for detection in species_groups["Otros"]
                if float(detection.get("confianza") or detection.get("confidence") or 0) >= 0.8
            ]
            if not species_groups["Otros"]:
                del species_groups["Otros"]

        final_detections: List[Dict[str, Any]] = []
        for species, group in species_groups.items():
            group.sort(
                key=lambda item: float(item.get("confianza") or item.get("confidence") or 0)
                * float(item.get("calidad") or 0.5),
                reverse=True,
            )
            for index, detection in enumerate(group[:2]):
                detection["has_bounding_box"] = index == 0
                detection["photo_rank"] = index + 1
                detection["photo_type"] = "with_bbox" if index == 0 else "clean"
                final_detections.append(detection)

        return final_detections

    def _save_final_evidence(self, detections: List[Dict[str, Any]], metadata: Dict[str, Any]) -> None:
        for index, detection in enumerate(detections, start=1):
            source_path = Path(detection.get("ruta_evidencia") or "")
            if not source_path.exists():
                continue

            species = detection["especie_final"]
            camera_id = self._sanitize_token(detection.get("camera_id") or metadata.get("camara_id") or "UNKNOWN")
            date_value = detection.get("fecha") or metadata.get("fecha_video")
            time_value = detection.get("hora") or metadata.get("hora_video")
            suffix = "_bbox" if detection.get("has_bounding_box") else "_clean"
            stamp = self._build_capture_stamp(date_value, time_value, index)

            species_dir = self.results_base / camera_id / species
            species_dir.mkdir(parents=True, exist_ok=True)
            evidence_name = f"{species}_{camera_id}_{stamp}{suffix}.jpg"
            evidence_path = species_dir / evidence_name

            if detection.get("has_bounding_box"):
                frame = cv2.imread(str(source_path))
                if frame is not None:
                    cv2.imwrite(str(evidence_path), self.detector.draw_bounding_box(frame, detection))
                else:
                    shutil.copy2(source_path, evidence_path)
            else:
                shutil.copy2(source_path, evidence_path)

            detection["especie"] = species
            detection["species"] = species
            detection["camera_id"] = camera_id
            detection["nombre_archivo"] = evidence_name
            detection["ruta_evidencia_final"] = str(evidence_path)

    def _dedupe_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        for detection in sorted(detections, key=lambda item: item.get("timestamp_video", 0)):
            species = self._normalize_species(detection.get("especie") or detection.get("species"))
            timestamp = float(detection.get("timestamp_video", 0) or 0)
            duplicate = False
            for existing in selected:
                existing_species = self._normalize_species(existing.get("especie") or existing.get("species"))
                existing_timestamp = float(existing.get("timestamp_video", 0) or 0)
                if species == existing_species and abs(timestamp - existing_timestamp) < 1.2:
                    if self._bbox_iou(detection.get("bbox"), existing.get("bbox")) > 0.3:
                        duplicate = True
                        if float(detection.get("confianza") or 0) > float(existing.get("confianza") or 0):
                            existing.update(detection)
                        break
            if not duplicate:
                selected.append(detection)
        return selected

    def _bbox_iou(self, first: Optional[List[int]], second: Optional[List[int]]) -> float:
        if not first or not second or len(first) != 4 or len(second) != 4:
            return 0.0

        ax1, ay1, ax2, ay2 = [float(value) for value in first]
        bx1, by1, bx2, by2 = [float(value) for value in second]
        inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        inter_area = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)
        first_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        second_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = first_area + second_area - inter_area
        return inter_area / union if union else 0.0

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

    def _is_plausible_camera_id(self, camera_id: Optional[str]) -> bool:
        if not camera_id:
            return False
        normalized = re.sub(r"[^A-Z0-9_-]", "", str(camera_id).upper())
        if len(normalized) < 2 or len(normalized) > 20:
            return False
        return any(ch.isdigit() for ch in normalized) or len(normalized) >= 3

    def _normalize_species(self, species: Optional[str]) -> str:
        value = (species or "").strip().lower()
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
            "peccary": "Pecari",
            "pecari": "Pecari",
            "tayassu": "Pecari",
            "bear": "Oso",
            "oso": "Oso",
            "tremarctos": "Oso",
            "bird": "Ave",
            "ave": "Ave",
            "cow": "Vaca",
            "vaca": "Vaca",
            "bos taurus": "Vaca",
            "mammal": "Otros",
            "animal": "Otros",
            "unknown": "Otros",
        }
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
                "calidad_promedio": 0,
            }

        species_count: Dict[str, int] = {}
        confidences = []
        qualities = []
        for detection in detections:
            species = detection.get("especie") or detection.get("species") or "Otros"
            species_count[species] = species_count.get(species, 0) + 1
            confidences.append(float(detection.get("confianza") or detection.get("confidence") or 0))
            qualities.append(float(detection.get("calidad") or 0))

        return {
            "total_animales": len(detections),
            "especies_encontradas": list(species_count.keys()),
            "detecciones_por_especie": species_count,
            "confianza_promedio": round(sum(confidences) / len(confidences), 3),
            "calidad_promedio": round(sum(qualities) / len(qualities), 3),
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
