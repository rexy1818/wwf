import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class JSONStorage:
    """Persistencia ligera para resultados de analisis."""

    def __init__(self, storage_file: str = "cameras_db.json") -> None:
        self.storage_file = Path(storage_file)
        self.data = self._load_data()
        self.data.setdefault("video_analyses", {})
        self.data.setdefault("created_at", datetime.now().isoformat())
        self.data.setdefault("last_updated", datetime.now().isoformat())

    def _load_data(self) -> Dict[str, Any]:
        if not self.storage_file.exists():
            return {
                "video_analyses": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }
        try:
            with open(self.storage_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.error("Error cargando %s: %s", self.storage_file, exc)
            return {
                "video_analyses": {},
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }

    def _save_data(self) -> None:
        self.data["last_updated"] = datetime.now().isoformat()
        if self.storage_file.exists():
            backup_file = self.storage_file.with_suffix(".backup.json")
            if backup_file.exists():
                backup_file.unlink()
            self.storage_file.rename(backup_file)

        with open(self.storage_file, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, ensure_ascii=False, default=str)

        logger.info("Datos guardados en %s", self.storage_file)


json_storage = JSONStorage()
