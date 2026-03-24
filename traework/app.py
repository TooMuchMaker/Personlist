#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK 应用主类
"""

import sys
import os
import threading
import time
from pathlib import Path

from .core import config, get_logger

logger = get_logger('app')


class App:
    def __init__(self):
        self._running = False
        self._flask_app = None
    
    def run(self):
        self._running = True
        
        logger.info("Starting Flask server...")
        self.start_flask_server()
        
        logger.info("Checking for updates...")
        self._check_updates_on_startup()
        
        logger.info("Starting desktop window...")
        self.run_desktop_window()
        
        logger.info("Application shutting down...")
    
    def _check_updates_on_startup(self):
        """启动时检查更新（后台线程）"""
        import threading
        from .core.updater import updater
        
        def check():
            try:
                updater.check_for_updates()
            except Exception as e:
                logger.error(f"Failed to check updates on startup: {e}")
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def start_flask_server(self):
        from flask import Flask, render_template, jsonify
        
        if getattr(sys, 'frozen', False):
            template_dir = os.path.join(sys._MEIPASS, 'traework', 'templates')
            static_dir = os.path.join(sys._MEIPASS, 'traework', 'static')
        else:
            template_dir = str(config.app_dir / 'traework' / 'templates')
            static_dir = str(config.app_dir / 'traework' / 'static')
        
        self._flask_app = Flask(__name__, 
                                template_folder=template_dir,
                                static_folder=static_dir)
        
        self._register_routes()
        
        port = config.get_port('main')
        
        def run_server():
            self._flask_app.run(host='127.0.0.1', port=port, threaded=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        time.sleep(1)
        logger.info(f"Flask server started on port {port}")
    
    def _register_routes(self):
        from flask import render_template, jsonify, request
        
        @self._flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self._flask_app.route('/api/platforms')
        def get_platforms():
            return jsonify({
                'plan': {'id': 'plan', 'name': '计划管理', 'status': 'running'},
                'course': {'id': 'course', 'name': '学校课程', 'status': 'running'},
                'algorithm': {'id': 'algorithm', 'name': '信竞知识', 'status': 'running'},
                'project': {'id': 'project', 'name': '项目管理', 'status': 'running'},
            })
        
        self._register_update_routes()
        self._register_plan_routes()
        self._register_course_routes()
        self._register_algorithm_routes()
        self._register_project_routes()
    
    def _register_plan_routes(self):
        from flask import jsonify, request
        from .core.data_manager import data_manager
        
        @self._flask_app.route('/api/plan/plans', methods=['GET'])
        def get_plans():
            plan_type = request.args.get('type')
            data = data_manager.load_data('plans')
            
            if plan_type and plan_type in ['long_term', 'mid_term', 'short_term']:
                return jsonify(data.get(plan_type, []))
            
            all_plans = []
            for ptype in ['long_term', 'mid_term', 'short_term']:
                for plan in data.get(ptype, []):
                    plan['type'] = ptype
                    all_plans.append(plan)
            
            return jsonify(all_plans)
        
        @self._flask_app.route('/api/plan/plans/<plan_id>', methods=['GET'])
        def get_plan(plan_id):
            data = data_manager.load_data('plans')
            
            for ptype in ['long_term', 'mid_term', 'short_term']:
                for plan in data.get(ptype, []):
                    if plan.get('id') == plan_id:
                        plan['type'] = ptype
                        return jsonify(plan)
            
            return jsonify({'error': 'Plan not found'}), 404
        
        @self._flask_app.route('/api/plan/plans', methods=['POST'])
        def create_plan():
            plan_data = request.json
            plan_type = plan_data.get('type', 'short_term')
            
            if plan_type not in ['long_term', 'mid_term', 'short_term']:
                plan_type = 'short_term'
            
            data = data_manager.load_data('plans')
            
            new_plan = {
                'id': data_manager.generate_id(),
                'title': plan_data.get('title', ''),
                'description': plan_data.get('description', ''),
                'priority': plan_data.get('priority', 'medium'),
                'status': plan_data.get('status', 'pending'),
                'start_date': plan_data.get('start_date', ''),
                'end_date': plan_data.get('end_date', ''),
                'tags': plan_data.get('tags', []),
                'progress': 0,
                'stages': [],
                'source': plan_data.get('source'),
                'created_at': data_manager.get_timestamp(),
                'updated_at': data_manager.get_timestamp()
            }
            
            data[plan_type].append(new_plan)
            data_manager.save_data('plans', data)
            
            new_plan['type'] = plan_type
            return jsonify(new_plan), 201
        
        @self._flask_app.route('/api/plan/plans/<plan_id>', methods=['PUT'])
        def update_plan(plan_id):
            plan_data = request.json
            data = data_manager.load_data('plans')
            
            for ptype in ['long_term', 'mid_term', 'short_term']:
                for i, plan in enumerate(data.get(ptype, [])):
                    if plan.get('id') == plan_id:
                        plan.update(plan_data)
                        plan['updated_at'] = data_manager.get_timestamp()
                        data[ptype][i] = plan
                        data_manager.save_data('plans', data)
                        plan['type'] = ptype
                        return jsonify(plan)
            
            return jsonify({'error': 'Plan not found'}), 404
        
        @self._flask_app.route('/api/plan/plans/<plan_id>', methods=['DELETE'])
        def delete_plan(plan_id):
            data = data_manager.load_data('plans')
            
            for ptype in ['long_term', 'mid_term', 'short_term']:
                for i, plan in enumerate(data.get(ptype, [])):
                    if plan.get('id') == plan_id:
                        data[ptype].pop(i)
                        data_manager.save_data('plans', data)
                        return jsonify({'success': True})
            
            return jsonify({'error': 'Plan not found'}), 404
        
        @self._flask_app.route('/api/plan/sync', methods=['POST'])
        def sync_to_plan():
            sync_data = request.json
            
            source_module = sync_data.get('source_module')
            source_type = sync_data.get('source_type')
            source_id = sync_data.get('source_id')
            plan_type = sync_data.get('plan_type', 'short_term')
            
            data = data_manager.load_data('plans')
            
            new_plan = {
                'id': data_manager.generate_id(),
                'title': sync_data.get('title', ''),
                'description': sync_data.get('description', ''),
                'priority': sync_data.get('priority', 'medium'),
                'status': 'pending',
                'start_date': sync_data.get('start_date', ''),
                'end_date': sync_data.get('end_date', ''),
                'tags': sync_data.get('tags', []),
                'progress': 0,
                'stages': sync_data.get('stages', []),
                'source': {
                    'module': source_module,
                    'type': source_type,
                    'id': source_id,
                    'name': sync_data.get('source_name', '')
                },
                'created_at': data_manager.get_timestamp(),
                'updated_at': data_manager.get_timestamp()
            }
            
            if plan_type not in data:
                data[plan_type] = []
            data[plan_type].append(new_plan)
            data_manager.save_data('plans', data)
            
            new_plan['type'] = plan_type
            return jsonify(new_plan), 201
    
    def _register_course_routes(self):
        from flask import jsonify, request
        from .core.data_manager import data_manager
        
        @self._flask_app.route('/api/course/courses', methods=['GET'])
        def get_courses():
            data = data_manager.load_data('courses')
            return jsonify(data)
        
        @self._flask_app.route('/api/course/courses/<course_id>', methods=['GET'])
        def get_course(course_id):
            data = data_manager.load_data('courses')
            for course in data:
                if course.get('id') == course_id:
                    return jsonify(course)
            return jsonify({'error': 'Course not found'}), 404
        
        @self._flask_app.route('/api/course/courses', methods=['POST'])
        def create_course():
            course_data = request.json
            data = data_manager.load_data('courses')
            
            new_course = {
                'id': data_manager.generate_id(),
                'name': course_data.get('name', ''),
                'teacher': course_data.get('teacher', ''),
                'category': course_data.get('category', ''),
                'description': course_data.get('description', ''),
                'schedule': course_data.get('schedule', ''),
                'classroom': course_data.get('classroom', ''),
                'materials': [],
                'assignments': [],
                'linked_plans': [],
                'created_at': data_manager.get_timestamp(),
                'updated_at': data_manager.get_timestamp()
            }
            
            data.append(new_course)
            data_manager.save_data('courses', data)
            
            return jsonify(new_course), 201
        
        @self._flask_app.route('/api/course/courses/<course_id>', methods=['PUT'])
        def update_course(course_id):
            course_data = request.json
            data = data_manager.load_data('courses')
            
            for i, course in enumerate(data):
                if course.get('id') == course_id:
                    course.update(course_data)
                    course['updated_at'] = data_manager.get_timestamp()
                    data[i] = course
                    data_manager.save_data('courses', data)
                    return jsonify(course)
            
            return jsonify({'error': 'Course not found'}), 404
        
        @self._flask_app.route('/api/course/courses/<course_id>', methods=['DELETE'])
        def delete_course(course_id):
            data = data_manager.load_data('courses')
            
            for i, course in enumerate(data):
                if course.get('id') == course_id:
                    data.pop(i)
                    data_manager.save_data('courses', data)
                    return jsonify({'success': True})
            
            return jsonify({'error': 'Course not found'}), 404
        
        @self._flask_app.route('/api/course/courses/<course_id>/assignments', methods=['POST'])
        def create_assignment(course_id):
            assignment_data = request.json
            data = data_manager.load_data('courses')
            
            for course in data:
                if course.get('id') == course_id:
                    new_assignment = {
                        'id': data_manager.generate_id(),
                        'title': assignment_data.get('title', ''),
                        'description': assignment_data.get('description', ''),
                        'due_date': assignment_data.get('due_date', ''),
                        'completed': False,
                        'linked_plan_id': None,
                        'created_at': data_manager.get_timestamp()
                    }
                    
                    if 'assignments' not in course:
                        course['assignments'] = []
                    course['assignments'].append(new_assignment)
                    course['updated_at'] = data_manager.get_timestamp()
                    data_manager.save_data('courses', data)
                    
                    return jsonify(new_assignment), 201
            
            return jsonify({'error': 'Course not found'}), 404
        
        @self._flask_app.route('/api/course/sync_to_plan', methods=['POST'])
        def course_sync_to_plan():
            import requests
            
            sync_data = request.json
            course_id = sync_data.get('course_id')
            assignment_id = sync_data.get('assignment_id')
            sync_type = sync_data.get('sync_type', 'study_plan')
            
            data = data_manager.load_data('courses')
            
            for course in data:
                if course.get('id') == course_id:
                    if sync_type == 'assignment' and assignment_id:
                        for assignment in course.get('assignments', []):
                            if assignment.get('id') == assignment_id:
                                plan_data = {
                                    'source_module': 'course',
                                    'source_type': 'assignment',
                                    'source_id': assignment_id,
                                    'plan_type': 'short_term',
                                    'title': f"完成作业: {assignment.get('title', '')}",
                                    'description': f"课程: {course.get('name', '')}\n作业: {assignment.get('description', '')}",
                                    'priority': 'high',
                                    'end_date': assignment.get('due_date', ''),
                                    'source_name': f"{course.get('name', '')} - {assignment.get('title', '')}"
                                }
                                
                                try:
                                    response = requests.post(
                                        'http://127.0.0.1:5000/api/plan/sync',
                                        json=plan_data
                                    )
                                    if response.status_code == 201:
                                        plan = response.json()
                                        assignment['linked_plan_id'] = plan.get('id')
                                        if 'linked_plans' not in course:
                                            course['linked_plans'] = []
                                        if plan.get('id') not in course['linked_plans']:
                                            course['linked_plans'].append(plan.get('id'))
                                        data_manager.save_data('courses', data)
                                        return jsonify({'success': True, 'plan': plan})
                                except Exception as e:
                                    return jsonify({'error': str(e)}), 500
                    
                    elif sync_type == 'study_plan':
                        plan_data = {
                            'source_module': 'course',
                            'source_type': 'course',
                            'source_id': course_id,
                            'plan_type': 'mid_term',
                            'title': f"学习课程: {course.get('name', '')}",
                            'description': course.get('description', ''),
                            'priority': 'medium',
                            'source_name': course.get('name', '')
                        }
                        
                        try:
                            response = requests.post(
                                'http://127.0.0.1:5000/api/plan/sync',
                                json=plan_data
                            )
                            if response.status_code == 201:
                                plan = response.json()
                                if 'linked_plans' not in course:
                                    course['linked_plans'] = []
                                if plan.get('id') not in course['linked_plans']:
                                    course['linked_plans'].append(plan.get('id'))
                                data_manager.save_data('courses', data)
                                return jsonify({'success': True, 'plan': plan})
                        except Exception as e:
                            return jsonify({'error': str(e)}), 500
            
            return jsonify({'error': 'Course not found'}), 404
    
    def _register_algorithm_routes(self):
        from flask import jsonify, request
        from .core.data_manager import data_manager
        
        @self._flask_app.route('/api/algorithm/templates', methods=['GET'])
        def get_templates():
            data = data_manager.load_data('knowledge')
            return jsonify(data.get('templates', []))
        
        @self._flask_app.route('/api/algorithm/templates', methods=['POST'])
        def create_template():
            template_data = request.json
            data = data_manager.load_data('knowledge')
            
            new_template = {
                'id': data_manager.generate_id(),
                'name': template_data.get('name', ''),
                'category_id': template_data.get('category_id'),
                'subcategory': template_data.get('subcategory', ''),
                'description': template_data.get('description', ''),
                'code': template_data.get('code', ''),
                'language': template_data.get('language', 'python'),
                'complexity': template_data.get('complexity', ''),
                'prerequisites': template_data.get('prerequisites', []),
                'linked_plans': [],
                'created_at': data_manager.get_timestamp(),
                'updated_at': data_manager.get_timestamp()
            }
            
            if 'templates' not in data:
                data['templates'] = []
            data['templates'].append(new_template)
            data_manager.save_data('knowledge', data)
            
            return jsonify(new_template), 201
        
        @self._flask_app.route('/api/algorithm/templates/<template_id>', methods=['PUT'])
        def update_template(template_id):
            template_data = request.json
            data = data_manager.load_data('knowledge')
            
            for i, template in enumerate(data.get('templates', [])):
                if template.get('id') == template_id:
                    template.update(template_data)
                    template['updated_at'] = data_manager.get_timestamp()
                    data['templates'][i] = template
                    data_manager.save_data('knowledge', data)
                    return jsonify(template)
            
            return jsonify({'error': 'Template not found'}), 404
        
        @self._flask_app.route('/api/algorithm/templates/<template_id>', methods=['DELETE'])
        def delete_template(template_id):
            data = data_manager.load_data('knowledge')
            
            for i, template in enumerate(data.get('templates', [])):
                if template.get('id') == template_id:
                    data['templates'].pop(i)
                    data_manager.save_data('knowledge', data)
                    return jsonify({'success': True})
            
            return jsonify({'error': 'Template not found'}), 404
        
        @self._flask_app.route('/api/algorithm/problems', methods=['GET'])
        def get_problems():
            data = data_manager.load_data('knowledge')
            return jsonify(data.get('problems', []))
        
        @self._flask_app.route('/api/algorithm/problems', methods=['POST'])
        def create_problem():
            problem_data = request.json
            data = data_manager.load_data('knowledge')
            
            new_problem = {
                'id': data_manager.generate_id(),
                'title': problem_data.get('title', ''),
                'url': problem_data.get('url', ''),
                'status': problem_data.get('status', 'todo'),
                'difficulty': problem_data.get('difficulty', 'medium'),
                'tags': problem_data.get('tags', []),
                'linked_plan_id': None,
                'created_at': data_manager.get_timestamp()
            }
            
            if 'problems' not in data:
                data['problems'] = []
            data['problems'].append(new_problem)
            data_manager.save_data('knowledge', data)
            
            return jsonify(new_problem), 201
        
        @self._flask_app.route('/api/algorithm/problems/<problem_id>', methods=['PUT'])
        def update_problem(problem_id):
            problem_data = request.json
            data = data_manager.load_data('knowledge')
            
            for i, problem in enumerate(data.get('problems', [])):
                if problem.get('id') == problem_id:
                    problem.update(problem_data)
                    data['problems'][i] = problem
                    data_manager.save_data('knowledge', data)
                    return jsonify(problem)
            
            return jsonify({'error': 'Problem not found'}), 404
        
        @self._flask_app.route('/api/algorithm/problems/<problem_id>', methods=['DELETE'])
        def delete_problem(problem_id):
            data = data_manager.load_data('knowledge')
            
            for i, problem in enumerate(data.get('problems', [])):
                if problem.get('id') == problem_id:
                    data['problems'].pop(i)
                    data_manager.save_data('knowledge', data)
                    return jsonify({'success': True})
            
            return jsonify({'error': 'Problem not found'}), 404
        
        @self._flask_app.route('/api/algorithm/sync_to_plan', methods=['POST'])
        def algorithm_sync_to_plan():
            import requests
            from .core.logger import get_logger
            logger = get_logger('algorithm')
            
            sync_data = request.json
            template_id = sync_data.get('template_id')
            problem_id = sync_data.get('problem_id')
            sync_type = sync_data.get('sync_type', 'learning')
            
            logger.info(f"sync_to_plan called: sync_data={sync_data}")
            logger.info(f"template_id={template_id}, problem_id={problem_id}, sync_type={sync_type}")
            logger.info(f"sync_type type: {type(sync_type)}, template_id type: {type(template_id)}")
            logger.info(f"sync_type == 'learning': {sync_type == 'learning'}")
            logger.info(f"template_id is truthy: {bool(template_id)}")
            
            data = data_manager.load_data('knowledge')
            
            if sync_type == 'practice' and problem_id:
                for problem in data.get('problems', []):
                    if problem.get('id') == problem_id:
                        plan_data = {
                            'source_module': 'algorithm',
                            'source_type': 'problem',
                            'source_id': problem_id,
                            'plan_type': 'short_term',
                            'title': f"解决题目: {problem.get('title', '')}",
                            'description': f"难度: {problem.get('difficulty', '')}\n链接: {problem.get('url', '')}",
                            'priority': 'high' if problem.get('difficulty') == 'hard' else 'medium',
                            'source_name': problem.get('title', '')
                        }
                        
                        try:
                            response = requests.post(
                                'http://127.0.0.1:5000/api/plan/sync',
                                json=plan_data
                            )
                            if response.status_code == 201:
                                plan = response.json()
                                problem['linked_plan_id'] = plan.get('id')
                                data_manager.save_data('knowledge', data)
                                return jsonify({'success': True, 'plan': plan})
                        except Exception as e:
                            return jsonify({'error': str(e)}), 500
            
            elif sync_type == 'learning' and template_id:
                logger.info(f"Searching for template_id={template_id} in {len(data.get('templates', []))} templates")
                for i, template in enumerate(data.get('templates', [])):
                    logger.info(f"Template {i}: id={template.get('id')}, name={template.get('name')}")
                    if template.get('id') == template_id:
                        plan_data = {
                            'source_module': 'algorithm',
                            'source_type': 'template',
                            'source_id': template_id,
                            'plan_type': 'mid_term',
                            'title': f"掌握算法: {template.get('name', '')}",
                            'description': template.get('description', ''),
                            'priority': 'medium',
                            'source_name': template.get('name', '')
                        }
                        
                        try:
                            response = requests.post(
                                'http://127.0.0.1:5000/api/plan/sync',
                                json=plan_data
                            )
                            if response.status_code == 201:
                                plan = response.json()
                                if 'linked_plans' not in template:
                                    template['linked_plans'] = []
                                if plan.get('id') not in template['linked_plans']:
                                    template['linked_plans'].append(plan.get('id'))
                                data_manager.save_data('knowledge', data)
                                return jsonify({'success': True, 'plan': plan})
                        except Exception as e:
                            return jsonify({'error': str(e)}), 500
            
            logger.warning(f"sync_to_plan: Not found - templates count: {len(data.get('templates', []))}, problems count: {len(data.get('problems', []))}")
            return jsonify({'error': 'Not found'}), 404
    
    def _register_project_routes(self):
        from flask import jsonify, request
        from .core.data_manager import data_manager
        
        @self._flask_app.route('/api/project/projects', methods=['GET'])
        def get_projects():
            project_type = request.args.get('type', 'all')
            data = data_manager.load_data('projects')
            
            if project_type == 'original':
                return jsonify(data.get('original', []))
            elif project_type == 'collected':
                return jsonify(data.get('collected', []))
            else:
                return jsonify({
                    'original': data.get('original', []),
                    'collected': data.get('collected', [])
                })
        
        @self._flask_app.route('/api/project/projects', methods=['POST'])
        def create_project():
            project_data = request.json
            is_collected = project_data.get('is_collected', False)
            data = data_manager.load_data('projects')
            
            new_project = {
                'id': data_manager.generate_id(),
                'name': project_data.get('name', ''),
                'description': project_data.get('description', ''),
                'category': project_data.get('category', ''),
                'tech_stack': project_data.get('tech_stack', []),
                'source_url': project_data.get('source_url', ''),
                'local_path': project_data.get('local_path', ''),
                'status': project_data.get('status', 'planning'),
                'files': [],
                'linked_plan_id': None,
                'is_collected': is_collected,
                'stars': project_data.get('stars', ''),
                'notes': project_data.get('notes', ''),
                'created_at': data_manager.get_timestamp(),
                'updated_at': data_manager.get_timestamp()
            }
            
            key = 'collected' if is_collected else 'original'
            if key not in data:
                data[key] = []
            data[key].append(new_project)
            data_manager.save_data('projects', data)
            
            return jsonify(new_project), 201
        
        @self._flask_app.route('/api/project/projects/<project_id>', methods=['PUT'])
        def update_project(project_id):
            project_data = request.json
            data = data_manager.load_data('projects')
            
            for key in ['original', 'collected']:
                for i, project in enumerate(data.get(key, [])):
                    if project.get('id') == project_id:
                        project.update(project_data)
                        project['updated_at'] = data_manager.get_timestamp()
                        data[key][i] = project
                        data_manager.save_data('projects', data)
                        return jsonify(project)
            
            return jsonify({'error': 'Project not found'}), 404
        
        @self._flask_app.route('/api/project/projects/<project_id>', methods=['DELETE'])
        def delete_project(project_id):
            data = data_manager.load_data('projects')
            
            for key in ['original', 'collected']:
                for i, project in enumerate(data.get(key, [])):
                    if project.get('id') == project_id:
                        data[key].pop(i)
                        data_manager.save_data('projects', data)
                        return jsonify({'success': True})
            
            return jsonify({'error': 'Project not found'}), 404
        
        @self._flask_app.route('/api/project/sync_to_plan', methods=['POST'])
        def project_sync_to_plan():
            import requests
            
            sync_data = request.json
            project_id = sync_data.get('project_id')
            sync_type = sync_data.get('sync_type', 'development')
            
            data = data_manager.load_data('projects')
            
            for key in ['original', 'collected']:
                for project in data.get(key, []):
                    if project.get('id') == project_id:
                        if sync_type == 'development':
                            plan_data = {
                                'source_module': 'project',
                                'source_type': 'project',
                                'source_id': project_id,
                                'plan_type': 'long_term',
                                'title': f"开发项目: {project.get('name', '')}",
                                'description': project.get('description', ''),
                                'priority': 'medium',
                                'source_name': project.get('name', '')
                            }
                        else:
                            plan_data = {
                                'source_module': 'project',
                                'source_type': 'project',
                                'source_id': project_id,
                                'plan_type': 'mid_term',
                                'title': f"完成项目里程碑: {project.get('name', '')}",
                                'description': project.get('description', ''),
                                'priority': 'high',
                                'source_name': project.get('name', '')
                            }
                        
                        try:
                            response = requests.post(
                                'http://127.0.0.1:5000/api/plan/sync',
                                json=plan_data
                            )
                            if response.status_code == 201:
                                plan = response.json()
                                project['linked_plan_id'] = plan.get('id')
                                data_manager.save_data('projects', data)
                                return jsonify({'success': True, 'plan': plan})
                        except Exception as e:
                            return jsonify({'error': str(e)}), 500
            
            return jsonify({'error': 'Project not found'}), 404
    
    def _register_update_routes(self):
        from flask import jsonify, request
        from .core.updater import updater
        
        @self._flask_app.route('/api/update/version', methods=['GET'])
        def get_version():
            return jsonify({
                'current_version': updater.current_version,
                'latest_version': updater.latest_version,
                'has_update': updater.has_update
            })
        
        @self._flask_app.route('/api/update/check', methods=['POST'])
        def check_update():
            has_update = updater.check_for_updates(force=True)
            return jsonify({
                'has_update': has_update,
                'current_version': updater.current_version,
                'latest_version': updater.latest_version,
                'update_info': updater.update_info
            })
        
        @self._flask_app.route('/api/update/download', methods=['POST'])
        def download_update():
            save_path = updater.download_update()
            if save_path:
                return jsonify({
                    'success': True,
                    'path': str(save_path)
                })
            return jsonify({'success': False, 'error': 'Download failed'}), 500
        
        @self._flask_app.route('/api/update/install', methods=['POST'])
        def install_update():
            data = request.json
            exe_path = data.get('path')
            if not exe_path:
                return jsonify({'success': False, 'error': 'No path provided'}), 400
            
            from pathlib import Path
            success = updater.install_update(Path(exe_path))
            if success:
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Install failed'}), 500
    
    def run_desktop_window(self):
        import webview
        
        main_port = config.get_port('main')
        url = f"http://127.0.0.1:{main_port}/"
        
        time.sleep(1)
        
        window = webview.create_window(
            'TRAEWORK - 人机共生工作平台',
            url,
            width=1200,
            height=800,
            resizable=True,
            min_size=(800, 600)
        )
        
        webview.start(debug=config.debug)
        self._running = False
