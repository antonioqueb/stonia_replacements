from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    def _get_return_pickings(self):
        """Get returns: both custom-flagged and standard Odoo incoming pickings."""
        self.ensure_one()
        marked_returns = self.picking_ids.filtered(lambda p: p.is_return_from_delivery)
        standard_returns = self.picking_ids.filtered(
            lambda p: (
                p.picking_type_code == 'incoming'
                and not p.is_replacement_delivery
                and p.state != 'cancel'
            )
        )
        return marked_returns | standard_returns

    @api.depends('picking_ids', 'picking_ids.state', 'picking_ids.picking_type_code',
                 'picking_ids.is_return_from_delivery')
    def _compute_return_pickings(self):
        for order in self:
            returns = order._get_return_pickings()
            order.return_picking_ids = returns
            order.return_count = len(returns)

    def _compute_m2_summary(self):
        for order in self:
            order.total_m2_sold = sum(order.order_line.mapped('product_uom_qty'))
            order.total_m2_delivered = sum(order.order_line.mapped('qty_delivered'))
            order.total_m2_returned = sum(
                order.replacement_order_ids.mapped('total_m2_returned')
            )
            order.total_m2_replaced = sum(
                order.replacement_order_ids.mapped('total_m2_replaced')
            )

    def action_open_replacements(self):
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
        self.ensure_one()
        returns = self._get_return_pickings()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Devoluciones - %s') % self.name,
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', returns.ids)],
        }

    def action_create_replacement(self):
        """Button action — intercepted by JS to open OWL dialog.
        Kept as fallback in case JS fails."""
        self.ensure_one()
        returns = self._get_return_pickings().filtered(lambda p: p.state == 'done')
        if not returns:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin devoluciones'),
                    'message': _('No hay devoluciones validadas para este pedido.'),
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
            'context': {'default_sale_order_id': self.id},
        }

    # ===================== RPC METHODS FOR OWL WIZARD =====================

    @api.model
    def get_available_returns(self, sale_order_id):
        """RPC: Get available validated return pickings for a sale order."""
        order = self.browse(sale_order_id)
        if not order.exists():
            return []
        returns = order._get_return_pickings().filtered(lambda p: p.state == 'done')
        result = []
        for ret in returns:
            total_m2 = sum(ret.move_ids.filtered(
                lambda m: m.state == 'done'
            ).mapped('quantity'))
            result.append({
                'id': ret.id,
                'name': ret.name,
                'origin': ret.origin or '',
                'date': ret.scheduled_date.strftime('%d/%m/%Y') if ret.scheduled_date else '',
                'state': ret.state,
                'total_m2': total_m2,
                'return_reason': ret.return_reason_id.name if ret.return_reason_id else '',
                'is_logistics': ret.is_logistics_return,
            })
        return result

    @api.model
    def get_return_lines_for_replacement(self, sale_order_id, return_picking_ids):
        """RPC: Get detailed move lines from selected return pickings."""
        pickings = self.env['stock.picking'].browse(return_picking_ids)
        lines = []
        for picking in pickings:
            for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                sale_line = move.sale_line_id
                original_price = sale_line.price_unit if sale_line else 0.0
                for move_line in move.move_line_ids:
                    lines.append({
                        'productId': move.product_id.id,
                        'productName': move.product_id.display_name,
                        'lotId': move_line.lot_id.id if move_line.lot_id else False,
                        'lotName': move_line.lot_id.name if move_line.lot_id else '',
                        'm2Returned': move_line.quantity,
                        'originalUnitPrice': original_price,
                        'moveId': move.id,
                        'saleLineId': sale_line.id if sale_line else False,
                        'pickingId': picking.id,
                        'pickingName': picking.name,
                    })
        return lines

    @api.model
    def create_replacement_from_wizard(self, sale_order_id, payload):
        """RPC: Create replacement order from OWL wizard data."""
        order = self.browse(sale_order_id)
        if not order.exists():
            raise UserError(_('Pedido de venta no encontrado.'))

        replacement_type = payload.get('replacement_type')
        lines_data = payload.get('lines', [])

        # Validate no zero prices (unless admin)
        if replacement_type != 'refund':
            zero_lines = [l for l in lines_data
                          if l.get('replacement_unit_price', 0) <= 0
                          and l.get('m2_to_replace', 0) > 0]
            if zero_lines and not self.env.user.has_group(
                'stonia_replacements.group_replacement_admin'
            ):
                raise UserError(_(
                    'No se permite crear reposiciones con precio $0.00. '
                    'Las diferencias deben manejarse con notas de crédito.'
                ))

        # Mark return pickings
        return_picking_ids = payload.get('return_picking_ids', [])
        for picking in self.env['stock.picking'].browse(return_picking_ids):
            if not picking.is_return_from_delivery:
                picking.is_return_from_delivery = True

        # Create replacement order
        replacement = self.env['sale.replacement.order'].create({
            'sale_order_id': sale_order_id,
            'return_picking_ids': [(6, 0, return_picking_ids)],
            'replacement_type': replacement_type,
            'replacement_reason_id': payload.get('replacement_reason_id'),
            'charge_difference': payload.get('charge_difference', False),
            'no_charge_reason': payload.get('no_charge_reason', ''),
        })

        # Create lines
        for line in lines_data:
            vals = {
                'replacement_order_id': replacement.id,
                'original_product_id': line.get('product_id'),
                'm2_returned': line.get('m2_returned', 0),
                'product_id': line.get('replacement_product_id') or line.get('product_id'),
                'm2_replaced': line.get('m2_to_replace', 0),
                'original_unit_price': line.get('original_unit_price', 0),
                'unit_price': line.get('replacement_unit_price', 0),
                'sale_line_id': line.get('sale_line_id'),
                'return_move_id': line.get('move_id'),
            }
            lot_id = line.get('lot_id')
            if lot_id:
                vals['original_lot_ids'] = [(6, 0, [lot_id])]
            self.env['sale.replacement.order.line'].create(vals)

        # Confirm
        replacement.action_confirm()

        return {
            'replacement_id': replacement.id,
            'name': replacement.name,
        }