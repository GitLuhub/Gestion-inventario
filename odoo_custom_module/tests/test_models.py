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
