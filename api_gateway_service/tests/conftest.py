"""
conftest.py — Fixtures de sesión para tests del API Gateway.

El problema central: odoo_client.py instanciaba OdooClient() al importarse,
intentando conectarse a Odoo. En CI no hay Odoo disponible.

Solución:
  1. odoo_client.py usa lazy init (_odoo_client = None, crea en primera llamada)
  2. Este conftest parchea _odoo_client con un MagicMock antes de importar la app,
     evitando cualquier conexión real.
  3. FastAPI dependency_overrides garantiza que get_odoo_client() devuelva el mock
     en todos los endpoints durante los tests.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Añadir src al path para importaciones directas en tests de utils
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Variables de entorno mínimas para que Settings no falle en CI
os.environ.setdefault('ODOO_URL', 'http://localhost:8069')
os.environ.setdefault('ODOO_DB', 'test_db')
os.environ.setdefault('ODOO_USER', 'admin')
os.environ.setdefault('ODOO_PASSWORD', 'admin_test')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-ci-only-32chars!')
os.environ.setdefault('LOG_LEVEL', 'WARNING')


def _build_mock_odoo() -> MagicMock:
    """Construye un MagicMock que simula OdooClient."""
    mock = MagicMock()
    mock.uid = 1
    mock.url = 'http://localhost:8069'
    mock.db = 'test_db'
    mock.user = 'admin'
    mock.password = 'admin_test'

    # common.authenticate — usado en el endpoint /login
    mock.common = MagicMock()
    mock.common.authenticate.return_value = 1
    mock.common.version.return_value = {'server_version': '16.0'}

    # test_connection — usado en /health y lifespan
    mock.test_connection.return_value = True

    # Métodos ORM — valores vacíos por defecto (cada test sobreescribe si necesita)
    mock.search_read.return_value = []
    mock.search_count.return_value = 0
    mock.read.return_value = []
    mock.create.return_value = 1
    mock.write.return_value = True
    mock.unlink.return_value = True
    mock.search.return_value = []
    mock.call_method.return_value = None

    return mock


@pytest.fixture(scope='session')
def mock_odoo() -> MagicMock:
    return _build_mock_odoo()


@pytest.fixture(scope='session')
def app(mock_odoo):
    """
    Importa la app FastAPI con _odoo_client parchado para evitar la conexión
    real al Odoo. El patch permanece activo durante toda la sesión de tests.
    """
    # Parchar _odoo_client ANTES de importar src.main para que:
    # a) lifespan no intente instanciar OdooClient
    # b) get_odoo_client() devuelva el mock directamente (lazy init lo omite)
    with patch('src.utils.odoo_client._odoo_client', mock_odoo):
        from src.main import app as fastapi_app
        from src.utils.odoo_client import get_odoo_client

        # Override de dependencia FastAPI para todos los endpoints
        fastapi_app.dependency_overrides[get_odoo_client] = lambda: mock_odoo

        yield fastapi_app

        fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope='session')
def client(app):
    """TestClient de sesión — el lifespan se ejecuta una vez."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope='session')
def access_token():
    """JWT de acceso válido para usar en headers Authorization."""
    from src.utils.auth import create_access_token
    return create_access_token({'sub': 'admin', 'user_id': 1})


@pytest.fixture(scope='session')
def refresh_token_value():
    """JWT de refresh válido para cookies."""
    from src.utils.auth import create_refresh_token
    return create_refresh_token({'sub': 'admin', 'user_id': 1})


@pytest.fixture(scope='session')
def auth_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}
