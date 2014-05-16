# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class res_partner(osv.osv):
    
    _inherit = 'res.partner'
    
    _defaults = {
        'is_company': 1
    }
     
res_partner()

