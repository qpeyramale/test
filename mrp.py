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
        'name_resource': fields.related('resource_id', 'name', string="Resource Name", type='char', size=128, store=True, select=True),
    }
    _defaults = {
     }
     
    _order = "name_resource"

mrp_workcenter()

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    
    def action_confirm(self, cr, uid, ids, context=None):
        shipment_id = super(mrp_production, self).action_confirm(cr, uid, ids, context=context)
        for production in self.browse(cr, uid, ids, context=context):
            if production.sale_name:
                sale_id=self.pool.get('sale.order').search(cr,uid,[('name','=',production.sale_name)])
                if sale_id:
                    sale=self.pool.get('sale.order').browse(cr,uid,sale_id[0],context=context)
                    for config in sale.configurator_ids:
                        if production.product_id.id==config.article_id.id:
                            for config_product in config.conf_product_lines:
                                product_search=self.pool.get('mrp.production.product.line').search(cr,uid,[('product_id','=',config_product.product_id.id),('production_id','=',production.id)])
                                if config_product.quantite!=0:
                                    if not product_search:
                                        product_line_id=self.pool.get('mrp.production.product.line').create(cr,uid,{
                                                        'name': config_product.product_id.name,
                                                        'product_id': config_product.product_id.id,
                                                        'product_qty': config_product.quantite,
                                                        'product_uom': config_product.product_id.uom_id.id,
                                                        'production_id': production.id,
                                                    })
                                        product_line_browse=self.pool.get('mrp.production.product.line').browse(cr,uid,product_line_id)
                                        consume_move_id = self._make_production_consume_line(cr, uid, product_line_browse, production.move_created_ids[0].id, source_location_id=production.location_src_id.id, context=context)
                                        if production.picking_id:
                                            shipment_move_id = self._make_production_internal_shipment_line(cr, uid, product_line_browse, production.picking_id.id, consume_move_id,\
                                                         destination_location_id=production.location_src_id.id, context=context)
                                            self._make_production_line_procurement(cr, uid, product_line_browse, shipment_move_id, context=context)
                                    for line in production.product_lines:
                                        if line.product_id.id==config_product.product_id.id:
                                            self.pool.get('mrp.production.product.line').write(cr,uid,line.id,{'product_qty':config_product.quantite})
                                    for move_line in production.move_lines:
                                        if move_line.product_id.id==config_product.product_id.id:
                                            self.pool.get('stock.move').write(cr,uid,move_line.id,{'product_qty':config_product.quantite})
                                else:
                                    if product_search:
                                        self.pool.get('mrp.production.product.line').unlink(cr,uid,product_search)
                                        for move_line in production.move_lines:
                                            if move_line.product_id.id==config_product.product_id.id:
                                                self.pool.get('stock.move').write(cr,uid,move_line.id,{'state':'draft'})
                                                self.pool.get('stock.move').unlink(cr,uid,[move_line.id])
                                        if production.picking_id:
                                            for int_move_line in production.picking_id.move_lines:
                                                if int_move_line.product_id.id==config_product.product_id.id:
                                                    self.pool.get('stock.move').write(cr,uid,int_move_line.id,{'state':'draft'})
                                                    self.pool.get('stock.move').unlink(cr,uid,[int_move_line.id])
                            for config_workcenter in config.conf_workcenter_lines:
                                for line in production.workcenter_lines:
                                    if line.workcenter_id.id==config_workcenter.workcenter_id.id:
                                        self.pool.get('mrp.production.workcenter.line').write(cr,uid,line.id,{'cycle':config_workcenter.quantite,'hour':config_workcenter.temps})
        return shipment_id

#~ class resource_resource(osv.osv):
    #~ _inherit = "resource.resource"
    #~ _order = "name asc"
