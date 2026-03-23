#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAEWORK - 人机共生工作平台
主入口文件
"""

import sys
import os

def main():
    from traework.core import config, get_logger
    from traework.app import App
    
    logger = get_logger('main')
    logger.info(f"TRAEWORK v{config.get('app.version', '1.0.0')} starting...")
    logger.info(f"App directory: {config.app_dir}")
    logger.info(f"Data directory: {config.data_dir}")
    
    app = App()
    app.run()


if __name__ == '__main__':
    main()
