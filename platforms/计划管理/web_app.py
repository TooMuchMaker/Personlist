from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import requests

app = Flask(__name__)

PLAN_FILE = os.path.join(os.path.dirname(__file__), 'plans.json')

PLAN_API_BASE = "http://127.0.0.1:5001"
COURSE_API_BASE = "http://127.0.0.1:5002"
PROXIES = {'http': None, 'https': None}

VALID_SOURCES = ['plan', 'project', 'course', 'algorithm']

def load_plans() -> Dict:
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {
        "plans": {
            "long_term": [],
            "mid_term": [],
            "short_term": []
        },
        "stages": [],
        "settings": {
            "sort_options": ["priority", "start_date", "end_date", "created_at"],
            "priority_levels": ["high", "medium", "low"],
            "status_options": ["pending", "in_progress", "completed", "cancelled"]
        }
    }

def auto_cleanup_plans(data: Dict) -> Dict:
    today = datetime.now().date()
    cleaned = False
    
    for plan_type in data['plans']:
        plans_to_keep = []
        for plan in data['plans'][plan_type]:
            if plan.get('status') in ['completed', 'cancelled']:
                status_changed_at = plan.get('status_changed_at', '')
                if status_changed_at:
                    try:
                        change_date = datetime.strptime(status_changed_at.split()[0], '%Y-%m-%d').date()
                        if change_date < today:
                            cleaned = True
                            continue
                    except:
                        pass
            plans_to_keep.append(plan)
        data['plans'][plan_type] = plans_to_keep
    
    if cleaned:
        save_plans(data)
    
    return data

@app.route('/api/cleanup', methods=['POST'])
def run_cleanup():
    data = load_plans()
    data = auto_cleanup_plans(data)
    return jsonify({'success': True})

def save_plans(data: Dict):
    with open(PLAN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_unique_id(plans_list: List) -> int:
    if not plans_list:
        return 1
    max_id = max(p.get('id', 0) for p in plans_list)
    return max_id + 1

@app.route('/')
def index():
    return render_template('plan_ui.html')

@app.route('/api/plans', methods=['GET'])
def get_plans():
    data = load_plans()
    return jsonify(data)

@app.route('/api/plans/<plan_type>', methods=['GET'])
def get_plans_by_type(plan_type):
    data = load_plans()
    if plan_type not in data['plans']:
        return jsonify({'error': 'Invalid plan type'}), 400
    
    sort_by = request.args.get('sort', 'priority')
    source = request.args.get('source')
    
    plans = data['plans'][plan_type]
    
    if source and source in VALID_SOURCES:
        plans = [p for p in plans if p.get('source') == source]
    
    plans = sort_plans(plans, sort_by)
    return jsonify(plans)

@app.route('/api/plans/source/<source>', methods=['GET'])
def get_plans_by_source(source):
    if source not in VALID_SOURCES:
        return jsonify({'error': 'Invalid source'}), 400
    
    data = load_plans()
    sort_by = request.args.get('sort', 'priority')
    
    all_plans = []
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if plan.get('source') == source:
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                all_plans.append(plan_copy)
    
    all_plans = sort_plans(all_plans, sort_by)
    return jsonify(all_plans)

@app.route('/api/plans', methods=['POST'])
def add_plan():
    data = load_plans()
    plan_data = request.json
    
    plan_type = plan_data.get('plan_type')
    if plan_type not in data['plans']:
        return jsonify({'error': 'Invalid plan type'}), 400
    
    title = plan_data.get('title', '').strip().lower()
    for existing in data['plans'][plan_type]:
        if existing.get('title', '').strip().lower() == title:
            if existing.get('status') not in ['completed', 'cancelled']:
                return jsonify({'error': f'已存在同名计划：「{plan_data.get("title", "")}」'}), 400
    
    source = plan_data.get('source', 'plan')
    if source not in VALID_SOURCES:
        source = 'plan'
    
    new_plan = {
        "id": generate_unique_id(data['plans'][plan_type]),
        "title": plan_data.get('title', '').strip(),
        "description": plan_data.get('description', ''),
        "priority": plan_data.get('priority', 'medium'),
        "status": plan_data.get('status', 'pending'),
        "start_date": plan_data.get('start_date', ''),
        "end_date": plan_data.get('end_date', ''),
        "tags": plan_data.get('tags', []),
        "source": source,
        "source_id": plan_data.get('source_id'),
        "creator": plan_data.get('creator', 'user'),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "progress": plan_data.get('progress', 0)
    }
    
    data['plans'][plan_type].append(new_plan)
    save_plans(data)
    return jsonify(new_plan)

@app.route('/api/plans/<plan_type>/<int:plan_id>', methods=['PUT'])
def update_plan(plan_type, plan_id):
    data = load_plans()
    if plan_type not in data['plans']:
        return jsonify({'error': 'Invalid plan type'}), 400
    
    for plan in data['plans'][plan_type]:
        if plan['id'] == plan_id:
            update_data = request.json
            old_status = plan.get('status', 'pending')
            for key, value in update_data.items():
                if key in plan and key != 'id' and key != 'source':
                    plan[key] = value
            if update_data.get('status') in ['completed', 'cancelled'] and old_status not in ['completed', 'cancelled']:
                plan['status_changed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plan['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_plans(data)
            return jsonify(plan)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/plans/<plan_type>/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_type, plan_id):
    data = load_plans()
    if plan_type not in data['plans']:
        return jsonify({'error': 'Invalid plan type'}), 400
    
    for i, plan in enumerate(data['plans'][plan_type]):
        if plan['id'] == plan_id:
            deleted = data['plans'][plan_type].pop(i)
            save_plans(data)
            
            if deleted.get('source') == 'course' and deleted.get('source_id'):
                try:
                    source_id = deleted.get('source_id')
                    if '_' in str(source_id):
                        course_id, assignment_id = str(source_id).split('_', 1)
                        requests.delete(
                            f"{COURSE_API_BASE}/api/courses/{course_id}/assignments/{assignment_id}",
                            proxies=PROXIES,
                            timeout=5
                        )
                except Exception as e:
                    print(f"Sync delete to course failed: {e}")
            
            return jsonify(deleted)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/plans/source/<source>/<source_id>', methods=['GET'])
def get_plan_by_source_id(source, source_id):
    if source not in VALID_SOURCES:
        return jsonify({'error': 'Invalid source'}), 400
    
    data = load_plans()
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if plan.get('source') == source and str(plan.get('source_id')) == str(source_id):
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                return jsonify(plan_copy)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/plans/source/<source>/<source_id>', methods=['PUT'])
def update_plan_by_source_id(source, source_id):
    if source not in VALID_SOURCES:
        return jsonify({'error': 'Invalid source'}), 400
    
    data = load_plans()
    update_data = request.json
    
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if plan.get('source') == source and str(plan.get('source_id')) == str(source_id):
                old_status = plan.get('status', 'pending')
                for key, value in update_data.items():
                    if key in plan and key != 'id' and key != 'source' and key != 'source_id':
                        plan[key] = value
                if update_data.get('status') in ['completed', 'cancelled'] and old_status not in ['completed', 'cancelled']:
                    plan['status_changed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                plan['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_plans(data)
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                return jsonify(plan_copy)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/plans/source/<source>/<source_id>', methods=['DELETE'])
def delete_plan_by_source_id(source, source_id):
    if source not in VALID_SOURCES:
        return jsonify({'error': 'Invalid source'}), 400
    
    data = load_plans()
    for plan_type in data['plans']:
        for i, plan in enumerate(data['plans'][plan_type]):
            if plan.get('source') == source and str(plan.get('source_id')) == str(source_id):
                deleted = data['plans'][plan_type].pop(i)
                save_plans(data)
                
                if source == 'course' and source_id:
                    try:
                        if '_' in str(source_id):
                            course_id, assignment_id = str(source_id).split('_', 1)
                            requests.delete(
                                f"{COURSE_API_BASE}/api/courses/{course_id}/assignments/{assignment_id}",
                                proxies=PROXIES,
                                timeout=5
                            )
                    except Exception as e:
                        print(f"Sync delete to course failed: {e}")
                
                return jsonify(deleted)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/stages', methods=['GET'])
def get_stages():
    data = load_plans()
    stages = data.get('stages', [])
    return jsonify(stages)

@app.route('/api/stages', methods=['POST'])
def add_stage():
    data = load_plans()
    stage_data = request.json
    
    new_stage = {
        "id": len(data.get('stages', [])) + 1,
        "name": stage_data.get('name', ''),
        "start_date": stage_data.get('start_date', ''),
        "end_date": stage_data.get('end_date', ''),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if 'stages' not in data:
        data['stages'] = []
    data['stages'].append(new_stage)
    save_plans(data)
    return jsonify(new_stage)

@app.route('/api/stages/<int:stage_id>', methods=['PUT'])
def update_stage(stage_id):
    data = load_plans()
    stages = data.get('stages', [])
    
    for stage in stages:
        if stage['id'] == stage_id:
            update_data = request.json
            for key, value in update_data.items():
                if key in stage:
                    stage[key] = value
            save_plans(data)
            return jsonify(stage)
    
    return jsonify({'error': 'Stage not found'}), 404

@app.route('/api/stages/<int:stage_id>', methods=['DELETE'])
def delete_stage(stage_id):
    data = load_plans()
    stages = data.get('stages', [])
    
    for i, stage in enumerate(stages):
        if stage['id'] == stage_id:
            deleted = stages.pop(i)
            save_plans(data)
            return jsonify(deleted)
    
    return jsonify({'error': 'Stage not found'}), 404

@app.route('/api/stages/<int:stage_id>/plans', methods=['GET'])
def get_stage_plans(stage_id):
    data = load_plans()
    stages = data.get('stages', [])
    
    target_stage = None
    for stage in stages:
        if stage['id'] == stage_id:
            target_stage = stage
            break
    
    if not target_stage:
        return jsonify({'error': 'Stage not found'}), 404
    
    sort_by = request.args.get('sort', 'priority')
    stage_start = target_stage['start_date']
    stage_end = target_stage['end_date']
    
    all_plans = []
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if is_plan_in_stage(plan, stage_start, stage_end):
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                all_plans.append(plan_copy)
    
    all_plans = sort_plans(all_plans, sort_by)
    return jsonify(all_plans)

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    data = load_plans()
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    upcoming_plans = []
    overdue_plans = []
    upcoming_stages = []
    overdue_stages = []
    yesterday_plans = []
    yesterday_stages = []
    
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if plan.get('end_date') and plan['status'] not in ['completed', 'cancelled']:
                end_date = datetime.strptime(plan['end_date'], '%Y-%m-%d').date()
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                
                if end_date < today:
                    plan_copy['auto_summary'] = generate_plan_summary(plan)
                    if end_date == yesterday:
                        yesterday_plans.append(plan_copy)
                    else:
                        overdue_plans.append(plan_copy)
                else:
                    days_left = (end_date - today).days
                    if days_left in [1, 2, 3]:
                        plan_copy['days_left'] = days_left
                        upcoming_plans.append(plan_copy)
    
    for stage in data.get('stages', []):
        if stage.get('end_date'):
            end_date = datetime.strptime(stage['end_date'], '%Y-%m-%d').date()
            stage_copy = stage.copy()
            
            if end_date < today:
                stage_copy['auto_summary'] = generate_stage_summary(stage, data)
                if end_date == yesterday:
                    yesterday_stages.append(stage_copy)
                else:
                    overdue_stages.append(stage_copy)
            else:
                days_left = (end_date - today).days
                if days_left in [1, 2, 3]:
                    stage_copy['days_left'] = days_left
                    upcoming_stages.append(stage_copy)
    
    return jsonify({
        'upcoming_plans': upcoming_plans,
        'overdue_plans': overdue_plans,
        'upcoming_stages': upcoming_stages,
        'overdue_stages': overdue_stages,
        'yesterday_plans': yesterday_plans,
        'yesterday_stages': yesterday_stages,
        'today': today.strftime('%Y-%m-%d')
    })

def generate_plan_summary(plan: Dict) -> str:
    summary_parts = []
    
    progress = plan.get('progress', 0)
    status = plan.get('status', 'pending')
    title = plan.get('title', '该计划')
    
    if progress == 100:
        summary_parts.append(f"「{title}」已完成100%，但状态未更新为已完成。")
    elif progress >= 80:
        summary_parts.append(f"「{title}」进度达到{progress}%，接近完成。")
    elif progress >= 50:
        summary_parts.append(f"「{title}」进度为{progress}%，完成过半。")
    elif progress > 0:
        summary_parts.append(f"「{title}」进度仅为{progress}%，尚未完成。")
    else:
        summary_parts.append(f"「{title}」尚未开始执行。")
    
    if status == 'pending':
        summary_parts.append("当前状态为待处理，建议尽快启动。")
    elif status == 'in_progress':
        summary_parts.append("当前状态为进行中，需要关注进度。")
    
    priority = plan.get('priority', 'medium')
    if priority == 'high':
        summary_parts.append("该计划优先级较高，建议优先处理。")
    
    return " ".join(summary_parts)

def generate_stage_summary(stage: Dict, data: Dict) -> str:
    summary_parts = []
    stage_name = stage.get('name', '该阶段')
    stage_start = stage.get('start_date', '')
    stage_end = stage.get('end_date', '')
    
    stage_plans = []
    for plan_type in data['plans']:
        for plan in data['plans'][plan_type]:
            if is_plan_in_stage(plan, stage_start, stage_end):
                plan_copy = plan.copy()
                plan_copy['plan_type'] = plan_type
                stage_plans.append(plan_copy)
    
    total = len(stage_plans)
    completed = sum(1 for p in stage_plans if p['status'] == 'completed')
    in_progress = sum(1 for p in stage_plans if p['status'] == 'in_progress')
    pending = sum(1 for p in stage_plans if p['status'] == 'pending')
    
    summary_parts.append(f"「{stage_name}」已结束。")
    summary_parts.append(f"该阶段共有{total}个计划：")
    summary_parts.append(f"已完成{completed}个，进行中{in_progress}个，待处理{pending}个。")
    
    if total > 0:
        completion_rate = (completed / total) * 100
        summary_parts.append(f"完成率为{completion_rate:.1f}%。")
        
        if completion_rate >= 80:
            summary_parts.append("阶段目标完成情况良好！")
        elif completion_rate >= 50:
            summary_parts.append("阶段目标完成情况一般，部分计划需要跟进。")
        else:
            summary_parts.append("阶段目标完成情况不理想，需要分析原因。")
    
    return " ".join(summary_parts)

@app.route('/api/plans/<plan_type>/<int:plan_id>/summary', methods=['POST'])
def add_plan_summary(plan_type, plan_id):
    data = load_plans()
    if plan_type not in data['plans']:
        return jsonify({'error': 'Invalid plan type'}), 400
    
    for plan in data['plans'][plan_type]:
        if plan['id'] == plan_id:
            summary = request.json.get('summary', '')
            plan['summary'] = summary
            plan['summary_added_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_plans(data)
            return jsonify(plan)
    
    return jsonify({'error': 'Plan not found'}), 404

@app.route('/api/stages/<int:stage_id>/summary', methods=['POST'])
def add_stage_summary(stage_id):
    data = load_plans()
    stages = data.get('stages', [])
    
    for stage in stages:
        if stage['id'] == stage_id:
            summary = request.json.get('summary', '')
            stage['summary'] = summary
            stage['summary_added_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_plans(data)
            return jsonify(stage)
    
    return jsonify({'error': 'Stage not found'}), 404

def is_plan_in_stage(plan: Dict, stage_start: str, stage_end: str) -> bool:
    if not plan.get('start_date') and not plan.get('end_date'):
        return False
    
    plan_start = plan.get('start_date', '')
    plan_end = plan.get('end_date', '')
    
    if plan_start and plan_end:
        return plan_start <= stage_end and plan_end >= stage_start
    elif plan_start:
        return plan_start <= stage_end
    elif plan_end:
        return plan_end >= stage_start
    
    return False

def sort_plans(plans: List[Dict], sort_by: str) -> List[Dict]:
    if sort_by == 'priority':
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(plans, key=lambda x: priority_order.get(x.get('priority', 'medium'), 1))
    elif sort_by == 'start_date':
        return sorted(plans, key=lambda x: x.get('start_date', '') or '9999-99-99')
    elif sort_by == 'end_date':
        return sorted(plans, key=lambda x: x.get('end_date', '') or '9999-99-99')
    elif sort_by == 'created_at':
        return sorted(plans, key=lambda x: x.get('created_at', ''), reverse=True)
    return plans

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
