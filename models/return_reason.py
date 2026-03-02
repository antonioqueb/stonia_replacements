from odoo import models, fields


class ReturnReason(models.Model):
    _name = 'stock.return.reason'
    _description = 'Motivo de devolución'
    _order = 'sequence, id'

    name = fields.Char(string='Motivo', required=True)
    code = fields.Char(string='Código')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    is_logistics = fields.Boolean(
        string='Retorno logístico',
        help='Marcar si este motivo aplica para retornos logísticos (no descargado, '
             'acceso bloqueado, etc.) y NO debe generar nota de crédito automática.',
    )
    requires_scrap = fields.Boolean(
        string='Requiere desecho',
        help='Si el motivo implica que el material regresa dañado y debe ir a scrap.',
    )
    no_physical_return = fields.Boolean(
        string='Sin retorno físico',
        help='El material no regresa al almacén (se rompió, se perdió, etc.)',
    )
