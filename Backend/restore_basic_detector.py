import shutil
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
