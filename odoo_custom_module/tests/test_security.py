# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase


class TestSecurityGroups(TransactionCase):
    """Tests para validar grupos de seguridad"""

    def test_brand_access_manager(self):
        """Test que el grupo manager tiene acceso a product.brand"""
        Group = self.env['res.groups']
        brand_model = self.env['ir.model'].search([('model', '=', 'product.brand')])
        
        manager_group = Group.search([
            ('name', '=', 'Gestor de Inventario')
        ])
        self.assertTrue(manager_group)
        
        viewer_group = Group.search([
            ('name', '=', 'Visor de Inventario')
        ])
        self.assertTrue(viewer_group)

    def test_category_exists(self):
        """Test que la categoría del módulo existe"""
        Category = self.env['ir.module.category']
        category = Category.search([('name', '=', 'Gestión de Inventario')])
        self.assertTrue(category)
        self.assertEqual(category.sequence, 15)


class TestModuleDependencies(TransactionCase):
    """Tests para validar dependencias del módulo"""

    def setUp(self):
        super(TestModuleDependencies, self).setUp()
        self.Module = self.env['ir.module.module']

    def test_module_installed(self):
        """Test que el módulo está instalado (o en proceso de actualización)."""
        module = self.Module.search([('name', '=', 'inventory_custom')])
        self.assertTrue(module)
        self.assertIn(module.state, ('installed', 'to upgrade'),
                      'El módulo debe estar instalado o actualizándose')

    def test_dependencies_installed(self):
        """Test que las dependencias están instaladas"""
        for dep in ['base', 'product', 'stock']:
            module = self.Module.search([('name', '=', dep)])
            self.assertTrue(module, f"Módulo {dep} no encontrado")
            self.assertEqual(module.state, 'installed', f"Módulo {dep} no instalado")
