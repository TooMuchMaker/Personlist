#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK 服务管理器
使用多进程架构运行各平台
"""

import subprocess
import sys
import time
import webbrowser
import os
import multiprocessing
from pathlib import Path
from typing import Dict, Optional, Callable
import requests

from .config import config
from .logger import get_logger

logger = get_logger('service_manager')


def run_platform_process(platform_id: str, port: int):
    """
    在子进程中运行平台
    """
    if platform_id == 'plan':
        from traework.platforms.plan_app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    elif platform_id == 'course':
        from traework.platforms.course_app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    elif platform_id == 'algorithm':
        from traework.platforms.algorithm_app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    elif platform_id == 'project':
        from traework.platforms.project_app import app
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)


class PlatformInfo:
    def __init__(self, platform_id: str, name: str, description: str, 
                 port: int, icon: str,
                 enabled: bool = True, auto_start: bool = False):
        self.id = platform_id
        self.name = name
        self.description = description
        self.port = port
        self.icon = icon
        self.enabled = enabled
        self.auto_start = auto_start
        self._process: Optional[multiprocessing.Process] = None
        self._status = 'stopped'
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"
    
    def check_status(self) -> str:
        try:
            response = requests.get(
                self.url,
                timeout=2,
                headers={'Connection': 'close'},
                proxies={'http': None, 'https': None}
            )
            self._status = 'running' if response.status_code == 200 else 'stopped'
        except:
            self._status = 'stopped'
        return self._status
    
    def start(self) -> bool:
        if self.check_status() == 'running':
            logger.info(f"Platform {self.name} already running")
            return True
        
        try:
            logger.info(f"Starting {self.name} on port {self.port}...")
            
            self._process = multiprocessing.Process(
                target=run_platform_process,
                args=(self.id, self.port),
                daemon=True
            )
            self._process.start()
            
            for i in range(20):
                time.sleep(0.5)
                if self.check_status() == 'running':
                    logger.info(f"Platform {self.name} started successfully")
                    return True
            
            logger.error(f"Platform {self.name} start timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start platform {self.name}: {e}")
            return False
    
    def stop(self) -> bool:
        if self._process:
            try:
                self._process.terminate()
                self._process.join(timeout=5)
            except:
                self._process.kill()
            self._process = None
            self._status = 'stopped'
            logger.info(f"Platform {self.name} stopped")
            return True
        return False
    
    def open_browser(self):
        if self.check_status() == 'running':
            webbrowser.open(self.url)
        else:
            logger.warning(f"Platform {self.name} is not running")


class ServiceManager:
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
        
        self._platforms: Dict[str, PlatformInfo] = {}
        self._callbacks: list = []
        self._load_platforms()
    
    def _load_platforms(self):
        ports = config.get('server.ports', {})
        platforms_config = config.get('platforms', {})
        
        platform_definitions = {
            'plan': {
                'name': '计划管理',
                'description': '管理日常计划、任务安排和进度跟踪',
                'icon': 'calendar',
            },
            'course': {
                'name': '学校课程',
                'description': '管理学校课程资料、作业和学习资源',
                'icon': 'book',
            },
            'algorithm': {
                'name': '信竞知识',
                'description': '管理算法知识、竞赛技巧和代码模板',
                'icon': 'cpu',
            },
            'project': {
                'name': '项目管理',
                'description': '管理原创项目和收藏项目',
                'icon': 'folder',
            },
        }
        
        for platform_id, info in platform_definitions.items():
            platform_config = platforms_config.get(platform_id, {})
            self._platforms[platform_id] = PlatformInfo(
                platform_id=platform_id,
                name=info['name'],
                description=info['description'],
                port=ports.get(platform_id, 5000),
                icon=info['icon'],
                enabled=platform_config.get('enabled', True),
                auto_start=platform_config.get('auto_start', False),
            )
    
    def get_platform(self, platform_id: str) -> Optional[PlatformInfo]:
        return self._platforms.get(platform_id)
    
    def get_all_platforms(self) -> Dict[str, PlatformInfo]:
        return self._platforms.copy()
    
    def start_platform(self, platform_id: str) -> bool:
        platform = self.get_platform(platform_id)
        if platform:
            result = platform.start()
            self._notify_callbacks()
            return result
        return False
    
    def stop_platform(self, platform_id: str) -> bool:
        platform = self.get_platform(platform_id)
        if platform:
            result = platform.stop()
            self._notify_callbacks()
            return result
        return False
    
    def start_all(self) -> Dict[str, bool]:
        results = {}
        for platform_id, platform in self._platforms.items():
            if platform.enabled:
                results[platform_id] = platform.start()
        self._notify_callbacks()
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        results = {}
        for platform_id, platform in self._platforms.items():
            if platform.status == 'running':
                results[platform_id] = platform.stop()
        self._notify_callbacks()
        return results
    
    def start_auto_start_platforms(self):
        for platform_id, platform in self._platforms.items():
            if platform.enabled and platform.auto_start:
                platform.start()
        self._notify_callbacks()
    
    def check_all_status(self):
        for platform in self._platforms.values():
            platform.check_status()
        self._notify_callbacks()
    
    def add_status_callback(self, callback: Callable):
        self._callbacks.append(callback)
    
    def _notify_callbacks(self):
        for callback in self._callbacks:
            try:
                callback(self._platforms)
            except Exception as e:
                logger.error(f"Callback error: {e}")


service_manager = ServiceManager()
