# -*- coding: utf-8 -*-
from odoo import http

# class SyncLdap(http.Controller):
#     @http.route('/sync_ldap/sync_ldap/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sync_ldap/sync_ldap/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sync_ldap.listing', {
#             'root': '/sync_ldap/sync_ldap',
#             'objects': http.request.env['sync_ldap.sync_ldap'].search([]),
#         })

#     @http.route('/sync_ldap/sync_ldap/objects/<model("sync_ldap.sync_ldap"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sync_ldap.object', {
#             'object': obj
#         })