from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
import shutil

PLAN_API_BASE = "http://127.0.0.1:5001"
PLAN_SOURCE = "algorithm"
PROXIES = {'http': None, 'https': None}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'knowledge.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'files')
CODE_EXTENSIONS = {'go', 'cpp', 'c', 'h', 'py', 'java', 'js', 'ts', 'rs', 'txt', 'md'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEFAULT_CATEGORIES = [
    {"id": 1, "name": "数据结构", "icon": "bi-diagram-3", "color": "#667eea", "subcategories": [
        {"id": 1, "name": "栈与队列"},
        {"id": 2, "name": "堆/优先队列"},
        {"id": 3, "name": "并查集"},
        {"id": 4, "name": "树状数组"},
        {"id": 5, "name": "线段树"},
        {"id": 6, "name": "平衡树"},
        {"id": 7, "name": "其他数据结构"}
    ]},
    {"id": 2, "name": "字符串", "icon": "bi-fonts", "color": "#28a745", "subcategories": [
        {"id": 1, "name": "字符串哈希"},
        {"id": 2, "name": "KMP"},
        {"id": 3, "name": "后缀数组"},
        {"id": 4, "name": "字典树"},
        {"id": 5, "name": "AC自动机"},
        {"id": 6, "name": "其他字符串算法"}
    ]},
    {"id": 3, "name": "数学", "icon": "bi-calculator", "color": "#fd7e14", "subcategories": [
        {"id": 1, "name": "数论"},
        {"id": 2, "name": "组合数学"},
        {"id": 3, "name": "FFT/NTT"},
        {"id": 4, "name": "线性代数"},
        {"id": 5, "name": "计算几何"},
        {"id": 6, "name": "博弈论"},
        {"id": 7, "name": "其他数学"}
    ]},
    {"id": 4, "name": "动态规划", "icon": "bi-grid-3x3", "color": "#dc3545", "subcategories": [
        {"id": 1, "name": "背包DP"},
        {"id": 2, "name": "线性DP"},
        {"id": 3, "name": "区间DP"},
        {"id": 4, "name": "状压DP"},
        {"id": 5, "name": "数位DP"},
        {"id": 6, "name": "树形DP"},
        {"id": 7, "name": "DP优化"},
        {"id": 8, "name": "其他DP"}
    ]},
    {"id": 5, "name": "图论", "icon": "bi-share", "color": "#17a2b8", "subcategories": [
        {"id": 1, "name": "最短路"},
        {"id": 2, "name": "最小生成树"},
        {"id": 3, "name": "网络流"},
        {"id": 4, "name": "强连通分量"},
        {"id": 5, "name": "二分图"},
        {"id": 6, "name": "树上问题"},
        {"id": 7, "name": "其他图论"}
    ]},
    {"id": 6, "name": "搜索", "icon": "bi-search", "color": "#6f42c1", "subcategories": [
        {"id": 1, "name": "BFS/DFS"},
        {"id": 2, "name": "剪枝"},
        {"id": 3, "name": "迭代加深"},
        {"id": 4, "name": "启发式搜索"},
        {"id": 5, "name": "其他搜索"}
    ]},
    {"id": 7, "name": "其他算法", "icon": "bi-three-dots", "color": "#6c757d", "subcategories": [
        {"id": 1, "name": "二分/三分"},
        {"id": 2, "name": "贪心"},
        {"id": 3, "name": "分治"},
        {"id": 4, "name": "位运算"},
        {"id": 5, "name": "随机算法"},
        {"id": 6, "name": "杂项"}
    ]}
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "categories": DEFAULT_CATEGORIES,
        "templates": [],
        "problems": [],
        "resources": []
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

@app.route('/api/templates', methods=['POST'])
def add_template():
    data = load_data()
    template = request.json
    
    new_template = {
        "id": max([t['id'] for t in data['templates']], default=0) + 1,
        "name": template.get('name', ''),
        "category_id": template.get('category_id'),
        "subcategory_id": template.get('subcategory_id'),
        "description": template.get('description', ''),
        "input_desc": template.get('input_desc', ''),
        "output_desc": template.get('output_desc', ''),
        "prerequisites": template.get('prerequisites', []),
        "details": template.get('details', ''),
        "code": template.get('code', ''),
        "language": template.get('language', 'go'),
        "complexity": template.get('complexity', ''),
        "space_complexity": template.get('space_complexity', ''),
        "references": template.get('references', []),
        "problems": template.get('problems', []),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['templates'].append(new_template)
    save_data(data)
    return jsonify(new_template)

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    data = load_data()
    for template in data['templates']:
        if template['id'] == template_id:
            update_data = request.json
            for key in ['name', 'category_id', 'subcategory_id', 'description', 'input_desc', 'output_desc', 'prerequisites', 'details', 'code', 'language', 'complexity', 'space_complexity', 'references', 'problems']:
                if key in update_data:
                    template[key] = update_data[key]
            template['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            return jsonify(template)
    return jsonify({'error': 'Template not found'}), 404

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    data = load_data()
    for i, template in enumerate(data['templates']):
        if template['id'] == template_id:
            data['templates'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Template not found'}), 404

@app.route('/api/problems', methods=['POST'])
def add_problem():
    data = load_data()
    problem = request.json
    
    new_problem = {
        "id": max([p['id'] for p in data['problems']], default=0) + 1,
        "title": problem.get('title', ''),
        "source": problem.get('source', ''),
        "difficulty": problem.get('difficulty', ''),
        "tags": problem.get('tags', []),
        "url": problem.get('url', ''),
        "description": problem.get('description', ''),
        "solution": problem.get('solution', ''),
        "code": problem.get('code', ''),
        "language": problem.get('language', 'go'),
        "status": problem.get('status', 'unsolved'),
        "notes": problem.get('notes', ''),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['problems'].append(new_problem)
    save_data(data)
    return jsonify(new_problem)

@app.route('/api/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    data = load_data()
    for problem in data['problems']:
        if problem['id'] == problem_id:
            update_data = request.json
            for key in ['title', 'source', 'difficulty', 'tags', 'url', 'description', 'solution', 'code', 'language', 'status', 'notes']:
                if key in update_data:
                    problem[key] = update_data[key]
            problem['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_data(data)
            return jsonify(problem)
    return jsonify({'error': 'Problem not found'}), 404

@app.route('/api/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    data = load_data()
    for i, problem in enumerate(data['problems']):
        if problem['id'] == problem_id:
            data['problems'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Problem not found'}), 404

@app.route('/api/resources', methods=['POST'])
def add_resource():
    data = load_data()
    resource = request.json
    
    new_resource = {
        "id": max([r['id'] for r in data['resources']], default=0) + 1,
        "title": resource.get('title', ''),
        "url": resource.get('url', ''),
        "type": resource.get('type', 'article'),
        "description": resource.get('description', ''),
        "tags": resource.get('tags', []),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data['resources'].append(new_resource)
    save_data(data)
    return jsonify(new_resource)

@app.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    data = load_data()
    for i, resource in enumerate(data['resources']):
        if resource['id'] == resource_id:
            data['resources'].pop(i)
            save_data(data)
            return jsonify({'success': True})
    return jsonify({'error': 'Resource not found'}), 404

@app.route('/api/categories', methods=['POST'])
def add_category():
    data = load_data()
    category = request.json
    
    new_category = {
        "id": max([c['id'] for c in data['categories']], default=0) + 1,
        "name": category.get('name', ''),
        "icon": category.get('icon', 'bi-folder'),
        "color": category.get('color', '#667eea'),
        "subcategories": []
    }
    
    data['categories'].append(new_category)
    save_data(data)
    return jsonify(new_category)

@app.route('/api/categories/<int:category_id>/subcategories', methods=['POST'])
def add_subcategory(category_id):
    data = load_data()
    for category in data['categories']:
        if category['id'] == category_id:
            subcategory = request.json
            new_sub = {
                "id": max([s['id'] for s in category.get('subcategories', [])], default=0) + 1,
                "name": subcategory.get('name', '')
            }
            if 'subcategories' not in category:
                category['subcategories'] = []
            category['subcategories'].append(new_sub)
            save_data(data)
            return jsonify(new_sub)
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/plans', methods=['GET'])
def get_plans():
    try:
        r = requests.get(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}", timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify([]), 200
    except:
        return jsonify([]), 200

@app.route('/api/plans/<path:item_id>', methods=['GET'])
def get_algorithm_plan(item_id):
    try:
        r = requests.get(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{item_id}", timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Plan not found'}), 404
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<path:item_id>', methods=['POST'])
def create_algorithm_plan(item_id):
    try:
        plan_data = request.json
        plan_data['source'] = PLAN_SOURCE
        plan_data['source_id'] = item_id
        r = requests.post(f"{PLAN_API_BASE}/api/plans", json=plan_data, timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Failed to create plan'}), 500
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<path:item_id>', methods=['PUT'])
def update_algorithm_plan(item_id):
    try:
        plan_data = request.json
        r = requests.put(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{item_id}", json=plan_data, timeout=5, proxies=PROXIES)
        if r.status_code == 200:
            return jsonify(r.json())
        return jsonify({'error': 'Failed to update plan'}), 500
    except:
        return jsonify({'error': 'Plan service unavailable'}), 503

@app.route('/api/plans/<path:item_id>', methods=['DELETE'])
def delete_algorithm_plan(item_id):
    try:
        r = requests.delete(f"{PLAN_API_BASE}/api/plans/source/{PLAN_SOURCE}/{item_id}", timeout=5, proxies=PROXIES)
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
    app.run(debug=False, port=5003, threaded=True)
