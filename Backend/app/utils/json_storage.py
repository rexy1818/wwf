import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONStorage:
    def __init__(self, storage_file: str = "cameras_db.json"):
        self.storage_file = Path(storage_file)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Cargar datos desde el archivo JSON"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Datos cargados desde {self.storage_file}")
                    return data
            else:
                logger.info(f"Archivo {self.storage_file} no existe, creando estructura inicial")
                return {
                    "cameras": {},
                    "processing_history": {},
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error cargando datos desde {self.storage_file}: {e}")
            return {
                "cameras": {},
                "processing_history": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_data(self) -> None:
        """Guardar datos al archivo JSON"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            
            # Crear backup del archivo anterior (manejar error de Windows si ya existe)
            if self.storage_file.exists():
                backup_file = self.storage_file.with_suffix('.backup.json')
                if backup_file.exists():
                    backup_file.unlink()
                self.storage_file.rename(backup_file)
            
            # Guardar nuevos datos
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Datos guardados en {self.storage_file}")
        
        except Exception as e:
            logger.error(f"Error guardando datos en {self.storage_file}: {e}")
            raise
    
    def save_camera(self, camera_id: str, camera_data: Dict[str, Any]) -> None:
        """Guardar información de una cámara"""
        try:
            self.data["cameras"][camera_id] = {
                **camera_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self._save_data()
            logger.info(f"Cámara guardada: {camera_id}")
        except Exception as e:
            logger.error(f"Error guardando cámara {camera_id}: {e}")
            raise
    
    def get_camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una cámara"""
        return self.data["cameras"].get(camera_id)
    
    def get_all_cameras(self) -> Dict[str, Any]:
        """Obtener todas las cámaras"""
        return self.data["cameras"]
    
    def update_camera(self, camera_id: str, updates: Dict[str, Any]) -> None:
        """Actualizar información de una cámara"""
        try:
            if camera_id in self.data["cameras"]:
                self.data["cameras"][camera_id].update(updates)
                self.data["cameras"][camera_id]["updated_at"] = datetime.now().isoformat()
                self._save_data()
                logger.info(f"Cámara actualizada: {camera_id}")
            else:
                raise ValueError(f"Cámara no encontrada: {camera_id}")
        except Exception as e:
            logger.error(f"Error actualizando cámara {camera_id}: {e}")
            raise
    
    def delete_camera(self, camera_id: str) -> bool:
        """Eliminar una cámara"""
        try:
            if camera_id in self.data["cameras"]:
                del self.data["cameras"][camera_id]
                self._save_data()
                logger.info(f"Cámara eliminada: {camera_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error eliminando cámara {camera_id}: {e}")
            raise
    
    def save_processing_result(self, camera_id: str, processing_data: Dict[str, Any]) -> None:
        """Guardar resultado de procesamiento"""
        try:
            if camera_id not in self.data["processing_history"]:
                self.data["processing_history"][camera_id] = []
            
            processing_record = {
                **processing_data,
                "processed_at": datetime.now().isoformat()
            }
            
            self.data["processing_history"][camera_id].append(processing_record)
            
            # Mantener solo los últimos 10 procesamientos por cámara
            if len(self.data["processing_history"][camera_id]) > 10:
                self.data["processing_history"][camera_id] = self.data["processing_history"][camera_id][-10:]
            
            self._save_data()
            logger.info(f"Resultado de procesamiento guardado para cámara: {camera_id}")
        except Exception as e:
            logger.error(f"Error guardando resultado de procesamiento para {camera_id}: {e}")
            raise
    
    def get_processing_history(self, camera_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de procesamientos de una cámara"""
        return self.data["processing_history"].get(camera_id, [])
    
    def get_latest_processing(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Obtener el último procesamiento de una cámara"""
        history = self.get_processing_history(camera_id)
        return history[-1] if history else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales"""
        total_cameras = len(self.data["cameras"])
        total_processings = sum(len(history) for history in self.data["processing_history"].values())
        
        # Calcular total de detecciones
        total_detections = 0
        for camera_id, history in self.data["processing_history"].items():
            for processing in history:
                total_detections += processing.get("animales_detectados", 0)
        
        return {
            "total_cameras": total_cameras,
            "total_processings": total_processings,
            "total_detections": total_detections,
            "created_at": self.data.get("created_at"),
            "last_updated": self.data.get("last_updated")
        }
    
    def export_data(self, export_file: str) -> None:
        """Exportar todos los datos a un archivo"""
        try:
            export_path = Path(export_file)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Datos exportados a {export_file}")
        except Exception as e:
            logger.error(f"Error exportando datos a {export_file}: {e}")
            raise

# Instancia global del almacenamiento
json_storage = JSONStorage()