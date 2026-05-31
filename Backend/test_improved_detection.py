#!/usr/bin/env python3
"""
Script para probar el detector YOLO mejorado vs el original
"""
import sys
import os
sys.path.append('.')

from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.yolo_detector import YOLODetector
from app.utils.video_metadata import VideoMetadataExtractor
from pathlib import Path
import cv2
import time

def test_improved_vs_original():
    """Comparar detector original vs mejorado"""
    
    print("🔬 COMPARANDO DETECTORES YOLO")
    print("="*50)
    
    # Video que detectó incorrectamente "cebra" en lugar de "jaguar"
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.26 (1).mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video no encontrado: {video_path}")
        return
    
    print(f"📹 Analizando: {Path(video_path).name}")
    
    # Extraer metadatos
    metadata_extractor = VideoMetadataExtractor()
    metadata = metadata_extractor.extract_metadata(video_path)
    
    print(f"📊 Duración: {metadata.get('duration', 0):.1f}s")
    print(f"📐 Resolución: {metadata.get('width')}x{metadata.get('height')}")
    
    # Inicializar detectores
    print("\n🤖 Inicializando detectores...")
    original_detector = YOLODetector()
    improved_detector = ImprovedYOLODetector()
    
    # Crear directorios de salida
    output_original = Path("test_results/original")
    output_improved = Path("test_results/improved")
    output_original.mkdir(parents=True, exist_ok=True)
    output_improved.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*50)
    print("🔍 DETECTOR ORIGINAL")
    print("="*50)
    
    start_time = time.time()
    
    # Extraer frames con método original
    original_frames = original_detector.extract_frames(video_path, interval_seconds=5)
    print(f"📊 Frames extraídos (original): {len(original_frames)}")
    
    original_detections = []
    for frame, frame_num, timestamp in original_frames:
        detections = original_detector.detect_animals(frame, confidence_threshold=0.5)
        for detection in detections:
            detection['frame_number'] = frame_num
            detection['timestamp'] = timestamp
            detection['frame'] = frame
            original_detections.append(detection)
    
    original_time = time.time() - start_time
    
    print(f"⏱️ Tiempo de procesamiento: {original_time:.2f}s")
    print(f"🐾 Detecciones encontradas: {len(original_detections)}")
    
    for i, det in enumerate(original_detections):
        print(f"   {i+1}. {det['species']} - Confianza: {det['confidence']:.3f} "
              f"(Frame: {det['frame_number']}, t={det['timestamp']:.1f}s)")
    
    print("\n" + "="*50)
    print("🚀 DETECTOR MEJORADO")
    print("="*50)
    
    start_time = time.time()
    
    # Extraer frames con método mejorado
    improved_frames = improved_detector.extract_frames_around_detections(video_path, initial_interval=3)
    print(f"📊 Frames extraídos (mejorado): {len(improved_frames)}")
    
    # Analizar con detector mejorado
    all_detections = []
    for frame, frame_num, timestamp in improved_frames:
        detections = improved_detector.detect_animals_enhanced(frame, confidence_threshold=0.4)
        if detections:
            all_detections.append((frame, frame_num, timestamp, detections))
    
    # Seleccionar mejores detecciones
    if all_detections:
        best_detections = improved_detector.select_best_detections(all_detections)
    else:
        best_detections = []
    
    improved_time = time.time() - start_time
    
    print(f"⏱️ Tiempo de procesamiento: {improved_time:.2f}s")
    print(f"🔍 Frames con detecciones: {len(all_detections)}")
    print(f"🏆 Mejores detecciones seleccionadas: {len(best_detections)}")
    
    for i, det in enumerate(best_detections):
        print(f"   {i+1}. {det['species']} - Confianza: {det['confidence']:.3f} "
              f"(Ajustada: {det['adjusted_confidence']:.3f}, Calidad: {det['quality_score']:.3f})")
        print(f"      Frame: {det['frame_number']}, t={det['timestamp']:.1f}s, Área: {det['area']:.0f}px²")
    
    print("\n" + "="*50)
    print("📊 COMPARACIÓN DE RESULTADOS")
    print("="*50)
    
    print(f"⏱️ Tiempo:")
    print(f"   Original: {original_time:.2f}s")
    print(f"   Mejorado: {improved_time:.2f}s")
    print(f"   Diferencia: {improved_time - original_time:+.2f}s")
    
    print(f"\n📊 Frames procesados:")
    print(f"   Original: {len(original_frames)}")
    print(f"   Mejorado: {len(improved_frames)}")
    
    print(f"\n🐾 Detecciones:")
    print(f"   Original: {len(original_detections)}")
    print(f"   Mejorado: {len(best_detections)}")
    
    # Comparar especies detectadas
    original_species = set(det['species'] for det in original_detections)
    improved_species = set(det['species'] for det in best_detections)
    
    print(f"\n🦎 Especies detectadas:")
    print(f"   Original: {', '.join(original_species) if original_species else 'Ninguna'}")
    print(f"   Mejorado: {', '.join(improved_species) if improved_species else 'Ninguna'}")
    
    if original_species != improved_species:
        print(f"   ⚠️ DIFERENCIAS DETECTADAS:")
        only_original = original_species - improved_species
        only_improved = improved_species - original_species
        
        if only_original:
            print(f"      Solo en original: {', '.join(only_original)}")
        if only_improved:
            print(f"      Solo en mejorado: {', '.join(only_improved)}")
    
    # Guardar evidencias para comparación visual
    print(f"\n💾 Guardando evidencias para comparación...")
    
    # Guardar evidencias del detector original
    for i, det in enumerate(original_detections):
        species = det['species']
        frame = det['frame']
        
        species_dir = output_original / species
        species_dir.mkdir(exist_ok=True)
        
        # Extraer ROI simple
        x1, y1, x2, y2 = det['bbox']
        roi = frame[y1:y2, x1:x2]
        
        filename = f"original_{species}_{i+1}_conf_{det['confidence']:.3f}.jpg"
        cv2.imwrite(str(species_dir / filename), roi)
    
    # Guardar evidencias del detector mejorado
    for i, det in enumerate(best_detections):
        species = det['species']
        
        species_dir = output_improved / species
        species_dir.mkdir(exist_ok=True)
        
        filename = f"improved_{species}_{i+1}_conf_{det['confidence']:.3f}_qual_{det['quality_score']:.3f}.jpg"
        improved_detector.save_enhanced_evidence(det, species_dir, filename)
    
    print(f"   📁 Evidencias originales: test_results/original/")
    print(f"   📁 Evidencias mejoradas: test_results/improved/")
    
    print("\n" + "="*50)
    print("🎯 ANÁLISIS DE PRECISIÓN")
    print("="*50)
    
    # Análisis específico para el caso cebra vs jaguar
    if 'cebra' in original_species:
        print("⚠️ DETECTOR ORIGINAL detectó CEBRA")
        cebra_detection = next(det for det in original_detections if det['species'] == 'cebra')
        print(f"   Confianza: {cebra_detection['confidence']:.3f}")
        print(f"   Área: {cebra_detection.get('area', 'N/A')} píxeles²")
        
        if 'felino' in improved_species:
            print("✅ DETECTOR MEJORADO detectó FELINO (más probable para jaguar)")
            felino_detection = next(det for det in best_detections if det['species'] == 'felino')
            print(f"   Confianza: {felino_detection['confidence']:.3f}")
            print(f"   Confianza ajustada: {felino_detection['adjusted_confidence']:.3f}")
            print(f"   Calidad: {felino_detection['quality_score']:.3f}")
            print(f"   Área: {felino_detection.get('area', 'N/A')} píxeles²")
            
            print("\n🔍 RECOMENDACIÓN:")
            print("   El detector mejorado parece más preciso al identificar")
            print("   la cola del jaguar como 'felino' en lugar de 'cebra'.")
        else:
            print("❓ DETECTOR MEJORADO no detectó felino")
    
    print("\n" + "="*60)
    print("🎉 COMPARACIÓN COMPLETADA")
    print("="*60)
    print("📋 Revisa las imágenes en test_results/ para comparación visual")

def analyze_detection_frames():
    """Analizar frames específicos donde se detectó la 'cebra'"""
    
    print("\n🔬 ANÁLISIS DETALLADO DE FRAMES")
    print("="*50)
    
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.26 (1).mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video no encontrado: {video_path}")
        return
    
    # Abrir video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📹 Video: {fps:.1f} FPS, {total_frames} frames totales")
    
    # Inicializar detector mejorado
    detector = ImprovedYOLODetector()
    
    # Analizar frame por frame en los primeros 10 segundos
    analysis_frames = []
    for second in range(0, min(10, int(total_frames/fps))):
        frame_num = int(second * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if ret:
            detections = detector.detect_animals_enhanced(frame, confidence_threshold=0.3)
            if detections:
                analysis_frames.append((second, frame_num, frame, detections))
    
    cap.release()
    
    print(f"🔍 Frames con detecciones: {len(analysis_frames)}")
    
    for second, frame_num, frame, detections in analysis_frames:
        print(f"\n⏰ Segundo {second} (Frame {frame_num}):")
        
        for i, det in enumerate(detections):
            print(f"   {i+1}. {det['species']} - Conf: {det['confidence']:.3f}, "
                  f"Calidad: {det['quality_score']:.3f}")
            print(f"      Bbox: {det['bbox']}, Área: {det['area']:.0f}px²")
            
            # Guardar frame para inspección manual
            output_dir = Path("test_results/frame_analysis")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"frame_{second}s_{det['species']}_conf_{det['confidence']:.3f}.jpg"
            cv2.imwrite(str(output_dir / filename), frame)
    
    print(f"\n📁 Frames guardados en: test_results/frame_analysis/")

if __name__ == "__main__":
    print("🎬 PRUEBA DE DETECTOR YOLO MEJORADO")
    print("="*60)
    
    try:
        test_improved_vs_original()
        analyze_detection_frames()
        
        print("\n🎯 CONCLUSIONES:")
        print("1. Revisa las imágenes en test_results/ para comparar visualmente")
        print("2. El detector mejorado debería ser más preciso en la identificación")
        print("3. La selección de frames mejorada debería capturar mejores evidencias")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()