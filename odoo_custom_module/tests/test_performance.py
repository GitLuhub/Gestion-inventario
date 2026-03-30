"""
Tests de rendimiento — RNF1
===========================
Verifican que las operaciones CRUD y de consulta cumplen los umbrales del PRD:
  - Operaciones CRUD simples:  < 2 segundos
  - Consultas de tipo informe: < 5 segundos

Cómo ejecutar:
    docker exec inventory_odoo_app odoo-bin \
      -d odoo_db \
      --test-tags /inventory_custom:TestCRUDPerformance \
      --stop-after-init

Los tests usan TransactionCase (transacción se revierte tras cada test) por lo que
no dejan datos en la base de datos.

Nota: los umbrales son conservadores y se miden en el servidor donde corre Odoo
(no incluyen latencia de red). En un entorno sin carga la mayoría de operaciones
tarda < 100 ms; el límite de 2 s da margen para entornos con recursos ajustados.
"""

import time
from odoo.tests import TransactionCase


class TestCRUDPerformance(TransactionCase):
    """CRUD < 2 s por operación (RNF1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CRUD_LIMIT = 2.0

        cls.location = cls.env['stock.location'].create({
            'name': 'Perf Test Location',
            'usage': 'internal',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Perf Test Product',
            'type': 'product',
        })

    # ------------------------------------------------------------------
    # product.brand
    # ------------------------------------------------------------------

    def test_brand_create_under_2s(self):
        """Crear una marca tarda menos de 2 s."""
        t0 = time.monotonic()
        self.env['product.brand'].create({'name': 'PerfBrand'})
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'product.brand.create tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )

    def test_brand_read_under_2s(self):
        """Leer todas las marcas tarda menos de 2 s."""
        for i in range(10):
            self.env['product.brand'].create({'name': f'Brand {i}'})
        t0 = time.monotonic()
        self.env['product.brand'].search_read([], ['name', 'product_count'])
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'product.brand.search_read tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )

    def test_product_template_write_under_2s(self):
        """Actualizar campos de producto tarda menos de 2 s."""
        tmpl = self.env['product.template'].create({
            'name': 'Perf Product Tmpl',
            'type': 'product',
            'min_stock_level': 0.0,
        })
        t0 = time.monotonic()
        tmpl.write({'min_stock_level': 50.0, 'max_stock_level': 200.0})
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'product.template.write tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )

    def test_stock_location_create_under_2s(self):
        """Crear una ubicación tarda menos de 2 s."""
        t0 = time.monotonic()
        self.env['stock.location'].create({
            'name': 'Perf Location',
            'usage': 'internal',
            'location_type': 'shelf',
            'max_capacity': 500.0,
        })
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'stock.location.create tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )

    def test_adjustment_create_and_start_under_2s(self):
        """Crear un ajuste de inventario y pasarlo a in_progress tarda menos de 2 s."""
        t0 = time.monotonic()
        adj = self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, self.location.id)],
        })
        adj.action_start()
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'Adjustment create+start tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )

    def test_adjustment_line_create_batch_under_2s(self):
        """Crear 20 líneas de ajuste en lote tarda menos de 2 s."""
        adj = self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, self.location.id)],
        })
        products = self.env['product.product'].create([
            {'name': f'Bulk Product {i}', 'type': 'product'} for i in range(20)
        ])
        lines_vals = [
            {
                'adjustment_id': adj.id,
                'product_id': p.id,
                'location_id': self.location.id,
                'current_qty': float(i),
                'expected_qty': float(i + 1),
            }
            for i, p in enumerate(products)
        ]
        t0 = time.monotonic()
        self.env['stock.inventory.adjustment.line'].create(lines_vals)
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.CRUD_LIMIT,
            f'Crear 20 líneas de ajuste tardó {elapsed:.3f}s (límite {self.CRUD_LIMIT}s)',
        )


class TestReportQueryPerformance(TransactionCase):
    """Consultas de tipo informe < 5 s (RNF1)."""

    REPORT_LIMIT = 5.0

    def test_stock_quant_report_under_5s(self):
        """La consulta del informe 'Stock por Ubicación' tarda menos de 5 s."""
        t0 = time.monotonic()
        self.env['stock.quant'].search_read(
            [('location_id.usage', '=', 'internal'), ('quantity', '>', 0)],
            ['product_id', 'location_id', 'quantity'],
        )
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.REPORT_LIMIT,
            f'stock.quant report tardó {elapsed:.3f}s (límite {self.REPORT_LIMIT}s)',
        )

    def test_stock_move_line_report_under_5s(self):
        """La consulta del informe 'Historial de Movimientos' tarda menos de 5 s."""
        t0 = time.monotonic()
        self.env['stock.move.line'].search_read(
            [('state', '=', 'done')],
            ['product_id', 'location_id', 'location_dest_id', 'qty_done', 'date'],
            limit=1000,
        )
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.REPORT_LIMIT,
            f'stock.move.line report tardó {elapsed:.3f}s (límite {self.REPORT_LIMIT}s)',
        )

    def test_low_stock_report_under_5s(self):
        """La consulta de 'Alertas de Stock Mínimo' tarda menos de 5 s."""
        t0 = time.monotonic()
        self.env['product.template'].search_read(
            [('is_low_stock', '=', True)],
            ['name', 'qty_available', 'min_stock_level'],
        )
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.REPORT_LIMIT,
            f'Alerta stock mínimo report tardó {elapsed:.3f}s (límite {self.REPORT_LIMIT}s)',
        )

    def test_adjustment_history_report_under_5s(self):
        """La consulta del 'Histórico de Ajustes' tarda menos de 5 s."""
        t0 = time.monotonic()
        self.env['stock.inventory.adjustment'].search_read(
            [('state', '=', 'done')],
            ['name', 'date', 'adjustment_type', 'total_discrepancy'],
        )
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.REPORT_LIMIT,
            f'Adjustment history report tardó {elapsed:.3f}s (límite {self.REPORT_LIMIT}s)',
        )

    def test_product_brand_count_via_read_group_under_5s(self):
        """read_group para conteo de productos por marca tarda menos de 5 s."""
        t0 = time.monotonic()
        self.env['product.template'].read_group(
            domain=[],
            fields=['brand_id'],
            groupby=['brand_id'],
        )
        elapsed = time.monotonic() - t0
        self.assertLess(
            elapsed, self.REPORT_LIMIT,
            f'read_group brand count tardó {elapsed:.3f}s (límite {self.REPORT_LIMIT}s)',
        )
