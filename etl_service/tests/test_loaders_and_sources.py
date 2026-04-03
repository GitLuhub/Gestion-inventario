import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


# ---------------------------------------------------------------------------
# CSVDataSource
# ---------------------------------------------------------------------------
class TestCSVDataSource:
    def _make_source(self, tmp_path=None, products_path=None, inventory_path=None):
        with patch('data_sources.csv_source.Config') as MockConfig:
            MockConfig.CSV_PRODUCTS_PATH = str(products_path or '')
            MockConfig.CSV_INVENTORY_PATH = str(inventory_path or '')
            from data_sources.csv_source import CSVDataSource
            config = {}
            if products_path:
                config['products_path'] = str(products_path)
            if inventory_path:
                config['inventory_path'] = str(inventory_path)
            return CSVDataSource(config)

    def test_extract_products_returns_list(self, tmp_path):
        csv_file = tmp_path / 'products.csv'
        csv_file.write_text('sku,name,list_price\nSKU001,Laptop,1500\nSKU002,Mouse,50\n')
        source = self._make_source(products_path=csv_file)
        products = source.extract_products()
        assert isinstance(products, list)
        assert len(products) == 2
        assert products[0]['sku'] == 'SKU001'
        assert products[0]['name'] == 'Laptop'

    def test_extract_products_missing_file_returns_empty(self):
        source = self._make_source(products_path=Path('/nonexistent/products.csv'))
        products = source.extract_products()
        assert products == []

    def test_extract_products_skips_invalid_rows(self, tmp_path):
        csv_file = tmp_path / 'products.csv'
        csv_file.write_text('sku,name\n,NoSKU\nSKU001,Valid\n')
        source = self._make_source(products_path=csv_file)
        products = source.extract_products()
        assert len(products) == 1
        assert products[0]['sku'] == 'SKU001'

    def test_extract_inventory_returns_list(self, tmp_path):
        inv_file = tmp_path / 'inventory.csv'
        inv_file.write_text('sku,location_name,quantity\nSKU001,WH/Stock,100\n')
        source = self._make_source(inventory_path=inv_file)
        inventory = source.extract_inventory()
        assert len(inventory) == 1
        assert inventory[0]['sku'] == 'SKU001'
        assert inventory[0]['quantity'] == 100.0

    def test_extract_inventory_missing_file_returns_empty(self):
        source = self._make_source(inventory_path=Path('/nonexistent/inv.csv'))
        inventory = source.extract_inventory()
        assert inventory == []

    def test_test_connection_true_when_file_exists(self, tmp_path):
        csv_file = tmp_path / 'products.csv'
        csv_file.write_text('sku,name\n')
        source = self._make_source(products_path=csv_file)
        assert source.test_connection() is True

    def test_test_connection_false_when_no_files(self):
        source = self._make_source(
            products_path=Path('/no/products.csv'),
            inventory_path=Path('/no/inventory.csv'),
        )
        assert source.test_connection() is False

    def test_parse_float_handles_comma_decimal(self, tmp_path):
        csv_file = tmp_path / 'products.csv'
        csv_file.write_text('sku,name,list_price\nSKU001,Prod,1.500,00\n')
        source = self._make_source(products_path=csv_file)
        assert source._parse_float('1,500') == 1.5

    def test_parse_float_handles_empty(self, tmp_path):
        csv_file = tmp_path / 'products.csv'
        csv_file.write_text('sku,name\n')
        source = self._make_source(products_path=csv_file)
        assert source._parse_float('') == 0.0

    def test_map_product_row_defaults(self, tmp_path):
        source = self._make_source(products_path=tmp_path / 'p.csv')
        row = {'sku': 'S1', 'name': 'N1'}
        result = source._map_product_row(row)
        assert result['sku'] == 'S1'
        assert result['list_price'] == 0.0
        assert result['active'] is True

    def test_map_inventory_row_lot_none_when_empty(self, tmp_path):
        source = self._make_source(inventory_path=tmp_path / 'i.csv')
        row = {'sku': 'S1', 'location_name': 'WH/Stock', 'quantity': '10', 'lot_name': ''}
        result = source._map_inventory_row(row)
        assert result['lot_name'] is None


# ---------------------------------------------------------------------------
# BaseDataSource
# ---------------------------------------------------------------------------
class TestBaseDataSource:
    def _make_concrete(self):
        from data_sources.base_source import BaseDataSource

        class ConcreteSource(BaseDataSource):
            def extract_products(self, last_sync=None):
                return []

            def extract_inventory(self, last_sync=None):
                return []

            def test_connection(self):
                return True

        return ConcreteSource({})

    def test_validate_product_data_valid(self):
        source = self._make_concrete()
        assert source.validate_product_data({'sku': 'X1', 'name': 'Prod'}) is True

    def test_validate_product_data_missing_sku(self):
        source = self._make_concrete()
        assert source.validate_product_data({'name': 'Prod'}) is False

    def test_validate_product_data_empty_name(self):
        source = self._make_concrete()
        assert source.validate_product_data({'sku': 'X1', 'name': ''}) is False

    def test_validate_inventory_data_valid(self):
        source = self._make_concrete()
        data = {'sku': 'X1', 'location_name': 'WH', 'quantity': 5.0}
        assert source.validate_inventory_data(data) is True

    def test_validate_inventory_data_missing_field(self):
        source = self._make_concrete()
        assert source.validate_inventory_data({'sku': 'X1', 'location_name': 'WH'}) is False

    def test_validate_inventory_data_invalid_quantity(self):
        source = self._make_concrete()
        data = {'sku': 'X1', 'location_name': 'WH', 'quantity': 'not_a_number'}
        assert source.validate_inventory_data(data) is False


# ---------------------------------------------------------------------------
# APIDataSource
# ---------------------------------------------------------------------------
class TestAPIDataSource:
    def _make_source(self):
        with patch('data_sources.api_source.Config') as MockConfig:
            MockConfig.EXTERNAL_API_URL = 'http://fake-api:8080/api/v1'
            MockConfig.EXTERNAL_API_KEY = 'test_key'
            from data_sources.api_source import APIDataSource
            return APIDataSource({})

    def test_extract_products_success(self):
        source = self._make_source()
        mock_response = {
            'products': [
                {'sku': 'P1', 'name': 'Prod 1', 'list_price': 100},
                {'sku': 'P2', 'name': 'Prod 2', 'list_price': 200},
            ]
        }
        with patch.object(source, '_make_request', return_value=mock_response):
            products = source.extract_products()
        assert len(products) == 2
        assert products[0]['sku'] == 'P1'

    def test_extract_products_uses_items_key(self):
        source = self._make_source()
        mock_response = {
            'items': [{'sku': 'P1', 'name': 'Item 1'}]
        }
        with patch.object(source, '_make_request', return_value=mock_response):
            products = source.extract_products()
        assert len(products) == 1

    def test_extract_products_request_error_returns_empty(self):
        source = self._make_source()
        with patch.object(source, '_make_request', side_effect=Exception("timeout")):
            products = source.extract_products()
        assert products == []

    def test_extract_inventory_success(self):
        source = self._make_source()
        mock_response = {
            'inventory': [
                {'sku': 'P1', 'location': 'WH/Stock', 'quantity': 50},
            ]
        }
        with patch.object(source, '_make_request', return_value=mock_response):
            inventory = source.extract_inventory()
        assert len(inventory) == 1
        assert inventory[0]['sku'] == 'P1'
        assert inventory[0]['quantity'] == 50

    def test_extract_inventory_error_returns_empty(self):
        source = self._make_source()
        with patch.object(source, '_make_request', side_effect=Exception("timeout")):
            inventory = source.extract_inventory()
        assert inventory == []

    def test_map_product_uses_default_code_as_sku(self):
        source = self._make_source()
        item = {'default_code': 'D001', 'name': 'Prod'}
        result = source._map_product(item)
        assert result['sku'] == 'D001'

    def test_map_inventory_location_name_fallback(self):
        source = self._make_source()
        item = {'sku': 'P1', 'location_name': 'WH/Rack', 'quantity': 10}
        result = source._map_inventory(item)
        assert result['location_name'] == 'WH/Rack'

    def test_test_connection_true(self):
        source = self._make_source()
        mock_resp = Mock()
        mock_resp.status_code = 200
        with patch('data_sources.api_source.requests.get', return_value=mock_resp):
            assert source.test_connection() is True

    def test_test_connection_false_on_exception(self):
        source = self._make_source()
        with patch('data_sources.api_source.requests.get', side_effect=Exception("conn")):
            assert source.test_connection() is False

    def test_test_connection_false_on_non_200(self):
        source = self._make_source()
        mock_resp = Mock()
        mock_resp.status_code = 503
        with patch('data_sources.api_source.requests.get', return_value=mock_resp):
            assert source.test_connection() is False


# ---------------------------------------------------------------------------
# DBDataSource
# ---------------------------------------------------------------------------
class TestDBDataSource:
    def _make_source(self):
        with patch('data_sources.db_source.Config') as MockConfig:
            MockConfig.DB_CONNECTION_STRING = 'postgresql://odoo:odoo@localhost:5432/odoo'
            from data_sources.db_source import DBDataSource
            return DBDataSource({})

    def _make_mock_conn(self, rows=None):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = rows or []
        mock_conn = MagicMock()
        mock_conn.closed = False
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    def test_extract_products_success(self):
        source = self._make_source()
        mock_conn, mock_cursor = self._make_mock_conn([
            {'sku': 'P1', 'name': 'Prod 1', 'category_name': 'Cat',
             'list_price': 100, 'standard_price': 80, 'weight': 1.0,
             'product_type': 'product', 'barcode': '', 'description': '', 'active': True},
        ])
        with patch('data_sources.db_source.psycopg2.connect', return_value=mock_conn):
            products = source.extract_products()
        assert len(products) == 1
        assert products[0]['sku'] == 'P1'

    def test_extract_products_db_error_returns_empty(self):
        source = self._make_source()
        with patch('data_sources.db_source.psycopg2.connect', side_effect=Exception("db down")):
            products = source.extract_products()
        assert products == []

    def test_extract_products_with_last_sync(self):
        source = self._make_source()
        mock_conn, mock_cursor = self._make_mock_conn([])
        with patch('data_sources.db_source.psycopg2.connect', return_value=mock_conn):
            source.extract_products(last_sync='2024-01-01')
        executed_query = mock_cursor.execute.call_args[0][0]
        assert '2024-01-01' in executed_query

    def test_extract_inventory_success(self):
        source = self._make_source()
        mock_conn, mock_cursor = self._make_mock_conn([
            {'sku': 'P1', 'location_name': 'WH/Stock', 'quantity': 50.0,
             'lot_name': None, 'expiration_date': None},
        ])
        with patch('data_sources.db_source.psycopg2.connect', return_value=mock_conn):
            inventory = source.extract_inventory()
        assert len(inventory) == 1
        assert inventory[0]['quantity'] == 50.0

    def test_extract_inventory_error_returns_empty(self):
        source = self._make_source()
        with patch('data_sources.db_source.psycopg2.connect', side_effect=Exception("err")):
            inventory = source.extract_inventory()
        assert inventory == []

    def test_test_connection_true(self):
        source = self._make_source()
        mock_conn, mock_cursor = self._make_mock_conn()
        with patch('data_sources.db_source.psycopg2.connect', return_value=mock_conn):
            assert source.test_connection() is True

    def test_test_connection_false_on_error(self):
        source = self._make_source()
        with patch('data_sources.db_source.psycopg2.connect', side_effect=Exception("err")):
            assert source.test_connection() is False

    def test_get_connection_reuses_open_connection(self):
        source = self._make_source()
        mock_conn = MagicMock()
        mock_conn.closed = False
        source._connection = mock_conn
        with patch('data_sources.db_source.psycopg2.connect') as mock_connect:
            result = source._get_connection()
        mock_connect.assert_not_called()
        assert result is mock_conn

    def test_close_connection_sets_none(self):
        source = self._make_source()
        mock_conn = MagicMock()
        mock_conn.closed = False
        source._connection = mock_conn
        source._close_connection()
        assert source._connection is None


# ---------------------------------------------------------------------------
# OdooLoader
# ---------------------------------------------------------------------------
class TestOdooLoader:
    def _make_loader(self):
        with patch('loaders.odoo_loader.Config') as MockConfig, \
             patch('loaders.odoo_loader.xmlrpc.client.ServerProxy') as MockProxy:
            MockConfig.ODOO_URL = 'http://odoo:8069'
            MockConfig.ODOO_DB = 'odoo_db'
            MockConfig.ODOO_USER = 'admin'
            MockConfig.ODOO_PASSWORD = 'admin'
            mock_common = MagicMock()
            mock_common.authenticate.return_value = 1
            mock_models = MagicMock()
            mock_models.execute_kw.return_value = True
            MockProxy.side_effect = [mock_common, mock_models]
            from loaders.odoo_loader import OdooLoader
            loader = OdooLoader(
                url='http://odoo:8069',
                db='odoo_db',
                user='admin',
                password='admin',
            )
            loader.common = mock_common
            loader.models = mock_models
            loader.uid = 1
            return loader, mock_common, mock_models

    def test_connect_sets_uid(self):
        loader, mock_common, _ = self._make_loader()
        assert loader.uid == 1

    def test_connect_raises_on_auth_failure(self):
        with patch('loaders.odoo_loader.Config'), \
             patch('loaders.odoo_loader.xmlrpc.client.ServerProxy') as MockProxy:
            mock_common = MagicMock()
            mock_common.authenticate.return_value = False
            mock_models = MagicMock()
            MockProxy.side_effect = [mock_common, mock_models]
            from loaders.odoo_loader import OdooLoader
            with pytest.raises(Exception):
                OdooLoader(url='http://odoo:8069', db='db', user='u', password='p')

    def test_search_record(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = [1, 2, 3]
        result = loader.search_record('product.product', [('active', '=', True)])
        assert result == [1, 2, 3]

    def test_read_record_empty_ids(self):
        loader, _, _ = self._make_loader()
        result = loader.read_record('product.product', [], ['name'])
        assert result == []

    def test_read_record_with_ids(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = [{'id': 1, 'name': 'Test'}]
        result = loader.read_record('product.product', [1], ['name'])
        assert result[0]['name'] == 'Test'

    def test_create_record(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = 42
        result = loader.create_record('product.product', {'name': 'New'})
        assert result == 42

    def test_write_record(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = True
        result = loader.write_record('product.product', [1], {'name': 'Updated'})
        assert result is True

    def test_get_product_by_sku_returns_none_for_empty_sku(self):
        loader, _, _ = self._make_loader()
        assert loader.get_product_by_sku('') is None
        assert loader.get_product_by_sku(None) is None

    def test_get_product_by_sku_found(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [
            [1],  # search
            [{'id': 1, 'name': 'Laptop', 'default_code': 'LAP001',
              'type': 'product', 'list_price': 1000, 'standard_price': 800,
              'active': True, 'categ_id': [1, 'All']}],  # read
        ]
        result = loader.get_product_by_sku('LAP001')
        assert result['id'] == 1
        assert result['name'] == 'Laptop'

    def test_get_product_by_sku_not_found(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = []
        result = loader.get_product_by_sku('NOTEXIST')
        assert result is None

    def test_get_category_by_name_found(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = [5]
        result = loader.get_category_by_name('Electronics')
        assert result == 5

    def test_get_category_by_name_empty(self):
        loader, _, _ = self._make_loader()
        assert loader.get_category_by_name('') is None
        assert loader.get_category_by_name(None) is None

    def test_create_category_creates_when_not_found(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [[], 10]
        result = loader.create_category('New Category')
        assert result == 10

    def test_create_category_returns_existing(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.return_value = [3]
        result = loader.create_category('Electronics')
        assert result == 3

    def test_create_or_update_product_creates_new(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [
            [],   # search for existing product
            99,   # create
        ]
        product_data = {'name': 'New Prod', 'default_code': 'NEW001', 'type': 'product'}
        result = loader.create_or_update_product(product_data)
        assert result == 99

    def test_create_or_update_product_updates_existing(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [
            [7],  # search for existing
            [{'id': 7, 'name': 'Old', 'default_code': 'SKU001',
              'type': 'product', 'list_price': 100, 'standard_price': 80,
              'active': True, 'categ_id': False}],  # read
            True,  # write
        ]
        product_data = {'name': 'Updated', 'default_code': 'SKU001'}
        result = loader.create_or_update_product(product_data)
        assert result == 7

    def test_test_connection_true(self):
        loader, mock_common, _ = self._make_loader()
        mock_common.version.return_value = {'server_version': '16.0'}
        assert loader.test_connection() is True

    def test_test_connection_false_on_error(self):
        loader, mock_common, _ = self._make_loader()
        mock_common.version.side_effect = Exception("conn failed")
        assert loader.test_connection() is False

    def test_adjust_inventory_returns_true_on_success(self):
        loader, _, mock_models = self._make_loader()
        # New Odoo 16 flow: search stock.quant (empty) → create quant → action_apply_inventory via JSON-RPC
        mock_models.execute_kw.side_effect = [
            [],   # search stock.quant → no existing quant
            201,  # create stock.quant
        ]
        mock_auth_resp = MagicMock()
        mock_auth_resp.cookies.get.return_value = 'test_session_id'
        mock_json_resp = MagicMock()
        mock_json_resp.json.return_value = {'result': None}
        with patch('loaders.odoo_loader.requests.post',
                   side_effect=[mock_auth_resp, mock_json_resp]):
            result = loader.adjust_inventory(
                product_id=1, location_id=5, quantity=10.0
            )
        assert result is True

    def test_adjust_inventory_returns_false_on_error(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = Exception("Odoo error")
        result = loader.adjust_inventory(product_id=1, location_id=5, quantity=10.0)
        assert result is False

    def test_get_location_by_name_none_for_empty(self):
        loader, _, _ = self._make_loader()
        assert loader.get_location_by_name('') is None
        assert loader.get_location_by_name(None) is None

    def test_get_location_by_name_found(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [[8]]
        result = loader.get_location_by_name('WH/Stock')
        assert result == 8

    def test_get_location_by_name_fallback_search(self):
        loader, _, mock_models = self._make_loader()
        mock_models.execute_kw.side_effect = [[], [12]]
        result = loader.get_location_by_name('Stock')
        assert result == 12

    def test_execute_catches_fault(self):
        import xmlrpc.client
        loader, _, mock_models = self._make_loader()
        fault = xmlrpc.client.Fault(1, 'Access Denied')
        mock_models.execute_kw.side_effect = fault
        with pytest.raises(xmlrpc.client.Fault):
            loader._execute('product.product', 'search', [])
