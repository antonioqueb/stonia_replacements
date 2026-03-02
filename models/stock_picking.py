from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return_from_delivery = fields.Boolean(
        string='Es devolución de entrega',
        default=False,
        copy=False,
    )
    return_reason_id = fields.Many2one(
        'stock.return.reason',
        string='Motivo de devolución',
        tracking=True,
    )
    return_notes = fields.Text(string='Notas de devolución')
    is_logistics_return = fields.Boolean(
        string='Retorno logístico',
        default=False,
        help='Retorno logístico: el material no se pudo descargar. '
             'No genera nota de crédito.',
    )
    is_replacement_delivery = fields.Boolean(
        string='Es entrega de reposición',
        default=False,
        copy=False,
    )
    replacement_order_id = fields.Many2one(
        'sale.replacement.order',
        string='Orden de reposición',
        copy=False,
    )
    original_delivery_id = fields.Many2one(
        'stock.picking',
        string='Entrega original',
        help='Referencia a la entrega original de la cual se hizo devolución.',
    )

    def action_create_return_wizard(self):
        """Abrir wizard de devolución con filtro de lotes."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Devolver Material'),
            'res_model': 'stock.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_sale_order_id': self.sale_id.id if self.sale_id else False,
            },
        }

    def action_scrap_from_return(self):
        """Abrir wizard para desechar desde devolución."""
        self.ensure_one()
        if not self.is_return_from_delivery:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Desechar desde Devolución'),
            'res_model': 'stock.scrap.from.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_return_picking_id': self.id,
            },
        }

    def button_validate(self):
        """Override para actualizar estado de reposición cuando se valida entrega."""
        res = super().button_validate()
        for picking in self:
            if picking.is_replacement_delivery and picking.replacement_order_id:
                ro = picking.replacement_order_id
                if ro.accounting_state == 'pending':
                    ro.state = 'accounting_pending'
                else:
                    ro.state = 'done'
                # Actualizar estatus de líneas
                for line in ro.line_ids:
                    line.status = 'delivered'
        return res
