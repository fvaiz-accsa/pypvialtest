from odoo import models, fields, api
from zeep import Client
from zeep.wsse.username import UsernameToken
import xml.etree.ElementTree as ET
import pathlib
import os
import base64
from odoo.exceptions import ValidationError

class fc_tipoCambio(models.Model):
    _inherit = 'res.currency'

    def getTipoCambio(self, currecy_id):
        # Currency
        moneda = self.env['res.currency'].browse([self.currecy_id])
        print(moneda)