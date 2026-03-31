from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockInventoryWizard(models.TransientModel):
    _name = 'stock.inventory.wizard'
    _description = 'Wizard de Ajuste Rápido de Inventario'

    location_id = fields.Many2one(
        'stock.location',
        string='Ubicación',
        domain=[('usage', '=', 'internal')],
        required=True,
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('type', '=', 'product')],
        required=True,
    )
    
    current_qty = fields.Float(
        string='Stock Actual',
        digits='Product Unit of Measure',
        readonly=True,
    )
    
    new_qty = fields.Float(
        string='Nuevo Stock',
        digits='Product Unit of Measure',
        required=True,
        help='Cantidad final en inventario.',
    )
    
    difference_qty = fields.Float(
        string='Diferencia',
        digits='Product Unit of Measure',
        compute='_compute_difference',
        store=True,
    )
    
    reason_id = fields.Many2one(
        'stock.inventory.adjustment.reason',
        string='Razón del Ajuste',
    )
    
    notes = fields.Text(
        string='Notas',
    )
    
    create_adjustment_record = fields.Boolean(
        string='Crear registro de ajuste',
        default=True,
        help='Si está marcado, se creará un registro en el historial de ajustes.',
    )

    @api.onchange('location_id', 'product_id')
    def _onchange_product_location(self):
        """Carga el stock actual"""
        if self.product_id and self.location_id:
            quant = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id),
            ], limit=1)
            
            self.current_qty = quant.quantity if quant else 0.0
            self.new_qty = self.current_qty

    @api.depends('current_qty', 'new_qty')
    def _compute_difference(self):
        for wizard in self:
            wizard.difference_qty = wizard.new_qty - wizard.current_qty

    def action_apply(self):
        """Aplica el ajuste de inventario"""
        self.ensure_one()
        
        if self.difference_qty == 0:
            raise UserError(_('No hay diferencia para ajustar.'))
        
        adjustment = None
        
        if self.create_adjustment_record:
            adjustment = self._create_adjustment_record()
        
        move = self._create_stock_move()
        
        if adjustment:
            adjustment.write({
                'move_ids': [(4, move.id)],
                'state': 'done',
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Movimiento de Stock'),
            'res_model': 'stock.move',
            'res_id': move.id,
            'view_mode': 'form',
        }

    def _create_adjustment_record(self):
        """Crea un registro de ajuste de inventario"""
        Adjustment = self.env['stock.inventory.adjustment']
        
        adjustment = Adjustment.create({
            'adjustment_type': 'correction',
            'reason_id': self.reason_id.id if self.reason_id else False,
            'location_ids': [(4, self.location_id.id)],
            'responsible_id': self.env.user.id,
            'notes': self.notes,
        })
        
        AdjustmentLine = self.env['stock.inventory.adjustment.line']
        AdjustmentLine.create({
            'adjustment_id': adjustment.id,
            'product_id': self.product_id.id,
            'location_id': self.location_id.id,
            'current_qty': self.current_qty,
            'expected_qty': self.new_qty,
            'adjustment_reason': 'correction',
            'notes': self.notes,
        })
        
        adjustment.action_start()
        
        return adjustment

    def _get_inventory_location(self):
        """Retorna la ubicación de inventario de la compañía actual."""
        inventory_location = getattr(
            self.env.company, 'property_stock_inventory_loc_id', False
        ) or self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', '=', self.env.company.id)],
            limit=1,
        )
        if not inventory_location:
            raise UserError(_(
                'No se encontró una ubicación de inventario configurada para la compañía. '
                'Configure "Ubicación de Inventario" en los ajustes de la compañía.'
            ))
        return inventory_location

    def _create_stock_move(self):
        """Crea el movimiento de stock."""
        inventory_location = self._get_inventory_location()

        if self.difference_qty > 0:
            location_dest = self.location_id
            location_src = inventory_location
        else:
            location_src = self.location_id
            location_dest = inventory_location
        
        move_vals = {
            'name': _('Ajuste Rápido: %s') % self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': abs(self.difference_qty),
            'product_uom': self.product_id.uom_id.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
            'state': 'confirmed',
            'origin': 'Ajuste Rápido de Inventario',
        }
        
        move = self.env['stock.move'].create(move_vals)
        move._action_done()
        
        return move


class StockInventoryQuickCount(models.TransientModel):
    _name = 'stock.inventory.quick.count'
    _description = 'Conteo Rápido de Inventario'

    location_id = fields.Many2one(
        'stock.location',
        string='Ubicación',
        domain=[('usage', '=', 'internal')],
        required=True,
    )
    
    line_ids = fields.One2many(
        'stock.inventory.quick.count.line',
        'wizard_id',
        string='Líneas de Conteo',
    )
    
    create_adjustment = fields.Boolean(
        string='Crear ajuste automáticamente',
        default=True,
    )

    @api.onchange('location_id')
    def _onchange_location_id(self):
        """Carga los productos de la ubicación"""
        self.line_ids = False
        
        if not self.location_id:
            return
        
        Line = self.env['stock.inventory.quick.count.line']
        lines = []
        
        quants = self.env['stock.quant'].search([
            ('location_id', '=', self.location_id.id),
            ('quantity', '>', 0),
        ])
        
        for quant in quants:
            lines.append((0, 0, {
                'product_id': quant.product_id.id,
                'current_qty': quant.quantity,
                'counted_qty': quant.quantity,
            }))
        
        self.line_ids = lines

    def action_validate(self):
        """Valida el conteo y crea ajustes si hay diferencias"""
        self.ensure_one()
        
        lines_with_diff = self.line_ids.filtered(
            lambda l: l.counted_qty != l.current_qty
        )
        
        if not lines_with_diff:
            return {
                'type': 'ir.actions.act_window_close',
            }
        
        if self.create_adjustment:
            adjustment = self._create_adjustment(lines_with_diff)
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Ajuste Creado'),
                'res_model': 'stock.inventory.adjustment',
                'res_id': adjustment.id,
                'view_mode': 'form',
            }
        
        return {
            'type': 'ir.actions.act_window_close',
        }

    def _create_adjustment(self, lines_with_diff):
        """Crea el registro de ajuste de inventario"""
        Adjustment = self.env['stock.inventory.adjustment']
        
        adjustment = Adjustment.create({
            'adjustment_type': 'cyclic',
            'location_ids': [(4, self.location_id.id)],
            'responsible_id': self.env.user.id,
            'notes': _('Conteo rápido realizado el %s') % fields.Datetime.now(),
            'state': 'draft',
        })
        
        AdjustmentLine = self.env['stock.inventory.adjustment.line']
        Line = self.env['stock.inventory.quick.count.line']
        
        for line in lines_with_diff:
            AdjustmentLine.create({
                'adjustment_id': adjustment.id,
                'product_id': line.product_id.id,
                'location_id': self.location_id.id,
                'current_qty': line.current_qty,
                'expected_qty': line.counted_qty,
                'adjustment_reason': 'count',
            })
        
        adjustment.action_start()
        
        return adjustment


class StockInventoryQuickCountLine(models.TransientModel):
    _name = 'stock.inventory.quick.count.line'
    _description = 'Línea de Conteo Rápido'

    wizard_id = fields.Many2one(
        'stock.inventory.quick.count',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True,
    )
    
    current_qty = fields.Float(
        string='Stock Actual',
        digits='Product Unit of Measure',
        readonly=True,
    )
    
    counted_qty = fields.Float(
        string='Cantidad Contada',
        digits='Product Unit of Measure',
    )
    
    difference = fields.Float(
        string='Diferencia',
        digits='Product Unit of Measure',
        compute='_compute_difference',
        store=True,
    )
    
    has_difference = fields.Boolean(
        string='Tiene Diferencia',
        compute='_compute_difference',
        store=True,
    )

    @api.depends('current_qty', 'counted_qty')
    def _compute_difference(self):
        for line in self:
            line.difference = line.counted_qty - line.current_qty
            line.has_difference = line.difference != 0
