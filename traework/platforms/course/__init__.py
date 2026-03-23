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

logger = get_logger('course_platform')


class CoursePlatform(BasePlatform):
    PLATFORM_ID = 'course'
    PLATFORM_NAME = '学校课程'
    
    def __init__(self):
        super().__init__()
        self._data_file = 'courses.json'
        self._upload_folder = self.data_dir / 'course_files'
        self._upload_folder.mkdir(parents=True, exist_ok=True)
    
    def create_app(self) -> Flask:
        app = Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        return app
    
    def register_routes(self, app: Flask):
        
        @app.route('/')
        def index():
            return render_template('course/index.html')
        
        @app.route('/api/courses', methods=['GET'])
        def get_courses():
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            return jsonify(data)
        
        @app.route('/api/courses', methods=['POST'])
        def add_course():
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            course_data = request.json
            
            new_id = max([c['id'] for c in data['courses']], default=0) + 1
            new_course = {
                "id": new_id,
                "name": course_data.get('name', ''),
                "teacher": course_data.get('teacher', ''),
                "category": course_data.get('category', ''),
                "description": course_data.get('description', ''),
                "schedule": course_data.get('schedule', ''),
                "classroom": course_data.get('classroom', ''),
                "materials": [],
                "assignments": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            course_folder = self._upload_folder / str(new_id)
            course_folder.mkdir(parents=True, exist_ok=True)
            
            data['courses'].append(new_course)
            self.save_data(data, self._data_file)
            return jsonify(new_course)
        
        @app.route('/api/courses/<int:course_id>', methods=['GET'])
        def get_course(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            for course in data['courses']:
                if course['id'] == course_id:
                    return jsonify(course)
            return jsonify({'error': 'Course not found'}), 404
        
        @app.route('/api/courses/<int:course_id>', methods=['PUT'])
        def update_course(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            for course in data['courses']:
                if course['id'] == course_id:
                    update_data = request.json
                    for key in ['name', 'teacher', 'category', 'description', 'schedule', 'classroom']:
                        if key in update_data:
                            course[key] = update_data[key]
                    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data(data, self._data_file)
                    return jsonify(course)
            return jsonify({'error': 'Course not found'}), 404
        
        @app.route('/api/courses/<int:course_id>', methods=['DELETE'])
        def delete_course(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            for i, course in enumerate(data['courses']):
                if course['id'] == course_id:
                    deleted = data['courses'].pop(i)
                    course_folder = self._upload_folder / str(course_id)
                    if course_folder.exists():
                        shutil.rmtree(course_folder)
                    self.save_data(data, self._data_file)
                    return jsonify(deleted)
            return jsonify({'error': 'Course not found'}), 404
        
        @app.route('/api/categories', methods=['GET'])
        def get_categories():
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            return jsonify(data.get('categories', []))
        
        @app.route('/api/categories', methods=['POST'])
        def add_category():
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            category_data = request.json
            
            new_id = max([c['id'] for c in data.get('categories', [])], default=0) + 1
            new_category = {
                "id": new_id,
                "name": category_data.get('name', ''),
                "color": category_data.get('color', '#667eea')
            }
            
            if 'categories' not in data:
                data['categories'] = []
            data['categories'].append(new_category)
            self.save_data(data, self._data_file)
            return jsonify(new_category)
        
        @app.route('/api/courses/<int:course_id>/materials', methods=['POST'])
        def upload_material(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            course = None
            for c in data['courses']:
                if c['id'] == course_id:
                    course = c
                    break
            
            if not course:
                return jsonify({'error': 'Course not found'}), 404
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            course_folder = self._upload_folder / str(course_id)
            course_folder.mkdir(parents=True, exist_ok=True)
            
            original_name = file.filename
            ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
            
            file_type_map = {
                'pdf': 'pdf', 'ppt': 'ppt', 'pptx': 'ppt', 'doc': 'doc', 'docx': 'doc',
                'xls': 'excel', 'xlsx': 'excel', 'txt': 'text', 'md': 'markdown',
                'py': 'code', 'js': 'code', 'ts': 'code', 'html': 'code', 'css': 'code',
                'json': 'code', 'xml': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
                'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
                'mp3': 'audio', 'wav': 'audio', 'mp4': 'video', 'avi': 'video',
            }
            file_type = file_type_map.get(ext, 'other')
            
            filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
            file_path = course_folder / filename
            file.save(str(file_path))
            
            new_material = {
                "id": max([m['id'] for m in course.get('materials', [])], default=0) + 1,
                "filename": filename,
                "original_name": original_name,
                "file_type": file_type,
                "size": file_path.stat().st_size,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if 'materials' not in course:
                course['materials'] = []
            course['materials'].append(new_material)
            self.save_data(data, self._data_file)
            
            return jsonify(new_material)
        
        @app.route('/api/courses/<int:course_id>/files/<path:filename>')
        def get_file(course_id, filename):
            course_folder = self._upload_folder / str(course_id)
            return send_from_directory(str(course_folder), filename)
        
        @app.route('/api/courses/<int:course_id>/assignments', methods=['GET'])
        def get_assignments(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            for course in data['courses']:
                if course['id'] == course_id:
                    return jsonify(course.get('assignments', []))
            return jsonify({'error': 'Course not found'}), 404
        
        @app.route('/api/courses/<int:course_id>/assignments', methods=['POST'])
        def add_assignment(course_id):
            data = self.load_data(self._data_file, {'courses': [], 'categories': []})
            for course in data['courses']:
                if course['id'] == course_id:
                    assignment_data = request.json
                    new_id = max([a['id'] for a in course.get('assignments', [])], default=0) + 1
                    new_assignment = {
                        "id": new_id,
                        "title": assignment_data.get('title', ''),
                        "description": assignment_data.get('description', ''),
                        "due_date": assignment_data.get('due_date', ''),
                        "status": assignment_data.get('status', 'pending'),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    if 'assignments' not in course:
                        course['assignments'] = []
                    course['assignments'].append(new_assignment)
                    self.save_data(data, self._data_file)
                    return jsonify(new_assignment)
            return jsonify({'error': 'Course not found'}), 404
