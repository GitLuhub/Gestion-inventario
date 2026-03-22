import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = os.getenv('ETL_DATA_PATH', str(BASE_DIR / 'data'))
    LOG_DIR = os.getenv('ETL_LOG_DIR', str(BASE_DIR / 'logs'))
    
    ODOO_URL = os.getenv('ODOO_URL', 'http://odoo_app:8069')
    ODOO_DB = os.getenv('ODOO_DB', 'odoo_db')
    ODOO_USER = os.getenv('ODOO_USER', 'admin')
    ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', '')
    if not ODOO_PASSWORD:
        password_file = os.getenv('ODOO_PASSWORD_FILE', '')
        if password_file and os.path.exists(password_file):
            with open(password_file, 'r') as f:
                ODOO_PASSWORD = f.read().strip()
    
    EXTERNAL_API_URL = os.getenv('EXTERNAL_API_URL', '')
    EXTERNAL_API_KEY = os.getenv('EXTERNAL_API_KEY', '')
    if not EXTERNAL_API_KEY:
        key_file = os.getenv('EXTERNAL_API_KEY_FILE', '')
        if key_file and os.path.exists(key_file):
            with open(key_file, 'r') as f:
                EXTERNAL_API_KEY = f.read().strip()
    
    CSV_PRODUCTS_PATH = os.path.join(DATA_DIR, 'products.csv')
    CSV_INVENTORY_PATH = os.path.join(DATA_DIR, 'inventory.csv')
    
    BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '100'))
    MAX_RETRIES = int(os.getenv('ETL_MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('ETL_RETRY_DELAY', '5'))
    LOG_LEVEL = os.getenv('ETL_LOG_LEVEL', 'INFO')
    SCHEDULE_CRON = os.getenv('ETL_SCHEDULE_CRON', '*/15 * * * *')
    
    DB_CONNECTION_STRING = os.getenv(
        'DB_CONNECTION_STRING',
        'postgresql://odoo:odoo@pg_db:5432/odoo_db'
    )
    
    SOURCE_TYPE = os.getenv('ETL_SOURCE_TYPE', 'csv')
    SUPPORTED_SOURCES = ['csv', 'api', 'db', 'excel']
    
    @classmethod
    def validate(cls):
        if cls.SOURCE_TYPE not in cls.SUPPORTED_SOURCES:
            raise ValueError(
                f"Fuente no soportada: {cls.SOURCE_TYPE}. "
                f"Soporta: {cls.SUPPORTED_SOURCES}"
            )
        if not cls.ODOO_PASSWORD:
            raise ValueError("ODOO_PASSWORD no configurado")
        return True
