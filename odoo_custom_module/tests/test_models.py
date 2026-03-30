# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestProductBrand(TransactionCase):
    """Tests para el modelo product.brand"""

    def setUp(self):
        super(TestProductBrand, self).setUp()
        self.Brand = self.env['product.brand']

    def test_brand_create(self):
        """Test crear una marca de producto"""
        brand = self.Brand.create({
            'name': 'Marca Test',
            'description': 'Descripción de prueba',
        })
        self.assertTrue(brand.id)
        self.assertEqual(brand.name, 'Marca Test')
        self.assertTrue(brand.active)

    def test_brand_name_get(self):
        """Test que name_get retorna formato correcto"""
        brand = self.Brand.create({'name': 'Marca Test'})
        result = brand.name_get()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], 'Marca Test')

    def test_brand_product_count(self):
        """Test que product_count se calcula correctamente"""
        brand = self.Brand.create({'name': 'Marca Test'})
        self.assertEqual(brand.product_count, 0)


class TestProductTemplate(TransactionCase):
    """Tests para la extensión de product.template"""

    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.ProductTemplate = self.env['product.template']
        self.Brand = self.env['product.brand']
        self.ProductProduct = self.env['product.product']

    def test_product_with_brand(self):
        """Test crear producto con marca"""
        brand = self.Brand.create({'name': 'Marca Test'})
        product = self.ProductTemplate.create({
            'name': 'Producto Test',
            'type': 'product',
            'brand_id': brand.id,
        })
        self.assertEqual(product.brand_id, brand)

    def test_stock_levels_validation(self):
        """Test que min_stock no puede ser mayor que max_stock"""
        with self.assertRaises(ValidationError):
            self.ProductTemplate.create({
                'name': 'Producto Test',
                'type': 'product',
                'min_stock_level': 100,
                'max_stock_level': 50,
            })

    def test_manufacturer_ref(self):
        """Test referencia de fabricante"""
        product = self.ProductTemplate.create({
            'name': 'Producto Test',
            'type': 'product',
            'manufacturer_ref': 'REF-12345',
        })
        self.assertEqual(product.manufacturer_ref, 'REF-12345')


class TestStockLocation(TransactionCase):
    """Tests para la extensión de stock.location"""

    def setUp(self):
        super(TestStockLocation, self).setUp()
        self.Location = self.env['stock.location']

    def test_location_type_selection(self):
        """Test crear ubicación con tipo"""
        location = self.Location.create({
            'name': 'Ubicación Test',
            'usage': 'internal',
            'location_type': 'zone',
        })
        self.assertEqual(location.location_type, 'zone')

    def test_capacity_fields(self):
        """Test campos de capacidad"""
        location = self.Location.create({
            'name': 'Ubicación Test',
            'usage': 'internal',
            'max_capacity': 1000,
        })
        self.assertEqual(location.max_capacity, 1000)
        self.assertGreaterEqual(location.capacity_usage_percent, 0)

    def test_usage_class_selection(self):
        """Test clase de almacenamiento"""
        location = self.Location.create({
            'name': 'Ubicación Test',
            'usage': 'internal',
            'usage_class': 'cold',
            'temperature_range': '2-8°C',
        })
        self.assertEqual(location.usage_class, 'cold')
        self.assertEqual(location.temperature_range, '2-8°C')

    def test_barcode(self):
        """Test código de barras"""
        location = self.Location.create({
            'name': 'Ubicación Test',
            'usage': 'internal',
            'barcode': '1234567890123',
        })
        self.assertEqual(location.barcode, '1234567890123')


class TestProductCategory(TransactionCase):
    """Tests para la extensión de product.category"""

    def setUp(self):
        super(TestProductCategory, self).setUp()
        self.Category = self.env['product.category']

    def test_category_code(self):
        """Test código de categoría"""
        category = self.Category.create({
            'name': 'Categoría Test',
            'code': 'CAT-TEST',
            'description': 'Descripción de prueba',
        })
        self.assertEqual(category.code, 'CAT-TEST')

    def test_category_name_create(self):
        """Test name_create"""
        result = self.Category.name_create('Nueva Categoría')
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_hierarchy_check(self):
        """Test que no permite jerarquía circular"""
        parent = self.Category.create({'name': 'Padre'})
        child = self.Category.create({
            'name': 'Hijo',
            'parent_id': parent.id,
        })
        parent.parent_id = child.id
        with self.assertRaises(ValidationError):
            parent._check_hierarchy()

    def test_get_subcategories_uses_child_ids(self):
        """Test que get_subcategories retorna todas las subcategorías correctamente."""
        root = self.Category.create({'name': 'Raíz'})
        child1 = self.Category.create({'name': 'Hijo 1', 'parent_id': root.id})
        child2 = self.Category.create({'name': 'Hijo 2', 'parent_id': root.id})
        self.Category.create({'name': 'Nieto 1', 'parent_id': child1.id})

        subcats = root.get_subcategories()
        self.assertIn(child1, subcats)
        self.assertIn(child2, subcats)

    def test_get_full_path(self):
        """Test que get_full_path retorna la ruta completa."""
        root = self.Category.create({'name': 'Raíz'})
        child = self.Category.create({'name': 'Hijo', 'parent_id': root.id})
        self.assertEqual(child.get_full_path(), 'Raíz / Hijo')


class TestStockInventoryAdjustment(TransactionCase):
    """Tests para stock.inventory.adjustment"""

    def setUp(self):
        super().setUp()
        self.Adjustment = self.env['stock.inventory.adjustment']
        self.AdjustmentLine = self.env['stock.inventory.adjustment.line']
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })

    def test_adjustment_create_sequence(self):
        """Test que se asigna secuencia automáticamente."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        self.assertNotEqual(adj.name, 'New')
        self.assertTrue(adj.name.startswith('ADJ/'))

    def test_adjustment_default_state_is_draft(self):
        """Test que el estado inicial es borrador."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        self.assertEqual(adj.state, 'draft')

    def test_adjustment_state_flow_to_in_progress(self):
        """Test transición de estados draft → in_progress."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        adj.action_start()
        self.assertEqual(adj.state, 'in_progress')

    def test_adjustment_cancel(self):
        """Test cancelación de ajuste."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        adj.action_cancel()
        self.assertEqual(adj.state, 'cancel')

    def test_total_discrepancy_uses_absolute_values(self):
        """Test que total_discrepancy suma valores absolutos (no con signo)."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'type': 'product',
        })
        location2 = self.env['stock.location'].create({
            'name': 'Test Location 2',
            'usage': 'internal',
        })
        # Línea con diferencia -3 (pérdida)
        self.AdjustmentLine.create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 10.0,
            'expected_qty': 7.0,
        })
        # Línea con diferencia +3 (exceso)
        self.AdjustmentLine.create({
            'adjustment_id': adj.id,
            'product_id': product2.id,
            'location_id': location2.id,
            'current_qty': 5.0,
            'expected_qty': 8.0,
        })
        # Con abs(): 3 + 3 = 6. Sin abs(): -3 + 3 = 0
        self.assertEqual(adj.total_discrepancy, 6.0)

    def test_generate_lines_no_duplicates_on_repeated_calls(self):
        """Test que generate_lines limpia líneas previas y no genera duplicados."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        adj.action_generate_lines()
        first_count = len(adj.line_ids)
        adj.action_generate_lines()
        second_count = len(adj.line_ids)
        self.assertEqual(first_count, second_count,
                         'generate_lines debe limpiar líneas previas antes de regenerar')

    def test_generate_lines_without_location_raises_error(self):
        """Test que generar líneas sin ubicación lanza UserError."""
        from odoo.exceptions import UserError
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        adj.location_ids = False
        with self.assertRaises(UserError):
            adj.action_generate_lines()

    def test_validate_without_lines_raises_error(self):
        """Test que validar sin líneas lanza UserError."""
        from odoo.exceptions import UserError
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        adj.action_start()
        with self.assertRaises(UserError):
            adj.action_validate()


class TestStockOperations(TransactionCase):
    """Tests de integración para RF3 (Recepciones), RF4 (Entregas) y RF6 (Traslados)."""

    def setUp(self):
        super().setUp()
        self.Action = self.env['ir.actions.act_window']

    def _get_action(self, xml_id):
        """Devuelve la acción por XML ID completo."""
        module, name = xml_id.split('.')
        return self.env.ref(xml_id)

    def test_action_receipts_domain(self):
        """La acción de recepciones filtra solo pickings de tipo incoming."""
        action = self._get_action('inventory_custom.action_custom_receipts')
        self.assertIn("'incoming'", action.domain)

    def test_action_deliveries_domain(self):
        """La acción de entregas filtra solo pickings de tipo outgoing."""
        action = self._get_action('inventory_custom.action_custom_deliveries')
        self.assertIn("'outgoing'", action.domain)

    def test_action_internal_transfers_domain(self):
        """La acción de traslados filtra solo pickings de tipo internal."""
        action = self._get_action('inventory_custom.action_custom_internal_transfers')
        self.assertIn("'internal'", action.domain)

    def test_actions_target_stock_picking(self):
        """Todas las acciones de operaciones apuntan al modelo stock.picking."""
        for xml_id in [
            'inventory_custom.action_custom_receipts',
            'inventory_custom.action_custom_deliveries',
            'inventory_custom.action_custom_internal_transfers',
        ]:
            action = self._get_action(xml_id)
            self.assertEqual(action.res_model, 'stock.picking',
                             f'{xml_id} debe apuntar a stock.picking')

    def test_low_stock_report_action(self):
        """La acción de alertas de stock mínimo apunta a product.template."""
        action = self._get_action('inventory_custom.action_report_low_stock')
        self.assertEqual(action.res_model, 'product.template')

    def test_stock_by_location_report_action(self):
        """La acción de stock por ubicación apunta a stock.quant."""
        action = self._get_action('inventory_custom.action_report_stock_by_location')
        self.assertEqual(action.res_model, 'stock.quant')

    def test_stock_moves_report_action(self):
        """La acción de historial de movimientos apunta a stock.move.line."""
        action = self._get_action('inventory_custom.action_report_stock_moves')
        self.assertEqual(action.res_model, 'stock.move.line')

    def test_action_check_low_stock_no_error_when_empty(self):
        """action_check_low_stock no falla cuando no hay productos con mínimo configurado."""
        try:
            self.env['product.template'].action_check_low_stock()
        except Exception as e:
            self.fail(f'action_check_low_stock lanzó excepción inesperada: {e}')

    def test_action_check_low_stock_notifies_below_minimum(self):
        """action_check_low_stock publica mensaje en productos con stock bajo el mínimo."""
        product = self.env['product.template'].create({
            'name': 'Producto Bajo Mínimo',
            'type': 'product',
            'min_stock_level': 10.0,
        })
        # qty_available = 0 < min_stock_level = 10 → debe notificar
        initial_message_count = len(product.message_ids)
        self.env['product.template'].action_check_low_stock()
        self.assertGreater(
            len(product.message_ids), initial_message_count,
            'Debe publicar un mensaje en el chatter del producto bajo mínimo',
        )

    def test_action_check_low_stock_no_notification_above_minimum(self):
        """action_check_low_stock no notifica productos con stock igual o mayor al mínimo."""
        # Producto sin stock bajo mínimo (min=0 → se ignora)
        product = self.env['product.template'].create({
            'name': 'Producto Normal',
            'type': 'product',
            'min_stock_level': 0.0,
        })
        initial_message_count = len(product.message_ids)
        self.env['product.template'].action_check_low_stock()
        self.assertEqual(
            len(product.message_ids), initial_message_count,
            'No debe publicar mensajes en productos sin mínimo configurado',
        )


class TestStockInventoryAdjustmentLine(TransactionCase):
    """Tests para stock.inventory.adjustment.line"""

    def setUp(self):
        super().setUp()
        self.location = self.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        self.adj = self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, self.location.id)],
        })

    def test_difference_qty_positive(self):
        """Test que difference_qty = expected - current cuando expected > current."""
        line = self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': self.adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 10.0,
            'expected_qty': 15.0,
        })
        self.assertEqual(line.difference_qty, 5.0)

    def test_difference_qty_negative(self):
        """Test diferencia negativa cuando expected < current."""
        line = self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': self.adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 20.0,
            'expected_qty': 10.0,
        })
        self.assertEqual(line.difference_qty, -10.0)

    def test_difference_qty_zero(self):
        """Test diferencia cero cuando expected == current."""
        line = self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': self.adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 5.0,
            'expected_qty': 5.0,
        })
        self.assertEqual(line.difference_qty, 0.0)
