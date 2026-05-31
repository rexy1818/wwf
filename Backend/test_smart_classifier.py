#!/usr/bin/env python3
"""
Script para probar el clasificador inteligente de especies
"""
import sys
import os
sys.path.append('.')

from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.smart_species_classifier import SmartSpeciesClassifier
from pathlib import Path
import cv2
import json
import numpy as np

def test_smart_classification():
    """Probar el clasificador inteligente en el video problemático"""
    
    print("🧠 PROBANDO CLASIFICADOR INTELIGENTE DE ESPECIES")
    print("="*60)
    
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.26 (1).mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video no encontrado: {video_path}")
        return
    
    print(f"📹 Analizando: {Path(video_path).name}")
    
    # Inicializar componentes
    detector = ImprovedYOLODetector()
    classifier = SmartSpeciesClassifier()
    
    # Extraer frames con detecciones
    frames = detector.extract_frames_around_detections(video_path, initial_interval=3)
    print(f"📊 Frames extraídos: {len(frames)}")
    
    # Analizar cada frame
    all_detections = []
    
    for frame, frame_num, timestamp in frames:
        # Detectar con YOLO
        yolo_detections = detector.detect_animals_enhanced(frame, confidence_threshold=0.4)
        
        if yolo_detections:
            print(f"\n⏰ Frame {frame_num} (t={timestamp:.1f}s):")
            
            for detection in yolo_detections:
                print(f"   🔍 YOLO detectó: {detection['species']} (conf: {detection['confidence']:.3f})")
                
                # Aplicar clasificación inteligente
                smart_detection = classifier.classify_species_intelligently(detection, frame)
                
                # Mostrar resultado
                if smart_detection['correction_applied']:
                    print(f"   🧠 CORRECCIÓN: {smart_detection['original_species']} -> {smart_detection['corrected_species']}")
                    print(f"      Confianza: {smart_detection['original_confidence']:.3f} -> {smart_detection['confidence']:.3f}")
                else:
                    print(f"   ✅ CONFIRMADO: {smart_detection['species']} (conf: {smart_detection['confidence']:.3f})")
                
                # Mostrar análisis visual
                patterns = smart_detection.get('visual_patterns', {})
                if patterns:
                    print(f"      📊 Análisis visual:")
                    print(f"         Rayas: {patterns.get('stripe_intensity', 0):.3f}")
                    print(f"         Manchas: {patterns.get('spot_intensity', 0):.3f}")
                    
                    colors = patterns.get('color_analysis', {})
                    if colors:
                        print(f"         Blanco-Negro: {colors.get('black_white', 0):.3f}")
                        print(f"         Amarillo-Marrón: {colors.get('yellow_brown', 0):.3f}")
                
                # Agregar contexto temporal
                smart_detection['frame_number'] = frame_num
                smart_detection['timestamp'] = timestamp
                smart_detection['frame'] = frame
                
                all_detections.append(smart_detection)
    
    if not all_detections:
        print("❌ No se encontraron detecciones")
        return
    
    print(f"\n📊 RESUMEN DE DETECCIONES:")
    print(f"   Total detecciones: {len(all_detections)}")
    
    # Agrupar por especie
    species_count = {}
    corrections_count = 0
    
    for detection in all_detections:
        species = detection['species']
        species_count[species] = species_count.get(species, 0) + 1
        
        if detection['correction_applied']:
            corrections_count += 1
    
    print(f"   Correcciones aplicadas: {corrections_count}")
    print(f"   Especies detectadas:")
    for species, count in species_count.items():
        print(f"      • {species}: {count}")
    
    # Validar en contexto
    print(f"\n🔍 VALIDACIÓN CONTEXTUAL:")
    validated_detections = classifier.validate_detection_context(all_detections)
    
    print(f"   Detecciones validadas: {len(validated_detections)}")
    
    # Seleccionar mejores detecciones
    best_detections = detector.select_best_detections([
        (det['frame'], det['frame_number'], det['timestamp'], [det]) 
        for det in validated_detections
    ])
    
    print(f"   Mejores detecciones: {len(best_detections)}")
    
    # Guardar resultados
    output_dir = Path("test_results/smart_classification")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 GUARDANDO RESULTADOS:")
    
    for i, detection in enumerate(best_detections):
        species = detection['species']
        frame_num = detection['frame_number']
        confidence = detection['confidence']
        
        # Crear directorio por especie
        species_dir = output_dir / species
        species_dir.mkdir(exist_ok=True)
        
        # Guardar evidencia mejorada
        filename = f"smart_{species}_{i+1}_frame_{frame_num}_conf_{confidence:.3f}.jpg"
        evidence_path = detector.save_enhanced_evidence(detection, species_dir, filename)
        
        print(f"   📸 {filename}")
        
        # Función auxiliar para convertir numpy types a tipos nativos de Python
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            else:
                return obj
        
        # Guardar análisis detallado en JSON
        analysis_data = {
            'species': detection['species'],
            'original_species': detection.get('original_species'),
            'confidence': float(detection['confidence']),
            'original_confidence': float(detection.get('original_confidence', 0)),
            'correction_applied': detection.get('correction_applied', False),
            'visual_patterns': convert_numpy_types(detection.get('visual_patterns', {})),
            'regional_multiplier': float(detection.get('regional_multiplier', 1.0)),
            'frame_number': int(detection['frame_number']),
            'timestamp': float(detection['timestamp']),
            'bbox': [int(x) for x in detection['bbox']]
        }
        
        json_filename = filename.replace('.jpg', '_analysis.json')
        with open(species_dir / json_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Resultados guardados en: {output_dir}")
    
    # Análisis final
    print(f"\n🎯 ANÁLISIS FINAL:")
    
    original_species = set(det.get('original_species', det['species']) for det in best_detections)
    final_species = set(det['species'] for det in best_detections)
    
    print(f"   Especies originales (YOLO): {', '.join(original_species)}")
    print(f"   Especies finales (Smart): {', '.join(final_species)}")
    
    if original_species != final_species:
        print(f"   🎉 MEJORA DETECTADA:")
        
        for detection in best_detections:
            if detection.get('correction_applied'):
                orig = detection.get('original_species')
                final = detection['species']
                orig_conf = detection.get('original_confidence', 0)
                final_conf = detection['confidence']
                
                print(f"      {orig} ({orig_conf:.3f}) -> {final} ({final_conf:.3f})")
                
                # Justificación de la corrección
                patterns = detection.get('visual_patterns', {})
                if patterns:
                    stripe_int = patterns.get('stripe_intensity', 0)
                    spot_int = patterns.get('spot_intensity', 0)
                    
                    if orig == 'cebra' and final == 'felino':
                        print(f"         Justificación: Rayas débiles ({stripe_int:.3f}), "
                              f"manchas presentes ({spot_int:.3f})")
                        print(f"         Contexto: Cebras improbables en América Latina")
    else:
        print(f"   ℹ️ No se aplicaron correcciones significativas")
    
    print(f"\n" + "="*60)
    print(f"🎉 ANÁLISIS COMPLETADO")
    print(f"="*60)

def compare_all_methods():
    """Comparar todos los métodos: Original, Mejorado, Smart"""
    
    print("\n🏆 COMPARACIÓN COMPLETA DE MÉTODOS")
    print("="*60)
    
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.26 (1).mp4"
    
    if not Path(video_path).exists():
        print(f"❌ Video no encontrado: {video_path}")
        return
    
    from app.utils.yolo_detector import YOLODetector
    
    # Inicializar todos los detectores
    original_detector = YOLODetector()
    improved_detector = ImprovedYOLODetector()
    smart_classifier = SmartSpeciesClassifier()
    
    methods = {
        'Original': original_detector,
        'Mejorado': improved_detector,
        'Smart': (improved_detector, smart_classifier)
    }
    
    results = {}
    
    for method_name, detector in methods.items():
        print(f"\n🔍 Método: {method_name}")
        print("-" * 30)
        
        if method_name == 'Smart':
            # Método especial que combina detector mejorado + clasificador
            improved_det, classifier = detector
            
            frames = improved_det.extract_frames_around_detections(video_path)
            all_detections = []
            
            for frame, frame_num, timestamp in frames:
                yolo_dets = improved_det.detect_animals_enhanced(frame, confidence_threshold=0.4)
                
                for det in yolo_dets:
                    smart_det = classifier.classify_species_intelligently(det, frame)
                    smart_det['frame_number'] = frame_num
                    smart_det['timestamp'] = timestamp
                    all_detections.append(smart_det)
            
            validated = classifier.validate_detection_context(all_detections)
            final_detections = validated
            
        elif method_name == 'Mejorado':
            frames = detector.extract_frames_around_detections(video_path)
            all_detections = []
            
            for frame, frame_num, timestamp in frames:
                dets = detector.detect_animals_enhanced(frame, confidence_threshold=0.4)
                for det in dets:
                    det['frame_number'] = frame_num
                    det['timestamp'] = timestamp
                    all_detections.append(det)
            
            final_detections = all_detections
            
        else:  # Original
            frames = detector.extract_frames(video_path, interval_seconds=5)
            final_detections = []
            
            for frame, frame_num, timestamp in frames:
                dets = detector.detect_animals(frame, confidence_threshold=0.5)
                for det in dets:
                    det['frame_number'] = frame_num
                    det['timestamp'] = timestamp
                    final_detections.append(det)
        
        # Resumir resultados
        species_found = set(det['species'] for det in final_detections)
        avg_confidence = sum(det['confidence'] for det in final_detections) / len(final_detections) if final_detections else 0
        
        results[method_name] = {
            'detections': len(final_detections),
            'species': species_found,
            'avg_confidence': avg_confidence,
            'details': final_detections
        }
        
        print(f"   Detecciones: {len(final_detections)}")
        print(f"   Especies: {', '.join(species_found) if species_found else 'Ninguna'}")
        print(f"   Confianza promedio: {avg_confidence:.3f}")
    
    # Comparación final
    print(f"\n📊 TABLA COMPARATIVA:")
    print(f"{'Método':<12} {'Detecciones':<12} {'Especies':<20} {'Confianza':<10}")
    print("-" * 60)
    
    for method, result in results.items():
        species_str = ', '.join(result['species']) if result['species'] else 'Ninguna'
        if len(species_str) > 18:
            species_str = species_str[:15] + "..."
        
        print(f"{method:<12} {result['detections']:<12} {species_str:<20} {result['avg_confidence']:<10.3f}")
    
    # Recomendación
    print(f"\n🎯 RECOMENDACIÓN:")
    
    smart_species = results.get('Smart', {}).get('species', set())
    original_species = results.get('Original', {}).get('species', set())
    
    if 'felino' in smart_species and 'cebra' in original_species:
        print("   ✅ El método SMART corrigió exitosamente la detección")
        print("   ✅ 'Cebra' -> 'Felino' es más probable para fauna de América Latina")
        print("   ✅ Recomendado usar el clasificador inteligente")
    elif smart_species == original_species:
        print("   ℹ️ Todos los métodos coinciden en las especies detectadas")
        print("   ℹ️ El método original puede ser suficiente para este caso")
    else:
        print("   ⚠️ Hay discrepancias entre métodos")
        print("   ⚠️ Revisar manualmente las evidencias generadas")

if __name__ == "__main__":
    try:
        test_smart_classification()
        compare_all_methods()
        
        print(f"\n📋 PRÓXIMOS PASOS:")
        print("1. Revisar las imágenes en test_results/smart_classification/")
        print("2. Verificar los archivos JSON con análisis detallado")
        print("3. Comparar visualmente las evidencias de cada método")
        print("4. Integrar el clasificador inteligente en la API principal")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()