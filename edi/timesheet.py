# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.tools.translate import _
from openerp.addons.edi import EDIMixin

class hr_deputy_timesheet_sheet(osv.osv, EDIMixin):
    _inherit = 'hr_deputy_timesheet_sheet.sheet'