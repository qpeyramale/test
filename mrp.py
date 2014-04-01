# -*- coding: utf-8 -*-

import time
from datetime import datetime

import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp import SUPERUSER_ID

class mrp_workcenter(osv.osv):
    _inherit = 'mrp.workcenter'
    
    def _get_prix(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for workcenter in self.browse(cr, uid, ids, context=context):
            res[workcenter.id] = {
                'prix_theo_fixe': 0.0,
                'prix_theo_variable': 0.0,
            }
            val = val1 = 0.0
            if workcenter.product_categ_id and workcenter.product_categ_id.taux>0:
                val=workcenter.product_categ_id.taux
            elif workcenter.product_categ_id.parent_id and workcenter.product_categ_id.parent_id.taux>0:
                val=workcenter.product_categ_id.parent_id.taux
            res[workcenter.id]['prix_theo_fixe'] = val*workcenter.time_cycle
            if workcenter.capacity_per_hour>0:
                res[workcenter.id]['prix_theo_variable'] = val/workcenter.capacity_per_hour
        return res
    
    _columns = {
        'product_categ_id': fields.many2one('product.category','Famille'),
        'capacity_per_hour': fields.float('Cadence horaire'),
        'prix_theo_fixe': fields.function(_get_prix,string=u"Prix théorique fixe",digits=(12,6),multi="prix"),
        'prix_theo_variable': fields.function(_get_prix,string=u"Prix théorique variable",digits=(12,6),multi="prix"),
        'prix_marche_fixe': fields.float(u'Prix marché fixe'),
        'prix_marche_variable': fields.float(u'Prix marché variable'),
    }
    _defaults = {
     }

mrp_workcenter()
