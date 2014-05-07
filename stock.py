# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    
    _columns = {
        'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
        'affranchissement_machine': fields.boolean('Affranchissement machine'),
        'affranchissement_dispense': fields.boolean('Affranchissement dispense'),
        'index_affran_depart': fields.integer(u'Index machine départ'),
        'index_affran_arrive': fields.integer(u'Index machine arrivé'),
        'cumul_affran': fields.float('Cumul'),
    }
    
    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        value={'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}
        pickings=self.browse(cr,uid,ids,context=context)
        for picking in pickings:
            index_arrive=0
            if picking.affranchissement_machine and picking.company_id:
                index_depart=picking.company_id.index_affran
                index_arrive=index_depart
                for move in picking.move_lines:
                    index_arrive+=move.product_qty
                self.pool.get('res.company').write(cr,uid,picking.company_id.id,{'index_affran':index_arrive})
                value.update({'index_affran_depart':index_depart,'index_affran_arrive':index_arrive})
                if picking.sale_id:
                    cumul=picking.company_id.cumul_affran
                    for move in picking.move_lines:
                        for line in picking.sale_id.order_line:
                            if line.product_id.id==move.product_id.id:
                                cumul+=line.price_subtotal
                                self.pool.get('res.company').write(cr,uid,picking.company_id.id,{'cumul_affran':cumul})
                                value.update({'cumul_affran':cumul})
            self.write(cr, uid, picking.id, value)
        return True

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _order = "index_affran_arrive, id desc"
    
    _columns = {
        'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
        'affranchissement_machine': fields.boolean('Affranchissement machine'),
        'affranchissement_dispense': fields.boolean('Affranchissement dispense'),
        'index_affran_depart': fields.integer(u'Index machine départ'),
        'index_affran_arrive': fields.integer(u'Index machine arrivé'),
        'cumul_affran': fields.float('Cumul'),
    }
 
