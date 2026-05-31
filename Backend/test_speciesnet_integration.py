import sys
import os
import logging
from pathlib import Path
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Asegurar que el path del proyecto esté disponible
sys.path.append('.')

from app.utils.improved_yolo_detector import ImprovedYOLODetector
from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer

def test_integration():
    print("🔬 TEST DE INTEGRACIÓN: GOOGLE SPECIESNET ENSEMBLE")
    print("="*60)
    
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.25 (1).mp4"
    if not Path(video_path).exists():
        # Buscar cualquier video en camara-1
        videos = list(Path("camara-1").glob("*.mp4"))
        if not videos:
            print("❌ No se encontraron videos para probar.")
            return
        video_path = str(videos[0])
    
    print(f"📹 Video de prueba: {video_path}")
    
    # 1. Probar Detector Directamente
    print("\n🤖 1. Probando ImprovedYOLODetector (SpeciesNet)...")
    try:
        detector = ImprovedYOLODetector()
        if not detector.model:
            print("❌ El modelo SpeciesNet no se cargó correctamente.")
            return
            
        detections = detector.process_video_enhanced(video_path, "video_analysis/test_output")
        print(f"✅ Detecciones crudas encontradas: {len(detections)}")
        for i, det in enumerate(detections[:5]):
            print(f"   {i+1}. {det['species']} (Conf: {det['confianza']:.3f}) en t={det['timestamp_video']:.2f}s")
    except Exception as e:
        print(f"❌ Error en detector: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Probar Analizador Completo
    print("\n🧠 2. Probando EnhancedVideoAnalyzer (Pipeline Completo)...")
    try:
        analyzer = EnhancedVideoAnalyzer()
        result = analyzer.analyze_video_smart(video_path, "video_analysis/test_analysis", video_id="test_speciesnet")
        
        print(f"✅ Análisis completado con éxito.")
        print(f"📊 Estadísticas: {json.dumps(result.get('estadisticas'), indent=2)}")
        
        # Verificar evidencias en Resultados
        print("\n📂 Verificando evidencias guardadas:")
        resultados_dir = Path("Resultados")
        for cam_dir in resultados_dir.iterdir():
            if cam_dir.is_dir():
                for sp_dir in cam_dir.iterdir():
                    if sp_dir.is_dir():
                        files = list(sp_dir.glob("*.jpg"))
                        print(f"   🐾 {sp_dir.name}: {len(files)} fotos")
                        for f in files[:2]:
                            print(f"      - {f.name}")
                            
    except Exception as e:
        print(f"❌ Error en analizador: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()
