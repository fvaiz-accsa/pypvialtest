# -*- coding: utf-8 -*-
# from odoo import http

#testing
# class FcPyp(http.Controller):
#     @http.route('/fc_pyp/fc_pyp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fc_pyp/fc_pyp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fc_pyp.listing', {
#             'root': '/fc_pyp/fc_pyp',
#             'objects': http.request.env['fc_pyp.fc_pyp'].search([]),
#         })

#     @http.route('/fc_pyp/fc_pyp/objects/<model("fc_pyp.fc_pyp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fc_pyp.object', {
#             'object': obj
#         })


