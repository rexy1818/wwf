import os
import cv2
import numpy as np
import time
import shutil
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple
from speciesnet.multiprocessing import SpeciesNet
from speciesnet.utils import BBox

logger = logging.getLogger(__name__)

class ImprovedYOLODetector:
    """
    Detector de animales avanzado utilizando Google SpeciesNet Ensemble 
    (MegaDetector v5a + EfficientNet V2 M).
    """
    
    def __init__(self):
        # Usamos el identificador oficial de Kaggle. 
        # La librería speciesnet se encargará de buscarlo en el caché local
        # o descargarlo si es la primera vez (requiere conexión).
        self.model_path = "kaggle:google/speciesnet/pyTorch/v4.0.2a/1"
        self.temp_dir = Path("video_analysis/temp_frames")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Inicializamos SpeciesNet Ensemble
            # Usamos multiprocessing=False para evitar colisiones de hilos en FastAPI
            logger.info(f"🧬 Inicializando Google SpeciesNet Ensemble desde {self.model_path}...")
            self.model = SpeciesNet(
                model_name=self.model_path,
                components="all",
                geofence=True,
                multiprocessing=False
            )
            logger.info("✅ SpeciesNet Ensemble inicializado con éxito (MegaDetector v5a + Classifier)")
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando SpeciesNet: {e}")
            self.model = None

    def _extract_common_name(self, prediction_str: str) -> str:
        """Extrae el nombre común del string de taxonomía de SpeciesNet."""
        if not prediction_str or ';' not in prediction_str:
            return prediction_str
        parts = prediction_str.split(';')
        # El formato es: GUID;class;order;family;genus;species;common_name
        common_name = parts[-1].strip() if parts[-1] else ""
        if not common_name and len(parts) > 1:
            # Si no hay common_name, intentar con species o genus
            for i in range(len(parts)-1, 0, -1):
                if parts[i].strip():
                    return parts[i].strip()
        return common_name or "Desconocido"

    def process_video_enhanced(self, video_path: str, output_dir: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Procesar video usando SpeciesNet Ensemble.
        Retorna una lista de detecciones enriquecidas.
        """
        if not self.model:
            logger.error("SpeciesNet no está inicializado. Abortando análisis.")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"No se pudo abrir el video {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # ID de sesión para limpieza de temporales
        session_id = str(uuid.uuid4())[:8]
        video_temp_dir = self.temp_dir / session_id
        video_temp_dir.mkdir(parents=True, exist_ok=True)

        # 1. MUESTREO ESTRATÉGICO: Cada 0.5 segundos
        sample_rate = 0.5 
        sample_step = max(1, int(fps * sample_rate))
        
        frame_paths = []
        frame_indices = []
        
        logger.info(f"🎞️ Extrayendo frames para análisis (total frames: {total_frames}, paso: {sample_step})")
        
        for i in range(0, total_frames, sample_step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_path = video_temp_dir / f"frame_{i:06d}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frame_paths.append(str(frame_path))
            frame_indices.append(i)
        
        cap.release()

        if not frame_paths:
            logger.warning("No se pudieron extraer frames del video.")
            return []

        # 2. INFERENCIA CON SPECIESNET ENSEMBLE
        logger.info(f"🧠 Ejecutando SpeciesNet Ensemble sobre {len(frame_paths)} frames...")
        try:
            results = self.model.predict(filepaths=frame_paths)
        except Exception as e:
            logger.error(f"Error durante la inferencia de SpeciesNet: {e}")
            return []
        
        # 3. CONVERSIÓN DE RESULTADOS
        all_detections = []
        for i, res in enumerate(results.get("predictions", [])):
            prediction = res.get("prediction")
            score = res.get("prediction_score", 0)
            detections = res.get("detections", [])
            
            # Filtrar vacíos, humanos o vehículos (MegaDetector v5a filtra esto pero confirmamos)
            if not prediction or any(x in str(prediction).lower() for x in ["blank", "vehicle", "human"]):
                continue
                
            species_name = self._extract_common_name(str(prediction))
            
            # SpeciesNet usualmente da una predicción consolidada por imagen.
            # Convertimos el bbox del primer animal detectado para compatibilidad
            if not detections:
                continue
                
            # MDv5a bbox format: [xmin, ymin, width, height] (normalized 0-1)
            main_det = detections[0]
            xmin, ymin, bw, bh = main_det["bbox"]
            
            # Convertir a coordenadas de píxeles [x1, y1, x2, y2]
            x1 = int(xmin * width)
            y1 = int(ymin * height)
            x2 = int((xmin + bw) * width)
            y2 = int((ymin + bh) * height)
            
            all_detections.append({
                "species": species_name,
                "especie": species_name,
                "confidence": float(score),
                "confianza": float(score),
                "bbox": [x1, y1, x2, y2],
                "normalized_bbox": main_det["bbox"],
                "ruta_evidencia": res.get("filepath"),
                "timestamp_video": frame_indices[i] / fps,
                "calidad": 0.95, # Marcamos como alta calidad por ser MDv5a + EfficientNet
                "detector_source": "Google_SpeciesNet_v4.0.2a",
                "original_prediction": prediction
            })

        logger.info(f"🎯 SpeciesNet detectó {len(all_detections)} instancias de animales.")
        
        # NO limpiamos el temp_dir aquí porque EnhancedVideoAnalyzer usará las rutas
        # Pero nos aseguramos de que las rutas sean persistentes por la duración del análisis.
        return all_detections

    def _add_professional_bounding_box(self, image: np.ndarray, detection: Dict[str, Any],
                                     original_bbox: List[int], crop_offset: Tuple[int, int],
                                     metadata: Dict[str, Any] = None) -> np.ndarray:
        """
        Agrega bounding box profesional con etiqueta.
        Mantenemos la firma para compatibilidad con EnhancedVideoAnalyzer.
        """
        try:
            result_image = image.copy()
            h, w = result_image.shape[:2]

            # Ajustar coordenadas del bbox al ROI (si es que hubo crop)
            x1, y1, x2, y2 = original_bbox
            crop_x, crop_y = crop_offset

            adj_x1 = max(0, x1 - crop_x)
            adj_y1 = max(0, y1 - crop_y)
            adj_x2 = min(w, x2 - crop_x)
            adj_y2 = min(h, y2 - crop_y)

            # Obtener datos de la detección
            species = (detection.get("species") or detection.get("especie") or "ANIMAL").upper()
            confidence = detection.get("confidence") or detection.get("confianza") or 0.0

            # Colores profesionales
            bbox_color = (0, 255, 0)  # Verde brillante
            text_bg_color = (0, 200, 0)  # Verde más oscuro para fondo
            text_color = (255, 255, 255)  # Blanco para texto

            # Grosor
            thickness = 3

            # Dibujar bounding box
            cv2.rectangle(result_image, (adj_x1, adj_y1), (adj_x2, adj_y2), bbox_color, thickness)

            # Preparar etiqueta
            label = f"{species} {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            font_thickness = 2

            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)
            
            # Fondo de la etiqueta
            cv2.rectangle(result_image, (adj_x1, adj_y1 - text_h - 10), (adj_x1 + text_w, adj_y1), bbox_color, -1)
            # Texto
            cv2.putText(result_image, label, (adj_x1, adj_y1 - 5), font, font_scale, (0, 0, 0), font_thickness)

            return result_image
        except Exception as e:
            logger.error(f"Error dibujando bounding box: {e}")
            return image

    def _enhance_image_quality(self, img: np.ndarray) -> np.ndarray:
        """Mejora sutil de la imagen para reporte."""
        try:
            # Ligero sharpening
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            return cv2.filter2D(img, -1, kernel)
        except:
            return img
