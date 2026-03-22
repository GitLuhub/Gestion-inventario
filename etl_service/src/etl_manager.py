from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger_util import get_logger
from data_sources import CSVDataSource, APIDataSource, DBDataSource, BaseDataSource
from transformers import ProductTransformer, InventoryTransformer
from loaders import OdooLoader
from config import Config


class ETLManager:
    def __init__(self, source_type: str = None):
        self.source_type = source_type or Config.SOURCE_TYPE
        self.logger = get_logger('ETLManager')
        self.start_time = None
        self.stats = {
            'products_extracted': 0,
            'products_transformed': 0,
            'products_loaded': 0,
            'inventory_extracted': 0,
            'inventory_transformed': 0,
            'inventory_adjusted': 0,
            'errors': [],
            'start_time': None,
            'end_time': None,
        }
        
        self.data_source = self._create_data_source()
        self.product_transformer = ProductTransformer()
        self.inventory_transformer = InventoryTransformer()
        self.odoo_loader = OdooLoader()
    
    def _create_data_source(self) -> BaseDataSource:
        source_config = {'source_type': self.source_type}
        
        if self.source_type == 'csv':
            self.logger.info("Usando fuente CSV")
            return CSVDataSource(source_config)
        elif self.source_type == 'api':
            self.logger.info("Usando fuente API")
            return APIDataSource(source_config)
        elif self.source_type == 'db':
            self.logger.info("Usando fuente DB")
            return DBDataSource(source_config)
        else:
            raise ValueError(f"Fuente no soportada: {self.source_type}")
    
    def run_pipeline(self, sync_type: str = 'full') -> Dict[str, Any]:
        self.start_time = datetime.now()
        self.stats['start_time'] = self.start_time.isoformat()
        self.logger.info(f"Iniciando pipeline ETL - Tipo: {sync_type}")
        
        try:
            if not self.odoo_loader.test_connection():
                raise Exception("No se puede conectar a Odoo")
            
            if not self.data_source.test_connection():
                raise Exception("No se puede conectar a la fuente de datos")
            
            self._run_products_etl()
            
            self._run_inventory_etl()
            
            self.stats['end_time'] = datetime.now().isoformat()
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"Pipeline completado en {duration:.2f} segundos")
            self.logger.info(f"Estadísticas: {self.stats}")
            
            return {
                'success': True,
                'stats': self.stats,
                'duration_seconds': duration,
            }
            
        except Exception as e:
            self.stats['errors'].append(str(e))
            self.stats['end_time'] = datetime.now().isoformat()
            self.logger.error(f"Error en pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats,
            }
    
    def _run_products_etl(self):
        self.logger.info("=== ETL de Productos ===")
        
        raw_products = self.data_source.extract_products()
        self.stats['products_extracted'] = len(raw_products)
        self.logger.info(f"Extraídos {len(raw_products)} productos")
        
        if not raw_products:
            self.logger.warning("No se extrajeron productos")
            return
        
        transformed_products = self.product_transformer.transform(raw_products)
        self.stats['products_transformed'] = len(transformed_products)
        
        product_mapping = {}
        for product in transformed_products:
            try:
                if self.product_transformer.validate(product):
                    product_id = self.odoo_loader.create_or_update_product(product)
                    product_mapping[product.get('default_code')] = product_id
                    self.stats['products_loaded'] += 1
            except Exception as e:
                self.stats['errors'].append(f"Producto {product.get('name')}: {e}")
                self.logger.error(f"Error al cargar producto: {e}")
        
        return product_mapping
    
    def _run_inventory_etl(self):
        self.logger.info("=== ETL de Inventario ===")
        
        raw_inventory = self.data_source.extract_inventory()
        self.stats['inventory_extracted'] = len(raw_inventory)
        self.logger.info(f"Extraídos {len(raw_inventory)} registros de inventario")
        
        if not raw_inventory:
            self.logger.warning("No se extrajeron registros de inventario")
            return
        
        product_mapping = self._get_product_mapping()
        
        transformed_inventory = self.inventory_transformer.transform(
            raw_inventory, 
            product_mapping
        )
        self.stats['inventory_transformed'] = len(transformed_inventory)
        
        grouped = self.inventory_transformer.group_by_location(transformed_inventory)
        
        for location_name, records in grouped.items():
            location_id = self.odoo_loader.get_location_by_name(location_name)
            
            if not location_id:
                self.logger.warning(f"Ubicación no encontrada: {location_name}")
                continue
            
            aggregated = self.inventory_transformer.aggregate_quantities(records)
            
            for sku, quantity in aggregated.items():
                if sku in product_mapping:
                    try:
                        success = self.odoo_loader.adjust_inventory(
                            product_id=product_mapping[sku],
                            location_id=location_id,
                            quantity=quantity,
                        )
                        if success:
                            self.stats['inventory_adjusted'] += 1
                    except Exception as e:
                        self.stats['errors'].append(
                            f"Inventario {sku}@{location_name}: {e}"
                        )
                        self.logger.error(f"Error al ajustar inventario: {e}")
    
    def _get_product_mapping(self) -> Dict[str, int]:
        self.logger.info("Obteniendo mapeo de productos...")
        products = self.odoo_loader.read_record(
            'product.product',
            self.odoo_loader.search_record('product.product', []),
            ['id', 'default_code']
        )
        
        mapping = {}
        for product in products:
            if product.get('default_code'):
                mapping[product['default_code']] = product['id']
        
        self.logger.info(f"Mapeo de productos: {len(mapping)} registros")
        return mapping
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


def run_etl(source_type: str = None) -> Dict[str, Any]:
    manager = ETLManager(source_type)
    return manager.run_pipeline()


if __name__ == '__main__':
    result = run_etl()
    print(f"ETL Result: {result}")
