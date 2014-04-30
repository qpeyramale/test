# -*- coding: utf-8 -*-

import time
from datetime import datetime
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv, orm

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    
    _columns = {
        'interimaire': fields.boolean(u'Intérimaire'),
        'partner_id': fields.many2one('res.partner', 'Société d\'intérimaires', required=True),
    }
    _defaults = {
     }
     

hr_employee()

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
            'name': _('Open Timesheet'),
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
        'timesheet_ids': fields.one2many('hr.deputy.analytic.timesheet', 'sheet_id',
            'Timesheet lines',
            readonly=True, states={
                'draft': [('readonly', False)],
                'new': [('readonly', False)]}
            ),
        'user_id': fields.many2one('res.users', 'User', required=True, select=1, states={'confirm':[('readonly', True)], 'done':[('readonly', True)]}),
        #'company_id': fields.many2one('res.company', 'Company'),
        #'department_id':fields.many2one('hr.department','Department'),
        'state' : fields.selection([
            ('new', 'New'),
            ('draft','Open'),
            ('confirm','Waiting Approval'),
            ('done','Approved')], 'Status', select=True, required=True, readonly=True,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed timesheet. \
                \n* The \'Confirmed\' status is used for to confirm the timesheet by user. \
                \n* The \'Done\' status is used when users timesheet is accepted by his/her senior.'),
    }
    
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
    
    _columns = {
        'name': fields.char(u'Nom', size=64),
        'date': fields.date('Date', required=True, select=True),
        'employee_id': fields.many2one('hr.employee', "Employee"),
        'sheet_id': fields.function(_sheet, string='Sheet', type='many2one', relation='hr_deputy_timesheet_sheet.sheet', ondelete="cascade",
                        store={
                            'hr_deputy_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                            #'account.analytic.line': (_get_account_analytic_line, ['user_id', 'date'], 10),
                            'hr.deputy.analytic.timesheet': (lambda self,cr,uid,ids,context=None: ids, None, 10),
                        },
        ),
        'unit_amount': fields.float('Units'),
        'user_id': fields.related('sheet_id', 'user_id', type="many2one", relation="res.users", store=True, string="User", required=False, readonly=True),
        #'line_id': fields.many2one('account.analytic.line', 'Analytic Line', ondelete='cascade', required=True),
    }
    
    def _get_default_date(self, cr, uid, context=None):
        return fields.date.context_today(self, cr, uid, context=context)

    def __get_default_date(self, cr, uid, context=None):
        return self._get_default_date(cr, uid, context=context)
    
    _defaults = {
        'date': __get_default_date,
    }

#~ class resource_resource(osv.osv):
    #~ _inherit = "resource.resource"
    #~ _order = "name asc"
