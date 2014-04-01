# -*- coding: utf-8 -*-

import math
import re


from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class product_product(osv.osv):
    
    def _get_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id]=0.0
            if not product.margin_perso and product.categ_id and product.categ_id.margin:
                res[product.id] = product.categ_id.margin
                self._set_margin(cr,uid,product.id,field_name,product.categ_id.margin,arg,context=context)
            elif product.standard_price>0:
                res[product.id] = ((product.list_price/product.standard_price)-1.0)*100.0
        return res
    
    def _set_margin(self, cursor, user, id, name, value, arg, context=None):
        product = self.browse(cursor, user, id, context=context)
        return self.write(cursor, user, id, {'list_price': product.standard_price*(1.0+(value/100.0))}, context=context)

    _inherit = "product.product"
    _columns = {
        'tag1': fields.char('Tag1'),
        'tag2': fields.char('Tag2'),
        'tag3': fields.char('Tag3'),
        'margin_perso': fields.boolean('Marge détaché de la famille'),
        'margin': fields.function(_get_margin,fnct_inv=_set_margin,string=u"Marge",digits=(12,2),type="float"),
    }

class product_category(osv.osv):

    _inherit = "product.category"
    _columns = {
        'taux': fields.integer('Taux'),
        'margin': fields.float('Marge sur les produits enfants',help="Ne s'applique seulement que pour la catégorie directement parente aux produit"),
    }

