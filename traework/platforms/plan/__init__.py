from traework.platforms.base import BasePlatform
from traework.core.config import config
from traework.core.logger import get_logger
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = get_logger('plan_platform')


class PlanPlatform(BasePlatform):
    PLATFORM_ID = 'plan'
    PLATFORM_NAME = '计划管理'
    
    def __init__(self):
        super().__init__()
        self._data_file = 'plans.json'
    
    def create_app(self) -> Flask:
        app = Flask(__name__)
        return app
    
    def register_routes(self, app: Flask):
        
        @app.route('/')
        def index():
            return render_template('plan/index.html')
        
        @app.route('/api/plans', methods=['GET'])
        def get_plans():
            default_data = {
                "plans": {"long_term": [], "mid_term": [], "short_term": []},
                "stages": [],
                "settings": {
                    "sort_options": ["priority", "start_date", "end_date", "created_at"],
                    "priority_levels": ["high", "medium", "low"],
                    "status_options": ["pending", "in_progress", "completed", "cancelled"]
                }
            }
            data = self.load_data(self._data_file, default_data)
            return jsonify(data)
        
        @app.route('/api/plans', methods=['POST'])
        def add_plan():
            data = self.load_data(self._data_file, {"plans": {"long_term": [], "mid_term": [], "short_term": []}})
            plan_data = request.json
            
            plan_type = plan_data.get('plan_type')
            if plan_type not in data['plans']:
                return jsonify({'error': 'Invalid plan type'}), 400
            
            title = plan_data.get('title', '').strip().lower()
            for existing in data['plans'][plan_type]:
                if existing.get('title', '').strip().lower() == title:
                    if existing.get('status') not in ['completed', 'cancelled']:
                        return jsonify({'error': f'已存在同名计划：「{title}」'}), 400
            
            new_plan = {
                "id": max([p['id'] for p in data['plans'][plan_type]], default=0) + 1,
                "title": plan_data.get('title', ''),
                "description": plan_data.get('description', ''),
                "priority": plan_data.get('priority', 'medium'),
                "status": plan_data.get('status', 'pending'),
                "start_date": plan_data.get('start_date', ''),
                "end_date": plan_data.get('end_date', ''),
                "tags": plan_data.get('tags', []),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "progress": plan_data.get('progress', 0)
            }
            
            data['plans'][plan_type].append(new_plan)
            self.save_data(data, self._data_file)
            return jsonify(new_plan)
        
        @app.route('/api/plans/<plan_type>/<int:plan_id>', methods=['PUT'])
        def update_plan(plan_type, plan_id):
            data = self.load_data(self._data_file, {"plans": {"long_term": [], "mid_term": [], "short_term": []}})
            if plan_type not in data['plans']:
                return jsonify({'error': 'Invalid plan type'}), 400
            
            for plan in data['plans'][plan_type]:
                if plan['id'] == plan_id:
                    update_data = request.json
                    for key in ['title', 'description', 'priority', 'status', 'start_date', 'end_date', 'tags', 'progress']:
                        if key in update_data:
                            plan[key] = update_data[key]
                    plan['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_data(data, self._data_file)
                    return jsonify(plan)
            
            return jsonify({'error': 'Plan not found'}), 404
        
        @app.route('/api/plans/<plan_type>/<int:plan_id>', methods=['DELETE'])
        def delete_plan(plan_type, plan_id):
            data = self.load_data(self._data_file, {"plans": {"long_term": [], "mid_term": [], "short_term": []}})
            if plan_type not in data['plans']:
                return jsonify({'error': 'Invalid plan type'}), 400
            
            for i, plan in enumerate(data['plans'][plan_type]):
                if plan['id'] == plan_id:
                    deleted = data['plans'][plan_type].pop(i)
                    self.save_data(data, self._data_file)
                    return jsonify(deleted)
            
            return jsonify({'error': 'Plan not found'}), 404
        
        @app.route('/api/reminders', methods=['GET'])
        def get_reminders():
            data = self.load_data(self._data_file, {"plans": {"long_term": [], "mid_term": [], "short_term": []}})
            today = datetime.now().date()
            
            upcoming_plans = []
            overdue_plans = []
            
            for plan_type in data['plans']:
                for plan in data['plans'][plan_type]:
                    if plan.get('end_date') and plan['status'] not in ['completed', 'cancelled']:
                        try:
                            end_date = datetime.strptime(plan['end_date'], '%Y-%m-%d').date()
                            plan_copy = plan.copy()
                            plan_copy['plan_type'] = plan_type
                            
                            if end_date < today:
                                overdue_plans.append(plan_copy)
                            elif end_date <= today + timedelta(days=3):
                                plan_copy['days_left'] = (end_date - today).days
                                upcoming_plans.append(plan_copy)
                        except ValueError:
                            pass
            
            return jsonify({
                'upcoming_plans': upcoming_plans,
                'overdue_plans': overdue_plans,
                'today': today.strftime('%Y-%m-%d')
            })
        
        @app.route('/api/stages', methods=['GET'])
        def get_stages():
            data = self.load_data(self._data_file, {"stages": []})
            return jsonify(data.get('stages', []))
        
        @app.route('/api/stages', methods=['POST'])
        def add_stage():
            data = self.load_data(self._data_file, {"stages": []})
            stage_data = request.json
            
            new_stage = {
                "id": max([s['id'] for s in data.get('stages', [])], default=0) + 1,
                "name": stage_data.get('name', ''),
                "description": stage_data.get('description', ''),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            if 'stages' not in data:
                data['stages'] = []
            data['stages'].append(new_stage)
            self.save_data(data, self._data_file)
            return jsonify(new_stage)
