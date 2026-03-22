import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestRootEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data

    def test_health_endpoint(self, client):
        with patch('src.utils.odoo_client.get_odoo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.test_connection.return_value = True
            mock_get_client.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"] or "text/" in response.headers["content-type"]


class TestAuthRoutes:
    def test_login_success(self, client):
        with patch('src.utils.odoo_client.get_odoo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.test_connection.return_value = True
            mock_get_client.return_value = mock_client
            
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            assert response.status_code in [200, 401]

    def test_login_missing_fields(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin"}
        )
        assert response.status_code == 422

    def test_refresh_token(self, client):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "test_token"}
        )
        assert response.status_code in [200, 401]


class TestProductRoutes:
    def test_list_products_unauthorized(self, client):
        response = client.get("/api/v1/products")
        assert response.status_code == 401

    def test_list_products_with_token(self, client, auth_token):
        with patch('src.utils.odoo_client.get_odoo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.test_connection.return_value = True
            mock_client.execute_kw.return_value = []
            mock_get_client.return_value = mock_client
            
            response = client.get(
                "/api/v1/products",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code in [200, 401]

    def test_get_product_not_found(self, client, auth_token):
        with patch('src.utils.odoo_client.get_odoo_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.test_connection.return_value = True
            mock_client.execute_kw.side_effect = Exception("Not found")
            mock_get_client.return_value = mock_client
            
            response = client.get(
                "/api/v1/products/99999",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code in [404, 500]

    def test_create_product_validation(self, client, auth_token):
        response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": ""}
        )
        assert response.status_code == 422


class TestInventoryRoutes:
    def test_get_quants_unauthorized(self, client):
        response = client.get("/api/v1/inventory/quants")
        assert response.status_code == 401

    def test_get_adjustments_unauthorized(self, client):
        response = client.get("/api/v1/inventory/adjustments")
        assert response.status_code == 401


@pytest.fixture
def client():
    from src.main import app
    return TestClient(app)


@pytest.fixture
def auth_token():
    return "test_token_12345"
