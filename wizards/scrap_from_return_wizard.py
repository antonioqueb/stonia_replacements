from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ScrapFromReturnWizard(models.TransientModel):
    _name = 'stock.scrap.from.return.wizard'
    _description = 'Desechar desde Devolución'

    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Devolución',
        required=True,
    )
    line_ids = fields.One2many(
        'stock.scrap.from.return.wizard.line',
        'wizard_id',
        string='Material a desechar',
    )
    scrap_reason = fields.Text(string='Motivo del desecho', required=True)

    @api.onchange('return_picking_id')
    def _onchange_return_picking(self):
        if not self.return_picking_id:
            return
        lines = []
        for move in self.return_picking_id.move_ids.filtered(lambda m: m.state == 'done'):
            for move_line in move.move_line_ids:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                    'qty_available': move_line.quantity,
                    'qty_to_scrap': move_line.quantity,
                    'to_scrap': False,
                }))
        self.line_ids = lines

    def action_scrap(self):
        """Crear registros de scrap para las líneas seleccionadas."""
        self.ensure_one()
        lines_to_scrap = self.line_ids.filtered('to_scrap')
        if not lines_to_scrap:
            raise UserError(_('Seleccione al menos un material para desechar.'))

        scrap_location = self.env['stock.location'].search([
            ('scrap_location', '=', True),
            ('company_id', 'in', [self.env.company.id, False]),
        ], limit=1)

        if not scrap_location:
            raise UserError(_('No se encontró una ubicación de desecho configurada.'))

        scraps = self.env['stock.scrap']
        for line in lines_to_scrap:
            scrap = self.env['stock.scrap'].create({
                'product_id': line.product_id.id,
                'lot_id': line.lot_id.id if line.lot_id else False,
                'scrap_qty': line.qty_to_scrap,
                'picking_id': self.return_picking_id.id,
                'location_id': self.return_picking_id.location_dest_id.id,
                'scrap_location_id': scrap_location.id,
                'origin': _('Desecho desde devolución %s - %s') % (
                    self.return_picking_id.name,
                    self.scrap_reason[:50] if self.scrap_reason else '',
                ),
            })
            scrap.action_validate()
            scraps |= scrap

        msg = _('Se desecharon %d líneas. Motivo: %s') % (
            len(lines_to_scrap), self.scrap_reason
        )
        self.return_picking_id.message_post(body=msg)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Desecho completado'),
                'message': msg,
                'type': 'success',
                'sticky': False,
            },
        }


class ScrapFromReturnWizardLine(models.TransientModel):
    _name = 'stock.scrap.from.return.wizard.line'
    _description = 'Línea de Wizard de Desecho'

    wizard_id = fields.Many2one(
        'stock.scrap.from.return.wizard',
        required=True,
        ondelete='cascade',
    )
    to_scrap = fields.Boolean(string='Desechar', default=False)
    product_id = fields.Many2one('product.product', string='Producto')
    lot_id = fields.Many2one('stock.lot', string='Lote/Placa')
    qty_available = fields.Float(string='m² disponibles')
    qty_to_scrap = fields.Float(string='m² a desechar')
