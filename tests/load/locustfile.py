"""
tests/load/locustfile.py — Tests de carga con Locust (J3)
==========================================================
Simula tráfico realista sobre el API Gateway para validar los objetivos
de rendimiento bajo carga concurrente:

  Criterios de aceptación (documentados en README):
    · P95 latencia < 500 ms para endpoints GET de listas
    · Tasa de error < 1% bajo 50 usuarios concurrentes
    · Throughput ≥ 20 req/s en el escenario principal

Cómo ejecutar:

  # Instalar locust (no incluido en requirements.txt del proyecto)
  pip install locust==2.20.1

  # Modo headless — 50 usuarios, rampa de 5/s, durante 2 minutos
  locust -f tests/load/locustfile.py \
    --headless \
    --users 50 \
    --spawn-rate 5 \
    --run-time 2m \
    --host http://localhost:8000

  # Modo web (dashboard interactivo)
  locust -f tests/load/locustfile.py --host http://localhost:8000
  # Abrir http://localhost:8089

Perfiles disponibles:
  InventoryReadUser    — operaciones de solo lectura (lectura de inventario, productos)
  InventoryWriteUser   — flujo completo (login → ajuste de stock → logout)
"""

import json
import random
from locust import HttpUser, TaskSet, between, task, events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
DEMO_CREDENTIALS = {"username": "admin", "password": "admin"}
PRODUCT_NAMES = [
    "Laptop Demo 15\"", "Monitor 24\" Demo", "Teclado Inalámbrico",
    "Ratón Ergonómico", "Disco Duro 1TB",
]


def login(client) -> str | None:
    """Autenticarse y retornar el access token."""
    with client.post(
        "/api/v1/auth/login",
        data=DEMO_CREDENTIALS,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        name="POST /auth/login",
        catch_response=True,
    ) as resp:
        if resp.status_code == 200:
            return resp.json().get("access_token")
        resp.failure(f"Login falló: {resp.status_code}")
        return None


# ---------------------------------------------------------------------------
# Escenario 1: Solo lectura (70% del tráfico simulado)
# ---------------------------------------------------------------------------
class InventoryReadUser(HttpUser):
    """
    Simula un usuario consultor que navega por el inventario sin escribir.
    · P95 objetivo: < 500 ms
    · Peso: 70% del tráfico total
    """
    weight = 7
    wait_time = between(1, 3)

    def on_start(self):
        self.token = login(self.client)
        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(5)
    def list_products(self):
        page = random.randint(1, 3)
        self.client.get(
            f"/api/v1/products?page={page}&page_size=20",
            name="GET /products (paginado)",
        )

    @task(3)
    def list_inventory(self):
        self.client.get(
            "/api/v1/inventory?page=1&page_size=20",
            name="GET /inventory",
        )

    @task(2)
    def low_stock(self):
        self.client.get(
            "/api/v1/products/search/low-stock",
            name="GET /products/search/low-stock",
        )

    @task(1)
    def health_check(self):
        with self.client.get("/health", name="GET /health", catch_response=True) as resp:
            if resp.json().get("status") not in ("healthy", "degraded"):
                resp.failure("Health check retornó estado inesperado")


# ---------------------------------------------------------------------------
# Escenario 2: Escritura (30% del tráfico simulado)
# ---------------------------------------------------------------------------
class InventoryWriteUser(HttpUser):
    """
    Simula un operador de almacén que realiza ajustes de inventario.
    · P95 objetivo: < 1000 ms (operaciones de escritura son más lentas)
    · Peso: 30% del tráfico total
    """
    weight = 3
    wait_time = between(2, 5)

    def on_start(self):
        self.token = login(self.client)
        if self.token:
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def list_products_before_adjust(self):
        """Consultar productos antes de ajustar — flujo realista."""
        self.client.get(
            "/api/v1/products?page=1&page_size=10",
            name="GET /products (pre-ajuste)",
        )

    @task(1)
    def adjust_inventory(self):
        """Crear un ajuste de inventario."""
        payload = {
            "product_id": random.randint(1, 10),
            "location_id": 5,
            "new_qty": random.uniform(10.0, 100.0),
        }
        with self.client.post(
            "/api/v1/inventory/adjust",
            json=payload,
            name="POST /inventory/adjust",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 201, 422):
                # 422 es esperado si el producto/ubicación no existe en el seed
                resp.failure(f"Adjust falló con status {resp.status_code}")

    @task(1)
    def list_adjustments(self):
        self.client.get(
            "/api/v1/inventory/adjustments?page=1&page_size=10",
            name="GET /inventory/adjustments",
        )


# ---------------------------------------------------------------------------
# Hook de reporte: imprime resumen de SLOs al finalizar
# ---------------------------------------------------------------------------
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    if stats.num_requests == 0:
        return

    p95 = stats.get_response_time_percentile(0.95)
    error_rate = stats.fail_ratio * 100

    print("\n" + "=" * 60)
    print("RESUMEN DE SLOs")
    print("=" * 60)
    print(f"  Total requests:    {stats.num_requests}")
    print(f"  Tasa de error:     {error_rate:.2f}% (objetivo: < 1%)")
    print(f"  P95 latencia:      {p95:.0f} ms (objetivo: < 500 ms)")
    print(f"  Throughput:        {stats.current_rps:.1f} req/s")
    print("=" * 60)

    slo_ok = error_rate < 1.0 and p95 < 500
    print(f"  SLOs cumplidos:    {'✅ SÍ' if slo_ok else '❌ NO'}")
    print("=" * 60 + "\n")

    if not slo_ok:
        environment.process_exit_code = 1
