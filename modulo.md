## ./__init__.py
```py
from . import models
from . import wizards
```

## ./__manifest__.py
```py
{
    'name': 'Reposición de Materiales',
    'version': '19.0.1.1.0',
    'category': 'Sales',
    'summary': 'Gestión de devoluciones y reposiciones de materiales con trazabilidad completa',
    'description': """
        Módulo para gestionar el flujo completo de:
        - Devoluciones de material (retorno físico al almacén)
        - Reposición de materiales (nueva entrega por material devuelto)
        - Scrap/Desecho desde devolución
        - Retorno logístico (no descargado)
        - Trazabilidad completa por lote/placa
        - Integración contable (notas de crédito, refacturación)
    """,
    'author': 'Alphaqueb Consulting',
    'website': 'https://www.alphaqueb.com',
    'depends': [
        'sale_management',
        'sale_stock',
        'stock',
        'account',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/replacement_reason_data.xml',
        'data/return_reason_data.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/replacement_order_views.xml',
        'views/return_reason_views.xml',
        'views/replacement_reason_views.xml',
        'views/menu_views.xml',
        'wizards/return_wizard_views.xml',
        'wizards/replacement_wizard_views.xml',
        'wizards/scrap_from_return_wizard_views.xml',
        'report/replacement_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stonia_replacements/static/src/css/replacement_wizard.css',
            'stonia_replacements/static/src/js/replacement_wizard_dialog.js',
            'stonia_replacements/static/src/js/sale_order_replacement_hook.js',
            'stonia_replacements/static/src/xml/replacement_wizard_dialog.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}```

## ./data/replacement_reason_data.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="replacement_reason_breakage" model="stock.replacement.reason">
            <field name="name">Rotura en descarga</field>
            <field name="code">BREAK</field>
            <field name="sequence">10</field>
        </record>
        <record id="replacement_reason_defect" model="stock.replacement.reason">
            <field name="name">Defecto de fábrica</field>
            <field name="code">DEFECT</field>
            <field name="sequence">20</field>
        </record>
        <record id="replacement_reason_wrong" model="stock.replacement.reason">
            <field name="name">Material equivocado</field>
            <field name="code">WRONG</field>
            <field name="sequence">30</field>
        </record>
        <record id="replacement_reason_change" model="stock.replacement.reason">
            <field name="name">Cambio negociado con cliente</field>
            <field name="code">CHANGE</field>
            <field name="sequence">40</field>
        </record>
        <record id="replacement_reason_finish" model="stock.replacement.reason">
            <field name="name">No le gustó acabado</field>
            <field name="code">FINISH</field>
            <field name="sequence">50</field>
        </record>
        <record id="replacement_reason_size" model="stock.replacement.reason">
            <field name="name">Medidas incorrectas</field>
            <field name="code">SIZE</field>
            <field name="sequence">60</field>
        </record>
    </data>
</odoo>
```

## ./data/return_reason_data.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="return_reason_not_liked" model="stock.return.reason">
            <field name="name">No le gustó al cliente</field>
            <field name="code">NOT_LIKED</field>
            <field name="sequence">10</field>
        </record>
        <record id="return_reason_defect" model="stock.return.reason">
            <field name="name">Defectos en el material</field>
            <field name="code">DEFECT</field>
            <field name="sequence">20</field>
        </record>
        <record id="return_reason_broken" model="stock.return.reason">
            <field name="name">Material roto/dañado</field>
            <field name="code">BROKEN</field>
            <field name="sequence">30</field>
            <field name="requires_scrap" eval="True"/>
        </record>
        <record id="return_reason_broken_no_return" model="stock.return.reason">
            <field name="name">Roto sin retorno (perdido en sitio)</field>
            <field name="code">BROKEN_NR</field>
            <field name="sequence">35</field>
            <field name="requires_scrap" eval="True"/>
            <field name="no_physical_return" eval="True"/>
        </record>
        <record id="return_reason_wrong_product" model="stock.return.reason">
            <field name="name">Producto equivocado</field>
            <field name="code">WRONG</field>
            <field name="sequence">40</field>
        </record>
        <record id="return_reason_change" model="stock.return.reason">
            <field name="name">Cambio de material (cliente)</field>
            <field name="code">CHANGE</field>
            <field name="sequence">50</field>
        </record>
        <record id="return_reason_not_unloaded" model="stock.return.reason">
            <field name="name">No se pudo descargar (retorno logístico)</field>
            <field name="code">LOGISTICS</field>
            <field name="sequence">60</field>
            <field name="is_logistics" eval="True"/>
        </record>
        <record id="return_reason_access_blocked" model="stock.return.reason">
            <field name="name">Acceso bloqueado en sitio</field>
            <field name="code">ACCESS</field>
            <field name="sequence">70</field>
            <field name="is_logistics" eval="True"/>
        </record>
    </data>
</odoo>
```

## ./models/__init__.py
```py
from . import return_reason
from . import replacement_reason
from . import replacement_order
from . import replacement_order_line
from . import sale_order
from . import sale_order_line
from . import stock_picking
from . import stock_move
```

## ./models/replacement_order_line.py
```py
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
```

## ./models/replacement_order.py
```py
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
```

## ./models/replacement_reason.py
```py
from odoo import models, fields


class ReplacementReason(models.Model):
    _name = 'stock.replacement.reason'
    _description = 'Motivo de reposición'
    _order = 'sequence, id'

    name = fields.Char(string='Motivo', required=True)
    code = fields.Char(string='Código')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
```

## ./models/return_reason.py
```py
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
```

## ./models/sale_order_line.py
```py
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
```

## ./models/sale_order.py
```py
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
        }```

## ./models/stock_move.py
```py
from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_replacement_move = fields.Boolean(
        string='Movimiento de reposición',
        default=False,
    )
```

## ./models/stock_picking.py
```py
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
```

## ./report/replacement_report_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Pivot View -->
    <record id="view_replacement_order_pivot" model="ir.ui.view">
        <field name="name">sale.replacement.order.pivot</field>
        <field name="model">sale.replacement.order</field>
        <field name="arch" type="xml">
            <pivot string="Análisis de Reposiciones">
                <field name="replacement_reason_id" type="row"/>
                <field name="replacement_type" type="col"/>
                <field name="total_m2_returned" type="measure"/>
                <field name="total_m2_replaced" type="measure"/>
                <field name="total_amount_difference" type="measure"/>
            </pivot>
        </field>
    </record>

    <!-- Graph View -->
    <record id="view_replacement_order_graph" model="ir.ui.view">
        <field name="name">sale.replacement.order.graph</field>
        <field name="model">sale.replacement.order</field>
        <field name="arch" type="xml">
            <graph string="Reposiciones">
                <field name="replacement_reason_id"/>
                <field name="total_m2_replaced" type="measure"/>
            </graph>
        </field>
    </record>

    <!-- Update action to include pivot/graph -->
    <record id="action_replacement_order" model="ir.actions.act_window">
        <field name="name">Órdenes de Reposición</field>
        <field name="res_model">sale.replacement.order</field>
        <field name="view_mode">list,form,pivot,graph</field>
        <field name="search_view_id" ref="view_replacement_order_search"/>
    </record>
</odoo>
```

## ./security/security_groups.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="group_replacement_user" model="res.groups">
        <field name="name">Reposiciones: Usuario</field>
        <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <record id="group_replacement_manager" model="res.groups">
        <field name="name">Reposiciones: Responsable</field>
        <field name="implied_ids" eval="[(4, ref('group_replacement_user'))]"/>
    </record>

    <record id="group_replacement_admin" model="res.groups">
        <field name="name">Reposiciones: Administrador</field>
        <field name="implied_ids" eval="[(4, ref('group_replacement_manager'))]"/>
        <field name="comment">Puede crear reposiciones con precio cero y acciones especiales.</field>
    </record>
</odoo>```

## ./static/src/js/replacement_wizard_dialog.js
```js
/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class ReplacementWizardDialog extends Component {
    static template = "stonia_replacements.ReplacementWizardDialog";
    static components = { Dialog };
    static props = {
        saleOrderId: Number,
        saleOrderName: { type: String, optional: true },
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            // Step control
            step: 1, // 1: config, 2: lines, 3: review
            loading: false,

            // Step 1 fields
            replacementType: "same_product",
            replacementReasonId: false,
            chargeCustomer: false,
            noChargeReason: "",
            selectedReturnIds: [],

            // Data
            availableReturns: [],
            replacementReasons: [],
            lines: [],

            // Totals
            totalM2Returned: 0,
            totalM2Replaced: 0,
            totalDifference: 0,
        });

        onWillStart(async () => {
            await this._loadInitialData();
        });
    }

    async _loadInitialData() {
        this.state.loading = true;
        try {
            // Load available returns
            const returns = await this.orm.call(
                "sale.order",
                "get_available_returns",
                [this.props.saleOrderId],
            );
            this.state.availableReturns = returns;

            // Load replacement reasons
            const reasons = await this.orm.searchRead(
                "stock.replacement.reason",
                [["active", "=", true]],
                ["id", "name", "code"],
                { order: "sequence, id" },
            );
            this.state.replacementReasons = reasons;
        } catch (e) {
            this.notification.add(_t("Error cargando datos: ") + e.message, {
                type: "danger",
            });
        }
        this.state.loading = false;
    }

    // --- Step navigation ---
    get canGoStep2() {
        return (
            this.state.selectedReturnIds.length > 0 &&
            this.state.replacementReasonId &&
            (this.state.chargeCustomer || this.state.noChargeReason.trim())
        );
    }

    get canGoStep3() {
        return this.state.lines.some((l) => l.m2ToReplace > 0);
    }

    async goToStep2() {
        if (!this.canGoStep2) return;
        this.state.loading = true;
        try {
            const linesData = await this.orm.call(
                "sale.order",
                "get_return_lines_for_replacement",
                [this.props.saleOrderId, this.state.selectedReturnIds],
            );
            this.state.lines = linesData.map((l) => ({
                ...l,
                replacementProductId: this.state.replacementType === "same_product" ? l.productId : false,
                replacementProductName: this.state.replacementType === "same_product" ? l.productName : "",
                m2ToReplace: this.state.replacementType === "refund" ? 0 : l.m2Returned,
                replacementUnitPrice:
                    this.state.replacementType === "same_product" ? l.originalUnitPrice : 0,
            }));
            this._recalcTotals();
            this.state.step = 2;
        } catch (e) {
            this.notification.add(_t("Error cargando líneas: ") + e.message, {
                type: "danger",
            });
        }
        this.state.loading = false;
    }

    goToStep3() {
        if (!this.canGoStep3) return;
        this._recalcTotals();
        this.state.step = 3;
    }

    goBack(step) {
        this.state.step = step;
    }

    // --- Return selection ---
    toggleReturn(returnId) {
        const idx = this.state.selectedReturnIds.indexOf(returnId);
        if (idx >= 0) {
            this.state.selectedReturnIds.splice(idx, 1);
        } else {
            this.state.selectedReturnIds.push(returnId);
        }
    }

    isReturnSelected(returnId) {
        return this.state.selectedReturnIds.includes(returnId);
    }

    selectAllReturns() {
        if (this.state.selectedReturnIds.length === this.state.availableReturns.length) {
            this.state.selectedReturnIds = [];
        } else {
            this.state.selectedReturnIds = this.state.availableReturns.map((r) => r.id);
        }
    }

    get allReturnsSelected() {
        return (
            this.state.availableReturns.length > 0 &&
            this.state.selectedReturnIds.length === this.state.availableReturns.length
        );
    }

    // --- Line editing ---
    onLineM2Change(index, ev) {
        const val = parseFloat(ev.target.value) || 0;
        this.state.lines[index].m2ToReplace = val;
        this._recalcTotals();
    }

    onLinePriceChange(index, ev) {
        const val = parseFloat(ev.target.value) || 0;
        this.state.lines[index].replacementUnitPrice = val;
        this._recalcTotals();
    }

    async onLineProductChange(index, ev) {
        const productId = parseInt(ev.target.value) || false;
        if (productId) {
            const products = await this.orm.read("product.product", [productId], [
                "display_name",
                "list_price",
            ]);
            if (products.length) {
                this.state.lines[index].replacementProductId = productId;
                this.state.lines[index].replacementProductName = products[0].display_name;
                this.state.lines[index].replacementUnitPrice = products[0].list_price;
            }
        }
        this._recalcTotals();
    }

    _recalcTotals() {
        let totalReturned = 0;
        let totalReplaced = 0;
        let totalDiff = 0;
        for (const line of this.state.lines) {
            totalReturned += line.m2Returned;
            totalReplaced += line.m2ToReplace;
            const origAmount = line.m2Returned * line.originalUnitPrice;
            const replAmount = line.m2ToReplace * line.replacementUnitPrice;
            totalDiff += replAmount - origAmount;
        }
        this.state.totalM2Returned = totalReturned;
        this.state.totalM2Replaced = totalReplaced;
        this.state.totalDifference = totalDiff;
    }

    // --- Labels ---
    get replacementTypeLabel() {
        const labels = {
            same_product: "Reposición mismo producto",
            different_product: "Cambio a otro producto",
            refund: "Devolución de dinero",
        };
        return labels[this.state.replacementType] || "";
    }

    get reasonLabel() {
        const r = this.state.replacementReasons.find(
            (x) => x.id === this.state.replacementReasonId,
        );
        return r ? r.name : "";
    }

    get isRefund() {
        return this.state.replacementType === "refund";
    }

    formatCurrency(val) {
        return "$" + (val || 0).toFixed(2);
    }

    formatM2(val) {
        return (val || 0).toFixed(2) + " m²";
    }

    // --- Submit ---
    async onConfirm() {
        this.state.loading = true;
        try {
            const payload = {
                sale_order_id: this.props.saleOrderId,
                replacement_type: this.state.replacementType,
                replacement_reason_id: this.state.replacementReasonId,
                charge_difference: this.state.chargeCustomer,
                no_charge_reason: this.state.noChargeReason,
                return_picking_ids: this.state.selectedReturnIds,
                lines: this.state.lines.map((l) => ({
                    product_id: l.productId,
                    replacement_product_id: l.replacementProductId || l.productId,
                    lot_id: l.lotId,
                    m2_returned: l.m2Returned,
                    m2_to_replace: l.m2ToReplace,
                    original_unit_price: l.originalUnitPrice,
                    replacement_unit_price: l.replacementUnitPrice,
                    move_id: l.moveId,
                    sale_line_id: l.saleLineId,
                })),
            };

            const result = await this.orm.call(
                "sale.order",
                "create_replacement_from_wizard",
                [this.props.saleOrderId, payload],
            );

            this.notification.add(_t("Reposición creada exitosamente"), {
                type: "success",
            });

            this.props.close();

            // Navigate to the created replacement
            if (result && result.replacement_id) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "sale.replacement.order",
                    res_id: result.replacement_id,
                    views: [[false, "form"]],
                    target: "current",
                });
            }
        } catch (e) {
            this.notification.add(_t("Error creando reposición: ") + (e.data?.message || e.message), {
                type: "danger",
                sticky: true,
            });
        }
        this.state.loading = false;
    }
}

// Register as client action for fallback
registry.category("actions").add("stonia_replacement_wizard", ReplacementWizardDialog);```

## ./static/src/js/sale_order_replacement_hook.js
```js
/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { ReplacementWizardDialog } from "./replacement_wizard_dialog";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.__replacementDialog = useService("dialog");
    },

    async onWillSaveRecord(record) {
        return super.onWillSaveRecord(...arguments);
    },

    /**
     * Intercept the action_create_replacement button to open OWL dialog instead
     */
    async onButtonClicked(params) {
        if (
            params.name === "action_create_replacement" &&
            this.props.resModel === "sale.order"
        ) {
            const record = this.model.root;
            const saleOrderId = record.resId;
            const saleOrderName = record.data.name || "";

            // First check if there are returns available
            const orm = this.env.services.orm;
            const returns = await orm.call(
                "sale.order",
                "get_available_returns",
                [saleOrderId],
            );

            if (!returns || returns.length === 0) {
                this.env.services.notification.add(
                    "No hay devoluciones validadas para este pedido. Primero debe registrar una devolución.",
                    { title: "Sin devoluciones", type: "warning" },
                );
                return;
            }

            this.__replacementDialog.add(ReplacementWizardDialog, {
                saleOrderId: saleOrderId,
                saleOrderName: saleOrderName,
            });
            return;
        }
        return super.onButtonClicked(...arguments);
    },
});```

## ./static/src/xml/replacement_wizard_dialog.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">

    <t t-name="stonia_replacements.ReplacementWizardDialog">
        <Dialog title="'Reposición de Materiales'" size="'xl'" contentClass="'o_replacement_wizard'">
            <div class="replacement-wizard">
                <!-- Loading overlay -->
                <div t-if="state.loading" class="rw-loading-overlay">
                    <div class="rw-spinner"/>
                    <span>Procesando...</span>
                </div>

                <!-- Step indicators -->
                <div class="rw-steps">
                    <div t-attf-class="rw-step {{ state.step >= 1 ? 'active' : '' }} {{ state.step > 1 ? 'done' : '' }}">
                        <div class="rw-step-number">
                            <t t-if="state.step > 1"><i class="fa fa-check"/></t>
                            <t t-else="">1</t>
                        </div>
                        <div class="rw-step-label">Configuración</div>
                    </div>
                    <div class="rw-step-connector" t-attf-class="{{ state.step > 1 ? 'active' : '' }}"/>
                    <div t-attf-class="rw-step {{ state.step >= 2 ? 'active' : '' }} {{ state.step > 2 ? 'done' : '' }}">
                        <div class="rw-step-number">
                            <t t-if="state.step > 2"><i class="fa fa-check"/></t>
                            <t t-else="">2</t>
                        </div>
                        <div class="rw-step-label">Líneas</div>
                    </div>
                    <div class="rw-step-connector" t-attf-class="{{ state.step > 2 ? 'active' : '' }}"/>
                    <div t-attf-class="rw-step {{ state.step >= 3 ? 'active' : '' }}">
                        <div class="rw-step-number">3</div>
                        <div class="rw-step-label">Confirmar</div>
                    </div>
                </div>

                <!-- ==================== STEP 1: Configuration ==================== -->
                <div t-if="state.step === 1" class="rw-content">
                    <div class="rw-two-cols">
                        <!-- Left column: Type + Reason -->
                        <div class="rw-col">
                            <div class="rw-section-title">Tipo de Reposición</div>
                            <div class="rw-type-cards">
                                <div t-attf-class="rw-type-card {{ state.replacementType === 'same_product' ? 'selected' : '' }}"
                                     t-on-click="() => { state.replacementType = 'same_product'; }">
                                    <i class="fa fa-refresh"/>
                                    <div class="rw-type-card-title">Mismo producto</div>
                                    <div class="rw-type-card-desc">Reponer los mismos m² con otras placas</div>
                                </div>
                                <div t-attf-class="rw-type-card {{ state.replacementType === 'different_product' ? 'selected' : '' }}"
                                     t-on-click="() => { state.replacementType = 'different_product'; }">
                                    <i class="fa fa-exchange"/>
                                    <div class="rw-type-card-title">Cambio de producto</div>
                                    <div class="rw-type-card-desc">Cambiar por otro material diferente</div>
                                </div>
                                <div t-attf-class="rw-type-card {{ state.replacementType === 'refund' ? 'selected' : '' }}"
                                     t-on-click="() => { state.replacementType = 'refund'; }">
                                    <i class="fa fa-money"/>
                                    <div class="rw-type-card-title">Devolución de dinero</div>
                                    <div class="rw-type-card-desc">Sin reposición, solo reembolso</div>
                                </div>
                            </div>

                            <div class="rw-section-title mt-3">Motivo</div>
                            <select class="rw-select" t-on-change="(ev) => { state.replacementReasonId = parseInt(ev.target.value) || false; }">
                                <option value="">— Seleccionar motivo —</option>
                                <t t-foreach="state.replacementReasons" t-as="reason" t-key="reason.id">
                                    <option t-att-value="reason.id"
                                            t-att-selected="state.replacementReasonId === reason.id">
                                        <t t-esc="reason.name"/>
                                    </option>
                                </t>
                            </select>

                            <div class="rw-section-title mt-3">Cobro de diferencia</div>
                            <div class="rw-toggle-row">
                                <label class="rw-toggle">
                                    <input type="checkbox"
                                           t-att-checked="state.chargeCustomer"
                                           t-on-change="(ev) => { state.chargeCustomer = ev.target.checked; }"/>
                                    <span class="rw-toggle-slider"/>
                                </label>
                                <span>Cobrar diferencia al cliente</span>
                            </div>
                            <t t-if="!state.chargeCustomer">
                                <input type="text" class="rw-input mt-2"
                                       placeholder="Motivo de no cobro..."
                                       t-att-value="state.noChargeReason"
                                       t-on-input="(ev) => { state.noChargeReason = ev.target.value; }"/>
                            </t>
                        </div>

                        <!-- Right column: Returns selection -->
                        <div class="rw-col">
                            <div class="rw-section-title">
                                Devoluciones a reponer
                                <span class="rw-badge" t-esc="state.selectedReturnIds.length + '/' + state.availableReturns.length"/>
                            </div>

                            <div t-if="state.availableReturns.length === 0" class="rw-empty">
                                <i class="fa fa-inbox fa-3x"/>
                                <p>No hay devoluciones disponibles</p>
                            </div>

                            <t t-if="state.availableReturns.length > 0">
                                <div class="rw-select-all" t-on-click="selectAllReturns">
                                    <input type="checkbox" t-att-checked="allReturnsSelected" readonly="1"/>
                                    <span>Seleccionar todas</span>
                                </div>
                                <div class="rw-return-list">
                                    <t t-foreach="state.availableReturns" t-as="ret" t-key="ret.id">
                                        <div t-attf-class="rw-return-card {{ isReturnSelected(ret.id) ? 'selected' : '' }}"
                                             t-on-click="() => this.toggleReturn(ret.id)">
                                            <div class="rw-return-check">
                                                <input type="checkbox" t-att-checked="isReturnSelected(ret.id)" readonly="1"/>
                                            </div>
                                            <div class="rw-return-info">
                                                <div class="rw-return-name" t-esc="ret.name"/>
                                                <div class="rw-return-detail">
                                                    <span t-esc="ret.origin || ''"/>
                                                    <span class="rw-return-date" t-esc="ret.date"/>
                                                </div>
                                            </div>
                                            <div class="rw-return-m2">
                                                <span t-esc="(ret.total_m2 || 0).toFixed(2)"/> m²
                                            </div>
                                        </div>
                                    </t>
                                </div>
                            </t>
                        </div>
                    </div>

                    <!-- Step 1 footer -->
                    <div class="rw-footer">
                        <button class="rw-btn rw-btn-secondary" t-on-click="props.close">Cancelar</button>
                        <button t-attf-class="rw-btn rw-btn-primary {{ !canGoStep2 ? 'disabled' : '' }}"
                                t-on-click="goToStep2">
                            Siguiente <i class="fa fa-arrow-right ms-1"/>
                        </button>
                    </div>
                </div>

                <!-- ==================== STEP 2: Lines ==================== -->
                <div t-if="state.step === 2" class="rw-content">
                    <div class="rw-table-wrapper">
                        <table class="rw-table">
                            <thead>
                                <tr>
                                    <th>Producto Original</th>
                                    <th>Lote</th>
                                    <th class="text-end">m² Devueltos</th>
                                    <th t-if="!isRefund">Producto Reposición</th>
                                    <th t-if="!isRefund" class="text-end">m² a Reponer</th>
                                    <th class="text-end">Precio Orig.</th>
                                    <th t-if="!isRefund" class="text-end">Precio Repos.</th>
                                    <th class="text-end">Diferencia</th>
                                </tr>
                            </thead>
                            <tbody>
                                <t t-foreach="state.lines" t-as="line" t-key="line_index">
                                    <tr>
                                        <td>
                                            <span class="rw-product-name" t-esc="line.productName"/>
                                        </td>
                                        <td>
                                            <span class="rw-lot-tag" t-if="line.lotName" t-esc="line.lotName"/>
                                            <span t-else="" class="text-muted">—</span>
                                        </td>
                                        <td class="text-end">
                                            <span class="rw-m2-val" t-esc="line.m2Returned.toFixed(2)"/>
                                        </td>
                                        <td t-if="!isRefund">
                                            <t t-if="state.replacementType === 'same_product'">
                                                <span t-esc="line.productName"/>
                                            </t>
                                            <t t-else="">
                                                <input type="text" class="rw-input rw-input-sm"
                                                       placeholder="ID producto..."
                                                       t-att-value="line.replacementProductId || ''"
                                                       t-on-change="(ev) => this.onLineProductChange(line_index, ev)"/>
                                                <div t-if="line.replacementProductName" class="rw-product-hint"
                                                     t-esc="line.replacementProductName"/>
                                            </t>
                                        </td>
                                        <td t-if="!isRefund" class="text-end">
                                            <input type="number" class="rw-input rw-input-num"
                                                   step="0.01" min="0"
                                                   t-att-value="line.m2ToReplace"
                                                   t-on-change="(ev) => this.onLineM2Change(line_index, ev)"/>
                                        </td>
                                        <td class="text-end">
                                            <span t-esc="formatCurrency(line.originalUnitPrice)"/>
                                        </td>
                                        <td t-if="!isRefund" class="text-end">
                                            <input type="number" class="rw-input rw-input-num"
                                                   step="0.01" min="0"
                                                   t-att-value="line.replacementUnitPrice"
                                                   t-on-change="(ev) => this.onLinePriceChange(line_index, ev)"/>
                                        </td>
                                        <td class="text-end">
                                            <span t-attf-class="rw-diff {{ (line.m2ToReplace * line.replacementUnitPrice - line.m2Returned * line.originalUnitPrice) &lt; 0 ? 'negative' : 'positive' }}"
                                                  t-esc="formatCurrency(line.m2ToReplace * line.replacementUnitPrice - line.m2Returned * line.originalUnitPrice)"/>
                                        </td>
                                    </tr>
                                </t>
                            </tbody>
                            <tfoot>
                                <tr class="rw-totals-row">
                                    <td colspan="2"><strong>Totales</strong></td>
                                    <td class="text-end"><strong t-esc="formatM2(state.totalM2Returned)"/></td>
                                    <td t-if="!isRefund"/>
                                    <td t-if="!isRefund" class="text-end"><strong t-esc="formatM2(state.totalM2Replaced)"/></td>
                                    <td/>
                                    <td t-if="!isRefund"/>
                                    <td class="text-end">
                                        <strong t-attf-class="rw-diff {{ state.totalDifference &lt; 0 ? 'negative' : 'positive' }}"
                                                t-esc="formatCurrency(state.totalDifference)"/>
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    <div class="rw-footer">
                        <button class="rw-btn rw-btn-secondary" t-on-click="() => this.goBack(1)">
                            <i class="fa fa-arrow-left me-1"/> Atrás
                        </button>
                        <button t-attf-class="rw-btn rw-btn-primary {{ !canGoStep3 ? 'disabled' : '' }}"
                                t-on-click="goToStep3">
                            Revisar <i class="fa fa-arrow-right ms-1"/>
                        </button>
                    </div>
                </div>

                <!-- ==================== STEP 3: Review + Confirm ==================== -->
                <div t-if="state.step === 3" class="rw-content">
                    <div class="rw-review">
                        <div class="rw-review-header">
                            <div class="rw-review-title">Resumen de Reposición</div>
                            <div class="rw-review-so" t-esc="props.saleOrderName"/>
                        </div>

                        <div class="rw-review-grid">
                            <div class="rw-review-card">
                                <div class="rw-review-card-label">Tipo</div>
                                <div class="rw-review-card-value" t-esc="replacementTypeLabel"/>
                            </div>
                            <div class="rw-review-card">
                                <div class="rw-review-card-label">Motivo</div>
                                <div class="rw-review-card-value" t-esc="reasonLabel"/>
                            </div>
                            <div class="rw-review-card">
                                <div class="rw-review-card-label">Devoluciones</div>
                                <div class="rw-review-card-value" t-esc="state.selectedReturnIds.length"/>
                            </div>
                            <div class="rw-review-card">
                                <div class="rw-review-card-label">Cobrar diferencia</div>
                                <div class="rw-review-card-value" t-esc="state.chargeCustomer ? 'Sí' : 'No'"/>
                            </div>
                        </div>

                        <div class="rw-review-totals">
                            <div class="rw-review-total-item">
                                <span>m² Devueltos</span>
                                <strong t-esc="formatM2(state.totalM2Returned)"/>
                            </div>
                            <t t-if="!isRefund">
                                <div class="rw-review-total-item">
                                    <span>m² a Reponer</span>
                                    <strong t-esc="formatM2(state.totalM2Replaced)"/>
                                </div>
                            </t>
                            <div class="rw-review-total-item highlight">
                                <span>Diferencia total</span>
                                <strong t-attf-class="rw-diff {{ state.totalDifference &lt; 0 ? 'negative' : 'positive' }}"
                                        t-esc="formatCurrency(state.totalDifference)"/>
                            </div>
                        </div>

                        <div class="rw-review-lines-title">
                            <t t-esc="state.lines.length"/> líneas de reposición
                        </div>
                        <div class="rw-review-lines">
                            <t t-foreach="state.lines" t-as="line" t-key="line_index">
                                <div class="rw-review-line">
                                    <div class="rw-review-line-product" t-esc="line.productName"/>
                                    <div class="rw-review-line-detail">
                                        <span t-esc="line.m2Returned.toFixed(2)"/> m² dev.
                                        <t t-if="!isRefund">
                                            → <span t-esc="line.m2ToReplace.toFixed(2)"/> m² rep.
                                        </t>
                                    </div>
                                </div>
                            </t>
                        </div>
                    </div>

                    <div class="rw-footer">
                        <button class="rw-btn rw-btn-secondary" t-on-click="() => this.goBack(2)">
                            <i class="fa fa-arrow-left me-1"/> Atrás
                        </button>
                        <button class="rw-btn rw-btn-confirm" t-on-click="onConfirm">
                            <i class="fa fa-check me-1"/> Confirmar Reposición
                        </button>
                    </div>
                </div>
            </div>
        </Dialog>
    </t>

</templates>```

## ./views/menu_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Menú bajo Ventas -->
    <menuitem id="menu_replacements_root"
              name="Reposiciones"
              parent="sale.sale_order_menu"
              sequence="30"
              groups="stonia_replacements.group_replacement_user"/>

    <menuitem id="menu_replacement_orders"
              name="Órdenes de Reposición"
              parent="menu_replacements_root"
              action="action_replacement_order"
              sequence="10"/>

    <!-- Configuración bajo Ventas > Configuración -->
    <menuitem id="menu_replacements_config"
              name="Reposiciones"
              parent="sale.menu_sale_config"
              sequence="90"
              groups="stonia_replacements.group_replacement_admin"/>

    <menuitem id="menu_return_reasons"
              name="Motivos de Devolución"
              parent="menu_replacements_config"
              action="action_return_reason"
              sequence="10"/>

    <menuitem id="menu_replacement_reasons"
              name="Motivos de Reposición"
              parent="menu_replacements_config"
              action="action_replacement_reason"
              sequence="20"/>
</odoo>
```

## ./views/replacement_order_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Sequence -->
    <record id="seq_replacement_order" model="ir.sequence">
        <field name="name">Orden de Reposición</field>
        <field name="code">sale.replacement.order</field>
        <field name="prefix">REP/%(year)s/</field>
        <field name="padding">4</field>
    </record>

    <!-- Form View -->
    <record id="view_replacement_order_form" model="ir.ui.view">
        <field name="name">sale.replacement.order.form</field>
        <field name="model">sale.replacement.order</field>
        <field name="arch" type="xml">
            <form string="Orden de Reposición">
                <header>
                    <button name="action_confirm"
                            string="Confirmar"
                            type="object"
                            class="btn-primary"
                            invisible="state != 'draft'"
                            groups="stonia_replacements.group_replacement_manager"/>
                    <button name="action_create_delivery"
                            string="Crear Entrega"
                            type="object"
                            class="btn-primary"
                            invisible="state != 'confirmed'"
                            groups="stonia_replacements.group_replacement_manager"/>
                    <button name="action_mark_accounting_done"
                            string="Contabilidad Completada"
                            type="object"
                            class="btn-success"
                            invisible="accounting_state != 'pending'"
                            groups="stonia_replacements.group_replacement_admin"/>
                    <button name="action_cancel"
                            string="Cancelar"
                            type="object"
                            invisible="state in ('done', 'cancelled')"
                            groups="stonia_replacements.group_replacement_admin"/>
                    <button name="action_set_to_draft"
                            string="Volver a Borrador"
                            type="object"
                            invisible="state != 'cancelled'"
                            groups="stonia_replacements.group_replacement_admin"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,confirmed,picking_pending,done"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name" readonly="1"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="sale_order_id" readonly="state != 'draft'"/>
                            <field name="partner_id" readonly="1"/>
                            <field name="replacement_type" readonly="state != 'draft'"/>
                            <field name="replacement_reason_id" readonly="state != 'draft'"/>
                        </group>
                        <group>
                            <field name="return_picking_ids" widget="many2many_tags"
                                   readonly="state != 'draft'"/>
                            <field name="out_picking_id" readonly="1"/>
                            <field name="credit_note_id" readonly="1"/>
                            <field name="new_invoice_id" readonly="1"/>
                        </group>
                    </group>

                    <!-- Resumen -->
                    <group>
                        <group string="Totales">
                            <field name="total_m2_returned"/>
                            <field name="total_m2_replaced"/>
                            <field name="total_amount_difference"
                                   decoration-danger="total_amount_difference &lt; 0"
                                   decoration-success="total_amount_difference &gt; 0"/>
                        </group>
                        <group string="Decisión Contable">
                            <field name="original_invoiced" readonly="1"/>
                            <field name="accounting_state" widget="badge"
                                   decoration-success="accounting_state == 'done'"
                                   decoration-warning="accounting_state == 'pending'"/>
                            <field name="charge_difference"
                                   readonly="state not in ('draft', 'confirmed')"/>
                            <field name="no_charge_reason"
                                   invisible="charge_difference == True"
                                   readonly="state not in ('draft', 'confirmed')"/>
                        </group>
                    </group>

                    <notebook>
                        <page string="Líneas de Reposición" name="lines">
                            <field name="line_ids" readonly="state not in ('draft', 'confirmed')">
                                <list editable="bottom">
                                    <field name="original_product_id"/>
                                    <field name="original_lot_ids" widget="many2many_tags"/>
                                    <field name="m2_returned"/>
                                    <field name="product_id"/>
                                    <field name="replacement_lot_ids" widget="many2many_tags"/>
                                    <field name="m2_replaced"/>
                                    <field name="original_unit_price"/>
                                    <field name="unit_price"/>
                                    <field name="amount_difference"
                                           decoration-danger="amount_difference &lt; 0"
                                           decoration-success="amount_difference &gt; 0"/>
                                    <field name="status" widget="badge"
                                           decoration-info="status == 'pending_selection'"
                                           decoration-warning="status == 'pending_delivery'"
                                           decoration-success="status == 'delivered'"/>
                                </list>
                            </field>
                        </page>
                        <page string="Notas" name="notes">
                            <field name="notes"/>
                        </page>
                    </notebook>
                </sheet>
                <chatter/>
            </form>
        </field>
    </record>

    <!-- List View -->
    <record id="view_replacement_order_list" model="ir.ui.view">
        <field name="name">sale.replacement.order.list</field>
        <field name="model">sale.replacement.order</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="sale_order_id"/>
                <field name="partner_id"/>
                <field name="replacement_type"/>
                <field name="replacement_reason_id"/>
                <field name="total_m2_returned"/>
                <field name="total_m2_replaced"/>
                <field name="total_amount_difference"/>
                <field name="state" widget="badge"
                       decoration-success="state == 'done'"
                       decoration-warning="state in ('picking_pending', 'accounting_pending')"
                       decoration-info="state in ('draft', 'confirmed')"
                       decoration-danger="state == 'cancelled'"/>
                <field name="accounting_state" widget="badge"
                       decoration-success="accounting_state == 'done'"
                       decoration-warning="accounting_state == 'pending'"/>
                <field name="create_date"/>
            </list>
        </field>
    </record>

    <!-- Search View -->
    <record id="view_replacement_order_search" model="ir.ui.view">
        <field name="name">sale.replacement.order.search</field>
        <field name="model">sale.replacement.order</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
                <field name="sale_order_id"/>
                <field name="partner_id"/>
                <filter name="draft" string="Borrador" domain="[('state', '=', 'draft')]"/>
                <filter name="confirmed" string="Confirmado" domain="[('state', '=', 'confirmed')]"/>
                <filter name="pending" string="Pendiente entrega"
                        domain="[('state', '=', 'picking_pending')]"/>
                <filter name="accounting" string="Conta. pendiente"
                        domain="[('accounting_state', '=', 'pending')]"/>
                <filter name="done" string="Completado" domain="[('state', '=', 'done')]"/>
                <separator/>
                <filter name="same_product" string="Mismo producto"
                        domain="[('replacement_type', '=', 'same_product')]"/>
                <filter name="different" string="Cambio producto"
                        domain="[('replacement_type', '=', 'different_product')]"/>
                <filter name="refund" string="Devolución dinero"
                        domain="[('replacement_type', '=', 'refund')]"/>
                    <filter name="group_state" string="Estado"
                            context="{'group_by': 'state'}"/>
                    <filter name="group_type" string="Tipo"
                            context="{'group_by': 'replacement_type'}"/>
                    <filter name="group_partner" string="Cliente"
                            context="{'group_by': 'partner_id'}"/>
                    <filter name="group_reason" string="Motivo"
                            context="{'group_by': 'replacement_reason_id'}"/>
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="action_replacement_order" model="ir.actions.act_window">
        <field name="name">Órdenes de Reposición</field>
        <field name="res_model">sale.replacement.order</field>
        <field name="view_mode">list,form</field>
        <field name="search_view_id" ref="view_replacement_order_search"/>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Aún no hay reposiciones
            </p>
            <p>
                Las reposiciones se crean desde un pedido de venta con devoluciones registradas.
            </p>
        </field>
    </record>
</odoo>
```

## ./views/replacement_reason_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_replacement_reason_list" model="ir.ui.view">
        <field name="name">stock.replacement.reason.list</field>
        <field name="model">stock.replacement.reason</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="code"/>
                <field name="active"/>
            </list>
        </field>
    </record>

    <record id="action_replacement_reason" model="ir.actions.act_window">
        <field name="name">Motivos de Reposición</field>
        <field name="res_model">stock.replacement.reason</field>
        <field name="view_mode">list</field>
    </record>
</odoo>
```

## ./views/return_reason_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_return_reason_list" model="ir.ui.view">
        <field name="name">stock.return.reason.list</field>
        <field name="model">stock.return.reason</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="code"/>
                <field name="is_logistics"/>
                <field name="requires_scrap"/>
                <field name="no_physical_return"/>
                <field name="active"/>
            </list>
        </field>
    </record>

    <record id="action_return_reason" model="ir.actions.act_window">
        <field name="name">Motivos de Devolución</field>
        <field name="res_model">stock.return.reason</field>
        <field name="view_mode">list</field>
    </record>
</odoo>
```

## ./views/sale_order_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Botones en SO -->
    <record id="sale_order_form_inherit_replacements" model="ir.ui.view">
        <field name="name">sale.order.form.inherit.replacements</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <!-- Botón de Reposición arriba -->
            <xpath expr="//field[@name='partner_id']/.." position="before">
                <div class="oe_button_box" name="replacement_button_box">
                    <button name="action_create_replacement"
                            type="object"
                            class="oe_stat_button btn-primary"
                            icon="fa-refresh"
                            string="Reposición de Materiales"
                            invisible="state != 'sale'"
                            groups="stonia_replacements.group_replacement_user"/>
                    <button name="action_open_replacements"
                            type="object"
                            class="oe_stat_button"
                            icon="fa-exchange"
                            invisible="replacement_count == 0">
                        <field name="replacement_count" widget="statinfo" string="Reposiciones"/>
                    </button>
                    <button name="action_open_returns"
                            type="object"
                            class="oe_stat_button"
                            icon="fa-undo"
                            invisible="return_count == 0">
                        <field name="return_count" widget="statinfo" string="Devoluciones"/>
                    </button>
                </div>
            </xpath>

            <!-- Sección de Resumen m² -->
            <xpath expr="//field[@name='note']" position="before">
                <separator string="Resumen de Entregas y Reposiciones"
                           invisible="replacement_count == 0"/>
                <group invisible="replacement_count == 0">
                    <group string="Entregas">
                        <field name="total_m2_sold" readonly="1"/>
                        <field name="total_m2_delivered" readonly="1"/>
                    </group>
                    <group string="Devoluciones / Reposiciones">
                        <field name="total_m2_returned" readonly="1"/>
                        <field name="total_m2_replaced" readonly="1"/>
                    </group>
                </group>

                <!-- Tabla de Reposiciones -->
                <field name="replacement_order_ids"
                       invisible="replacement_count == 0"
                       readonly="1"
                       nolabel="1">
                    <list>
                        <field name="name"/>
                        <field name="replacement_type"/>
                        <field name="replacement_reason_id"/>
                        <field name="total_m2_returned" string="m² Devueltos"/>
                        <field name="total_m2_replaced" string="m² Repuestos"/>
                        <field name="total_amount_difference" string="Diferencia"/>
                        <field name="state" widget="badge"
                               decoration-success="state == 'done'"
                               decoration-warning="state in ('picking_pending', 'accounting_pending')"
                               decoration-info="state in ('draft', 'confirmed')"
                               decoration-danger="state == 'cancelled'"/>
                        <field name="accounting_state" widget="badge"
                               decoration-success="accounting_state == 'done'"
                               decoration-warning="accounting_state == 'pending'"/>
                    </list>
                </field>
            </xpath>
        </field>
    </record>

    <!-- Marcar líneas de reposición en la SO -->
    <record id="sale_order_line_form_inherit" model="ir.ui.view">
        <field name="name">sale.order.line.form.inherit.replacements</field>
        <field name="model">sale.order</field>
        <field name="inherit_id" ref="sale.view_order_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='order_line']//list//field[@name='product_id']" position="after">
                <field name="is_replacement" column_invisible="True"/>
            </xpath>
        </field>
    </record>
</odoo>```

## ./views/stock_picking_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="stock_picking_form_inherit_replacements" model="ir.ui.view">
        <field name="name">stock.picking.form.inherit.replacements</field>
        <field name="model">stock.picking</field>
        <field name="inherit_id" ref="stock.view_picking_form"/>
        <field name="arch" type="xml">
            <!-- Botones de devolución y scrap -->
            <xpath expr="//div[@name='button_box']" position="inside">
                <button name="action_create_return_wizard"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-undo"
                        string="Devolver"
                        invisible="state != 'done' or picking_type_code != 'outgoing'"
                        groups="stonia_replacements.group_replacement_user"/>
                <button name="action_scrap_from_return"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-trash"
                        string="Desechar"
                        invisible="is_return_from_delivery != True or state != 'done'"
                        groups="stonia_replacements.group_replacement_user"/>
            </xpath>

            <!-- Campos de devolución -->
            <xpath expr="//field[@name='origin']" position="after">
                <field name="is_return_from_delivery" invisible="1"/>
                <field name="is_replacement_delivery" invisible="1"/>
                <field name="is_logistics_return" invisible="1"/>
                <field name="return_reason_id"
                       invisible="is_return_from_delivery != True"
                       readonly="state == 'done'"/>
                <field name="original_delivery_id"
                       invisible="is_return_from_delivery != True"
                       readonly="1"/>
                <field name="replacement_order_id"
                       invisible="is_replacement_delivery != True"
                       readonly="1"/>
            </xpath>

            <!-- Banner retorno logístico -->
            <xpath expr="//sheet" position="inside">
                <div class="alert alert-warning text-center"
                     role="alert"
                     invisible="is_logistics_return != True">
                    <strong>⚠️ RETORNO LOGÍSTICO</strong> — No se pudo descargar. 
                    Este retorno NO genera nota de crédito automática.
                </div>
                <div class="alert alert-info text-center"
                     role="alert"
                     invisible="is_replacement_delivery != True">
                    <strong>📦 ENTREGA DE REPOSICIÓN</strong> — Material de reemplazo.
                </div>
            </xpath>

            <!-- Notas de devolución -->
            <xpath expr="//page[@name='extra']" position="inside">
                <group string="Información de Devolución"
                       invisible="is_return_from_delivery != True">
                    <field name="return_notes"/>
                </group>
            </xpath>
        </field>
    </record>
</odoo>
```

## ./wizards/__init__.py
```py
from . import return_wizard
from . import replacement_wizard
from . import scrap_from_return_wizard
```

## ./wizards/replacement_wizard_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_replacement_wizard_form" model="ir.ui.view">
        <field name="name">sale.replacement.wizard.form</field>
        <field name="model">sale.replacement.wizard</field>
        <field name="arch" type="xml">
            <form string="Generar Reposición de Materiales">
                <group>
                    <group>
                        <field name="sale_order_id" readonly="1"/>
                        <field name="replacement_type"/>
                        <field name="replacement_reason_id"/>
                    </group>
                    <group>
                        <field name="available_return_picking_ids" invisible="1"/>
                        <field name="return_picking_ids" widget="many2many_tags"
                               required="1"
                               domain="[('id', 'in', available_return_picking_ids)]"
                               options="{'no_create': True}"/>
                        <field name="charge_difference"/>
                        <field name="no_charge_reason"
                               invisible="charge_difference == True"
                               required="charge_difference == False"/>
                    </group>
                </group>
                <separator string="Líneas de Reposición"/>
                <field name="line_ids">
                    <list editable="bottom">
                        <field name="product_id" readonly="1" string="Prod. Original"/>
                        <field name="lot_id" readonly="1" string="Lote devuelto"/>
                        <field name="m2_returned" readonly="1"/>
                        <field name="replacement_product_id" string="Prod. Reposición"/>
                        <field name="m2_to_replace"/>
                        <field name="original_unit_price" readonly="1"/>
                        <field name="replacement_unit_price"/>
                    </list>
                </field>
                <group>
                    <field name="notes" placeholder="Notas internas..."/>
                </group>
                <footer>
                    <button name="action_create_replacement"
                            string="Crear Reposición"
                            type="object"
                            class="btn-primary"/>
                    <button string="Cancelar" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>```

## ./wizards/replacement_wizard.py
```py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleReplacementWizard(models.TransientModel):
    _name = 'sale.replacement.wizard'
    _description = 'Wizard de Reposición de Materiales'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
        required=True,
    )
    return_picking_ids = fields.Many2many(
        'stock.picking',
        string='Devoluciones a reponer',
    )
    available_return_picking_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_available_return_pickings',
        string='Devoluciones disponibles',
    )
    replacement_type = fields.Selection([
        ('same_product', 'Reposición mismo producto'),
        ('different_product', 'Cambio a otro producto'),
        ('refund', 'Devolución de dinero (sin reposición)'),
    ], string='Tipo de reposición', required=True, default='same_product')

    replacement_reason_id = fields.Many2one(
        'stock.replacement.reason',
        string='Motivo de reposición',
        required=True,
    )
    charge_difference = fields.Boolean(
        string='Cobrar diferencia al cliente',
        default=False,
    )
    no_charge_reason = fields.Char(string='Motivo de no cobro')
    line_ids = fields.One2many(
        'sale.replacement.wizard.line',
        'wizard_id',
        string='Líneas',
    )
    notes = fields.Html(string='Notas')

    @api.depends('sale_order_id')
    def _compute_available_return_pickings(self):
        for wiz in self:
            if wiz.sale_order_id:
                # Obtener devoluciones validadas del pedido (custom + estándar)
                wiz.available_return_picking_ids = wiz.sale_order_id._get_return_pickings().filtered(
                    lambda p: p.state == 'done'
                )
            else:
                wiz.available_return_picking_ids = self.env['stock.picking']

    @api.onchange('return_picking_ids', 'replacement_type')
    def _onchange_return_pickings(self):
        """Cargar líneas desde las devoluciones seleccionadas."""
        if not self.return_picking_ids:
            self.line_ids = [(5, 0, 0)]
            return
        lines = []
        for picking in self.return_picking_ids:
            for move in picking.move_ids.filtered(lambda m: m.state == 'done'):
                # Buscar precio original de la línea de venta
                sale_line = move.sale_line_id
                original_price = sale_line.price_unit if sale_line else 0.0
                for move_line in move.move_line_ids:
                    lines.append((0, 0, {
                        'product_id': move.product_id.id,
                        'replacement_product_id': move.product_id.id if self.replacement_type == 'same_product' else False,
                        'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                        'm2_returned': move_line.quantity,
                        'm2_to_replace': move_line.quantity if self.replacement_type != 'refund' else 0,
                        'original_unit_price': original_price,
                        'replacement_unit_price': original_price if self.replacement_type == 'same_product' else 0,
                        'move_id': move.id,
                        'sale_line_id': sale_line.id if sale_line else False,
                    }))
        self.line_ids = [(5, 0, 0)] + lines

    def action_create_replacement(self):
        """Crear la orden de reposición."""
        self.ensure_one()
        if not self.return_picking_ids:
            raise UserError(_('Debe seleccionar al menos una devolución.'))

        # Validar que no haya precios en 0 para reposiciones
        if self.replacement_type != 'refund':
            zero_lines = self.line_ids.filtered(
                lambda l: l.replacement_unit_price <= 0 and l.m2_to_replace > 0
            )
            if zero_lines and not self.env.user.has_group(
                'stonia_replacements.group_replacement_admin'
            ):
                raise UserError(_(
                    'No se permite crear reposiciones con precio $0.00. '
                    'Las diferencias deben manejarse con notas de crédito.'
                ))

        # Marcar los pickings de devolución si no están marcados
        for picking in self.return_picking_ids:
            if not picking.is_return_from_delivery:
                picking.is_return_from_delivery = True

        # Crear orden de reposición
        replacement = self.env['sale.replacement.order'].create({
            'sale_order_id': self.sale_order_id.id,
            'return_picking_ids': [(6, 0, self.return_picking_ids.ids)],
            'replacement_type': self.replacement_type,
            'replacement_reason_id': self.replacement_reason_id.id,
            'charge_difference': self.charge_difference,
            'no_charge_reason': self.no_charge_reason,
            'notes': self.notes,
        })

        # Crear líneas
        for line in self.line_ids:
            self.env['sale.replacement.order.line'].create({
                'replacement_order_id': replacement.id,
                'original_product_id': line.product_id.id,
                'original_lot_ids': [(6, 0, [line.lot_id.id])] if line.lot_id else False,
                'm2_returned': line.m2_returned,
                'product_id': line.replacement_product_id.id or line.product_id.id,
                'm2_replaced': line.m2_to_replace,
                'original_unit_price': line.original_unit_price,
                'unit_price': line.replacement_unit_price,
                'sale_line_id': line.sale_line_id.id,
                'return_move_id': line.move_id.id,
            })

        # Confirmar automáticamente
        replacement.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reposición de Materiales'),
            'res_model': 'sale.replacement.order',
            'res_id': replacement.id,
            'view_mode': 'form',
            'target': 'current',
        }


class SaleReplacementWizardLine(models.TransientModel):
    _name = 'sale.replacement.wizard.line'
    _description = 'Línea de Wizard de Reposición'

    wizard_id = fields.Many2one(
        'sale.replacement.wizard',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto original',
    )
    replacement_product_id = fields.Many2one(
        'product.product',
        string='Producto de reposición',
    )
    lot_id = fields.Many2one('stock.lot', string='Lote devuelto')
    m2_returned = fields.Float(string='m² devueltos')
    m2_to_replace = fields.Float(string='m² a reponer')
    original_unit_price = fields.Float(string='Precio original')
    replacement_unit_price = fields.Float(string='Precio reposición')
    move_id = fields.Many2one('stock.move', string='Movimiento')
    sale_line_id = fields.Many2one('sale.order.line', string='Línea de venta')```

## ./wizards/return_wizard_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_return_wizard_form" model="ir.ui.view">
        <field name="name">stock.return.wizard.form</field>
        <field name="model">stock.return.wizard</field>
        <field name="arch" type="xml">
            <form string="Devolver Material">
                <group>
                    <group>
                        <field name="picking_id" readonly="1"/>
                        <field name="sale_order_id" readonly="1"/>
                    </group>
                    <group>
                        <field name="return_reason_id"/>
                        <field name="is_logistics_return" invisible="1"/>
                        <field name="no_physical_return" invisible="1"/>
                    </group>
                </group>
                <div class="alert alert-warning"
                     role="alert"
                     invisible="is_logistics_return != True">
                    <strong>⚠️ Retorno logístico:</strong> No se generará nota de crédito automática.
                </div>
                <div class="alert alert-danger"
                     role="alert"
                     invisible="no_physical_return != True">
                    <strong>⚠️ Sin retorno físico:</strong> El material no regresa al almacén.
                    Se registrará como evento de pérdida controlado.
                </div>
                <field name="line_ids">
                    <list editable="bottom">
                        <field name="to_return" widget="boolean_toggle"/>
                        <field name="product_id" readonly="1"/>
                        <field name="lot_id" readonly="1"/>
                        <field name="qty_delivered" readonly="1"/>
                        <field name="qty_to_return"/>
                    </list>
                </field>
                <group>
                    <field name="total_m2" readonly="1"/>
                    <field name="notes" placeholder="Notas adicionales sobre la devolución..."/>
                </group>
                <footer>
                    <button name="action_confirm_return"
                            string="Confirmar Devolución"
                            type="object"
                            class="btn-primary"/>
                    <button string="Cancelar" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

## ./wizards/return_wizard.py
```py
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockReturnWizard(models.TransientModel):
    _name = 'stock.return.wizard'
    _description = 'Wizard de Devolución de Material'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Entrega',
        required=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Pedido de Venta',
    )
    return_reason_id = fields.Many2one(
        'stock.return.reason',
        string='Motivo de devolución',
        required=True,
    )
    is_logistics_return = fields.Boolean(
        string='Retorno logístico',
        related='return_reason_id.is_logistics',
        readonly=True,
    )
    no_physical_return = fields.Boolean(
        string='Sin retorno físico',
        related='return_reason_id.no_physical_return',
        readonly=True,
    )
    notes = fields.Text(string='Notas')
    line_ids = fields.One2many(
        'stock.return.wizard.line',
        'wizard_id',
        string='Líneas a devolver',
    )
    total_m2 = fields.Float(
        string='Total m² a devolver',
        compute='_compute_total_m2',
    )

    @api.depends('line_ids.qty_to_return')
    def _compute_total_m2(self):
        for wiz in self:
            wiz.total_m2 = sum(wiz.line_ids.filtered('to_return').mapped('qty_to_return'))

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        """Cargar líneas desde la entrega con lotes entregados."""
        if not self.picking_id:
            return
        lines = []
        for move in self.picking_id.move_ids.filtered(lambda m: m.state == 'done'):
            for move_line in move.move_line_ids:
                lines.append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                    'qty_delivered': move_line.quantity,
                    'qty_to_return': move_line.quantity,
                    'to_return': False,
                }))
        self.line_ids = lines

    def action_confirm_return(self):
        """Crear el picking de devolución."""
        self.ensure_one()
        lines_to_return = self.line_ids.filtered('to_return')
        if not lines_to_return:
            raise UserError(_('Debe seleccionar al menos un producto para devolver.'))
        if not self.return_reason_id:
            raise UserError(_('Debe indicar un motivo de devolución.'))

        picking = self.picking_id
        picking_type = picking.picking_type_id.return_picking_type_id or picking.picking_type_id

        # Crear picking de devolución
        return_picking_vals = {
            'picking_type_id': picking_type.id,
            'partner_id': picking.partner_id.id,
            'origin': _('Devolución de %s') % picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': picking.location_id.id,
            'sale_id': self.sale_order_id.id,
            'is_return_from_delivery': True,
            'return_reason_id': self.return_reason_id.id,
            'return_notes': self.notes,
            'is_logistics_return': self.return_reason_id.is_logistics,
            'original_delivery_id': picking.id,
        }
        return_picking = self.env['stock.picking'].create(return_picking_vals)

        for line in lines_to_return:
            self.env['stock.move'].create({
                'name': _('Devolución: %s') % line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty_to_return,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': return_picking.id,
                'location_id': picking.location_dest_id.id,
                'location_dest_id': picking.location_id.id,
                'origin_returned_move_id': line.move_id.id,
            })

        return_picking.action_confirm()

        # Si es sin retorno físico, marcar para scrap directo
        if self.return_reason_id.no_physical_return:
            return_picking.message_post(
                body=_('⚠️ Devolución sin retorno físico. '
                       'El material debe registrarse como merma/scrap.')
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Devolución'),
            'res_model': 'stock.picking',
            'res_id': return_picking.id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockReturnWizardLine(models.TransientModel):
    _name = 'stock.return.wizard.line'
    _description = 'Línea de Wizard de Devolución'

    wizard_id = fields.Many2one(
        'stock.return.wizard',
        required=True,
        ondelete='cascade',
    )
    to_return = fields.Boolean(string='Devolver', default=False)
    move_id = fields.Many2one('stock.move', string='Movimiento')
    product_id = fields.Many2one('product.product', string='Producto')
    lot_id = fields.Many2one('stock.lot', string='Lote/Placa')
    qty_delivered = fields.Float(string='m² entregados')
    qty_to_return = fields.Float(string='m² a devolver')
```

## ./wizards/scrap_from_return_wizard_views.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_scrap_from_return_wizard_form" model="ir.ui.view">
        <field name="name">stock.scrap.from.return.wizard.form</field>
        <field name="model">stock.scrap.from.return.wizard</field>
        <field name="arch" type="xml">
            <form string="Desechar desde Devolución">
                <group>
                    <field name="return_picking_id" readonly="1"/>
                    <field name="scrap_reason" placeholder="Motivo del desecho (obligatorio)..."/>
                </group>
                <separator string="Material a Desechar"/>
                <field name="line_ids">
                    <list editable="bottom">
                        <field name="to_scrap" widget="boolean_toggle"/>
                        <field name="product_id" readonly="1"/>
                        <field name="lot_id" readonly="1"/>
                        <field name="qty_available" readonly="1"/>
                        <field name="qty_to_scrap"/>
                    </list>
                </field>
                <footer>
                    <button name="action_scrap"
                            string="Desechar Material"
                            type="object"
                            class="btn-danger"/>
                    <button string="Cancelar" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
```

## ./wizards/scrap_from_return_wizard.py
```py
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
```

