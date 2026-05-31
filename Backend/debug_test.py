import cv2
import json
import logging
from pathlib import Path
from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer

# Configurar logs para ver el detalle de la clasificación
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DEBUG_TEST")

def run_diagnostic():
    analyzer = EnhancedVideoAnalyzer()
    video_path = "camara-1/WhatsApp Video 2026-05-30 at 12.38.25 (1).mp4"
    
    print(f"\n🔍 ANALIZANDO VIDEO: {video_path}")
    print("="*60)
    
    # Limpiar antes de la prueba
    analysis_dir = Path("video_analysis/debug_test")
    if analysis_dir.exists():
        import shutil
        shutil.rmtree(analysis_dir)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Ejecutar el análisis
    result = analyzer.analyze_video_smart(video_path, output_dir=str(analysis_dir))
    
    print("\n📊 RESULTADOS FINALES DE DETECCIÓN:")
    print("-" * 40)
    for det in result['detecciones']:
        print(f"🐾 Especie: {det['especie']} | Confianza: {det['confianza']:.3f} | Cuadro: {det['has_bounding_box']} | Tipo: {det.get('photo_type')}")
        if 'biological_traits' in det:
            traits = det['biological_traits']
            print(f"   🧬 Rasgos: Manchas={traits['has_spots']}, Rosetas={traits['has_rosettes']}, Robusto={traits['is_bulky']}")

    # Verificar carpetas en Resultados
    print("\n📁 VERIFICANDO CARPETAS EN RESULTADOS:")
    res_path = Path("Resultados/EST12B")
    if res_path.exists():
        for sp_dir in res_path.iterdir():
            if sp_dir.is_dir():
                files = list(sp_dir.glob("*.jpg"))
                print(f"   📂 {sp_dir.name}: {len(files)} archivos")
    else:
        print("   ❌ No se encontró la carpeta de Resultados para EST12B")

if __name__ == "__main__":
    run_diagnostic()
