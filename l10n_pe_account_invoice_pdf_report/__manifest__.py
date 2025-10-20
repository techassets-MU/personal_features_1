{
    'name': 'Peru - Formato de Factura de Venta en PDF',
    'version': '1.0',
    'summary': 'Formato de Factura de Venta en PDF para la localización peruana. Segun ejericicio SAMEMOTION',
    'description': """
        Este módulo permite generar el formato de factura de venta en PDF
        desde el módulo de facturas de venta (account.move).
        para la localización peruana.
    """,
    'author': 'Paul Chipana',
    'license': 'LGPL-3',
    'depends': ['account', 'account_accountant', 'web', 'l10n_pe_reports', 'l10n_pe_edi', 'l10n_latam_invoice_document', 'l10n_pe_edi',
        'l10n_pe_account_move_serie_correlativo',
        'l10n_pe_account_move_emission_datetime',
    ],
    'data': [
        'report/report_invoice_document.xml',
    ],
    'installable': True,
    'application': False,
}