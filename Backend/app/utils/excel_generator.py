import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelGenerator:
    def __init__(self):
        pass
    
    def generate_report(self, detections: List[Dict[str, Any]], camera_id: str, 
                       file_manager) -> str:
        """
        Generar reporte Excel con todas las detecciones
        Args:
            detections: Lista de detecciones
            camera_id: ID de la cámara
            file_manager: Instancia del gestor de archivos
        Returns:
            Ruta del archivo Excel generado
        """
        try:
            # Crear DataFrame
            df = pd.DataFrame(detections)
            
            if df.empty:
                logger.warning(f"No hay detecciones para generar reporte de cámara {camera_id}")
                # Crear DataFrame vacío con columnas esperadas
                df = pd.DataFrame(columns=[
                    'video', 'especie', 'confianza', 'fecha', 'hora', 
                    'frame', 'ruta_evidencia'
                ])
            
            # Ordenar por fecha y hora
            if not df.empty:
                df = df.sort_values(['fecha', 'hora'])
            
            # Obtener ruta de Excel
            excel_path = file_manager.get_excel_path(camera_id)
            excel_path.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre del archivo con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_file = excel_path / f"reporte_{timestamp}.xlsx"
            
            # Crear el archivo Excel con múltiples hojas
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Hoja principal con todas las detecciones
                df_main = df[['video', 'especie', 'confianza', 'fecha', 'hora', 'frame', 'ruta_evidencia']]
                df_main.to_excel(writer, sheet_name='Detecciones', index=False)
                
                # Hoja de resumen por especie
                if not df.empty:
                    species_summary = df.groupby('especie').agg({
                        'video': 'count',
                        'confianza': ['mean', 'max', 'min']
                    }).round(3)
                    species_summary.columns = ['Total_Detecciones', 'Confianza_Promedio', 'Confianza_Maxima', 'Confianza_Minima']
                    species_summary.to_excel(writer, sheet_name='Resumen_Especies')
                    
                    # Hoja de resumen por video
                    video_summary = df.groupby('video').agg({
                        'especie': 'count',
                        'confianza': 'mean'
                    }).round(3)
                    video_summary.columns = ['Total_Detecciones', 'Confianza_Promedio']
                    video_summary.to_excel(writer, sheet_name='Resumen_Videos')
            
            logger.info(f"Reporte Excel generado: {excel_file}")
            return str(excel_file)
        
        except Exception as e:
            logger.error(f"Error generando reporte Excel: {e}")
            return ""
    
    def get_summary_stats(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Obtener estadísticas resumidas de las detecciones
        Args:
            detections: Lista de detecciones
        Returns:
            Diccionario con estadísticas
        """
        if not detections:
            return {
                'videos_procesados': 0,
                'animales_detectados': 0,
                'especies_encontradas': [],
                'total_evidencias': 0
            }
        
        df = pd.DataFrame(detections)
        
        # Contar videos únicos
        videos_procesados = df['video'].nunique()
        
        # Total de animales detectados
        animales_detectados = len(detections)
        
        # Especies únicas encontradas
        especies_encontradas = df['especie'].unique().tolist()
        
        # Total de evidencias (igual al número de detecciones)
        total_evidencias = len(detections)
        
        return {
            'videos_procesados': videos_procesados,
            'animales_detectados': animales_detectados,
            'especies_encontradas': especies_encontradas,
            'total_evidencias': total_evidencias
        }