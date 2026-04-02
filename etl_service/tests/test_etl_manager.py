import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


# ---------------------------------------------------------------------------
# logger_util
# ---------------------------------------------------------------------------
class TestLoggerUtil:
    def test_get_logger_returns_logger(self):
        from utils.logger_util import get_logger
        logger = get_logger('test_logger')
        assert isinstance(logger, logging.Logger)

    def test_get_logger_singleton(self):
        from utils.logger_util import get_logger
        logger1 = get_logger('singleton_test')
        logger2 = get_logger('singleton_test')
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        from utils.logger_util import get_logger
        logger_a = get_logger('logger_a')
        logger_b = get_logger('logger_b')
        assert logger_a.name != logger_b.name

    def test_json_formatter_produces_valid_json(self):
        import json
        from utils.logger_util import _JsonFormatter
        formatter = _JsonFormatter()
        record = logging.LogRecord(
            name='test', level=logging.INFO,
            pathname='', lineno=0, msg='hello world',
            args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed['message'] == 'hello world'
        assert parsed['level'] == 'INFO'
        assert parsed['service'] == 'etl'
        assert 'timestamp' in parsed

    def test_json_formatter_with_exception(self):
        import json
        from utils.logger_util import _JsonFormatter
        formatter = _JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name='test', level=logging.ERROR,
            pathname='', lineno=0, msg='error',
            args=(), exc_info=exc_info,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert 'exception' in parsed


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
class TestConfig:
    def test_validate_returns_true_when_valid(self):
        from config import Config
        original_source = Config.SOURCE_TYPE
        original_password = Config.ODOO_PASSWORD
        try:
            Config.SOURCE_TYPE = 'csv'
            Config.ODOO_PASSWORD = 'secret'
            result = Config.validate()
            assert result is True
        finally:
            Config.SOURCE_TYPE = original_source
            Config.ODOO_PASSWORD = original_password

    def test_validate_raises_on_invalid_source(self):
        from config import Config
        original = Config.SOURCE_TYPE
        try:
            Config.SOURCE_TYPE = 'invalid_source'
            with pytest.raises(ValueError, match="Fuente no soportada"):
                Config.validate()
        finally:
            Config.SOURCE_TYPE = original

    def test_validate_raises_when_no_password(self):
        from config import Config
        original_password = Config.ODOO_PASSWORD
        original_source = Config.SOURCE_TYPE
        try:
            Config.SOURCE_TYPE = 'csv'
            Config.ODOO_PASSWORD = ''
            with pytest.raises(ValueError, match="ODOO_PASSWORD"):
                Config.validate()
        finally:
            Config.ODOO_PASSWORD = original_password
            Config.SOURCE_TYPE = original_source

    def test_config_has_required_attributes(self):
        from config import Config
        assert hasattr(Config, 'ODOO_URL')
        assert hasattr(Config, 'ODOO_DB')
        assert hasattr(Config, 'SOURCE_TYPE')
        assert hasattr(Config, 'BATCH_SIZE')
        assert hasattr(Config, 'SUPPORTED_SOURCES')

    def test_supported_sources(self):
        from config import Config
        assert 'csv' in Config.SUPPORTED_SOURCES
        assert 'api' in Config.SUPPORTED_SOURCES
        assert 'db' in Config.SUPPORTED_SOURCES


# ---------------------------------------------------------------------------
# etl_manager
# ---------------------------------------------------------------------------
class TestETLManager:
    def _make_manager(self, source_type='csv'):
        """Crea un ETLManager con todas las dependencias mockeadas."""
        with patch('etl_manager.CSVDataSource') as MockCSV, \
             patch('etl_manager.APIDataSource') as MockAPI, \
             patch('etl_manager.DBDataSource') as MockDB, \
             patch('etl_manager.OdooLoader') as MockLoader, \
             patch('etl_manager.Config') as MockConfig:
            MockConfig.SOURCE_TYPE = source_type
            mock_source = MagicMock()
            mock_source.test_connection.return_value = True
            mock_source.extract_products.return_value = []
            mock_source.extract_inventory.return_value = []
            MockCSV.return_value = mock_source
            MockAPI.return_value = mock_source
            MockDB.return_value = mock_source
            mock_loader = MagicMock()
            mock_loader.test_connection.return_value = True
            MockLoader.return_value = mock_loader
            from etl_manager import ETLManager
            manager = ETLManager.__new__(ETLManager)
            manager.source_type = source_type
            manager.logger = MagicMock()
            manager.start_time = None
            manager.stats = {
                'products_extracted': 0, 'products_transformed': 0,
                'products_loaded': 0, 'inventory_extracted': 0,
                'inventory_transformed': 0, 'inventory_adjusted': 0,
                'errors': [], 'start_time': None, 'end_time': None,
            }
            manager.data_source = mock_source
            manager.product_transformer = MagicMock()
            manager.inventory_transformer = MagicMock()
            manager.odoo_loader = mock_loader
            return manager

    def test_create_data_source_csv(self):
        with patch('etl_manager.CSVDataSource') as MockCSV, \
             patch('etl_manager.OdooLoader'), \
             patch('etl_manager.Config') as MockConfig:
            MockConfig.SOURCE_TYPE = 'csv'
            MockCSV.return_value = MagicMock()
            from etl_manager import ETLManager
            manager = ETLManager.__new__(ETLManager)
            manager.logger = MagicMock()
            manager.source_type = 'csv'
            source = manager._create_data_source()
            assert source is not None

    def test_create_data_source_invalid_raises(self):
        with patch('etl_manager.OdooLoader'), \
             patch('etl_manager.Config') as MockConfig:
            MockConfig.SOURCE_TYPE = 'invalid'
            from etl_manager import ETLManager
            manager = ETLManager.__new__(ETLManager)
            manager.logger = MagicMock()
            manager.source_type = 'invalid'
            with pytest.raises(ValueError, match="Fuente no soportada"):
                manager._create_data_source()

    def test_run_pipeline_success_no_data(self):
        manager = self._make_manager()
        manager.data_source.extract_products.return_value = []
        manager.data_source.extract_inventory.return_value = []
        result = manager.run_pipeline()
        assert result['success'] is True
        assert 'stats' in result
        assert 'duration_seconds' in result

    def test_run_pipeline_odoo_connection_failure(self):
        manager = self._make_manager()
        manager.odoo_loader.test_connection.return_value = False
        result = manager.run_pipeline()
        assert result['success'] is False
        assert 'error' in result

    def test_run_pipeline_source_connection_failure(self):
        manager = self._make_manager()
        manager.odoo_loader.test_connection.return_value = True
        manager.data_source.test_connection.return_value = False
        result = manager.run_pipeline()
        assert result['success'] is False

    def test_get_stats_returns_copy(self):
        manager = self._make_manager()
        stats = manager.get_stats()
        assert isinstance(stats, dict)
        assert 'products_extracted' in stats
        assert 'errors' in stats

    def test_run_products_etl_no_products(self):
        manager = self._make_manager()
        manager.data_source.extract_products.return_value = []
        manager._run_products_etl()
        assert manager.stats['products_extracted'] == 0

    def test_run_products_etl_with_products(self):
        manager = self._make_manager()
        raw = [{'name': 'Prod A', 'default_code': 'A001'}]
        manager.data_source.extract_products.return_value = raw
        manager.product_transformer.transform.return_value = raw
        manager.product_transformer.validate.return_value = True
        manager.odoo_loader.create_or_update_product.return_value = 1
        manager._run_products_etl()
        assert manager.stats['products_extracted'] == 1
        assert manager.stats['products_loaded'] == 1

    def test_run_inventory_etl_no_inventory(self):
        manager = self._make_manager()
        manager.data_source.extract_inventory.return_value = []
        manager._run_inventory_etl()
        assert manager.stats['inventory_extracted'] == 0


class TestRunEtlFunction:
    def test_run_etl_returns_dict(self):
        with patch('etl_manager.ETLManager') as MockManager:
            mock_instance = MagicMock()
            mock_instance.run_pipeline.return_value = {'success': True, 'stats': {}}
            MockManager.return_value = mock_instance
            from etl_manager import run_etl
            result = run_etl('csv')
            assert isinstance(result, dict)


class TestRunInventoryEtl:
    """Tests for _run_inventory_etl with inventory data."""

    def _make_manager(self):
        with patch('etl_manager.CSVDataSource'), \
             patch('etl_manager.APIDataSource'), \
             patch('etl_manager.DBDataSource'), \
             patch('etl_manager.OdooLoader'), \
             patch('etl_manager.Config'):
            from etl_manager import ETLManager
            manager = ETLManager.__new__(ETLManager)
            manager.source_type = 'csv'
            manager.logger = MagicMock()
            manager.start_time = None
            manager.stats = {
                'products_extracted': 0, 'products_transformed': 0,
                'products_loaded': 0, 'inventory_extracted': 0,
                'inventory_transformed': 0, 'inventory_adjusted': 0,
                'errors': [], 'start_time': None, 'end_time': None,
            }
            manager.data_source = MagicMock()
            manager.product_transformer = MagicMock()
            manager.inventory_transformer = MagicMock()
            manager.odoo_loader = MagicMock()
            return manager

    def test_run_inventory_etl_with_data_adjusts(self):
        manager = self._make_manager()
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 10}]
        transformed = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 10}]
        manager.data_source.extract_inventory.return_value = raw
        manager.inventory_transformer.transform.return_value = transformed
        manager.inventory_transformer.group_by_location.return_value = {
            'WH': [{'sku': 'S1', 'quantity': 10}]
        }
        manager.inventory_transformer.aggregate_quantities.return_value = {'S1': 10}
        manager.odoo_loader.get_location_by_name.return_value = 5
        manager.odoo_loader.search_record.return_value = []
        manager.odoo_loader.read_record.return_value = [{'id': 1, 'default_code': 'S1'}]
        manager.odoo_loader.adjust_inventory.return_value = True
        manager._run_inventory_etl()
        assert manager.stats['inventory_extracted'] == 1
        assert manager.stats['inventory_adjusted'] == 1

    def test_run_inventory_etl_location_not_found_skips(self):
        manager = self._make_manager()
        raw = [{'sku': 'S1', 'location_name': 'UNKNOWN', 'quantity': 5}]
        manager.data_source.extract_inventory.return_value = raw
        manager.inventory_transformer.transform.return_value = raw
        manager.inventory_transformer.group_by_location.return_value = {
            'UNKNOWN': [{'sku': 'S1', 'quantity': 5}]
        }
        manager.odoo_loader.search_record.return_value = []
        manager.odoo_loader.read_record.return_value = []
        manager.odoo_loader.get_location_by_name.return_value = None
        manager._run_inventory_etl()
        manager.odoo_loader.adjust_inventory.assert_not_called()

    def test_run_inventory_etl_adjust_error_logged(self):
        manager = self._make_manager()
        raw = [{'sku': 'S1', 'location_name': 'WH', 'quantity': 10}]
        manager.data_source.extract_inventory.return_value = raw
        manager.inventory_transformer.transform.return_value = raw
        manager.inventory_transformer.group_by_location.return_value = {
            'WH': [{'sku': 'S1', 'quantity': 10}]
        }
        manager.inventory_transformer.aggregate_quantities.return_value = {'S1': 10}
        manager.odoo_loader.get_location_by_name.return_value = 5
        manager.odoo_loader.search_record.return_value = [1]
        manager.odoo_loader.read_record.return_value = [{'id': 1, 'default_code': 'S1'}]
        manager.odoo_loader.adjust_inventory.side_effect = Exception("adjust failed")
        manager._run_inventory_etl()
        assert len(manager.stats['errors']) == 1

    def test_get_product_mapping_builds_dict(self):
        manager = self._make_manager()
        manager.odoo_loader.search_record.return_value = [1, 2]
        manager.odoo_loader.read_record.return_value = [
            {'id': 1, 'default_code': 'SKU001'},
            {'id': 2, 'default_code': None},
        ]
        mapping = manager._get_product_mapping()
        assert mapping == {'SKU001': 1}

    def test_run_products_etl_validate_false_skips(self):
        manager = self._make_manager()
        raw = [{'name': 'Prod A', 'default_code': 'A001'}]
        manager.data_source.extract_products.return_value = raw
        manager.product_transformer.transform.return_value = raw
        manager.product_transformer.validate.return_value = False
        manager._run_products_etl()
        manager.odoo_loader.create_or_update_product.assert_not_called()

    def test_run_products_etl_load_error_logged(self):
        manager = self._make_manager()
        raw = [{'name': 'Prod A', 'default_code': 'A001'}]
        manager.data_source.extract_products.return_value = raw
        manager.product_transformer.transform.return_value = raw
        manager.product_transformer.validate.return_value = True
        manager.odoo_loader.create_or_update_product.side_effect = Exception("create failed")
        manager._run_products_etl()
        assert len(manager.stats['errors']) == 1
