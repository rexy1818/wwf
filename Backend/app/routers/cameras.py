from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging

from app.utils.json_storage import json_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """
    Obtener estadísticas generales del sistema
    
    Retorna información sobre:
    - Total de videos analizados
    - Total de detecciones de animales
    - Cámaras identificadas automáticamente
    - Especies encontradas
    - Fechas de creación y última actualización
    """
    try:
        # Obtener estadísticas de análisis de videos
        video_analyses = json_storage.data.get("video_analyses", {})
        
        if not video_analyses:
            return {
                "total_videos": 0,
                "total_detecciones": 0,
                "camaras_identificadas": [],
                "especies_encontradas": [],
                "videos_por_camara": {},
                "detecciones_por_especie": {},
                "temperatura_promedio": None,
                "ultima_actualizacion": json_storage.data.get("last_updated")
            }
        
        # Calcular estadísticas
        total_videos = len(video_analyses)
        total_detecciones = 0
        camaras_set = set()
        especies_set = set()
        videos_por_camara = {}
        detecciones_por_especie = {}
        temperaturas = []
        
        for analysis in video_analyses.values():
            # Contar detecciones
            num_detecciones = analysis.get('estadisticas', {}).get('total_animales', 0)
            total_detecciones += num_detecciones
            
            # Recopilar especies
            especies = analysis.get('estadisticas', {}).get('especies_encontradas', [])
            especies_set.update(especies)
            
            # Contar por especie
            especies_count = analysis.get('estadisticas', {}).get('detecciones_por_especie', {})
            for especie, count in especies_count.items():
                detecciones_por_especie[especie] = detecciones_por_especie.get(especie, 0) + count
            
            # Recopilar cámaras
            camara_id = analysis.get('metadata', {}).get('camara_id')
            if camara_id:
                camaras_set.add(camara_id)
                videos_por_camara[camara_id] = videos_por_camara.get(camara_id, 0) + 1
            
            # Recopilar temperaturas
            temp = analysis.get('metadata', {}).get('temperatura')
            if temp is not None:
                temperaturas.append(temp)
        
        # Calcular temperatura promedio
        temp_promedio = round(sum(temperaturas) / len(temperaturas), 1) if temperaturas else None
        
        stats = {
            "total_videos": total_videos,
            "total_detecciones": total_detecciones,
            "camaras_identificadas": sorted(list(camaras_set)),
            "especies_encontradas": sorted(list(especies_set)),
            "videos_por_camara": videos_por_camara,
            "detecciones_por_especie": detecciones_por_especie,
            "temperatura_promedio": temp_promedio,
            "rango_temperaturas": {
                "minima": min(temperaturas) if temperaturas else None,
                "maxima": max(temperaturas) if temperaturas else None
            },
            "ultima_actualizacion": json_storage.data.get("last_updated")
        }
        
        logger.info("Estadísticas del sistema obtenidas")
        return stats
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.get("/cameras", response_model=List[Dict[str, Any]])
async def list_identified_cameras():
    """
    Listar todas las cámaras identificadas automáticamente de los videos
    
    Retorna información de las cámaras extraída automáticamente del análisis de videos:
    - ID de cámara (extraído del texto superpuesto)
    - Número de videos por cámara
    - Fechas de videos procesados
    - Total de detecciones por cámara
    - Especies encontradas por cámara
    """
    try:
        video_analyses = json_storage.data.get("video_analyses", {})
        cameras_info = {}
        
        # Agrupar información por cámara
        for video_id, analysis in video_analyses.items():
            camara_id = analysis.get('metadata', {}).get('camara_id')
            
            if not camara_id:
                continue
            
            if camara_id not in cameras_info:
                cameras_info[camara_id] = {
                    'camara_id': camara_id,
                    'videos_procesados': 0,
                    'total_detecciones': 0,
                    'especies_encontradas': set(),
                    'fechas_videos': set(),
                    'temperaturas': [],
                    'primer_video': None,
                    'ultimo_video': None
                }
            
            cam_info = cameras_info[camara_id]
            
            # Actualizar estadísticas
            cam_info['videos_procesados'] += 1
            cam_info['total_detecciones'] += analysis.get('estadisticas', {}).get('total_animales', 0)
            
            # Especies
            especies = analysis.get('estadisticas', {}).get('especies_encontradas', [])
            cam_info['especies_encontradas'].update(especies)
            
            # Fechas
            fecha_video = analysis.get('metadata', {}).get('fecha_video')
            if fecha_video:
                cam_info['fechas_videos'].add(fecha_video)
            
            # Temperaturas
            temp = analysis.get('metadata', {}).get('temperatura')
            if temp is not None:
                cam_info['temperaturas'].append(temp)
            
            # Fechas de procesamiento
            procesado_en = analysis.get('procesado_en')
            if procesado_en:
                if not cam_info['primer_video'] or procesado_en < cam_info['primer_video']:
                    cam_info['primer_video'] = procesado_en
                if not cam_info['ultimo_video'] or procesado_en > cam_info['ultimo_video']:
                    cam_info['ultimo_video'] = procesado_en
        
        # Convertir a lista y formatear
        cameras_list = []
        for cam_info in cameras_info.values():
            # Calcular temperatura promedio
            temp_promedio = None
            if cam_info['temperaturas']:
                temp_promedio = round(sum(cam_info['temperaturas']) / len(cam_info['temperaturas']), 1)
            
            camera_summary = {
                'camara_id': cam_info['camara_id'],
                'videos_procesados': cam_info['videos_procesados'],
                'total_detecciones': cam_info['total_detecciones'],
                'especies_encontradas': sorted(list(cam_info['especies_encontradas'])),
                'fechas_videos': sorted(list(cam_info['fechas_videos'])),
                'temperatura_promedio': temp_promedio,
                'rango_temperaturas': {
                    'minima': min(cam_info['temperaturas']) if cam_info['temperaturas'] else None,
                    'maxima': max(cam_info['temperaturas']) if cam_info['temperaturas'] else None
                },
                'primer_procesamiento': cam_info['primer_video'],
                'ultimo_procesamiento': cam_info['ultimo_video']
            }
            cameras_list.append(camera_summary)
        
        # Ordenar por ID de cámara
        cameras_list.sort(key=lambda x: x['camara_id'])
        
        logger.info(f"Listadas {len(cameras_list)} cámaras identificadas automáticamente")
        return cameras_list
    
    except Exception as e:
        logger.error(f"Error listando cámaras identificadas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando cámaras: {str(e)}"
        )

@router.get("/export", response_model=Dict[str, str])
async def export_all_data():
    """
    Exportar todos los datos del sistema a un archivo JSON
    
    Genera un archivo con toda la información de análisis de videos y detecciones.
    """
    try:
        from datetime import datetime
        export_filename = f"fauna_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_storage.export_data(export_filename)
        
        return {
            "message": "Datos exportados exitosamente",
            "filename": export_filename,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error exportando datos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exportando datos: {str(e)}"
        )