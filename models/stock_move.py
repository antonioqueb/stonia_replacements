from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_replacement_move = fields.Boolean(
        string='Movimiento de reposición',
        default=False,
    )
