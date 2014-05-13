# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.osv import fields, osv
from openerp import netsvc

class wizard_timesheet_invoice(osv.osv):
    
    _name = "wizard_timesheet_invoice"
    
    _description = "Timesheet invoice"
    
    _columns = {
        'state': fields.selection([
            ('ok', 'OK'),
            ('all_invoiced','All invoiced'),
            ('partially_invoiced','Partially invoiced')], 'State', select=True, required=True, readonly=True),
    }
    
    def _get_state(self, cr, uid, context=None):
        
        valid=[]
        if context.has_key('active_ids'):
            for timesheet in self.pool.get('hr.deputy.analytic.timesheet').browse(cr, uid, context.get('active_ids')):
                if timesheet.state and timesheet.state != 'invoiced':
                    valid.append(timesheet.id)
        if not context.has_key('active_ids'):
            return 'ok'
        elif len(valid) == len(context.get('active_ids')) :
            return 'ok'
        elif len(valid) == 0:
            return 'all_invoiced'
        else:
            return 'partially_invoiced'
    
    _defaults = {
        'state': _get_state,
    }
    
    def get_partners(self, cr, uid, context):
        
        partners = []
        
        if context.has_key('active_ids'):
            for timesheet in self.pool.get('hr.deputy.analytic.timesheet').browse(cr, uid, context.get('active_ids')):
                #print timesheet.employee_id.partner_id.id,' ? ',timesheet.employee_id.partner_id.id not in retour
                if timesheet.employee_id.partner_id.id not in partners and timesheet.state != 'invoiced':
                    partners.append(timesheet.employee_id.partner_id.id)
        return partners
    
    def _prepare_inv_line(self, cr, uid, account_id, obj_partner, obj_product, context=None):
        
        quantity = 0
        for timesheet in self.pool.get('hr.deputy.analytic.timesheet').browse(cr, uid, context.get('active_ids')):
            if timesheet.employee_id.partner_id.id == obj_partner.id and timesheet.state != 'invoiced':
                quantity += timesheet.unit_amount
                
        price_unit = obj_product.standard_price
        
        return {
            'name': '['+obj_product.default_code+'] '+obj_product.name,
            'account_id': account_id,
            'price_unit': price_unit,
            'quantity': quantity,
            'product_id': obj_product.id,
            'uos_id': obj_product.uos_id.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in obj_product.supplier_taxes_id])],
            #'account_analytic_id': order_line.account_analytic_id.id or False,
        }
        
    def create_invoice(self, cr, uid, partner_id, context):
        
        res = False
        
        obj_user = self.pool.get('hr.deputy.analytic.timesheet').browse(cr, uid, context.get('active_ids')[0]).user_id

        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')
            
        obj_partner = self.pool.get('res.partner').browse(cr, uid, partner_id)    
            
        pay_acc_id = obj_partner.property_account_payable.id
        journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', obj_user.company_id.id)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Define purchase journal for this company: "%s" (id:%d).') % (obj_user.company_id.name, obj_user.company_id.id))

        # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
        inv_lines = []
        
        product_ids = self.pool.get('product.product').search(cr, uid, [('default_code', '=', 'MO')])
        if product_ids:
            obj_product = self.pool.get('product.product').browse(cr, uid, product_ids[0])
            acc_id = obj_product.property_account_expense.id
            if not acc_id:
                acc_id = obj_product.categ_id.property_account_expense_categ.id
            if not acc_id:
                raise osv.except_osv(_('Error!'), _('Define expense account for this company: "%s" (id:%d).') % (obj_product.name, obj_product.id,))
        else:
            raise osv.except_osv(_('Error!'), _('No product %s for invoice lines') % (obj_product.default_code))
            
        fpos = obj_partner.property_account_position and obj_partner.property_account_position.id or False
        
        acc_id = fiscal_obj.map_account(cr, uid, fpos, acc_id)

        inv_line_data = self._prepare_inv_line(cr, uid, acc_id, obj_partner, obj_product, context=context)
        inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
        inv_lines.append(inv_line_id)

        # get invoice data and create invoice
        inv_data = {
            'account_id': pay_acc_id,
            'type': 'in_invoice',
            'partner_id': obj_partner.id,
            'currency_id': obj_partner.property_product_pricelist_purchase.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, inv_lines)],
            'fiscal_position': obj_partner.property_account_position and obj_partner.property_account_position.id or False,
            'payment_term': obj_partner.property_supplier_payment_term.id or False,
            'company_id': obj_user.company_id.id,
        }
        inv_id = inv_obj.create(cr, uid, inv_data, context=context)
        
        #-------------- states -------------------------------------------------
        for timesheet in self.pool.get('hr.deputy.analytic.timesheet').browse(cr, uid, context.get('active_ids')):
            if timesheet.employee_id.partner_id.id == obj_partner.id and timesheet.state != 'invoiced':
                self.pool.get('hr.deputy.analytic.timesheet').write(cr, uid, timesheet.id, {'state': 'invoiced'}, context)

        return inv_id
        
    def create_invoices(self, cr, uid, ids, context=None):
        
        #print context
        if context.has_key('active_ids'):
            partners = self.get_partners(cr, uid, context)
            for partner_id in partners:
                self.create_invoice(cr, uid, partner_id, context)
        
        return True

wizard_timesheet_invoice()
