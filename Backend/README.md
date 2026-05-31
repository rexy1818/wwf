# Sistema de Monitoreo de Fauna con Cámaras Trampa

MVP funcional para análisis automático de videos de cámaras trampa usando YOLO para detectar animales.

## 🎯 Objetivo Principal

Analizar automáticamente videos de cámaras trampa y detectar animales usando YOLO, generando evidencias y reportes detallados.

## 🚀 Tecnologías

- **Python 3.12**
- **FastAPI** - Framework web moderno y rápido
- **OpenCV** - Procesamiento de video e imágenes
- **Ultralytics YOLO** - Detección de objetos/animales
- **Pandas & OpenPyXL** - Generación de reportes Excel
- **Uvicorn** - Servidor ASGI

## 📁 Estructura del Proyecto

```
Backend/
├── app/
│   ├── routers/          # Endpoints de la API
│   │   ├── cameras.py    # Gestión de cámaras
│   │   ├── videos.py     # Subida de videos
│   │   └── processing.py # Procesamiento con YOLO
│   ├── services/         # Lógica de negocio
│   │   ├── camera_service.py
│   │   ├── video_service.py
│   │   └── processing_service.py
│   ├── schemas/          # Modelos de datos
│   │   └── camera.py
│   └── utils/            # Utilidades
│       ├── file_manager.py
│       ├── yolo_detector.py
│       └── excel_generator.py
├── storage/              # Almacenamiento de datos
├── main.py              # Aplicación principal
└── requirements.txt     # Dependencias
```

## 🔧 Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd Backend
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python main.py
```

La API estará disponible en: http://localhost:8000

## 📖 Documentación de la API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Guia para frontend y pruebas**: `APIDOG_TESTING_GUIDE.md`

## 🎮 Uso del Sistema

### Fase 1: Crear Cámara
```bash
POST /cameras
{
  "nombre": "Camara 1",
  "ubicacion": "Bosque Norte"
}
```

### Fase 2: Subir Videos
```bash
POST /videos/upload
Form Data:
- camera_id: "camara_1_abc123"
- file: video.mp4
```

### Fase 3: Procesar Videos
```bash
POST /process/camera/{camera_id}?interval_seconds=5&confidence_threshold=0.5
```

### Fase 4: Consultar Resultados
```bash
GET /process/camera/{camera_id}/results
```

## 🐾 Especies Detectables

El sistema puede detectar las siguientes especies usando el modelo YOLO preentrenado:

- **Ave** (bird)
- **Felino** (cat) 
- **Canino** (dog)
- **Caballo** (horse)
- **Oveja** (sheep)
- **Bovino** (cow)
- **Elefante** (elephant)
- **Oso** (bear)
- **Cebra** (zebra)
- **Jirafa** (giraffe)

## 📊 Estructura de Almacenamiento

```
storage/
└── camera_id/
    ├── videos/           # Videos originales subidos
    ├── resultados/       # Archivos JSON con resultados
    ├── evidencias/       # Capturas organizadas por especie
    │   ├── ave/
    │   ├── felino/
    │   ├── canino/
    │   └── ...
    ├── excel/           # Reportes Excel generados
    └── metadata/        # Información de la cámara
```

## 🔍 Procesamiento con YOLO

### Configuración
- **Modelo**: YOLOv8n (se descarga automáticamente)
- **Intervalo de frames**: Configurable (default: 5 segundos)
- **Umbral de confianza**: Configurable (default: 0.5)

### Proceso
1. Extrae frames cada N segundos del video
2. Analiza cada frame con YOLO
3. Filtra detecciones por umbral de confianza
4. Guarda evidencias automáticamente por especie
5. Genera reporte Excel con todas las detecciones

## 📈 Reportes Excel

Los reportes incluyen:

### Hoja "Detecciones"
- Video origen
- Especie detectada
- Nivel de confianza
- Fecha y hora
- Número de frame
- Ruta de evidencia

### Hoja "Resumen_Especies"
- Total de detecciones por especie
- Confianza promedio, máxima y mínima

### Hoja "Resumen_Videos"
- Total de detecciones por video
- Confianza promedio por video

## 🧪 Pruebas con Apidog

### 1. Crear Cámara
```
POST http://localhost:8000/cameras
Content-Type: application/json

{
  "nombre": "Cámara Bosque Norte",
  "ubicacion": "Sector A - Bosque Norte"
}
```

### 2. Subir Video
```
POST http://localhost:8000/videos/upload
Content-Type: multipart/form-data

camera_id: [ID_OBTENIDO_PASO_1]
file: [SELECCIONAR_ARCHIVO_VIDEO]
```

### 3. Procesar Videos
```
POST http://localhost:8000/process/camera/[CAMERA_ID]?interval_seconds=3&confidence_threshold=0.6
```

### 4. Obtener Resultados
```
GET http://localhost:8000/process/camera/[CAMERA_ID]/results
```

## ⚠️ Consideraciones

### Rendimiento
- El procesamiento puede tomar varios minutos según el tamaño y número de videos
- Se recomienda usar videos de máximo 10 minutos para pruebas iniciales
- El sistema procesa videos en paralelo (máximo 2 workers por defecto)

### Formatos Soportados
- **Videos**: mp4, avi, mov, mkv, wmv, flv, webm
- **Salida**: JPG para evidencias, XLSX para reportes

### Limitaciones del MVP
- No incluye autenticación
- No incluye dashboard web
- Detección limitada a especies del modelo COCO
- No incluye identificación individual de animales

## 🔧 Configuración Avanzada

### Cambiar Modelo YOLO
Editar `app/utils/yolo_detector.py`:
```python
# Usar modelo más preciso pero más lento
self.model = YOLO("yolov8m.pt")  # o yolov8l.pt, yolov8x.pt
```

### Ajustar Especies
Modificar `species_mapping` en `yolo_detector.py` para personalizar nombres de especies.

### Configurar Logging
El sistema genera logs en `app.log` y consola. Ajustar nivel en `main.py`.

## 🐛 Solución de Problemas

### Error: "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### Error: "YOLO model not found"
El modelo se descarga automáticamente en la primera ejecución. Verificar conexión a internet.

### Error: "Camera not found"
Verificar que el ID de cámara existe usando `GET /cameras`.

### Videos no se procesan
- Verificar formato de video soportado
- Comprobar que el archivo no esté corrupto
- Revisar logs en `app.log`

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades:
- Crear issue en el repositorio
- Revisar logs en `app.log`
- Verificar documentación en `/docs`
