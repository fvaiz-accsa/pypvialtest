from odoo import models, fields, api
from datetime import datetime
class facturas(models.Model):
    _inherit = 'account.move'

    calculoDC = fields.Float(string='Caluclo DC')
    calculoDC_fecha = fields.Date(string='Fecha DC')

    actualizarDC_fecha = fields.Date(string='Fecha DC')

    def actulizarMasivoCalculoDC(self):
        inv_ids = self.env['account.move'].browse(self.env.context.get('active_ids'))
        try:
            for inv in inv_ids:
                inv.actulizarCaluloDC()
        except Exception as e:
            raise print('Error: /n' + str(e))

    def actulizarCaluloDC(self):
        # Diferencia de Cambio
        if(self.currency_id.id == 2):
            tipocambio = self.env['fc_pyp_add.diferenciacambio'].search([('activo', '=', True)], order='fecha_DC desc', limit=1)
            print(tipocambio)
            if tipocambio:
                rate_usd = tipocambio.tipo_cambio
                dc = (self.amount_residual / rate_usd) - self.amount_residual_signed
                self.write({'calculoDC': dc, 'calculoDC_fecha': tipocambio.fecha_DC})
        else:
            self.write({'calculoDC': 0, 'calculoDC_fecha': datetime.today()})

        # rate_usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).rate
        # dc = (self.amount_residual_signed * rate_usd) - self.amount_residual
        # self.write({'calculoDC': dc, 'calculoDC_fecha': datetime.today()})

    def obtenertipocambio(self):
        tipocambio = self.env['fc_pyp_add.diferenciacambio'].search([],order='fecha_DC desc', limit=1)