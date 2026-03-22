import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from .base_source import BaseDataSource
from config import Config


class DBDataSource(BaseDataSource):
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.connection_string = config.get(
            'connection_string', Config.DB_CONNECTION_STRING
        )
        self._connection = None
    
    def _get_connection(self):
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(self.connection_string)
        return self._connection
    
    def extract_products(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info("Extrayendo productos desde base de datos SQL")
        
        products = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    sku as sku,
                    name as name,
                    description as description,
                    category as category_name,
                    list_price as list_price,
                    standard_price as standard_price,
                    weight as weight,
                    type as product_type,
                    barcode as barcode,
                    active as active
                FROM products
                WHERE active = TRUE
            """
            if last_sync:
                query += f" AND updated_at > '{last_sync}'"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                product = dict(row)
                if self.validate_product_data(product):
                    products.append(product)
            
            cursor.close()
            self.logger.info(f"Extraídos {len(products)} productos desde DB")
            
        except Exception as e:
            self.logger.error(f"Error al extraer productos desde DB: {e}")
        finally:
            self._close_connection()
        
        return products
    
    def extract_inventory(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info("Extrayendo inventario desde base de datos SQL")
        
        inventory = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    sku as sku,
                    location_name as location_name,
                    quantity as quantity,
                    lot_name as lot_name,
                    expiration_date as expiration_date
                FROM inventory
            """
            if last_sync:
                query += f" WHERE updated_at > '{last_sync}'"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                inv_record = dict(row)
                if self.validate_inventory_data(inv_record):
                    inventory.append(inv_record)
            
            cursor.close()
            self.logger.info(f"Extraídos {len(inventory)} registros de inventario desde DB")
            
        except Exception as e:
            self.logger.error(f"Error al extraer inventario desde DB: {e}")
        finally:
            self._close_connection()
        
        return inventory
    
    def _close_connection(self):
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
    
    def test_connection(self) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            self.logger.error(f"Error en test_connection: {e}")
            return False
