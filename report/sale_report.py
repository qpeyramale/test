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

import time
from report import report_sxw

class simpac_sale_report(report_sxw.rml_parse):
    
    _name = "simpac.sale.report"
    
    def __init__(self, cr, uid, name, context):
        super(simpac_sale_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_amounts' : self._get_amounts,
        })
        
    def _get_amounts(self, line):
        
        retour = []
        for obj_tax in line.tax_id:
            if obj_tax.type == 'percent':
                retour.append(str(100*obj_tax.amount)+'%')
            elif obj_tax.type == 'fixed':
                retour.append(str(obj_tax.amount))
        #print '==========>', retour
        return ', '.join(retour)

report_sxw.report_sxw(
    'report.simpac_report_sale',
    'sale.order',
    'addons/sudokeys_simpac/report/sale_report.rml',
    header=True,
    parser=simpac_sale_report
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
