import sys
import os
import logging
from pathlib import Path
import json
import time

# Configurar logging para ver el progreso
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Asegurar que el path del proyecto esté disponible
sys.path.append('.')

from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer

def run_batch_test():
    print("🚀 INICIANDO PRUEBA POR LOTES: CAMARA-1 (3 VIDEOS)")
    print("="*60)
    
    input_dir = Path("camara-1")
    videos = list(input_dir.glob("*.mp4"))
    
    if not videos:
        print("❌ No se encontraron videos en camara-1")
        return

    print(f"📁 Encontrados {len(videos)} videos. Iniciando analizador profesional...")
    
    analyzer = EnhancedVideoAnalyzer()
    
    all_start_time = time.time()
    batch_results = []

    for i, video_path in enumerate(videos, 1):
        print(f"\n📹 [{i}/{len(videos)}] PROCESANDO: {video_path.name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            # Ejecutar análisis completo
            result = analyzer.analyze_video_smart(
                str(video_path), 
                output_dir="video_analysis/batch_test",
                video_id=f"batch_{i}"
            )
            
            duration = time.time() - start_time
            stats = result.get('estadisticas', {})
            species = stats.get('especies_encontradas', [])
            
            print(f"✅ Completado en {duration:.2f}s")
            print(f"🐾 Especies detectadas: {species if species else 'Ninguna'}")
            print(f"📸 Total animales: {stats.get('total_animales', 0)}")
            
            batch_results.append({
                "video": video_path.name,
                "species": species,
                "count": stats.get('total_animales', 0),
                "camera": result.get('metadata', {}).get('camara_id', 'UNKNOWN')
            })
            
        except Exception as e:
            print(f"❌ Error procesando {video_path.name}: {e}")

    total_duration = time.time() - all_start_time
    
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL DE LA PRUEBA")
    print("="*60)
    print(f"⏱️ Tiempo total: {total_duration:.2f}s")
    
    for res in batch_results:
        print(f"Video: {res['video']}")
        print(f"  └─ Cámara: {res['camera']}")
        print(f"  └─ Hallazgos: {', '.join(res['species']) if res['species'] else 'Nada'}")
    
    print("\n📂 Estructura de Resultados generada:")
    resultados_dir = Path("Resultados")
    for cam_dir in resultados_dir.iterdir():
        if cam_dir.is_dir():
            print(f"📍 Cámara: {cam_dir.name}")
            for sp_dir in cam_dir.iterdir():
                if sp_dir.is_dir():
                    files = list(sp_dir.glob("*.jpg"))
                    print(f"   └─ 🐾 {sp_dir.name}: {len(files)} evidencias")

if __name__ == "__main__":
    run_batch_test()
