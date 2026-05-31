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
                     evidence_path: Path, evidence_name: str, 
                     metadata: Dict[str, Any] = None) -> str:
        """
        Guardar evidencia de detección con información superpuesta
        Args:
            frame: Frame original
            detection: Información de la detección
            evidence_path: Ruta donde guardar la evidencia
            evidence_name: Nombre del archivo de evidencia
            metadata: Metadatos adicionales del video
        Returns:
            Ruta completa del archivo guardado
        """
        try:
            # Crear directorio si no existe
            evidence_path.mkdir(parents=True, exist_ok=True)
            
            # Extraer región de interés (ROI) con margen
            x1, y1, x2, y2 = detection['bbox']
            h, w = frame.shape[:2]
            
            # Añadir margen del 30% para mejor contexto
            margin_x = int((x2 - x1) * 0.3)
            margin_y = int((y2 - y1) * 0.3)
            
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(w, x2 + margin_x)
            y2 = min(h, y2 + margin_y)
            
            # Extraer ROI
            roi = frame[y1:y2, x1:x2].copy()
            
            # Agregar información superpuesta en la imagen
            roi_with_info = self._add_info_overlay(roi, detection, metadata)
            
            # Guardar imagen con alta calidad
            file_path = evidence_path / evidence_name
            
            # Usar calidad alta para JPEG
            cv2.imwrite(str(file_path), roi_with_info, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # También guardar versión sin overlay (imagen limpia)
            clean_name = evidence_name.replace('.jpg', '_clean.jpg')
            clean_path = evidence_path / clean_name
            cv2.imwrite(str(clean_path), roi, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.info(f"Evidencia guardada: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error guardando evidencia: {e}")
            return ""
    
    def _add_info_overlay(self, image: np.ndarray, detection: Dict[str, Any], 
                         metadata: Dict[str, Any] = None) -> np.ndarray:
        """
        Agregar información superpuesta a la imagen de evidencia
        Args:
            image: Imagen del animal
            detection: Información de la detección
            metadata: Metadatos del video
        Returns:
            Imagen con información superpuesta
        """
        try:
            # Crear copia para no modificar original
            overlay_image = image.copy()
            h, w = overlay_image.shape[:2]
            
            # Configuración de texto
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = min(w, h) / 400  # Escalar según tamaño de imagen
            thickness = max(1, int(font_scale * 2))
            
            # Colores
            bg_color = (0, 0, 0)  # Negro para fondo
            text_color = (255, 255, 255)  # Blanco para texto
            box_color = (0, 255, 0)  # Verde para bounding box
            
            # Información a mostrar
            info_lines = []
            
            # Especie y confianza
            species = detection.get('species', 'Unknown')
            confidence = detection.get('confidence', 0)
            info_lines.append(f"{species.upper()} ({confidence:.1%})")
            
            # Información del video si está disponible
            if metadata:
                if metadata.get('camara_id'):
                    info_lines.append(f"CAM: {metadata['camara_id']}")
                
                if metadata.get('fecha_video') and metadata.get('hora_video'):
                    info_lines.append(f"{metadata['fecha_video']} {metadata['hora_video']}")
                
                if metadata.get('temperatura') is not None:
                    info_lines.append(f"TEMP: {metadata['temperatura']}°C")
            
            # Timestamp de detección
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_lines.append(f"Detected: {timestamp}")
            
            # Dibujar bounding box original en la ROI
            bbox = detection.get('bbox', [])
            if len(bbox) == 4:
                # Ajustar coordenadas al ROI
                roi_x1, roi_y1 = 30, 30  # Margen aproximado
                roi_x2 = roi_x1 + (bbox[2] - bbox[0])
                roi_y2 = roi_y1 + (bbox[3] - bbox[1])
                
                cv2.rectangle(overlay_image, (roi_x1, roi_y1), (roi_x2, roi_y2), box_color, thickness)
            
            # Dibujar fondo para texto
            text_height = int(30 * font_scale)
            total_text_height = len(info_lines) * text_height + 10
            
            # Fondo semi-transparente
            overlay = overlay_image.copy()
            cv2.rectangle(overlay, (5, 5), (w-5, total_text_height + 10), bg_color, -1)
            cv2.addWeighted(overlay_image, 0.7, overlay, 0.3, 0, overlay_image)
            
            # Dibujar texto
            y_offset = text_height
            for line in info_lines:
                cv2.putText(overlay_image, line, (10, y_offset), font, font_scale, text_color, thickness)
                y_offset += text_height
            
            return overlay_image
        
        except Exception as e:
            logger.error(f"Error agregando overlay: {e}")
            return image
    
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
        
        # Extraer metadatos del video
        from app.utils.video_metadata import VideoMetadataExtractor
        metadata_extractor = VideoMetadataExtractor()
        video_metadata = metadata_extractor.extract_metadata(video_path)
        
        # Obtener fecha y hora del video
        fecha_video, hora_video, datetime_obj = metadata_extractor.get_video_datetime(video_metadata)
        
        # Formatear coordenadas GPS si están disponibles
        gps_coords = metadata_extractor.format_gps_coordinates(video_metadata.get('gps_coordinates'))
        
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
                evidence_name = f"{species}_{video_name}_frame_{frame_number}_{datetime_obj.strftime('%Y%m%d_%H%M%S')}.jpg"
                
                # Guardar evidencia con metadatos
                evidence_file = self.save_evidence(frame, detection, species_path, evidence_name, {
                    'camara_id': metadata.get('camara_id'),
                    'fecha_video': metadata.get('fecha_video'),
                    'hora_video': metadata.get('hora_video'),
                    'temperatura': metadata.get('temperatura')
                })
                
                # Crear registro de detección con metadatos del video
                detection_record = {
                    'video': video_name,
                    'especie': species,
                    'confianza': round(confidence, 3),
                    'fecha_video': fecha_video,
                    'hora_video': hora_video,
                    'ubicacion_gps': gps_coords,
                    'frame': frame_number,
                    'timestamp': round(timestamp, 2),
                    'ruta_evidencia': evidence_file,
                    'bbox': detection['bbox'],
                    'timestamp_video': datetime_obj.isoformat() if datetime_obj else None,
                    'duracion_video': video_metadata.get('duration', 0),
                    'resolucion_video': f"{video_metadata.get('width', 0)}x{video_metadata.get('height', 0)}",
                    'camara_marca': video_metadata.get('camera_make'),
                    'camara_modelo': video_metadata.get('camera_model')
                }
                
                all_detections.append(detection_record)
                logger.info(f"Detectado: {species} (confianza: {confidence:.3f}) en frame {frame_number} - {fecha_video} {hora_video}")
        
        logger.info(f"Video procesado: {len(all_detections)} detecciones en {video_name}")
        return all_detections