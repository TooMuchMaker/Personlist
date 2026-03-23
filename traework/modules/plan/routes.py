#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计划管理模块路由
"""

from flask import Blueprint, request, jsonify
from traework.core.data_manager import data_manager

plan_bp = Blueprint('plan', __name__, url_prefix='/api/plan')


@plan_bp.route('/plans', methods=['GET'])
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


@plan_bp.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    data = data_manager.load_data('plans')
    
    for ptype in ['long_term', 'mid_term', 'short_term']:
        for plan in data.get(ptype, []):
            if plan.get('id') == plan_id:
                plan['type'] = ptype
                return jsonify(plan)
    
    return jsonify({'error': 'Plan not found'}), 404


@plan_bp.route('/plans', methods=['POST'])
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


@plan_bp.route('/plans/<plan_id>', methods=['PUT'])
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


@plan_bp.route('/plans/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    data = data_manager.load_data('plans')
    
    for ptype in ['long_term', 'mid_term', 'short_term']:
        for i, plan in enumerate(data.get(ptype, [])):
            if plan.get('id') == plan_id:
                data[ptype].pop(i)
                data_manager.save_data('plans', data)
                return jsonify({'success': True})
    
    return jsonify({'error': 'Plan not found'}), 404


@plan_bp.route('/stages', methods=['GET'])
def get_stages():
    data = data_manager.load_data('plans')
    return jsonify(data.get('stages', []))


@plan_bp.route('/stages', methods=['POST'])
def create_stage():
    stage_data = request.json
    data = data_manager.load_data('plans')
    
    new_stage = {
        'id': data_manager.generate_id(),
        'plan_id': stage_data.get('plan_id'),
        'title': stage_data.get('title', ''),
        'description': stage_data.get('description', ''),
        'status': stage_data.get('status', 'pending'),
        'start_date': stage_data.get('start_date', ''),
        'end_date': stage_data.get('end_date', ''),
        'order': stage_data.get('order', 0),
        'created_at': data_manager.get_timestamp()
    }
    
    if 'stages' not in data:
        data['stages'] = []
    data['stages'].append(new_stage)
    data_manager.save_data('plans', data)
    
    return jsonify(new_stage), 201


@plan_bp.route('/stages/<stage_id>', methods=['PUT'])
def update_stage(stage_id):
    stage_data = request.json
    data = data_manager.load_data('plans')
    
    for i, stage in enumerate(data.get('stages', [])):
        if stage.get('id') == stage_id:
            stage.update(stage_data)
            data['stages'][i] = stage
            data_manager.save_data('plans', data)
            return jsonify(stage)
    
    return jsonify({'error': 'Stage not found'}), 404


@plan_bp.route('/stages/<stage_id>', methods=['DELETE'])
def delete_stage(stage_id):
    data = data_manager.load_data('plans')
    
    for i, stage in enumerate(data.get('stages', [])):
        if stage.get('id') == stage_id:
            data['stages'].pop(i)
            data_manager.save_data('plans', data)
            return jsonify({'success': True})
    
    return jsonify({'error': 'Stage not found'}), 404


@plan_bp.route('/sync', methods=['POST'])
def sync_to_plan():
    """
    从其他模块同步数据到计划管理
    """
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


@plan_bp.route('/source/<source_module>/<source_id>', methods=['GET'])
def get_plan_by_source(source_module, source_id):
    """
    根据来源查询关联的计划
    """
    data = data_manager.load_data('plans')
    
    for ptype in ['long_term', 'mid_term', 'short_term']:
        for plan in data.get(ptype, []):
            source = plan.get('source', {})
            if source.get('module') == source_module and source.get('id') == source_id:
                plan['type'] = ptype
                return jsonify(plan)
    
    return jsonify({'error': 'Plan not found'}), 404


def register_routes(app):
    app.register_blueprint(plan_bp)
