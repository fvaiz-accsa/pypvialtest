from odoo import models, fields, api
from zeep import Client
from zeep.wsse.username import UsernameToken
import xml.etree.ElementTree as ET
import pathlib
import os
import base64
from odoo.exceptions import ValidationError



class fc_pagoregistrar(models.TransientModel):
    _inherit = 'account.payment.register'
    tipoCFE_w = fields.Selection([('182', 'e-Resguardo')], string='Tipo Comprobante')
    retenciones_w = fields.Many2one(string='Retenciones', comodel_name='fc_pyp.fc_codigos')

    ### CHEQUES / PAGOS ###
    referencia = fields.Char(string='Referencia')
    fechaEmision = fields.Date(string='Fecha Emisión ')
    fechaVencimiento = fields.Date(string='Fecha Vencimiento')
    isCheque = fields.Boolean(string='Es Cheque')
    banco_id = fields.Many2one('res.bank', string='Banco')
    estadoCheque = fields.Selection([('0', 'Por Cobrar'), ('1', 'Cobrado'), ('2', 'Rechazado '),
                                     ('3', 'Anulado')], string='Estado Cheque')

    #list_cheq_id = fields.One2many('fc_pyp.fc_pago_cheque', 'cheq_id', 'Cheques')

    @api.model
    def afun(self):
        len(self)
        print('afun', self.journal_id.cheques)

    @api.onchange('journal_id')
    def _onchangeJournal(self):
        self.isCheque = self.journal_id.cheques
        if(self.isCheque == False):
            self.referencia = False
            self.estadoCheque = False
            self.fechaEmision = False
            self.fechaVencimiento = False
            self.banco_id = False
        print('onchange',str(self.isCheque))

    ###########

    def _create_payment_vals_from_wizard(self):
        payment_vals = super()._create_payment_vals_from_wizard()
        ##############
        mensaje = ''
        factura = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
        if (factura.customerRUT == False): mensaje = mensaje + '- Cliente / Documento \n'
        cliente = self.env['res.partner'].browse([factura.partner_id.id])
        if (cliente.country_id.id  == False): mensaje = mensaje + '- Cliente / País \n'
        print(mensaje)

        ###########

        print('Create Context')
        self.env.context = dict(self.env.context)
        self.env.context.update({'tipoCFE_wiz': self.tipoCFE_w,
                                 'payment_date_wiz': self.payment_date,
                                'amount_wiz': self.amount,
                                 'currency_id_wiz': self.currency_id.id,
                                 'communication': self.communication,
                                 'cliente_id': cliente.id,
                                 'retenciones_wiz': self.retenciones_w,
                                 'ischeque_wiz': self.journal_id.cheques,
                                 'referenciaCheque': self.referencia,
                                 'fechaEmisionCheque': self.fechaEmision,
                                 'fechaFencimientoCheque': self.fechaVencimiento,
                                 'estadoCheque': self.estadoCheque,
                                 'banco_idCheque': self.banco_id})
        print('Fin Context')
        print('Contexto', self._context)

        return payment_vals

    def camposObligatorios_eResg(self):
        mensaje = ''
        factura = self.env[self._context.get('active_model')].browse([self._context.get('active_id')])
        if (factura.customerRUT == False): mensaje = mensaje + '- Cliente / Documento \n'
        cliente = self.env['res.partner'].browse([factura.partner_id.id])
        if (cliente.country_id.id  == False): mensaje = mensaje + '- Cliente / País \n'
        print(mensaje)
        return mensaje
