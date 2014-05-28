# -*- coding: utf-8 -*-

import time
from report import report_sxw
from osv import osv
import pooler

class bdx_depot_courrier_en(report_sxw.rml_parse):
    
    _name = "bdx.depot.courrier.en"
    
    def __init__(self, cr, uid, name, context):
        super(bdx_depot_courrier_en, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
        

report_sxw.report_sxw(
    'report.bdx_depot_courrier_en',
    'stock.picking.out',
    'addons/sudokeys_simpac/report/bdx_depot_courrier_en.rml',
    parser=bdx_depot_courrier_en)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
