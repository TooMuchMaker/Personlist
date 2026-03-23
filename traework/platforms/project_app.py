from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import subprocess
import platform
import shutil
import requests
from datetime import datetime
from werkzeug.utils import secure_filename

PLAN_API_BASE = "http://127.0.0.1:5001"
PLAN_SOURCE = "project"
PROXIES = {'http': None, 'https': None}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'projects.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {
        "original_projects": [],
        "collected_projects": [],
        "original_categories": [],
        "collected_categories": []
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/original', methods=['POST'])
def add_original_project():
    data = load_data()
    project_data = request.json
    
    project = {
        "id": max([p['id'] for p in data['original_projects']], default=0) + 1,
        "name": project_data.get('name', ''),
        "description": project_data.get('description', ''),
        "category": project_data.get('category', ''),
        "tech_stack": project_data.get('tech_stack', []),
        "source_url": project_data.get('source_url', ''),
        "local_path": project_data.get('local_path', ''),
        "status": project_data.get('status', 'developing'),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['original_projects'].append(project)
    save_data(data)
    return jsonify(project)

@app.route('/api/original/<int:project_id>', methods=['PUT'])
def update_original_project(project_id):
    data = load_data()
    for project in data['original_projects']:
        if project['id'] == project_id:
            update_data = request.json
            for key in ['name', 'description', 'category', 'tech_stack', 'source_url', 'local_path', 'status']:
                if key in update_data:
                    project[key] = update_data[key]
            project['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            return jsonify(project)
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/original/<int:project_id>', methods=['DELETE'])
def delete_original_project(project_id):
    data = load_data()
    for i, project in enumerate(data['original_projects']):
        if project['id'] == project_id:
            data['original_projects'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/collected', methods=['POST'])
def add_collected_project():
    data = load_data()
    project_data = request.json
    
    project = {
        "id": max([p['id'] for p in data['collected_projects']], default=0) + 1,
        "name": project_data.get('name', ''),
        "description": project_data.get('description', ''),
        "category": project_data.get('category', ''),
        "tech_stack": project_data.get('tech_stack', []),
        "source_url": project_data.get('source_url', ''),
        "local_path": project_data.get('local_path', ''),
        "status": project_data.get('status', 'active'),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['collected_projects'].append(project)
    save_data(data)
    return jsonify(project)

@app.route('/api/collected/<int:project_id>', methods=['PUT'])
def update_collected_project(project_id):
    data = load_data()
    for project in data['collected_projects']:
        if project['id'] == project_id:
            update_data = request.json
            for key in ['name', 'description', 'category', 'tech_stack', 'source_url', 'local_path', 'status']:
                if key in update_data:
                    project[key] = update_data[key]
            project['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            return jsonify(project)
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/collected/<int:project_id>', methods=['DELETE'])
def delete_collected_project(project_id):
    data = load_data()
    for i, project in enumerate(data['collected_projects']):
        if project['id'] == project_id:
            data['collected_projects'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/original/categories', methods=['POST'])
def add_original_category():
    data = load_data()
    category_data = request.json
    
    category = {
        "id": max([c['id'] for c in data['original_categories']], default=0) + 1,
        "name": category_data.get('name', ''),
        "color": category_data.get('color', '#667eea')
    }
    
    data['original_categories'].append(category)
    save_data(data)
    return jsonify(category)

@app.route('/api/original/categories/<int:category_id>', methods=['DELETE'])
def delete_original_category(category_id):
    data = load_data()
    for i, category in enumerate(data['original_categories']):
        if category['id'] == category_id:
            data['original_categories'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/collected/categories', methods=['POST'])
def add_collected_category():
    data = load_data()
    category_data = request.json
    
    category = {
        "id": max([c['id'] for c in data['collected_categories']], default=0) + 1,
        "name": category_data.get('name', ''),
        "color": category_data.get('color', '#28a745')
    }
    
    data['collected_categories'].append(category)
    save_data(data)
    return jsonify(category)

@app.route('/api/collected/categories/<int:category_id>', methods=['DELETE'])
def delete_collected_category(category_id):
    data = load_data()
    for i, category in enumerate(data['collected_categories']):
        if category['id'] == category_id:
            data['collected_categories'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    path = request.json.get('path', '')
    if not path or not os.path.exists(path):
        return jsonify({'error': 'Path not found'}), 404
    
    try:
        if platform.system() == 'Windows':
            subprocess.run(['explorer', os.path.normpath(path)])
        elif platform.system() == 'Darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<project_type>/<int:project_id>/files', methods=['GET'])
def get_project_files(project_type, project_id):
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    
    if not os.path.exists(project_folder):
        return jsonify({'files': [], 'folders': []})
    
    files = []
    folders = set()
    
    for root, dirs, filenames in os.walk(project_folder):
        rel_root = os.path.relpath(root, project_folder).replace('\\', '/')
        if rel_root != '.':
            folders.add(rel_root)
        
        for d in dirs:
            folder_path = os.path.join(rel_root, d).replace('\\', '/') if rel_root != '.' else d
            folders.add(folder_path)
        
        for filename in filenames:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, project_folder).replace('\\', '/')
            files.append({
                'name': filename,
                'path': rel_path,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return jsonify({'files': files, 'folders': sorted(list(folders))})

@app.route('/api/<project_type>/<int:project_id>/upload', methods=['POST'])
def upload_project_file(project_type, project_id):
    if 'file' not in request.files and not any(k.startswith('empty_folder_') for k in request.form):
        return jsonify({'error': 'No file part'}), 400
    
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    os.makedirs(project_folder, exist_ok=True)
    
    uploaded = []
    
    files = request.files.getlist('file')
    for index, file in enumerate(files):
        if file.filename:
            relative_path = request.form.get(f'relative_path_{index}', '')
            
            if relative_path:
                subfolder = os.path.dirname(relative_path)
                if subfolder:
                    full_path = os.path.join(project_folder, subfolder)
                    os.makedirs(full_path, exist_ok=True)
                else:
                    full_path = project_folder
                filename = os.path.basename(relative_path)
            else:
                full_path = project_folder
                filename = secure_filename(file.filename)
            
            filepath = os.path.join(full_path, filename)
            file.save(filepath)
            
            uploaded.append({
                'name': filename,
                'path': os.path.relpath(filepath, project_folder).replace('\\', '/')
            })
    
    for key in request.form:
        if key.startswith('empty_folder_'):
            folder_path = request.form[key]
            full_path = os.path.join(project_folder, folder_path)
            os.makedirs(full_path, exist_ok=True)
    
    return jsonify({'success': True, 'files': uploaded})

@app.route('/api/<project_type>/<int:project_id>/files/<path:filepath>', methods=['DELETE'])
def delete_project_file(project_type, project_id, filepath):
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    full_path = os.path.join(project_folder, filepath)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    if os.path.isfile(full_path):
        os.remove(full_path)
    else:
        shutil.rmtree(full_path)
    
    return jsonify({'success': True})

@app.route('/api/<project_type>/<int:project_id>/folder/<path:folderpath>', methods=['DELETE'])
def delete_project_folder(project_type, project_id, folderpath):
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    full_path = os.path.join(project_folder, folderpath)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'Folder not found'}), 404
    
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Not a folder'}), 400

@app.route('/api/<project_type>/<int:project_id>/files/<path:filepath>')
def download_project_file(project_type, project_id, filepath):
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    return send_from_directory(project_folder, filepath)

@app.route('/api/<project_type>/<int:project_id>/open-file/<path:filepath>', methods=['POST'])
def open_project_file(project_type, project_id, filepath):
    project_folder = os.path.join(UPLOAD_FOLDER, project_type, str(project_id))
    full_path = os.path.join(project_folder, filepath)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        if platform.system() == 'Windows':
            os.startfile(os.path.normpath(full_path))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', full_path])
        else:
            subprocess.run(['xdg-open', full_path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plans', methods=['GET'])
def get_plans():
    try:
        r = requests.get(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}", timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify([]), 200
    except:
        return jsonify([]), 200

@app.route('/api/plans/<int:project_id>', methods=['GET'])
def get_project_plan(project_id):
    try:
        r = requests.get(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{project_id}", timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Plan not found'}), 404
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<int:project_id>', methods=['POST'])
def create_project_plan(project_id):
    try:
        plan_data = request.json
        plan_data['source'] = PLAN_SOURCE
        plan_data['source_id'] = project_id
        r = requests.post(f"{PLAN_API_BASE}/api/plans", json=plan_data, timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Failed to create plan'}), 500
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<int:project_id>', methods=['PUT'])
def update_project_plan(project_id):
    try:
        plan_data = request.json
        r = requests.put(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{project_id}", json=plan_data, timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Failed to update plan'}), 500
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<int:project_id>', methods=['DELETE'])
def delete_project_plan(project_id):
    try:
        r = requests.delete(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{project_id}", timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Failed to delete plan'}), 500
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plan-status', methods=['GET'])
def check_plan_service():
    try:
        r = requests.get(f"{PLAN_API_BASE}/api/plans", timeout=2, proxies=PROXIES)
        return jsonify({'available': r.status_code == 200})
    except:
        return jsonify({'available': False})

if __name__ == '__main__':
    app.run(debug=False, port=5004, threaded=True)
