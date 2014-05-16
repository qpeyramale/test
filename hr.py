# -*- coding: utf-8 -*-

# *************

import time
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
import base64
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv, orm

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    _columns = {
        'interimaire': fields.boolean(u'Intérimaire'),
        'prenom': fields.char(u'Prénom', size=64),
        'partner_id': fields.many2one('res.partner', u'Société'),
        'num_secu': fields.char(u'Numéro Sécurité Sociale', size=20),
        'timesheet_ids': fields.one2many('hr.deputy.analytic.timesheet', 'employee_id', u'Timesheet lines', readonly=True),
        'phone': fields.char(u'Téléphone', size=64),
        'mobile': fields.char(u'Portable', size=64),
        'phone2': fields.char(u'Autre numéro', size=64),
        'title': fields.many2one('res.partner.title', u'Civilité'),
    }
    
    _defaults = {
     }
     
    def create(self, cr, uid, data, context=None):
        if data.has_key('interimaire') and data['interimaire']:
            data['name'] = data['name'].upper()
        return super(hr_employee, self).create(cr, uid, data, context=context)
    
    def write(self, cr, uid, ids, data, context=None):
        if data.has_key('interimaire') and data['interimaire']:
            data['name'] = data['name'].upper()
        elif not data.has_key('interimaire'):
            for obj_employee in self.browse(cr, uid, ids):
                if obj_employee.interimaire:
                    data['name'] = data['name'].upper()
        return super(hr_employee, self).write(cr, uid, ids, data, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []

        res = [(r['id'], r['prenom'] and (r['name']+' '+r['prenom']) or r['name']  ) for r in self.read(cr, uid, ids, ['name', 'prenom'], context)]
        return res
     

hr_employee()

class hr_deputy_timesheet_previous(osv.osv_memory):
    _name = 'hr.deputy.timesheet.previous'
    _description = 'hr.deputy.timesheet.previous'

    def open_timesheet(self, cr, uid, ids, context=None):
        ts = self.pool.get('hr_deputy_timesheet_sheet.sheet')
        if context is None:
            context = {}
        view_type = 'form,tree'

        user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(user_ids):
            raise osv.except_osv(_('Error!'), _('Please create an employee and associate it with this user.'))
        
        date_debut = datetime.strptime(time.strftime('%d/%m/%y',time.localtime()), '%d/%m/%y')
        duree = timedelta(7) 
        date_fin = date_debut - duree_finale
        
        ids = ts.search(cr, uid, [('user_id','=',uid),('state','in',('draft','new')),('date_from','<=',date_fin.strftime('%Y-%m-%d')), ('date_to','>=',date_fin.strftime('%Y-%m-%d'))], context=context)

        if len(ids) > 1:
            view_type = 'tree,form'
            domain = "[('id','in',["+','.join(map(str, ids))+"]),('user_id', '=', uid)]"
        elif len(ids)==1:
            domain = "[('user_id', '=', uid)]"
        else:
            domain = "[('user_id', '=', uid)]"
        value = {
            'domain': domain,
            'name': 'Nouveau',
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'hr_deputy_timesheet_sheet.sheet',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        if len(ids) == 1:
            value['res_id'] = ids[0]
        return value

hr_deputy_timesheet_previous()

class hr_deputy_timesheet_current_open(osv.osv_memory):
    _name = 'hr.deputy.timesheet.current.open'
    _description = 'hr.deputy.timesheet.current.open'

    def open_timesheet(self, cr, uid, ids, context=None):
        ts = self.pool.get('hr_deputy_timesheet_sheet.sheet')
        if context is None:
            context = {}
        view_type = 'form,tree'

        user_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        if not len(user_ids):
            raise osv.except_osv(_('Error!'), _('Please create an employee and associate it with this user.'))
        ids = ts.search(cr, uid, [('user_id','=',uid),('state','in',('draft','new')),('date_from','<=',time.strftime('%Y-%m-%d')), ('date_to','>=',time.strftime('%Y-%m-%d'))], context=context)

        if len(ids) > 1:
            view_type = 'tree,form'
            domain = "[('id','in',["+','.join(map(str, ids))+"]),('user_id', '=', uid)]"
        elif len(ids)==1:
            domain = "[('user_id', '=', uid)]"
        else:
            domain = "[('user_id', '=', uid)]"
        value = {
            'domain': domain,
            'name': 'Nouveau',
            'view_type': 'form',
            'view_mode': view_type,
            'res_model': 'hr_deputy_timesheet_sheet.sheet',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        if len(ids) == 1:
            value['res_id'] = ids[0]
        return value

hr_deputy_timesheet_current_open()

class hr_deputy_timesheet_sheet(osv.osv):
    
    _name = "hr_deputy_timesheet_sheet.sheet"
    
    _inherit = "mail.thread"
    
    _order = "id desc"
    
    _description="Timesheet"
    
    _columns = {
        'name': fields.char('Note', size=64, select=1,
                states={'confirm':[('readonly', True)], 'done':[('readonly', True)]}),
        'date_from': fields.date('Date from', required=True, select=1, readonly=True, states={'new':[('readonly', False)]}),
        'date_to': fields.date('Date to', required=True, select=1, readonly=True, states={'new':[('readonly', False)]}),
        'last_date': fields.date('Dernière date', required=False),
        'last_hour_from': fields.float('Dernière heure entrée', required=False),
        'last_hour_to':  fields.float('Dernière heure sortie', required=False),
        'timesheet_ids': fields.one2many('hr.deputy.analytic.timesheet', 'sheet_id',
            'Timesheet lines',
            readonly=True, states={
                'draft': [('readonly', False)],
                'new': [('readonly', False)]}
            ),
        'user_id': fields.many2one('res.users', 'User', required=True, select=1, states={'confirm':[('readonly', True)], 'done':[('readonly', True)]}),
        'state' : fields.selection([
            ('new', 'New'),
            ('draft','Open'),
            ('confirm','Waiting Approval'),
            ('done','Approved'),('invoiced','Invoiced')], 'Status', select=True, required=True, readonly=True),
    }
    
    _order = 'date_from desc'
    
    def button_confirm(self, cr, uid, ids, context=None):
        for sheet in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, sheet.id, {'state': 'done'})
            for timesheet in sheet.timesheet_ids:
                if timesheet.state != 'invoiced':
                    self.pool.get('hr.deputy.analytic.timesheet').write(cr, uid, timesheet.id, {'state': 'done'})
        return True
    
    def _default_date_from(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return time.strftime('%Y-%m-01')
        elif r=='week':
            return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r=='year':
            return time.strftime('%Y-01-01')
        return time.strftime('%Y-%m-%d')

    def _default_date_to(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r=='month':
            return (datetime.today() + relativedelta(months=+1,day=1,days=-1)).strftime('%Y-%m-%d')
        elif r=='week':
            return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r=='year':
            return time.strftime('%Y-12-31')
        return time.strftime('%Y-%m-%d')
    
    _defaults = {
        'date_from' : _default_date_from,
        'date_to' : _default_date_to,
        'user_id': lambda cr, uid, id, c={}: id,
        'state': 'new',
        'last_date': datetime.today().strftime('%Y-%m-%d'),
        #'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'hr_deputy_timesheet_sheet.sheet', context=c)
    }
    
    def _sheet_date(self, cr, uid, ids, forced_user_id=False, context=None):
        for sheet in self.browse(cr, uid, ids, context=context):
            new_user_id = forced_user_id or sheet.user_id and sheet.user_id.id
            if new_user_id:
                cr.execute('SELECT id \
                    FROM hr_deputy_timesheet_sheet_sheet \
                    WHERE (date_from <= %s and %s <= date_to) \
                        AND user_id=%s \
                        AND id <> %s',(sheet.date_to, sheet.date_from, new_user_id, sheet.id))
                if cr.fetchall():
                    return False
        return True
    
    _constraints = [
        (_sheet_date, 'You cannot have 2 timesheets that overlap!\nPlease use the menu \'My Current Timesheet\' to avoid this problem.', ['date_from','date_to']),
    ]
    
    #~ def onchange_timesheet_ids(self, cr, uid, ids, lines, context=None):
        #~ if context is None:
            #~ context={}
        #~ res={}
        #~ for line in lines:
            #~ print 'line',line
            #~ if line[0]==0:
                #~ res['last_hour_from']=line[2]['hour_from']
                #~ res['last_hour_to']=line[2]['hour_to']
                #~ res['last_date']=line[2]['date']
                #~ break
        #~ return {'value':res} 
    
hr_deputy_timesheet_sheet()
    
class hr_deputy_analytic_timesheet(osv.osv):
    
    _name = "hr.deputy.analytic.timesheet"
    
    def _sheet(self, cursor, user, ids, name, args, context=None):
        sheet_obj = self.pool.get('hr_deputy_timesheet_sheet.sheet')
        res = {}.fromkeys(ids, False)
        for ts_line in self.browse(cursor, user, ids, context=context):
            sheet_ids = sheet_obj.search(cursor, user,
                [('date_to', '>=', ts_line.date), ('date_from', '<=', ts_line.date)],
                context=context)
            if sheet_ids:
            # [0] because only one sheet possible for an employee between 2 dates
                res[ts_line.id] = sheet_obj.name_get(cursor, user, sheet_ids, context=context)[0]
        return res
    
    def _get_hr_timesheet_sheet(self, cr, uid, ids, context=None):
        ts_line_ids = []
        for ts in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                    SELECT l.id
                        FROM hr_deputy_analytic_timesheet l
                    WHERE %(date_to)s >= l.date
                        AND %(date_from)s <= l.date
                    GROUP BY l.id""", {'date_from': ts.date_from,
                                        'date_to': ts.date_to,
                                        })
            ts_line_ids.extend([row[0] for row in cr.fetchall()])
        return ts_line_ids
    
    def _get_hours(self, cursor, user, ids, name, args, context=None):
        res = {}
        for ts_line in self.browse(cursor, user, ids, context=context):
            res[ts_line.id] = ts_line.hour_to - ts_line.hour_from
        return res
    
    _columns = {
        #'name': fields.char(u'Nom', size=64),
        'date': fields.date(u'Date', required=True, select=True),
        'employee_id': fields.many2one('hr.employee', u"Employee", required=True),
        'partner_id': fields.related('employee_id', 'partner_id', 'name', type='char', string=u'Société'),
        'sheet_id': fields.function(_sheet, string=u'Sheet', type='many2one', relation='hr_deputy_timesheet_sheet.sheet', ondelete="cascade",
                        store={
                            'hr_deputy_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                            #'account.analytic.line': (_get_account_analytic_line, ['user_id', 'date'], 10),
                            'hr.deputy.analytic.timesheet': (lambda self,cr,uid,ids,context=None: ids, None, 10),
                        },
        ),
        'hour_from': fields.float(u'Heure entrée', required=True),
        'hour_to':  fields.float(u'Heure sortie', required=True),
        'unit_amount': fields.function(_get_hours, string='Heures', type='float', store=False),
        'user_id': fields.related('sheet_id', 'user_id', type="many2one", relation="res.users", store=True, string=u"User", required=False, readonly=True),
        'state' : fields.selection([
            ('new', u'New'),
            ('draft',u'Open'),
            ('confirm',u'Waiting Approval'),
            ('done',u'Approved'),
            ('invoiced',u'Invoiced')], u'Status', select=True, required=True, readonly=True),
        'search_date_from':fields.function(lambda *a,**k:{}, method=True, type='date',string=u"Du"),
        'search_date_to':fields.function(lambda *a,**k:{}, method=True, type='date',string=u"Au"),
    }
    
    _order = 'date desc, hour_from desc, hour_to desc'
    
    def _get_default_date(self, cr, uid, context=None):
        #print context
        if context.has_key('timesheet_id') and context.get('timesheet_id'):
            obj_timesheet = self.pool.get('hr_deputy_timesheet_sheet.sheet').browse(cr, uid, context.get('timesheet_id'))
            if obj_timesheet.last_date:
                return obj_timesheet.last_date
        return fields.date.context_today(self, cr, uid, context=context)
    
    def _get_default_hour_from(self, cr, uid, context=None):
        #print context
        if context.has_key('timesheet_id') and context.get('timesheet_id'):
            obj_timesheet = self.pool.get('hr_deputy_timesheet_sheet.sheet').browse(cr, uid, context.get('timesheet_id'))
            if obj_timesheet.last_hour_from:
                return obj_timesheet.last_hour_from
        return 0
    
    def _get_default_hour_to(self, cr, uid, context=None):
        if context.has_key('timesheet_id') and context.get('timesheet_id'):
            obj_timesheet = self.pool.get('hr_deputy_timesheet_sheet.sheet').browse(cr, uid, context.get('timesheet_id'))
            if obj_timesheet.last_hour_to:
                return obj_timesheet.last_hour_to
        return 0
    
    def onchange_hour_from(self, cr, uid, ids, hour_from, context=None):
        if context.get('timesheet_id') and context['timesheet_id']:
            self.pool.get('hr_deputy_timesheet_sheet.sheet').write(cr, uid, context.get('timesheet_id'), {'last_hour_from': hour_from})
        return {}
    
    def onchange_hour_to(self, cr, uid, ids, hour_to, context=None):
        if context.get('timesheet_id') and context['timesheet_id']:
            self.pool.get('hr_deputy_timesheet_sheet.sheet').write(cr, uid, context.get('timesheet_id'), {'last_hour_to': hour_to})
        return {}
    
    def onchange_date(self, cr, uid, ids, date, context=None):
        if context.get('timesheet_id') and context['timesheet_id']:
            self.pool.get('hr_deputy_timesheet_sheet.sheet').write(cr, uid, context.get('timesheet_id'), {'last_date': date})
        return {}
    
    def check_hours(self, cr, uid, ids, context=None):
         timesheet = self.read(cr, uid, ids[0], ['hour_from', 'hour_to'])
         if timesheet['hour_from'] and timesheet['hour_to']:
             if timesheet['hour_from'] > timesheet['hour_to']:
                 return False
         return True

    _constraints = [
        (check_hours, "Erreur! l'heure d'entrée doit être inférieure à l'heure de sortie.", ['hour_from', 'hour_to'])
    ]
    
    _defaults = {
        'date': _get_default_date,
        #'hour_from': _get_default_hour_from,
        #'hour_to': _get_default_hour_to,
        'state': 'new',
    }
    
class email_template(osv.osv):
    
    "Templates for sending email"
    
    _inherit = "email.template"
    
    def generate_email(self, cr, uid, template_id, res_id, context=None):
        """Generates an email from the template for given (model, res_id) pair.

           :param template_id: id of the template to render.
           :param res_id: id of the record to use for rendering the template (model
                          is taken from template definition)
           :returns: a dict containing all relevant fields for creating a new
                     mail.mail entry, with one extra key ``attachments``, in the
                     format expected by :py:meth:`mail_thread.message_post`.
        """

        if context is None:
            context = {}
        
        if context.has_key('form') and context['form'].has_key('partner_id'):
            obj_partner = self.pool.get('res.partner').browse(cr, uid, context['form']['partner_id'][0])
            context.update({
                'partner_id': context.get('form')['partner_id'][0],
                'partner_name': obj_partner.name or '',
            })
            
        report_xml_pool = self.pool.get('ir.actions.report.xml')
        template = self.get_email_template(cr, uid, template_id, res_id, context)
        values = {}
        for field in ['subject', 'body_html', 'email_from',
                      'email_to', 'email_recipients', 'email_cc', 'reply_to']:
            values[field] = self.render_template(cr, uid, getattr(template, field),
                                                 template.model, res_id, context=context) \
                                                 or False
        if template.user_signature:
            signature = self.pool.get('res.users').browse(cr, uid, uid, context).signature
            values['body_html'] = tools.append_content_to_html(values['body_html'], signature)

        if values['body_html']:
            values['body'] = tools.html_sanitize(values['body_html'])

        values.update(mail_server_id=template.mail_server_id.id or False,
                      auto_delete=template.auto_delete,
                      model=template.model,
                      res_id=res_id or False)

        attachments = []
        # Add report in attachments
        if template.report_template:
            report_name = self.render_template(cr, uid, template.report_name, template.model, res_id, context=context)
            report_service = 'report.' + report_xml_pool.browse(cr, uid, template.report_template.id, context).report_name
            # Ensure report is rendered using template's language
            ctx = context.copy()
            if template.lang:
                ctx['lang'] = self.render_template(cr, uid, template.lang, template.model, res_id, context)
            service = netsvc.LocalService(report_service)
            #print '==========>', context
            if template.model == 'hr_deputy_timesheet_sheet.sheet':
                (result, format) = service.create(cr, uid, [res_id], {'model': template.model, 'form': context.get('form')}, ctx)
            else:
                (result, format) = service.create(cr, uid, [res_id], {'model': template.model}, ctx)
            result = base64.b64encode(result)
            if not report_name:
                report_name = report_service
            ext = "." + format
            if not report_name.endswith(ext):
                report_name += ext
            attachments.append((report_name, result))

        # Add template attachments
        for attach in template.attachment_ids:
            attachments.append((attach.datas_fname, attach.datas))

        values['attachments'] = attachments
        return values


#~ class resource_resource(osv.osv):
    #~ _inherit = "resource.resource"
    #~ _order = "name asc"
