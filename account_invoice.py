# -*- coding: utf-8 -*-

import time
from lxml import etree
import openerp.addons.decimal_precision as dp
import openerp.exceptions

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class account_invoice_line(osv.osv):

    _inherit = "account.invoice.line"
    _columns = {
        'configurator_id': fields.many2one('configurator',string='Configuration'),
        'composant': fields.boolean('Composant'),
        'produit_fini': fields.boolean('Produit fini'),
    }
