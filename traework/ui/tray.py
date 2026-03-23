import sys
import threading
from typing import Dict, Optional

from traework.core.config import config
from traework.core.logger import get_logger
from traework.core.service_manager import service_manager, PlatformInfo

logger = get_logger('tray')


class SystemTrayApp:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self._icon = None
        self._running = False
        self._menu = None
        self._platforms = {}
    
    def _create_icon(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            draw.ellipse([8, 8, size-8, size-8], fill='#667eea', outline='#5a6fd6', width=2)
            draw.ellipse([20, 20, size-20, size-20], fill='white')
            draw.ellipse([28, 28, size-28, size-28], fill='#667eea')
            
            return image
            
        except ImportError:
            logger.warning("pystray or PIL not installed")
            return None
    
    def _create_menu(self):
        try:
            import pystray
            
            self._platforms = service_manager.get_all_platforms()
            menu_items = []
            
            for platform_id, platform in self._platforms.items():
                status_icon = "✓" if platform.check_status() == 'running' else "○"
                menu_items.append(
                    pystray.MenuItem(
                        f"{status_icon} {platform.name}",
                        lambda item, pid=platform_id: self._toggle_platform(pid)
                    )
                )
            
            menu_items.append(pystray.Menu.SEPARATOR)
            
            menu_items.append(
                pystray.MenuItem("启动全部", self._start_all))
            menu_items.append(
                pystray.MenuItem("停止全部", self._stop_all))
            
            menu_items.append(pystray.Menu.SEPARATOR)
            
            menu_items.append(
                pystray.MenuItem("查看日志", self._open_logs))
            
            menu_items.append(pystray.Menu.SEPARATOR)
            
            menu_items.append(
                pystray.MenuItem("退出", self._quit))
            
            return pystray.Menu(*menu_items)
            
        except ImportError:
            return None
    
    def _toggle_platform(self, platform_id: str):
        platform = self._platforms.get(platform_id)
        if platform:
            if platform.check_status() == 'running':
                service_manager.stop_platform(platform_id)
            else:
                service_manager.start_platform(platform_id)
            self._update_menu()
    
    def _start_all(self):
        service_manager.start_all()
        self._update_menu()
    
    def _stop_all(self):
        service_manager.stop_all()
        self._update_menu()
    
    def _open_logs(self):
        import os
        logs_dir = config.logs_dir
        if sys.platform == 'win32':
            os.startfile(str(logs_dir))
        else:
            import subprocess
            subprocess.run(['xdg-open', str(logs_dir)])
    
    def _quit(self):
        logger.info("User requested quit")
        service_manager.stop_all()
        self._running = False
        if self._icon:
            self._icon.stop()
    
    def _update_menu(self):
        if self._icon:
            try:
                self._icon.menu = self._create_menu()
                self._icon.update_menu()
            except Exception as e:
                logger.error(f"Failed to update menu: {e}")
    
    def _on_status_change(self, platforms: Dict[str, PlatformInfo]):
        self._update_menu()
    
    def run(self):
        try:
            import pystray
            
            icon_image = self._create_icon()
            if icon_image is None:
                logger.error("Failed to create tray icon image")
                return False
            
            self._menu = self._create_menu()
            if self._menu is None:
                logger.error("Failed to create tray menu")
                return False
            
            self._icon = pystray.Icon(
                "TRAEWORK",
                icon_image,
                f"TRAEWORK v{config.get('app.version', '1.0.0')}",
                menu=self._menu
            )
            service_manager.add_status_callback(self._on_status_change)
            
            self._running = True
            
            logger.info("Starting system tray application")
            self._icon.run()
            
            return True
            
        except ImportError:
            logger.warning("pystray not installed, running without system tray")
            return self._run_fallback()
    
    def _run_fallback(self):
        import time
        
        logger.info("Running in fallback mode (no system tray)")
        self._running = True
        
        while self._running:
            time.sleep(1)
        
        return True


def run_tray():
    app = SystemTrayApp()
    return app.run()
