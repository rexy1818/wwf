# Guía de Pruebas con Apidog - Sistema de Monitoreo de Fauna

Esta guía te ayudará a probar todos los endpoints del sistema usando Apidog.

## 🚀 Configuración Inicial

### 1. Iniciar el Servidor
```bash
python main.py
```
El servidor estará disponible en: `http://localhost:8000`

### 2. Verificar que el Servidor Funciona
Abrir en navegador: http://localhost:8000/health

## 📋 Colección de Pruebas para Apidog

### Configuración Base
- **Base URL**: `http://localhost:8000`
- **Headers comunes**: `Content-Type: application/json`

---

## 🎯 FASE 1: GESTIÓN DE CÁMARAS

### 1.1 Crear Cámara
```
POST {{baseUrl}}/cameras
Content-Type: application/json

{
  "nombre": "Cámara Bosque Norte",
  "ubicacion": "Sector A - Reserva Natural"
}
```

**Respuesta esperada (201):**
```json
{
  "id": "camara_bosque_norte_abc12345",
  "nombre": "Cámara Bosque Norte",
  "ubicacion": "Sector A - Reserva Natural",
  "fecha_creacion": "2026-05-30T14:51:00",
  "ruta_storage": "storage/camara_bosque_norte_abc12345"
}
```

**⚠️ IMPORTANTE**: Guardar el `id` de la cámara para usar en las siguientes pruebas.

### 1.2 Listar Todas las Cámaras
```
GET {{baseUrl}}/cameras
```

**Respuesta esperada (200):**
```json
[
  {
    "id": "camara_bosque_norte_abc12345",
    "nombre": "Cámara Bosque Norte",
    "ubicacion": "Sector A - Reserva Natural",
    "fecha_creacion": "2026-05-30T14:51:00",
    "ruta_storage": "storage/camara_bosque_norte_abc12345",
    "videos_procesados": 0,
    "total_detecciones": 0
  }
]
```

### 1.3 Obtener Información de Cámara Específica
```
GET {{baseUrl}}/cameras/{{camera_id}}
```

Reemplazar `{{camera_id}}` con el ID obtenido en el paso 1.1.

---

## 🎬 FASE 2: GESTIÓN DE VIDEOS

### 2.1 Subir Video
```
POST {{baseUrl}}/videos/upload
Content-Type: multipart/form-data

Form Data:
- camera_id: {{camera_id}}
- file: [SELECCIONAR ARCHIVO DE VIDEO]
```

**Formatos soportados**: mp4, avi, mov, mkv, wmv, flv, webm

**Respuesta esperada (201):**
```json
{
  "filename": "video_prueba.mp4",
  "original_filename": "video_prueba.mp4",
  "file_path": "storage/camara_bosque_norte_abc12345/videos/video_prueba.mp4",
  "file_size": 15728640,
  "camera_id": "camara_bosque_norte_abc12345",
  "status": "uploaded"
}
```

### 2.2 Listar Videos de una Cámara
```
GET {{baseUrl}}/videos/{{camera_id}}
```

**Respuesta esperada (200):**
```json
[
  {
    "filename": "video_prueba.mp4",
    "file_path": "storage/camara_bosque_norte_abc12345/videos/video_prueba.mp4",
    "file_size": 15728640,
    "created_at": 1717077060.0,
    "modified_at": 1717077060.0
  }
]
```

### 2.3 Obtener Información de Video Específico
```
GET {{baseUrl}}/videos/{{camera_id}}/video_prueba.mp4
```

---

## 🔍 FASE 3: PROCESAMIENTO CON YOLO

### 3.1 Procesar Videos de una Cámara
```
POST {{baseUrl}}/process/camera/{{camera_id}}?interval_seconds=5&confidence_threshold=0.5
```

**Parámetros opcionales:**
- `interval_seconds`: Intervalo entre frames (1-60, default: 5)
- `confidence_threshold`: Umbral de confianza (0.1-1.0, default: 0.5)

**⏱️ Nota**: Este proceso puede tomar varios minutos dependiendo del tamaño del video.

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
      "video": "video_prueba",
      "especie": "ave",
      "confianza": 0.847,
      "fecha": "2026-05-30",
      "hora": "14:51:30",
      "frame": 0,
      "timestamp": 0.0,
      "ruta_evidencia": "storage/camara_bosque_norte_abc12345/evidencias/ave/ave_video_prueba_frame_0_20260530_145130.jpg"
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

## 📊 FASE 4: CONSULTA DE RESULTADOS

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
  "detecciones": [...]
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

## 🧪 CASOS DE PRUEBA ADICIONALES

### Caso 1: Error - Cámara No Existe
```
GET {{baseUrl}}/cameras/camara_inexistente
```
**Respuesta esperada (404):**
```json
{
  "detail": "Cámara no encontrada: camara_inexistente"
}
```

### Caso 2: Error - Formato de Video No Soportado
```
POST {{baseUrl}}/videos/upload
Content-Type: multipart/form-data

Form Data:
- camera_id: {{camera_id}}
- file: [ARCHIVO .txt o .pdf]
```
**Respuesta esperada (400):**
```json
{
  "detail": "Formato no soportado: .txt. Formatos válidos: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm"
}
```

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

## 📁 VERIFICACIÓN DE ARCHIVOS GENERADOS

Después del procesamiento, verificar que se crearon los siguientes archivos:

### Estructura de Directorios
```
storage/
└── camara_bosque_norte_abc12345/
    ├── videos/
    │   └── video_prueba.mp4
    ├── evidencias/
    │   ├── ave/
    │   │   └── ave_video_prueba_frame_0_20260530_145130.jpg
    │   └── felino/
    │       └── felino_video_prueba_frame_5_20260530_145135.jpg
    ├── excel/
    │   └── reporte_20260530_145100.xlsx
    ├── resultados/
    │   ├── ultimo_procesamiento.json
    │   └── procesamiento_20260530_145100.json
    └── metadata/
        └── camera_info.json
```

---

## 🎯 FLUJO COMPLETO DE PRUEBA

### Secuencia Recomendada:
1. **Crear cámara** → Obtener camera_id
2. **Subir video** → Confirmar upload exitoso
3. **Procesar videos** → Esperar completación
4. **Verificar resultados** → Revisar detecciones
5. **Comprobar archivos** → Validar estructura generada

### Variables de Entorno para Apidog:
```
baseUrl: http://localhost:8000
camera_id: [ID_OBTENIDO_EN_PASO_1]
```

---

## 🐛 Solución de Problemas

### Error de Conexión
- Verificar que el servidor esté corriendo en puerto 8000
- Comprobar firewall/antivirus

### Error 500 en Procesamiento
- Verificar que el video no esté corrupto
- Comprobar formato de video soportado
- Revisar logs en `app.log`

### Procesamiento Muy Lento
- Usar videos más cortos para pruebas (<2 minutos)
- Aumentar `interval_seconds` para procesar menos frames
- Verificar recursos del sistema (CPU/RAM)

---

## 📊 MÉTRICAS DE RENDIMIENTO

### Tiempos Esperados:
- **Crear cámara**: <1 segundo
- **Subir video (10MB)**: 2-5 segundos
- **Procesar video (1 minuto)**: 30-120 segundos
- **Generar reporte**: 1-3 segundos

### Recursos:
- **RAM**: ~500MB durante procesamiento
- **CPU**: Uso intensivo durante análisis YOLO
- **Disco**: Videos + evidencias + reportes