import cv2
import numpy as np
import re
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class OCRExtractor:
    def __init__(self):
        self.ocr_engine = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Inicializar motor OCR (prioridad: EasyOCR > Tesseract)"""
        try:
            # Intentar usar EasyOCR (más preciso para texto en imágenes)
            import easyocr
            self.ocr_engine = easyocr.Reader(['en', 'es'], gpu=False)
            self.ocr_method = 'easyocr'
            logger.info("OCR inicializado con EasyOCR")
        except ImportError:
            try:
                # Fallback a Tesseract
                import pytesseract
                self.ocr_engine = pytesseract
                self.ocr_method = 'tesseract'
                logger.info("OCR inicializado con Tesseract")
            except ImportError:
                logger.warning("No se pudo inicializar OCR. Instalar easyocr o pytesseract")
                self.ocr_method = None
    
    def extract_text_from_video(self, video_path: str, sample_frames: int = 5) -> Dict[str, Any]:
        """
        Extraer texto de varios frames del video para obtener información consistente
        Args:
            video_path: Ruta del video
            sample_frames: Número de frames a muestrear
        Returns:
            Diccionario con información extraída
        """
        try:
            if not self.ocr_engine:
                logger.warning("OCR no disponible")
                return {}
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Seleccionar frames distribuidos a lo largo del video
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            all_extractions = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    timestamp = frame_idx / fps if fps > 0 else 0
                    extraction = self._extract_text_from_frame(frame, timestamp)
                    if extraction:
                        all_extractions.append(extraction)
            
            cap.release()
            
            # Consolidar información de todos los frames
            consolidated = self._consolidate_extractions(all_extractions)
            
            logger.info(f"OCR completado para {video_path}: {len(all_extractions)} frames procesados")
            return consolidated
        
        except Exception as e:
            logger.error(f"Error en OCR de video {video_path}: {e}")
            return {}
    
    def _extract_text_from_frame(self, frame: np.ndarray, timestamp: float) -> Dict[str, Any]:
        """Extraer texto de un frame específico"""
        try:
            # Preprocesar frame para mejorar OCR
            processed_frame = self._preprocess_frame_for_ocr(frame)
            
            # Extraer texto según el motor disponible
            if self.ocr_method == 'easyocr':
                text_data = self._extract_with_easyocr(processed_frame)
            elif self.ocr_method == 'tesseract':
                text_data = self._extract_with_tesseract(processed_frame)
            else:
                return {}
            
            # Parsear información del texto extraído
            parsed_info = self._parse_extracted_text(text_data, timestamp)
            
            return parsed_info
        
        except Exception as e:
            logger.debug(f"Error extrayendo texto del frame en {timestamp}s: {e}")
            return {}
    
    def _preprocess_frame_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """Preprocesar frame para mejorar precisión del OCR"""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Aumentar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Aplicar filtro para reducir ruido
            denoised = cv2.medianBlur(enhanced, 3)
            
            # Binarización adaptativa para mejorar texto
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Enfocar áreas típicas donde aparece el texto (esquinas)
            h, w = binary.shape
            
            # Región superior (fecha/hora/cámara)
            top_region = binary[0:int(h*0.15), :]
            
            # Región inferior (información adicional)
            bottom_region = binary[int(h*0.85):h, :]
            
            # Combinar regiones de interés
            roi = np.vstack([top_region, bottom_region])
            
            return roi
        
        except Exception as e:
            logger.debug(f"Error preprocesando frame: {e}")
            return frame
    
    def _extract_with_easyocr(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Extraer texto usando EasyOCR"""
        try:
            results = self.ocr_engine.readtext(frame)
            
            # Filtrar resultados por confianza
            text_data = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Solo texto con confianza > 50%
                    text_data.append((text.strip(), confidence))
            
            return text_data
        
        except Exception as e:
            logger.debug(f"Error con EasyOCR: {e}")
            return []
    
    def _extract_with_tesseract(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Extraer texto usando Tesseract"""
        try:
            import pytesseract
            
            # Configuración para mejorar detección de texto pequeño
            config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:°C-/ '
            
            text = pytesseract.image_to_string(frame, config=config)
            
            # Tesseract no da confianza por defecto, usar 0.8 como estimación
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text_data = [(line, 0.8) for line in lines]
            
            return text_data
        
        except Exception as e:
            logger.debug(f"Error con Tesseract: {e}")
            return []
    
    def _parse_extracted_text(self, text_data: List[Tuple[str, float]], timestamp: float) -> Dict[str, Any]:
        """Parsear texto extraído para obtener información estructurada"""
        try:
            parsed = {
                'timestamp': timestamp,
                'raw_text': [text for text, conf in text_data],
                'camera_id': None,
                'fecha': None,
                'hora': None,
                'temperatura': None,
                'confidence_scores': [conf for text, conf in text_data]
            }
            
            # Combinar todo el texto para análisis
            full_text = ' '.join([text for text, conf in text_data])
            
            # Extraer ID de cámara
            parsed['camera_id'] = self._extract_camera_id(full_text)
            
            # Extraer fecha y hora
            fecha, hora = self._extract_datetime(full_text)
            parsed['fecha'] = fecha
            parsed['hora'] = hora
            
            # Extraer temperatura
            parsed['temperatura'] = self._extract_temperature(full_text)
            
            return parsed
        
        except Exception as e:
            logger.debug(f"Error parseando texto: {e}")
            return {}
    
    def _extract_camera_id(self, text: str) -> Optional[str]:
        """Extraer ID de cámara del texto"""
        try:
            # Patrones comunes para ID de cámara
            patterns = [
                r'CAM\s*(\d+)',           # CAM001, CAM 001
                r'CAMERA\s*(\w+)',        # CAMERA A1
                r'ID\s*(\w+)',            # ID 001
                r'TRAP\s*(\d+)',          # TRAP001
                r'(\w+)\s*CAM',           # SITE1 CAM
                r'C(\d+)',                # C001
                r'([A-Z]\d+)',            # A1, B2
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text.upper())
                if match:
                    return match.group(1)
            
            return None
        
        except Exception as e:
            logger.debug(f"Error extrayendo camera ID: {e}")
            return None
    
    def _extract_datetime(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extraer fecha y hora del texto"""
        try:
            # Patrones para fecha y hora
            datetime_patterns = [
                r'(\d{4}[-/]\d{2}[-/]\d{2})\s+(\d{2}:\d{2}:\d{2})',  # 2024-05-30 08:30:15
                r'(\d{2}[-/]\d{2}[-/]\d{4})\s+(\d{2}:\d{2}:\d{2})',  # 30-05-2024 08:30:15
                r'(\d{2}[-/]\d{2}[-/]\d{2})\s+(\d{2}:\d{2}:\d{2})',  # 30-05-24 08:30:15
            ]
            
            for pattern in datetime_patterns:
                match = re.search(pattern, text)
                if match:
                    fecha = match.group(1)
                    hora = match.group(2)
                    
                    # Normalizar formato de fecha
                    fecha = self._normalize_date_format(fecha)
                    
                    return fecha, hora
            
            # Buscar solo fecha
            date_patterns = [
                r'(\d{4}[-/]\d{2}[-/]\d{2})',
                r'(\d{2}[-/]\d{2}[-/]\d{4})',
                r'(\d{2}[-/]\d{2}[-/]\d{2})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    fecha = self._normalize_date_format(match.group(1))
                    
                    # Buscar hora por separado
                    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', text)
                    hora = time_match.group(1) if time_match else None
                    
                    return fecha, hora
            
            return None, None
        
        except Exception as e:
            logger.debug(f"Error extrayendo fecha/hora: {e}")
            return None, None
    
    def _extract_temperature(self, text: str) -> Optional[float]:
        """Extraer temperatura del texto"""
        try:
            # Patrones para temperatura
            temp_patterns = [
                r'(-?\d+(?:\.\d+)?)\s*°?C',     # 15°C, 15C, -5.5°C
                r'(-?\d+(?:\.\d+)?)\s*TEMP',    # 15 TEMP
                r'TEMP\s*(-?\d+(?:\.\d+)?)',    # TEMP 15
                r'T:\s*(-?\d+(?:\.\d+)?)',      # T: 15
            ]
            
            for pattern in temp_patterns:
                match = re.search(pattern, text.upper())
                if match:
                    temp_str = match.group(1)
                    try:
                        temperature = float(temp_str)
                        # Validar rango razonable (-50°C a 60°C)
                        if -50 <= temperature <= 60:
                            return temperature
                    except ValueError:
                        continue
            
            return None
        
        except Exception as e:
            logger.debug(f"Error extrayendo temperatura: {e}")
            return None
    
    def _normalize_date_format(self, date_str: str) -> str:
        """Normalizar formato de fecha a YYYY-MM-DD"""
        try:
            # Reemplazar separadores
            date_str = date_str.replace('/', '-')
            
            parts = date_str.split('-')
            if len(parts) != 3:
                return date_str
            
            # Detectar formato y convertir a YYYY-MM-DD
            if len(parts[0]) == 4:  # YYYY-MM-DD
                return date_str
            elif len(parts[2]) == 4:  # DD-MM-YYYY
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            elif len(parts[2]) == 2:  # DD-MM-YY
                year = int(parts[2])
                # Asumir 20XX para años 00-30, 19XX para 31-99
                full_year = 2000 + year if year <= 30 else 1900 + year
                return f"{full_year}-{parts[1]}-{parts[0]}"
            
            return date_str
        
        except Exception as e:
            logger.debug(f"Error normalizando fecha: {e}")
            return date_str
    
    def _consolidate_extractions(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Consolidar información de múltiples frames"""
        try:
            if not extractions:
                return {}
            
            # Encontrar la extracción más completa y confiable
            best_extraction = {}
            
            # Consolidar camera_id (el más común)
            camera_ids = [ext.get('camera_id') for ext in extractions if ext.get('camera_id')]
            best_extraction['camera_id'] = max(set(camera_ids), key=camera_ids.count) if camera_ids else None
            
            # Consolidar fecha (la más común)
            fechas = [ext.get('fecha') for ext in extractions if ext.get('fecha')]
            best_extraction['fecha'] = max(set(fechas), key=fechas.count) if fechas else None
            
            # Consolidar hora (la primera válida)
            for ext in extractions:
                if ext.get('hora') and not best_extraction.get('hora'):
                    best_extraction['hora'] = ext['hora']
                    break
            
            # Consolidar temperatura (promedio de valores válidos)
            temperaturas = [ext.get('temperatura') for ext in extractions if ext.get('temperatura') is not None]
            if temperaturas:
                best_extraction['temperatura'] = round(sum(temperaturas) / len(temperaturas), 1)
            else:
                best_extraction['temperatura'] = None
            
            # Agregar información adicional
            best_extraction['frames_procesados'] = len(extractions)
            best_extraction['raw_extractions'] = extractions
            
            return best_extraction
        
        except Exception as e:
            logger.error(f"Error consolidando extracciones: {e}")
            return extractions[0] if extractions else {}