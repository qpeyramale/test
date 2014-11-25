# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"
    
    def do_partial(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('mrp.production')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        partial_data_normal = {
            'delivery_date' : partial.date
        }
        quantity_normal=0.0
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
            quantity_normal=wizard_line.quantity
            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (wizard_line.move_id.id)].update(product_price=wizard_line.cost,
                                                                  product_currency=wizard_line.currency.id)
        if partial.picking_id.sale_id and partial.picking_id.sale_id.contrat_cadre:
            production_ids=self.pool.get('mrp.production').search(cr,uid,[('origin','=',partial.picking_id.sale_id.name)])
            if production_ids:
                prod_obj.action_produce(cr, uid, production_ids[0],
                                                quantity_normal, 'consume_produce', context=context)
            
            picking_normal=self.pool.get('stock.picking').search(cr,uid,[('sale_id','=',partial.picking_id.sale_id.id),('affranchissement_machine','=',False),('affranchissement_dispense','=',False)])
            if picking_normal and partial.picking_id.id not in picking_normal:
                picking_normal_browse=self.pool.get('stock.picking').browse(cr,uid,picking_normal[-1])
                for move in picking_normal_browse.move_lines:
                    partial_data_normal['move%s' % (move.id)] = {
                        'product_id': move.product_id.id,
                        'product_qty': quantity_normal,
                        'product_uom': move.product_uom.id,
                        'prodlot_id': move.prodlot_id.id,
                    }
                stock_picking.do_partial(cr, uid, [picking_normal_browse.id], partial_data_normal, context=context)
            
        picking=stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        backorder=stock_picking.read(cr,uid,picking.values()[0]['delivered_picking'],['backorder_id'])['backorder_id']
        return {
            #'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            #'name': _('Returned Picking'),
            'view_type':'form',
            'view_mode':'form',
            'res_model': 'stock.picking.out',
            'res_id': backorder and backorder[0] or picking.values()[0]['delivered_picking'],
            'type':'ir.actions.act_window',
            'context':context,
        }
