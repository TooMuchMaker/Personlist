from flask import Flask, render_template, jsonify, request
import os
import sys
from pathlib import Path

from .config import config
from .service_manager import service_manager
from .logger import get_logger

logger = get_logger('api_server')


def create_app():
    app = Flask(
        __name__,
        template_folder=str(config.app_dir / 'traework' / 'templates'),
        static_folder=str(config.app_dir / 'traework' / 'static')
    )
    
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    
    @app.route('/')
    def index():
        platforms = service_manager.get_all_platforms()
        return render_template('index.html', platforms=platforms)
    
    @app.route('/api/platforms')
    def api_platforms():
        platforms = service_manager.get_all_platforms()
        result = {}
        for pid, p in platforms.items():
            result[pid] = {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'port': p.port,
                'status': p.check_status(),
                'url': p.url,
                'icon': p.icon,
                'enabled': p.enabled,
                'auto_start': p.auto_start,
            }
        return jsonify(result)
    
    @app.route('/api/platform/<platform_id>')
    def api_platform(platform_id):
        p = service_manager.get_platform(platform_id)
        if not p:
            return jsonify({'error': 'Platform not found'}), 404
        
        return jsonify({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'port': p.port,
            'status': p.check_status(),
            'url': p.url,
            'icon': p.icon,
            'enabled': p.enabled,
            'auto_start': p.auto_start,
        })
    
    @app.route('/api/start/<platform_id>')
    def start_platform(platform_id):
        success = service_manager.start_platform(platform_id)
        if success:
            p = service_manager.get_platform(platform_id)
            return jsonify({
                'success': True,
                'message': f'{p.name} 启动成功',
                'url': p.url
            })
        return jsonify({'success': False, 'message': '启动失败'}), 500
    
    @app.route('/api/stop/<platform_id>')
    def stop_platform(platform_id):
        success = service_manager.stop_platform(platform_id)
        if success:
            return jsonify({'success': True, 'message': '已停止'})
        return jsonify({'success': False, 'message': '停止失败'}), 500
    
    @app.route('/api/start-all')
    def start_all():
        results = service_manager.start_all()
        return jsonify({'success': True, 'results': results})
    
    @app.route('/api/stop-all')
    def stop_all():
        results = service_manager.stop_all()
        return jsonify({'success': True, 'results': results})
    
    @app.route('/api/open/<platform_id>')
    def open_platform(platform_id):
        p = service_manager.get_platform(platform_id)
        if not p:
            return jsonify({'error': 'Platform not found'}), 404
        
        if p.check_status() == 'running':
            import webbrowser
            webbrowser.open(p.url)
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': '平台未运行'}), 400
    
    @app.route('/api/config')
    def get_config():
        return jsonify({
            'app': config.get('app'),
            'ui': config.get('ui'),
            'platforms': config.get('platforms'),
        })
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        data = request.json
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        for key, value in data.items():
            config.set(key, value)
        
        return jsonify({'success': True})
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok'})
    
    return app


def run_server():
    app = create_app()
    port = config.get_port('main')
    logger.info(f"Starting API server on port {port}")
    app.run(
        host='127.0.0.1',
        port=port,
        debug=config.debug,
        threaded=True
    )
