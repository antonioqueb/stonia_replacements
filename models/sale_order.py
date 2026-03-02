from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    replacement_order_ids = fields.One2many(
        'sale.replacement.order',
        'sale_order_id',
        string='Órdenes de reposición',
    )
    replacement_count = fields.Integer(
        string='Reposiciones',
        compute='_compute_replacement_count',
    )
    return_picking_ids = fields.One2many(
        'stock.picking',
        compute='_compute_return_pickings',
        string='Devoluciones',
    )
    return_count = fields.Integer(
        compute='_compute_return_pickings',
        string='Devoluciones',
    )
    # Resumen comercial
    total_m2_sold = fields.Float(
        string='m² vendidos',
        compute='_compute_m2_summary',
    )
    total_m2_delivered = fields.Float(
        string='m² entregados',
        compute='_compute_m2_summary',
    )
    total_m2_returned = fields.Float(
        string='m² devueltos',
        compute='_compute_m2_summary',
    )
    total_m2_replaced = fields.Float(
        string='m² repuestos',
        compute='_compute_m2_summary',
    )

    @api.depends('replacement_order_ids')
    def _compute_replacement_count(self):
        for order in self:
            order.replacement_count = len(order.replacement_order_ids)

    @api.depends('picking_ids')
    def _compute_return_pickings(self):
        for order in self:
            returns = order.picking_ids.filtered(lambda p: p.is_return_from_delivery)
            order.return_picking_ids = returns
            order.return_count = len(returns)

    def _compute_m2_summary(self):
        for order in self:
            # m² vendidos = suma de qty en líneas de venta
            order.total_m2_sold = sum(order.order_line.mapped('product_uom_qty'))
            # m² entregados = qty_delivered
            order.total_m2_delivered = sum(order.order_line.mapped('qty_delivered'))
            # m² devueltos
            order.total_m2_returned = sum(
                order.replacement_order_ids.mapped('total_m2_returned')
            )
            # m² repuestos
            order.total_m2_replaced = sum(
                order.replacement_order_ids.mapped('total_m2_replaced')
            )

    def action_open_replacements(self):
        """Abrir lista de reposiciones del pedido."""
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Reposiciones - %s') % self.name,
            'res_model': 'sale.replacement.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }
        if self.replacement_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.replacement_order_ids.id
        return action

    def action_open_returns(self):
        """Abrir devoluciones del pedido."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Devoluciones - %s') % self.name,
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.return_picking_ids.ids)],
        }

    def action_create_replacement(self):
        """Abrir wizard para crear reposición de materiales."""
        self.ensure_one()
        # Verificar que hay devoluciones
        returns = self.picking_ids.filtered(
            lambda p: p.is_return_from_delivery and p.state == 'done'
        )
        if not returns:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin devoluciones'),
                    'message': _('No hay devoluciones validadas para este pedido. '
                                 'Primero debe registrar una devolución.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generar Reposición de Materiales'),
            'res_model': 'sale.replacement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
        }
