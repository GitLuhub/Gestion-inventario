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
    image = fields.Binary(
        string='Imagen',
        attachment=True,
    )
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si desactiva esta categoría, no aparecerá en las listas.',
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
        categories = self.child_id
        for child in self.child_id:
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
