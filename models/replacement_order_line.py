from odoo import models, fields, api


class ReplacementOrderLine(models.Model):
    _name = 'sale.replacement.order.line'
    _description = 'Línea de Orden de Reposición'

    replacement_order_id = fields.Many2one(
        'sale.replacement.order',
        string='Orden de reposición',
        required=True,
        ondelete='cascade',
    )
    sale_order_id = fields.Many2one(
        related='replacement_order_id.sale_order_id',
        store=True,
    )
    # Producto original (devuelto)
    original_product_id = fields.Many2one(
        'product.product',
        string='Producto original (devuelto)',
    )
    original_lot_ids = fields.Many2many(
        'stock.lot',
        'replacement_line_original_lot_rel',
        'line_id',
        'lot_id',
        string='Lotes devueltos',
    )
    m2_returned = fields.Float(string='m² devueltos')

    # Producto de reposición
    product_id = fields.Many2one(
        'product.product',
        string='Producto de reposición',
        required=True,
    )
    replacement_lot_ids = fields.Many2many(
        'stock.lot',
        'replacement_line_new_lot_rel',
        'line_id',
        'lot_id',
        string='Lotes de reposición',
        help='Placas/lotes seleccionados para la reposición',
    )
    m2_replaced = fields.Float(string='m² a reponer')

    # Precios y diferencias
    original_unit_price = fields.Float(string='Precio original (por m²)')
    unit_price = fields.Float(string='Precio reposición (por m²)')
    amount_difference = fields.Float(
        string='Diferencia',
        compute='_compute_amount_difference',
        store=True,
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de pedido original',
    )
    return_move_id = fields.Many2one(
        'stock.move',
        string='Movimiento de devolución',
    )
    status = fields.Selection([
        ('pending_selection', 'Pendiente de seleccionar placas'),
        ('pending_delivery', 'Pendiente de entrega'),
        ('delivered', 'Entregado'),
    ], string='Estatus', default='pending_selection')

    notes = fields.Text(string='Notas')

    @api.depends('m2_returned', 'original_unit_price', 'm2_replaced', 'unit_price')
    def _compute_amount_difference(self):
        for line in self:
            original_amount = line.m2_returned * line.original_unit_price
            replacement_amount = line.m2_replaced * line.unit_price
            line.amount_difference = replacement_amount - original_amount
