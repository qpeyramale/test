# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp

class report_stock_affran(osv.osv):
    _name = "report.stock.affran"
    _description = "Affranchissement stats"
    _auto = False
    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char(u'Année', size=4, readonly=True),
        'day': fields.char('Jour', size=128, readonly=True),
        'week': fields.char('Semaine', size=128, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partenaire', readonly=True),
        'product_id':fields.many2one('product.product', 'Produit', readonly=True),
        'company_id':fields.many2one('res.company', u'Société', readonly=True),
        'picking_id':fields.many2one('stock.picking', u'Expédition', readonly=True),
        'type': fields.selection([('out', 'Livraison'), ('in', 'Réception'), ('internal', 'Interne'), ('other', 'Autres')], 'Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'location_id': fields.many2one('stock.location', 'Emplacement source', readonly=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'location_dest_id': fields.many2one('stock.location', 'Emplacement de dest.', readonly=True, select=True, help="Location where the system will stock the finished products."),
        'state': fields.selection([('draft', 'Brouillon'), ('waiting', 'En attente'), ('confirmed', 'Confirmé'), ('assigned', 'Prêt'), ('done', 'Terminé'), ('cancel', 'Annulé')], u'État', readonly=True, select=True),
        'product_qty':fields.integer(u'Quantité',readonly=True),
        'categ_id': fields.many2one('product.category', u'Catégorie de produit', ),
        'product_qty_in':fields.integer(u'Qté entrante',readonly=True),
        'product_qty_out':fields.integer(u'Qté sortante',readonly=True),
        'value' : fields.float('Valeur totale', required=True),
        'day_diff2':fields.float('Lag (Days)',readonly=True,  digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'day_diff1':fields.float('Planned Lead Time (Days)',readonly=True, digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'day_diff':fields.float('Execution Lead Time (Days)',readonly=True,  digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'stock_journal': fields.many2one('stock.journal','Journal de stock ', select=True),

        'type_affran': fields.selection([('devis', 'Devis'), ('mensuel', 'Mensuel'), ('seul', 'Seul')], 'Affranchissement Type'),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_affran')
        cr.execute("""
            CREATE OR REPLACE view report_stock_affran AS (
                SELECT
                        min(sm.id) as id, 
                        date_trunc('day', sm.date) as date,
                        to_char(date_trunc('day',sm.date), 'YYYY') as year,
                        to_char(date_trunc('day',sm.date), 'MM') as month,
                        to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as day,
                        'Semaine ' || to_char(date_trunc('day',sm.date), 'WW') as week,
                        avg(date(sm.date)-date(sm.create_date)) as day_diff,
                        avg(date(sm.date_expected)-date(sm.create_date)) as day_diff1,
                        avg(date(sm.date)-date(sm.date_expected)) as day_diff2,
                        sm.location_id as location_id,
                        sm.picking_id as picking_id,
                        sm.company_id as company_id,
                        sm.location_dest_id as location_dest_id,
                        sum(sm.product_qty) as product_qty,
                        sum(
                            (CASE WHEN sp.type in ('out') THEN
                                     (sm.product_qty * pu.factor / pu2.factor)
                                  ELSE 0.0 
                            END)
                        ) as product_qty_out,
                        sum(
                            (CASE WHEN sp.type in ('in') THEN
                                     (sm.product_qty * pu.factor / pu2.factor)
                                  ELSE 0.0 
                            END)
                        ) as product_qty_in,
                        sm.partner_id as partner_id,
                        sm.product_id as product_id,
                        sm.state as state,
                        sp.type_affran as type_affran,
                        sm.product_uom as product_uom,
                        pt.categ_id as categ_id ,
                        coalesce(sp.type, 'other') as type,
                        sp.stock_journal_id AS stock_journal,
                        sum(
                            (CASE WHEN sp.type in ('in') THEN
                                     (sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                                  ELSE 0.0 
                            END)
                            -
                            (CASE WHEN sp.type in ('out') THEN
                                     (sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                                  ELSE 0.0 
                            END)
                        ) as value
                    FROM
                        stock_move sm
                        LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.product_uom=pu.id)
                          LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    WHERE sp.affranchissement_machine = True or sp.affranchissement_dispense = True
                    GROUP BY
                        coalesce(sp.type, 'other'), date_trunc('day', sm.date), sm.partner_id,
                        sm.state, sm.product_uom, sm.date_expected,
                        sm.product_id, pt.standard_price, sm.picking_id,
                        sm.company_id, sm.location_id, sm.location_dest_id, pu.factor, pt.categ_id, sp.stock_journal_id,
                        year, month, day, week, sp.type_affran
               )
        """)

report_stock_affran()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
