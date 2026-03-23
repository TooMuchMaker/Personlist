#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据管理器
"""

import os
import sys
import json
import uuid
import copy
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class DataManager:
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
        
        from traework.core.config import config
        self._data_dir = config.data_dir
    
    def _get_data_file(self, name: str) -> Path:
        platform_paths = {
            'plans': self._data_dir / 'platforms' / '计划管理' / 'plans.json',
            'courses': self._data_dir / 'platforms' / '学校课程' / 'courses.json',
            'knowledge': self._data_dir / 'platforms' / '信竞' / 'knowledge.json',
            'projects': self._data_dir / 'platforms' / '项目管理' / 'projects.json',
        }
        
        if name in platform_paths:
            return platform_paths[name]
        
        return self._data_dir / 'data' / f'{name}.json'
    
    def load_data(self, name: str) -> Any:
        data_file = self._get_data_file(name)
        
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"Loaded {name} from {data_file}, templates count: {len(data.get('templates', []))}")
                return data
            except Exception as e:
                print(f"Failed to load data: {e}")
                return self._get_default_data(name)
        else:
            default_data = self._get_default_data(name)
            self.save_data(name, default_data)
            return default_data
    
    def save_data(self, name: str, data: Any):
        data_file = self._get_data_file(name)
        try:
            data_file.parent.mkdir(parents=True, exist_ok=True)
            data_copy = copy.deepcopy(data)
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data_copy, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {data_file}")
        except Exception as e:
            print(f"Failed to save data: {e}")
    
    def _get_default_data(self, name: str) -> Any:
        defaults = {
            'plans': {
                'long_term': [],
                'mid_term': [],
                'short_term': [],
                'stages': [],
                'reminders': []
            },
            'courses': [],
            'knowledge': {
                'categories': [
                    {'id': 1, 'name': '数据结构', 'subcategories': ['数组', '链表', '栈', '队列', '树', '堆', '哈希表']},
                    {'id': 2, 'name': '字符串', 'subcategories': []},
                    {'id': 3, 'name': '数学', 'subcategories': []},
                    {'id': 4, 'name': '动态规划', 'subcategories': []},
                    {'id': 5, 'name': '图论', 'subcategories': []},
                    {'id': 6, 'name': '搜索', 'subcategories': []},
                    {'id': 7, 'name': '其他算法', 'subcategories': []}
                ],
                'templates': [],
                'problems': [],
                'resources': []
            },
            'projects': {
                'original': [],
                'collected': [],
                'categories': []
            }
        }
        return defaults.get(name, [])
    
    def generate_id(self) -> str:
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @property
    def data_dir(self) -> Path:
        return self._data_dir
    
    @property
    def uploads_dir(self) -> Path:
        return self._data_dir / 'uploads'


data_manager = DataManager()
