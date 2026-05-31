# Guía de Pruebas con Apidog - Sistema de Análisis de Videos de Fauna

Esta guía te ayudará a probar el nuevo sistema simplificado que analiza videos directamente extrayendo información del texto superpuesto.

## 🚀 Configuración Inicial

### 1. Iniciar el Servidor
```bash
python main.py
```
El servidor estará disponible en: `http://localhost:8000`

### 2. Instalar OCR (Recomendado)
```bash
pip install easyocr
# o
pip install pytesseract
```

### 3. Verificar que el Servidor Funciona
Abrir en navegador: http://localhost:8000/health

## 📋 Colección de Pruebas para Apidog

### Configuración Base
- **Base URL**: `http://localhost:8000`
- **Headers comunes**: `Content-Type: multipart/form-data` (para uploads)

---

## 🎯 NUEVO FLUJO SIMPLIFICADO

### 1. Subir y Analizar Video Automáticamente
```
POST {{baseUrl}}/analyze/upload
Content-Type: multipart/form-data

Form Data:
- file: [SELECCIONAR VIDEO DE CÁMARA TRAMPA]
```

**El sistema automáticamente:**
1. ✅ **Extrae texto superpuesto** con OCR (ID cámara, fecha, hora, temperatura)
2. ✅ **Detecta animales** con YOLO
3. ✅ **Genera evidencias** fotográficas por especie
4. ✅ **Guarda todo** en JSON estructurado

**Respuesta esperada (201):**
```json
{
  "video_id": "abc123def456",
  "filename": "WhatsApp Video 2026-05-30 at 12.38.25.mp4",
  "status": "analyzed",
  "upload_time": "2026-05-30T16:30:00",
  "analysis": {
    "video_id": "abc123def456",
    "video_name": "WhatsApp Video 2026-05-30 at 12.38.25",
    "metadata": {
      "filename": "WhatsApp Video 2026-05-30 at 12.38.25.mp4",
      "file_size": 934567,
      "duration": 15.5,
      "fps": 30.0,
      "resolution": "1920x1080",
      "fecha_video": "2026-05-30",
      "hora_video": "12:38:25",
      "ubicacion_gps": null,
      "temperatura": 15.0,
      "camara_id": "CAM001",
      "ocr_info": {
        "frames_procesados": 5,
        "texto_detectado": true
      }
    },
    "estadisticas": {
      "total_animales": 2,
      "especies_encontradas": ["ave", "felino"],
      "detecciones_por_especie": {
        "ave": 1,
        "felino": 1
      },
      "confianza_promedio": 0.847
    }
  }
}
```

**⚠️ IMPORTANTE**: Guardar el `id` de la cámara para usar en las siguientes pruebas.

### 1.2 Listar Todas las Cámaras
```
GET {{baseUrl}}/cameras
```

### 2. Ver Resultado Completo del Análisis
```
GET {{baseUrl}}/analyze/results/{{video_id}}
```

**Respuesta esperada (200):**
```json
{
  "video_id": "abc123def456",
  "metadata": {
    "camara_id": "CAM001",
    "fecha_video": "2026-05-30",
    "hora_video": "12:38:25",
    "temperatura": 15.0,
    "resolution": "1920x1080",
    "duration": 15.5
  },
  "detecciones": [
    {
      "especie": "ave",
      "confianza": 0.847,
      "frame_numero": 0,
      "timestamp_video": 0.0,
      "bbox_x": 150,
      "bbox_y": 200,
      "bbox_width": 300,
      "bbox_height": 250,
      "ruta_evidencia": "video_analysis/analysis/evidencias/ave/ave_video_frame_0_0.jpg",
      "fecha_video": "2026-05-30",
      "hora_video": "12:38:25",
      "camara_id": "CAM001",
      "temperatura": 15.0
    }
  ],
  "estadisticas": {
    "total_animales": 2,
    "especies_encontradas": ["ave", "felino"],
    "confianza_promedio": 0.847
  }
}
```

---

## 🎯 FLUJO COMPLETO SIMPLIFICADO

### **Nuevo flujo (sin crear cámaras):**
1. **Subir video** → `POST /analyze/upload`
2. **Ver resultado** → `GET /analyze/results/{video_id}`
3. **Ver estadísticas** → `GET /system/stats`
4. **Ver cámaras identificadas** → `GET /system/cameras`
5. **Generar reporte** → `POST /analyze/report`
6. **Ver imágenes** → `GET /analyze/evidence/{video_id}/list`

### **Variables de Entorno para Apidog:**
```
baseUrl: http://localhost:8000
video_id: [ID_OBTENIDO_AL_SUBIR_VIDEO]
```

### **Ejemplo Completo:**

#### 1. Subir Video con Texto Superpuesto
```
POST /analyze/upload
# El video debe tener texto como:
# CAM001    15°C
# 2024-05-30 08:30:15
```

#### 2. Ver Resultado Completo
```
GET /analyze/results/{video_id}
```

#### 3. Ver Todas las Cámaras Identificadas
```
GET /system/cameras
# Muestra CAM001, CAM002, etc. extraídos automáticamente
```

#### 4. Ver Estadísticas del Sistema
```
GET /system/stats
# Resumen completo de todo el sistema
```

#### 5. Generar Reporte Excel
```
POST /analyze/report
# Incluye todas las imágenes de evidencia
```

### **Hojas incluidas:**

#### **1. Resumen_Videos**
- Video ID, Nombre, Cámara ID
- Fecha, Hora, Temperatura
- Ubicación GPS, Duración, Resolución
- Total detecciones, Especies encontradas
- Confianza promedio

#### **2. Detecciones_Completas**
- Información completa de cada detección
- **Rutas de imágenes**: `ruta_evidencia` y `ruta_evidencia_limpia`
- Coordenadas del bounding box
- Tamaño del animal en píxeles

#### **3. Estadisticas_Especies**
- Videos únicos por especie
- Total detecciones, confianza promedio/máxima/mínima
- Temperatura promedio por especie
- Tamaño promedio de animales detectados

#### **4. Evidencias_Fotograficas** (NUEVA)
- Lista completa de imágenes generadas
- Especie, cámara, fecha, ruta de archivo
- Nombre del archivo de imagen
- Nivel de confianza de cada detección

### **Ejemplo de fila en Excel:**
```
| Video ID | Especie | Confianza | Fecha | Hora | Temp | Ruta Evidencia |
|----------|---------|-----------|-------|------|------|-----------------|
| abc123   | ave     | 0.847     | 2026-05-30 | 12:38:25 | 15°C | .../ave_video_frame_0_15.jpg |
```
```
GET {{baseUrl}}/analyze/list
```

**Respuesta esperada (200):**
```json
[
  {
    "video_id": "abc123def456",
    "video_name": "WhatsApp Video 2026-05-30 at 12.38.25",
    "camara_id": "CAM001",
    "fecha_video": "2026-05-30",
    "total_detecciones": 2,
    "especies_encontradas": ["ave", "felino"],
    "procesado_en": "2026-05-30T16:30:00"
  }
]
```

### 4. Ver Estadísticas Generales
```
GET {{baseUrl}}/analyze/stats
```

**Respuesta esperada (200):**
```json
{
  "total_videos": 5,
  "total_detecciones": 12,
  "especies_unicas": ["ave", "felino", "canino"],
  "camaras_unicas": ["CAM001", "CAM002", "TRAP123"],
  "videos_por_camara": {
    "CAM001": 3,
    "CAM002": 2
  },
  "detecciones_por_especie": {
    "ave": 8,
    "felino": 3,
    "canino": 1
  }
}
```

### 5. Generar Reporte Excel
```
POST {{baseUrl}}/analyze/report
```

**Para videos específicos:**
```
POST {{baseUrl}}/analyze/report?video_ids=abc123def456&video_ids=xyz789abc123
```

### 6. Ver Imágenes de Evidencias

#### 6.1 Listar Imágenes de un Video
```
GET {{baseUrl}}/analyze/evidence/{{video_id}}/list
```

**Respuesta esperada (200):**
```json
{
  "ave": [
    "ave_video_frame_0_15.jpg",
    "ave_video_frame_0_15_clean.jpg"
  ],
  "felino": [
    "felino_video_frame_8_30.jpg",
    "felino_video_frame_8_30_clean.jpg"
  ]
}
```

#### 6.2 Descargar Imagen Específica
```
GET {{baseUrl}}/analyze/evidence/{{video_id}}/{{species}}/{{filename}}
```

**Ejemplo:**
```
GET {{baseUrl}}/analyze/evidence/abc123def456/ave/ave_video_frame_0_15.jpg
```

**Respuesta:** Archivo de imagen JPEG

**Tipos de imágenes disponibles:**
- **Con información**: `animal_video_frame_X_Y.jpg` (incluye datos superpuestos)
- **Limpia**: `animal_video_frame_X_Y_clean.jpg` (solo el animal, sin texto)

---

## 🖼️ **CARACTERÍSTICAS DE LAS IMÁGENES DE EVIDENCIA**

### **Información Superpuesta:**
- ✅ **Especie y confianza**: "AVE (84.7%)"
- ✅ **ID de cámara**: "CAM: CAM001"
- ✅ **Fecha y hora**: "2026-05-30 12:38:25"
- ✅ **Temperatura**: "TEMP: 15°C"
- ✅ **Timestamp de detección**: "Detected: 2026-05-30 16:30:00"
- ✅ **Bounding box**: Rectángulo verde alrededor del animal

### **Calidad de Imagen:**
- **Formato**: JPEG con 95% de calidad
- **Margen**: 30% extra alrededor del animal para contexto
- **Resolución**: Mantiene resolución original del video
- **Dos versiones**: Con información superpuesta y limpia

### 7. Ver Información del Sistema

#### 7.1 Estadísticas Generales
```
GET {{baseUrl}}/system/stats
```

**Respuesta esperada (200):**
```json
{
  "total_videos": 5,
  "total_detecciones": 12,
  "camaras_identificadas": ["CAM001", "CAM002", "TRAP123"],
  "especies_encontradas": ["ave", "felino", "canino"],
  "videos_por_camara": {
    "CAM001": 3,
    "CAM002": 2
  },
  "detecciones_por_especie": {
    "ave": 8,
    "felino": 3,
    "canino": 1
  },
  "temperatura_promedio": 18.5,
  "rango_temperaturas": {
    "minima": 12.0,
    "maxima": 25.0
  }
}
```

#### 7.2 Información de Cámaras Identificadas
```
GET {{baseUrl}}/system/cameras
```

**Respuesta esperada (200):**
```json
[
  {
    "camara_id": "CAM001",
    "videos_procesados": 3,
    "total_detecciones": 8,
    "especies_encontradas": ["ave", "felino"],
    "fechas_videos": ["2026-05-28", "2026-05-29", "2026-05-30"],
    "temperatura_promedio": 16.5,
    "rango_temperaturas": {
      "minima": 12.0,
      "maxima": 20.0
    },
    "primer_procesamiento": "2026-05-30T15:00:00",
    "ultimo_procesamiento": "2026-05-30T16:30:00"
  }
]
```

#### 7.3 Exportar Todos los Datos
```
GET {{baseUrl}}/system/export
```

**Respuesta esperada (200):**
```json
{
  "message": "Datos exportados exitosamente",
  "filename": "fauna_export_20260530_163000.json",
  "timestamp": "2026-05-30T16:30:00"
}
```

### 3.1 Procesar Videos de una Cámara (Con Metadatos)
```
POST {{baseUrl}}/process/camera/{{camera_id}}?interval_seconds=5&confidence_threshold=0.5
```

**Parámetros opcionales:**
- `interval_seconds`: Intervalo entre frames (1-60, default: 5)
- `confidence_threshold`: Umbral de confianza (0.1-1.0, default: 0.5)

**⏱️ Nota**: 
- El procesamiento usa los videos ya cargados en el storage
- Extrae fecha, hora y GPS de los metadatos originales del video
- Puede tomar varios minutos dependiendo del número y tamaño de videos

**Respuesta esperada (200):**
```json
{
  "videos_procesados": 1,
  "animales_detectados": 3,
  "especies_encontradas": ["ave", "felino"],
  "ruta_excel": "storage/camara_bosque_norte_abc12345/excel/reporte_20260530_145100.xlsx",
  "total_evidencias": 3,
  "detecciones": [
    {
      "video": "video_fauna_001",
      "especie": "ave",
      "confianza": 0.847,
      "fecha_video": "2026-05-25",
      "hora_video": "08:30:15",
      "ubicacion_gps": "-12.345678, -76.543210",
      "frame": 0,
      "timestamp": 0.0,
      "ruta_evidencia": "storage/camara_bosque_norte_abc12345/evidencias/ave/ave_video_fauna_001_frame_0_20260525_083015.jpg",
      "timestamp_video": "2026-05-25T08:30:15",
      "duracion_video": 120.5,
      "resolucion_video": "1920x1080",
      "camara_marca": "Reconyx",
      "camara_modelo": "HC600"
    }
  ],
  "configuracion": {
    "intervalo_segundos": 5,
    "umbral_confianza": 0.5
  }
}
```

### 3.2 Procesar con Configuración Personalizada
```
POST {{baseUrl}}/process/camera/{{camera_id}}?interval_seconds=3&confidence_threshold=0.7
```

Para mayor precisión (más lento):
- `interval_seconds=3` (más frames)
- `confidence_threshold=0.7` (mayor confianza)

---

## 📊 FASE 4: CONSULTA DE RESULTADOS (ACTUALIZADA)

### 4.1 Obtener Resultados del Último Procesamiento
```
GET {{baseUrl}}/process/camera/{{camera_id}}/results
```

**Respuesta esperada (200):**
```json
{
  "videos_procesados": 1,
  "animales_detectados": 3,
  "especies_encontradas": ["ave", "felino"],
  "ruta_excel": "storage/camara_bosque_norte_abc12345/excel/reporte_20260530_145100.xlsx",
  "total_evidencias": 3,
  "fecha_procesamiento": "2026-05-30T14:51:00",
  "camera_id": "camara_bosque_norte_abc12345",
  "detecciones": [
    {
      "video": "video_fauna_001",
      "especie": "ave",
      "confianza": 0.847,
      "fecha_video": "2026-05-25",
      "hora_video": "08:30:15",
      "ubicacion_gps": "-12.345678, -76.543210",
      "frame": 0,
      "ruta_evidencia": "storage/.../evidencias/ave/ave_video_fauna_001_frame_0_20260525_083015.jpg",
      "timestamp_video": "2026-05-25T08:30:15",
      "camara_marca": "Reconyx",
      "camara_modelo": "HC600"
    }
  ]
}
```

### 4.2 Obtener Historial de Procesamientos
```
GET {{baseUrl}}/process/camera/{{camera_id}}/history
```

**Respuesta esperada (200):**
```json
[
  {
    "fecha_procesamiento": "2026-05-30T14:51:00",
    "videos_procesados": 1,
    "animales_detectados": 3,
    "especies_encontradas": ["ave", "felino"],
    "archivo": "procesamiento_20260530_145100.json"
  }
]
```

---

## 🔧 ENDPOINTS DE UTILIDAD

### Health Check
```
GET {{baseUrl}}/health
```

### Información General del Sistema
```
GET {{baseUrl}}/
```

### Documentación Swagger
```
GET {{baseUrl}}/docs
```

---

## 🧪 CASOS DE PRUEBA ADICIONALES (ACTUALIZADOS)

### Caso 1: Error - Ruta de Videos No Existe
```
POST {{baseUrl}}/cameras
Content-Type: application/json

{
  "nombre": "Cámara Inexistente",
  "ruta_videos": "D:\\ruta\\que\\no\\existe"
}
```
**Respuesta esperada (400):**
```json
{
  "detail": "La ruta de videos no existe: D:\\ruta\\que\\no\\existe"
}
```

### Caso 2: Crear Cámara con Carpeta Vacía
```
POST {{baseUrl}}/cameras
Content-Type: application/json

{
  "nombre": "Cámara Sin Videos",
  "ruta_videos": "D:\\carpeta\\vacia"
}
```
**Respuesta esperada (201):** Cámara creada pero sin videos cargados.

### Caso 3: Procesar Cámara Sin Videos
```
POST {{baseUrl}}/process/camera/{{camera_id_sin_videos}}
```
**Respuesta esperada (200):**
```json
{
  "videos_procesados": 0,
  "animales_detectados": 0,
  "especies_encontradas": [],
  "ruta_excel": "",
  "total_evidencias": 0
}
```

---

## 📁 VERIFICACIÓN DE ARCHIVOS GENERADOS (ACTUALIZADA)

Después del procesamiento, verificar que se crearon los siguientes archivos:

### Estructura de Directorios
```
storage/
└── camara_bosque_norte_abc12345/
    ├── videos/
    │   └── video_fauna_001.mp4          # Copiado desde carpeta original
    ├── evidencias/
    │   ├── ave/
    │   │   └── ave_video_fauna_001_frame_0_20260525_083015.jpg
    │   └── felino/
    │       └── felino_video_fauna_001_frame_5_20260525_083020.jpg
    ├── excel/
    │   └── reporte_20260530_145100.xlsx  # Con metadatos del video
    ├── resultados/
    │   ├── ultimo_procesamiento.json
    │   └── procesamiento_20260530_145100.json
    └── metadata/
        └── camera_info.json              # Incluye ruta_videos
```

### Contenido del Reporte Excel (Actualizado)
El reporte Excel ahora incluye las siguientes columnas:

#### Hoja "Detecciones"
- **video**: Nombre del video
- **especie**: Especie detectada
- **confianza**: Nivel de confianza
- **fecha_video**: Fecha extraída del video (metadatos)
- **hora_video**: Hora extraída del video (metadatos)
- **ubicacion_gps**: Coordenadas GPS del video
- **frame**: Número de frame
- **ruta_evidencia**: Ruta de la imagen capturada
- **timestamp_video**: Timestamp original del video
- **duracion_video**: Duración total del video
- **resolucion_video**: Resolución del video
- **camara_marca**: Marca de la cámara
- **camara_modelo**: Modelo de la cámara

---

## 🎯 FLUJO COMPLETO DE PRUEBA (ACTUALIZADO)

### Secuencia Recomendada:
1. **Preparar carpeta con videos** → Asegurar que `D:\1-fauna\camara-1` tiene videos
2. **Crear cámara** → Especificar ruta de videos, obtener camera_id
3. **Verificar carga automática** → Confirmar que videos se copiaron al storage
4. **Procesar videos** → Ejecutar análisis YOLO con extracción de metadatos
5. **Verificar resultados** → Revisar detecciones con fecha/hora/GPS originales
6. **Comprobar archivos** → Validar estructura y contenido del Excel

### Variables de Entorno para Apidog:
```
baseUrl: http://localhost:8000
camera_id: [ID_OBTENIDO_EN_PASO_2]
ruta_videos: D:\1-fauna\camara-1
```

### Ejemplo Completo con Datos Reales:

#### 1. Crear Cámara
```json
POST /cameras
{
  "nombre": "Cámara Trampa Bosque Norte",
  "ruta_videos": "D:\\1-fauna\\camara-1"
}
```

#### 2. Verificar Videos Cargados
```
GET /videos/{{camera_id}}
```

#### 3. Procesar con Configuración Óptima
```
POST /process/camera/{{camera_id}}?interval_seconds=3&confidence_threshold=0.6
```

#### 4. Obtener Resultados Detallados
```
GET /process/camera/{{camera_id}}/results
```

---

## 🐛 Solución de Problemas (ACTUALIZADA)

### Error de Conexión
- Verificar que el servidor esté corriendo en puerto 8000
- Comprobar firewall/antivirus

### Error: "La ruta de videos no existe"
- Verificar que la ruta especificada en `ruta_videos` existe
- Usar rutas absolutas (ej: `D:\\1-fauna\\camara-1`)
- En Windows, usar doble backslash (`\\`) o forward slash (`/`)

### Error 500 en Procesamiento
- Verificar que los videos no estén corruptos
- Comprobar formato de video soportado
- Revisar logs en `app.log`
- Verificar que ffprobe esté instalado (opcional, para metadatos avanzados)

### Videos No Se Cargan Automáticamente
- Verificar permisos de lectura en la carpeta de videos
- Comprobar que los videos tienen extensiones soportadas
- Revisar logs para errores específicos

### Metadatos Incompletos
- Algunos videos pueden no tener metadatos GPS o de fecha
- El sistema usa fecha de archivo como fallback
- ffprobe (opcional) mejora la extracción de metadatos

### Procesamiento Muy Lento
- Usar videos más cortos para pruebas (<2 minutos)
- Aumentar `interval_seconds` para procesar menos frames
- Verificar recursos del sistema (CPU/RAM)

---

## 📊 MÉTRICAS DE RENDIMIENTO (ACTUALIZADAS)

### Tiempos Esperados:
- **Crear cámara + cargar videos**: 5-30 segundos (según cantidad de videos)
- **Procesar video (1 minuto)**: 30-120 segundos
- **Generar reporte con metadatos**: 2-5 segundos
- **Extracción de metadatos por video**: 1-3 segundos

### Recursos:
- **RAM**: ~500MB durante procesamiento
- **CPU**: Uso intensivo durante análisis YOLO
- **Disco**: Videos originales + copia en storage + evidencias + reportes

### Formatos de Video Soportados:
- **Principales**: mp4, avi, mov, mkv
- **Adicionales**: wmv, flv, webm, m4v
- **Metadatos**: Mejor soporte en mp4 y mov

## 🎥 METADATOS DE VIDEO SOPORTADOS

### Información Extraída:
- **Fecha/Hora**: Timestamp de creación del video
- **GPS**: Coordenadas de ubicación (si están disponibles)
- **Cámara**: Marca y modelo del dispositivo
- **Técnicos**: Resolución, FPS, duración
- **Archivo**: Tamaño, fechas de creación/modificación

### Fuentes de Metadatos (Prioridad):
1. **Metadatos EXIF/MP4** (más precisos)
2. **Nombre del archivo** (patrones comunes)
3. **Fecha de archivo** (fallback)

### Patrones de Nombre Soportados:
- `YYYYMMDD_HHMMSS.mp4`
- `YYYY-MM-DD_HH-MM-SS.mp4`
- `IMG_YYYYMMDD_HHMMSS.mp4`