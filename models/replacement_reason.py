from odoo import models, fields


class ReplacementReason(models.Model):
    _name = 'stock.replacement.reason'
    _description = 'Motivo de reposición'
    _order = 'sequence, id'

    name = fields.Char(string='Motivo', required=True)
    code = fields.Char(string='Código')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
