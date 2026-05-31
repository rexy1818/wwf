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

    def _ensure_yolo(self) -> Any:
        from ultralytics import YOLO
        if not hasattr(self, 'yolo'):
            # Cargamos nano por velocidad
            self.yolo = YOLO("yolov8n.pt") 
        return self.yolo

    def process_video(self, video_path: str, sample_rate_seconds: float = None) -> List[Dict[str, Any]]:
        """Procesa un video usando YOLO como filtro previo y SpeciesNet para clasificar."""
        if not self._ensure_model():
            logger.error("SpeciesNet no esta inicializado")
            return []
        
        yolo = self._ensure_yolo()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("No se pudo abrir el video: %s", video_path)
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if sample_rate_seconds is None:
            sample_rate_seconds = float(os.getenv("SPECIESNET_SAMPLE_SECONDS", "1.0"))

        session_dir = self.temp_dir / str(uuid.uuid4())[:8]
        session_dir.mkdir(parents=True, exist_ok=True)
        sample_step = max(1, int(round(fps * sample_rate_seconds)))

        # Paso 1: Filtro rápido con YOLO
        animal_frame_paths = []
        frame_metadata = []
        
        sample_indices = sorted(set(list(range(0, total_frames, sample_step)) + [max(0, total_frames - 1)]))
        
        logger.info("Iniciando filtrado YOLO en %d frames", len(sample_indices))
        for frame_index in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok:
                break
            
            # YOLO: Buscar clases de animales (COCO id: 15-23 son animales, pero YOLOv8 detecta 'person' que ignoraremos)
            results = yolo.predict(frame, verbose=False, classes=[15, 16, 17, 18, 19, 20, 21, 22, 23])
            
            if len(results[0].boxes) > 0:
                frame_path = session_dir / f"frame_{frame_index:06d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                animal_frame_paths.append(str(frame_path))
                frame_metadata.append({"index": frame_index, "bbox": results[0].boxes[0].xyxy[0].cpu().numpy().tolist()})

        cap.release()

        if not animal_frame_paths:
            logger.info("YOLO no detecto animales")
            return []
            
        logger.info("YOLO detecto candidatos en %d frames. Iniciando SpeciesNet...", len(animal_frame_paths))

        # Paso 2: Clasificación solo de frames candidatos con SpeciesNet
        try:
            results = self.model.predict(filepaths=animal_frame_paths)
        except Exception as exc:
            logger.error("Error ejecutando SpeciesNet: %s", exc)
            return []

        detections: List[Dict[str, Any]] = []
        for i, prediction_result in enumerate(results.get("predictions", [])):
            prediction = prediction_result.get("prediction")
            score = float(prediction_result.get("prediction_score") or 0)
            species_name = self._extract_common_name(str(prediction or ""))

            if self._is_non_animal_prediction(species_name, prediction):
                continue
                
            detections.append(
                {
                    "species": species_name,
                    "especie": species_name,
                    "confidence": score,
                    "confianza": score,
                    "bbox": frame_metadata[i]["bbox"],
                    "ruta_evidencia": animal_frame_paths[i],
                    "timestamp_video": frame_metadata[i]["index"] / fps,
                    "calidad": 0.95,
                    "detector_source": "YOLOv8n + Google_SpeciesNet_v4.0.2a",
                }
            )

        logger.info("Pipeline completado. Detectados: %s", len(detections))
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
        return any(token in value for token in ("blank", "vehicle", "human", "person", "no cv result"))

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
