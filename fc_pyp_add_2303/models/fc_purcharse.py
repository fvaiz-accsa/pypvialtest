# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
#import models.numero_letras
from . import numero_letras


class fc_purcharse(models.Model):
    _inherit = 'purchase.order'

    estado = fields.Selection(selection=[
                             ('draft','Petición presupuesto'),
                             ('sent', 'Solicitud de presupuesto enviada'),
                             ('pre_approved', 'Para Pre-Aprobar'),
                             ('to approve', 'Para Aprobar'),
                             ('purchase', 'Pedido de compra'),
                             ('done', 'Bloqueado'),
                             ('cancel', 'Cancelado')
                            ], string='Estatus', default='draft')

    preAprobador = fields.Many2one('res.users', string="PreAprobador por")
    aprobador = fields.Many2one('res.users', string="Aprobador por")

    #dsn_amount_in_words = fields.Char(string='Amount in Words')
    # dsn_amount_in_words = fields.Char(string='Amount in Words',
    #                                   compute='_amount_to_words',
    #                                   store=True)
    def action_confirmar(self):
        self.write({'estado': 'pre_approved'})

    def button_confirm(self):
        super(fc_purcharse, self).button_confirm()
        context = self._context
        current_uid = context.get('uid')
        self.write({'preAprobador': current_uid})

    def button_approve(self):
        super(fc_purcharse, self).button_approve()
        context = self._context
        current_uid = context.get('uid')
        self.write({'aprobador': current_uid})

    def update_estado(self):
        log = 'ppla'
        estado_preaApro = 'pre_approved'
        purcharse_rec = self.env['purchase.order'].search([('estado', '!=', estado_preaApro)])
        users_rec = self.env['res.users'].search([('login', '=', log)])
        for purch in purcharse_rec:
            status = purch.state
            if users_rec:
                purch.update({
                    'estado': status,
                    'preAprobador': users_rec,
                     'aprobador': users_rec,
                })
            elif purch.estado != "pre_approved":
                purch.update({
                    'estado': status,
                })
    # @api.depends('amount_total')
    # def _amount_to_words(self):
    #     self.dsn_amount_in_words = models.numero_a_letras(8)

    # def _get_product_purchase_description(self):
    #     print("Prueba")
    #     res = super(fc_purcharse, self)._get_product_purchase_description()
    #     return res
    #
    # @api.onchange('product_id')
    # def product_id_change(self):
    #     res = super(fc_purcharse, self).product_id_change()
    #     print("Test")
    #     vals = {}
    #     if self.product_id.default_code:
    #         vals['name'] = self.product_id.name + " [" + self.product_id.default_code + "]"
    #     self.update(vals)
    #     return res

    # def _onchange_state(self):
    #     print('_onchange_state ' + self.state)
    #     self.write({'estado': self.state})

    # @api.onchange(lgs)
    # def on_change_state(self):
    #     for record in self:
    #         if record.lgs:
    #             record.state = 'waiting'
    #         else:
    #             record.state = 'draft'
    #         print
    #         self.state, self.lgs