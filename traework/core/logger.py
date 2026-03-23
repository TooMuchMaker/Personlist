import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from .config import config


class LogManager:
    _loggers = {}
    _initialized = False
    
    @classmethod
    def initialize(cls):
        if cls._initialized:
            return
        cls._initialized = True
        
        log_dir = config.logs_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config.get_log_file('traework'),
            maxBytes=config.get('logging.max_size_mb', 10) * 1024 * 1024,
            backupCount=config.get('logging.backup_count', 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]
    
    @classmethod
    def get_platform_logger(cls, platform: str) -> logging.Logger:
        if not cls._initialized:
            cls.initialize()
        
        logger_name = f'traework.{platform}'
        if logger_name not in cls._loggers:
            logger = logging.getLogger(logger_name)
            
            log_file = config.get_log_file(platform)
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config.get('logging.max_size_mb', 10) * 1024 * 1024,
                backupCount=config.get('logging.backup_count', 5),
                encoding='utf-8'
            )
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            logger.addHandler(handler)
            
            cls._loggers[logger_name] = logger
        
        return cls._loggers[logger_name]


def get_logger(name: str = 'traework') -> logging.Logger:
    return LogManager.get_logger(name)


def get_platform_logger(platform: str) -> logging.Logger:
    return LogManager.get_platform_logger(platform)
