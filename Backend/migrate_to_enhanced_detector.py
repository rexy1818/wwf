import os
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    logger.info("🚀 INICIANDO MIGRACIÓN AL DETECTOR MEJORADO v2.0")
    logger.info("============================================================")
    
    # 1. Crear backup
    backup_dir = Path("backup_basic_detector")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "app/utils/video_analyzer.py",
        "app/services/video_analysis_service.py",
        "app/services/processing_service.py"
    ]
    
    logger.info("📦 Creando backup del sistema actual...")
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_dir / os.path.basename(file_path))
            logger.info(f"   ✅ Backup: {file_path}")
    
    # 2. Verificar archivos nuevos
    logger.info("🔍 Verificando archivos del detector mejorado...")
    new_files = [
        "app/utils/enhanced_video_analyzer.py",
        "app/utils/improved_yolo_detector.py",
        "app/utils/smart_species_classifier.py"
    ]
    for file_path in new_files:
        if os.path.exists(file_path):
            logger.info(f"   ✅ Encontrado: {file_path}")
        else:
            logger.error(f"   ❌ NO ENCONTRADO: {file_path}")
            return

    # 3. Aplicar cambios en VideoAnalysisService
    logger.info("🔄 Actualizando VideoAnalysisService...")
    service_path = "app/services/video_analysis_service.py"
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cambiar import y uso de VideoAnalyzer por EnhancedVideoAnalyzer
    content = content.replace(
        "from app.utils.video_analyzer import VideoAnalyzer",
        "from app.utils.enhanced_video_analyzer import EnhancedVideoAnalyzer"
    )
    content = content.replace(
        "self.video_analyzer = VideoAnalyzer()",
        "self.video_analyzer = EnhancedVideoAnalyzer()"
    )
    content = content.replace(
        "self.video_analyzer.analyze_video(",
        "self.video_analyzer.analyze_video_smart("
    )
    
    with open(service_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info("   ✅ VideoAnalysisService actualizado")

    # 4. Crear script de rollback
    logger.info("🔙 Creando script de rollback...")
    with open("restore_basic_detector.py", 'w', encoding='utf-8') as f:
        f.write("""import shutil
import os
from pathlib import Path

backup_dir = Path("backup_basic_detector")
mapping = {
    "video_analyzer.py": "app/utils/video_analyzer.py",
    "video_analysis_service.py": "app/services/video_analysis_service.py",
    "processing_service.py": "app/services/processing_service.py"
}

print("⏪ Restaurando sistema básico...")
for backup_file, target in mapping.items():
    if (backup_dir / backup_file).exists():
        shutil.copy2(backup_dir / backup_file, target)
        print(f"   ✅ Restaurado: {target}")
print("🎉 Sistema restaurado exitosamente.")
""")
    
    logger.info("============================================================")
    logger.info("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
    logger.info("============================================================")

if __name__ == "__main__":
    migrate()
