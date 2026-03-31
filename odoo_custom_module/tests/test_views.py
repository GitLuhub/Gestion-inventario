# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase
from lxml import etree


class TestViewsXPath(TransactionCase):
    """Tests para validar XPath de vistas"""

    def test_product_template_view_exists(self):
        """Test que la vista de producto existe"""
        view = self.env.ref('inventory_custom.view_product_template_form_inventory')
        self.assertTrue(view)
        self.assertEqual(view.model, 'product.template')

    def test_product_brand_view_exists(self):
        """Test que la vista de marca existe"""
        view = self.env.ref('inventory_custom.view_product_brand_form')
        self.assertTrue(view)
        self.assertEqual(view.model, 'product.brand')

    def test_stock_location_view_exists(self):
        """Test que la vista de ubicación existe"""
        view = self.env.ref('inventory_custom.view_stock_location_form_inventory')
        self.assertTrue(view)
        self.assertEqual(view.model, 'stock.location')

    def test_view_arch_valid_xml(self):
        """Test que el arch de vistas es XML válido"""
        views = [
            'inventory_custom.view_product_template_form_inventory',
            'inventory_custom.view_product_brand_form',
            'inventory_custom.view_product_brand_tree',
            'inventory_custom.view_stock_location_form_inventory',
        ]
        
        for xml_id in views:
            view = self.env.ref(xml_id)
            self.assertTrue(view.arch)
            try:
                etree.fromstring(view.arch.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                self.fail(f"Vista {xml_id} tiene XML inválido: {e}")

    def test_view_inherits_parent(self):
        """Test que las vistas heredan de las vistas padre correctas"""
        product_view = self.env.ref('inventory_custom.view_product_template_form_inventory')
        self.assertEqual(
            product_view.inherit_id.xml_id,
            'product.product_template_form_view'
        )

        location_view = self.env.ref('inventory_custom.view_stock_location_form_inventory')
        self.assertEqual(
            location_view.inherit_id.xml_id,
            'stock.view_location_form'
        )


class TestMenusAndActions(TransactionCase):
    """Tests para validar menús y acciones"""

    def test_action_product_brand(self):
        """Test acción de marcas de producto"""
        action = self.env.ref('inventory_custom.action_product_brand')
        self.assertTrue(action)
        self.assertEqual(action.res_model, 'product.brand')
        self.assertIn('tree', action.view_mode)
        self.assertIn('form', action.view_mode)

    def test_action_stock_location_type(self):
        """Test acción de ubicaciones por tipo"""
        action = self.env.ref('inventory_custom.action_stock_location_type')
        self.assertTrue(action)
        self.assertEqual(action.res_model, 'stock.location')
        self.assertIn('tree', action.view_mode)

    def test_menu_inventory_root(self):
        """Test menú raíz de inventario"""
        menu = self.env.ref('inventory_custom.menu_inventory_custom_root')
        self.assertTrue(menu)
        self.assertEqual(menu.name, 'Inventario Avanzado')

    def test_menu_hierarchy(self):
        """Test jerarquía de menús — verifica un submenú conocido apunta al root."""
        root = self.env.ref('inventory_custom.menu_inventory_custom_root')
        products_menu = self.env.ref('inventory_custom.menu_inventory_custom_products')
        self.assertEqual(products_menu.parent_id, root,
                         'El menú Productos debe ser hijo del menú raíz')


class TestAllMenusExist(TransactionCase):
    """Verifica que los 23 menús del módulo existen y tienen la jerarquía correcta."""

    def _menu(self, xml_id):
        return self.env.ref(f'inventory_custom.{xml_id}')

    def test_root_menu(self):
        menu = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.name, 'Inventario Avanzado')
        self.assertFalse(menu.parent_id)

    # ------------------------------------------------------------------
    # Submenús de primer nivel (hijos del root)
    # ------------------------------------------------------------------

    def test_menu_productos_parent(self):
        menu = self._menu('menu_inventory_custom_products')
        root = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.parent_id, root)
        self.assertEqual(menu.name, 'Productos')

    def test_menu_ubicaciones_parent(self):
        menu = self._menu('menu_inventory_custom_locations')
        root = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.parent_id, root)
        self.assertEqual(menu.name, 'Ubicaciones')

    def test_menu_operaciones_parent(self):
        menu = self._menu('menu_inventory_custom_operations')
        root = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.parent_id, root)
        self.assertEqual(menu.name, 'Operaciones')

    def test_menu_informes_parent(self):
        menu = self._menu('menu_inventory_custom_reports')
        root = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.parent_id, root)
        self.assertEqual(menu.name, 'Informes')

    def test_menu_configuracion_parent(self):
        menu = self._menu('menu_inventory_custom_configuration')
        root = self._menu('menu_inventory_custom_root')
        self.assertEqual(menu.parent_id, root)
        self.assertEqual(menu.name, 'Configuración')

    # ------------------------------------------------------------------
    # Submenús de Productos
    # ------------------------------------------------------------------

    def test_menu_todos_productos(self):
        menu = self._menu('menu_custom_product_list')
        parent = self._menu('menu_inventory_custom_products')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Todos los Productos')

    def test_menu_categorias(self):
        menu = self._menu('menu_custom_product_categories')
        parent = self._menu('menu_inventory_custom_products')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Categorías')

    def test_menu_marcas(self):
        menu = self._menu('menu_product_brand')
        parent = self._menu('menu_inventory_custom_products')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Marcas')

    # ------------------------------------------------------------------
    # Submenús de Ubicaciones
    # ------------------------------------------------------------------

    def test_menu_todas_ubicaciones(self):
        menu = self._menu('menu_custom_locations_all')
        parent = self._menu('menu_inventory_custom_locations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Todas las Ubicaciones')

    def test_menu_almacenes(self):
        menu = self._menu('menu_custom_warehouses')
        parent = self._menu('menu_inventory_custom_locations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Almacenes')

    def test_menu_por_tipo(self):
        menu = self._menu('menu_stock_location_type')
        parent = self._menu('menu_inventory_custom_locations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Por Tipo')

    # ------------------------------------------------------------------
    # Submenús de Operaciones
    # ------------------------------------------------------------------

    def test_menu_ajustes_inventario(self):
        menu = self._menu('menu_inventory_custom_adjustments_list')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Ajustes de Inventario')

    def test_menu_ajuste_rapido(self):
        menu = self._menu('menu_inventory_custom_quick_adjust')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Ajuste Rápido')

    def test_menu_conteo_rapido(self):
        menu = self._menu('menu_inventory_custom_quick_count')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Conteo Rápido')

    def test_menu_recepciones(self):
        menu = self._menu('menu_custom_receipts')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Recepciones')

    def test_menu_entregas(self):
        menu = self._menu('menu_custom_deliveries')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Entregas')

    def test_menu_traslados_internos(self):
        menu = self._menu('menu_custom_internal_transfers')
        parent = self._menu('menu_inventory_custom_operations')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Traslados Internos')

    # ------------------------------------------------------------------
    # Submenús de Informes
    # ------------------------------------------------------------------

    def test_menu_stock_por_ubicacion(self):
        menu = self._menu('menu_report_stock_location')
        parent = self._menu('menu_inventory_custom_reports')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Stock por Ubicación')

    def test_menu_historial_movimientos(self):
        menu = self._menu('menu_report_stock_moves')
        parent = self._menu('menu_inventory_custom_reports')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Historial de Movimientos')

    def test_menu_alertas_stock_minimo(self):
        menu = self._menu('menu_report_low_stock')
        parent = self._menu('menu_inventory_custom_reports')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Alertas de Stock Mínimo')

    def test_menu_historico_ajustes(self):
        menu = self._menu('menu_report_adjustments_history')
        parent = self._menu('menu_inventory_custom_reports')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Histórico de Ajustes')

    # ------------------------------------------------------------------
    # Submenús de Configuración
    # ------------------------------------------------------------------

    def test_menu_razones_ajuste(self):
        menu = self._menu('menu_inventory_custom_reasons')
        parent = self._menu('menu_inventory_custom_configuration')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.name, 'Razones de Ajuste')

    # ------------------------------------------------------------------
    # Verificar que cada menú tiene una acción asignada (o hijos)
    # ------------------------------------------------------------------

    def test_leaf_menus_have_actions(self):
        """Todos los menús hoja tienen una acción asignada."""
        leaf_xml_ids = [
            'menu_custom_product_list',
            'menu_custom_product_categories',
            'menu_product_brand',
            'menu_custom_locations_all',
            'menu_custom_warehouses',
            'menu_stock_location_type',
            'menu_inventory_custom_adjustments_list',
            'menu_inventory_custom_quick_adjust',
            'menu_inventory_custom_quick_count',
            'menu_custom_receipts',
            'menu_custom_deliveries',
            'menu_custom_internal_transfers',
            'menu_report_stock_location',
            'menu_report_stock_moves',
            'menu_report_low_stock',
            'menu_report_adjustments_history',
            'menu_inventory_custom_reasons',
        ]
        for xml_id in leaf_xml_ids:
            menu = self._menu(xml_id)
            self.assertTrue(
                menu.action,
                f'El menú {xml_id} no tiene acción asignada',
            )


class TestAllActionsCorrect(TransactionCase):
    """Verifica que todas las acciones apuntan al modelo y vista correctos."""

    def _action(self, xml_id):
        return self.env.ref(f'inventory_custom.{xml_id}')

    # ------------------------------------------------------------------
    # Marcas
    # ------------------------------------------------------------------

    def test_action_product_brand_model(self):
        action = self._action('action_product_brand')
        self.assertEqual(action.res_model, 'product.brand')

    def test_action_product_brand_view_mode(self):
        action = self._action('action_product_brand')
        self.assertIn('tree', action.view_mode)
        self.assertIn('form', action.view_mode)

    # ------------------------------------------------------------------
    # Ubicaciones
    # ------------------------------------------------------------------

    def test_action_stock_location_type_model(self):
        action = self._action('action_stock_location_type')
        self.assertEqual(action.res_model, 'stock.location')

    # ------------------------------------------------------------------
    # Ajustes de Inventario
    # ------------------------------------------------------------------

    def test_action_adjustment_model(self):
        action = self._action('action_stock_inventory_adjustment')
        self.assertEqual(action.res_model, 'stock.inventory.adjustment')

    def test_action_adjustment_view_mode(self):
        action = self._action('action_stock_inventory_adjustment')
        self.assertIn('tree', action.view_mode)
        self.assertIn('form', action.view_mode)

    # ------------------------------------------------------------------
    # Wizard de ajuste rápido
    # ------------------------------------------------------------------

    def test_action_wizard_model(self):
        action = self._action('action_stock_inventory_wizard')
        self.assertEqual(action.res_model, 'stock.inventory.wizard')

    def test_action_wizard_target_new(self):
        action = self._action('action_stock_inventory_wizard')
        self.assertEqual(action.target, 'new')

    # ------------------------------------------------------------------
    # Wizard de conteo rápido
    # ------------------------------------------------------------------

    def test_action_quick_count_model(self):
        action = self._action('action_stock_inventory_quick_count')
        self.assertEqual(action.res_model, 'stock.inventory.quick.count')

    def test_action_quick_count_target_new(self):
        action = self._action('action_stock_inventory_quick_count')
        self.assertEqual(action.target, 'new')

    # ------------------------------------------------------------------
    # Razones de ajuste
    # ------------------------------------------------------------------

    def test_action_adjustment_reason_model(self):
        action = self._action('action_stock_inventory_adjustment_reason')
        self.assertEqual(action.res_model, 'stock.inventory.adjustment.reason')

    def test_action_adjustment_reason_view_mode(self):
        action = self._action('action_stock_inventory_adjustment_reason')
        self.assertIn('tree', action.view_mode)

    # ------------------------------------------------------------------
    # Informes
    # ------------------------------------------------------------------

    def test_action_report_stock_by_location_model(self):
        action = self._action('action_report_stock_by_location')
        self.assertEqual(action.res_model, 'stock.quant')

    def test_action_report_stock_moves_model(self):
        action = self._action('action_report_stock_moves')
        self.assertEqual(action.res_model, 'stock.move.line')

    def test_action_report_low_stock_model(self):
        action = self._action('action_report_low_stock')
        self.assertEqual(action.res_model, 'product.template')

    def test_action_report_low_stock_domain_uses_is_low_stock(self):
        """El informe de stock mínimo usa el campo is_low_stock (no qty_available fijo)."""
        action = self._action('action_report_low_stock')
        self.assertIn('is_low_stock', action.domain)

    def test_action_report_adjustments_history_model(self):
        action = self._action('action_report_adjustments_history')
        self.assertEqual(action.res_model, 'stock.inventory.adjustment')

    # ------------------------------------------------------------------
    # Operaciones de almacén
    # ------------------------------------------------------------------

    def test_action_receipts_model(self):
        action = self._action('action_custom_receipts')
        self.assertEqual(action.res_model, 'stock.picking')

    def test_action_deliveries_model(self):
        action = self._action('action_custom_deliveries')
        self.assertEqual(action.res_model, 'stock.picking')

    def test_action_internal_transfers_model(self):
        action = self._action('action_custom_internal_transfers')
        self.assertEqual(action.res_model, 'stock.picking')


class TestViewsComplete(TransactionCase):
    """Verifica que todas las vistas del módulo existen y son XML válido."""

    def _view(self, xml_id):
        return self.env.ref(f'inventory_custom.{xml_id}')

    def test_adjustment_tree_view(self):
        view = self._view('view_stock_inventory_adjustment_tree')
        self.assertEqual(view.model, 'stock.inventory.adjustment')
        self.assertEqual(view.type, 'tree')

    def test_adjustment_form_view(self):
        view = self._view('view_stock_inventory_adjustment_form')
        self.assertEqual(view.model, 'stock.inventory.adjustment')
        self.assertEqual(view.type, 'form')

    def test_adjustment_search_view(self):
        view = self._view('view_stock_inventory_adjustment_search')
        self.assertEqual(view.model, 'stock.inventory.adjustment')
        self.assertEqual(view.type, 'search')

    def test_wizard_form_view(self):
        view = self._view('view_stock_inventory_wizard_form')
        self.assertEqual(view.model, 'stock.inventory.wizard')
        self.assertEqual(view.type, 'form')

    def test_quick_count_form_view(self):
        view = self._view('view_stock_inventory_quick_count_form')
        self.assertEqual(view.model, 'stock.inventory.quick.count')
        self.assertEqual(view.type, 'form')

    def test_adjustment_reason_tree_view(self):
        view = self._view('view_stock_inventory_adjustment_reason_tree')
        self.assertEqual(view.model, 'stock.inventory.adjustment.reason')
        self.assertEqual(view.type, 'tree')

    def test_adjustment_form_contains_state_buttons(self):
        """El formulario de ajuste contiene botones de workflow."""
        view = self._view('view_stock_inventory_adjustment_form')
        self.assertIn('action_start', view.arch)
        self.assertIn('action_validate', view.arch)
        self.assertIn('action_cancel', view.arch)

    def test_adjustment_form_contains_discrepancy_fields(self):
        """El formulario de ajuste muestra los tres totales de discrepancia."""
        view = self._view('view_stock_inventory_adjustment_form')
        self.assertIn('total_discrepancy', view.arch)
        self.assertIn('total_surplus', view.arch)
        self.assertIn('total_shortage', view.arch)

    def test_adjustment_search_has_state_filters(self):
        """La vista de búsqueda tiene filtros por estado."""
        view = self._view('view_stock_inventory_adjustment_search')
        self.assertIn('draft', view.arch)
        self.assertIn('done', view.arch)

    def test_sequence_adjustment_exists(self):
        """La secuencia ADJ/ existe en la base de datos."""
        seq = self.env.ref('inventory_custom.seq_stock_inventory_adjustment')
        self.assertTrue(seq)
        self.assertEqual(seq.code, 'stock.inventory.adjustment')
        self.assertEqual(seq.prefix, 'ADJ/')

    def test_security_groups_exist(self):
        """Los tres grupos de seguridad del módulo existen."""
        viewer = self.env.ref('inventory_custom.group_inventory_viewer')
        operator = self.env.ref('inventory_custom.group_inventory_operator')
        manager = self.env.ref('inventory_custom.group_inventory_manager')
        self.assertTrue(viewer)
        self.assertTrue(operator)
        self.assertTrue(manager)

    def test_manager_implies_operator(self):
        """El grupo Manager implica al grupo Operator."""
        manager = self.env.ref('inventory_custom.group_inventory_manager')
        operator = self.env.ref('inventory_custom.group_inventory_operator')
        self.assertIn(operator, manager.implied_ids)

    def test_operator_implies_viewer(self):
        """El grupo Operator implica al grupo Viewer."""
        operator = self.env.ref('inventory_custom.group_inventory_operator')
        viewer = self.env.ref('inventory_custom.group_inventory_viewer')
        self.assertIn(viewer, operator.implied_ids)
