# Guia de API y pruebas - Camaras trampa

Esta guia sirve para integrar el backend con un frontend y para probar el flujo con Apidog, cURL o scripts locales.

## Estado actual

El backend expone endpoints FastAPI para:

- Subir uno o varios videos.
- Procesar videos.
- Detectar animales.
- Clasificar especie.
- Extraer OCR desde la banda inferior de la imagen.
- Guardar evidencias en `Resultados/<CAMERA_ID>/<Especie>/`.
- Generar Excel por camara: `Resultados/<CAMERA_ID>/excel_<CAMERA_ID>.xlsx`.

El OCR corregido ya fue validado con el video de `camara-1`:

- Camera ID: `EST12B`
- Fecha: `2025-07-31`
- Hora: `18:20:19` a `18:20:25`
- Temperatura: `20.0` a `21.0`
- Especie validada con SpeciesNet: `Jaguar`

Nota importante: el endpoint `/analyze/upload` ya usa SpeciesNet oficial mediante `SpeciesNetDetector`.

## Instalacion

Usa Python 3.12.

```powershell
pip install -r requirements.txt
```

Si `megadetector` falla por `onnx`/`cmake` en Windows, instala primero una rueda precompilada:

```powershell
pip install onnx==1.19.1
pip install speciesnet
```

## Variables recomendadas en Windows

Estas variables evitan errores de permisos al descargar modelos o crear cache fuera del proyecto.

```powershell
$env:MPLCONFIGDIR="D:\backend-v2\wwf\Backend\.matplotlib"
$env:EASYOCR_MODULE_PATH="D:\backend-v2\wwf\Backend\video_analysis\ocr_models"
$env:KAGGLEHUB_CACHE="D:\backend-v2\wwf\Backend\video_analysis\speciesnet_models"
```

## Iniciar servidor

```powershell
python main.py
```

URL base:

```text
http://localhost:8000
```

Documentacion interactiva:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
```

Health check:

```http
GET /health
```

## Endpoints principales para frontend

### 1. Subir y analizar un video

```http
POST /analyze/upload
Content-Type: multipart/form-data
```

Form data:

| Campo | Tipo | Requerido | Descripcion |
|---|---|---:|---|
| `file` | File | Si | Video de camara trampa (`mp4`, `avi`, `mov`, `mkv`, `wmv`, `flv`, `webm`, `m4v`) |

Ejemplo `fetch`:

```js
async function analyzeVideo(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("http://localhost:8000/analyze/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
```

Respuesta esperada:

```json
{
  "video_id": "abc123def456",
  "filename": "video.mp4",
  "status": "analyzed",
  "analysis": {
    "video_id": "abc123def456",
    "status": "success",
    "metadata": {
      "filename": "video.mp4",
      "duration": 9.83,
      "fps": 14.54,
      "resolution": "848x480",
      "fecha_video": "2025-07-31",
      "hora_video": "18:20:19",
      "temperatura": 21.0,
      "camara_id": "EST12B"
    },
    "detecciones": [
      {
        "camera_id": "EST12B",
        "especie": "Jaguar",
        "fecha": "2025-07-31",
        "hora": "18:20:19",
        "temperatura_c": 21.0,
        "nombre_archivo": "Jaguar_EST12B_20250731_182019.jpg",
        "ruta_evidencia_final": "Resultados/EST12B/Jaguar/Jaguar_EST12B_20250731_182019.jpg",
        "confianza": 0.8535
      }
    ],
    "estadisticas": {
      "total_animales": 1,
      "especies_encontradas": ["Jaguar"],
      "detecciones_por_especie": {
        "Jaguar": 1
      }
    },
    "excel_files": {
      "EST12B": "Resultados/EST12B/excel_EST12B.xlsx"
    }
  }
}
```

Campos que el frontend normalmente necesita:

| Campo | Uso |
|---|---|
| `video_id` | Consultar el resultado despues |
| `analysis.detecciones[]` | Tabla/listado de detecciones |
| `analysis.detecciones[].ruta_evidencia_final` | Imagen de evidencia |
| `analysis.excel_files` | Ruta del Excel generado por camara |
| `analysis.estadisticas` | Resumen para cards/dashboard |

### 2. (Nuevo) Extraer OCR bajo demanda

Este endpoint realiza la extracción de OCR para una detección específica, actualizando los resultados almacenados. Es más rápido que el flujo original porque el análisis principal ahora omite el OCR.

```http
POST /analyze/detection/{video_id}/{detection_index}/extract-ocr
```

Parámetros:
- `video_id`: ID del análisis retornado en `/analyze/upload`.
- `detection_index`: Índice de la detección en el array `detecciones`.

Respuesta:
Retorna el objeto de la detección actualizado con los campos `camera_id`, `fecha`, `hora`, `temperatura_c` y `ocr_raw_text`.

Form data:

| Campo | Tipo | Requerido | Descripcion |
|---|---|---:|---|
| `files` | File[] | Si | Uno o varios videos |

Ejemplo `fetch`:

```js
async function analyzeVideos(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const response = await fetch("http://localhost:8000/analyze/upload/batch", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}
```

Respuesta esperada:

```json
{
  "status": "completed",
  "total_recibidos": 2,
  "total_procesados": 2,
  "total_errores": 0,
  "results": [],
  "errors": [],
  "processed_at": "2026-05-31T00:00:00"
}
```

### 3. Obtener resultado por video

```http
GET /analyze/results/{video_id}
```

Ejemplo:

```js
async function getAnalysis(videoId) {
  const response = await fetch(`http://localhost:8000/analyze/results/${videoId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}
```

### 4. Listar analisis

```http
GET /analyze/list
```

Uso frontend:

- Historial de videos procesados.
- Tabla de analisis recientes.
- Reintentar descarga de Excel o visualizacion de evidencias.

### 5. Estadisticas generales

```http
GET /analyze/stats
```

Respuesta tipica:

```json
{
  "total_videos": 1,
  "total_detecciones": 13,
  "especies_unicas": ["Jaguar"],
  "camaras_unicas": ["EST12B"],
  "videos_por_camara": {
    "EST12B": 1
  },
  "detecciones_por_especie": {
    "Jaguar": 13
  }
}
```

### 6. Generar reporte Excel

```http
POST /analyze/report
```

Para videos especificos:

```http
POST /analyze/report?video_ids=abc123def456&video_ids=xyz789abc123
```

Salida esperada:

```json
{
  "message": "Reporte Excel generado exitosamente",
  "filename": "Resultados/EST12B/excel_EST12B.xlsx",
  "videos_incluidos": "todos"
}
```

### 7. Evidencias por video

Listar imagenes:

```http
GET /analyze/evidence/{video_id}/list
```

Descargar imagen:

```http
GET /analyze/evidence/{video_id}/{species}/{filename}
```

Nota: el endpoint de evidencia lee desde `video_analysis/analysis/...`. Las salidas finales corregidas se guardan en `Resultados/<CAMERA_ID>/<Especie>/`. Si el frontend necesita servir directamente `Resultados`, conviene agregar un endpoint estatico o un endpoint `GET /results/{camera_id}/{species}/{filename}`.

## Estructura final generada

```text
Resultados/
  EST12B/
    excel_EST12B.xlsx
    Jaguar/
      Jaguar_EST12B_20250731_182019.jpg
      Jaguar_EST12B_20250731_182019_02.jpg
      Jaguar_EST12B_20250731_182020.jpg
```

Columnas del Excel:

| Columna | Ejemplo |
|---|---|
| `Camera ID` | `EST12B` |
| `Especie` | `Jaguar` |
| `Fecha` | `2025-07-31` |
| `Hora` | `18:20:19` |
| `Temperatura °C` | `21.0` |
| `Nombre archivo` | `Jaguar_EST12B_20250731_182019.jpg` |
| `Ruta archivo` | `Resultados/EST12B/Jaguar/...jpg` |
| `Confianza clasificación` | `0.8535` |

## Configuracion en Apidog

Variables de entorno:

```text
baseUrl=http://localhost:8000
video_id=
camera_id=EST12B
```

Request para un video:

```text
POST {{baseUrl}}/analyze/upload
Body: form-data
file: seleccionar archivo .mp4
```

Request para multiples videos:

```text
POST {{baseUrl}}/analyze/upload/batch
Body: form-data
files: seleccionar archivo 1
files: seleccionar archivo 2
```

Tests sugeridos en Apidog:

```js
pm.test("status analyzed", function () {
  pm.expect(pm.response.json().status).to.eql("analyzed");
});

pm.test("has video_id", function () {
  pm.expect(pm.response.json().video_id).to.be.a("string");
});

pm.test("has analysis", function () {
  pm.expect(pm.response.json().analysis).to.be.an("object");
});
```

## cURL

Subir un video:

```bash
curl -X POST "http://localhost:8000/analyze/upload" \
  -F "file=@camara-1/WhatsApp Video 2026-05-30 at 12.38.25 (1).mp4"
```

Consultar resultado:

```bash
curl "http://localhost:8000/analyze/results/{video_id}"
```

Generar reporte:

```bash
curl -X POST "http://localhost:8000/analyze/report"
```

## Prueba local validada con SpeciesNet

Este bloque reproduce la prueba hecha con el video de `camara-1`.

### 1. Extraer frames desde segundo 0

```powershell
C:\Users\ale\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -c "import cv2, pathlib; video=r'camara-1\WhatsApp Video 2026-05-30 at 12.38.25 (1).mp4'; out=pathlib.Path('video_analysis/speciesnet_frames/testcam1'); out.mkdir(parents=True, exist_ok=True); cap=cv2.VideoCapture(video); fps=cap.get(cv2.CAP_PROP_FPS) or 30; total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); step=max(1,int(round(fps*0.5))); saved=0; indices=sorted(set([0,total-1]+list(range(0,total,step)))); 
for idx in indices:
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx); ok, frame=cap.read()
    if ok:
        cv2.imwrite(str(out / f'frame_{idx:06d}_{idx/fps:.2f}s.jpg'), frame); saved += 1
cap.release(); print({'fps':fps,'total_frames':total,'saved_frames':saved,'folder':str(out)})"
```

### 2. Ejecutar SpeciesNet con geofencing Bolivia

```powershell
$env:MPLCONFIGDIR="D:\backend-v2\wwf\Backend\.matplotlib"
$env:KAGGLEHUB_CACHE="D:\backend-v2\wwf\Backend\video_analysis\speciesnet_models"

C:\Users\ale\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m speciesnet.scripts.run_model `
  --folders "video_analysis\speciesnet_frames\testcam1" `
  --predictions_json "video_analysis\speciesnet_testcam1_predictions.json" `
  --country BOL `
  --bypass_prompts `
  --ignore_existing_predictions
```

Resultado validado:

```text
total_frames: 22
frames_with_animal: 14
Jaguar: 13
blank: 8
mammal: 1
avg_confidence_jaguar: 0.9766
```

### 3. Validar OCR sobre una evidencia

```powershell
$env:EASYOCR_MODULE_PATH="D:\backend-v2\wwf\Backend\video_analysis\ocr_models"

C:\Users\ale\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -c "import cv2, json; from app.utils.ocr_extractor import OCRExtractor; o=OCRExtractor(); img=cv2.imread(r'Resultados\EST12B\Jaguar\Jaguar_EST12B_20250731_182019.jpg'); print(json.dumps(o.extract_text_from_frame_band(img), ensure_ascii=False, indent=2))"
```

Salida esperada:

```json
{
  "camera_id": "EST12B",
  "fecha": "2025-07-31",
  "hora": "18:20:19",
  "temperatura": 21.0
}
```

## Manejo de errores para frontend

| Caso | Codigo esperado | Accion UI |
|---|---:|---|
| Sin archivo | `400` | Mostrar "Selecciona un video" |
| Formato no soportado | `400` | Mostrar formatos permitidos |
| Error procesando video | `500` | Permitir reintento y mostrar detalle |
| `video_id` inexistente | `404` | Mostrar "Analisis no encontrado" |

Ejemplo:

```js
async function requestJson(url, options) {
  const response = await fetch(url, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = data?.detail || `Error HTTP ${response.status}`;
    throw new Error(message);
  }

  return data;
}
```

## Checklist de prueba

- El video se procesa desde el segundo 0.
- No se guardan imagenes vacias en `Resultados`.
- La especie aparece como una de: `Jaguar`, `Puma`, `Ocelote`, `Tapir`, `Venado`, `Otros`.
- La imagen final conserva la banda inferior visible.
- OCR extrae `Camera ID`, `Fecha`, `Hora`, `Temperatura °C`.
- El Excel por camara existe.
- Las rutas del Excel apuntan a imagenes reales.
- El batch devuelve `completed` o `completed_with_errors` con detalle por archivo.

## Notas tecnicas importantes

- No usar EXIF para fecha/hora/camara. La fuente valida es el texto impreso en la imagen.
- EasyOCR debe leer la banda inferior cruda o suavemente escalada; binarizar agresivamente puede eliminar texto en camaras Bushnell.
- SpeciesNet es mas apropiado que YOLO COCO para especies latinoamericanas. YOLO COCO no conoce `jaguar`, `tapir` u `ocelote` como clases nativas.
- Para produccion, cachear los modelos en `video_analysis/speciesnet_models` y evitar descargarlos en cada despliegue.
