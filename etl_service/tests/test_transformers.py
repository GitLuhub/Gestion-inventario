import sys
import pytest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from transformers.product_transformer import ProductTransformer
from transformers.inventory_transformer import InventoryTransformer


# ---------------------------------------------------------------------------
# ProductTransformer
# ---------------------------------------------------------------------------
class TestProductTransformer:
    def setup_method(self):
        self.transformer = ProductTransformer()

    def test_transform_list_returns_list(self):
        raw = [{'sku': 'S1', 'name': 'Prod 1'}, {'sku': 'S2', 'name': 'Prod 2'}]
        result = self.transformer.transform(raw)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_transform_empty_list(self):
        assert self.transformer.transform([]) == []

    def test_transform_product_maps_sku_to_default_code(self):
        raw = [{'sku': 'LAP001', 'name': 'Laptop'}]
        result = self.transformer.transform(raw)
        assert result[0]['default_code'] == 'LAP001'

    def test_transform_product_numeric_fields(self):
        raw = [{'sku': 'S1', 'name': 'Prod', 'list_price': '1500', 'standard_price': '1000', 'weight': '1,5'}]
        result = self.transformer.transform(raw)
        assert result[0]['list_price'] == 1500.0
        assert result[0]['standard_price'] == 1000.0
        assert result[0]['weight'] == 1.5

    def test_transform_product_type_product(self):
        raw = [{'sku': 'S1', 'name': 'N', 'product_type': 'product'}]
        result = self.transformer.transform(raw)
        assert result[0]['type'] == 'product'

    def test_transform_product_type_consu_becomes_consumable(self):
        raw = [{'sku': 'S1', 'name': 'N', 'product_type': 'consu'}]
        result = self.transformer.transform(raw)
        assert result[0]['type'] == 'consumable'

    def test_transform_product_type_unknown_defaults_to_product(self):
        raw = [{'sku': 'S1', 'name': 'N', 'product_type': 'unknown_type'}]
        result = self.transformer.transform(raw)
        assert result[0]['type'] == 'product'

    def test_transform_product_active_boolean(self):
        raw = [{'sku': 'S1', 'name': 'N', 'active': True}]
        result = self.transformer.transform(raw)
        assert result[0]['active'] is True

    def test_transform_product_active_string_true(self):
        raw = [{'sku': 'S1', 'name': 'N', 'active': 'true'}]
        result = self.transformer.transform(raw)
        assert result[0]['active'] is True

    def test_transform_product_active_string_false(self):
        raw = [{'sku': 'S1', 'name': 'N', 'active': 'false'}]
        result = self.transformer.transform(raw)
        assert result[0]['active'] is False

    def test_transform_product_with_category_name(self):
        raw = [{'sku': 'S1', 'name': 'N', 'category_name': 'Electronics'}]
        result = self.transformer.transform(raw)
        assert result[0]['categ_name'] == 'Electronics'

    def test_transform_product_cleans_whitespace(self):
        raw = [{'sku': '  SKU1  ', 'name': '  Prod  '}]
        result = self.transformer.transform(raw)
        assert result[0]['sku'] == 'SKU1'
        assert result[0]['name'] == 'Prod'

    def test_transform_skips_exception_products(self):
        raw = [
            {'sku': 'S1', 'name': 'Good'},
            None,  # will raise AttributeError
        ]
        result = self.transformer.transform(raw)
        assert len(result) == 1

    def test_validate_valid_product(self):
        assert self.transformer.validate({'name': 'Prod', 'list_price': 100}) is True

    def test_validate_missing_name(self):
        assert self.transformer.validate({'list_price': 100}) is False

    def test_validate_negative_price(self):
        assert self.transformer.validate({'name': 'Prod', 'list_price': -10}) is False

    def test_clean_string_none(self):
        assert self.transformer._clean_string(None) == ''

    def test_clean_string_strips(self):
        assert self.transformer._clean_string('  hello  ') == 'hello'

    def test_parse_numeric_int(self):
        assert self.transformer._parse_numeric(5) == 5.0

    def test_parse_numeric_invalid_string(self):
        assert self.transformer._parse_numeric('abc') == 0.0

    def test_parse_boolean_string_si(self):
        assert self.transformer._parse_boolean('si') is True

    def test_parse_boolean_string_no(self):
        assert self.transformer._parse_boolean('no') is False

    def test_parse_boolean_other_type(self):
        assert self.transformer._parse_boolean(42) is True


# ---------------------------------------------------------------------------
# InventoryTransformer
# ---------------------------------------------------------------------------
class TestInventoryTransformer:
    def setup_method(self):
        self.transformer = InventoryTransformer()

    def test_transform_list_returns_list(self):
        raw = [{'sku': 'S1', 'location_name': 'WH/Stock', 'quantity': 10}]
        result = self.transformer.transform(raw)
        assert len(result) == 1

    def test_transform_empty_list(self):
        assert self.transformer.transform([]) == []

    def test_transform_skips_empty_sku(self):
        raw = [{'sku': '', 'location_name': 'WH', 'quantity': 5}]
        result = self.transformer.transform(raw)
        assert result == []

    def test_transform_skips_empty_location(self):
        raw = [{'sku': 'S1', 'location_name': '', 'quantity': 5}]
        result = self.transformer.transform(raw)
        assert result == []

    def test_transform_with_product_mapping(self):
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 5}]
        mapping = {'S1': 42}
        result = self.transformer.transform(raw, product_mapping=mapping)
        assert result[0]['product_id'] == 42

    def test_transform_without_product_mapping(self):
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 5}]
        result = self.transformer.transform(raw, product_mapping=None)
        assert 'product_id' not in result[0]

    def test_transform_quantity_numeric(self):
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': '100'}]
        result = self.transformer.transform(raw)
        assert result[0]['quantity'] == 100.0

    def test_transform_includes_lot_name(self):
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 5, 'lot_name': 'LOT001'}]
        result = self.transformer.transform(raw)
        assert result[0]['lot_name'] == 'LOT001'

    def test_transform_includes_expiration_date(self):
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 5, 'expiration_date': '2025-12-31'}]
        result = self.transformer.transform(raw)
        assert result[0]['expiration_date'] == '2025-12-31'

    def test_parse_date_iso_format(self):
        assert self.transformer._parse_date('2025-06-15') == '2025-06-15'

    def test_parse_date_european_format(self):
        assert self.transformer._parse_date('15/06/2025') == '2025-06-15'

    def test_parse_date_us_format(self):
        assert self.transformer._parse_date('06/15/2025') == '2025-06-15'

    def test_parse_date_datetime_object(self):
        dt = datetime(2025, 6, 15)
        assert self.transformer._parse_date(dt) == '2025-06-15'

    def test_parse_date_none_returns_none(self):
        assert self.transformer._parse_date(None) is None

    def test_parse_date_invalid_returns_none(self):
        assert self.transformer._parse_date('not-a-date') is None

    def test_parse_numeric_float(self):
        assert self.transformer._parse_numeric(3.14) == 3.14

    def test_parse_numeric_string_with_comma(self):
        assert self.transformer._parse_numeric('1,5') == 1.5

    def test_parse_numeric_invalid(self):
        assert self.transformer._parse_numeric('bad') == 0.0

    def test_group_by_location(self):
        records = [
            {'sku': 'S1', 'location_name': 'WH/Stock', 'quantity': 10},
            {'sku': 'S2', 'location_name': 'WH/Stock', 'quantity': 5},
            {'sku': 'S3', 'location_name': 'WH/Rack', 'quantity': 3},
        ]
        grouped = self.transformer.group_by_location(records)
        assert len(grouped['WH/Stock']) == 2
        assert len(grouped['WH/Rack']) == 1

    def test_group_by_location_empty(self):
        assert self.transformer.group_by_location([]) == {}

    def test_aggregate_quantities_sums_by_sku(self):
        records = [
            {'sku': 'S1', 'quantity': 10},
            {'sku': 'S1', 'quantity': 5},
            {'sku': 'S2', 'quantity': 3},
        ]
        result = self.transformer.aggregate_quantities(records)
        assert result['S1'] == 15
        assert result['S2'] == 3

    def test_aggregate_quantities_skips_empty_sku(self):
        records = [{'sku': '', 'quantity': 10}]
        result = self.transformer.aggregate_quantities(records)
        assert '' not in result
