from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from utils.logger_util import get_logger


class BaseDataSource(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger('DataSource')
    
    @abstractmethod
    def extract_products(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def extract_inventory(self, last_sync: Optional[str] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        pass
    
    def validate_product_data(self, product: Dict[str, Any]) -> bool:
        required_fields = ['sku', 'name']
        for field in required_fields:
            if field not in product or not product[field]:
                self.logger.warning(f"Producto sin campo requerido: {field}")
                return False
        return True
    
    def validate_inventory_data(self, inventory: Dict[str, Any]) -> bool:
        required_fields = ['sku', 'location_name', 'quantity']
        for field in required_fields:
            if field not in inventory:
                self.logger.warning(f"Inventario sin campo requerido: {field}")
                return False
        if not isinstance(inventory.get('quantity'), (int, float)):
            return False
        return True
