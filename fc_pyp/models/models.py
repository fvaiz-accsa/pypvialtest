from odoo import models, fields, api
from zeep import Client
from zeep.wsse.username import UsernameToken
import xml.etree.ElementTree as ET
import pathlib
import os
import base64
from odoo.exceptions import ValidationError

class CustomSaleOrder(models.Model):
    _inherit = 'sale.order'
    leyesSociales = fields.Monetary(string='Leyes Sociales')

    @api.depends('leyesSociales')
    def _amount_all(self):
        res = super(CustomSaleOrder, self)._amount_all()
        for order in self:
            order.amount_total += order.leyesSociales
            print(order.amount_total)
        return res

# class CustomAccountPayment(models.Model):
#     _inherit = 'account.payment'


