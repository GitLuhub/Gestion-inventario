"""
Tests de data sources — cobertura principal en test_loaders_and_sources.py.
Este archivo valida la interfaz pública del paquete data_sources.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_sources import CSVDataSource, APIDataSource, DBDataSource, BaseDataSource


class TestDataSourcesPackage:
    def test_csv_source_is_exported(self):
        assert CSVDataSource is not None

    def test_api_source_is_exported(self):
        assert APIDataSource is not None

    def test_db_source_is_exported(self):
        assert DBDataSource is not None

    def test_base_source_is_exported(self):
        assert BaseDataSource is not None

    def test_csv_source_is_subclass_of_base(self):
        assert issubclass(CSVDataSource, BaseDataSource)

    def test_api_source_is_subclass_of_base(self):
        assert issubclass(APIDataSource, BaseDataSource)

    def test_db_source_is_subclass_of_base(self):
        assert issubclass(DBDataSource, BaseDataSource)
