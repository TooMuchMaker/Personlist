import sys
import os
import webbrowser

from traework.platforms.base import BasePlatform
from traework.core.config import config
from traework.core.logger import get_logger
from flask import Flask, render_template, jsonify

logger = get_logger('main_platform')


class MainPlatform(BasePlatform):
    PLATFORM_ID = 'main'
    PLATFORM_NAME = '主控面板'
    
    def __init__(self):
        super().__init__()
    
    def create_app(self) -> Flask:
        if getattr(sys, 'frozen', False):
            template_dir = os.path.join(sys._MEIPASS, 'traework', 'templates')
        else:
            template_dir = str(config.app_dir / 'traework' / 'templates')
        
        app = Flask(__name__, template_folder=template_dir)
        return app
    
    def register_routes(self, app: Flask):
        
        @app.route('/')
        def index():
            return render_template('index.html')
        
        @app.route('/api/platforms')
        def get_platforms():
            from traework.core.service_manager import service_manager
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
                }
            return jsonify(result)
        
        @app.route('/api/platforms/<platform_id>')
        def get_platform(platform_id):
            from traework.core.service_manager import service_manager
            p = service_manager.get_platform(platform_id)
            if not p:
                return jsonify({'error': 'Platform not found'}), 404
            
            return jsonify({
                'id': p.id,
                'name': p.name,
                'status': p.check_status(),
                'url': p.url,
            })
        
        @app.route('/api/start/<platform_id>')
        def start_platform(platform_id):
            from traework.core.service_manager import service_manager
            success = service_manager.start_platform(platform_id)
            p = service_manager.get_platform(platform_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'{p.name} 启动成功',
                    'url': p.url
                })
            return jsonify({'success': False, 'message': '启动失败'}), 500
        
        @app.route('/api/stop/<platform_id>')
        def stop_platform(platform_id):
            from traework.core.service_manager import service_manager
            service_manager.stop_platform(platform_id)
            return jsonify({
                'success': True,
                'message': '已停止'
            })
        
        @app.route('/api/start-all')
        def start_all():
            from traework.core.service_manager import service_manager
            results = service_manager.start_all()
            return jsonify({'success': True, 'results': results})
        
        @app.route('/api/stop-all')
        def stop_all():
            from traework.core.service_manager import service_manager
            results = service_manager.stop_all()
            return jsonify({'success': True, 'results': results})
        
        @app.route('/api/open/<platform_id>')
        def open_platform(platform_id):
            from traework.core.service_manager import service_manager
            p = service_manager.get_platform(platform_id)
            if not p:
                return jsonify({'error': 'Platform not found'}), 404
            
            if p.check_status() == 'running':
                webbrowser.open(p.url)
                return jsonify({'success': True})
            return jsonify({'success': False, 'message': '平台未运行'}), 400
        
        @app.route('/api/open-logs')
        def open_logs():
            logs_dir = config.logs_dir
            if sys.platform == 'win32':
                os.startfile(str(logs_dir))
            else:
                import subprocess
                subprocess.run(['xdg-open', str(logs_dir)])
            return jsonify({'success': True})
