# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

class res_partner(osv.osv):
    
    _inherit = 'res.partner'
    
    _columns = {
        'interimaires': fields.boolean(u"Société d'intérimaires"),
        
        #Affranchissement
        'n_contrat': fields.char(u'N° du contrat'),
        'n_courrier': fields.char(u'Identifiant courrier'),
        'n_siret': fields.char(u'SIRET'),
        'n_autorisation': fields.char(u'N° autorisation'),
    }
    
    _defaults = {
        'is_company': 1
    }
     
res_partner()

