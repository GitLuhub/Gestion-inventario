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
        """Test jerarquía de menús"""
        root = self.env.ref('inventory_custom.menu_inventory_custom_root')
        self.assertTrue(root.child_id)
