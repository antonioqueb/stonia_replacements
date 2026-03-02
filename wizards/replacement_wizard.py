from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleReplacementWizard(models.TransientModel):
    _name = 'sale.replacement.wizard'
    _description = 'Wizard de Reposición de Materiales'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
        required=True,
    )
    return_picking_ids = fields.Many2many(
        'stock.picking',
        string='Devoluciones a reponer',
    )
    available_return_picking_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_available_return_pickings',
        string='Devoluciones disponibles',
    )
    replacement_type = fields.Selection([
        ('same_product', 'Reposición mismo producto'),
        ('different_product', 'Cambio a otro producto'),
        ('refund', 'Devolución de dinero (sin reposición)'),
    ], string='Tipo de reposición', required=True, default='same_product')

    replacement_reason_id = fields.Many2one(
        'stock.replacement.reason',
        string='Motivo de reposición',
        required=True,
    )
    charge_difference = fields.Boolean(
        string='Cobrar diferencia al cliente',
        default=False,
    )
    no_charge_reason = fields.Char(string='Motivo de no cobro')
    line_ids = fields.One2many(
        'sale.replacement.wizard.line',
        'wizard_id',
        string='Líneas',
    )
    notes = fields.Html(string='Notas')

    @api.depends('sale_order_id')
    def _compute_available_return_pickings(self):
        for wiz in self:
            if wiz.sale_order_id:
                # Obtener devoluciones validadas del pedido (custom + estándar)
                wiz.available_return_picking_ids = wiz.sale_order_id._get_return_pickings().filtered(
                    lambda p: p.state == 'done'
                )
            else:
                wiz.available_return_picking_ids = self.env['stock.picking']

    @api.onchange('return_picking_ids', 'replacement_type')
    def _onchange_return_pickings(self):
        """Cargar líneas desde las devoluciones seleccionadas."""
        if not self.return_picking_ids:
            self.line_ids = [(5, 0, 0)]
            return
        lines = []
        for picking in self.return_picking_ids:
            for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                # Buscar precio original de la línea de venta
                sale_line = move.sale_line_id
                original_price = sale_line.price_unit if sale_line else 0.0
                for move_line in move.move_line_ids:
                    lines.append((0, 0, {
                        'product_id': move.product_id.id,
                        'replacement_product_id': move.product_id.id if self.replacement_type == 'same_product' else False,
                        'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                        'm2_returned': move_line.quantity,
                        'm2_to_replace': move_line.quantity if self.replacement_type != 'refund' else 0,
                        'original_unit_price': original_price,
                        'replacement_unit_price': original_price if self.replacement_type == 'same_product' else 0,
                        'move_id': move.id,
                        'sale_line_id': sale_line.id if sale_line else False,
                    }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_create_replacement(self):
        """Crear la orden de reposición."""
        self.ensure_one()
        if not self.return_picking_ids:
            raise UserError(_('Debe seleccionar al menos una devolución.'))

        # Validar que no haya precios en 0 para reposiciones
        if self.replacement_type != 'refund':
            zero_lines = self.line_ids.filtered(
                lambda l: l.replacement_unit_price <= 0 and l.m2_to_replace > 0
            )
            if zero_lines and not self.env.user.has_group(
                'stonia_replacements.group_replacement_admin'
            ):
                raise UserError(_(
                    'No se permite crear reposiciones con precio $0.00. '
                    'Las diferencias deben manejarse con notas de crédito.'
                ))

        # Marcar los pickings de devolución si no están marcados
        for picking in self.return_picking_ids:
            if not picking.is_return_from_delivery:
                picking.is_return_from_delivery = True

        # Crear orden de reposición
        replacement = self.env['sale.replacement.order'].create({
            'sale_order_id': self.sale_order_id.id,
            'return_picking_ids': [(6, 0, self.return_picking_ids.ids)],
            'replacement_type': self.replacement_type,
            'replacement_reason_id': self.replacement_reason_id.id,
            'charge_difference': self.charge_difference,
            'no_charge_reason': self.no_charge_reason,
            'notes': self.notes,
        })

        # Crear líneas
        for line in self.line_ids:
            self.env['sale.replacement.order.line'].create({
                'replacement_order_id': replacement.id,
                'original_product_id': line.product_id.id,
                'original_lot_ids': [(6, 0, [line.lot_id.id])] if line.lot_id else False,
                'm2_returned': line.m2_returned,
                'product_id': line.replacement_product_id.id or line.product_id.id,
                'm2_replaced': line.m2_to_replace,
                'original_unit_price': line.original_unit_price,
                'unit_price': line.replacement_unit_price,
                'sale_line_id': line.sale_line_id.id,
                'return_move_id': line.move_id.id,
            })

        # Confirmar automáticamente
        replacement.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reposición de Materiales'),
            'res_model': 'sale.replacement.order',
            'res_id': replacement.id,
            'view_mode': 'form',
            'target': 'current',
        }


class SaleReplacementWizardLine(models.TransientModel):
    _name = 'sale.replacement.wizard.line'
    _description = 'Línea de Wizard de Reposición'

    wizard_id = fields.Many2one(
        'sale.replacement.wizard',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto original',
    )
    replacement_product_id = fields.Many2one(
        'product.product',
        string='Producto de reposición',
    )
    lot_id = fields.Many2one('stock.lot', string='Lote devuelto')
    m2_returned = fields.Float(string='m² devueltos')
    m2_to_replace = fields.Float(string='m² a reponer')
    original_unit_price = fields.Float(string='Precio original')
    replacement_unit_price = fields.Float(string='Precio reposición')
    move_id = fields.Many2one('stock.move', string='Movimiento')
    sale_line_id = fields.Many2one('sale.order.line', string='Línea de venta')