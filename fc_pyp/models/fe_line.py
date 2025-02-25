from odoo import models, fields, api

## FE Lines
class fe_line(models.Model):
    _name = 'fc_pyp.fe_line'
    _description = 'FE_Line'

    Number = fields.Char(string='Number')
    RtaMessage = fields.Char(string='RtaMessage')
    RtaCode = fields.Char(string='RtaCode')
    Series = fields.Char(string='Series')
    Uuid = fields.Char(string='Identificador')
    xmlText = fields.Text(string='XML')
    line_attachment_id = fields.Many2one('ir.attachment', 'PDF')
    cfe_id = fields.Many2one('account.move', 'Factura')
    pay_id = fields.Many2one('account.payment', 'Pago')
