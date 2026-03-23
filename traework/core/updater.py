#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK 更新检查模块
"""

import os
import sys
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
from packaging import version

from traework.core.config import config
from traework.core.logger import get_logger

logger = get_logger('updater')


class Updater:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._current_version = config.get('app.version', '1.0.0')
        self._update_url = config.get('app.update_url', None)
        self._latest_version: Optional[str] = None
        self._update_info: Optional[Dict[str, Any]] = None
        self._last_check_time = 0
    
    @property
    def current_version(self) -> str:
        return self._current_version
    
    @property
    def latest_version(self) -> Optional[str]:
        return self._latest_version
    
    @property
    def has_update(self) -> bool:
        if self._latest_version is None:
            return False
        return version.parse(self._latest_version) > version.parse(self._current_version)
    
    @property
    def update_info(self) -> Optional[Dict[str, Any]]:
        return self._update_info
    
    def check_for_updates(self, force: bool = False) -> bool:
        """检查更新"""
        try:
            logger.info(f"Checking for updates (current version: {self._current_version})")
            
            if not self._update_url:
                logger.warning("No update URL configured")
                return False
            
            response = requests.get(
                self._update_url,
                timeout=10,
                headers={'User-Agent': f'TRAEWORK/{self._current_version}'}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to check updates: HTTP {response.status_code}")
                return False
            
            self._update_info = response.json()
            self._latest_version = self._update_info.get('version', self._current_version)
            
            logger.info(f"Latest version: {self._latest_version}")
            
            if self.has_update:
                logger.info("Update available!")
                return True
            else:
                logger.info("No update available")
                return False
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def download_update(self, save_path: Optional[Path] = None) -> Optional[Path]:
        """下载更新（如果有）"""
        if not self.has_update or not self._update_info:
            return None
        
        download_url = self._update_info.get('download_url')
        if not download_url:
            logger.error("No download URL in update info")
            return None
        
        if save_path is None:
            save_path = config.data_dir / 'updates' / f'TRAEWORK_{self._latest_version}.exe'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Downloading update from {download_url}")
            
            response = requests.get(download_url, stream=True, timeout=300)
            
            if response.status_code != 200:
                logger.error(f"Failed to download: HTTP {response.status_code}")
                return None
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            logger.info(f"Downloaded to {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}")
            if save_path.exists():
                save_path.unlink()
            return None
    
    def install_update(self, exe_path: Path) -> bool:
        """安装更新"""
        try:
            logger.info(f"Installing update from {exe_path}")
            
            if sys.platform == 'win32':
                import subprocess
                import time
                
                current_exe = sys.executable if getattr(sys, 'frozen', False) else None
                
                if current_exe:
                    batch_script = f'''
@echo off
echo Waiting for TRAEWORK to close...
timeout /t 2 /nobreak >nul
echo Installing update...
copy /Y "{exe_path}" "{current_exe}"
echo Starting TRAEWORK...
start "" "{current_exe}"
del "%~f0"
'''
                    batch_file = config.data_dir / 'update.bat'
                    with open(batch_file, 'w', encoding='gbk') as f:
                        f.write(batch_script)
                    
                    subprocess.Popen([str(batch_file)], shell=True)
                    return True
            
            logger.error("Platform not supported for auto-install")
            return False
            
        except Exception as e:
            logger.error(f"Error installing update: {e}")
            return False


updater = Updater()
