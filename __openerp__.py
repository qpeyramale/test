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
    'depends': ['sale', 'hr_timesheet_sheet', 'mrp','account','stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/sale_security.xml',
        'wizard/configurator_view.xml',
        'wizard/timesheet_view.xml',
        'sale_view.xml',
        'mrp_view.xml',
        'product_view.xml',
        'stock_view.xml',
        'hr_view.xml',
        'report/timesheet.xml',
        'edi/timesheet_action_data.xml',
        'data/simpac_data.xml',
        
        #données
        #~ 'product.category.csv',
        #~ 'product.tags.csv',
        #~ 'product.product.csv',
        #~ 'mrp.workcenter.csv',
        #~ 'mrp.routing.csv',
        #~ 'mrp.routing.workcenter.csv',
        #~ 'mrp.bom.xml',
    ],
    'js': ['static/src/js/limit_search.js'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
