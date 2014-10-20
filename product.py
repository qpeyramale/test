# -*- coding: utf-8 -*-

import math
import re


from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class product_product(osv.osv):
    
    def _get_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id]=0.0
            if not product.margin_perso and product.categ_id and product.categ_id.margin and 'categ_margin' in context:
                res[product.id] = context.get('categ_margin')
            elif not product.margin_perso and product.categ_id and product.categ_id.margin:
                res[product.id] = product.categ_id.margin
            elif product.standard_price>0:
                res[product.id] = ((product.list_price/product.standard_price)-1.0)*100.0
        return res
    
    def _set_margin(self, cursor, user, id, name, value, arg, context=None):
        product = self.browse(cursor, user, id, context=context)
        return self.write(cursor, user, id, {'list_price': product.standard_price*(1.0+(value/100.0))}, context=context)
    
    def _get_margin_category(self, cr, uid, ids, context=None):
        res = []
        for categ in self.pool.get('product.category').browse(cr, uid, ids, context=context):
            if categ.margin:
                res.append(categ.id)
        return res
    
    def create(self, cr, uid, vals, context=None):
        categ_margin=0.0
        if vals.get('categ_id'):
            categ_margin=self.pool.get('product.category').read(cr,uid,vals.get('categ_id'),['margin'])['margin']
        if vals.get('margin_perso')==False:
            vals['list_price']=vals.get('standard_price')*(1.0+(categ_margin/100.0))
        elif vals.get('margin'):
            vals['list_price']=vals.get('standard_price')*(1.0+(vals.get('margin')/100.0))
        return super(product_product, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid,ids, vals, context=None):
        if context is None:
            context={}
        if isinstance(ids, (str, int, long)):
            ids = [ids]
        product = self.browse(cr, uid, ids[0], context=context)
        if 'margin_perso' in vals:
            margin_perso=vals.get('margin_perso')
        else:
            margin_perso=product.margin_perso
        if margin_perso==False:
            if 'margin_perso' in vals:
                if 'categ_margin' in context:
                    margin=context.get('categ_margin')
                else:
                    margin=product.categ_id.margin
                if 'standard_price' in vals:
                    vals['list_price']=vals.get('standard_price')*(1.0+(margin/100.0))
                if 'list_price' not in vals and 'standard_price' not in vals:
                    vals['list_price']=product.standard_price*(1.0+(margin/100.0))
            elif 'standard_price' in vals:
                vals['list_price']=vals.get('standard_price')*(1.0+(product.margin/100.0))
            elif 'list_price' in vals:
                vals['standard_price']=vals.get('list_price')*(1.0-(product.margin/100.0))
        elif 'list_price' in vals and 'standard_price' in vals:
            vals['list_price']=vals.get('standard_price')*(1.0+(product.margin/100.0))
        return super(product_product,self).write(cr, uid, ids,vals, context=context)
    
    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
            if code:
                #MODIF ORIGINAL
                #~ name = '[%s] %s' % (code,name)
                name = '%s' % (name,)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'default_code': product.default_code,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result
    
    def _get_tags(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = ','.join(tag.name for tag in product.tag_ids)
        return res
        
    def _get_tags_search(self, cr, uid, obj, name, domain, context=None):
        res=[]
        if domain==[('tag_ids_fnct', '!=', 'ImpOff')]:
            cr.execute('''select id from product_product pp
                where pp.id not in
                (select distinct pp.id
                from product_product pp
                join product_product_product_tags_rel ppptr on ppptr.product_product_id=pp.id
                join product_tags pt on pt.id=ppptr.product_tags_id and pt.name='ImpOff') ''')
            res = cr.fetchall()
        return [('id', 'in', map(lambda x: x[0], res))]
    
    _inherit = "product.product"
    _columns = {
        'tag_ids': fields.many2many('product.tags',string='Tags'),
        'tag_ids_fnct': fields.function(_get_tags,type='char',string='Tags fnct',fnct_search=_get_tags_search),
        'margin_perso': fields.boolean(u'Marge détaché de la famille'),
        'margin': fields.function(_get_margin,fnct_inv=_set_margin,string=u"Marge",digits=(12,2),type="float",
            store = {
                'product.product': (lambda self,cr,uid,ids,c=None: ids, ['list_price','standard_price'], 10),
                #~ 'product.category': (_get_margin_category, ['margin'], 10),
            }),
        'plis_mini': fields.integer('Nombre de plis mini'),
        'plis_maxi': fields.integer('Nombre de plis maxi'),
        'masse_mini': fields.integer('Masse d\'1 pli mini'),
        'masse_maxi': fields.integer('Masse d\'1 pli maxi'),
        'delai': fields.integer(u'Délai'),
        #surtaxe
        #~ 'affran_surtaxe': fields.boolean('Surtaxe'),
        #~ 'tarif10g_seuil1': fields.float('Tarif par tranche de 10g niv 1'),
        #~ 'tarif10g_seuil2': fields.float('Tarif par tranche de 10g niv 2'),
        #en nombre
        'affran_en_nombre': fields.boolean('En nombre'),
        'tarif35g': fields.float('Tarif 35g'),
        'tarif_objet': fields.float('Tarif par objet'),
        'tarif_kg': fields.float('Tarif au kg'),
        
    }
    
    _order = 'name_template'

class product_category(osv.osv):

    _inherit = "product.category"
    
    def write(self, cr, uid,ids, vals, context=None):
        if context is None:
            context={}
        if isinstance(ids, (str, int, long)):
            ids = [ids]
        categ = self.browse(cr, uid, ids[0], context=context)
        if 'margin' in vals:
            margin=vals.get('margin')
        else:
            margin=categ.margin
        products=self.pool.get('product.product').search(cr,uid,[('categ_id','=',ids[0]),('margin_perso','=',False)])
        for product in self.pool.get('product.product').browse(cr,uid,products,context):
            #~ self.pool.get('product.product').write(cr,uid,product.id,{'list_price':product.standard_price*(1.0+(margin/100.0))})
            context.update({'categ_margin':margin})
            self.pool.get('product.product').write(cr,uid,product.id,{'margin_perso':False},context)
        return super(product_category,self).write(cr, uid, ids,vals, context=context)
    
    _columns = {
        'taux': fields.integer('Taux'),
        'margin': fields.float('Marge sur les produits enfants',help="Ne s'applique seulement que pour la catégorie directement parente aux produit"),
        #surtaxe
        'poids_min': fields.integer('Poids minimal'),
        'tarif10g_seuil1': fields.float('Tarif par tranche de 10g niv 1'),
        'tarif10g_seuil2': fields.float('Tarif par tranche de 10g niv 2'),
        #en nombre
        'tarif35g': fields.float('Tarif 35g'),
        'tarif_objet': fields.float('Tarif par objet'),
        'tarif_kg': fields.float('Tarif au kg'),
    }
class product_tags(osv.osv):

    _name = "product.tags"
    _columns = {
        'name': fields.char(u'Libellé'),
    }

