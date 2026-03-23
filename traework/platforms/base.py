from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from flask import Flask

from traework.core.config import config
from traework.core.logger import get_logger

logger = get_logger('base_platform')


class BasePlatform(ABC):
    PLATFORM_ID: str = ""
    PLATFORM_NAME: str = ""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self._data_dir = data_dir or config.data_dir / 'data'
        self._app: Optional[Flask] = None
        self._routes: list = []
    
    @property
    def platform_id(self) -> str:
        return self.PLATFORM_ID
    
    @property
    def platform_name(self) -> str:
        return self.PLATFORM_NAME
    
    @property
    def data_dir(self) -> Path:
        return self._data_dir
    
    @property
    def app(self) -> Flask:
        if self._app is None:
            self._app = self.create_app()
            self.register_routes(self._app)
        return self._app
    
    def get_data_file(self, filename: str) -> Path:
        return self._data_dir / filename
    
    def load_data(self, filename: str, default: Any = None) -> Any:
        filepath = self.get_data_file(filename)
        if filepath.exists():
            try:
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
        return default if default is not None else {}
    
    def save_data(self, data: Any, filename: str):
        import json
        filepath = self.get_data_file(filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {filename}")
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
    
    @abstractmethod
    def create_app(self) -> Flask:
        pass
    
    @abstractmethod
    def register_routes(self, app: Flask):
        pass
    
    def get_app(self) -> Flask:
        if self._app is None:
            self._app = self.create_app()
            self.register_routes(self._app)
        return self._app
    
    def ensure_data_dir(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, host: str = '127.0.0.1', port: int = 5000):
        self.ensure_data_dir()
        app = self.get_app()
        app.run(host=host, port=port, threaded=True)
