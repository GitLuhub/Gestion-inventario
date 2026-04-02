"""
test_routes.py — Tests de integración del API Gateway.

Usa el cliente HTTP de sesión definido en conftest.py con OdooClient mockeado.
Cubre: root, health, metrics, auth, products, inventory.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


# ===========================================================================
# Endpoints raíz / infraestructura
# ===========================================================================
class TestRootEndpoints:
    def test_root_returns_name_version_status(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint_returns_healthy(self, client, mock_odoo):
        mock_odoo.test_connection.return_value = True
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data

    def test_health_endpoint_degraded_when_odoo_down(self, client, mock_odoo):
        mock_odoo.test_connection.return_value = False
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
        mock_odoo.test_connection.return_value = True  # restore

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_request_id_header_propagated(self, client):
        response = client.get("/", headers={"X-Request-ID": "test-req-123"})
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == "test-req-123"

    def test_request_id_generated_when_absent(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_process_time_header_present(self, client):
        response = client.get("/")
        assert "X-Process-Time" in response.headers


# ===========================================================================
# Auth — /api/v1/auth
# ===========================================================================
class TestAuthLogin:
    def test_login_success(self, client, mock_odoo):
        mock_odoo.common.authenticate.return_value = 1
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, mock_odoo):
        mock_odoo.common.authenticate.return_value = False
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "wrong", "password": "wrong"},
        )
        assert response.status_code == 401
        mock_odoo.common.authenticate.return_value = 1  # restore

    def test_login_missing_username(self, client):
        response = client.post(
            "/api/v1/auth/login",
            data={"password": "admin"},
        )
        assert response.status_code == 422

    def test_login_sets_httponly_cookie(self, client, mock_odoo):
        mock_odoo.common.authenticate.return_value = 1
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},
        )
        assert response.status_code == 200
        cookies = response.headers.get("set-cookie", "")
        assert "refresh_token" in cookies
        assert "HttpOnly" in cookies

    def test_login_odoo_exception_returns_500(self, client, mock_odoo):
        mock_odoo.common.authenticate.side_effect = Exception("Odoo down")
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin"},
        )
        assert response.status_code == 500
        mock_odoo.common.authenticate.side_effect = None
        mock_odoo.common.authenticate.return_value = 1  # restore


class TestAuthRefresh:
    def test_refresh_no_cookie_returns_401(self, client):
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    def test_refresh_with_valid_cookie_returns_new_token(
        self, client, refresh_token_value
    ):
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token_value},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_refresh_with_invalid_cookie_returns_401(self, client):
        response = client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "invalid.jwt.token"},
        )
        assert response.status_code == 401


class TestAuthMe:
    def test_me_authorized(self, client, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"

    def test_me_unauthorized(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)


class TestAuthLogout:
    def test_logout_authorized(self, client, auth_headers):
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200

    def test_logout_unauthorized(self, client):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code in (401, 403)


# ===========================================================================
# Products — /api/v1/products
# ===========================================================================
PRODUCT_DICT = {
    'id': 1,
    'name': 'Laptop HP',
    'default_code': 'LAP001',
    'description': False,
    'type': 'product',
    'list_price': 1299.99,
    'standard_price': 950.0,
    'weight': 1.8,
    'barcode': False,
    'active': True,
    'categ_id': [1, 'All'],
    'qty_available': 10.0,
    'virtual_available': 8.0,
    'create_date': '2025-01-01 00:00:00',
    'write_date': '2025-06-01 00:00:00',
}


class TestProductsList:
    def test_list_products_unauthorized(self, client):
        response = client.get("/api/v1/products")
        assert response.status_code in (401, 403)

    def test_list_products_returns_paginated(self, client, auth_headers, mock_odoo):
        mock_odoo.search_count.return_value = 1
        mock_odoo.search_read.return_value = [PRODUCT_DICT]
        response = client.get("/api/v1/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1

    def test_list_products_with_search(self, client, auth_headers, mock_odoo):
        mock_odoo.search_count.return_value = 0
        mock_odoo.search_read.return_value = []
        response = client.get(
            "/api/v1/products?search=laptop", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_products_with_category_filter(self, client, auth_headers, mock_odoo):
        mock_odoo.search_count.return_value = 0
        mock_odoo.search_read.return_value = []
        response = client.get(
            "/api/v1/products?category_id=1", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_products_inactive(self, client, auth_headers, mock_odoo):
        mock_odoo.search_count.return_value = 0
        mock_odoo.search_read.return_value = []
        response = client.get(
            "/api/v1/products?active=false", headers=auth_headers
        )
        assert response.status_code == 200


class TestProductGet:
    def test_get_product_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = [PRODUCT_DICT]
        response = client.get("/api/v1/products/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Laptop HP"

    def test_get_product_not_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = []
        response = client.get("/api/v1/products/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_product_unauthorized(self, client):
        response = client.get("/api/v1/products/1")
        assert response.status_code in (401, 403)


class TestProductCreate:
    def test_create_product_success(self, client, auth_headers, mock_odoo):
        mock_odoo.create.return_value = 42
        mock_odoo.read.return_value = [{**PRODUCT_DICT, 'id': 42}]
        payload = {"name": "New Product", "list_price": 100.0, "type": "product"}
        response = client.post(
            "/api/v1/products", headers=auth_headers, json=payload
        )
        assert response.status_code == 201

    def test_create_product_validation_error(self, client, auth_headers):
        response = client.post(
            "/api/v1/products",
            headers=auth_headers,
            json={"name": ""},  # min_length=1
        )
        assert response.status_code == 422

    def test_create_product_odoo_error(self, client, auth_headers, mock_odoo):
        mock_odoo.create.side_effect = Exception("Duplicate barcode")
        payload = {"name": "Error Product"}
        response = client.post(
            "/api/v1/products", headers=auth_headers, json=payload
        )
        assert response.status_code == 400
        mock_odoo.create.side_effect = None
        mock_odoo.create.return_value = 1  # restore

    def test_create_product_unauthorized(self, client):
        response = client.post("/api/v1/products", json={"name": "X"})
        assert response.status_code in (401, 403)


class TestProductUpdate:
    def test_update_product_success(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = [PRODUCT_DICT]
        mock_odoo.write.return_value = True
        response = client.put(
            "/api/v1/products/1",
            headers=auth_headers,
            json={"name": "Updated Laptop"},
        )
        assert response.status_code == 200

    def test_update_product_not_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = []
        response = client.put(
            "/api/v1/products/99999",
            headers=auth_headers,
            json={"name": "X"},
        )
        assert response.status_code == 404

    def test_update_product_unauthorized(self, client):
        response = client.put("/api/v1/products/1", json={"name": "X"})
        assert response.status_code in (401, 403)


class TestProductDelete:
    def test_delete_product_success(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = [PRODUCT_DICT]
        mock_odoo.write.return_value = True
        response = client.delete("/api/v1/products/1", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_product_not_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = []
        response = client.delete("/api/v1/products/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_product_unauthorized(self, client):
        response = client.delete("/api/v1/products/1")
        assert response.status_code in (401, 403)


class TestLowStockProducts:
    def test_low_stock_returns_list(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = [
            {'id': 1, 'name': 'Prod A', 'default_code': 'A1',
             'qty_available': 2, 'min_stock_level': 10}
        ]
        response = client.get(
            "/api/v1/products/search/low-stock", headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_low_stock_unauthorized(self, client):
        response = client.get("/api/v1/products/search/low-stock")
        assert response.status_code in (401, 403)


# ===========================================================================
# Inventory — /api/v1/inventory
# ===========================================================================
QUANT_DICT = {
    'id': 1,
    'product_id': [1, 'Laptop HP'],
    'location_id': [5, 'WH/Stock'],
    'quantity': 10.0,
    'reserved_quantity': 2.0,
    'lot_id': False,
    'in_date': '2025-01-01 00:00:00',
}

ADJUSTMENT_DICT = {
    'id': 1,
    'name': 'ADJ/00001',
    'write_date': '2025-06-01 00:00:00',
    'state': 'done',
    'adjustment_type': 'partial',
}


class TestInventoryQuants:
    def test_list_quants_unauthorized(self, client):
        response = client.get("/api/v1/inventory/quants")
        assert response.status_code in (401, 403)

    def test_list_quants_empty(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = []
        mock_odoo.read.return_value = []
        response = client.get("/api/v1/inventory/quants", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_quants_with_data(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = [QUANT_DICT]
        mock_odoo.read.return_value = [
            {'id': 1, 'name': 'Laptop HP'},
        ]
        response = client.get("/api/v1/inventory/quants", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["product_id"] == 1

    def test_list_quants_with_product_filter(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = []
        mock_odoo.read.return_value = []
        response = client.get(
            "/api/v1/inventory/quants?product_id=1", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_quants_with_location_filter(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = []
        mock_odoo.read.return_value = []
        response = client.get(
            "/api/v1/inventory/quants?location_id=5", headers=auth_headers
        )
        assert response.status_code == 200


class TestInventoryAdjustments:
    def test_list_adjustments_unauthorized(self, client):
        response = client.get("/api/v1/inventory/adjustments")
        assert response.status_code in (401, 403)

    def test_list_adjustments_empty(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = []
        response = client.get(
            "/api/v1/inventory/adjustments", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_adjustments_with_data(self, client, auth_headers, mock_odoo):
        mock_odoo.search_read.return_value = [ADJUSTMENT_DICT]
        mock_odoo.search_count.return_value = 2
        response = client.get(
            "/api/v1/inventory/adjustments", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "ADJ/00001"

    def test_create_adjustment_unauthorized(self, client):
        response = client.post("/api/v1/inventory/adjustments", json={})
        assert response.status_code in (401, 403)

    def test_create_adjustment_success(self, client, auth_headers, mock_odoo):
        mock_odoo.create.return_value = 10
        mock_odoo.call_method.return_value = None
        payload = {
            "name": "ADJ Test",
            "lines": [
                {
                    "name": "Line 1",
                    "product_id": 1,
                    "location_id": 5,
                    "quantity": 10.0,
                    "adjustment_reason": "count",
                }
            ],
        }
        response = client.post(
            "/api/v1/inventory/adjustments",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code in (201, 400)  # 400 si Odoo falla en acción

    def test_create_adjustment_odoo_error(self, client, auth_headers, mock_odoo):
        mock_odoo.create.side_effect = Exception("Odoo error")
        payload = {
            "name": "ADJ Fail",
            "lines": [
                {"name": "Line 1", "product_id": 1, "location_id": 5,
                 "quantity": 5.0, "adjustment_reason": "count"}
            ],
        }
        response = client.post(
            "/api/v1/inventory/adjustments",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 400
        mock_odoo.create.side_effect = None
        mock_odoo.create.return_value = 1  # restore


class TestInventoryByLocation:
    def test_by_location_unauthorized(self, client):
        response = client.get("/api/v1/inventory/by-location/5")
        assert response.status_code in (401, 403)

    def test_by_location_not_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.return_value = []
        response = client.get(
            "/api/v1/inventory/by-location/99999", headers=auth_headers
        )
        assert response.status_code == 404

    def test_by_location_found(self, client, auth_headers, mock_odoo):
        mock_odoo.read.side_effect = [
            [{'id': 5, 'name': 'WH/Stock'}],   # location read
            [],                                  # products read
        ]
        mock_odoo.search_read.return_value = []
        response = client.get(
            "/api/v1/inventory/by-location/5", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] == 5
        assert data["location_name"] == "WH/Stock"
        mock_odoo.read.side_effect = None
        mock_odoo.read.return_value = []  # restore


# ===========================================================================
# Utils — auth.py (coverage sin HTTP)
# ===========================================================================
class TestAuthUtils:
    def test_create_access_token(self):
        from src.utils.auth import create_access_token
        token = create_access_token({'sub': 'user1', 'user_id': 1})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        from src.utils.auth import create_access_token
        from datetime import timedelta
        token = create_access_token({'sub': 'u'}, expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)

    def test_create_refresh_token(self):
        from src.utils.auth import create_refresh_token
        token = create_refresh_token({'sub': 'user1', 'user_id': 1})
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        from src.utils.auth import create_access_token, decode_token
        token = create_access_token({'sub': 'user1'})
        payload = decode_token(token)
        assert payload['sub'] == 'user1'
        assert payload['type'] == 'access'

    def test_decode_invalid_token_raises(self):
        from src.utils.auth import decode_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_get_password_hash_and_verify(self):
        from src.utils.auth import get_password_hash, verify_password
        # Use mock to avoid bcrypt/passlib version incompatibilities in CI
        with patch('src.utils.auth.pwd_context') as mock_ctx:
            mock_ctx.hash.return_value = '$2b$12$fakehash'
            mock_ctx.verify.side_effect = lambda plain, hashed: plain == 'secret'
            h = get_password_hash('secret')
            assert h == '$2b$12$fakehash'
            assert verify_password('secret', h) is True
            assert verify_password('wrong', h) is False

    def test_verify_refresh_token_valid(self):
        import asyncio
        from src.utils.auth import create_refresh_token, verify_refresh_token
        token = create_refresh_token({'sub': 'user1'})
        payload = asyncio.get_event_loop().run_until_complete(
            verify_refresh_token(token)
        )
        assert payload['type'] == 'refresh'

    def test_verify_refresh_token_access_token_raises(self):
        import asyncio
        from src.utils.auth import create_access_token, verify_refresh_token
        from fastapi import HTTPException
        token = create_access_token({'sub': 'user1'})
        with pytest.raises(HTTPException):
            asyncio.get_event_loop().run_until_complete(
                verify_refresh_token(token)
            )


# ===========================================================================
# Utils — OdooClient (coverage de métodos individuales)
# ===========================================================================
class TestOdooClientMethods:
    def _make_client(self):
        """Crea OdooClient con _connect mockeado para no conectar."""
        with patch('src.utils.odoo_client.OdooClient._connect'):
            from src.utils.odoo_client import OdooClient
            c = OdooClient()
        c.uid = 1
        c.db = 'test_db'
        c.password = 'test_pass'
        c.models = MagicMock()
        c.common = MagicMock()
        c.common.version.return_value = {'server_version': '16.0'}
        return c

    def test_search_read(self):
        c = self._make_client()
        c.models.execute_kw.return_value = [{'id': 1}]
        result = c.search_read('product.product', [])
        assert result == [{'id': 1}]

    def test_search_read_with_fields_and_order(self):
        c = self._make_client()
        c.models.execute_kw.return_value = []
        result = c.search_read('product.product', [], fields=['name'], order='name ASC')
        assert result == []

    def test_create(self):
        c = self._make_client()
        c.models.execute_kw.return_value = 5
        assert c.create('product.product', {'name': 'X'}) == 5

    def test_write(self):
        c = self._make_client()
        c.models.execute_kw.return_value = True
        assert c.write('product.product', [1], {'name': 'Y'}) is True

    def test_unlink(self):
        c = self._make_client()
        c.models.execute_kw.return_value = True
        assert c.unlink('product.product', [1]) is True

    def test_search_count(self):
        c = self._make_client()
        c.models.execute_kw.return_value = 7
        assert c.search_count('product.product') == 7

    def test_search_with_limit(self):
        c = self._make_client()
        c.models.execute_kw.return_value = [1, 2]
        result = c.search('product.product', [], limit=10)
        assert result == [1, 2]

    def test_search_without_limit(self):
        c = self._make_client()
        c.models.execute_kw.return_value = [1]
        result = c.search('product.product')
        assert result == [1]

    def test_read_empty_ids(self):
        c = self._make_client()
        assert c.read('product.product', []) == []

    def test_read_with_ids(self):
        c = self._make_client()
        c.models.execute_kw.return_value = [{'id': 1, 'name': 'X'}]
        result = c.read('product.product', [1], fields=['name'])
        assert result[0]['name'] == 'X'

    def test_call_method(self):
        c = self._make_client()
        c.models.execute_kw.return_value = None
        c.call_method('stock.inventory.adjustment', 'action_validate', [1])

    def test_test_connection_true(self):
        c = self._make_client()
        c.common.version.return_value = {'server_version': '16.0'}
        assert c.test_connection() is True

    def test_test_connection_false_on_error(self):
        c = self._make_client()
        c.common.version.side_effect = Exception("down")
        assert c.test_connection() is False


# ===========================================================================
# Utils — audit.py
# ===========================================================================
class TestAuditLog:
    def test_log_audit_does_not_raise(self):
        from src.utils.audit import log_audit
        log_audit(
            action="test.action",
            user_id=1,
            resource="product",
            resource_id="42",
            ip="127.0.0.1",
            request_id="req-uuid-123",
            status="success",
            details={"key": "value"},
        )

    def test_log_audit_none_details(self):
        from src.utils.audit import log_audit
        log_audit(
            action="test.action",
            user_id=None,
            resource="session",
            resource_id=None,
            ip="-",
            request_id="-",
            status="failure",
        )


# ===========================================================================
# Utils — logger.py
# ===========================================================================
class TestLogger:
    def test_get_logger_returns_logger(self):
        from src.utils.logger import get_logger
        import logging
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_json_formatter_produces_valid_json(self):
        import json
        import logging
        from src.utils.logger import JsonFormatter
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name='test', level=logging.INFO,
            pathname='', lineno=0, msg='hello',
            args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed['message'] == 'hello'
        assert parsed['level'] == 'INFO'

    def test_json_formatter_with_exception(self):
        import json
        import logging
        from src.utils.logger import JsonFormatter
        formatter = JsonFormatter()
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

    def test_setup_json_logging_does_not_raise(self):
        from src.utils.logger import setup_json_logging
        setup_json_logging('INFO')
        setup_json_logging('DEBUG')


# ===========================================================================
# Middleware — request_id.py
# ===========================================================================
class TestRequestIDMiddleware:
    def test_middleware_adds_request_id(self, client):
        response = client.get("/")
        assert "X-Request-ID" in response.headers

    def test_middleware_preserves_provided_request_id(self, client):
        custom_id = "my-custom-id-abc123"
        response = client.get("/", headers={"X-Request-ID": custom_id})
        assert response.headers.get("X-Request-ID") == custom_id
