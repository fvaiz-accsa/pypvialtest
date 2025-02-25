# -*- coding: utf-8 -*-
# from odoo import http


# class CustomAddons/fcPypAdd/(http.Controller):
#     @http.route('/custom_addons/fc_pyp_add//custom_addons/fc_pyp_add//', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_addons/fc_pyp_add//custom_addons/fc_pyp_add//objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_addons/fc_pyp_add/.listing', {
#             'root': '/custom_addons/fc_pyp_add//custom_addons/fc_pyp_add/',
#             'objects': http.request.env['custom_addons/fc_pyp_add/.custom_addons/fc_pyp_add/'].search([]),
#         })

#     @http.route('/custom_addons/fc_pyp_add//custom_addons/fc_pyp_add//objects/<model("custom_addons/fc_pyp_add/.custom_addons/fc_pyp_add/"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_addons/fc_pyp_add/.object', {
#             'object': obj
#         })
