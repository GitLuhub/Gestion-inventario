from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    location_type = fields.Selection([
        ('warehouse', 'Almacén'),
        ('zone', 'Zona'),
        ('aisle', 'Pasillo'),
        ('rack', 'Estantería'),
        ('shelf', 'Estante'),
        ('bin', 'Ubicación/Bin'),
        ('transit', 'En Tránsito'),
        ('quality', 'Control de Calidad'),
        ('returns', 'Devoluciones'),
        ('scrap', 'Desechos'),
    ], string='Tipo de Ubicación', default='bin', index=True)

    max_capacity = fields.Float(
        string='Capacidad Máxima',
        digits='Product Unit of Measure',
        help='Capacidad máxima de almacenamiento en unidades.',
    )
    current_capacity = fields.Float(
        string='Capacidad Actual',
        compute='_compute_current_capacity',
        digits='Product Unit of Measure',
    )
    capacity_usage_percent = fields.Float(
        string='% Uso de Capacidad',
        compute='_compute_capacity_usage',
        store=False,
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        index=True,
    )
    barcode = fields.Char(
        string='Código de Barras',
        index=True,
        copy=False,
    )
    usage_class = fields.Selection([
        ('dry', 'Seco'),
        ('cold', 'Refrigerado'),
        ('frozen', 'Congelado'),
        ('hazardous', 'Peligroso'),
        ('standard', 'Estándar'),
    ], string='Clase de Almacenamiento', default='standard')
    temperature_range = fields.Char(
        string='Rango de Temperatura',
        help='Ej: 2-8°C para refrigerado',
    )

    @api.depends('max_capacity', 'quant_ids.quantity')
    def _compute_current_capacity(self):
        for location in self:
            total_qty = sum(location.quant_ids.mapped('quantity'))
            location.current_capacity = total_qty

    @api.depends('max_capacity', 'current_capacity')
    def _compute_capacity_usage(self):
        for location in self:
            if location.max_capacity > 0:
                location.capacity_usage_percent = (
                    location.current_capacity / location.max_capacity * 100
                )
            else:
                location.capacity_usage_percent = 0.0

    @api.constrains('location_type', 'usage')
    def _check_location_type_compatibility(self):
        for location in self:
            if location.location_type == 'warehouse' and location.usage not in ('internal', 'view'):
                raise ValidationError(_(
                    'Una ubicación de tipo "Almacén" solo puede tener '
                    'uso "Interno" o "Vista".'
                ))

    def get_child_locations_tree(self):
        """Retorna todos los hijos en estructura de árbol."""
        self.ensure_one()
        children = self.child_ids
        tree = [{'id': self.id, 'name': self.name, 'children': []}]

        for child in children:
            tree[0]['children'].append(child.get_child_locations_tree()[0])

        return tree

    @api.model
    def get_locations_by_type(self, location_type):
        """Retorna ubicaciones filtradas por tipo."""
        return self.search([
            ('location_type', '=', location_type),
            ('usage', '=', 'internal'),
        ])


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # NOTE: lot_id already exists on stock.quant in Odoo 16 core — do NOT redefine it.
    lot_name = fields.Char(
        string='Nombre Lote',
        related='lot_id.name',
        store=False,
        readonly=True,
    )
