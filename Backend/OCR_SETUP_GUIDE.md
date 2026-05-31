# Guía de Configuración OCR - Sistema de Monitoreo de Fauna

Esta guía explica cómo configurar OCR para extraer texto superpuesto en videos de cámaras trampa.

## 🎯 ¿Qué puede extraer el OCR?

El sistema puede leer texto superpuesto en videos como:
```
CAM001    15°C
2024-05-30 08:30:15
```

### Información extraída:
- **ID de Cámara**: CAM001, TRAP123, C001, etc.
- **Fecha**: 2024-05-30, 30/05/2024, etc.
- **Hora**: 08:30:15, 14:25:00, etc.
- **Temperatura**: 15°C, -5.5°C, 25 TEMP, etc.

## 📦 Instalación de Dependencias OCR

### Opción 1: EasyOCR (Recomendado)
```bash
pip install easyocr
```

**Ventajas:**
- ✅ Más preciso para texto en imágenes
- ✅ No requiere instalación externa
- ✅ Funciona bien con texto pequeño
- ✅ Soporta múltiples idiomas

### Opción 2: Tesseract OCR
```bash
pip install pytesseract
```

**Además necesitas instalar Tesseract:**

#### Windows:
1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instalar el ejecutable
3. Agregar a PATH o configurar ruta:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### Linux:
```bash
sudo apt install tesseract-ocr
```

#### macOS:
```bash
brew install tesseract
```

## 🔧 Configuración del Sistema

### Instalación Automática
El sistema detecta automáticamente qué motor OCR está disponible:

1. **Prioridad 1**: EasyOCR (si está instalado)
2. **Prioridad 2**: Tesseract (si está instalado)
3. **Fallback**: Sin OCR (usa solo metadatos del archivo)

### Verificar Instalación
```bash
python -c "import easyocr; print('EasyOCR disponible')"
# o
python -c "import pytesseract; print('Tesseract disponible')"
```

## 🎮 Patrones de Texto Soportados

### ID de Cámara
```
CAM001, CAM 001
CAMERA A1, CAMERA_A1
ID001, ID 001
TRAP123, TRAP 123
SITE1 CAM, FOREST CAM
C001, A1, B2
```

### Fecha y Hora
```
2024-05-30 08:30:15
30-05-2024 08:30:15
30/05/24 08:30:15
2024/05/30 14:25:00
```

### Temperatura
```
15°C, 15C
-5.5°C
25 TEMP, TEMP 25
T: 15, T:15
```

## 🔍 Proceso de Extracción

### 1. Muestreo de Frames
- Extrae 5 frames distribuidos a lo largo del video
- Procesa cada frame independientemente
- Consolida resultados para mayor precisión

### 2. Preprocesamiento
- Convierte a escala de grises
- Mejora contraste con CLAHE
- Aplica filtros de ruido
- Enfoca en regiones típicas (esquinas superior e inferior)

### 3. Reconocimiento de Texto
- Usa EasyOCR o Tesseract según disponibilidad
- Filtra resultados por confianza (>50%)
- Aplica patrones regex para extraer información

### 4. Consolidación
- Combina resultados de múltiples frames
- Usa el valor más común para cada campo
- Calcula promedio para temperatura

## 📊 Precisión Esperada

### EasyOCR:
- **Texto claro**: 90-95%
- **Texto pequeño**: 80-90%
- **Texto con ruido**: 70-85%

### Tesseract:
- **Texto claro**: 85-90%
- **Texto pequeño**: 70-80%
- **Texto con ruido**: 60-75%

## 🐛 Solución de Problemas

### Error: "No module named 'easyocr'"
```bash
pip install easyocr
```

### Error: "TesseractNotFoundError"
- Verificar que Tesseract esté instalado
- Configurar ruta correcta en Windows
- Agregar a PATH del sistema

### OCR no detecta texto
- Verificar que el texto esté visible en el video
- Comprobar contraste del texto
- Asegurar que el texto esté en las esquinas del frame

### Resultados inconsistentes
- El sistema procesa múltiples frames para mayor precisión
- Revisa logs para ver qué texto se detectó
- Ajusta patrones regex si es necesario

## 🎯 Optimización

### Para mejorar precisión:
1. **Videos de alta calidad**: Mayor resolución = mejor OCR
2. **Texto contrastado**: Texto blanco sobre fondo oscuro
3. **Posición consistente**: Texto siempre en la misma ubicación
4. **Fuente legible**: Evitar fuentes muy decorativas

### Configuración personalizada:
```python
# En app/utils/ocr_extractor.py
# Ajustar número de frames a procesar
sample_frames = 10  # Más frames = mayor precisión pero más lento

# Ajustar umbral de confianza
if confidence > 0.7:  # Más estricto = menos falsos positivos
```

## 📈 Rendimiento

### Tiempos esperados por video:
- **EasyOCR**: 10-30 segundos
- **Tesseract**: 5-15 segundos
- **Sin OCR**: <1 segundo

### Recursos:
- **RAM**: +200-500MB durante OCR
- **CPU**: Uso intensivo durante procesamiento
- **GPU**: EasyOCR puede usar GPU si está disponible

## 🔄 Flujo Completo

```
Video de cámara trampa
         ↓
1. Extraer 5 frames distribuidos
         ↓
2. Preprocesar cada frame (escala de grises, contraste)
         ↓
3. Aplicar OCR (EasyOCR/Tesseract)
         ↓
4. Parsear texto con regex
         ↓
5. Consolidar resultados de todos los frames
         ↓
6. Retornar: camera_id, fecha, hora, temperatura
```

## 📝 Ejemplo de Salida

```json
{
  "camera_id": "CAM001",
  "fecha": "2024-05-30",
  "hora": "08:30:15",
  "temperatura": 15.0,
  "frames_procesados": 5,
  "texto_detectado": true
}
```