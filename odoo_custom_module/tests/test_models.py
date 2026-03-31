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

    def test_get_subcategories_returns_children(self):
        """Test que get_subcategories retorna todas las subcategorías correctamente."""
        root = self.Category.create({'name': 'Raíz'})
        child1 = self.Category.create({'name': 'Hijo 1', 'parent_id': root.id})
        child2 = self.Category.create({'name': 'Hijo 2', 'parent_id': root.id})
        self.Category.create({'name': 'Nieto 1', 'parent_id': child1.id})

        subcats = root.get_subcategories()
        self.assertIn(child1, subcats)
        self.assertIn(child2, subcats)

    def test_hierarchy_check_raises_on_circular_parent(self):
        """Odoo detecta jerarquías circulares al asignar parent_id."""
        parent = self.Category.create({'name': 'Padre Circ'})
        child = self.Category.create({'name': 'Hijo Circ', 'parent_id': parent.id})
        # _parent_store_update lanza UserError("Recursion Detected") durante la escritura
        raised = False
        try:
            parent.write({'parent_id': child.id})
        except Exception:
            raised = True
        self.assertTrue(raised, 'Debe lanzar excepción al crear jerarquía circular')

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

    def test_total_surplus_and_shortage(self):
        """total_surplus acumula excesos y total_shortage acumula faltantes."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        product2 = self.env['product.product'].create({
            'name': 'Product Surplus',
            'type': 'product',
        })
        location2 = self.env['stock.location'].create({
            'name': 'Location 2',
            'usage': 'internal',
        })
        # Línea con +5 (exceso)
        self.AdjustmentLine.create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 10.0,
            'expected_qty': 15.0,
        })
        # Línea con -3 (faltante)
        self.AdjustmentLine.create({
            'adjustment_id': adj.id,
            'product_id': product2.id,
            'location_id': location2.id,
            'current_qty': 8.0,
            'expected_qty': 5.0,
        })
        self.assertEqual(adj.total_surplus, 5.0)
        self.assertEqual(adj.total_shortage, 3.0)
        self.assertEqual(adj.total_discrepancy, 8.0)

    def test_total_surplus_and_shortage_zero_when_no_lines(self):
        """Sin líneas, los tres totales son 0."""
        adj = self.Adjustment.create({
            'location_ids': [(4, self.location.id)],
        })
        self.assertEqual(adj.total_surplus, 0.0)
        self.assertEqual(adj.total_shortage, 0.0)
        self.assertEqual(adj.total_discrepancy, 0.0)


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


class TestAdjustmentValidateIntegration(TransactionCase):
    """Tests de integración para action_validate — verifica creación de stock.move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reutiliza la ubicación de inventario virtual que Odoo crea al instalar stock
        cls.inventory_location = cls.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', '=', cls.env.company.id)],
            limit=1,
        )

        cls.location = cls.env['stock.location'].create({
            'name': 'Test Warehouse Location',
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Integration Test Product',
            'type': 'product',
        })

    def _make_adjustment_with_line(self, current_qty, expected_qty):
        adj = self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, self.location.id)],
        })
        self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': current_qty,
            'expected_qty': expected_qty,
        })
        return adj

    def test_validate_creates_stock_move_for_positive_difference(self):
        """Validar con diferencia positiva crea un stock.move y pasa el ajuste a done."""
        adj = self._make_adjustment_with_line(current_qty=0.0, expected_qty=10.0)
        adj.action_start()
        adj.action_validate()
        self.assertEqual(adj.state, 'done')
        self.assertTrue(adj.move_ids, 'Debe existir al menos un stock.move tras validar')

    def test_validate_creates_stock_move_for_negative_difference(self):
        """Validar con diferencia negativa (pérdida) crea un stock.move en estado done."""
        adj = self._make_adjustment_with_line(current_qty=10.0, expected_qty=5.0)
        adj.action_start()
        adj.action_validate()
        self.assertEqual(adj.state, 'done')
        self.assertTrue(adj.move_ids)

    def test_validate_raises_when_all_differences_are_zero(self):
        """Validar con todas las diferencias en cero lanza UserError."""
        from odoo.exceptions import UserError
        adj = self._make_adjustment_with_line(current_qty=5.0, expected_qty=5.0)
        adj.action_start()
        with self.assertRaises(UserError):
            adj.action_validate()
        self.assertFalse(adj.move_ids, 'No debe crear movimientos si la diferencia es cero')

    def test_is_low_stock_computed_correctly(self):
        """is_low_stock es True cuando qty_available < min_stock_level > 0."""
        product_tmpl = self.env['product.template'].create({
            'name': 'Low Stock Test',
            'type': 'product',
            'min_stock_level': 20.0,
        })
        # qty_available = 0 < min_stock_level = 20
        self.assertTrue(product_tmpl.is_low_stock)

    def test_is_low_stock_false_when_min_is_zero(self):
        """is_low_stock es False cuando min_stock_level = 0 (sin mínimo configurado)."""
        product_tmpl = self.env['product.template'].create({
            'name': 'No Min Stock',
            'type': 'product',
            'min_stock_level': 0.0,
        })
        self.assertFalse(product_tmpl.is_low_stock)


class TestStockInventoryAdjustmentReason(TransactionCase):
    """Tests para stock.inventory.adjustment.reason."""

    def setUp(self):
        super().setUp()
        self.Reason = self.env['stock.inventory.adjustment.reason']

    def test_reason_create(self):
        """Se puede crear una razón de ajuste."""
        reason = self.Reason.create({'name': 'Razón Test'})
        self.assertTrue(reason.id)
        self.assertEqual(reason.name, 'Razón Test')

    def test_reason_sequence_default(self):
        """La secuencia por defecto es 10."""
        reason = self.Reason.create({'name': 'Razón Secuencia'})
        self.assertEqual(reason.sequence, 10)

    def test_reason_active_default(self):
        """Las razones están activas por defecto."""
        reason = self.Reason.create({'name': 'Razón Activa'})
        self.assertTrue(reason.active)

    def test_reason_toggle_active(self):
        """Se puede desactivar y volver a activar una razón."""
        reason = self.Reason.create({'name': 'Razón Toggle'})
        reason.write({'active': False})
        self.assertFalse(reason.active)
        reason.write({'active': True})
        self.assertTrue(reason.active)

    def test_reason_description(self):
        """El campo description se guarda correctamente."""
        reason = self.Reason.create({
            'name': 'Razón Desc',
            'description': 'Descripción detallada de la razón',
        })
        self.assertEqual(reason.description, 'Descripción detallada de la razón')

    def test_reason_sequence_ordering(self):
        """Las razones se ordenan por secuencia."""
        r1 = self.Reason.create({'name': 'R1', 'sequence': 20})
        r2 = self.Reason.create({'name': 'R2', 'sequence': 5})
        reasons = self.Reason.search([('name', 'in', ['R1', 'R2'])])
        self.assertEqual(reasons[0], r2, 'La de menor secuencia debe aparecer primero')

    def test_reason_used_in_adjustment(self):
        """Una razón puede asignarse a un ajuste de inventario."""
        reason = self.Reason.create({'name': 'Razón Asignada'})
        location = self.env['stock.location'].create({
            'name': 'Reason Test Location',
            'usage': 'internal',
        })
        adj = self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, location.id)],
            'reason_id': reason.id,
        })
        self.assertEqual(adj.reason_id, reason)


class TestStockInventoryAdjustmentExtra(TransactionCase):
    """Tests adicionales para stock.inventory.adjustment — action_draft y generate_lines."""

    def setUp(self):
        super().setUp()
        self.location = self.env['stock.location'].create({
            'name': 'Extra Test Location',
            'usage': 'internal',
        })
        self.product = self.env['product.product'].create({
            'name': 'Extra Test Product',
            'type': 'product',
        })

    def _make_adj(self):
        return self.env['stock.inventory.adjustment'].create({
            'location_ids': [(4, self.location.id)],
        })

    def test_action_draft_returns_to_draft(self):
        """action_draft regresa el ajuste a estado borrador desde in_progress."""
        adj = self._make_adj()
        adj.action_start()
        self.assertEqual(adj.state, 'in_progress')
        adj.action_draft()
        self.assertEqual(adj.state, 'draft')

    def test_action_draft_from_cancel(self):
        """action_draft también funciona desde estado cancelado."""
        adj = self._make_adj()
        adj.action_cancel()
        self.assertEqual(adj.state, 'cancel')
        adj.action_draft()
        self.assertEqual(adj.state, 'draft')

    def test_generate_lines_in_non_draft_state_raises_error(self):
        """action_generate_lines lanza UserError si el estado no es draft."""
        from odoo.exceptions import UserError
        adj = self._make_adj()
        adj.action_start()
        with self.assertRaises(UserError):
            adj.action_generate_lines()

    def test_generate_lines_creates_lines_from_quants(self):
        """action_generate_lines genera líneas basadas en los quants reales."""
        # Crear un quant para que generate_lines encuentre algo
        quant = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 15.0,
        })
        adj = self._make_adj()
        adj.action_generate_lines()
        matching = adj.line_ids.filtered(
            lambda l: l.product_id == self.product and l.location_id == self.location
        )
        self.assertTrue(matching, 'Debe generarse una línea para el producto con quant')
        self.assertAlmostEqual(matching[0].current_qty, 15.0)
        self.assertAlmostEqual(matching[0].expected_qty, 15.0)

    def test_generate_lines_ignores_zero_quants(self):
        """action_generate_lines no crea líneas para quants con cantidad 0."""
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 0.0,
        })
        adj = self._make_adj()
        adj.action_generate_lines()
        matching = adj.line_ids.filtered(
            lambda l: l.product_id == self.product and l.location_id == self.location
        )
        self.assertFalse(matching, 'No debe generar líneas para quants con cantidad 0')

    def test_line_count_computed(self):
        """line_count refleja el número de líneas del ajuste."""
        adj = self._make_adj()
        self.assertEqual(adj.line_count, 0)
        product2 = self.env['product.product'].create({
            'name': 'Line Count Product',
            'type': 'product',
        })
        self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 0.0,
            'expected_qty': 5.0,
        })
        self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': adj.id,
            'product_id': product2.id,
            'location_id': self.location.id,
            'current_qty': 0.0,
            'expected_qty': 3.0,
        })
        self.assertEqual(adj.line_count, 2)

    def test_sql_constraint_prevents_duplicate_lines(self):
        """No puede haber dos líneas con mismo ajuste, producto y ubicación."""
        from psycopg2 import IntegrityError
        adj = self._make_adj()
        self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 0.0,
            'expected_qty': 5.0,
        })
        with self.assertRaises(Exception):  # IntegrityError o ValidationError según Odoo
            self.env['stock.inventory.adjustment.line'].create({
                'adjustment_id': adj.id,
                'product_id': self.product.id,
                'location_id': self.location.id,
                'current_qty': 0.0,
                'expected_qty': 8.0,
            })
            self.env.flush_all()

    def test_validate_all_zero_differences_raises_error(self):
        """action_validate lanza UserError cuando todas las diferencias son 0."""
        from odoo.exceptions import UserError
        adj = self._make_adj()
        self.env['stock.inventory.adjustment.line'].create({
            'adjustment_id': adj.id,
            'product_id': self.product.id,
            'location_id': self.location.id,
            'current_qty': 5.0,
            'expected_qty': 5.0,  # diferencia = 0
        })
        adj.action_start()
        with self.assertRaises(UserError):
            adj.action_validate()


class TestStockLocationExtra(TransactionCase):
    """Tests adicionales para stock.location — métodos y constraints extendidos."""

    def setUp(self):
        super().setUp()
        self.Location = self.env['stock.location']

    def test_get_child_locations_tree_no_children(self):
        """get_child_locations_tree retorna el nodo raíz sin hijos si no tiene."""
        loc = self.Location.create({
            'name': 'Leaf Location',
            'usage': 'internal',
        })
        tree = loc.get_child_locations_tree()
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['id'], loc.id)
        self.assertEqual(tree[0]['children'], [])

    def test_get_child_locations_tree_with_children(self):
        """get_child_locations_tree incluye los hijos correctamente."""
        parent = self.Location.create({
            'name': 'Parent Loc',
            'usage': 'view',
        })
        child = self.Location.create({
            'name': 'Child Loc',
            'usage': 'internal',
            'location_id': parent.id,
        })
        tree = parent.get_child_locations_tree()
        self.assertEqual(tree[0]['id'], parent.id)
        children_ids = [c['id'] for c in tree[0]['children']]
        self.assertIn(child.id, children_ids)

    def test_get_child_locations_tree_nested(self):
        """get_child_locations_tree es recursivo para ubicaciones anidadas."""
        root = self.Location.create({'name': 'Root', 'usage': 'view'})
        mid = self.Location.create({
            'name': 'Mid',
            'usage': 'view',
            'location_id': root.id,
        })
        leaf = self.Location.create({
            'name': 'Leaf',
            'usage': 'internal',
            'location_id': mid.id,
        })
        tree = root.get_child_locations_tree()
        # Nivel 1: mid
        self.assertEqual(len(tree[0]['children']), 1)
        mid_node = tree[0]['children'][0]
        self.assertEqual(mid_node['id'], mid.id)
        # Nivel 2: leaf
        self.assertEqual(len(mid_node['children']), 1)
        self.assertEqual(mid_node['children'][0]['id'], leaf.id)

    def test_get_locations_by_type(self):
        """get_locations_by_type retorna ubicaciones del tipo indicado."""
        shelf = self.Location.create({
            'name': 'Shelf Test',
            'usage': 'internal',
            'location_type': 'shelf',
        })
        rack = self.Location.create({
            'name': 'Rack Test',
            'usage': 'internal',
            'location_type': 'rack',
        })
        shelves = self.Location.get_locations_by_type('shelf')
        self.assertIn(shelf, shelves)
        self.assertNotIn(rack, shelves)

    def test_get_locations_by_type_only_internal(self):
        """get_locations_by_type solo retorna ubicaciones con usage='internal'."""
        view_loc = self.Location.create({
            'name': 'View Shelf',
            'usage': 'view',
            'location_type': 'zone',
        })
        result = self.Location.get_locations_by_type('zone')
        self.assertNotIn(view_loc, result)

    def test_location_type_warehouse_constraint_violation(self):
        """Una ubicación tipo 'warehouse' con usage distinto de internal/view lanza error."""
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.Location.create({
                'name': 'Bad Warehouse',
                'usage': 'customer',
                'location_type': 'warehouse',
            })

    def test_location_type_warehouse_allowed_usage_internal(self):
        """Una ubicación tipo 'warehouse' con usage='internal' es válida."""
        loc = self.Location.create({
            'name': 'Valid Warehouse',
            'usage': 'internal',
            'location_type': 'warehouse',
        })
        self.assertTrue(loc.id)

    def test_responsible_id_assignment(self):
        """El campo responsible_id se asigna y recupera correctamente."""
        user = self.env.user
        loc = self.Location.create({
            'name': 'Responsible Loc',
            'usage': 'internal',
            'responsible_id': user.id,
        })
        self.assertEqual(loc.responsible_id, user)

    def test_current_capacity_computed_from_quants(self):
        """current_capacity suma las cantidades de los quants en la ubicación."""
        loc = self.Location.create({'name': 'Cap Loc', 'usage': 'internal'})
        product = self.env['product.product'].create({
            'name': 'Cap Product',
            'type': 'product',
        })
        self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': loc.id,
            'quantity': 30.0,
        })
        self.assertAlmostEqual(loc.current_capacity, 30.0)

    def test_capacity_usage_percent_zero_when_no_max(self):
        """capacity_usage_percent es 0 cuando max_capacity=0."""
        loc = self.Location.create({
            'name': 'No Max Loc',
            'usage': 'internal',
            'max_capacity': 0.0,
        })
        self.assertAlmostEqual(loc.capacity_usage_percent, 0.0)

    def test_capacity_usage_percent_computed(self):
        """capacity_usage_percent = (current/max)*100."""
        loc = self.Location.create({
            'name': 'Percent Loc',
            'usage': 'internal',
            'max_capacity': 100.0,
        })
        product = self.env['product.product'].create({
            'name': 'Percent Product',
            'type': 'product',
        })
        self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': loc.id,
            'quantity': 50.0,
        })
        self.assertAlmostEqual(loc.capacity_usage_percent, 50.0)


class TestProductBrandExtra(TransactionCase):
    """Tests adicionales para product.brand — product_count con productos reales."""

    def test_product_count_with_multiple_products(self):
        """product_count se incrementa al asignar productos a la marca."""
        brand = self.env['product.brand'].create({'name': 'Marca Multi'})
        self.assertEqual(brand.product_count, 0)

        self.env['product.template'].create({
            'name': 'Producto A',
            'type': 'product',
            'brand_id': brand.id,
        })
        self.env['product.template'].create({
            'name': 'Producto B',
            'type': 'product',
            'brand_id': brand.id,
        })
        brand.invalidate_recordset()
        self.assertEqual(brand.product_count, 2)

    def test_product_count_decreases_when_brand_removed(self):
        """product_count disminuye al quitar la marca de un producto."""
        brand = self.env['product.brand'].create({'name': 'Marca Quitar'})
        product = self.env['product.template'].create({
            'name': 'Producto Quitar',
            'type': 'product',
            'brand_id': brand.id,
        })
        brand.invalidate_recordset()
        self.assertEqual(brand.product_count, 1)
        product.write({'brand_id': False})
        brand.invalidate_recordset()
        self.assertEqual(brand.product_count, 0)

    def test_brand_active_toggle_hides_from_default_search(self):
        """Una marca inactiva no aparece en búsquedas por defecto."""
        brand = self.env['product.brand'].create({'name': 'Marca Inactiva'})
        brand.write({'active': False})
        results = self.env['product.brand'].search([('name', '=', 'Marca Inactiva')])
        self.assertFalse(results, 'Marca inactiva no debe aparecer en búsqueda por defecto')
        results_all = self.env['product.brand'].with_context(active_test=False).search(
            [('name', '=', 'Marca Inactiva')]
        )
        self.assertTrue(results_all, 'Debe encontrarse con active_test=False')


class TestStockQuantExtra(TransactionCase):
    """Tests para la extensión de stock.quant — campo lot_name."""

    def test_lot_name_related_to_lot(self):
        """lot_name es el nombre del lote del quant cuando tiene lote."""
        location = self.env['stock.location'].create({
            'name': 'Quant Lot Location',
            'usage': 'internal',
        })
        product = self.env['product.product'].create({
            'name': 'Lot Product',
            'type': 'product',
            'tracking': 'lot',
        })
        lot = self.env['stock.lot'].create({
            'name': 'LOT-001',
            'product_id': product.id,
        })
        quant = self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': location.id,
            'lot_id': lot.id,
            'quantity': 5.0,
        })
        self.assertEqual(quant.lot_name, 'LOT-001')

    def test_lot_name_empty_without_lot(self):
        """lot_name es False/vacío cuando el quant no tiene lote."""
        location = self.env['stock.location'].create({
            'name': 'Quant No Lot Location',
            'usage': 'internal',
        })
        product = self.env['product.product'].create({
            'name': 'No Lot Product',
            'type': 'product',
        })
        quant = self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': location.id,
            'quantity': 3.0,
        })
        self.assertFalse(quant.lot_name)
