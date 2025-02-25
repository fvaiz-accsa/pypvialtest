from odoo import models, fields, api

class Account_journal(models.Model):
    _inherit = 'account.journal'
    cheques = fields.Boolean(string='Cheques')