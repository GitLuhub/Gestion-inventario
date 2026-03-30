from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class StockInventoryAdjustment(models.Model):
    _name = 'stock.inventory.adjustment'
    _description = 'Ajuste de Inventario'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En Progreso'),
        ('done', 'Validado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)

    adjustment_type = fields.Selection([
        ('full', 'Inventario Completo'),
        ('partial', 'Inventario Parcial'),
        ('cyclic', 'Inventario Cíclico'),
        ('correction', 'Corrección'),
    ], string='Tipo de Ajuste', default='partial', tracking=True)

    reason_id = fields.Many2one(
        'stock.inventory.adjustment.reason',
        string='Razón del Ajuste',
    )

    location_ids = fields.Many2many(
        'stock.location',
        'inventory_adjustment_location_rel',
        'adjustment_id',
        'location_id',
        string='Ubicaciones',
        domain="[('usage', '=', 'internal')]",
        required=True,
        tracking=True,
    )

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsable',
        default=lambda self: self.env.user,
    )

    notes = fields.Text(
        string='Notas',
        help='Notas adicionales sobre el ajuste.',
    )

    line_ids = fields.One2many(
        'stock.inventory.adjustment.line',
        'adjustment_id',
        string='Líneas de Ajuste',
        copy=True,
    )

    line_count = fields.Integer(
        string='Cantidad de Líneas',
        compute='_compute_line_count',
        store=True,
    )

    total_discrepancy = fields.Float(
        string='Total Discrepancia',
        compute='_compute_totals',
        store=True,
    )

    move_ids = fields.Many2many(
        'stock.move',
        string='Movimientos de Stock',
        readonly=True,
        copy=False,
    )

    date = fields.Datetime(
        string='Fecha',
        default=fields.Datetime.now,
        required=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.inventory.adjustment') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for adjustment in self:
            adjustment.line_count = len(adjustment.line_ids)

    @api.depends('line_ids.difference_qty')
    def _compute_totals(self):
        for adjustment in self:
            adjustment.total_discrepancy = sum(
                abs(qty) for qty in adjustment.line_ids.mapped('difference_qty')
            )

    def action_start(self):
        """Inicia el proceso de ajuste."""
        self.write({'state': 'in_progress'})
        return True

    def action_generate_lines(self):
        """Genera líneas de ajuste basadas en el stock actual."""
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_('Solo puede regenerar líneas en estado Borrador.'))

        if not self.location_ids:
            raise UserError(_('Debe seleccionar al menos una ubicación.'))

        # Clear existing lines to avoid duplicates on repeated calls
        self.line_ids.unlink()

        Line = self.env['stock.inventory.adjustment.line']

        for location in self.location_ids:
            quants = self.env['stock.quant'].search([
                ('location_id', '=', location.id),
                ('quantity', '!=', 0),
            ])

            for quant in quants:
                Line.create({
                    'adjustment_id': self.id,
                    'product_id': quant.product_id.id,
                    'location_id': quant.location_id.id,
                    'current_qty': quant.quantity,
                    'expected_qty': quant.quantity,
                })

        return True

    def action_validate(self):
        """Valida el ajuste y crea movimientos de stock."""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_('No hay líneas para validar.'))

        lines_to_adjust = self.line_ids.filtered(lambda l: l.difference_qty != 0)

        if not lines_to_adjust:
            raise UserError(_('No hay diferencias para ajustar.'))

        moves = self.env['stock.move']

        for line in lines_to_adjust:
            move = self._create_stock_move(line)
            if move:
                moves |= move

        if moves:
            moves._action_done()

        self.write({
            'state': 'done',
            'move_ids': [(4, m.id) for m in moves],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Movimientos Creados'),
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', moves.ids)],
        }

    def _get_inventory_location(self):
        """Retorna la ubicación de inventario de la compañía actual."""
        inventory_location = (
            self.env.company.property_stock_inventory_loc_id
            or self.env['stock.location'].search(
                [('usage', '=', 'inventory'), ('company_id', '=', self.env.company.id)],
                limit=1,
            )
        )
        if not inventory_location:
            raise UserError(_(
                'No se encontró una ubicación de inventario configurada para la compañía. '
                'Configure "Ubicación de Inventario" en los ajustes de la compañía.'
            ))
        return inventory_location

    def _create_stock_move(self, line):
        """Crea un movimiento de stock para la línea de ajuste."""
        self.ensure_one()

        inventory_location = self._get_inventory_location()

        if line.difference_qty > 0:
            location_dest = line.location_id
            location_src = inventory_location
        else:
            location_src = line.location_id
            location_dest = inventory_location

        move_vals = {
            'name': _('Ajuste Inventario: %s') % self.name,
            'product_id': line.product_id.id,
            'product_uom_qty': abs(line.difference_qty),
            'product_uom': line.product_id.uom_id.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
            'state': 'confirmed',
            'origin': self.name,
        }

        move = self.env['stock.move'].create(move_vals)

        line.write({'move_id': move.id})

        return move

    def action_cancel(self):
        """Cancela el ajuste."""
        self.ensure_one()
        if self.move_ids:
            self.move_ids._action_cancel()
        self.write({'state': 'cancel'})
        return True

    def action_draft(self):
        """Regresa a borrador."""
        self.ensure_one()
        self.write({'state': 'draft'})
        return True


class StockInventoryAdjustmentLine(models.Model):
    _name = 'stock.inventory.adjustment.line'
    _description = 'Línea de Ajuste de Inventario'
    _order = 'product_id, location_id'

    _sql_constraints = [
        (
            'unique_product_location_adjustment',
            'UNIQUE(adjustment_id, product_id, location_id)',
            'Ya existe una línea para este producto y ubicación en el mismo ajuste.',
        ),
    ]

    adjustment_id = fields.Many2one(
        'stock.inventory.adjustment',
        string='Ajuste',
        required=True,
        ondelete='cascade',
        index=True,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True,
        domain=[('type', '=', 'product')],
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Ubicación',
        required=True,
        domain=[('usage', '=', 'internal')],
    )

    current_qty = fields.Float(
        string='Cantidad Actual',
        digits='Product Unit of Measure',
        default=0.0,
    )

    expected_qty = fields.Float(
        string='Cantidad Esperada',
        digits='Product Unit of Measure',
        required=True,
    )

    difference_qty = fields.Float(
        string='Diferencia',
        digits='Product Unit of Measure',
        compute='_compute_difference',
        store=True,
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
    ], string='Razón', default='count')

    notes = fields.Text(
        string='Notas',
    )

    move_id = fields.Many2one(
        'stock.move',
        string='Movimiento',
        readonly=True,
        copy=False,
    )

    state = fields.Selection(
        related='adjustment_id.state',
        string='Estado del Ajuste',
        readonly=True,
    )

    @api.depends('current_qty', 'expected_qty')
    def _compute_difference(self):
        for line in self:
            line.difference_qty = line.expected_qty - line.current_qty

    @api.onchange('current_qty')
    def _onchange_current_qty(self):
        """Actualiza la diferencia al cambiar cantidad actual."""
        if self.current_qty:
            self.difference_qty = self.expected_qty - self.current_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualiza ubicación y cantidad al cambiar producto."""
        if self.product_id and self.location_id:
            quant = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id),
            ], limit=1)

            if quant:
                self.current_qty = quant.quantity
                self.expected_qty = quant.quantity


class StockInventoryAdjustmentReason(models.Model):
    _name = 'stock.inventory.adjustment.reason'
    _description = 'Razón de Ajuste de Inventario'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
    )

    description = fields.Text(
        string='Descripción',
        translate=True,
    )
