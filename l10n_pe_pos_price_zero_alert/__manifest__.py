{
    'name': 'POS: Alerta precio S/ 0.0 al validar pago',
    'summary': 'Confirma cuando hay líneas con precio 0.0 al validar el pago en POS',
    'version': '18.0.1.0.0',
    'author': 'Paul Chipana',
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            (
                'after',
                'point_of_sale/static/src/app/screens/payment_screen/payment_screen.js',
                'l10n_pe_pos_price_zero_alert/static/src/overrides/payment_zero_price_validation.js',
            ),
        ],
    },
    'installable': True,
    'application': False,
}


