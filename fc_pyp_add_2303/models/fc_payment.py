from odoo import models, fields, api
from odoo.exceptions import ValidationError
#import models.numero_letras
from . import numero_letras


class fc_payment(models.Model):
    _inherit = 'account.payment'

    # def create(self, cr, uid, vals, context=None):
    #     new_id = super(fc_payment, self).create(cr, uid, vals, context=context)
    #     print("pesos")
    #     self.description = "Pesos uruguayos cuantos"
    #     # lead = self.browse(cr, uid, new_id, context=context)
    #     # self._compute_stage_deadline(cr, uid, lead, context)
    #     return new_id

    @api.model
    def create(self, vals):
        currency_id = vals["currency_id"]
        amount = vals["amount"]
        valor = numero_letras.numero_a_letras(amount)
        curr_rec = self.env['res.currency'].search([('id', '=', currency_id)])
        texto = "Son " + curr_rec.currency_unit_label + " " + valor + ".-"
        vals["descripcion"] = texto
        rec = super(fc_payment, self).create(vals)
        return rec

    def action_numToText(self):
        valor = numero_letras.numero_a_letras(self.amount)
        curr_id = self.currency_id
        curr_rec = self.env['res.currency'].search([('id', '=', curr_id.id)])
        texto = "Son " + curr_rec.currency_unit_label + " " + valor + ".-"
        self.write({'descripcion': texto})