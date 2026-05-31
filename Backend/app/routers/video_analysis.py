from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from app.services.video_analysis_service import VideoAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["video-analysis"])

# Instancia del servicio
video_analysis_service = VideoAnalysisService()

@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_and_analyze_video(
    file: UploadFile = File(..., description="Video a analizar")
):
    """
    Subir y analizar un video automáticamente con detector mejorado
    
    **🚀 NUEVO: Detector Mejorado v2.0**
    
    **Proceso automático mejorado:**
    1. Sube el video
    2. Extrae metadatos (ID cámara, fecha, hora, GPS, temperatura si disponible)
    3. **NUEVO**: Detecta animales con YOLO mejorado (más frames, mejor calidad)
    4. **NUEVO**: Aplica clasificador inteligente de especies (corrige errores)
    5. **NUEVO**: Considera contexto geográfico (fauna de América Latina)
    6. Genera evidencias fotográficas de alta calidad
    7. Crea registro completo en JSON
    
    **🧠 Clasificador Inteligente:**
    - Corrige detecciones erróneas (ej: cebra → felino)
    - Analiza patrones visuales (rayas, manchas, colores)
    - Considera probabilidad regional de especies
    - Selecciona los mejores frames por calidad
    
    **Formatos soportados:** mp4, avi, mov, mkv, wmv, flv, webm, m4v
    
    **Información extraída:**
    - ID de cámara (del nombre del archivo o metadatos)
    - Fecha y hora del video
    - Coordenadas GPS (si están disponibles)
    - Temperatura (si está en metadatos)
    - Especies de animales detectadas con alta precisión
    - Nivel de confianza ajustado por contexto
    - Calidad de detección por frame
    """
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionó ningún archivo"
            )
        
        result = await video_analysis_service.upload_and_analyze_video(file, file.filename)
        
        # Log de mejoras aplicadas
        analysis = result.get('analysis', {})
        stats = analysis.get('estadisticas', {})
        correcciones = stats.get('correcciones_aplicadas', 0)
        
        if correcciones > 0:
            logger.info(f"🎯 Clasificador inteligente aplicó {correcciones} correcciones en {file.filename}")
        
        logger.info(f"✅ Video analizado exitosamente con detector mejorado: {file.filename}")
        return result
    
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analizando video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analizando video: {str(e)}"
        )

@router.get("/results/{video_id}", response_model=Dict[str, Any])
async def get_analysis_result(video_id: str):
    """
    Obtener resultado completo de análisis por ID de video
    
    - **video_id**: ID único del video analizado
    
    Retorna toda la información del análisis incluyendo:
    - Metadatos del video
    - Lista de detecciones de animales
    - Estadísticas del análisis
    - Rutas de evidencias fotográficas
    """
    try:
        result = video_analysis_service.get_analysis_result(video_id)
        logger.info(f"Resultado obtenido para video: {video_id}")
        return result
    
    except ValueError as e:
        logger.warning(f"Video no encontrado: {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo resultado {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resultado: {str(e)}"
        )

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_all_analyses():
    """
    Listar todos los análisis de videos realizados
    
    Retorna resumen de todos los videos analizados incluyendo:
    - ID del video
    - ID de cámara extraído
    - Fecha y hora del video
    - Total de detecciones
    - Especies encontradas
    - Fecha de procesamiento
    """
    try:
        analyses = video_analysis_service.list_all_analyses()
        logger.info(f"Listados {len(analyses)} análisis")
        return analyses
    
    except Exception as e:
        logger.error(f"Error listando análisis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando análisis: {str(e)}"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_statistics():
    """
    Obtener estadísticas generales del sistema
    
    Retorna:
    - Total de videos analizados
    - Total de detecciones de animales
    - Especies únicas encontradas
    - Cámaras únicas identificadas
    - Distribución de videos por cámara
    - Distribución de detecciones por especie
    """
    try:
        stats = video_analysis_service.get_system_statistics()
        logger.info("Estadísticas del sistema obtenidas")
        return stats
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.post("/report", response_model=Dict[str, str])
async def generate_excel_report(
    video_ids: Optional[List[str]] = Query(None, description="IDs de videos específicos (opcional)")
):
    """
    Generar reporte Excel mejorado con análisis de videos
    
    **🚀 NUEVO: Reporte Mejorado v2.0**
    
    - **video_ids**: Lista opcional de IDs de videos específicos
    
    Si no se especifican video_ids, genera reporte con todos los análisis.
    
    **El reporte Excel mejorado incluye:**
    - Hoja "Resumen_Videos_Enhanced": Información general por video + métricas de calidad
    - Hoja "Detecciones_Enhanced": Todas las detecciones con información de correcciones
    - Hoja "Estadisticas_Especies_Enhanced": Resumen por especie + correcciones aplicadas
    - Hoja "Correcciones_Inteligentes": Detalle de correcciones del clasificador
    - Hoja "Evidencias_Enhanced": Lista de imágenes con calidad de frame
    
    **Nuevas columnas incluidas:**
    - Confianza original vs corregida
    - Correcciones aplicadas por el clasificador inteligente
    - Calidad de frame (nitidez, contraste, posición)
    - Multiplicador regional aplicado
    - Versión del detector utilizado
    """
    try:
        report_file = video_analysis_service.generate_combined_report(video_ids)
        
        return {
            "message": "Reporte Excel generado exitosamente",
            "filename": report_file,
            "videos_incluidos": len(video_ids) if video_ids else "todos"
        }
    
    except ValueError as e:
        logger.warning(f"Error generando reporte: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte: {str(e)}"
        )

@router.get("/evidence/{video_id}/{species}/{filename}")
async def get_evidence_image(video_id: str, species: str, filename: str):
    """
    Obtener imagen de evidencia específica
    
    - **video_id**: ID del video analizado
    - **species**: Especie del animal (ave, felino, etc.)
    - **filename**: Nombre del archivo de imagen
    
    Retorna la imagen de evidencia del animal detectado.
    """
    try:
        # Construir ruta de la imagen
        evidence_path = Path("video_analysis") / "analysis" / f"*{video_id}*" / "evidencias" / species / filename
        
        # Buscar el archivo (puede haber variaciones en el nombre del directorio)
        import glob
        matching_files = glob.glob(str(evidence_path))
        
        if not matching_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Imagen de evidencia no encontrada: {filename}"
            )
        
        image_path = Path(matching_files[0])
        
        if not image_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo de imagen no existe: {filename}"
            )
        
        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sirviendo imagen {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo imagen: {str(e)}"
        )

@router.get("/evidence/{video_id}/list", response_model=Dict[str, List[str]])
async def list_evidence_images(video_id: str):
    """
    Listar todas las imágenes de evidencia de un video
    
    - **video_id**: ID del video analizado
    
    Retorna diccionario con especies como claves y listas de nombres de archivos como valores.
    """
    try:
        # Buscar directorio de evidencias del video
        analysis_dir = Path("video_analysis") / "analysis"
        
        evidence_dict = {}
        
        # Buscar directorios que contengan el video_id
        for video_dir in analysis_dir.glob(f"*{video_id}*"):
            evidencias_dir = video_dir / "evidencias"
            
            if evidencias_dir.exists():
                # Listar por especie
                for species_dir in evidencias_dir.iterdir():
                    if species_dir.is_dir():
                        species = species_dir.name
                        images = [f.name for f in species_dir.glob("*.jpg")]
                        if images:
                            evidence_dict[species] = images
        
        return evidence_dict
    
    except Exception as e:
        logger.error(f"Error listando evidencias de video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listando evidencias: {str(e)}"
        )