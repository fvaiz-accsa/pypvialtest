from odoo import models, fields, api

## Settings
class fe_settings(models.Model):
    _name = 'fc_pyp.settings_fc'
    _description = 'Settings_FC'

    url = fields.Char(string='URL')
    usuario = fields.Char(string='Usuario')
    clave = fields.Char(string='Clave')
    comercio = fields.Char(string='Comercio')
    terminal = fields.Char(string='Terminal')
    activo = fields.Boolean(string='Activo')
    timeout = fields.Char(string='TimeOut')