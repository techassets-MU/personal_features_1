from odoo import api, fields, models
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    qr_image = fields.Binary(
        string='QR Image',
        compute='_compute_qr_image',
        store=True,
        attachment=True,
        help='Imagen PNG del código QR generado para el comprobante.'
    )

    @api.depends('x_serie_correlativo', 'partner_id.name', 'x_date_time_issuance', 'amount_total')
    def _compute_qr_image(self) -> None:
        report_model = self.env['ir.actions.report']
        for move in self:
            try:
                numero = getattr(move, 'x_serie_correlativo', '') or ''
                cliente = move.partner_id.name or ''
                fecha = ''
                if hasattr(move, 'x_date_time_issuance') and move.x_date_time_issuance:
                    # ISO 8601 recomendado
                    fecha = move.x_date_time_issuance.isoformat()
                total_pagar = ('%.2f' % move.amount_total) if move.amount_total else ''

                # TOTAL_CANTIDADES_DE_LINEA y TOTAL_A_PAGAR iguales (amount_total)
                qr_value = '|'.join([numero, cliente, fecha, total_pagar, total_pagar])

                if qr_value.strip('|'):
                    png_bytes = report_model.barcode('QR', qr_value, width=60, height=60)
                    move.qr_image = base64.b64encode(png_bytes)
                else:
                    move.qr_image = False
            except Exception:
                move.qr_image = False


