import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if Config._initialized:
            return
        Config._initialized = True
        
        self._is_frozen = getattr(sys, 'frozen', False)
        
        if self._is_frozen:
            self._app_dir = Path(sys.executable).parent
            self._data_dir = self._get_user_data_dir()
        else:
            self._app_dir = Path(__file__).parent.parent.parent
            self._data_dir = self._app_dir
        
        self._ensure_data_dirs()
        self._config = self._load_config()
    
    def _get_user_data_dir(self) -> Path:
        if sys.platform == 'win32':
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            data_dir = Path(base) / 'TRAEWORK'
        elif sys.platform == 'darwin':
            data_dir = Path.home() / 'Library' / 'Application Support' / 'TRAEWORK'
        else:
            data_dir = Path.home() / '.traework'
        
        return data_dir
    
    def _ensure_data_dirs(self):
        dirs = [
            self._data_dir,
            self._data_dir / 'data',
            self._data_dir / 'logs',
            self._data_dir / 'cache',
            self._data_dir / 'backups',
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        config_file = self._data_dir / 'config.json'
        default_config = self._get_default_config()
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception:
                pass
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except PermissionError:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        existing_config = json.load(f)
                    default_config.update(existing_config)
                except Exception:
                    pass
        except Exception as e:
            pass
        
        return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        config_file = self._data_dir / 'config.json'
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'app': {
                'name': 'TRAEWORK',
                'version': '1.0.0',
                'author': 'TRAEWORK Team',
                'debug': not self._is_frozen,
                'update_url': 'https://TooMuchMaker.github.io/Personlist/version.json',
                'check_updates_on_startup': True,
            },
            'server': {
                'host': '127.0.0.1',
                'ports': {
                    'main': 5000,
                    'plan': 5001,
                    'course': 5002,
                    'algorithm': 5003,
                    'project': 5004,
                },
            },
            'platforms': {
                'plan': {
                    'name': '计划管理',
                    'description': '管理日常计划、任务安排和进度跟踪',
                    'icon': 'calendar',
                    'enabled': True,
                    'auto_start': True,
                },
                'course': {
                    'name': '学校课程',
                    'description': '管理学校课程资料、作业和学习资源',
                    'icon': 'book',
                    'enabled': True,
                    'auto_start': True,
                },
                'algorithm': {
                    'name': '信竞知识',
                    'description': '管理算法知识、竞赛技巧和代码模板',
                    'icon': 'cpu',
                    'enabled': True,
                    'auto_start': False,
                },
                'project': {
                    'name': '项目管理',
                    'description': '管理原创项目和收藏项目',
                    'icon': 'folder',
                    'enabled': True,
                    'auto_start': False,
                },
            },
            'ui': {
                'theme': 'light',
                'language': 'zh_CN',
                'minimize_to_tray': True,
                'close_to_tray': True,
                'start_with_windows': False,
            },
            'logging': {
                'level': 'INFO',
                'max_size_mb': 10,
                'backup_count': 5,
            },
        }
    
    @property
    def app_dir(self) -> Path:
        return self._app_dir
    
    @property
    def data_dir(self) -> Path:
        return self._data_dir
    
    @property
    def logs_dir(self) -> Path:
        return self._data_dir / 'logs'
    
    @property
    def cache_dir(self) -> Path:
        return self._data_dir / 'cache'
    
    @property
    def backups_dir(self) -> Path:
        return self._data_dir / 'backups'
    
    @property
    def is_frozen(self) -> bool:
        return self._is_frozen
    
    @property
    def debug(self) -> bool:
        return self._config['app']['debug']
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self._config)
    
    def get_port(self, platform: str) -> int:
        return self._config['server']['ports'].get(platform, 5000)
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        return self._config['platforms'].get(platform, {})
    
    def get_data_file(self, filename: str) -> Path:
        return self._data_dir / 'data' / filename
    
    def get_log_file(self, name: str) -> Path:
        return self.logs_dir / f'{name}.log'


config = Config()
