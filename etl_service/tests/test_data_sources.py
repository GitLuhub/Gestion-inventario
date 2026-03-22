import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.data_sources.csv_source import CSVDataSource
from src.data_sources.base_source import DataSource


class TestCSVDataSource:
    def test_csv_source_initialization(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,code\nProduct 1,001\nProduct 2,002")
        
        source = CSVDataSource(str(csv_file))
        
        assert source.file_path == str(csv_file)

    def test_csv_source_extract(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,code\nProduct 1,001\nProduct 2,002")
        
        source = CSVDataSource(str(csv_file))
        records = source.extract()
        
        assert len(records) == 2
        assert records[0]['name'] == 'Product 1'
        assert records[1]['code'] == '002'

    def test_csv_source_with_different_delimiter(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name;code\nProduct 1;001")
        
        source = CSVDataSource(str(csv_file), delimiter=';')
        records = source.extract()
        
        assert len(records) == 1
        assert records[0]['name'] == 'Product 1'

    def test_csv_source_file_not_found(self):
        source = CSVDataSource('/nonexistent/file.csv')
        
        with pytest.raises(FileNotFoundError):
            source.extract()


class TestDataSource:
    def test_base_source_interface(self):
        source = DataSource()
        
        assert hasattr(source, 'extract')
        assert hasattr(source, 'validate')
        assert callable(source.extract)
        assert callable(source.validate)
