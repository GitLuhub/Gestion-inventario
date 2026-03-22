from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare, float_is_zero


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
        help='Nivel mínimo de stock para alertas de reposición.',
    )
    max_stock_level = fields.Float(
        string='Nivel Máximo de Stock',
        digits='Product Unit of Measure',
        default=0.0,
        tracking=True,
        help='Nivel máximo de stock para control de capacidad.',
    )
    reorder_point = fields.Float(
        string='Punto de Reorden',
        digits='Product Unit of Measure',
        compute='_compute_reorder_point',
        store=True,
        readonly=False,
        help='Cantidad que activa la alerta de reorden.',
    )
    inventory_valuation = fields.Selection(
        selection=[
            ('manual', 'Costo Manual'),
            ('standard', 'Costo Estándar'),
            ('average', 'Costo Promedio'),
        ],
        string='Método de Valoración',
        default='standard',
        tracking=True,
    )
    last_inventory_date = fields.Date(
        string='Último Inventario',
        readonly=True,
        copy=False,
    )
    inventory_count_frequency = fields.Selection([
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('none', 'Sin conteo regular'),
    ], string='Frecuencia de Conteo', default='monthly')
    product_stock_count = fields.Integer(
        string='Total Ubicaciones',
        compute='_compute_stock_count',
        store=False,
    )
    
    @api.depends('min_stock_level', 'standard_price')
    def _compute_reorder_point(self):
        for product in self:
            if product.min_stock_level > 0 and product.standard_price > 0:
                product.reorder_point = product.min_stock_level * 0.5
            else:
                product.reorder_point = 0.0
    
    def _compute_stock_count(self):
        for product in self:
            quant_count = self.env['stock.quant'].search_count([
                ('product_id.product_tmpl_id', '=', product.id)
            ])
            product.product_stock_count = quant_count
    
    @api.constrains('min_stock_level', 'max_stock_level')
    def _check_stock_levels(self):
        for product in self:
            if product.min_stock_level and product.max_stock_level:
                if product.min_stock_level > product.max_stock_level:
                    raise ValidationError(_(
                        'El nivel mínimo de stock no puede ser mayor que el nivel máximo '
                        'para el producto %s.'
                    ) % product.name)
    
    @api.model
    def get_low_stock_products(self, limit=10):
        """Retorna productos con stock bajo el nivel mínimo."""
        products = self.search([
            ('type', '=', 'product'),
            ('min_stock_level', '>', 0),
            ('active', '=', True),
        ])
        
        low_stock = []
        for product in products:
            qty_available = product.qty_available
            if qty_available <= product.min_stock_level:
                low_stock.append({
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code,
                    'qty_available': qty_available,
                    'min_stock_level': product.min_stock_level,
                    'uom_id': product.uom_id.name,
                })
        
        low_stock.sort(key=lambda x: x['qty_available'])
        return low_stock[:limit]
    
    @api.model
    def get_products_needing_reorder(self):
        """Retorna productos que necesitan reordenarse."""
        return self.get_low_stock_products(limit=100)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    lot_ids = fields.One2many(
        'stock.production.lot',
        'product_id',
        string='Lotes',
        readonly=True,
    )
    lot_count = fields.Integer(
        string='Número de Lotes',
        compute='_compute_lot_count',
    )
    earliest_lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lote Más Antiguo',
        compute='_compute_earliest_lot',
        store=True,
    )
    latest_lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lote Más Reciente',
        compute='_compute_latest_lot',
        store=True,
    )
    
    @api.depends('lot_ids')
    def _compute_lot_count(self):
        for product in self:
            product.lot_count = len(product.lot_ids)
    
    @api.depends('lot_ids.create_date')
    def _compute_earliest_lot(self):
        for product in self:
            lots = product.lot_ids.sorted('create_date')
            product.earliest_lot_id = lots[0] if lots else False
    
    @api.depends('lot_ids.create_date')
    def _compute_latest_lot(self):
        for product in self:
            lots = product.lot_ids.sorted('create_date', reverse=True)
            product.latest_lot_id = lots[0] if lots else False
    
    def action_view_lots(self):
        self.ensure_one()
        return {
            'name': _('Lotes de %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'stock.production.lot',
            'type': 'ir.actions.act_window',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }
    
    def action_view_quants(self):
        self.ensure_one()
        return {
            'name': _('Stock de %s') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }


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
        string='Productos',
        compute='_compute_product_count',
        store=True,
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
        for brand in self:
            brand.product_count = len(brand.product_ids)
    
    @api.depends('name')
    def name_get(self):
        result = []
        for brand in self:
            name = brand.name
            result.append((brand.id, name))
        return result
