# -*- coding: utf-8 -*-
# from odoo import http


# class AjedrezXrm(http.Controller):
#     @http.route('/ajedrez_xrm/ajedrez_xrm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ajedrez_xrm/ajedrez_xrm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ajedrez_xrm.listing', {
#             'root': '/ajedrez_xrm/ajedrez_xrm',
#             'objects': http.request.env['ajedrez_xrm.ajedrez_xrm'].search([]),
#         })

#     @http.route('/ajedrez_xrm/ajedrez_xrm/objects/<model("ajedrez_xrm.ajedrez_xrm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ajedrez_xrm.object', {
#             'object': obj
#         })
