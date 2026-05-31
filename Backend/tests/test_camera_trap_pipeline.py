import asyncio
import sys
import types
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

try:
    import cv2
except ModuleNotFoundError:
    cv2 = types.ModuleType("cv2")
    _IMAGE_STORE = {}

    def _imwrite(path, image, *args, **kwargs):
        _IMAGE_STORE[str(path)] = np.array(image).copy()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"stub-image")
        return True

    def _imread(path, *args, **kwargs):
        return _IMAGE_STORE.get(str(path))

    class _CLAHE:
        def apply(self, image):
            return image

    class _VideoCapture:
        def __init__(self, path):
            self.path = path

        def isOpened(self):
            return False

        def release(self):
            return None

        def get(self, prop):
            return 0

    cv2.imwrite = _imwrite
    cv2.imread = _imread
    cv2.cvtColor = lambda image, code: image.mean(axis=2).astype(np.uint8) if image.ndim == 3 else image
    cv2.createCLAHE = lambda *args, **kwargs: _CLAHE()
    cv2.medianBlur = lambda image, ksize: image
    cv2.adaptiveThreshold = lambda image, *args, **kwargs: image
    cv2.VideoCapture = _VideoCapture
    cv2.COLOR_BGR2GRAY = 0
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C = 0
    cv2.THRESH_BINARY = 0
    cv2.CAP_PROP_FPS = 0
    cv2.CAP_PROP_FRAME_COUNT = 1
    cv2.CAP_PROP_FRAME_WIDTH = 2
    cv2.CAP_PROP_FRAME_HEIGHT = 3
    sys.modules["cv2"] = cv2

from app.services.video_analysis_service import VideoAnalysisService
from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer
from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.ocr_extractor import OCRExtractor
from app.utils.smart_species_classifier import SmartSpeciesClassifier


class FakeDetector:
    def __init__(self, evidence_path):
        self.evidence_path = str(evidence_path)

    def process_video_enhanced(self, video_path, output_dir, metadata=None):
        return [
            {
                "especie": "jaguar",
                "species": "jaguar",
                "confianza": 0.82,
                "confidence": 0.82,
                "calidad": 0.9,
                "bbox": [10, 10, 80, 80],
                "frame_numero": 0,
                "timestamp_video": 0.0,
                "ruta_evidencia": self.evidence_path,
            }
        ]


class FakeClassifier:
    def classify_species_intelligently(self, detection, frame):
        detection["especie"] = "jaguar"
        detection["species"] = "jaguar"
        detection["confianza"] = detection.get("confianza", 0.82)
        return detection

    def validate_detection_context(self, detections, metadata=None):
        return detections


class FakeOCR:
    def extract_text_from_video(self, video_path):
        return {
            "camera_id": "EST12B",
            "fecha": "2025-07-28",
            "hora": "17:34:49",
            "temperatura": 29.0,
            "frames_procesados": 1,
            "raw_extractions": [],
        }

    def extract_text_from_frame_band(self, frame, timestamp=0):
        return self.extract_text_from_video("")


class CameraTrapPipelineTests(unittest.TestCase):
    def test_ocr_regex_extracts_camera_date_time_temperature(self):
        extractor = OCRExtractor.__new__(OCRExtractor)
        parsed = extractor._parse_extracted_text(
            [("Camera ID: EST12B", 0.9), ("84°F", 0.9), ("29°C", 0.9), ("07-28-2025", 0.9), ("17:34:49", 0.9)],
            0,
        )

        self.assertEqual(parsed["camera_id"], "EST12B")
        self.assertEqual(parsed["fecha"], "2025-07-28")
        self.assertEqual(parsed["hora"], "17:34:49")
        self.assertEqual(parsed["temperatura"], 29.0)

    def test_ocr_preprocess_uses_bottom_band_only(self):
        extractor = OCRExtractor.__new__(OCRExtractor)
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        processed = extractor._preprocess_frame_for_ocr(frame)
        self.assertLessEqual(processed.shape[0], 25)
        self.assertEqual(processed.shape[1], 200)

    def test_detector_keeps_separate_events(self):
        detector = ImprovedYOLODetector.__new__(ImprovedYOLODetector)
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        all_detections = [
            (frame, 0, 0.0, [{"species": "jaguar", "confidence": 0.8, "adjusted_confidence": 0.8, "bbox": [1, 1, 40, 40]}]),
            (frame, 10, 0.5, [{"species": "jaguar", "confidence": 0.7, "adjusted_confidence": 0.7, "bbox": [2, 2, 41, 41]}]),
            (frame, 80, 4.0, [{"species": "jaguar", "confidence": 0.6, "adjusted_confidence": 0.6, "bbox": [2, 2, 41, 41]}]),
        ]

        selected = detector.select_representative_detections(all_detections)
        self.assertEqual(len(selected), 2)

    def test_classifier_preserves_temporally_separate_species_detections(self):
        classifier = SmartSpeciesClassifier()
        detections = [
            {"species": "jaguar", "confidence": 0.8, "timestamp_video": 0.0},
            {"species": "jaguar", "confidence": 0.7, "timestamp_video": 4.0},
        ]
        self.assertEqual(len(classifier.validate_detection_context(detections)), 2)

    def test_analyzer_generates_result_structure_and_camera_excel(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            evidence_path = tmp_path / "evidence.jpg"
            cv2.imwrite(str(evidence_path), np.zeros((120, 160, 3), dtype=np.uint8))

            analyzer = EnhancedVideoAnalyzer.__new__(EnhancedVideoAnalyzer)
            analyzer.metadata_extractor = None
            analyzer.yolo_detector = FakeDetector(evidence_path)
            analyzer.classifier = FakeClassifier()
            analyzer.ocr_extractor = FakeOCR()
            analyzer.results_base = tmp_path / "Resultados"

            result = analyzer.analyze_video_smart(str(tmp_path / "video.mp4"), str(tmp_path / "analysis"), video_id="vid001")

            expected_image = analyzer.results_base / "EST12B" / "Jaguar" / "Jaguar_EST12B_20250728_173449.jpg"
            expected_excel = analyzer.results_base / "EST12B" / "excel_EST12B.xlsx"
            self.assertTrue(expected_image.exists())
            self.assertTrue(expected_excel.exists())
            self.assertEqual(result["detecciones"][0]["camera_id"], "EST12B")

            excel = pd.read_excel(expected_excel)
            self.assertEqual(list(excel.columns), analyzer._excel_columns())
            self.assertEqual(excel.iloc[0]["Camera ID"], "EST12B")
            self.assertEqual(excel.iloc[0]["Especie"], "Jaguar")

    def test_batch_processing_reports_success_and_errors(self):
        service = VideoAnalysisService.__new__(VideoAnalysisService)

        async def fake_upload(file, filename):
            if filename == "bad.mp4":
                raise ValueError("boom")
            return {"video_id": filename, "analysis": {"estadisticas": {"total_animales": 1}}}

        service.upload_and_analyze_video = fake_upload
        files = [SimpleNamespace(filename="ok.mp4"), SimpleNamespace(filename="bad.mp4")]
        result = asyncio.run(service.upload_and_analyze_videos(files))

        self.assertEqual(result["status"], "completed_with_errors")
        self.assertEqual(result["total_procesados"], 1)
        self.assertEqual(result["total_errores"], 1)


if __name__ == "__main__":
    unittest.main()
