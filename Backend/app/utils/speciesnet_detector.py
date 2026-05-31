import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class SpeciesNetDetector:
    """Detector oficial SpeciesNet para videos de camaras trampa."""

    def __init__(self) -> None:
        self.model_path = "kaggle:google/speciesnet/pyTorch/v4.0.2a/1"
        self.temp_dir = Path("video_analysis/temp_frames")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.model = None

    def _ensure_model(self) -> bool:
        if self.model is not None:
            return True

        try:
            from speciesnet.multiprocessing import SpeciesNet

            logger.info("Inicializando Google SpeciesNet Ensemble: %s", self.model_path)
            self.model = SpeciesNet(
                model_name=self.model_path,
                components="all",
                geofence=True,
                multiprocessing=False,
            )
            logger.info("SpeciesNet listo")
            return True
        except Exception as exc:
            logger.error("No se pudo inicializar SpeciesNet: %s", exc)
            return False

    def process_video(self, video_path: str, sample_rate_seconds: float = None) -> List[Dict[str, Any]]:
        """Procesa un video desde el segundo 0 y devuelve detecciones animales."""
        if not self._ensure_model():
            logger.error("SpeciesNet no esta inicializado")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("No se pudo abrir el video: %s", video_path)
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if sample_rate_seconds is None:
            sample_rate_seconds = float(os.getenv("SPECIESNET_SAMPLE_SECONDS", "1.0"))

        session_dir = self.temp_dir / str(uuid.uuid4())[:8]
        session_dir.mkdir(parents=True, exist_ok=True)
        sample_step = max(1, int(round(fps * sample_rate_seconds)))

        frame_paths: List[str] = []
        frame_indices: List[int] = []
        sample_indices = sorted(set(list(range(0, total_frames, sample_step)) + [max(0, total_frames - 1)]))
        for frame_index in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok:
                break

            frame_path = session_dir / f"frame_{frame_index:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(str(frame_path))
            frame_indices.append(frame_index)

        cap.release()

        if not frame_paths:
            return []

        try:
            results = self.model.predict(filepaths=frame_paths)
        except Exception as exc:
            logger.error("Error ejecutando SpeciesNet: %s", exc)
            return []

        detections: List[Dict[str, Any]] = []
        for index, prediction_result in enumerate(results.get("predictions", [])):
            prediction = prediction_result.get("prediction")
            score = float(prediction_result.get("prediction_score") or 0)
            species_name = self._extract_common_name(str(prediction or ""))

            if self._is_non_animal_prediction(species_name, prediction):
                continue

            model_detections = prediction_result.get("detections") or []
            if not model_detections:
                continue

            bbox = self._bbox_to_pixels(model_detections[0].get("bbox"), width, height)
            if not bbox:
                continue

            detections.append(
                {
                    "species": species_name,
                    "especie": species_name,
                    "confidence": score,
                    "confianza": score,
                    "bbox": bbox,
                    "normalized_bbox": model_detections[0].get("bbox"),
                    "ruta_evidencia": prediction_result.get("filepath"),
                    "timestamp_video": frame_indices[index] / fps,
                    "calidad": 0.95,
                    "detector_source": "Google_SpeciesNet_v4.0.2a",
                    "original_prediction": prediction,
                }
            )

        logger.info("SpeciesNet detecto %s animales", len(detections))
        return detections

    def draw_bounding_box(self, image: np.ndarray, detection: Dict[str, Any]) -> np.ndarray:
        try:
            result = image.copy()
            x1, y1, x2, y2 = detection.get("bbox") or [0, 0, 0, 0]
            h, w = result.shape[:2]
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w, int(x2)), min(h, int(y2))

            label = f"{(detection.get('especie') or detection.get('species') or 'Animal').upper()} {float(detection.get('confianza') or detection.get('confidence') or 0):.2f}"
            cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 3)
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            label_y = max(text_h + 10, y1)
            cv2.rectangle(result, (x1, label_y - text_h - 10), (x1 + text_w + 8, label_y), (0, 255, 0), -1)
            cv2.putText(result, label, (x1 + 4, label_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            return result
        except Exception as exc:
            logger.error("Error dibujando bounding box: %s", exc)
            return image

    def _extract_common_name(self, prediction: str) -> str:
        if not prediction:
            return "Desconocido"
        if ";" not in prediction:
            return prediction.strip()
        parts = [part.strip() for part in prediction.split(";")]
        for value in reversed(parts):
            if value:
                return value
        return "Desconocido"

    def _is_non_animal_prediction(self, species_name: str, prediction: Any) -> bool:
        value = f"{species_name} {prediction or ''}".lower()
        return any(token in value for token in ("blank", "vehicle", "human", "person"))

    def _bbox_to_pixels(self, bbox: Any, width: int, height: int) -> List[int]:
        if not bbox or len(bbox) != 4:
            return []
        xmin, ymin, bbox_width, bbox_height = [float(value) for value in bbox]
        return [
            int(xmin * width),
            int(ymin * height),
            int((xmin + bbox_width) * width),
            int((ymin + bbox_height) * height),
        ]
