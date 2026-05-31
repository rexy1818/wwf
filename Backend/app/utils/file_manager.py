import os
import json
from pathlib import Path
from typing import Dict, Any

class FileManager:
    def __init__(self, base_path: str = "storage"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_camera_structure(self, camera_id: str) -> str:
        """Crear estructura de directorios para una cámara"""
        camera_path = self.base_path / camera_id
        
        # Crear directorios
        directories = ["videos", "resultados", "evidencias", "excel", "metadata"]
        for directory in directories:
            (camera_path / directory).mkdir(parents=True, exist_ok=True)
        
        return str(camera_path)
    
    def save_camera_metadata(self, camera_id: str, metadata: Dict[str, Any]) -> None:
        """Guardar metadatos de la cámara"""
        metadata_path = self.base_path / camera_id / "metadata" / "camera_info.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    
    def get_camera_metadata(self, camera_id: str) -> Dict[str, Any]:
        """Obtener metadatos de la cámara"""
        metadata_path = self.base_path / camera_id / "metadata" / "camera_info.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_videos_path(self, camera_id: str) -> Path:
        """Obtener ruta de videos de una cámara"""
        return self.base_path / camera_id / "videos"
    
    def get_evidencias_path(self, camera_id: str) -> Path:
        """Obtener ruta de evidencias de una cámara"""
        return self.base_path / camera_id / "evidencias"
    
    def get_excel_path(self, camera_id: str) -> Path:
        """Obtener ruta de excel de una cámara"""
        return self.base_path / camera_id / "excel"
    
    def create_species_directory(self, camera_id: str, species: str) -> Path:
        """Crear directorio para una especie específica"""
        species_path = self.get_evidencias_path(camera_id) / species
        species_path.mkdir(parents=True, exist_ok=True)
        return species_path
    
    def list_cameras(self) -> list:
        """Listar todas las cámaras disponibles"""
        cameras = []
        for item in self.base_path.iterdir():
            if item.is_dir() and (item / "metadata" / "camera_info.json").exists():
                cameras.append(item.name)
        return cameras