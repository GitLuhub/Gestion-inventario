from odoo import models, fields, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    code = fields.Char(
        string='Código',
        index=True,
    )
    description = fields.Text(
        string='Descripción',
        translate=True,
    )
    parent_path = fields.Char(
        string='Ruta Padre',
        index=True,
        readonly=True,
    )
    product_count = fields.Integer(
        string='Cantidad de Productos',
        compute='_compute_product_count',
        store=True,
    )
    average_cost = fields.Float(
        string='Costo Promedio',
        compute='_compute_average_cost',
        store=False,
    )
    total_value = fields.Float(
        string='Valor Total',
        compute='_compute_total_value',
        store=False,
    )
    parent_id = fields.Many2one(
        'product.category',
        string='Categoría Padre',
        index=True,
        ondelete='cascade',
        domain="[('id', '!=', active_id)]" if 'active_id' in self.env.context else [],
    )
    child_ids = fields.One2many(
        'product.category',
        'parent_id',
        string='Categorías Hijas',
    )
    image = fields.Binary(
        string='Imagen',
        attachment=True,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si desactiva esta categoría, no aparecerá en las listas.',
    )
    
    @api.depends('product_ids', 'child_ids.product_count')
    def _compute_product_count(self):
        for category in self:
            direct_count = len(category.product_ids)
            child_count = sum(category.child_ids.mapped('product_count'))
            category.product_count = direct_count + child_count
    
    @api.depends('product_ids.standard_price', 'product_ids.qty_available')
    def _compute_average_cost(self):
        for category in self:
            products = category.product_ids.filtered(
                lambda p: p.type == 'product' and p.qty_available > 0
            )
            if products:
                total_value = sum(
                    p.standard_price * p.qty_available 
                    for p in products
                )
                total_qty = sum(p.qty_available for p in products)
                category.average_cost = total_value / total_qty if total_qty else 0
            else:
                category.average_cost = 0
    
    @api.depends('product_ids.standard_price', 'product_ids.qty_available')
    def _compute_total_value(self):
        for category in self:
            products = category.product_ids.filtered(
                lambda p: p.type == 'product'
            )
            category.total_value = sum(
                p.standard_price * p.qty_available 
                for p in products
            )
    
    @api.model
    def name_create(self, name):
        """Permite crear categorías directamente desde el nombre."""
        vals = {'name': name}
        if 'default_code' in self.env.context:
            vals['code'] = self.env.context['default_code']
        
        record = self.create(vals)
        return record.name_get()[0]
    
    def get_full_path(self):
        """Retorna la ruta completa de categorías."""
        self.ensure_one()
        names = []
        category = self
        while category:
            names.insert(0, category.name)
            category = category.parent_id
        return ' / '.join(names)
    
    def get_subcategories(self, include_self=False):
        """Retorna todas las subcategorías."""
        self.ensure_one()
        categories = self.child_ids
        for child in self.child_ids:
            categories |= child.get_subcategories()
        
        if include_self:
            categories |= self
        
        return categories
    
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Evita categorías recursivas."""
        if not self._check_recursion():
            raise models.ValidationError(
                _('Error: No puede crear categorías recursivas.')
            )
