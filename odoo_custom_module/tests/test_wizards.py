# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase
from odoo.exceptions import UserError


class TestStockInventoryWizard(TransactionCase):
    """Tests para stock.inventory.wizard (Ajuste Rápido)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reutiliza la ubicación de inventario virtual que Odoo crea al instalar stock
        cls.inventory_location = cls.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', '=', cls.env.company.id)],
            limit=1,
        )

        cls.location = cls.env['stock.location'].create({
            'name': 'Warehouse Loc Wizard Test',
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Wizard Test Product',
            'type': 'product',
        })

    def _make_wizard(self, current_qty=0.0, new_qty=10.0, **extra):
        vals = {
            'location_id': self.location.id,
            'product_id': self.product.id,
            'current_qty': current_qty,
            'new_qty': new_qty,
        }
        vals.update(extra)
        return self.env['stock.inventory.wizard'].create(vals)

    # ------------------------------------------------------------------
    # _compute_difference
    # ------------------------------------------------------------------

    def test_compute_difference_positive(self):
        """difference_qty = new_qty - current_qty cuando new > current."""
        wizard = self._make_wizard(current_qty=5.0, new_qty=10.0)
        self.assertAlmostEqual(wizard.difference_qty, 5.0)

    def test_compute_difference_negative(self):
        """difference_qty es negativo cuando new < current."""
        wizard = self._make_wizard(current_qty=10.0, new_qty=3.0)
        self.assertAlmostEqual(wizard.difference_qty, -7.0)

    def test_compute_difference_zero(self):
        """difference_qty es 0 cuando new == current."""
        wizard = self._make_wizard(current_qty=5.0, new_qty=5.0)
        self.assertAlmostEqual(wizard.difference_qty, 0.0)

    # ------------------------------------------------------------------
    # action_apply — caso error
    # ------------------------------------------------------------------

    def test_action_apply_zero_difference_raises_user_error(self):
        """action_apply lanza UserError si no hay diferencia."""
        wizard = self._make_wizard(current_qty=5.0, new_qty=5.0)
        with self.assertRaises(UserError):
            wizard.action_apply()

    # ------------------------------------------------------------------
    # action_apply — caso éxito
    # ------------------------------------------------------------------

    def test_action_apply_returns_stock_move_action(self):
        """action_apply retorna una acción de ventana apuntando a stock.move."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=10.0)
        result = wizard.action_apply()
        self.assertEqual(result.get('res_model'), 'stock.move')
        move = self.env['stock.move'].browse(result['res_id'])
        self.assertTrue(move.exists())
        self.assertIn(move.state, ('done', 'confirmed'))

    def test_action_apply_move_quantity_is_absolute_value(self):
        """El stock.move se crea con la cantidad absoluta de la diferencia."""
        wizard = self._make_wizard(current_qty=10.0, new_qty=3.0)
        result = wizard.action_apply()
        move = self.env['stock.move'].browse(result['res_id'])
        # Verificar la cantidad ordenada (product_uom_qty) que es siempre positiva
        self.assertAlmostEqual(move.product_uom_qty, 7.0)

    # ------------------------------------------------------------------
    # create_adjustment_record flag
    # ------------------------------------------------------------------

    def test_action_apply_creates_adjustment_when_flag_true(self):
        """Con create_adjustment_record=True se crea un ajuste en historial."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=8.0,
                                    create_adjustment_record=True)
        count_before = self.env['stock.inventory.adjustment'].search_count([])
        wizard.action_apply()
        count_after = self.env['stock.inventory.adjustment'].search_count([])
        self.assertGreater(count_after, count_before)

    def test_action_apply_no_adjustment_when_flag_false(self):
        """Con create_adjustment_record=False NO se crea ajuste."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=6.0,
                                    create_adjustment_record=False)
        count_before = self.env['stock.inventory.adjustment'].search_count([])
        wizard.action_apply()
        count_after = self.env['stock.inventory.adjustment'].search_count([])
        self.assertEqual(count_before, count_after)

    # ------------------------------------------------------------------
    # _create_adjustment_record
    # ------------------------------------------------------------------

    def test_create_adjustment_record_type_is_correction(self):
        """El ajuste creado por el wizard es de tipo 'correction'."""
        wizard = self._make_wizard(current_qty=2.0, new_qty=12.0)
        adj = wizard._create_adjustment_record()
        self.assertEqual(adj.adjustment_type, 'correction')

    def test_create_adjustment_record_creates_line(self):
        """_create_adjustment_record crea una línea con las cantidades correctas."""
        wizard = self._make_wizard(current_qty=5.0, new_qty=15.0)
        adj = wizard._create_adjustment_record()
        self.assertTrue(adj.line_ids, 'Debe existir al menos una línea')
        line = adj.line_ids[0]
        self.assertEqual(line.product_id, self.product)
        self.assertAlmostEqual(line.current_qty, 5.0)
        self.assertAlmostEqual(line.expected_qty, 15.0)

    def test_create_adjustment_record_state_is_in_progress(self):
        """El ajuste queda en estado in_progress tras _create_adjustment_record."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=10.0)
        adj = wizard._create_adjustment_record()
        self.assertEqual(adj.state, 'in_progress')

    def test_create_adjustment_record_with_reason(self):
        """El reason_id se transfiere al ajuste si se especifica."""
        reason = self.env['stock.inventory.adjustment.reason'].create({
            'name': 'Test Reason',
        })
        wizard = self._make_wizard(current_qty=0.0, new_qty=5.0,
                                    reason_id=reason.id)
        adj = wizard._create_adjustment_record()
        self.assertEqual(adj.reason_id, reason)

    # ------------------------------------------------------------------
    # _create_stock_move — dirección según signo
    # ------------------------------------------------------------------

    def test_create_stock_move_positive_diff_inventory_to_location(self):
        """Diferencia positiva: inventario → ubicación."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=5.0)
        move = wizard._create_stock_move()
        self.assertEqual(move.location_id, self.inventory_location)
        self.assertEqual(move.location_dest_id, self.location)

    def test_create_stock_move_negative_diff_location_to_inventory(self):
        """Diferencia negativa: ubicación → inventario."""
        wizard = self._make_wizard(current_qty=10.0, new_qty=3.0)
        move = wizard._create_stock_move()
        self.assertEqual(move.location_id, self.location)
        self.assertEqual(move.location_dest_id, self.inventory_location)

    def test_create_stock_move_is_created_with_correct_quantity(self):
        """_create_stock_move crea el movimiento con la cantidad correcta."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=4.0)
        move = wizard._create_stock_move()
        self.assertTrue(move.exists())
        self.assertAlmostEqual(move.product_uom_qty, 4.0)

    def test_get_inventory_location_returns_location(self):
        """_get_inventory_location retorna la ubicación de inventario de la compañía."""
        wizard = self._make_wizard(current_qty=0.0, new_qty=5.0)
        inv_loc = wizard._get_inventory_location()
        self.assertTrue(inv_loc.exists())
        self.assertEqual(inv_loc.usage, 'inventory')


class TestStockInventoryQuickCount(TransactionCase):
    """Tests para stock.inventory.quick.count (Conteo Rápido)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env['stock.location'].create({
            'name': 'Quick Count Test Location',
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Quick Count Test Product',
            'type': 'product',
        })

    def _make_wizard(self, **extra):
        vals = {'location_id': self.location.id}
        vals.update(extra)
        return self.env['stock.inventory.quick.count'].create(vals)

    def _make_wizard_with_lines(self, current_qty=10.0, counted_qty=7.0):
        """Crea wizard con una línea de conteo."""
        wizard = self._make_wizard()
        self.env['stock.inventory.quick.count.line'].create({
            'wizard_id': wizard.id,
            'product_id': self.product.id,
            'current_qty': current_qty,
            'counted_qty': counted_qty,
        })
        return wizard

    # ------------------------------------------------------------------
    # action_validate — sin diferencias
    # ------------------------------------------------------------------

    def test_action_validate_no_lines_returns_close(self):
        """Sin líneas de conteo, action_validate retorna close."""
        wizard = self._make_wizard()
        result = wizard.action_validate()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    def test_action_validate_all_same_returns_close(self):
        """Sin diferencias, action_validate retorna close sin crear ajuste."""
        wizard = self._make_wizard_with_lines(current_qty=5.0, counted_qty=5.0)
        result = wizard.action_validate()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    # ------------------------------------------------------------------
    # action_validate — con diferencias y create_adjustment=True
    # ------------------------------------------------------------------

    def test_action_validate_with_differences_creates_adjustment(self):
        """Con diferencias y create_adjustment=True, se crea y retorna un ajuste."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=7.0)
        count_before = self.env['stock.inventory.adjustment'].search_count([])
        result = wizard.action_validate()
        count_after = self.env['stock.inventory.adjustment'].search_count([])
        self.assertGreater(count_after, count_before)
        self.assertEqual(result.get('res_model'), 'stock.inventory.adjustment')

    def test_action_validate_adjustment_is_in_progress(self):
        """El ajuste creado por conteo rápido queda en estado in_progress."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=3.0)
        result = wizard.action_validate()
        adj = self.env['stock.inventory.adjustment'].browse(result['res_id'])
        self.assertEqual(adj.state, 'in_progress')

    # ------------------------------------------------------------------
    # action_validate — con diferencias y create_adjustment=False
    # ------------------------------------------------------------------

    def test_action_validate_differences_no_flag_returns_close(self):
        """Con diferencias pero create_adjustment=False retorna close."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=7.0)
        wizard.write({'create_adjustment': False})
        result = wizard.action_validate()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    def test_action_validate_differences_no_flag_no_adjustment_created(self):
        """Con create_adjustment=False no se crea ningún ajuste."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=7.0)
        wizard.write({'create_adjustment': False})
        count_before = self.env['stock.inventory.adjustment'].search_count([])
        wizard.action_validate()
        count_after = self.env['stock.inventory.adjustment'].search_count([])
        self.assertEqual(count_before, count_after)

    # ------------------------------------------------------------------
    # _create_adjustment
    # ------------------------------------------------------------------

    def test_create_adjustment_creates_line_for_each_diff(self):
        """_create_adjustment crea una línea por cada diferencia."""
        product2 = self.env['product.product'].create({
            'name': 'Quick Count Product 2',
            'type': 'product',
        })
        wizard = self._make_wizard()
        line1 = self.env['stock.inventory.quick.count.line'].create({
            'wizard_id': wizard.id,
            'product_id': self.product.id,
            'current_qty': 10.0,
            'counted_qty': 7.0,
        })
        line2 = self.env['stock.inventory.quick.count.line'].create({
            'wizard_id': wizard.id,
            'product_id': product2.id,
            'current_qty': 5.0,
            'counted_qty': 8.0,
        })
        lines_with_diff = wizard.line_ids.filtered(
            lambda l: l.counted_qty != l.current_qty
        )
        adj = wizard._create_adjustment(lines_with_diff)
        self.assertEqual(len(adj.line_ids), 2)

    def test_create_adjustment_type_is_cyclic(self):
        """El ajuste creado por conteo rápido es de tipo 'cyclic'."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=7.0)
        lines_with_diff = wizard.line_ids
        adj = wizard._create_adjustment(lines_with_diff)
        self.assertEqual(adj.adjustment_type, 'cyclic')

    def test_create_adjustment_line_quantities(self):
        """Las cantidades en la línea del ajuste reflejan el conteo."""
        wizard = self._make_wizard_with_lines(current_qty=10.0, counted_qty=7.0)
        lines_with_diff = wizard.line_ids
        adj = wizard._create_adjustment(lines_with_diff)
        line = adj.line_ids[0]
        self.assertAlmostEqual(line.current_qty, 10.0)
        self.assertAlmostEqual(line.expected_qty, 7.0)


class TestStockInventoryQuickCountLine(TransactionCase):
    """Tests para stock.inventory.quick.count.line."""

    def setUp(self):
        super().setUp()
        self.location = self.env['stock.location'].create({
            'name': 'Quick Count Line Test Location',
            'usage': 'internal',
        })
        self.product = self.env['product.product'].create({
            'name': 'Quick Count Line Test Product',
            'type': 'product',
        })
        self.wizard = self.env['stock.inventory.quick.count'].create({
            'location_id': self.location.id,
        })

    def _make_line(self, current_qty, counted_qty):
        return self.env['stock.inventory.quick.count.line'].create({
            'wizard_id': self.wizard.id,
            'product_id': self.product.id,
            'current_qty': current_qty,
            'counted_qty': counted_qty,
        })

    def test_difference_positive(self):
        """difference = counted - current cuando counted > current."""
        line = self._make_line(current_qty=5.0, counted_qty=10.0)
        self.assertAlmostEqual(line.difference, 5.0)

    def test_difference_negative(self):
        """difference es negativo cuando counted < current."""
        line = self._make_line(current_qty=10.0, counted_qty=4.0)
        self.assertAlmostEqual(line.difference, -6.0)

    def test_difference_zero(self):
        """difference es 0 cuando counted == current."""
        line = self._make_line(current_qty=7.0, counted_qty=7.0)
        self.assertAlmostEqual(line.difference, 0.0)

    def test_has_difference_true_when_not_zero(self):
        """has_difference es True cuando hay diferencia."""
        line = self._make_line(current_qty=5.0, counted_qty=8.0)
        self.assertTrue(line.has_difference)

    def test_has_difference_false_when_zero(self):
        """has_difference es False cuando no hay diferencia."""
        line = self._make_line(current_qty=5.0, counted_qty=5.0)
        self.assertFalse(line.has_difference)

    def test_has_difference_true_for_negative_difference(self):
        """has_difference es True también para diferencia negativa."""
        line = self._make_line(current_qty=10.0, counted_qty=3.0)
        self.assertTrue(line.has_difference)
