from typing import List, Dict, Any
from utils.logger_util import get_logger


class ProductTransformer:
    def __init__(self):
        self.logger = get_logger('ProductTransformer')
        self.required_fields = ['name']
        self.numeric_fields = ['list_price', 'standard_price', 'weight']
        self.boolean_fields = ['active']
    
    def transform(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.logger.info(f"Transformando {len(raw_products)} productos")
        
        transformed = []
        errors = []
        
        for idx, product in enumerate(raw_products):
            try:
                transformed_product = self._transform_product(product)
                if transformed_product:
                    transformed.append(transformed_product)
            except Exception as e:
                errors.append({'index': idx, 'product': product, 'error': str(e)})
                self.logger.warning(f"Error en producto {idx}: {e}")
        
        self.logger.info(
            f"Transformados {len(transformed)} productos, {len(errors)} errores"
        )
        
        if errors:
            self.logger.warning(f"Productos con errores: {errors[:5]}")
        
        return transformed
    
    def _transform_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        transformed = {}
        
        for field in ['sku', 'name', 'description', 'barcode']:
            transformed[field] = self._clean_string(product.get(field, ''))
        
        transformed['default_code'] = transformed.get('sku', '')
        
        for field in self.numeric_fields:
            transformed[field] = self._parse_numeric(product.get(field, 0))
        
        transformed['active'] = self._parse_boolean(product.get('active', True))
        
        product_type = product.get('product_type', 'product').lower()
        if product_type in ['product', 'consu', 'service']:
            transformed['type'] = product_type if product_type != 'consu' else 'consumable'
        else:
            transformed['type'] = 'product'
        
        if product.get('category_name'):
            transformed['categ_name'] = product['category_name']
        
        return transformed
    
    def _clean_string(self, value: Any) -> str:
        if value is None:
            return ''
        return str(value).strip()
    
    def _parse_numeric(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except (ValueError, AttributeError):
                return 0.0
        return 0.0
    
    def _parse_boolean(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'si', 's']
        return True
    
    def validate(self, product: Dict[str, Any]) -> bool:
        for field in self.required_fields:
            if not product.get(field):
                self.logger.warning(f"Producto sin campo requerido: {field}")
                return False
        
        if product.get('list_price', 0) < 0:
            self.logger.warning("Precio de venta no puede ser negativo")
            return False
        
        return True
