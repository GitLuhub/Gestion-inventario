import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_source import BaseDataSource
from config import Config
from tenacity import retry, stop_after_attempt, wait_exponential


class APIDataSource(BaseDataSource):
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.base_url = config.get('base_url', Config.EXTERNAL_API_URL)
        self.api_key = config.get('api_key', Config.EXTERNAL_API_KEY)
        self.timeout = config.get('timeout', 30)
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en request a {url}: {e}")
            raise
    
    def extract_products(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info(f"Extrayendo productos desde API: {self.base_url}")
        
        products = []
        try:
            params = {'last_sync': last_sync} if last_sync else {}
            data = self._make_request('products', params)
            
            items = data.get('products', data.get('items', []))
            for item in items:
                product = self._map_product(item)
                if self.validate_product_data(product):
                    products.append(product)
            
            self.logger.info(f"Extraídos {len(products)} productos desde API")
            
        except Exception as e:
            self.logger.error(f"Error al extraer productos desde API: {e}")
        
        return products
    
    def extract_inventory(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        self.logger.info(f"Extrayendo inventario desde API: {self.base_url}")
        
        inventory = []
        try:
            params = {'last_sync': last_sync} if last_sync else {}
            data = self._make_request('inventory', params)
            
            items = data.get('inventory', data.get('items', []))
            for item in items:
                inv_record = self._map_inventory(item)
                if self.validate_inventory_data(inv_record):
                    inventory.append(inv_record)
            
            self.logger.info(f"Extraídos {len(inventory)} registros de inventario desde API")
            
        except Exception as e:
            self.logger.error(f"Error al extraer inventario desde API: {e}")
        
        return inventory
    
    def _map_product(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'sku': item.get('sku', item.get('default_code', '')),
            'name': item.get('name', ''),
            'description': item.get('description', ''),
            'category_name': item.get('category', ''),
            'list_price': item.get('list_price', 0),
            'standard_price': item.get('standard_price', 0),
            'weight': item.get('weight', 0),
            'product_type': item.get('type', 'product'),
            'barcode': item.get('barcode', ''),
            'active': item.get('active', True),
        }
    
    def _map_inventory(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'sku': item.get('sku', ''),
            'location_name': item.get('location', item.get('location_name', '')),
            'quantity': item.get('quantity', 0),
            'lot_name': item.get('lot_name', None),
            'expiration_date': item.get('expiration_date', None),
        }
    
    def test_connection(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error en test_connection: {e}")
            return False
