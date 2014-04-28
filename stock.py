# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
from openerp.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class stock_picking(osv.osv):
    _inherit = "stock.picking"

    _columns = {
        'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
    }

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"

    _columns = {
        'order_line_ids': fields.related('sale_id','order_line',type='one2many', relation='sale.order.line', string='Lignes de commande',readonly=True),
    }
 
