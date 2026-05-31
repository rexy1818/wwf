# Backend de cámaras trampa

Backend FastAPI para procesar uno o varios videos de cámaras trampa con Google SpeciesNet oficial, OCR de la banda inferior impresa en la imagen y generación de resultados por cámara.

## Flujo activo

1. El frontend sube uno o varios videos a `/analyze/upload` o `/analyze/upload/batch`.
2. El backend guarda temporalmente el video en `video_analysis/`.
3. `SpeciesNetDetector` extrae frames desde el segundo 0 cada 0.5 s y ejecuta SpeciesNet.
4. `EnhancedVideoAnalyzer` descarta vacíos/humanos/vehículos, normaliza especies y aplica OCR sobre la banda inferior del frame detectado.
5. Se guardan imágenes finales en `Resultados/CAMERA_ID/Especie/`.
6. Se genera `Resultados/CAMERA_ID/excel_CAMERA_ID.xlsx`.

## Estructura relevante

```text
app/
  routers/
    video_analysis.py
  services/
    video_analysis_service.py
  utils/
    enhanced_video_analyzer.py
    speciesnet_detector.py
    ocr_extractor.py
    json_storage.py
tests/
  test_camera_trap_pipeline.py
Resultados/
video_analysis/
```

## Instalación

```powershell
pip install -r requirements.txt
```

En Windows, si usas caché local de modelos:

```powershell
$env:KAGGLEHUB_CACHE="D:\backend-v2\wwf\Backend\video_analysis\speciesnet_models"
```

## Ejecutar API

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva:

```text
http://localhost:8000/docs
```

## Endpoints principales

- `POST /analyze/upload`: procesa un video.
- `POST /analyze/upload/batch`: procesa múltiples videos.
- `GET /analyze/results/{video_id}`: devuelve el JSON completo del análisis.
- `GET /analyze/list`: lista análisis guardados.
- `GET /analyze/stats`: estadísticas generales.
- `POST /analyze/report`: regenera Excel desde análisis guardados.
- `GET /analyze/excel/{camera_id}`: descarga el Excel de una cámara.
- `GET /analyze/file/{camera_id}/{species}/{filename}`: sirve una imagen final.

## Excel generado

Cada cámara tiene su propio Excel con estas columnas:

- Camera ID
- Especie
- Fecha
- Hora
- Temperatura °C
- Nombre archivo
- Ruta archivo
- Confianza clasificación

## Pruebas

```powershell
python -m pytest tests
```

El flujo ya no usa YOLO COCO ni clasificadores heurísticos internos. La clasificación de especies depende de SpeciesNet oficial y el OCR no usa EXIF ni metadatos del video.
