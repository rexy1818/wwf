import cv2
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SmartSpeciesClassifier:
    """
    Clasificador ligero para fauna LATAM. Devuelve nombres de especie, no categorias genericas.
    """
    def __init__(self):
        self.families = {
            'felidae': ['jaguar', 'puma', 'ocelote', 'yaguarundi'],
            'cervidae': ['venado_cola_blanca', 'corzuela', 'venado_andino'],
            'dasyproctidae': ['agouti', 'paca', 'guatin'],
            'canidae': ['zorro_gris', 'zorro_perro', 'lobo_de_crin'],
            'tapiridae': ['danta', 'tapir_amazonico'],
            'ursidae': ['oso_de_anteojos'],
        }

    def classify_species_intelligently(self, detection: Dict[str, Any], image: np.ndarray) -> Dict[str, Any]:
        """
        Identificar una especie probable y escribirla en `especie` y `species`.
        """
        try:
            x1, y1, x2, y2 = detection['bbox']
            roi = image[y1:y2, x1:x2]
            if roi.size == 0:
                return detection

            traits = self._extract_biological_traits(roi, image)
            original_species = detection.get('especie') or detection.get('species') or 'animal_silvestre'
            species = original_species
            confidence_boost = 1.0
            detection['original_species'] = original_species

            if traits['has_rosettes'] or traits['large_spotted_cat']:
                species = 'jaguar'
                confidence_boost = 1.45
            elif traits['has_spots']:
                species = 'jaguar' if traits['is_large'] or traits['frame_area_ratio'] >= 0.06 else 'ocelote'
                confidence_boost = 1.4
            elif traits['is_solid_gold'] and traits['is_large']:
                species = 'puma'
                confidence_boost = 1.3
            elif traits['long_legs'] and traits['slender_build']:
                species = 'venado'
                confidence_boost = 1.3
            elif traits['is_bulky'] and traits['short_tail'] and traits['dark_color']:
                species = 'tapir' if traits['is_very_large'] else 'otros'
                confidence_boost = 1.4
            elif traits['hunched_back'] and not traits['has_visible_tail']:
                species = 'otros'
                confidence_boost = 1.2
            elif traits['pointed_ears'] and traits['long_snout']:
                species = 'otros'
                confidence_boost = 1.2

            base_confidence = detection.get('confidence', detection.get('confianza', 0)) or 0
            detection['especie'] = species
            detection['species'] = species
            detection['confidence'] = min(0.99, float(base_confidence) * confidence_boost)
            detection['confianza'] = detection['confidence']
            detection['correction_applied'] = species != original_species
            detection['biological_traits'] = traits
            return detection
        except Exception as e:
            logger.error(f"Error en clasificacion taxonomica: {e}")
            return detection

    def _extract_biological_traits(self, roi: np.ndarray, frame: np.ndarray) -> Dict[str, Any]:
        """Extraer rasgos basicos de color, textura y tamano."""
        h, w = roi.shape[:2]
        frame_h, frame_w = frame.shape[:2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        edges = cv2.Canny(gray, 50, 150)
        texture_density = np.mean(edges) / 255.0

        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        aspect_ratio = w / h if h > 0 else 1
        roi_area = h * w
        frame_area = frame_h * frame_w if frame_h and frame_w else roi_area
        frame_area_ratio = roi_area / frame_area if frame_area else 0

        return {
            'has_spots': bool(texture_density > 0.08),
            'has_rosettes': bool(texture_density > 0.15),
            'large_spotted_cat': bool(texture_density > 0.10 and (roi_area > 30000 or frame_area_ratio >= 0.06)),
            'is_solid_gold': bool(10 < h_mean < 25 and s_mean > 50),
            'long_legs': bool(aspect_ratio < 0.8),
            'hunched_back': bool(aspect_ratio > 1.2),
            'is_large': bool(roi_area > 30000 or frame_area_ratio >= 0.06),
            'is_very_large': bool(roi_area > 150000 or frame_area_ratio >= 0.16),
            'frame_area_ratio': round(float(frame_area_ratio), 4),
            'is_bulky': bool(aspect_ratio > 1.5),
            'has_visible_tail': False,
            'pointed_ears': False,
            'long_snout': False,
            'slender_build': bool(aspect_ratio < 1.0),
            'short_tail': True,
            'dark_color': bool(np.mean(gray) < 80),
        }

    def validate_detection_context(self, detections: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Reducir duplicados inmediatos sin colapsar todos los eventos de una especie."""
        ordered = sorted(detections, key=lambda det: float(det.get('timestamp_video', det.get('timestamp', 0)) or 0))
        selected = []
        for detection in ordered:
            species = detection.get('especie') or detection.get('species') or 'animal_silvestre'
            timestamp = float(detection.get('timestamp_video', detection.get('timestamp', 0)) or 0)
            duplicate_index = None
            for index, current in enumerate(selected):
                current_species = current.get('especie') or current.get('species') or 'animal_silvestre'
                current_timestamp = float(current.get('timestamp_video', current.get('timestamp', 0)) or 0)
                if species == current_species and abs(timestamp - current_timestamp) <= 1.0:
                    duplicate_index = index
                    break

            if duplicate_index is None:
                selected.append(detection)
                continue

            new_score = float(detection.get('confidence', detection.get('confianza', 0)) or 0)
            old_score = float(selected[duplicate_index].get('confidence', selected[duplicate_index].get('confianza', 0)) or 0)
            if new_score > old_score:
                selected[duplicate_index] = detection
        return selected
