import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImprovedYOLODetector:
    def __init__(self, model_path: str = "app/utils/md_v5a.0.0.pt"):
        """
        Detector hibrido: MegaDetector v5a si esta disponible, con YOLOv8n como respaldo.
        """
        self.model_pro = None
        self.model_base = None

        try:
            from ultralytics import YOLO
        except ImportError:
            logger.error("ultralytics no esta instalado. Instala requirements.txt para habilitar YOLO.")
            return

        try:
            self.model_pro = YOLO(model_path)
            logger.info("MegaDetector v5a cargado: %s", model_path)
        except Exception as e:
            logger.warning("No se pudo cargar MegaDetector (%s), usando YOLOv8 si esta disponible", e)

        try:
            self.model_base = YOLO("yolov8n.pt")
            logger.info("YOLOv8n cargado como detector de respaldo")
        except Exception as e:
            logger.error("No se pudo cargar YOLOv8n.pt: %s", e)

        self.animal_classes = {
            15: "bird",
            16: "cat",
            17: "dog",
            18: "horse",
            19: "sheep",
            20: "cow",
            22: "bear",
            23: "zebra",
        }
        self.species_mapping = {
            "zebra": "jaguar",
            "cat": "jaguar",
            "horse": "venado",
            "sheep": "venado",
            "dog": "agouti",
            "bear": "oso",
            "bird": "ave",
        }
        self.species_confidence_thresholds = {
            "jaguar": 0.1,
            "venado": 0.1,
            "agouti": 0.1,
            "oso": 0.1,
            "ave": 0.1,
        }

    def _build_frame_sample_indices(
        self, fps: float, total_frames: int, normal_interval_seconds: float = 3.0
    ) -> List[int]:
        """Crear un muestreo que no pierda animales al inicio del video."""
        if total_frames <= 0:
            return []

        safe_fps = fps if fps and fps > 0 else 30.0
        indices = {0, total_frames - 1}

        early_step = max(1, int(round(safe_fps * 0.1)))
        early_limit = min(total_frames - 1, int(round(safe_fps * 1.0)))
        indices.update(range(0, early_limit + 1, early_step))

        medium_step = max(1, int(round(safe_fps * 0.5)))
        medium_start = min(total_frames - 1, early_limit + 1)
        medium_limit = min(total_frames - 1, int(round(safe_fps * 3.0)))
        if medium_start <= medium_limit:
            indices.update(range(medium_start, medium_limit + 1, medium_step))

        normal_step = max(1, int(round(safe_fps * normal_interval_seconds)))
        normal_start = min(total_frames - 1, medium_limit + 1)
        if normal_start < total_frames:
            indices.update(range(normal_start, total_frames, normal_step))

        return sorted(i for i in indices if 0 <= i < total_frames)

    def extract_frames_around_detections(
        self, video_path: str, initial_interval: int = 3
    ) -> List[Tuple[np.ndarray, int, float]]:
        """
        Extraer frames con prioridad fuerte para el segundo 0-1.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        safe_fps = fps if fps and fps > 0 else 30.0
        sample_indices = self._build_frame_sample_indices(safe_fps, total_frames, initial_interval)

        initial_frames = []
        for frame_count in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if ret:
                initial_frames.append((frame.copy(), frame_count, frame_count / safe_fps))
        cap.release()

        detection_zones = []
        for frame, frame_num, timestamp in initial_frames:
            detections = self.detect_animals_raw(frame, confidence_threshold=0.1)
            if detections:
                detection_zones.append((frame_num, timestamp))

        if detection_zones:
            cap = cv2.VideoCapture(video_path)
            final_frame_indices = {f[1] for f in initial_frames}
            refinement_step = max(1, int(safe_fps * 0.2))
            for detection_frame, _ in detection_zones:
                for offset in range(-5, 6):
                    target_frame = detection_frame + (offset * refinement_step)
                    if 0 <= target_frame < total_frames and target_frame not in final_frame_indices:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                        ret, frame = cap.read()
                        if ret:
                            initial_frames.append((frame.copy(), target_frame, target_frame / safe_fps))
                            final_frame_indices.add(target_frame)
            cap.release()

        initial_frames.sort(key=lambda x: x[2])
        return initial_frames

    def detect_animals_raw(self, frame: np.ndarray, confidence_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        Deteccion hibrida de alta sensibilidad.
        """
        detections = []
        if self.model_pro:
            try:
                results = self.model_pro(frame, verbose=False)
                for res in results:
                    for box in res.boxes:
                        conf = float(box.conf[0])
                        if int(box.cls[0]) == 0 and conf >= confidence_threshold:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            detections.append(
                                {
                                    "species": "animal_silvestre",
                                    "confidence": conf,
                                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                    "area": (x2 - x1) * (y2 - y1),
                                }
                            )
            except Exception as e:
                logger.debug("Error detectando con MegaDetector: %s", e)

        if not detections and self.model_base:
            try:
                results = self.model_base(frame, verbose=False)
                for res in results:
                    for box in res.boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        if cls in self.animal_classes and conf >= confidence_threshold:
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            label = self.animal_classes[cls]
                            species = self.species_mapping.get(label, label)
                            detections.append(
                                {
                                    "species": species,
                                    "confidence": conf,
                                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                    "area": (x2 - x1) * (y2 - y1),
                                }
                            )
            except Exception as e:
                logger.debug("Error detectando con YOLOv8: %s", e)
        return detections

    def detect_animals_enhanced(self, frame: np.ndarray, confidence_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Detectar animales con evaluacion de calidad mejorada."""
        raw_detections = self.detect_animals_raw(frame, confidence_threshold)
        enhanced_detections = []
        for detection in raw_detections:
            quality_score = self._evaluate_detection_quality(frame, detection)
            detection["quality_score"] = quality_score
            detection["adjusted_confidence"] = detection["confidence"] * quality_score
            enhanced_detections.append(detection)
        enhanced_detections.sort(key=lambda x: x["adjusted_confidence"], reverse=True)
        return enhanced_detections

    def _evaluate_detection_quality(self, frame: np.ndarray, detection: Dict[str, Any]) -> float:
        try:
            x1, y1, x2, y2 = detection["bbox"]
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                return 0.1
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            sharpness_score = min(1.0, cv2.Laplacian(gray_roi, cv2.CV_64F).var() / 100.0)
            return max(0.1, min(1.0, sharpness_score))
        except Exception:
            return 0.5

    def select_best_detections(
        self, all_detections: List[Tuple[np.ndarray, int, float, List[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        species_detections = {}
        for frame, frame_num, timestamp, detections in all_detections:
            for d in detections:
                sp = d["species"]
                if sp not in species_detections:
                    species_detections[sp] = []
                species_detections[sp].append({**d, "frame": frame, "frame_number": frame_num, "timestamp": timestamp})

        best_detections = []
        for _, dets in species_detections.items():
            dets.sort(key=lambda x: x["adjusted_confidence"], reverse=True)
            best_detections.append(dets[0])
        return best_detections

    def save_enhanced_evidence(
        self, detection: Dict[str, Any], evidence_path: Path, evidence_name: str, metadata: Dict[str, Any] = None
    ) -> str:
        try:
            evidence_path.mkdir(parents=True, exist_ok=True)
            file_path = evidence_path / evidence_name
            cv2.imwrite(str(file_path), detection["frame"])
            return str(file_path)
        except Exception:
            return ""

    def process_video_enhanced(self, video_path: str, output_dir: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            frames = self.extract_frames_around_detections(video_path)
            all_detections = []
            for frame, frame_num, timestamp in frames:
                dets = self.detect_animals_enhanced(frame, 0.1)
                if dets:
                    all_detections.append((frame, frame_num, timestamp, dets))
            if not all_detections:
                return []

            best_detections = self.select_best_detections(all_detections)
            final_detections = []
            evidencias_dir = Path(output_dir) / "evidencias"
            for det in best_detections:
                sp = det["species"]
                sp_dir = evidencias_dir / sp
                ev_name = f"{sp}_{Path(video_path).stem}_{det['frame_number']}.jpg"
                path = self.save_enhanced_evidence(det, sp_dir, ev_name, metadata)
                final_detections.append(
                    {
                        "especie": sp,
                        "confianza": round(det["confidence"], 3),
                        "calidad": round(det.get("quality_score", 0), 3),
                        "bbox": det.get("bbox"),
                        "area": det.get("area"),
                        "frame_numero": det["frame_number"],
                        "timestamp_video": round(det["timestamp"], 2),
                        "ruta_evidencia": path,
                    }
                )
            return final_detections
        except Exception as e:
            logger.error("Error procesando video con detector mejorado: %s", e)
            return []
