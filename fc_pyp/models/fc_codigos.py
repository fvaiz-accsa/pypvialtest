from odoo import models, fields, api

## FE Lines
class fc_codigos(models.Model):
    _name = 'fc_pyp.fc_codigos'
    _description = 'fc_codigos'

    codigo = fields.Char(string='Código', required=True)
    name = fields.Char(string='Descripción', required=True)

    # @api.model
    # def create(self, values):
    #     print(values)
    #
    #     values['display_name'] = self.descripcion
    #     res = super(fc_codigos, self).create(values)
    #     return res

    # @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    # def _compute_display_name(self):
    #     #names = dict(self.name_get())
    #     for record in self:
    #         record.display_name = self.descripcion #names.get(record.id, False)