from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    # NOTE: parent_path is auto-managed by Odoo core via _parent_store=True on product.category.
    # Do NOT redefine it here — manual definition conflicts with Odoo's ORM internals.
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
            raise ValidationError(
                _('Error: No puede crear categorías recursivas.')
            )
