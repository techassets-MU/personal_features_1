# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class AccountMove(models.Model):
	_inherit = 'account.move'

	x_serie = fields.Char(
		string='Serie (PE)',
		readonly=True,
		copy=False,
		index=True,
	)
	x_correlativo = fields.Char(
		string='Correlativo (PE)',
		readonly=True,
		copy=False,
		index=True,
	)
	x_serie_correlativo = fields.Char(
		string='Serie-Correlativo',
		compute='_compute_serie_correlativo_display',
		readonly=True,
	)

	_sql_constraints = [
		(
			'uniq_journal_serie_correlativo',
			'unique(journal_id, x_serie, x_correlativo)',
			'La combinación Serie + Correlativo debe ser única por diario.',
		),
	]

	@staticmethod
	def _parse_serie_correlativo_from_name(name):
		"""Mantener utilitario si se requiere parseo futuro de cadenas externas."""
		if not name:
			return None, None
		last_num_match = re.search(r'(\d+)(?!.*\d)', name)
		if not last_num_match:
			return None, None
		correlativo_raw = last_num_match.group(1)
		correlativo = correlativo_raw if len(correlativo_raw) >= 8 else correlativo_raw.zfill(8)
		serie_part = name[: last_num_match.start()]
		serie_clean = re.sub(r'[^A-Za-z0-9]', '', serie_part) or None
		serie = serie_clean.upper() if serie_clean else None
		return serie, correlativo

	def action_post(self):
		res = super().action_post()
		# Generar serie y correlativo SOLO tras postear facturas de cliente
		for move in self.filtered(lambda m: m.state == 'posted' and m.move_type in ('out_invoice',)):
			# No sobrescribir si ya existe
			if move.x_serie and move.x_correlativo:
				continue
			# Requisitos mínimos: diario y tipo de documento
			doc_type = getattr(move, 'l10n_latam_document_type_id', False)
			if not (doc_type and doc_type.code and move.journal_id):
				continue
			journal_code = (move.journal_id.code or '').strip().upper()
			doc_code = (doc_type.code or '').strip().upper()
			serie = f"{journal_code}-{doc_code}" if journal_code else doc_code
			# Obtener el máximo correlativo ya usado para este diario y serie
			self.env.cr.execute(
				"""
				SELECT MAX(CAST(m.x_correlativo AS INTEGER))
				FROM account_move m
				WHERE m.journal_id = %s
				  AND m.x_serie = %s
				  AND m.state = 'posted'
				""",
				(move.journal_id.id, serie),
			)
			row = self.env.cr.fetchone()
			max_num = (row[0] if row and row[0] is not None else 0)
			next_num = max_num + 1
			move.write({
				'x_serie': serie,
				'x_correlativo': str(next_num).zfill(8),
			})
		return res

	@api.depends('x_serie', 'x_correlativo')
	def _compute_serie_correlativo_display(self):
		for move in self:
			if move.x_serie and move.x_correlativo:
				move.x_serie_correlativo = f"{move.x_serie}-{move.x_correlativo}"
			elif move.x_serie:
				move.x_serie_correlativo = move.x_serie
			elif move.x_correlativo:
				move.x_serie_correlativo = move.x_correlativo
			else:
				move.x_serie_correlativo = False
