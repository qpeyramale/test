# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class res_partner(osv.osv):
    
    _inherit = 'res.partner'
    
    _defaults = {
        'is_company': 1
    }
     
res_partner()


#~ class resource_resource(osv.osv):
    #~ _inherit = "resource.resource"
    #~ _order = "name asc"
