{
    'name': 'PE: Fecha de emisión en account.move',
    'summary': 'Reemplaza Fecha por Fecha de emisión (con hora) en facturas',
    'version': '18.0.1.0.0',
    'author': 'Paul Chipana',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
