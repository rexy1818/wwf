import shutil
from pathlib import Path
from typing import List, Dict, Any
import logging
import uuid
from datetime import datetime

# CAMBIO: Importar el analizador mejorado en lugar del básico
from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer
from app.utils.json_storage import json_storage

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    def __init__(self):
        # CAMBIO: Usar el analizador mejorado con detector inteligente
        self.video_analyzer = EnhancedVideoAnalyzer()
        self.storage_dir = Path("video_analysis")
        self.storage_dir.mkdir(exist_ok=True)
        
        # Formatos de video soportados
        self.supported_formats = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        
        logger.info("🚀 VideoAnalysisService inicializado con detector mejorado y clasificador inteligente")
    
    async def upload_and_analyze_video(self, file, filename: str) -> Dict[str, Any]:
        """
        Subir y analizar un video automáticamente
        Args:
            file: Archivo de video subido
            filename: Nombre original del archivo
        Returns:
            Resultado completo del análisis
        """
        try:
            # Verificar formato
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Formato no soportado: {file_extension}")
            
            # Generar ID único para el video
            video_id = str(uuid.uuid4())[:12]
            safe_filename = self._sanitize_filename(filename)
            
            # Guardar archivo temporalmente
            temp_video_path = self.storage_dir / f"{video_id}_{safe_filename}"
            
            with open(temp_video_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"📹 Video subido: {filename} -> {temp_video_path}")
            
            # CAMBIO: Analizar video con detector mejorado y clasificador inteligente
            logger.info(f"🧠 Iniciando análisis con detector mejorado...")
            analysis_result = self.video_analyzer.analyze_video(
                str(temp_video_path), 
                str(self.storage_dir / "analysis")
            )
            
            # Log de mejoras aplicadas
            stats = analysis_result.get('estadisticas', {})
            correcciones = stats.get('correcciones_aplicadas', 0)
            if correcciones > 0:
                logger.info(f"🎯 Clasificador inteligente aplicó {correcciones} correcciones")
            
            logger.info(f"✅ Análisis completado: {stats.get('total_animales', 0)} detecciones, "
                       f"calidad promedio: {stats.get('calidad_promedio', 0):.3f}")
            
            # Guardar resultado en JSON storage
            self._save_analysis_to_storage(video_id, analysis_result)
            
            # Limpiar archivo temporal (opcional, mantener para evidencias)
            # temp_video_path.unlink()
            
            return {
                'video_id': video_id,
                'filename': filename,
                'status': 'analyzed',
                'analysis': analysis_result,
                'upload_time': datetime.now().isoformat(),
                'detector_version': 'enhanced_v2.0',
                'features': [
                    'improved_yolo_detection',
                    'smart_species_classification', 
                    'enhanced_frame_selection',
                    'contextual_validation'
                ]
            }
        
        except Exception as e:
            logger.error(f"Error analizando video {filename}: {e}")
            raise
    
    def get_analysis_result(self, video_id: str) -> Dict[str, Any]:
        """Obtener resultado de análisis por ID"""
        try:
            # Buscar en JSON storage
            all_analyses = json_storage.data.get("video_analyses", {})
            
            if video_id in all_analyses:
                return all_analyses[video_id]
            
            raise ValueError(f"Análisis no encontrado: {video_id}")
        
        except Exception as e:
            logger.error(f"Error obteniendo análisis {video_id}: {e}")
            raise
    
    def list_all_analyses(self) -> List[Dict[str, Any]]:
        """Listar todos los análisis realizados"""
        try:
            all_analyses = json_storage.data.get("video_analyses", {})
            
            analyses_list = []
            for video_id, analysis in all_analyses.items():
                summary = {
                    'video_id': video_id,
                    'video_name': analysis.get('video_name'),
                    'camara_id': analysis.get('metadata', {}).get('camara_id'),
                    'fecha_video': analysis.get('metadata', {}).get('fecha_video'),
                    'total_detecciones': analysis.get('estadisticas', {}).get('total_animales', 0),
                    'especies_encontradas': analysis.get('estadisticas', {}).get('especies_encontradas', []),
                    'procesado_en': analysis.get('procesado_en'),
                    'detector_version': analysis.get('detector_version', 'basic'),
                    'correcciones_aplicadas': analysis.get('estadisticas', {}).get('correcciones_aplicadas', 0),
                    'calidad_promedio': analysis.get('estadisticas', {}).get('calidad_promedio', 0)
                }
                analyses_list.append(summary)
            
            # Ordenar por fecha de procesamiento (más reciente primero)
            analyses_list.sort(key=lambda x: x.get('procesado_en', ''), reverse=True)
            
            return analyses_list
        
        except Exception as e:
            logger.error(f"Error listando análisis: {e}")
            raise
    
    def generate_combined_report(self, video_ids: List[str] = None) -> str:
        """Generar reporte Excel combinado"""
        try:
            all_analyses = json_storage.data.get("video_analyses", {})
            
            # Si no se especifican IDs, usar todos
            if not video_ids:
                video_ids = list(all_analyses.keys())
            
            # Filtrar análisis solicitados
            selected_analyses = []
            for video_id in video_ids:
                if video_id in all_analyses:
                    selected_analyses.append(all_analyses[video_id])
            
            if not selected_analyses:
                raise ValueError("No se encontraron análisis para generar reporte")
            
            # CAMBIO: Generar reporte Excel mejorado
            report_file = self.video_analyzer.generate_excel_report(selected_analyses)
            
            logger.info(f"📊 Reporte mejorado generado: {report_file}")
            return report_file
        
        except Exception as e:
            logger.error(f"Error generando reporte combinado: {e}")
            raise
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales del sistema"""
        try:
            all_analyses = json_storage.data.get("video_analyses", {})
            
            if not all_analyses:
                return {
                    'total_videos': 0,
                    'total_detecciones': 0,
                    'especies_unicas': [],
                    'camaras_unicas': [],
                    'videos_por_camara': {},
                    'detecciones_por_especie': {}
                }
            
            total_videos = len(all_analyses)
            total_detecciones = 0
            especies_set = set()
            camaras_set = set()
            videos_por_camara = {}
            detecciones_por_especie = {}
            
            for analysis in all_analyses.values():
                # Contar detecciones
                num_detecciones = analysis.get('estadisticas', {}).get('total_animales', 0)
                total_detecciones += num_detecciones
                
                # Recopilar especies
                especies = analysis.get('estadisticas', {}).get('especies_encontradas', [])
                especies_set.update(especies)
                
                # Contar por especie
                for especie in especies:
                    detecciones_por_especie[especie] = detecciones_por_especie.get(especie, 0) + 1
                
                # Recopilar cámaras
                camara_id = analysis.get('metadata', {}).get('camara_id')
                if camara_id:
                    camaras_set.add(camara_id)
                    videos_por_camara[camara_id] = videos_por_camara.get(camara_id, 0) + 1
            
            return {
                'total_videos': total_videos,
                'total_detecciones': total_detecciones,
                'especies_unicas': list(especies_set),
                'camaras_unicas': list(camaras_set),
                'videos_por_camara': videos_por_camara,
                'detecciones_por_especie': detecciones_por_especie,
                'ultima_actualizacion': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise
    
    def _save_analysis_to_storage(self, video_id: str, analysis_result: Dict[str, Any]) -> None:
        """Guardar análisis en JSON storage"""
        try:
            if "video_analyses" not in json_storage.data:
                json_storage.data["video_analyses"] = {}
            
            json_storage.data["video_analyses"][video_id] = analysis_result
            json_storage._save_data()
            
            logger.info(f"Análisis guardado en storage: {video_id}")
        
        except Exception as e:
            logger.error(f"Error guardando análisis en storage: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Limpiar nombre de archivo"""
        import re
        # Reemplazar caracteres problemáticos
        clean_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limitar longitud
        if len(clean_name) > 100:
            name_part = Path(clean_name).stem[:80]
            extension = Path(clean_name).suffix
            clean_name = f"{name_part}{extension}"
        
        return clean_name