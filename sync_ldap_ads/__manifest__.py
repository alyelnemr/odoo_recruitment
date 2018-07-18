# -*- coding: utf-8 -*-
{
    'name': "LDAP Sync",

    'summary': """
        Sync LDAP users to Odoo Partners""",

    'description': """
        Sync LDAP users to Odoo Partners
        """,

    'author': "Andalusia",
    'website': "http://www.andalusia.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ldap',
    'version': '1.0.5',

    # any module necessary for this one to work correctly
    'depends': ['base','auth_ldap','contacts'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/scheduled_actions.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}