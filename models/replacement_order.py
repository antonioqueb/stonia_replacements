from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReplacementOrder(models.Model):
    _name = 'sale.replacement.order'
    _description = 'Orden de Reposición'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
        string='Cliente',
        store=True,
    )
    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Devolución origen',
        domain="[('is_return_from_delivery', '=', True), "
               "('sale_id', '=', sale_order_id)]",
        tracking=True,
    )
    return_picking_ids = fields.Many2many(
        'stock.picking',
        'replacement_order_return_picking_rel',
        'replacement_id',
        'picking_id',
        string='Devoluciones origen',
    )
    replacement_type = fields.Selection([
        ('same_product', 'Reposición mismo producto'),
        ('different_product', 'Cambio a otro producto'),
        ('refund', 'Devolución de dinero (sin reposición)'),
    ], string='Tipo de reposición', required=True, tracking=True)

    replacement_reason_id = fields.Many2one(
        'stock.replacement.reason',
        string='Motivo de reposición',
        required=True,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('picking_pending', 'Pendiente de entrega'),
        ('picking_done', 'Entregado'),
        ('accounting_pending', 'Contabilidad pendiente'),
        ('done', 'Completado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)

    line_ids = fields.One2many(
        'sale.replacement.order.line',
        'replacement_order_id',
        string='Líneas de reposición',
    )
    out_picking_id = fields.Many2one(
        'stock.picking',
        string='Entrega de reposición',
        readonly=True,
        copy=False,
    )
    credit_note_id = fields.Many2one(
        'account.move',
        string='Nota de crédito',
        readonly=True,
        copy=False,
    )
    new_invoice_id = fields.Many2one(
        'account.move',
        string='Nueva factura',
        readonly=True,
        copy=False,
    )

    # Campos contables / decisión
    charge_difference = fields.Boolean(
        string='Cobrar diferencia al cliente',
        default=False,
        tracking=True,
    )
    no_charge_reason = fields.Char(
        string='Motivo de no cobro',
        tracking=True,
    )
    accounting_state = fields.Selection([
        ('not_required', 'No requiere'),
        ('pending', 'Pendiente'),
        ('done', 'Completada'),
    ], string='Estado contable', default='not_required', tracking=True)

    original_invoiced = fields.Boolean(
        string='Entrega original facturada',
        compute='_compute_original_invoiced',
        store=True,
    )
    total_m2_returned = fields.Float(
        string='m² devueltos',
        compute='_compute_totals',
        store=True,
    )
    total_m2_replaced = fields.Float(
        string='m² repuestos',
        compute='_compute_totals',
        store=True,
    )
    total_amount_difference = fields.Float(
        string='Diferencia en importe',
        compute='_compute_totals',
        store=True,
    )
    notes = fields.Html(string='Notas internas')
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )

    @api.depends('return_picking_id', 'return_picking_ids')
    def _compute_original_invoiced(self):
        for rec in self:
            # Check if any related SO invoice exists
            rec.original_invoiced = bool(rec.sale_order_id.invoice_ids.filtered(
                lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'
            ))

    @api.depends('line_ids.m2_returned', 'line_ids.m2_replaced', 'line_ids.amount_difference')
    def _compute_totals(self):
        for rec in self:
            rec.total_m2_returned = sum(rec.line_ids.mapped('m2_returned'))
            rec.total_m2_replaced = sum(rec.line_ids.mapped('m2_replaced'))
            rec.total_amount_difference = sum(rec.line_ids.mapped('amount_difference'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sale.replacement.order'
                ) or _('Nuevo')
        return super().create(vals_list)

    def action_confirm(self):
        """Confirmar la orden de reposición."""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Debe agregar al menos una línea de reposición.'))
            if rec.replacement_type == 'refund':
                rec.state = 'accounting_pending'
                rec.accounting_state = 'pending'
            else:
                rec._validate_no_zero_price()
                rec.state = 'confirmed'
                if rec.original_invoiced:
                    rec.accounting_state = 'pending'

    def _validate_no_zero_price(self):
        """No permitir líneas con precio 0 como práctica estándar."""
        zero_lines = self.line_ids.filtered(lambda l: l.unit_price <= 0 and l.m2_replaced > 0)
        if zero_lines:
            raise UserError(_(
                'No se permite crear reposiciones con precio $0.00. '
                'Las diferencias de costo deben manejarse a través de notas de crédito. '
                'Si necesita crear una reposición sin cobro, contacte a un administrador.'
            ))

    def action_create_delivery(self):
        """Crear el picking de salida para la reposición."""
        self.ensure_one()
        if self.replacement_type == 'refund':
            raise UserError(_('Las devoluciones de dinero no generan entrega.'))

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1)

        if not picking_type:
            raise UserError(_('No se encontró un tipo de operación de salida.'))

        picking_vals = {
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'origin': f'{self.sale_order_id.name} / {self.name}',
            'sale_id': self.sale_order_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.partner_id.property_stock_customer.id,
            'is_replacement_delivery': True,
            'replacement_order_id': self.id,
        }
        picking = self.env['stock.picking'].create(picking_vals)

        for line in self.line_ids.filtered(lambda l: l.m2_replaced > 0):
            self.env['stock.move'].create({
                'name': f'Reposición: {line.product_id.display_name}',
                'product_id': line.product_id.id,
                'product_uom_qty': line.m2_replaced,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': self.partner_id.property_stock_customer.id,
                'origin': self.name,
                'sale_line_id': line.sale_line_id.id if line.sale_line_id else False,
                'is_replacement_move': True,
            })

        picking.action_confirm()
        self.out_picking_id = picking.id
        self.state = 'picking_pending'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_mark_accounting_done(self):
        """Contabilidad marca como completado."""
        for rec in self:
            rec.accounting_state = 'done'
            if rec.state == 'accounting_pending':
                rec.state = 'done'
            elif rec.out_picking_id and rec.out_picking_id.state == 'done':
                rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            if rec.out_picking_id and rec.out_picking_id.state == 'done':
                raise UserError(_('No se puede cancelar una reposición con entrega ya validada.'))
            if rec.out_picking_id and rec.out_picking_id.state != 'cancel':
                rec.out_picking_id.action_cancel()
            rec.state = 'cancelled'

    def action_set_to_draft(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.state = 'draft'
