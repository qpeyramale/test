# -*- coding: utf-8 -*-

{
    'name': 'Simpac',
    'version': '0.1',
    'category': 'Sudokeys',
    'sequence': 1,
    'summary': 'Simpac',
    'description': """""",
    'author': 'Sudokeys',
    'website': 'http://www.sudokeys.com',
    'depends': ['sale','mrp'],
    'data': [
        'wizard/configurator_view.xml',
        'sale_view.xml',
        'mrp_view.xml',
        'product_view.xml',
    ],
    'js': ['static/src/js/limit_search.js'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
