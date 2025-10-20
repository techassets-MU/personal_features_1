from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_date_time_issuance = fields.Datetime(
        string='Fecha de emisión',
        help='Fecha y hora de emisión del comprobante.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.is_invoice(include_receipts=True) and not move.x_date_time_issuance:
                move.x_date_time_issuance = fields.Datetime.now()
        return moves

    def action_post(self):
        for move in self:
            if move.is_invoice(include_receipts=True) and not move.x_date_time_issuance:
                move.x_date_time_issuance = fields.Datetime.now()
        return super().action_post()
