from traework.platforms.base import BasePlatform
from traework.core.config import config
from traework.core.logger import get_logger
from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid
import os
import shutil

logger = get_logger('algorithm_platform')


class AlgorithmPlatform(BasePlatform):
    PLATFORM_ID = 'algorithm'
    PLATFORM_NAME = '信竞知识'
    
    def __init__(self):
        super().__init__()
        self._data_file = 'algorithms.json'
        self._upload_folder = self.data_dir / 'algorithm_files'
        self._upload_folder.mkdir(parents=True, exist_ok=True)
    
    def create_app(self) -> Flask:
        app = Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        return app
    
    def register_routes(self, app: Flask):
        
        @app.route('/')
        def index():
            return render_template('algorithm/index.html')
        
        @app.route('/api/templates', methods=['GET'])
        def get_templates():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            return jsonify(data.get('templates', []))
        
        @app.route('/api/templates', methods=['POST'])
        def add_template():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            template_data = request.json
            
            new_template = {
                "id": max([t['id'] for t in data.get('templates', [])], default=0) + 1,
                "name": template_data.get('name', ''),
                "category": template_data.get('category', ''),
                "language": template_data.get('language', 'cpp'),
                "code": template_data.get('code', ''),
                "description": template_data.get('description', ''),
                "tags": template_data.get('tags', []),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if 'templates' not in data:
                data['templates'] = []
            data['templates'].append(new_template)
            self.save_data(data, self._data_file)
            return jsonify(new_template)
        
        @app.route('/api/templates/<int:template_id>', methods=['PUT'])
        def update_template(template_id):
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            for template in data.get('templates', []):
                if template['id'] == template_id:
                    update_data = request.json
                    for key in ['name', 'category', 'language', 'code', 'description', 'tags']:
                        if key in update_data:
                            template[key] = update_data[key]
                    template['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data(data, self._data_file)
                    return jsonify(template)
            return jsonify({'error': 'Template not found'}), 404
        
        @app.route('/api/templates/<int:template_id>', methods=['DELETE'])
        def delete_template(template_id):
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            for i, template in enumerate(data.get('templates', [])):
                if template['id'] == template_id:
                    deleted = data['templates'].pop(i)
                    self.save_data(data, self._data_file)
                    return jsonify(deleted)
            return jsonify({'error': 'Template not found'}), 404
        
        @app.route('/api/problems', methods=['GET'])
        def get_problems():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            return jsonify(data.get('problems', []))
        
        @app.route('/api/problems', methods=['POST'])
        def add_problem():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            problem_data = request.json
            
            new_problem = {
                "id": max([p['id'] for p in data.get('problems', [])], default=0) + 1,
                "title": problem_data.get('title', ''),
                "source": problem_data.get('source', ''),
                "difficulty": problem_data.get('difficulty', 'medium'),
                "tags": problem_data.get('tags', []),
                "status": problem_data.get('status', 'unsolved'),
                "notes": problem_data.get('notes', ''),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if 'problems' not in data:
                data['problems'] = []
            data['problems'].append(new_problem)
            self.save_data(data, self._data_file)
            return jsonify(new_problem)
        
        @app.route('/api/problems/<int:problem_id>', methods=['PUT'])
        def update_problem(problem_id):
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            for problem in data.get('problems', []):
                if problem['id'] == problem_id:
                    update_data = request.json
                    for key in ['title', 'source', 'difficulty', 'tags', 'status', 'notes']:
                        if key in update_data:
                            problem[key] = update_data[key]
                    problem['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data(data, self._data_file)
                    return jsonify(problem)
            return jsonify({'error': 'Problem not found'}), 404
        
        @app.route('/api/problems/<int:problem_id>', methods=['DELETE'])
        def delete_problem(problem_id):
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            for i, problem in enumerate(data.get('problems', [])):
                if problem['id'] == problem_id:
                    deleted = data['problems'].pop(i)
                    self.save_data(data, self._data_file)
                    return jsonify(deleted)
            return jsonify({'error': 'Problem not found'}), 404
        
        @app.route('/api/categories', methods=['GET'])
        def get_categories():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            return jsonify(data.get('categories', []))
        
        @app.route('/api/categories', methods=['POST'])
        def add_category():
            data = self.load_data(self._data_file, {'templates': [], 'categories': [], 'problems': []})
            category_data = request.json
            
            new_category = {
                "id": max([c['id'] for c in data.get('categories', [])], default=0) + 1,
                "name": category_data.get('name', ''),
                "type": category_data.get('type', 'template'),
                "color": category_data.get('color', '#667eea')
            }
            
            if 'categories' not in data:
                data['categories'] = []
            data['categories'].append(new_category)
            self.save_data(data, self._data_file)
            return jsonify(new_category)
