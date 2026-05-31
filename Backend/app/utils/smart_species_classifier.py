import cv2
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class SmartSpeciesClassifier:
    """
    Clasificador inteligente para fauna LATAM. 
    Fusiona detecciones espaciales y detecta rasgos biológicos (Jaguar, Tapir, etc.)
    """
    def __init__(self):
        pass

    def classify_species_intelligently(self, detection: Dict[str, Any], image: np.ndarray) -> Dict[str, Any]:
        """Identificar especie por rasgos biológicos, respetando fuentes de alta confianza."""
        try:
            # Si la detección ya viene de SpeciesNet con alta confianza, no la modificamos drásticamente
            if detection.get('detector_source') == "Google_SpeciesNet_v4.0.2a" and float(detection.get('confidence', 0)) > 0.6:
                logger.info(f"Conservando predicción de SpeciesNet: {detection.get('species')}")
                return detection

            x1, y1, x2, y2 = detection['bbox']
            roi = image[y1:y2, x1:x2]
            if roi.size == 0:
                return detection

            traits = self._extract_biological_traits(roi, image)
            original_species = detection.get('especie') or detection.get('species') or 'animal_silvestre'
            species = original_species
            confidence_boost = 1.0
            
            # LÓGICA DE DETECCIÓN TAXONÓMICA
            if traits['has_rosettes'] or traits['large_spotted_cat']:
                species = 'jaguar'
                confidence_boost = 1.45
            elif traits['has_spots']:
                species = 'jaguar' if traits['is_large'] else 'ocelote'
                confidence_boost = 1.3
            elif traits['is_bulky'] and traits['dark_color']:
                species = 'tapir'
                confidence_boost = 1.5
            elif traits['long_legs'] and traits['slender_build']:
                species = 'venado'
                confidence_boost = 1.2
            elif traits['is_solid_gold'] and traits['is_large']:
                species = 'puma'
                confidence_boost = 1.3

            base_confidence = float(detection.get('confidence', 0))
            detection['especie'] = species
            detection['species'] = species
            detection['confidence'] = min(0.99, base_confidence * confidence_boost)
            detection['confianza'] = detection['confidence']
            detection['biological_traits'] = traits
            return detection
        except Exception as e:
            logger.error(f"Error en clasificacion taxonomica: {e}")
            return detection

    def _extract_biological_traits(self, roi: np.ndarray, frame: np.ndarray) -> Dict[str, Any]:
        """Extraer rasgos de textura, color y forma."""
        h, w = roi.shape[:2]
        frame_h, frame_w = frame.shape[:2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Detectar textura (manchas/rosetas) usando Canny y varianza
        edges = cv2.Canny(gray, 50, 150)
        texture_density = np.mean(edges) / 255.0

        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        aspect_ratio = w / h if h > 0 else 1
        roi_area = h * w
        frame_area = frame_h * frame_w
        frame_area_ratio = roi_area / frame_area if frame_area > 0 else 0

        return {
            'has_spots': bool(texture_density > 0.07),
            'has_rosettes': bool(texture_density > 0.12),
            'large_spotted_cat': bool(texture_density > 0.10 and frame_area_ratio > 0.05),
            'is_solid_gold': bool(10 < h_mean < 25 and s_mean > 40),
            'is_bulky': bool(aspect_ratio > 1.3 and frame_area_ratio > 0.08),
            'dark_color': bool(np.mean(gray) < 90),
            'is_large': bool(frame_area_ratio > 0.06),
            'is_very_large': bool(frame_area_ratio > 0.15),
            'long_legs': bool(aspect_ratio < 0.9),
            'slender_build': bool(aspect_ratio < 1.1),
            'frame_area_ratio': frame_area_ratio
        }

    def _bbox_iou(self, bbox_a, bbox_b):
        """Calcular solapamiento entre dos cajas."""
        if not bbox_a or not bbox_b: return 0
        ax1, ay1, ax2, ay2 = bbox_a
        bx1, by1, bx2, by2 = bbox_b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        union = float(area_a + area_b - inter)
        return inter / union if union > 0 else 0

    def validate_detection_context(self, detections: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fusionar duplicados espaciales (mismo animal, distinto nombre)."""
        ordered = sorted(detections, key=lambda d: float(d.get('timestamp_video', 0) or 0))
        selected = []
        for det in ordered:
            t = float(det.get('timestamp_video', 0) or 0)
            bbox = det.get('bbox')
            is_duplicate = False
            for i, cur in enumerate(selected):
                cur_t = float(cur.get('timestamp_video', 0) or 0)
                # Si están en el mismo segundo y se solapan físicamente (>30%)
                if abs(t - cur_t) < 1.2 and self._bbox_iou(bbox, cur.get('bbox')) > 0.3:
                    # Gana el que tenga mejor confianza o sea una especie conocida (no 'animal_silvestre')
                    new_conf = float(det.get('confidence', 0))
                    old_conf = float(cur.get('confidence', 0))
                    if new_conf > old_conf:
                        selected[i] = det
                    is_duplicate = True
                    break
            if not is_duplicate:
                selected.append(det)
        return selected
