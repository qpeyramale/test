# -*- coding: utf-8 -*-

from openerp import pooler
from openerp.osv import fields, osv
from openerp import netsvc

class wizard_timesheet(osv.osv):
    
    _name = "wizard_timesheet"
    
    _description = "Timesheet edition"
    
    _columns = {
        'partner_id': fields.many2one('res.partner', u"Société d'intérimaires"),
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
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        #------------------- pièce jointe --------------------------------------
        ir_attachment = self.pool.get('ir.attachment')
        
        attachment_ids
        #-----------------------------------------------------------------------
        ctx.update({
            'default_model': 'hr_deputy_timesheet_sheet.sheet',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_attachment_ids': [(6, 0, [attachment_ids])],
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

wizard_timesheet()
