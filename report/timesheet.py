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

from datetime import date, time, datetime, timedelta
import time
from report import report_sxw
from osv import osv
import pooler

class simpac_timesheet(report_sxw.rml_parse):
    
    _name = 'simpac.timesheet'
    
    def __init__(self, cr, uid, name, context):
        super(simpac_timesheet, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'total_amount': {},
            'time': time.strftime('%d/%m/%y %H:%M',time.localtime()),
            'get_partners' : self._get_partners,
            'get_partner_name': self._get_partner_name,
            'get_lines' : self._get_lines,
            'get_days' : self._get_days,
            'get_day' : self._get_day,
        })
        
    def _get_day(self, date_from, timedel):
        
        array_date_from = date_from.split('-')

        d = date(int(array_date_from[0]), int(array_date_from[1]), int(array_date_from[2]))
        d += timedelta(days=timedel)
        #print d.strftime('%d/%m/%Y')
        return d.strftime('%d/%m/%Y')
        
    def _get_days(self, date_from, date_to):
        retour = []
        array_date_from = date_from.split('-')
        retour.append(array_date_from[2]+'/'+array_date_from[1]+'/'+array_date_from[0])
        #Nombre de jours à générer
        number = 6

        d = date(int(array_date_from[0]), int(array_date_from[1]), int(array_date_from[2]))
        for i in range(number):
            d += timedelta(days=1)
            retour.append(d.strftime('%d/%m/%Y'))
        #print retour
        return retour
    
    def _get_partner_name(self, partner_id):
        
        obj_partner = self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
        return obj_partner.name
    
    def _get_partners(self, timesheet_sheet, data):
        
        retour = []
        if data.has_key('form') and data['form'].has_key('partner_id') and data['form']['partner_id']:
            retour = [data['form']['partner_id'][0]]
        else:
            for timesheet in timesheet_sheet.timesheet_ids:
                #print timesheet.employee_id.partner_id.id,' ? ',timesheet.employee_id.partner_id.id not in retour
                if timesheet.employee_id.partner_id.id not in retour:
                    retour.append(timesheet.employee_id.partner_id.id)
        #print 'partners =====>', retour        
        return retour

    def _get_lines(self,timesheet_sheet, partner_id):
        tmp_lines = {}
        total = 0
        #------------------ dates ----------------------------------------------
        days = self._get_days(timesheet_sheet.date_from, timesheet_sheet.date_to)
        #-----------------------------------------------------------------------
        previous_partner = 0
        for timesheet in timesheet_sheet.timesheet_ids:
            if partner_id == timesheet.employee_id.partner_id.id:
                if tmp_lines.has_key(timesheet.employee_id.id):
                    array_date = timesheet.date.split('-')
                    for k,day in enumerate(days):
                        #print k
                        if day == array_date[2]+'/'+array_date[1]+'/'+array_date[0]:
                            tmp_lines[timesheet.employee_id.id][day] += timesheet.unit_amount
                            tmp_lines[timesheet.employee_id.id]['total'] += timesheet.unit_amount
                            total += timesheet.unit_amount
                else:
                    tmp_lines[timesheet.employee_id.id] = {}
                    tmp_lines[timesheet.employee_id.id]['name'] = timesheet.employee_id.name
                    tmp_lines[timesheet.employee_id.id]['partner'] = timesheet.employee_id.partner_id.name
                    tmp_lines[timesheet.employee_id.id]['partner_id'] = timesheet.employee_id.partner_id
                    tmp_lines[timesheet.employee_id.id]['total'] = 0
                    array_date = timesheet.date.split('-')
                    for day in days:
                        if day == array_date[2]+'/'+array_date[1]+'/'+array_date[0]:
                            tmp_lines[timesheet.employee_id.id][day] = timesheet.unit_amount
                            tmp_lines[timesheet.employee_id.id]['total'] = timesheet.unit_amount
                            total += timesheet.unit_amount
                        else:
                            tmp_lines[timesheet.employee_id.id][day] = 0
        lines = []
        for k, line in tmp_lines.iteritems():
            lines.append(line)
        
        total_amount = self.localcontext.get('total_amount')
        total_amount[partner_id] = total
        self.localcontext.update({
            'total_amount': total_amount,
        })    
            
        #print '=====>', lines
        
        return lines

report_sxw.report_sxw(
    'report.simpac.timesheet',
    'hr_deputy_timesheet_sheet.sheet',
    'addons/sudokeys_simpac/report/timesheet.rml',
    parser=simpac_timesheet)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
