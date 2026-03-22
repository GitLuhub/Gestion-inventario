import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.transformers.product_transformer import ProductTransformer
from src.transformers.inventory_transformer import InventoryTransformer


class TestProductTransformer:
    def test_transform_valid_product(self):
        transformer = ProductTransformer()
        
        raw_product = {
            'name': 'Laptop HP ProBook',
            'default_code': 'HP-450-G9',
            'list_price': 1500000.00,
            'standard_price': 1200000.00,
            'type': 'product',
            'weight': 1.75,
            'categ_id': 1,
        }
        
        result = transformer.transform(raw_product)
        
        assert result['name'] == 'Laptop HP ProBook'
        assert result['default_code'] == 'HP-450-G9'
        assert result['list_price'] == 1500000.00
        assert result['standard_price'] == 1200000.00
        assert result['type'] == 'product'
        assert result['weight'] == 1.75
        assert result['categ_id'] == 1

    def test_transform_with_missing_fields(self):
        transformer = ProductTransformer()
        
        raw_product = {
            'name': 'Simple Product',
        }
        
        result = transformer.transform(raw_product)
        
        assert result['name'] == 'Simple Product'
        assert result['default_code'] is None
        assert result['list_price'] == 0.0
        assert result['standard_price'] == 0.0

    def test_transform_batch(self):
        transformer = ProductTransformer()
        
        raw_products = [
            {'name': 'Product 1', 'list_price': 100},
            {'name': 'Product 2', 'list_price': 200},
            {'name': 'Product 3', 'list_price': 300},
        ]
        
        results = transformer.transform_batch(raw_products)
        
        assert len(results) == 3
        assert all('name' in r for r in results)


class TestInventoryTransformer:
    def test_transform_valid_quant(self):
        transformer = InventoryTransformer()
        
        raw_quant = {
            'product_id': 1,
            'location_id': 1,
            'quantity': 100.0,
            'reserved_quantity': 10.0,
            'lot_id': None,
        }
        
        result = transformer.transform_quant(raw_quant)
        
        assert result['product_id'] == 1
        assert result['location_id'] == 1
        assert result['quantity'] == 100.0
        assert result['reserved_quantity'] == 10.0

    def test_transform_quant_with_negative_quantity(self):
        transformer = InventoryTransformer()
        
        raw_quant = {
            'product_id': 1,
            'location_id': 1,
            'quantity': -5.0,
        }
        
        result = transformer.transform_quant(raw_quant)
        
        assert result['quantity'] == 0.0

    def test_calculate_available_quantity(self):
        transformer = InventoryTransformer()
        
        result = transformer.calculate_available(100.0, 10.0)
        
        assert result == 90.0

    def test_calculate_available_with_reserved_exceeds(self):
        transformer = InventoryTransformer()
        
        result = transformer.calculate_available(10.0, 100.0)
        
        assert result == 0.0
