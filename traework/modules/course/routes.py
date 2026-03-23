#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学校课程模块路由
"""

from flask import Blueprint, request, jsonify
from traework.core.data_manager import data_manager

course_bp = Blueprint('course', __name__, url_prefix='/api/course')


@course_bp.route('/courses', methods=['GET'])
def get_courses():
    data = data_manager.load_data('courses')
    return jsonify(data)


@course_bp.route('/courses/<course_id>', methods=['GET'])
def get_course(course_id):
    data = data_manager.load_data('courses')
    for course in data:
        if course.get('id') == course_id:
            return jsonify(course)
    return jsonify({'error': 'Course not found'}), 404


@course_bp.route('/courses', methods=['POST'])
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


@course_bp.route('/courses/<course_id>', methods=['PUT'])
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


@course_bp.route('/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    data = data_manager.load_data('courses')
    
    for i, course in enumerate(data):
        if course.get('id') == course_id:
            data.pop(i)
            data_manager.save_data('courses', data)
            return jsonify({'success': True})
    
    return jsonify({'error': 'Course not found'}), 404


@course_bp.route('/courses/<course_id>/assignments', methods=['POST'])
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


@course_bp.route('/courses/<course_id>/assignments/<assignment_id>', methods=['PUT'])
def update_assignment(course_id, assignment_id):
    assignment_data = request.json
    data = data_manager.load_data('courses')
    
    for course in data:
        if course.get('id') == course_id:
            for i, assignment in enumerate(course.get('assignments', [])):
                if assignment.get('id') == assignment_id:
                    assignment.update(assignment_data)
                    course['assignments'][i] = assignment
                    course['updated_at'] = data_manager.get_timestamp()
                    data_manager.save_data('courses', data)
                    return jsonify(assignment)
    
    return jsonify({'error': 'Assignment not found'}), 404


@course_bp.route('/sync_to_plan', methods=['POST'])
def sync_to_plan():
    """
    同步课程/作业到计划管理
    """
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


@course_bp.route('/courses/<course_id>/plans', methods=['GET'])
def get_course_plans(course_id):
    """
    获取课程关联的计划
    """
    import requests
    
    data = data_manager.load_data('courses')
    
    for course in data:
        if course.get('id') == course_id:
            linked_plans = course.get('linked_plans', [])
            plans = []
            
            for plan_id in linked_plans:
                try:
                    response = requests.get(
                        f'http://127.0.0.1:5000/api/plan/plans/{plan_id}'
                    )
                    if response.status_code == 200:
                        plans.append(response.json())
                except:
                    pass
            
            return jsonify(plans)
    
    return jsonify({'error': 'Course not found'}), 404


def register_routes(app):
    app.register_blueprint(course_bp)
