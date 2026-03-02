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
}