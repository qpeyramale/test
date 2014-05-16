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

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _order = "index_affran_arrive, id desc"
    
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
    }
                            
class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"
    
    def do_partial(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        for wizard_line in partial.move_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id

            #Quantiny must be Positive
            if wizard_line.quantity < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))

            #Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
            qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)

            if line_uom.factor and line_uom.factor <> 0:
                if float_compare(qty_in_line_uom, wizard_line.quantity, precision_rounding=line_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only rounding of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
            if move_id:
                #Check rounding Quantity.ex.
                #picking: 1kg, uom kg rounding = 0.01 (rounding to 10g),
                #partial delivery: 253g
                #=> result= refused, as the qty left on picking would be 0.747kg and only 0.75 is accepted by the uom.
                initial_uom = wizard_line.move_id.product_uom
                #Compute the quantity for respective wizard_line in the initial uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
                without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
                if float_compare(qty_in_initial_uom, without_rounding_qty, precision_rounding=initial_uom.rounding) != 0:
                    raise osv.except_osv(_('Warning!'), _('The rounding of the initial uom does not allow you to ship "%s %s", as it would let a quantity of "%s %s" to ship and only rounding of "%s %s" is accepted by the uom.') % (wizard_line.quantity, line_uom.name, wizard_line.move_id.product_qty - without_rounding_qty, initial_uom.name, initial_uom.rounding, initial_uom.name))
            else:
                seq_obj_name =  'stock.picking.' + picking_type
                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uom': wizard_line.product_uom.id,
                                                    'prodlot_id': wizard_line.prodlot_id.id,
                                                    'location_id' : wizard_line.location_id.id,
                                                    'location_dest_id' : wizard_line.location_dest_id.id,
                                                    'picking_id': partial.picking_id.id
                                                    },context=context)
                stock_move.action_confirm(cr, uid, [move_id], context)
            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.quantity,
                'product_uom': wizard_line.product_uom.id,
                'prodlot_id': wizard_line.prodlot_id.id,
            }
            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
                                                                  product_currency=wizard_line.currency.id)
        picking=stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        backorder=stock_picking.read(cr,uid,picking.values()[0]['delivered_picking'],['backorder_id'])['backorder_id']
        
        
        return {
            #~ 'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            #~ 'name': _('Returned Picking'),
            'view_type':'form',
            'view_mode':'form',
            'res_model': 'stock.picking.out',
            'res_id': backorder and backorder[0] or picking.values()[0]['delivered_picking'],
            'type':'ir.actions.act_window',
            'context':context,
        }

 
