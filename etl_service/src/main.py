import sys
import schedule
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl_manager import ETLManager
from src.config import Config
from src.utils.logger_util import get_logger


logger = get_logger('Main')


def run_etl_job():
    logger.info("=" * 50)
    logger.info(f"Iniciando job ETL - {datetime.now()}")
    logger.info("=" * 50)
    
    try:
        Config.validate()
        
        manager = ETLManager(Config.SOURCE_TYPE)
        result = manager.run_pipeline()
        
        if result['success']:
            logger.info("Job ETL completado exitosamente")
            logger.info(f"Duración: {result['duration_seconds']:.2f} segundos")
            logger.info(f"Productos cargados: {result['stats']['products_loaded']}")
            logger.info(f"Inventario ajustado: {result['stats']['inventory_adjusted']}")
        else:
            logger.error(f"Job ETL falló: {result['error']}")
            
    except Exception as e:
        logger.exception(f"Error en job ETL: {e}")


def main():
    logger.info("Servicio ETL de Inventario iniciado")
    logger.info(f"Fuente de datos: {Config.SOURCE_TYPE}")
    logger.info(f"Programación: {Config.SCHEDULE_CRON}")
    logger.info(f"Odoo URL: {Config.ODOO_URL}")
    
    schedule.every().hour.do(run_etl_job)
    
    logger.info("Primera ejecución inmediata...")
    run_etl_job()
    
    logger.info("Esperando siguiente ejecución programada...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    main()
