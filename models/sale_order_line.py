from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_replacement = fields.Boolean(
        string='Es reposición',
        default=False,
        help='Línea generada por una reposición de materiales',
    )
    replacement_order_id = fields.Many2one(
        'sale.replacement.order',
        string='Orden de reposición',
    )
    replacement_of_return_id = fields.Many2one(
        'stock.picking',
        string='Devolución origen',
    )
