import logging
import sys
from datetime import datetime
from pathlib import Path
from config import Config


class CustomLogger:
    _instances = {}
    
    def __init__(self, name='ETL', log_level=None):
        self.name = name
        self.log_level = log_level or Config.LOG_LEVEL
        self._setup_logger()
    
    @classmethod
    def get_logger(cls, name='ETL'):
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]
    
    def _setup_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            log_dir = Path(Config.LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_dir / f'etl_{datetime.now().strftime("%Y%m%d")}.log'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message, **kwargs):
        self.logger.critical(message, extra=kwargs)
    
    def exception(self, message, **kwargs):
        self.logger.exception(message, extra=kwargs)


def get_logger(name='ETL'):
    return CustomLogger.get_logger(name)
