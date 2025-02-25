from odoo import models, fields, api

## fe_pago_cheque
class fc_pago_cheque(models.Model):
    _name = 'fc_pyp.fc_pago_cheque'
    _description = 'fc_pago_cheque'

    referenciaPago = fields.Char(string='Referencia')
    fechaEmisionPago = fields.Date(string='Fecha Emisión ')
    fechaVencimientoPago = fields.Date(string='Fecha Vencimiento')
    isChequePago = fields.Boolean(string='Es Cheque')
    bancoPago_id = fields.Many2one('res.bank', string='Banco')
    currency_id = fields.Many2one('res.currency', string='Currency')
    estadoChequePago = fields.Selection([('0', 'Por Cobrar'), ('1', 'Cobrado'), ('2', 'Rechazado '),
                                     ('3', 'Anulado')], string='Estado Cheque')

    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id)
    valor = fields.Monetary(string="Valor")
    cheq_id = fields.Many2one('account.payment', 'Pago')

    # @api.model
    # def create(self, values):
    #     res = super(fc_pago_cheque, self).create(values)
    #     self.env.context = dict(self.env.context)
    #     print('Contexto', self._context)
    #     # here you can do accordingly
    #     return res