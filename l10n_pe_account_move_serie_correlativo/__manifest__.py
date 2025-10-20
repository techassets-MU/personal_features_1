# -*- coding: utf-8 -*-
{
	'name': 'Perú: Serie y Correlativo en Facturas',
	'code': 'l10n_pe_account_move_serie_correlativo',
	'version': '18.0.1.0.0',
	'category': 'Accounting/Localizations',
	'summary': 'Campos x_serie y x_correlativo en account.move con visualización y unicidad por diario',
	'author': 'Paul Chipana',
	'license': 'LGPL-3',
	'depends': [
		'account',
		'l10n_latam_invoice_document',
	],
	'data': [
		'views/account_move_views.xml',
	],
	'installable': True,
	'application': False,
}
