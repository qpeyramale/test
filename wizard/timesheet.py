# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.osv import fields, osv
from openerp import netsvc

class wizard_timesheet(osv.osv):
    
    _name = "wizard_timesheet"
    
    _description = "Timesheet edition"
    
    _columns = {
        'partner_id': fields.many2one('res.partner', u"Société d'intérimaires",),
        'action': fields.selection([
            ('report', 'New'),
            ('invoice','Open')], 'Action', select=True, required=True, readonly=True),
        'date_invoice': fields.date('Date de facturation'),
        'reference': fields.char(u'Référence facture société'),
    }
    
    def _action_get(obj, cr, uid, context=None):
        return (context.has_key('action') and context.get('action')) or 'report'
    
    _defaults = {
        'action': _action_get,
    }
    
    def print_report(self, cr, uid, ids, context=None):
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        datas = {
             'ids': [context.get('active_id')],
             'model': '',
             'form': data
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'simpac.timesheet',
            'datas': datas,
        }
        
    def send_mail(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'Simpac', 'email_template_edi_deputy_timesheet')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        ctx.update({
            'default_model': 'hr_deputy_timesheet_sheet.sheet',
            'default_res_id': context.get('active_id'),
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'form': data,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        
    def get_partners(self, cr, uid, obj_timesheet_sheet):
        
        partners = []
        
        for timesheet in obj_timesheet_sheet.timesheet_ids:
            #print timesheet.employee_id.partner_id.id,' ? ',timesheet.employee_id.partner_id.id not in retour
            if timesheet.employee_id.partner_id.id not in partners and timesheet.state != 'invoiced':
                partners.append(timesheet.employee_id.partner_id.id)
        return partners
    
    def _prepare_inv_line(self, cr, uid, account_id, obj_timesheet_sheet, obj_partner, obj_product, context=None):
        
        quantity = 0
        for timesheet in obj_timesheet_sheet.timesheet_ids:
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
        
    def create_invoice(self, cr, uid, timesheet_sheet, partner_id, context):
        
        res = False

        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')
            
        obj_partner = self.pool.get('res.partner').browse(cr, uid, partner_id)    
            
        pay_acc_id = obj_partner.property_account_payable.id
        journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', timesheet_sheet.user_id.company_id.id)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Define purchase journal for this company: "%s" (id:%d).') % (timesheet_sheet.user_id.company_id.name, timesheet_sheet.user_id.company_id.id))

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

        inv_line_data = self._prepare_inv_line(cr, uid, acc_id, timesheet_sheet, obj_partner, obj_product, context=context)
        inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
        inv_lines.append(inv_line_id)
        
        for timesheet in timesheet_sheet.timesheet_ids:
            if timesheet.employee_id.partner_id.id == partner_id:
                self.pool.get('hr.deputy.analytic.timesheet').write(cr, uid, [timesheet.id],{'state':'invoiced'}, context=context)

        # get invoice data and create invoice
        inv_data = {
            'name': timesheet_sheet.name,
            'reference': timesheet_sheet.name,
            'account_id': pay_acc_id,
            'type': 'in_invoice',
            'partner_id': obj_partner.id,
            'currency_id': obj_partner.property_product_pricelist_purchase.currency_id.id,
            'journal_id': len(journal_ids) and journal_ids[0] or False,
            'invoice_line': [(6, 0, inv_lines)],
            'origin': timesheet_sheet.name,
            'fiscal_position': obj_partner.property_account_position and obj_partner.property_account_position.id or False,
            'payment_term': obj_partner.property_supplier_payment_term.id or False,
            'company_id': timesheet_sheet.user_id.company_id.id,
            'supplier_invoice_number': 'reference' in context and context.get('reference') or '',
            'date_invoice': 'date_invoice' in context and context.get('date_invoice') or False,
        }
        inv_id = inv_obj.create(cr, uid, inv_data, context=context)

        res = inv_id
        
    def create_invoices(self, cr, uid, ids, context=None):
        
        obj_timesheet_sheet = self.pool.get('hr_deputy_timesheet_sheet.sheet').browse(cr, uid, context.get('active_id'))
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        context.update({'date_invoice':data['date_invoice'],'reference':data['reference']})
        if not data['partner_id']:
            partners = self.get_partners(cr, uid, obj_timesheet_sheet)
            for partner_id in partners:
                self.create_invoice(cr, uid, obj_timesheet_sheet, partner_id, context)
            self.pool.get('hr_deputy_timesheet_sheet.sheet').write(cr, uid, [context.get('active_id')], {'state': 'invoiced'})
        else:
            partner_id = int(data['partner_id'][0])
            self.create_invoice(cr, uid, obj_timesheet_sheet, partner_id, context)

wizard_timesheet()
