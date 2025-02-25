# -*- coding: utf-8 -*-
{
    'name': "custom_addons/fc_pyp_add/",

    'summary': """
        Cambios Agregados a FC_pyp. Tipo de Cambio""",

    'description': """
        Cambios Agregados a FC_pyp
        Diferencia de cambio:
           - Menu de Facturacion/Contabilidad/Contabilidad (Dif. de Cambio
           - Campo en vista tree Cliente/Factura
           - Boton 'Actualizar Calculo DC' al seleccionar facturas en vista tree"
    """,

    'author': "GN",
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
        'views/diferenciacambio_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
