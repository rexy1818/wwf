import cv2
import numpy as np
import re
import os
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRExtractor:
    def __init__(self):
        self.ocr_engine = None
        self.ocr_method = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """Inicializar motor OCR con prioridad EasyOCR > Tesseract."""
        try:
            import easyocr

            os.environ.setdefault("EASYOCR_MODULE_PATH", str(Path("video_analysis") / "ocr_models"))
            Path(os.environ["EASYOCR_MODULE_PATH"]).mkdir(parents=True, exist_ok=True)
            self.ocr_engine = easyocr.Reader(["en", "es"], gpu=False)
            self.ocr_method = "easyocr"
            logger.info("OCR inicializado con EasyOCR")
        except Exception as e:
            logger.warning("No se pudo inicializar EasyOCR: %s", e)
            try:
                import pytesseract

                self.ocr_engine = pytesseract
                self.ocr_method = "tesseract"
                logger.info("OCR inicializado con Tesseract")
            except Exception as e:
                logger.warning("No se pudo inicializar OCR: %s", e)

    def extract_text_from_video(self, video_path: str, sample_frames: int = 5) -> Dict[str, Any]:
        """Extraer metadatos impresos en la banda inferior de varios frames."""
        try:
            if not self.ocr_engine:
                logger.warning("OCR no disponible")
                return {}

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_indices = self._build_ocr_frame_indices(total_frames, fps, sample_frames)
            all_extractions = []

            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
                ret, frame = cap.read()
                if ret:
                    timestamp = frame_idx / fps if fps and fps > 0 else 0
                    extraction = self.extract_text_from_frame_band(frame, timestamp)
                    if extraction:
                        all_extractions.append(extraction)

            cap.release()
            consolidated = self._consolidate_extractions(all_extractions)
            logger.info("OCR completado para %s: %s frames", video_path, len(all_extractions))
            return consolidated
        except Exception as e:
            logger.error("Error en OCR de video %s: %s", video_path, e)
            return {}

    def _build_ocr_frame_indices(self, total_frames: int, fps: float, sample_frames: int) -> np.ndarray:
        """Seleccionar frames para OCR con peso en el primer segundo."""
        if total_frames <= 0:
            return np.array([], dtype=int)

        safe_fps = fps if fps and fps > 0 else 30.0
        indices = {0, total_frames - 1}
        first_second_limit = min(total_frames - 1, int(round(safe_fps)))
        early_step = max(1, int(round(safe_fps * 0.25)))
        indices.update(range(0, first_second_limit + 1, early_step))

        remaining_slots = max(0, sample_frames - len(indices))
        if remaining_slots > 0:
            distributed = np.linspace(0, total_frames - 1, remaining_slots + 2, dtype=int)[1:-1]
            indices.update(int(i) for i in distributed)

        return np.array(sorted(i for i in indices if 0 <= i < total_frames), dtype=int)

    def extract_text_from_frame_band(self, frame: np.ndarray, timestamp: float = 0) -> Dict[str, Any]:
        """Aplicar OCR solo sobre la banda inferior del frame."""
        try:
            if not self.ocr_engine:
                return {}

            if self.ocr_method == "easyocr":
                text_data = self._extract_with_easyocr_variants(frame)
            elif self.ocr_method == "tesseract":
                text_data = self._extract_with_tesseract(self._preprocess_frame_for_ocr(frame))
            else:
                return {}

            return self._parse_extracted_text(text_data, timestamp)
        except Exception as e:
            logger.debug("Error extrayendo texto del frame en %ss: %s", timestamp, e)
            return {}

    def _crop_bottom_band(self, frame: np.ndarray, start_ratio: float = 0.78) -> np.ndarray:
        h, _ = frame.shape[:2]
        return frame[int(h * start_ratio):h, :]

    def _preprocess_frame_for_ocr(self, frame: np.ndarray) -> np.ndarray:
        """Recortar la banda inferior y mejorar contraste para OCR de respaldo."""
        try:
            bottom_band = self._crop_bottom_band(frame)
            gray = cv2.cvtColor(bottom_band, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            denoised = cv2.medianBlur(enhanced, 3)
            return cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2,
            )
        except Exception as e:
            logger.debug("Error preprocesando frame: %s", e)
            return frame

    def _extract_with_easyocr_variants(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Probar variantes suaves; las bandas Bushnell pierden texto con binarizacion fuerte."""
        variants = []
        for ratio in (0.78, 0.84, 0.70):
            band = self._crop_bottom_band(frame, ratio)
            variants.extend([
                band,
                cv2.cvtColor(band, cv2.COLOR_BGR2GRAY),
                cv2.resize(band, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC),
            ])

        candidates = []
        for variant in variants:
            text_data = self._extract_with_easyocr(variant)
            parsed = self._parse_extracted_text(text_data, 0)
            score = sum(1 for key in ("camera_id", "fecha", "hora", "temperatura") if parsed.get(key))
            candidates.append((score, len(text_data), text_data))

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2] if candidates else []

    def _extract_with_easyocr(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        try:
            results = self.ocr_engine.readtext(
                frame,
                detail=1,
                paragraph=False,
                text_threshold=0.3,
                low_text=0.2,
                width_ths=1.0,
            )
            return [(text.strip(), float(confidence)) for _, text, confidence in results if confidence > 0.12 and text.strip()]
        except Exception as e:
            logger.debug("Error con EasyOCR: %s", e)
            return []

    def _extract_with_tesseract(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        try:
            import pytesseract

            config = "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:°CF-/ _"
            text = pytesseract.image_to_string(frame, config=config)
            return [(line.strip(), 0.8) for line in text.split("\n") if line.strip()]
        except Exception as e:
            logger.debug("Error con Tesseract: %s", e)
            return []

    def _parse_extracted_text(self, text_data: List[Tuple[str, float]], timestamp: float) -> Dict[str, Any]:
        parsed = {
            "timestamp": timestamp,
            "raw_text": [text for text, _ in text_data],
            "camera_id": None,
            "fecha": None,
            "hora": None,
            "temperatura": None,
            "confidence_scores": [conf for _, conf in text_data],
        }

        full_text = " ".join(text for text, _ in text_data)
        parsed["camera_id"] = self._extract_camera_id(full_text)
        parsed["fecha"], parsed["hora"] = self._extract_datetime(full_text)
        parsed["temperatura"] = self._extract_temperature(full_text)
        return parsed

    def _extract_camera_id(self, text: str) -> Optional[str]:
        try:
            normalized_text = re.sub(r"[^A-Z0-9:_\-\s/]", " ", text.upper())
            patterns = [
                r"\bCAMERA\s+ID\s*[:#-]?\s*([A-Z0-9_-]{2,20})\b",
                r"\bCAM(?:ERA)?\s*[:#-]\s*([A-Z0-9_-]{2,20})\b",
                r"\bID\s*[:#-]?\s*([A-Z0-9_-]{2,20})\b",
                r"\bTRAP\s*[:#-]?\s*([A-Z0-9_-]{2,20})\b",
                r"\b([A-Z]{2,8}\d{1,6}[A-Z0-9_-]{0,6})\b",
                r"\b([A-Z]\d{1,6}[A-Z0-9_-]{0,6})\b",
            ]
            for pattern in patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    camera_id = self._normalize_camera_id(match.group(1).strip("_- "))
                    if self._is_plausible_camera_id(camera_id):
                        return camera_id
            return None
        except Exception as e:
            logger.debug("Error extrayendo camera ID: %s", e)
            return None

    def _normalize_camera_id(self, camera_id: str) -> str:
        camera_id = re.sub(r"[^A-Z0-9_-]", "", camera_id.upper())
        camera_id = re.sub(r"^([A-Z]{3})[ILT](\d.*)$", r"\g<1>1\2", camera_id)
        match = re.match(r"^([A-Z]{2,5})([A-Z0-9_-]+)$", camera_id)
        if not match:
            return camera_id

        prefix, suffix = match.groups()
        fixed_suffix = []
        for char in suffix:
            if char in {"I", "L", "T"}:
                fixed_suffix.append("1")
            elif char in {"O", "Q"}:
                fixed_suffix.append("0")
            elif char == "S":
                fixed_suffix.append("5")
            else:
                fixed_suffix.append(char)
        return prefix + "".join(fixed_suffix)

    def _is_plausible_camera_id(self, camera_id: str) -> bool:
        if not camera_id:
            return False
        normalized = re.sub(r"[^A-Z0-9_-]", "", camera_id.upper())
        if len(normalized) < 2 or len(normalized) > 20:
            return False
        return any(ch.isdigit() for ch in normalized)

    def _extract_datetime(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            text = re.sub(r"\s+", " ", text)
            date_patterns = [
                r"(\d{4}[-/]\d{2}[-/]\d{2})",
                r"(\d{2}[-/]\d{2}[-/]\d{4})",
                r"(\d{2}[-/]\d{2}[-/]\d{2})",
            ]

            fecha = None
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    fecha = self._normalize_date_format(match.group(1))
                    if fecha:
                        break

            time_match = re.search(r"\b(\d{2})\s*:\s*(\d{2})\s*:\s*(\d{2})\b", text)
            hora = None
            if time_match:
                hh, mm, ss = time_match.groups()
                if int(ss) > 59 and ss[0] in {"7", "1"}:
                    ss = "1" + ss[1]
                if int(hh) < 24 and int(mm) < 60 and int(ss) < 60:
                    hora = f"{hh}:{mm}:{ss}"
            return fecha, hora
        except Exception as e:
            logger.debug("Error extrayendo fecha/hora: %s", e)
            return None, None

    def _extract_temperature(self, text: str) -> Optional[float]:
        try:
            normalized = text.upper()
            normalized = normalized.replace("Ã‚Â°", "°").replace("Â°", "°")
            normalized = normalized.replace("'", "°").replace('"', "°").replace("~", "°")
            patterns = [
                (r"(-?\d+(?:\.\d+)?)\s*°?\s*C\b", "C"),
                (r"(-?\d+(?:\.\d+)?)\s*°?\s*F\b", "F"),
                (r"(-?\d+(?:\.\d+)?)\s*[A-Z<]*F\s+(-?\d+(?:\.\d+)?)\s*(?:°|C|$)", "FC_PAIR"),
                (r"TEMP(?:ERATURE)?\s*[:#-]?\s*(-?\d+(?:\.\d+)?)", "C"),
                (r"T\s*:\s*(-?\d+(?:\.\d+)?)", "C"),
            ]
            celsius_candidates = []
            fahrenheit_candidates = []
            for pattern, unit in patterns:
                for match in re.finditer(pattern, normalized):
                    if unit == "FC_PAIR":
                        value = float(match.group(2))
                        if -50 <= value <= 60:
                            celsius_candidates.append(value)
                        continue
                    value = float(match.group(1))
                    if unit == "F":
                        value = (value - 32) * 5 / 9
                        if -50 <= value <= 60:
                            fahrenheit_candidates.append(value)
                    elif -50 <= value <= 60:
                        celsius_candidates.append(value)

            if celsius_candidates:
                return round(celsius_candidates[0], 1)
            if fahrenheit_candidates:
                return round(fahrenheit_candidates[0], 1)
            return None
        except Exception as e:
            logger.debug("Error extrayendo temperatura: %s", e)
            return None

    def _normalize_date_format(self, date_str: str) -> Optional[str]:
        try:
            parts = date_str.replace("/", "-").split("-")
            if len(parts) != 3:
                return None

            if len(parts[0]) == 4:
                return date_str.replace("/", "-") if self._is_valid_date(parts[0], parts[1], parts[2]) else None

            year = parts[2]
            if len(year) == 2:
                yy = int(year)
                year = str(2000 + yy if yy <= 30 else 1900 + yy)

            first = int(parts[0])
            second = int(parts[1])
            if first > 12 and self._is_valid_date(year, parts[1], parts[0]):
                return f"{year}-{parts[1]}-{parts[0]}"
            if second > 12 and self._is_valid_date(year, parts[0], parts[1]):
                return f"{year}-{parts[0]}-{parts[1]}"
            if self._is_valid_date(year, parts[1], parts[0]):
                return f"{year}-{parts[1]}-{parts[0]}"
            if self._is_valid_date(year, parts[0], parts[1]):
                return f"{year}-{parts[0]}-{parts[1]}"
            return None
        except Exception as e:
            logger.debug("Error normalizando fecha: %s", e)
            return None

    def _is_valid_date(self, year: str, month: str, day: str) -> bool:
        try:
            datetime(int(year), int(month), int(day))
            return True
        except ValueError:
            return False

    def _consolidate_extractions(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            if not extractions:
                return {}

            best_extraction = {}
            camera_ids = [ext.get("camera_id") for ext in extractions if ext.get("camera_id")]
            best_extraction["camera_id"] = max(set(camera_ids), key=camera_ids.count) if camera_ids else None

            fechas = [ext.get("fecha") for ext in extractions if ext.get("fecha")]
            best_extraction["fecha"] = max(set(fechas), key=fechas.count) if fechas else None

            for ext in extractions:
                if ext.get("hora") and not best_extraction.get("hora"):
                    best_extraction["hora"] = ext["hora"]
                    break

            temperaturas = [ext.get("temperatura") for ext in extractions if ext.get("temperatura") is not None]
            best_extraction["temperatura"] = round(sum(temperaturas) / len(temperaturas), 1) if temperaturas else None
            best_extraction["frames_procesados"] = len(extractions)
            best_extraction["raw_extractions"] = extractions
            return best_extraction
        except Exception as e:
            logger.error("Error consolidando extracciones: %s", e)
            return extractions[0] if extractions else {}
