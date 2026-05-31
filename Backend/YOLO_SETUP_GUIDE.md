# Guía de Configuración YOLO - Sistema de Monitoreo de Fauna

Esta guía explica cómo configurar YOLO para la detección de animales en el sistema.

## 📦 Instalación de YOLO

### 1. Instalación Automática
YOLO se instala automáticamente con las dependencias:
```bash
pip install ultralytics
```

### 2. Descarga Automática del Modelo
El modelo YOLOv8n se descarga automáticamente en la primera ejecución:
- **Modelo**: `yolov8n.pt` (~6MB)
- **Ubicación**: Se descarga en el directorio de trabajo
- **Tiempo**: ~30 segundos en la primera ejecución

## 🎯 Modelos YOLO Disponibles

### YOLOv8 Variants (Recomendados)
| Modelo | Tamaño | Velocidad | Precisión | Uso Recomendado |
|--------|--------|-----------|-----------|-----------------|
| `yolov8n.pt` | 6MB | Muy Rápido | Buena | **MVP/Pruebas** ✅ |
| `yolov8s.pt` | 22MB | Rápido | Mejor | Producción Ligera |
| `yolov8m.pt` | 52MB | Medio | Muy Buena | **Producción** ✅ |
| `yolov8l.pt` | 87MB | Lento | Excelente | Alta Precisión |
| `yolov8x.pt` | 136MB | Muy Lento | Máxima | Investigación |

### Cambiar Modelo
Editar `app/utils/yolo_detector.py`:
```python
# Para mayor precisión (más lento)
self.model = YOLO("yolov8m.pt")

# Para máxima precisión (muy lento)
self.model = YOLO("yolov8x.pt")
```

## 🐾 Especies Detectables

### Clases COCO Soportadas
El modelo preentrenado detecta estas clases de animales:

| Clase ID | Nombre Original | Nombre Local | Confianza Típica |
|----------|----------------|--------------|------------------|
| 15 | bird | ave | 0.6-0.9 |
| 16 | cat | felino | 0.7-0.95 |
| 17 | dog | canino | 0.8-0.95 |
| 18 | horse | caballo | 0.8-0.9 |
| 19 | sheep | oveja | 0.7-0.9 |
| 20 | cow | bovino | 0.8-0.95 |
| 21 | elephant | elefante | 0.9-0.98 |
| 22 | bear | oso | 0.7-0.9 |
| 23 | zebra | cebra | 0.8-0.95 |
| 24 | giraffe | jirafa | 0.9-0.95 |

### Personalizar Nombres de Especies
Editar `species_mapping` en `app/utils/yolo_detector.py`:
```python
self.species_mapping = {
    'bird': 'ave_tropical',
    'cat': 'jaguar',  # Mapear gatos a jaguares
    'dog': 'lobo',    # Mapear perros a lobos
    'bear': 'oso_andino',
    # Agregar más mapeos según la fauna local
}
```

## ⚙️ Configuración de Detección

### Parámetros Principales

#### 1. Umbral de Confianza
```python
# Configuración conservadora (menos falsos positivos)
confidence_threshold = 0.7

# Configuración sensible (más detecciones)
confidence_threshold = 0.3

# Configuración balanceada (recomendada)
confidence_threshold = 0.5
```

#### 2. Intervalo de Frames
```python
# Análisis intensivo (cada segundo)
interval_seconds = 1

# Análisis balanceado (cada 5 segundos) - RECOMENDADO
interval_seconds = 5

# Análisis ligero (cada 10 segundos)
interval_seconds = 10
```

### Configuración Avanzada

#### Filtros Adicionales por Tamaño
Editar `detect_animals()` en `yolo_detector.py`:
```python
def detect_animals(self, frame, confidence_threshold=0.5):
    # ... código existente ...
    
    for box in boxes:
        # Filtrar por tamaño mínimo del bounding box
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        # Filtrar objetos muy pequeños (posibles falsos positivos)
        if area < 1000:  # píxeles cuadrados
            continue
            
        # ... resto del código ...
```

#### Filtros por Relación de Aspecto
```python
# Filtrar formas muy alargadas (posibles objetos no animales)
aspect_ratio = width / height
if aspect_ratio > 5 or aspect_ratio < 0.2:
    continue
```

## 🚀 Optimización de Rendimiento

### 1. Configuración de Hardware

#### CPU
```python
# Usar múltiples cores
import torch
torch.set_num_threads(4)  # Ajustar según CPU
```

#### GPU (Si está disponible)
```python
# Verificar GPU automáticamente
device = 'cuda' if torch.cuda.is_available() else 'cpu'
self.model = YOLO("yolov8n.pt").to(device)
```

### 2. Optimización de Memoria
```python
# Procesar frames en lotes más pequeños
def process_video_optimized(self, video_path, batch_size=10):
    frames = self.extract_frames(video_path)
    
    for i in range(0, len(frames), batch_size):
        batch = frames[i:i+batch_size]
        # Procesar lote
        for frame_data in batch:
            # ... procesamiento ...
```

### 3. Configuración de Calidad vs Velocidad

#### Configuración Rápida (Para pruebas)
```python
# Modelo pequeño + intervalos grandes + confianza alta
model = "yolov8n.pt"
interval_seconds = 10
confidence_threshold = 0.7
```

#### Configuración Balanceada (Producción)
```python
# Modelo medio + intervalos medios + confianza media
model = "yolov8m.pt"
interval_seconds = 5
confidence_threshold = 0.5
```

#### Configuración Precisa (Investigación)
```python
# Modelo grande + intervalos pequeños + confianza baja
model = "yolov8l.pt"
interval_seconds = 2
confidence_threshold = 0.3
```

## 🔧 Configuración Personalizada

### 1. Modelo Personalizado para Fauna Local

#### Entrenar Modelo Específico
```python
# Para entrenar con fauna específica (requiere dataset)
from ultralytics import YOLO

# Cargar modelo preentrenado
model = YOLO('yolov8n.pt')

# Entrenar con dataset personalizado
model.train(
    data='fauna_local.yaml',  # Configuración del dataset
    epochs=100,
    imgsz=640,
    batch=16
)
```

#### Estructura del Dataset
```yaml
# fauna_local.yaml
path: ./dataset
train: images/train
val: images/val

names:
  0: jaguar
  1: puma
  2: venado
  3: tapir
  4: mono_aullador
  5: tucán
```

### 2. Configuración Multi-Modelo
```python
class MultiModelDetector:
    def __init__(self):
        # Modelo general para animales comunes
        self.general_model = YOLO("yolov8m.pt")
        
        # Modelo específico para fauna local (si existe)
        self.local_model = YOLO("fauna_local.pt")
    
    def detect_animals(self, frame):
        # Usar ambos modelos y combinar resultados
        general_detections = self.general_model(frame)
        local_detections = self.local_model(frame)
        
        # Combinar y filtrar duplicados
        return self.merge_detections(general_detections, local_detections)
```

## 📊 Monitoreo y Métricas

### 1. Métricas de Rendimiento
```python
import time

class PerformanceMonitor:
    def __init__(self):
        self.stats = {
            'total_frames': 0,
            'total_detections': 0,
            'processing_time': 0,
            'fps': 0
        }
    
    def log_processing(self, frames_processed, detections, time_taken):
        self.stats['total_frames'] += frames_processed
        self.stats['total_detections'] += detections
        self.stats['processing_time'] += time_taken
        self.stats['fps'] = self.stats['total_frames'] / self.stats['processing_time']
```

### 2. Logging Detallado
```python
import logging

# Configurar logging específico para YOLO
yolo_logger = logging.getLogger('yolo_detector')
yolo_logger.setLevel(logging.DEBUG)

# Log cada detección
yolo_logger.info(f"Detectado: {species} (confianza: {confidence:.3f})")
```

## 🐛 Solución de Problemas

### Error: "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### Error: "Model download failed"
```bash
# Descargar manualmente
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Error: "CUDA out of memory"
```python
# Reducir tamaño de imagen
results = self.model(frame, imgsz=320)  # En lugar de 640

# O usar CPU
device = 'cpu'
```

### Detecciones Incorrectas
```python
# Aumentar umbral de confianza
confidence_threshold = 0.8

# Filtrar por tamaño
min_area = 2000  # píxeles cuadrados

# Verificar calidad del video
# Videos borrosos o con poca luz reducen precisión
```

### Rendimiento Lento
```python
# Usar modelo más pequeño
model = "yolov8n.pt"

# Aumentar intervalo entre frames
interval_seconds = 10

# Reducir resolución
results = self.model(frame, imgsz=416)
```

## 📈 Benchmarks de Rendimiento

### Hardware de Referencia
- **CPU**: Intel i5-8400 / AMD Ryzen 5 3600
- **RAM**: 8GB
- **GPU**: GTX 1060 / RTX 3060 (opcional)

### Tiempos Esperados (Video 1 minuto, 30 FPS)

| Modelo | Intervalo | Frames | Tiempo CPU | Tiempo GPU |
|--------|-----------|--------|------------|------------|
| yolov8n | 5s | 12 | 15s | 5s |
| yolov8s | 5s | 12 | 25s | 8s |
| yolov8m | 5s | 12 | 45s | 12s |
| yolov8l | 5s | 12 | 80s | 20s |

### Recomendaciones por Uso

#### Desarrollo/Pruebas
- **Modelo**: yolov8n.pt
- **Intervalo**: 10 segundos
- **Confianza**: 0.6

#### Producción Ligera
- **Modelo**: yolov8s.pt
- **Intervalo**: 5 segundos
- **Confianza**: 0.5

#### Producción Estándar
- **Modelo**: yolov8m.pt
- **Intervalo**: 3 segundos
- **Confianza**: 0.5

#### Alta Precisión
- **Modelo**: yolov8l.pt
- **Intervalo**: 2 segundos
- **Confianza**: 0.4