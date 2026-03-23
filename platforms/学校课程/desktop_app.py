import webview
import threading
import os
import sys
from app import app
import json
from datetime import datetime
import uuid
import shutil
import platform

# 全局变量
global window

# 配置
PORT = 5002
DEBUG = False

# API 函数已移至 Api 类中

def start_flask():
    """在后台线程中启动 Flask 服务器"""
    app.run(debug=DEBUG, host='127.0.0.1', port=PORT, threaded=True)

class Api:
    """暴露给前端的 API 类"""
    def select_folder(self):
        """选择文件夹"""
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            return result[0]
        return None
    
    def select_file(self):
        """选择文件"""
        result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True)
        if result:
            return result
        return []
    
    def get_file_info(self, file_path):
        """获取文件信息"""
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        return {
            "name": os.path.basename(file_path),
            "path": file_path,
            "size": os.path.getsize(file_path),
            "is_file": os.path.isfile(file_path),
            "is_dir": os.path.isdir(file_path),
            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def list_directory(self, path):
        """列出目录内容"""
        if not os.path.exists(path):
            return {"error": "Path not found"}
        
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                items.append({
                    "name": item,
                    "path": item_path,
                    "is_file": os.path.isfile(item_path),
                    "is_dir": os.path.isdir(item_path),
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                })
        except Exception as e:
            return {"error": str(e)}
        
        return {"items": items}

def main():
    """主函数"""
    global window
    
    # 启动 Flask 服务器
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 创建 API 实例
    api = Api()
    
    # 创建 WebView 窗口
    window = webview.create_window(
        '学校课程管理',
        f'http://127.0.0.1:{PORT}',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600),
        js_api=api
    )
    
    # 启动 WebView
    webview.start(
        private_mode=False,
        debug=DEBUG
    )

if __name__ == '__main__':
    # 确保课程文件目录存在
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'course_files')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # 启动应用
    main()
