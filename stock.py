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
    
    def _produit_machine(self, cr, uid, ids, name, args, context=None):
        res = {}
        for m in self.browse(cr, uid, ids, context=context):
            names=[]
            for line in m.move_lines:
                names.append(line.product_id.name)
            res[m.id] = ' / '.join(names)
        return res
    
    _columns = {
        'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
        'affranchissement_machine': fields.boolean('Affranchissement machine'),
        'affranchissement_dispense': fields.boolean('Affranchissement dispense'),
        'index_affran_depart': fields.integer(u'Index machine départ'),
        'index_affran_arrive': fields.integer(u'Index machine arrivé'),
        'cumul_affran': fields.float('Cumul'),
        'type_affran': fields.selection([('devis', 'Devis'), ('mensuel', 'Mensuel'), ('seul', 'Seul')], 'Affranchissement Type'),
        'produit_machine': fields.function(_produit_machine, type='char', size=256, string="Produit"),
        'configurator_id': fields.many2one('configurator',string='Configuration'),
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
                                cumul+=line.price_unit*move.product_qty
                                self.pool.get('res.company').write(cr,uid,picking.company_id.id,{'cumul_affran':cumul})
                                value.update({'cumul_affran':cumul})
            self.write(cr, uid, picking.id, value)
        return True
    
    def create(self, cr, user, vals, context=None):
        if ('affranchissement_machine' in vals and vals.get('affranchissement_machine'))\
            or ('affranchissement_dispense' in vals and vals.get('affranchissement_dispense')):
            if 'move_lines' in vals:
                if len(vals.get('move_lines'))>1:
                    raise osv.except_osv(_('Attention!'),_('Vous ne pouvez créer qu\'un seul BL par affranchissement.'))
        
        new_id = super(stock_picking, self).create(cr, user, vals, context)
        return new_id
    
    
#~ class stock_picking_out(osv.osv):
    #~ _inherit = "stock.picking.out"
    #~ _order = "index_affran_arrive, id desc"
    #~ 
    #~ def _produit_machine(self, cr, uid, ids, name, args, context=None):
        #~ res = {}
        #~ for m in self.browse(cr, uid, ids, context=context):
            #~ names=[]
            #~ for line in m.move_lines:
                #~ names.append(line.product_id.name)
            #~ res[m.id] = ' / '.join(names)
        #~ return res
    #~ 
    #~ _columns = {
        #~ 'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
        #~ 'affranchissement_machine': fields.boolean('Affranchissement machine'),
        #~ 'affranchissement_dispense': fields.boolean('Affranchissement dispense'),
        #~ 'index_affran_depart': fields.integer(u'Index machine départ'),
        #~ 'index_affran_arrive': fields.integer(u'Index machine arrivé'),
        #~ 'cumul_affran': fields.float('Cumul'),
        #~ 'type_affran': fields.selection([('devis', 'Devis'), ('mensuel', 'Mensuel'), ('seul', 'Seul')], 'Affranchissement Type'),
        #~ 'produit_machine': fields.function(_produit_machine, type='char', size=256, string="Produit"),
    #~ }
    #~ 
    #~ def create(self, cr, user, vals, context=None):
        #~ if ('affranchissement_machine' in vals and vals.get('affranchissement_machine'))\
            #~ or ('affranchissement_dispense' in vals and vals.get('affranchissement_dispense')):
            #~ if 'move_lines' in vals:
                #~ if len(vals.get('move_lines'))>1:
                    #~ raise osv.except_osv(_('Attention!'),_('Vous ne pouvez créer qu\'un seul BL par affranchissement.'))
        #~ 
        #~ new_id = super(stock_picking_out, self).create(cr, user, vals, context)
        #~ return new_id

                            
class stock_move(osv.osv):
    _inherit = "stock.move"
    
    _columns = {
        'affranchissement_machine': fields.boolean('Affranchissement machine'),
        'affranchissement_dispense': fields.boolean('Affranchissement dispense'),
        'type_affran': fields.selection([('devis', 'Devis'), ('mensuel', 'Mensuel'), ('seul', 'Seul')], 'Affranchissement Type'),
        'configurator_id': fields.many2one('configurator',string='Configuration'),
    }
    

    def create(self, cr, uid, data, context=None):
        picking_obj = self.pool.get('stock.picking')
        print data,context
        if 'type_affr' in context:
            proc=self.pool.get('procurement.order').browse(cr,uid,data['procurement_id'])
            data['configurator_id']=proc.sale_line_id.configurator_id.id
            if context.get('type_affr')=='machine':
                if proc.sale_line_id.order_id.contrat_cadre:
                    data['affranchissement_machine']=True
                    data['type_affran']='mensuel'
                else:
                    data['affranchissement_machine']=True
                    data['type_affran']='devis'
            if context.get('type_affr')=='dispense':
                data['affranchissement_dispense']=True
        new_id=super(stock_move, self).create(cr, uid, data, context)
        return new_id
 
    def write(self, cr, uid, ids,data, context=None):
        picking_obj = self.pool.get('stock.picking')
        print data,context
        if 'picking_id' in data:
            for move in self.browse(cr,uid,ids):
                picking_obj.write(cr,uid,data['picking_id'],{'configurator_id':move.configurator_id.id,
                                                            'affranchissement_machine':move.affranchissement_machine,
                                                            'type_affran':move.type_affran,
                                                            'affranchissement_dispense':move.affranchissement_dispense
                                                            })
        new_id=super(stock_move, self).write(cr, uid, ids,data, context)
        return new_id
 
