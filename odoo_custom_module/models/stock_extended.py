from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


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
        tracking=True,
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
            if location.location_type == 'warehouse' and location.usage != 'internal':
                if location.usage not in ('internal', 'view'):
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
    
    lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lote',
        readonly=True,
        check_company=True,
        ondelete='restrict',
    )
    lot_expiration_date = fields.Date(
        string='Fecha Vencimiento Lote',
        related='lot_id.expiration_date',
        store=True,
        readonly=True,
    )
    is_expired = fields.Boolean(
        string='Vencido',
        compute='_compute_is_expired',
        search='_search_is_expired',
    )
    incoming_date = fields.Datetime(
        string='Fecha de Entrada',
        related='lot_id.create_date',
        store=True,
        readonly=True,
    )
    product_min_date = fields.Date(
        string='Fecha Mínima',
        related='lot_id.use_date',
        store=True,
        readonly=True,
    )
    
    @api.depends('lot_expiration_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for quant in self:
            if quant.lot_expiration_date:
                quant.is_expired = quant.lot_expiration_date < today
            else:
                quant.is_expired = False
    
    def _search_is_expired(self, operator, value):
        today = fields.Date.today()
        if operator == '=' and value:
            return [('lot_expiration_date', '<', today)]
        elif operator == '=' and not value:
            return ['|',
                    ('lot_expiration_date', '>=', today),
                    ('lot_expiration_date', '=', False)]
        return []
    
    @api.model
    def get_expired_quants(self):
        """Retorna quants con productos vencidos."""
        today = fields.Date.today()
        return self.search([
            ('lot_expiration_date', '<', today),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ])


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'
    
    theoretical_qty = fields.Float(
        string='Cantidad Teórica',
        compute='_compute_theoretical_qty',
        store=True,
        readonly=False,
    )
    difference_qty = fields.Float(
        string='Diferencia',
        compute='_compute_difference_qty',
        store=True,
        readonly=True,
    )
    adjustment_reason = fields.Selection([
        ('count', 'Conteo Físico'),
        ('damage', 'Daño'),
        ('loss', 'Pérdida'),
        ('theft', 'Robo'),
        ('expiration', 'Vencimiento'),
        ('return', 'Devolución'),
        ('correction', 'Corrección'),
        ('other', 'Otro'),
    ], string='Razón del Ajuste', default='count')
    notes = fields.Text(
        string='Notas',
        help='Notas adicionales sobre el ajuste.',
    )
    
    @api.depends('product_id', 'location_id', 'product_uom_id', 'prod_lot_id')
    def _compute_theoretical_qty(self):
        for line in self:
            if not line.product_id or not line.location_id:
                line.theoretical_qty = 0
                continue
            
            theoretical_qty = line.product_id.with_context(
                location=line.location_id.id,
                lot_id=line.prod_lot_id.id,
            ).qty_available
            
            if line.product_uom_id and line.product_uom_id != line.product_id.uom_id:
                theoretical_qty = line.product_id.uom_id._compute_quantity(
                    theoretical_qty,
                    line.product_uom_id,
                )
            
            line.theoretical_qty = theoretical_qty
    
    @api.depends('theoretical_qty', 'product_qty')
    def _compute_difference_qty(self):
        for line in self:
            line.difference_qty = line.product_qty - line.theoretical_qty
    
    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        if self.product_id and self.location_id:
            theoretical = self.product_id.with_context(
                location=self.location_id.id,
            ).qty_available
            self.difference_qty = self.product_qty - theoretical


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    
    adjustment_type = fields.Selection([
        ('full', 'Inventario Completo'),
        ('partial', 'Inventario Parcial'),
        ('cyclic', 'Inventario Cíclico'),
    ], string='Tipo de Ajuste', default='partial', tracking=True)
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        default=lambda self: self.env.user,
    )
    location_ids = fields.Many2many(
        'stock.location',
        'stock_inventory_location_rel',
        'inventory_id',
        'location_id',
        string='Ubicaciones',
        domain="[('usage', '=', 'internal')]",
        required=True,
    )
    notes = fields.Text(
        string='Notas',
    )
    is_complete = fields.Boolean(
        string='Inventario Completo',
        compute='_compute_is_complete',
        store=True,
    )
    
    @api.depends('line_ids.difference_qty')
    def _compute_is_complete(self):
        for inventory in self:
            lines_with_diff = inventory.line_ids.filtered(
                lambda l: l.difference_qty != 0
            )
            inventory.is_complete = len(lines_with_diff) > 0
    
    def action_validate(self):
        """Valida el inventario y registra los movimientos."""
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_('No hay líneas para validar.'))
        
        for line in self.line_ids:
            if line.difference_qty == 0:
                continue
            
            if line.adjustment_reason == 'count':
                self._create_inventory_line_move(line)
        
        return super(StockInventory, self).action_validate()
    
    def _create_inventory_line_move(self, line):
        """Crea movimiento de stock para la línea."""
        self.ensure_one()
        
        if line.difference_qty > 0:
            location_dest_id = line.location_id.id
            location_src_id = self.env.ref('stock.location_inventory').id
        else:
            location_src_id = line.location_id.id
            location_dest_id = self.env.ref('stock.location_inventory').id
        
        move_vals = {
            'name': _('Ajuste Inventario: %s') % self.name,
            'product_id': line.product_id.id,
            'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
            'product_uom_qty': abs(line.difference_qty),
            'location_id': location_src_id,
            'location_dest_id': location_dest_id,
            'inventory_id': self.id,
            'state': 'confirmed',
        }
        
        move = self.env['stock.move'].create(move_vals)
        move._action_done()
        
        line.write({'move_id': move.id})
    
    @api.model
    def create_cyclic_inventory(self, location_ids=False):
        """Crea un inventario cíclico para las ubicaciones especificadas."""
        vals = {
            'name': _('Inventario Cíclico - %s') % fields.Date.today(),
            'adjustment_type': 'cyclic',
            'state': 'draft',
        }
        
        if location_ids:
            vals['location_ids'] = [(6, 0, location_ids)]
        
        inventory = self.create(vals)
        inventory.action_start()
        
        return inventory
