from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    brand_id = fields.Many2one(
        'product.brand',
        string='Marca',
        index=True,
        tracking=True,
    )
    manufacturer_ref = fields.Char(
        string='Ref. Fabricante',
        tracking=True,
        index=True,
    )
    min_stock_level = fields.Float(
        string='Nivel Mínimo de Stock',
        digits='Product Unit of Measure',
        default=0.0,
        tracking=True,
    )
    max_stock_level = fields.Float(
        string='Nivel Máximo de Stock',
        digits='Product Unit of Measure',
        default=0.0,
        tracking=True,
    )
    
    @api.constrains('min_stock_level', 'max_stock_level')
    def _check_stock_levels(self):
        for product in self:
            if product.min_stock_level and product.max_stock_level:
                if product.min_stock_level > product.max_stock_level:
                    raise ValidationError(_(
                        'El nivel mínimo de stock no puede ser mayor que el nivel máximo.'
                    ))


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Marca de Producto'
    _order = 'name'
    
    name = fields.Char(
        string='Nombre',
        required=True,
        index=True,
        translate=True,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    logo = fields.Binary(
        string='Logo',
        attachment=True,
    )
    product_count = fields.Integer(
        string='Nº Productos',
        compute='_compute_product_count',
        store=False,
    )
    product_ids = fields.One2many(
        'product.template',
        'brand_id',
        string='Productos',
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
    )
    
    @api.depends('product_ids')
    def _compute_product_count(self):
        count_data = self.env['product.template'].read_group(
            domain=[('brand_id', 'in', self.ids)],
            fields=['brand_id'],
            groupby=['brand_id'],
        )
        count_map = {row['brand_id'][0]: row['brand_id_count'] for row in count_data}
        for brand in self:
            brand.product_count = count_map.get(brand.id, 0)
