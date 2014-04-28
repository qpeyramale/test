# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc


class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
        'configurator_ids': fields.one2many('configurator','sale_id',string='Configurations'),
        #~ 'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, domain=[('composant','=',False)]),
    }
    
    
    
class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    _columns = {
        'configurator_id': fields.many2one('configurator',string='Configuration'),
        'composant': fields.boolean('Composant'),
        'produit_fini': fields.boolean('Produit fini'),
    }
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_('Error!'),
                                _('Please define income account for this product: "%s" (id:%d).') % \
                                    (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                'produit_fini': line.produit_fini,
                'composant': line.composant,
                'configurator_id': line.configurator_id.id
            }
        return res
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        print 'default copy sale line',default
        print coucou
        #~ default.update({
            #~ 'date_order': fields.date.context_today(self, cr, uid, context=context),
            #~ 'state': 'draft',
            #~ 'invoice_ids': [],
            #~ 'date_confirm': False,
            #~ 'client_order_ref': '',
            #~ 'name': self.pool.get('ir.sequence').get(cr, uid, 'sale.order'),
        #~ })
        return super(sale_order_line, self).copy(cr, uid, id, default, context=context)
    
    
