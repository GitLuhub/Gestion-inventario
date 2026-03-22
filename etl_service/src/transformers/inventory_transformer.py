from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger_util import get_logger


class InventoryTransformer:
    def __init__(self):
        self.logger = get_logger('InventoryTransformer')
    
    def transform(
        self, 
        raw_inventory: List[Dict[str, Any]],
        product_mapping: Dict[str, int] = None
    ) -> List[Dict[str, Any]]:
        self.logger.info(f"Transformando {len(raw_inventory)} registros de inventario")
        
        transformed = []
        errors = []
        
        for idx, record in enumerate(raw_inventory):
            try:
                transformed_record = self._transform_inventory(record, product_mapping)
                if transformed_record:
                    transformed.append(transformed_record)
            except Exception as e:
                errors.append({'index': idx, 'record': record, 'error': str(e)})
                self.logger.warning(f"Error en inventario {idx}: {e}")
        
        self.logger.info(
            f"Transformados {len(transformed)} registros, {len(errors)} errores"
        )
        
        if errors:
            self.logger.warning(f"Registros con errores: {errors[:5]}")
        
        return transformed
    
    def _transform_inventory(
        self, 
        record: Dict[str, Any],
        product_mapping: Optional[Dict[str, int]]
    ) -> Optional[Dict[str, Any]]:
        transformed = {}
        
        transformed['sku'] = record.get('sku', '').strip()
        if not transformed['sku']:
            return None
        
        if product_mapping and transformed['sku'] in product_mapping:
            transformed['product_id'] = product_mapping[transformed['sku']]
        
        transformed['location_name'] = record.get('location_name', '').strip()
        if not transformed['location_name']:
            return None
        
        transformed['quantity'] = self._parse_numeric(record.get('quantity', 0))
        
        if record.get('lot_name'):
            transformed['lot_name'] = str(record['lot_name']).strip()
        
        if record.get('expiration_date'):
            transformed['expiration_date'] = self._parse_date(record['expiration_date'])
        
        return transformed
    
    def _parse_numeric(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except (ValueError, AttributeError):
                return 0.0
        return 0.0
    
    def _parse_date(self, value: Any) -> Optional[str]:
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(value, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def group_by_location(
        self, 
        inventory_records: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {}
        for record in inventory_records:
            location = record.get('location_name', 'Unknown')
            if location not in grouped:
                grouped[location] = []
            grouped[location].append(record)
        return grouped
    
    def aggregate_quantities(
        self, 
        inventory_records: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        aggregated = {}
        for record in inventory_records:
            sku = record.get('sku', '')
            if sku:
                aggregated[sku] = aggregated.get(sku, 0) + record.get('quantity', 0)
        return aggregated
