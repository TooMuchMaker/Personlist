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

logger = get_logger('project_platform')


class ProjectPlatform(BasePlatform):
    PLATFORM_ID = 'project'
    PLATFORM_NAME = '项目管理'
    
    def __init__(self):
        super().__init__()
        self._data_file = 'projects.json'
        self._upload_folder = self.data_dir / 'project_files'
        self._upload_folder.mkdir(parents=True, exist_ok=True)
    
    def create_app(self) -> Flask:
        app = Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        return app
    
    def register_routes(self, app: Flask):
        
        @app.route('/')
        def index():
            return render_template('project/index.html')
        
        @app.route('/api/projects', methods=['GET'])
        def get_projects():
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            return jsonify(data)
        
        @app.route('/api/projects', methods=['POST'])
        def add_project():
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            project_data = request.json
            
            new_id = max([p['id'] for p in data.get('projects', [])], default=0) + 1
            new_project = {
                "id": new_id,
                "name": project_data.get('name', ''),
                "description": project_data.get('description', ''),
                "category": project_data.get('category', 'original'),
                "status": project_data.get('status', 'in_progress'),
                "tech_stack": project_data.get('tech_stack', []),
                "repository_url": project_data.get('repository_url', ''),
                "documentation": project_data.get('documentation', ''),
                "files": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            project_folder = self._upload_folder / str(new_id)
            project_folder.mkdir(parents=True, exist_ok=True)
            
            if 'projects' not in data:
                data['projects'] = []
            data['projects'].append(new_project)
            self.save_data(data, self._data_file)
            return jsonify(new_project)
        
        @app.route('/api/projects/<int:project_id>', methods=['GET'])
        def get_project(project_id):
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            for project in data.get('projects', []):
                if project['id'] == project_id:
                    return jsonify(project)
            return jsonify({'error': 'Project not found'}), 404
        
        @app.route('/api/projects/<int:project_id>', methods=['PUT'])
        def update_project(project_id):
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            for project in data.get('projects', []):
                if project['id'] == project_id:
                    update_data = request.json
                    for key in ['name', 'description', 'category', 'status', 'tech_stack', 'repository_url', 'documentation']:
                        if key in update_data:
                            project[key] = update_data[key]
                    project['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data(data, self._data_file)
                    return jsonify(project)
            return jsonify({'error': 'Project not found'}), 404
        
        @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
        def delete_project(project_id):
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            for i, project in enumerate(data.get('projects', [])):
                if project['id'] == project_id:
                    deleted = data['projects'].pop(i)
                    project_folder = self._upload_folder / str(project_id)
                    if project_folder.exists():
                        shutil.rmtree(project_folder)
                    self.save_data(data, self._data_file)
                    return jsonify(deleted)
            return jsonify({'error': 'Project not found'}), 404
        
        @app.route('/api/categories', methods=['GET'])
        def get_categories():
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            return jsonify(data.get('categories', [
                {"id": 1, "name": "原创项目", "type": "original"},
                {"id": 2, "name": "收藏项目", "type": "starred"}
            ]))
        
        @app.route('/api/projects/<int:project_id>/files', methods=['POST'])
        def upload_file(project_id):
            data = self.load_data(self._data_file, {'projects': [], 'categories': []})
            project = None
            for p in data.get('projects', []):
                if p['id'] == project_id:
                    project = p
                    break
            
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            project_folder = self._upload_folder / str(project_id)
            project_folder.mkdir(parents=True, exist_ok=True)
            
            original_name = file.filename
            ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
            
            filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
            file_path = project_folder / filename
            file.save(str(file_path))
            
            new_file = {
                "id": max([f['id'] for f in project.get('files', [])], default=0) + 1,
                "filename": filename,
                "original_name": original_name,
                "size": file_path.stat().st_size,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if 'files' not in project:
                project['files'] = []
            project['files'].append(new_file)
            self.save_data(data, self._data_file)
            
            return jsonify(new_file)
        
        @app.route('/api/projects/<int:project_id>/files/<path:filename>')
        def get_file(project_id, filename):
            project_folder = self._upload_folder / str(project_id)
            return send_from_directory(str(project_folder), filename)
