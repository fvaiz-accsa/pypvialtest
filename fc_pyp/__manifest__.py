# -*- coding: utf-8 -*-
{
    'name': "fc_pyp",

    'summary': """
        Facturacion Electronica.
        """,

    'description': """
        Facturacion Electronica.
        Memory API
        Version: 2.5
        Fecha: 11/Oct/2022
        
    """,

    'author': "Ajedrez",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/payment_receipt_report.xml',
        'views/payment_receipt_template.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
