import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Tuple, Any
import logging
from datetime import datetime
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YOLODetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Inicializar detector YOLO
        Args:
            model_path: Ruta al modelo YOLO (se descarga automáticamente si no existe)
        """
        try:
            self.model = YOLO(model_path)
            logger.info(f"Modelo YOLO cargado: {model_path}")
        except Exception as e:
            logger.error(f"Error cargando modelo YOLO: {e}")
            raise
        
        # Clases de animales del modelo COCO (índices de animales)
        self.animal_classes = {
            15: 'bird',      # pájaro
            16: 'cat',       # gato
            17: 'dog',       # perro
            18: 'horse',     # caballo
            19: 'sheep',     # oveja
            20: 'cow',       # vaca
            21: 'elephant',  # elefante
            22: 'bear',      # oso
            23: 'zebra',     # cebra
            24: 'giraffe'    # jirafa
        }
        
        # Mapeo a especies locales (personalizable)
        self.species_mapping = {
            'bird': 'ave',
            'cat': 'felino',
            'dog': 'canino',
            'horse': 'caballo',
            'sheep': 'oveja',
            'cow': 'bovino',
            'elephant': 'elefante',
            'bear': 'oso',
            'zebra': 'cebra',
            'giraffe': 'jirafa'
        }
    
    def extract_frames(self, video_path: str, interval_seconds: int = 5) -> List[Tuple[np.ndarray, int, float]]:
        """
        Extraer frames de un video cada N segundos
        Args:
            video_path: Ruta del video
            interval_seconds: Intervalo en segundos entre frames
        Returns:
            Lista de tuplas (frame, frame_number, timestamp)
        """
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"No se pudo abrir el video: {video_path}")
            return frames
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * interval_seconds)
        
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frames.append((frame, extracted_count, timestamp))
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        logger.info(f"Extraídos {len(frames)} frames de {video_path}")
        return frames
    
    def detect_animals(self, frame: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Detectar animales en un frame
        Args:
            frame: Frame de imagen
            confidence_threshold: Umbral de confianza mínimo
        Returns:
            Lista de detecciones con información de cada animal detectado
        """
        detections = []
        
        try:
            results = self.model(frame, verbose=False)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener clase y confianza
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Verificar si es un animal y supera el umbral de confianza
                        if class_id in self.animal_classes and confidence >= confidence_threshold:
                            # Obtener coordenadas del bounding box
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Mapear a especie local
                            original_species = self.animal_classes[class_id]
                            local_species = self.species_mapping.get(original_species, original_species)
                            
                            detection = {
                                'species': local_species,
                                'confidence': confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'class_id': class_id,
                                'original_species': original_species
                            }
                            detections.append(detection)
        
        except Exception as e:
            logger.error(f"Error en detección: {e}")
        
        return detections
    
    def save_evidence(self, frame: np.ndarray, detection: Dict[str, Any], 
                     evidence_path: Path, evidence_name: str) -> str:
        """
        Guardar evidencia de detección
        Args:
            frame: Frame original
            detection: Información de la detección
            evidence_path: Ruta donde guardar la evidencia
            evidence_name: Nombre del archivo de evidencia
        Returns:
            Ruta completa del archivo guardado
        """
        try:
            # Crear directorio si no existe
            evidence_path.mkdir(parents=True, exist_ok=True)
            
            # Extraer región de interés (ROI) con margen
            x1, y1, x2, y2 = detection['bbox']
            h, w = frame.shape[:2]
            
            # Añadir margen del 20%
            margin_x = int((x2 - x1) * 0.2)
            margin_y = int((y2 - y1) * 0.2)
            
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(w, x2 + margin_x)
            y2 = min(h, y2 + margin_y)
            
            # Extraer ROI
            roi = frame[y1:y2, x1:x2]
            
            # Guardar imagen
            file_path = evidence_path / evidence_name
            cv2.imwrite(str(file_path), roi)
            
            logger.info(f"Evidencia guardada: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error guardando evidencia: {e}")
            return ""
    
    def process_video(self, video_path: str, camera_id: str, file_manager, 
                     interval_seconds: int = 5, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Procesar un video completo y detectar animales
        Args:
            video_path: Ruta del video
            camera_id: ID de la cámara
            file_manager: Instancia del gestor de archivos
            interval_seconds: Intervalo entre frames
            confidence_threshold: Umbral de confianza
        Returns:
            Lista de todas las detecciones del video
        """
        all_detections = []
        video_name = Path(video_path).stem
        
        logger.info(f"Procesando video: {video_name}")
        
        # Extraer frames
        frames = self.extract_frames(video_path, interval_seconds)
        
        if not frames:
            logger.warning(f"No se pudieron extraer frames de {video_path}")
            return all_detections
        
        # Procesar cada frame
        for frame, frame_number, timestamp in frames:
            detections = self.detect_animals(frame, confidence_threshold)
            
            for detection in detections:
                species = detection['species']
                confidence = detection['confidence']
                
                # Crear directorio para la especie
                species_path = file_manager.create_species_directory(camera_id, species)
                
                # Generar nombre único para la evidencia
                now = datetime.now()
                evidence_name = f"{species}_{video_name}_frame_{frame_number}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                
                # Guardar evidencia
                evidence_file = self.save_evidence(frame, detection, species_path, evidence_name)
                
                # Crear registro de detección
                detection_record = {
                    'video': video_name,
                    'especie': species,
                    'confianza': round(confidence, 3),
                    'fecha': now.strftime('%Y-%m-%d'),
                    'hora': now.strftime('%H:%M:%S'),
                    'frame': frame_number,
                    'timestamp': round(timestamp, 2),
                    'ruta_evidencia': evidence_file,
                    'bbox': detection['bbox']
                }
                
                all_detections.append(detection_record)
                logger.info(f"Detectado: {species} (confianza: {confidence:.3f}) en frame {frame_number}")
        
        logger.info(f"Video procesado: {len(all_detections)} detecciones en {video_name}")
        return all_detections