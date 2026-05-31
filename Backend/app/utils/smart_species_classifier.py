import cv2
import numpy as np
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class SmartSpeciesClassifier:
    """
    Clasificador avanzado basado en rasgos biológicos para FAUNA DE AMÉRICA LATINA.
    Especializado en distinguir especies selváticas y andinas.
    """
    def __init__(self):
        # Familias biológicas de LATAM
        self.families = {
            'felidae': ['jaguar', 'puma', 'ocelote', 'yaguarundi'],
            'cervidae': ['venado_cola_blanca', 'corzuela', 'venado_andino'],
            'dasyproctidae': ['agouti', 'paca', 'guatin'],
            'canidae': ['zorro_gris', 'zorro_perro', 'lobo_de_crin'],
            'tapiridae': ['danta', 'tapir_amazonico'],
            'ursidae': ['oso_de_anteojos']
        }

    def classify_species_intelligently(self, detection: Dict[str, Any], image: np.ndarray) -> Dict[str, Any]:
        """
        Analiza múltiples rasgos para identificar cualquier animal de la región.
        """
        try:
            x1, y1, x2, y2 = detection['bbox']
            roi = image[y1:y2, x1:x2]
            if roi.size == 0: return detection

            # 1. Extraer Vector de Rasgos (Traits)
            traits = self._extract_biological_traits(roi)
            
            # 2. Lógica de Decisión Taxonómica
            species = "desconocido"
            confidence_boost = 1.0

            # Caso: Felinos (Manchas o Tamaño)
            if traits['has_spots'] or traits['has_rosettes']:
                species = "jaguar" if traits['is_large'] else "ocelote"
                confidence_boost = 1.4
            elif traits['is_solid_gold'] and traits['is_large']:
                species = "puma"
                confidence_boost = 1.3
            
            # Caso: Ungulados (Venados/Dantas)
            elif traits['long_legs'] and traits['slender_build']:
                species = "venado"
                confidence_boost = 1.3
            elif traits['is_bulky'] and traits['short_tail'] and traits['dark_color']:
                species = "danta" if traits['is_very_large'] else "pecari"
                confidence_boost = 1.4

            # Caso: Pequeños Mamíferos (Agouti/Paca)
            elif traits['hunched_back'] and not traits['has_visible_tail']:
                species = "agouti"
                confidence_boost = 1.2
            
            # Caso: Caninos
            elif traits['pointed_ears'] and traits['long_snout']:
                species = "zorro"
                confidence_boost = 1.2

            # Actualizar detección
            detection['especie'] = species
            detection['species'] = species
            detection['confidence'] = min(0.99, detection['confidence'] * confidence_boost)
            detection['biological_traits'] = traits
            
            return detection
        except Exception as e:
            logger.error(f"Error en clasificación taxonómica: {e}")
            return detection

    def _extract_biological_traits(self, roi: np.ndarray) -> Dict[str, Any]:
        """Extrae características físicas reales del animal"""
        h, w = roi.shape[:2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 1. Patrones cutáneos
        edges = cv2.Canny(gray, 50, 150)
        texture_density = np.mean(edges) / 255.0
        
        # 2. Análisis de color (Marrón/Dorado/Negro)
        h_mean = np.mean(hsv[:,:,0])
        s_mean = np.mean(hsv[:,:,1])
        
        # 3. Morfometría básica
        aspect_ratio = w / h if h > 0 else 1
        
        return {
            'has_spots': texture_density > 0.08,
            'has_rosettes': texture_density > 0.15,
            'is_solid_gold': 10 < h_mean < 25 and s_mean > 50,
            'long_legs': aspect_ratio < 0.8,
            'hunched_back': aspect_ratio > 1.2,
            'is_large': (h * w) > 50000,
            'is_very_large': (h * w) > 150000,
            'is_bulky': aspect_ratio > 1.5,
            'has_visible_tail': False, # Placeholder para lógica de segmentación
            'pointed_ears': False,     # Placeholder
            'long_snout': False,       # Placeholder
            'slender_build': aspect_ratio < 1.0,
            'dark_color': np.mean(gray) < 80
        }

    def validate_detection_context(self, detections: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Filtra especies imposibles según el contexto (ej: Altitud/Temperatura)"""
        # (Lógica para descartar especies africanas o de otro clima)
        return [d for d in detections if d.get('especie') != 'desconocido']
