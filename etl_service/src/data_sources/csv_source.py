import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_source import BaseDataSource
from config import Config


class CSVDataSource(BaseDataSource):
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.products_file = config.get('products_path', Config.CSV_PRODUCTS_PATH)
        self.inventory_file = config.get('inventory_path', Config.CSV_INVENTORY_PATH)
    
    def extract_products(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info(f"Extrayendo productos desde CSV: {self.products_file}")
        
        products = []
        try:
            file_path = Path(self.products_file)
            if not file_path.exists():
                self.logger.warning(f"Archivo de productos no encontrado: {self.products_file}")
                return products
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product = self._map_product_row(row)
                    if self.validate_product_data(product):
                        products.append(product)
            
            self.logger.info(f"Extraídos {len(products)} productos")
            
        except Exception as e:
            self.logger.error(f"Error al extraer productos: {e}")
        
        return products
    
    def extract_inventory(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info(f"Extrayendo inventario desde CSV: {self.inventory_file}")
        
        inventory = []
        try:
            file_path = Path(self.inventory_file)
            if not file_path.exists():
                self.logger.warning(f"Archivo de inventario no encontrado: {self.inventory_file}")
                return inventory
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    inv_record = self._map_inventory_row(row)
                    if self.validate_inventory_data(inv_record):
                        inventory.append(inv_record)
            
            self.logger.info(f"Extraídos {len(inventory)} registros de inventario")
            
        except Exception as e:
            self.logger.error(f"Error al extraer inventario: {e}")
        
        return inventory
    
    def _map_product_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        return {
            'sku': row.get('sku', '').strip(),
            'name': row.get('name', '').strip(),
            'description': row.get('description', '').strip(),
            'category_name': row.get('categ_id', row.get('category', '')).strip(),
            'list_price': self._parse_float(row.get('list_price', 0)),
            'standard_price': self._parse_float(row.get('standard_price', 0)),
            'weight': self._parse_float(row.get('weight', 0)),
            'product_type': row.get('type', 'product'),
            'barcode': row.get('barcode', '').strip(),
            'active': row.get('active', 'True').lower() == 'true',
        }
    
    def _map_inventory_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        return {
            'sku': row.get('sku', '').strip(),
            'location_name': row.get('location_name', '').strip(),
            'quantity': self._parse_float(row.get('quantity', 0)),
            'lot_name': row.get('lot_name', '').strip() or None,
            'expiration_date': row.get('expiration_date', '').strip() or None,
        }
    
    def _parse_float(self, value: str) -> float:
        try:
            return float(value.replace(',', '.')) if value else 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def test_connection(self) -> bool:
        try:
            products_path = Path(self.products_file)
            inventory_path = Path(self.inventory_file)
            
            return products_path.exists() or inventory_path.exists()
        except Exception as e:
            self.logger.error(f"Error en test_connection: {e}")
            return False
