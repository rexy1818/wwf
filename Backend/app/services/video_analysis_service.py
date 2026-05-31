import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer
from app.utils.json_storage import json_storage

logger = logging.getLogger(__name__)


class VideoAnalysisService:
    def __init__(self) -> None:
        self.video_analyzer = EnhancedVideoAnalyzer()
        self.storage_dir = Path("video_analysis")
        self.storage_dir.mkdir(exist_ok=True)
        self.supported_formats = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}
        logger.info("VideoAnalysisService inicializado con SpeciesNet oficial y OCR")

    async def upload_and_analyze_video(self, file, filename: str) -> Dict[str, Any]:
        try:
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Formato no soportado: {file_extension}")

            video_id = str(uuid.uuid4())[:12]
            safe_filename = self._sanitize_filename(filename)
            temp_video_path = self.storage_dir / f"{video_id}_{safe_filename}"

            with open(temp_video_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info("Video subido: %s -> %s", filename, temp_video_path)
            analysis_result = self.video_analyzer.analyze_video_smart(
                str(temp_video_path),
                str(self.storage_dir / "analysis"),
                video_id=video_id,
            )

            stats = analysis_result.get("estadisticas", {})
            logger.info(
                "Analisis completado: %s detecciones, calidad promedio %.3f",
                stats.get("total_animales", 0),
                stats.get("calidad_promedio", 0),
            )

            self._save_analysis_to_storage(video_id, analysis_result)
            return {
                "video_id": video_id,
                "filename": filename,
                "status": "analyzed",
                "analysis": analysis_result,
                "upload_time": datetime.now().isoformat(),
                "detector_version": "Google_SpeciesNet_v4.0.2a",
                "features": [
                    "speciesnet_official",
                    "bottom_band_ocr",
                    "per_camera_results",
                    "per_camera_excel",
                ],
            }
        except Exception as exc:
            logger.error("Error analizando video %s: %s", filename, exc)
            raise

    async def upload_and_analyze_videos(self, files: List[Any]) -> Dict[str, Any]:
        results = []
        errors = []

        for index, file in enumerate(files, start=1):
            filename = getattr(file, "filename", None) or f"video_{index}"
            try:
                results.append(await self.upload_and_analyze_video(file, filename))
            except Exception as exc:
                logger.error("Error analizando video en lote %s: %s", filename, exc)
                errors.append({"filename": filename, "error": str(exc)})

        return {
            "status": "completed_with_errors" if errors else "completed",
            "total_recibidos": len(files),
            "total_procesados": len(results),
            "total_errores": len(errors),
            "results": results,
            "errors": errors,
            "processed_at": datetime.now().isoformat(),
        }

    def get_analysis_result(self, video_id: str) -> Dict[str, Any]:
        all_analyses = json_storage.data.get("video_analyses", {})
        if video_id in all_analyses:
            return all_analyses[video_id]
        raise ValueError(f"Analisis no encontrado: {video_id}")

    def list_all_analyses(self) -> List[Dict[str, Any]]:
        all_analyses = json_storage.data.get("video_analyses", {})
        analyses_list = []
        for video_id, analysis in all_analyses.items():
            analyses_list.append(
                {
                    "video_id": video_id,
                    "video_name": analysis.get("video_name"),
                    "camara_id": analysis.get("metadata", {}).get("camara_id"),
                    "fecha_video": analysis.get("metadata", {}).get("fecha_video"),
                    "total_detecciones": analysis.get("estadisticas", {}).get("total_animales", 0),
                    "especies_encontradas": analysis.get("estadisticas", {}).get("especies_encontradas", []),
                    "procesado_en": analysis.get("procesado_en"),
                    "detector_version": analysis.get("detector_version", "Google_SpeciesNet_v4.0.2a"),
                    "calidad_promedio": analysis.get("estadisticas", {}).get("calidad_promedio", 0),
                    "excel_files": analysis.get("excel_files", {}),
                }
            )
        analyses_list.sort(key=lambda item: item.get("procesado_en", ""), reverse=True)
        return analyses_list

    def generate_combined_report(self, video_ids: List[str] = None) -> str:
        all_analyses = json_storage.data.get("video_analyses", {})
        selected_ids = video_ids or list(all_analyses.keys())
        selected_analyses = [all_analyses[video_id] for video_id in selected_ids if video_id in all_analyses]
        if not selected_analyses:
            raise ValueError("No se encontraron analisis para generar reporte")

        report_file = self.video_analyzer.generate_excel_report(selected_analyses)
        logger.info("Reporte Excel generado: %s", report_file)
        return report_file

    def get_system_statistics(self) -> Dict[str, Any]:
        all_analyses = json_storage.data.get("video_analyses", {})
        total_detections = 0
        species_set = set()
        camera_set = set()
        videos_by_camera: Dict[str, int] = {}
        detections_by_species: Dict[str, int] = {}

        for analysis in all_analyses.values():
            detections = analysis.get("detecciones", [])
            total_detections += len(detections)
            camera_id = analysis.get("metadata", {}).get("camara_id")
            if camera_id:
                camera_set.add(camera_id)
                videos_by_camera[camera_id] = videos_by_camera.get(camera_id, 0) + 1
            for detection in detections:
                species = detection.get("especie") or detection.get("species")
                if species:
                    species_set.add(species)
                    detections_by_species[species] = detections_by_species.get(species, 0) + 1

        return {
            "total_videos": len(all_analyses),
            "total_detecciones": total_detections,
            "especies_unicas": sorted(species_set),
            "camaras_unicas": sorted(camera_set),
            "videos_por_camara": videos_by_camera,
            "detecciones_por_especie": detections_by_species,
            "ultima_actualizacion": datetime.now().isoformat(),
        }

    def _save_analysis_to_storage(self, video_id: str, analysis_result: Dict[str, Any]) -> None:
        if "video_analyses" not in json_storage.data:
            json_storage.data["video_analyses"] = {}
        json_storage.data["video_analyses"][video_id] = analysis_result
        json_storage._save_data()
        logger.info("Analisis guardado en storage: %s", video_id)

    def _sanitize_filename(self, filename: str) -> str:
        import re

        clean_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
        if len(clean_name) > 100:
            name_part = Path(clean_name).stem[:80]
            clean_name = f"{name_part}{Path(clean_name).suffix}"
        return clean_name
