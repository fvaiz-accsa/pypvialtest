from odoo import models, fields, api

class CustomNotaCredito(models.TransientModel):
    _inherit = 'account.move.reversal'
    tipoCFE_NC = fields.Selection(
        [('102', '102 Nota de Crédito de e-Ticket'), ('112', '112 Nota de Crédito de e-Factura')],
        string='Tipo Comprobante')