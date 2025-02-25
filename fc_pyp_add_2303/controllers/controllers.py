# -*- coding: utf-8 -*-
# from odoo import http


# class FcPypAdd2303(http.Controller):
#     @http.route('/fc_pyp_add_2303/fc_pyp_add_2303/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fc_pyp_add_2303/fc_pyp_add_2303/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fc_pyp_add_2303.listing', {
#             'root': '/fc_pyp_add_2303/fc_pyp_add_2303',
#             'objects': http.request.env['fc_pyp_add_2303.fc_pyp_add_2303'].search([]),
#         })

#     @http.route('/fc_pyp_add_2303/fc_pyp_add_2303/objects/<model("fc_pyp_add_2303.fc_pyp_add_2303"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fc_pyp_add_2303.object', {
#             'object': obj
#         })
