from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
class diferenciacambio(models.Model):
    _name = 'fc_pyp_add.diferenciacambio'
    _description = 'Definicion para el caluclo de diferencia de cambio'

    fecha_DC = fields.Date(string='Fecha de DC')
    tipo_cambio = fields.Float(string='Tipo Cambio', digits=(4,12))
    year = fields.Integer(string='Año')
    activo = fields.Boolean(string='Activo', default=True)


    @api.onchange('fecha_DC')
    def _onchange_fecha_DC(self):
        if(self.fecha_DC != False):
            if self.fecha_DC > datetime.now().date():
                raise ValidationError("La fecha no puede ser mayor a la fecha de hoy")
            td = timedelta(30)
            dia_anterior = self.fecha_DC - td
            print(dia_anterior)
            tipocambio = self.env['res.currency.rate'].search([('name', '>=', dia_anterior), ('name', '<', self.fecha_DC)],order='name desc', limit=1)
            if(tipocambio.id == False):
                tipocambio = self.env['res.currency.rate'].search([('name', '<', self.fecha_DC)],order='name desc', limit=1)
            print(tipocambio.id)
            self.tipo_cambio = tipocambio.rate
            self.year = self.fecha_DC.year

    # @api.constrains('fecha_DC')
    # def _check_fecha_DC(self):
    #     for record in self:
    #         if self.fecha_DC > datetime.now().date():
    #             raise ValidationError("La fecha no puede ser mayor a la fecha de hoy")
    #         tipocambioanio = self.env['res.currency.rate'].search([('year', '=', self.year)], limit=1)
    #         print(tipocambioanio)
    #         # if tipocambioanio.id:
    #         #     raise ValidationError("Ya existe un campo para la diferencia de cambio de este año")