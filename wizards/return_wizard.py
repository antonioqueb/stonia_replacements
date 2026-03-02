from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockReturnWizard(models.TransientModel):
    _name = 'stock.return.wizard'
    _description = 'Wizard de Devolución de Material'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Entrega',
        required=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
    )
    return_reason_id = fields.Many2one(
        'stock.return.reason',
        string='Motivo de devolución',
        required=True,
    )
    is_logistics_return = fields.Boolean(
        string='Retorno logístico',
        related='return_reason_id.is_logistics',
        readonly=True,
    )
    no_physical_return = fields.Boolean(
        string='Sin retorno físico',
        related='return_reason_id.no_physical_return',
        readonly=True,
    )
    notes = fields.Text(string='Notas')
    line_ids = fields.One2many(
        'stock.return.wizard.line',
        'wizard_id',
        string='Líneas a devolver',
    )
    total_m2 = fields.Float(
        string='Total m² a devolver',
        compute='_compute_total_m2',
    )

    @api.depends('line_ids.qty_to_return')
    def _compute_total_m2(self):
        for wiz in self:
            wiz.total_m2 = sum(wiz.line_ids.filtered('to_return').mapped('qty_to_return'))

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        """Cargar líneas desde la entrega con lotes entregados."""
        if not self.picking_id:
            return
        lines = []
        for move in self.picking_id.move_ids.filtered(lambda m: m.state == 'done'):
            for move_line in move.move_line_ids:
                lines.append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                    'qty_delivered': move_line.quantity,
                    'qty_to_return': move_line.quantity,
                    'to_return': False,
                }))
        self.line_ids = lines

    def action_confirm_return(self):
        """Crear el picking de devolución."""
        self.ensure_one()
        lines_to_return = self.line_ids.filtered('to_return')
        if not lines_to_return:
            raise UserError(_('Debe seleccionar al menos un producto para devolver.'))
        if not self.return_reason_id:
            raise UserError(_('Debe indicar un motivo de devolución.'))

        picking = self.picking_id
        picking_type = picking.picking_type_id.return_picking_type_id or picking.picking_type_id

        # Crear picking de devolución
        return_picking_vals = {
            'picking_type_id': picking_type.id,
            'partner_id': picking.partner_id.id,
            'origin': _('Devolución de %s') % picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': picking.location_id.id,
            'sale_id': self.sale_order_id.id,
            'is_return_from_delivery': True,
            'return_reason_id': self.return_reason_id.id,
            'return_notes': self.notes,
            'is_logistics_return': self.return_reason_id.is_logistics,
            'original_delivery_id': picking.id,
        }
        return_picking = self.env['stock.picking'].create(return_picking_vals)

        for line in lines_to_return:
            self.env['stock.move'].create({
                'name': _('Devolución: %s') % line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty_to_return,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': return_picking.id,
                'location_id': picking.location_dest_id.id,
                'location_dest_id': picking.location_id.id,
                'origin_returned_move_id': line.move_id.id,
            })

        return_picking.action_confirm()

        # Si es sin retorno físico, marcar para scrap directo
        if self.return_reason_id.no_physical_return:
            return_picking.message_post(
                body=_('⚠️ Devolución sin retorno físico. '
                       'El material debe registrarse como merma/scrap.')
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Devolución'),
            'res_model': 'stock.picking',
            'res_id': return_picking.id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockReturnWizardLine(models.TransientModel):
    _name = 'stock.return.wizard.line'
    _description = 'Línea de Wizard de Devolución'

    wizard_id = fields.Many2one(
        'stock.return.wizard',
        required=True,
        ondelete='cascade',
    )
    to_return = fields.Boolean(string='Devolver', default=False)
    move_id = fields.Many2one('stock.move', string='Movimiento')
    product_id = fields.Many2one('product.product', string='Producto')
    lot_id = fields.Many2one('stock.lot', string='Lote/Placa')
    qty_delivered = fields.Float(string='m² entregados')
    qty_to_return = fields.Float(string='m² a devolver')
