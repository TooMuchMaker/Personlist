from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import json
import os
from datetime import datetime
import uuid
import shutil
import subprocess
import platform
import requests

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'courses.json')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'course_files')

PLAN_API_BASE = "http://127.0.0.1:5001"
PLAN_SOURCE = "course"
PROXIES = {'http': None, 'https': None}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"courses": [], "categories": [
        {"id": 1, "name": "专业课", "color": "#667eea"},
        {"id": 2, "name": "公共课", "color": "#28a745"},
        {"id": 3, "name": "选修课", "color": "#fd7e14"}
    ]}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_course_folder(course_id):
    return os.path.join(UPLOAD_FOLDER, str(course_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/courses', methods=['GET'])
def get_courses():
    data = load_data()
    return jsonify(data)

@app.route('/api/courses', methods=['POST'])
def add_course():
    data = load_data()
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
    
    data['courses'].append(new_course)
    save_data(data)
    
    course_folder = get_course_folder(new_id)
    os.makedirs(course_folder, exist_ok=True)
    
    return jsonify(new_course)

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    data = load_data()
    for course in data['courses']:
        if course['id'] == course_id:
            return jsonify(course)
    return jsonify({'error': 'Course not found'}), 404

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    data = load_data()
    for course in data['courses']:
        if course['id'] == course_id:
            update_data = request.json
            for key, value in update_data.items():
                if key in course:
                    course[key] = value
            course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            return jsonify(course)
    return jsonify({'error': 'Course not found'}), 404

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    data = load_data()
    for i, course in enumerate(data['courses']):
        if course['id'] == course_id:
            deleted = data['courses'].pop(i)
            save_data(data)
            
            course_folder = get_course_folder(course_id)
            if os.path.exists(course_folder):
                shutil.rmtree(course_folder)
            
            return jsonify(deleted)
    return jsonify({'error': 'Course not found'}), 404

@app.route('/api/categories', methods=['GET'])
def get_categories():
    data = load_data()
    return jsonify(data.get('categories', []))

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = load_data()
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
    save_data(data)
    return jsonify(new_category)

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    data = load_data()
    categories = data.get('categories', [])
    for i, cat in enumerate(categories):
        if cat['id'] == category_id:
            deleted = categories.pop(i)
            save_data(data)
            return jsonify(deleted)
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/courses/<int:course_id>/materials', methods=['POST'])
def upload_material(course_id):
    data = load_data()
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
    
    course_folder = get_course_folder(course_id)
    os.makedirs(course_folder, exist_ok=True)
    
    original_name = file.filename
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    
    file_type_map = {
        'pdf': 'pdf',
        'ppt': 'ppt', 'pptx': 'ppt',
        'doc': 'doc', 'docx': 'doc',
        'xls': 'excel', 'xlsx': 'excel',
        'txt': 'text',
        'md': 'markdown',
        'py': 'code', 'js': 'code', 'ts': 'code', 'html': 'code', 'css': 'code',
        'json': 'code', 'xml': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
        'h': 'code', 'cs': 'code', 'go': 'code', 'rs': 'code', 'php': 'code',
        'rb': 'code', 'swift': 'code', 'kt': 'code', 'vue': 'code', 'jsx': 'code',
        'tsx': 'code', 'sql': 'code', 'sh': 'code', 'bat': 'code', 'yaml': 'code',
        'yml': 'code', 'ini': 'code', 'conf': 'code', 'log': 'code', 'csv': 'code',
        'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
        'bmp': 'image', 'webp': 'image', 'svg': 'image',
        'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio', 'flac': 'audio',
        'mp4': 'video', 'avi': 'video', 'mov': 'video', 'mkv': 'video', 'webm': 'video'
    }
    file_type = file_type_map.get(ext, 'other')
    
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    file_path = os.path.join(course_folder, filename)
    file.save(file_path)
    
    new_material = {
        "id": max([m['id'] for m in course.get('materials', [])], default=0) + 1,
        "filename": filename,
        "original_name": original_name,
        "file_type": file_type,
        "size": os.path.getsize(file_path),
        "description": "",
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "folder": "",
        "relative_path": filename
    }
    
    if 'materials' not in course:
        course['materials'] = []
    course['materials'].append(new_material)
    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    return jsonify(new_material)

@app.route('/api/courses/<int:course_id>/directory')
def get_course_directory(course_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    course_folder = get_course_folder(course_id)
    if not os.path.exists(course_folder):
        return jsonify({'items': []})
    
    items = []
    
    for root, dirs, files in os.walk(course_folder):
        rel_root = os.path.relpath(root, course_folder)
        if rel_root == '.':
            rel_root = ''
        
        for d in dirs:
            dir_path = os.path.join(rel_root, d) if rel_root else d
            full_path = os.path.join(root, d)
            file_count = sum(1 for _, _, f in os.walk(full_path) for _ in f)
            items.append({
                'type': 'folder',
                'name': d,
                'path': dir_path,
                'size': file_count,
                'file_type': 'folder'
            })
        
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f) if rel_root else f
            
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            file_type_map = {
                'pdf': 'pdf',
                'ppt': 'ppt', 'pptx': 'ppt',
                'doc': 'doc', 'docx': 'doc',
                'xls': 'excel', 'xlsx': 'excel',
                'txt': 'text',
                'md': 'markdown',
                'py': 'code', 'js': 'code', 'ts': 'code', 'html': 'code', 'css': 'code',
                'json': 'code', 'xml': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
                'h': 'code', 'cs': 'code', 'go': 'code', 'rs': 'code', 'php': 'code',
                'rb': 'code', 'swift': 'code', 'kt': 'code', 'vue': 'code', 'jsx': 'code',
                'tsx': 'code', 'sql': 'code', 'sh': 'code', 'bat': 'code', 'yaml': 'code',
                'yml': 'code', 'ini': 'code', 'conf': 'code', 'log': 'code', 'csv': 'code',
                'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
                'bmp': 'image', 'webp': 'image', 'svg': 'image',
                'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio', 'flac': 'audio',
                'mp4': 'video', 'avi': 'video', 'mov': 'video', 'mkv': 'video', 'webm': 'video'
            }
            file_type = file_type_map.get(ext, 'other')
            
            items.append({
                'type': 'file',
                'name': f,
                'path': rel_path.replace('\\', '/'),
                'size': os.path.getsize(file_path),
                'file_type': file_type
            })
        break
    
    return jsonify({'items': items})

@app.route('/api/courses/<int:course_id>/directory/<path:subpath>')
def get_subdirectory(course_id, subpath):
    course_folder = get_course_folder(course_id)
    target_folder = os.path.join(course_folder, subpath)
    
    if not os.path.exists(target_folder) or not os.path.isdir(target_folder):
        return jsonify({'items': []})
    
    items = []
    
    for item in os.listdir(target_folder):
        item_path = os.path.join(target_folder, item)
        rel_path = os.path.join(subpath, item).replace('\\', '/')
        
        if os.path.isdir(item_path):
            file_count = sum(1 for _, _, f in os.walk(item_path) for _ in f)
            items.append({
                'type': 'folder',
                'name': item,
                'path': rel_path,
                'size': file_count,
                'file_type': 'folder'
            })
        else:
            ext = item.rsplit('.', 1)[-1].lower() if '.' in item else ''
            file_type_map = {
                'pdf': 'pdf',
                'ppt': 'ppt', 'pptx': 'ppt',
                'doc': 'doc', 'docx': 'doc',
                'xls': 'excel', 'xlsx': 'excel',
                'txt': 'text',
                'md': 'markdown',
                'py': 'code', 'js': 'code', 'ts': 'code', 'html': 'code', 'css': 'code',
                'json': 'code', 'xml': 'code', 'java': 'code', 'cpp': 'code', 'c': 'code',
                'h': 'code', 'cs': 'code', 'go': 'code', 'rs': 'code', 'php': 'code',
                'rb': 'code', 'swift': 'code', 'kt': 'code', 'vue': 'code', 'jsx': 'code',
                'tsx': 'code', 'sql': 'code', 'sh': 'code', 'bat': 'code', 'yaml': 'code',
                'yml': 'code', 'ini': 'code', 'conf': 'code', 'log': 'code', 'csv': 'code',
                'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
                'bmp': 'image', 'webp': 'image', 'svg': 'image',
                'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio', 'flac': 'audio',
                'mp4': 'video', 'avi': 'video', 'mov': 'video', 'mkv': 'video', 'webm': 'video'
            }
            file_type = file_type_map.get(ext, 'other')
            
            items.append({
                'type': 'file',
                'name': item,
                'path': rel_path,
                'size': os.path.getsize(item_path),
                'file_type': file_type
            })
    
    return jsonify({'items': items})

@app.route('/api/courses/<int:course_id>/files/<path:file_path>')
def get_file(course_id, file_path):
    course_folder = get_course_folder(course_id)
    full_path = os.path.join(course_folder, file_path)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(full_path)

@app.route('/api/courses/<int:course_id>/file/<path:file_path>', methods=['DELETE'])
def delete_file(course_id, file_path):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    course_folder = get_course_folder(course_id)
    full_path = os.path.join(course_folder, file_path)
    
    if os.path.exists(full_path):
        os.remove(full_path)
    
    course['materials'] = [m for m in course.get('materials', []) 
                          if m.get('relative_path') != file_path]
    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/folder/<path:folder_path>', methods=['DELETE'])
def delete_folder(course_id, folder_path):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    course_folder = get_course_folder(course_id)
    full_path = os.path.join(course_folder, folder_path)
    
    if os.path.exists(full_path) and os.path.isdir(full_path):
        shutil.rmtree(full_path)
    
    course['materials'] = [m for m in course.get('materials', []) 
                          if not m.get('relative_path', '').startswith(folder_path)]
    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/open-folder', methods=['POST'])
@app.route('/api/courses/<int:course_id>/open-folder/<path:subpath>', methods=['POST'])
def open_course_folder(course_id, subpath=''):
    course_folder = get_course_folder(course_id)
    target_path = os.path.join(course_folder, subpath) if subpath else course_folder
    
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
    
    if platform.system() == 'Windows':
        os.startfile(target_path)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', target_path])
    else:
        subprocess.run(['xdg-open', target_path])
    
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/open-file/<path:file_path>', methods=['POST'])
def open_file_with_app(course_id, file_path):
    course_folder = get_course_folder(course_id)
    full_path = os.path.join(course_folder, file_path)
    
    if not os.path.exists(full_path):
        return jsonify({'error': 'File not found'}), 404
    
    if platform.system() == 'Windows':
        os.startfile(full_path)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', full_path])
    else:
        subprocess.run(['xdg-open', full_path])
    
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/folders/upload', methods=['POST'])
def upload_folder(course_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    course_folder = get_course_folder(course_id)
    os.makedirs(course_folder, exist_ok=True)
    
    folder_name = request.form.get('folder_name', '')
    structure = json.loads(request.form.get('structure', '[]'))
    files = request.files.getlist('files')
    
    file_map = {}
    for f in files:
        file_map[f.filename] = f
    
    for item in structure:
        if item['type'] == 'folder':
            if item['path']:
                folder_path = os.path.join(course_folder, item['path'])
            else:
                folder_path = os.path.join(course_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
    
    for item in structure:
        if item['type'] == 'file' and item['path'] in file_map:
            file = file_map[item['path']]
            file_path = os.path.join(course_folder, item['path'])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
    
    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    return jsonify({'success': True})

@app.route('/api/courses/<int:course_id>/assignments', methods=['POST'])
def add_assignment(course_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    assignment_data = request.json
    
    new_id = max([a['id'] for a in course.get('assignments', [])], default=0) + 1
    new_assignment = {
        "id": new_id,
        "title": assignment_data.get('title', ''),
        "description": assignment_data.get('description', ''),
        "due_date": assignment_data.get('due_date', ''),
        "status": assignment_data.get('status', 'pending'),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if 'assignments' not in course:
        course['assignments'] = []
    course['assignments'].append(new_assignment)
    course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data)
    
    try:
        source_id = f"{course_id}_{new_id}"
        plan_data = {
            "title": f"[{course['name']}] {new_assignment['title']}",
            "description": new_assignment.get('description', ''),
            "plan_type": "short_term",
            "priority": "medium",
            "status": new_assignment.get('status', 'pending'),
            "end_date": new_assignment.get('due_date', ''),
            "source": PLAN_SOURCE,
            "source_id": source_id,
            "creator": "user"
        }
        requests.post(f"{PLAN_API_BASE}/api/plans", json=plan_data, proxies=PROXIES, timeout=5)
    except Exception as e:
        print(f"Sync to plan failed: {e}")
    
    return jsonify(new_assignment)

@app.route('/api/courses/<int:course_id>/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(course_id, assignment_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    update_data = request.json
    for assignment in course.get('assignments', []):
        if assignment['id'] == assignment_id:
            for key, value in update_data.items():
                if key in assignment:
                    assignment[key] = value
            course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            
            try:
                source_id = f"{course_id}_{assignment_id}"
                plan_update = {}
                if 'status' in update_data:
                    plan_update['status'] = update_data['status']
                if 'due_date' in update_data:
                    plan_update['end_date'] = update_data['due_date']
                if plan_update:
                    requests.put(
                        f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{source_id}",
                        json=plan_update,
                        proxies=PROXIES,
                        timeout=5
                    )
            except Exception as e:
                print(f"Sync update to plan failed: {e}")
            
            return jsonify(assignment)
    
    return jsonify({'error': 'Assignment not found'}), 404

@app.route('/api/courses/<int:course_id>/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(course_id, assignment_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    for i, assignment in enumerate(course.get('assignments', [])):
        if assignment['id'] == assignment_id:
            deleted = course['assignments'].pop(i)
            course['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            
            try:
                source_id = f"{course_id}_{assignment_id}"
                requests.delete(
                    f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{source_id}",
                    proxies=PROXIES,
                    timeout=5
                )
            except Exception as e:
                print(f"Sync delete from plan failed: {e}")
            
            return jsonify(deleted)
    
    return jsonify({'error': 'Assignment not found'}), 404

@app.route('/api/plans/<int:course_id>', methods=['GET'])
def get_course_plan(course_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    try:
        source_id = f"{course_id}_main"
        res = requests.get(
            f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{source_id}",
            proxies=PROXIES,
            timeout=5
        )
        if res.status_code == 200:
            return jsonify(res.json())
    except:
        pass
    
    return jsonify({'error': 'No plan found'}), 404

@app.route('/api/plans/<int:course_id>', methods=['POST'])
def create_course_plan(course_id):
    data = load_data()
    course = None
    for c in data['courses']:
        if c['id'] == course_id:
            course = c
            break
    
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    
    plan_data = request.json
    plan_data['source'] = PLAN_SOURCE
    plan_data['source_id'] = f"{course_id}_main"
    plan_data['title'] = plan_data.get('title', f"[{course['name']}] 学习计划")
    
    try:
        res = requests.post(
            f"{PLAN_API_BASE}/api/plans",
            json=plan_data,
            proxies=PROXIES,
            timeout=5
        )
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plans/<int:course_id>', methods=['PUT'])
def update_course_plan(course_id):
    plan_data = request.json
    source_id = f"{course_id}_main"
    
    try:
        res = requests.put(
            f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{source_id}",
            json=plan_data,
            proxies=PROXIES,
            timeout=5
        )
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/plans/<int:course_id>', methods=['DELETE'])
def delete_course_plan(course_id):
    source_id = f"{course_id}_main"
    
    try:
        res = requests.delete(
            f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{source_id}",
            proxies=PROXIES,
            timeout=5
        )
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5002, threaded=True)
