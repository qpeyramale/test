# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class configurator_product_line(osv.osv_memory):
    _name = "configurator.product.line"
    
    _columns = {
        'conf_id': fields.many2one('configurator','Configurateur'),
        'product_id': fields.many2one('product.product','Composant'),
        'cout': fields.float(u'Coût'),
        'quantite': fields.float(u'Quantité'),
    }
class configurator_workcenter_line(osv.osv_memory):
    _name = "configurator.workcenter.line"
    
    _columns = {
        'conf_id': fields.many2one('configurator','Configurateur'),
        'workcenter_id': fields.many2one('mrp.workcenter',u'Tâche'),
        'cout_marche': fields.float(u'Coût marché'),
        'cout_theo': fields.float(u'Coût théorique'),
        'quantite': fields.float(u'Quantité'),
        'temps': fields.float(u'Temps'),
    }

class configurator(osv.osv_memory):
    _name = "configurator"
    _description = "Configurator"
    _columns = {
        
        'atelier': fields.selection([
            ('editique', 'Editique'),
            ('faconnage', 'Faconnage'),
            ('numerique', 'Numerique'),
            ('offset', 'Offset'),
            ('routage', 'Routage'),
            ], 'Atelier',
            help="Famille d'articles"),
        'atelier_id': fields.many2one('product.category','Atelier'),
        'article_id': fields.many2one('product.product','Article'),
        'article_code': fields.char('Code article'),
        'name': fields.text('Nom'),
        'quantite': fields.integer(u'Quantité'),
        
        #ATELIER OFFSET : Impression offset sur enveloppes
        'quantite_env': fields.integer(u'Quantité d\'enveloppes à fabriquer'),
        'produit_env': fields.many2one('product.product','Enveloppes'),
        'env_fournies': fields.boolean('Enveloppes fournies par nous',help="Coché pour Oui"),
        'impression_env': fields.selection([
            ('10', '1:0'),
            ('11', '1:1'),
            ('20', '2:0'),
            ('21', '2:1'),
            ('22', '2:2'),
            ('40', '4:0'),
            ('41', '4:1'),
            ('42', '4:2'),
            ('44', '4:4'),
            ], u'Type d\'impression',
            help="Type d'impression"),
        #ATELIER OFFSET : Impression offset sur papier
        'quantite_pap': fields.integer(u'Quantité de documents à imprimer'),
        'produit_pap': fields.many2one('product.product','Papier'),
        'pose_pap': fields.integer('Nombre de poses',help="Nombre de documents par feuille"),
        'impression_pap': fields.selection([
            ('10', '1:0'),
            ('11', '1:1'),
            ('20', '2:0'),
            ('21', '2:1'),
            ('22', '2:2'),
            ('40', '4:0'),
            ('41', '4:1'),
            ('42', '4:2'),
            ('44', '4:4'),
            ], u'Type d\'impression',
            help="Type d'impression"),
        #ATELIER OFFSET : Impression jet d’encre
        'quantite_jet': fields.integer(u'Quantité d\'enveloppes à imprimer'),
        'produit_jet': fields.many2one('product.product','Enveloppes'),
        'zone_jet': fields.selection([
            ('petite', 'Petite'),
            ('grande', 'Grande.'),
            ], u'Zone d\'impression',
            help="Zone d\'impression"),
        'jet_fournies': fields.boolean('Enveloppes fournies par nous',help="Coché pour Oui"),
        'adressage_jet': fields.boolean('Adressage',help="Coché pour Oui"),
        'impression_jet': fields.selection([
            ('recto', 'recto seul'),
            ('recto_verso', 'recto-verso'),
            ], u'Type d\'impression',
            help="Type d'impression"),
        #ATELIER EDITIQUE : Campagne email
        'quantite_email': fields.integer(u'Quantité d\'email à envoyer'),
        'heures_email': fields.integer(u'Nombre d\'heures développement spécifique'),
        'notes_email': fields.text(u'Notes sur le développement spécifique'),
        #ATELIER EDITIQUE : Préparation données
        'type_prepa': fields.selection([
            ('simple', 'Simple'),
            ('complexe', 'Complexe'),
            ('specifique', 'Spécifique'),
            ], u'Type de travail',
            help="Type de travail"),
        'heures_prepa': fields.integer(u'Nombre d\'heures'),
        #ATELIER NUMERIQUE : Fabrication d’un imprimé
        'quantite_imp': fields.integer(u'Quantité d\'imprimés à fabriquer'),
        'perso_imp': fields.selection([
            ('sans', 'Sans'),
            ('simple', 'Simple'),
            ('param', 'Param.'),
            ], u'Personalisation',
            help="Personalisation"),
        'impression_imp': fields.selection([
            ('10', '1:0'),
            ('11', '1:1'),
            ('40', '4:0'),
            ('41', '4:1'),
            ('44', '4:4'),
            ], u'Type d\'impression',
            help="Type d'impression"),
        'pose_imp': fields.integer(u'Nombre de poses'),
        'produit_imp': fields.many2one('product.product','Papier'),
        'perforation_imp': fields.boolean('Perforation',help="Coché pour Oui"),
        'rainage_imp': fields.boolean('Rainage',help="Coché pour Oui"),
        'pliage_imp': fields.boolean('Pliage',help="Coché pour Oui"),
        
        'conf_product_lines': fields.one2many('configurator.product.line','conf_id',u'Détails composants'),
        'conf_workcenter_lines': fields.one2many('configurator.workcenter.line','conf_id',u'Détails tâches'),
        'prix_revient': fields.float('Prix de revient des composants'),
        'prix_theo': fields.float(u'Estimation du coût des tâches (théorique)'),
        'prix_marche': fields.float(u'Estimation du coût des tâches (marché)'),
        'prix_global_theo': fields.float(u'Prix global proposé (théorique)'),
        'prix_global_marche': fields.float(u'Prix global proposé (marché)'),
        'prix_offert': fields.float(u'Prix de vente offert'),
    }
    _defaults = {
        'perso_imp': lambda *a: 'sans',
    }

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        order = self.pool.get('sale.order').browse(cr, uid, record_id, context=context)
        if not order.partner_id:
            raise osv.except_osv(_('Warning!'), _('Pas de client.'))
        return False
    
    def onchange_article(self, cr, uid, ids, article_id, context=None):
        v = {}
        mrp_bom=self.pool.get('mrp.bom')
        conf_product_lines=[]
        conf_workcenter_lines=[]
        if article_id:
            article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
            if article.default_code:
                v['article_code'] = article.default_code
            mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
            if mrp_bom_id:
                bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                for bom_line in bom.bom_lines:
                    conf_product_lines.append({'product_id':bom_line.product_id.id})
                v['conf_product_lines'] = conf_product_lines
                if bom.routing_id:
                    for workcenter_line in bom.routing_id.workcenter_lines:
                        conf_workcenter_lines.append({'workcenter_id':workcenter_line.workcenter_id.id})
                v['conf_workcenter_lines'] = conf_workcenter_lines
        return {'value': v}
    
    #ATELIER OFFSET : Impression offset sur enveloppes
    def onchange_enveloppe(self, cr, uid, ids, quantite_env,produit_env,env_fournies,
        impression_env,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0
        produit_env_browse=False
        if produit_env:
            produit_env_browse=product_obj.browse(cr,uid,produit_env)
        if produit_env and produit_env not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
            if len(conf_product_lines)==3:
                del conf_product_lines[-1]
            conf_product_lines.append([0,False,{'product_id':produit_env}])
            produit_env_browse=product_obj.browse(cr,uid,produit_env)
        
        for product in conf_product_lines:
            if product[2]:
                products.append(product[2]['product_id'])
                prod=product_obj.browse(cr,uid,product[2]['product_id'])
                #[Env/???]
                if env_fournies and product[2]['product_id']==produit_env:
                    product[2]['cout']=quantite_env*prod.list_price
                    product[2]['quantite']=quantite_env
                elif product[2]['product_id']==produit_env:
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                #[Off/Plaque]
                if prod.name=='Plaque' and impression_env:
                    product[2]['cout']=(int(impression_env[0])+int(impression_env[1]))*prod.list_price
                    product[2]['quantite']=(int(impression_env[0])+int(impression_env[1]))
                prix_revient+=product[2]['cout']
        for workcenter in conf_workcenter_lines:
            if workcenter[2] and impression_env:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_env/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0
                #[Off/Pla/Offset]
                if work.name=='Offset : Sortie plaque':
                    workcenter[2]['cout_theo']=(int(impression_env[0])+int(impression_env[1]))*work.prix_theo_variable + work.prix_theo_fixe
                    workcenter[2]['cout_marche']=(int(impression_env[0])+int(impression_env[1]))*work.prix_marche_variable + work.prix_marche_fixe
                    workcenter[2]['quantite']=(int(impression_env[0])+int(impression_env[1]))
                    workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 1 couleur]
                if work.name=='Offset : Calage 1:0':
                    if impression_env in ('10','21','41'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_env in ('11'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 2 couleurs]
                if work.name=='Offset : Calage 2:0':
                    if impression_env in ('20','21','42'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_env in ('22'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 4 couleurs]
                if work.name=='Offset : Calage 4:0':
                    if impression_env in ('40','41','42'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_env in ('44'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Rou/Offset:Roulage]
                if work.name=='Offset : Roulage':
                    if produit_env_browse and not produit_env_browse.tag2:
                        workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_env + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_env + work.prix_marche_fixe 
                        workcenter[2]['quantite']=quantite_env
                        workcenter[2]['temps']=temps
                if work.name=='Offset : Roulage grand format':
                    if produit_env_browse and produit_env_browse.tag2 == 'Grandes':
                        workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_env + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_env + work.prix_marche_fixe 
                        workcenter[2]['quantite']=quantite_env
                        workcenter[2]['temps']=temps
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
              
        a=quantite_env
        b=produit_env_browse and produit_env_browse.name or 'N/A'
        c=env_fournies and ' ' or ' - Enveloppes fournies par vos soins.'
        if impression_env:
            d=impression_env[0] + ' couleur(s) recto et ' + impression_env[1] + ' couleur(s) verso'
        else: d='N/A'
        v['name'] = 'Fourniture de ' + str(a) + ' enveloppes ' + b + u' imprimées ' + d + c
            
        v['quantite'] = quantite_env
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}
    
    #ATELIER OFFSET : Impression jet d’encre
    def onchange_jet(self, cr, uid, ids, quantite_jet,produit_jet,jet_fournies,
        impression_jet, zone_jet,adressage_jet,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0
        produit_jet_browse=False
        if produit_jet:
            produit_jet_browse=product_obj.browse(cr,uid,produit_jet)
        if produit_jet and produit_jet not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
            if len(conf_product_lines)==3:
                del conf_product_lines[-1]
            conf_product_lines.append([0,False,{'product_id':produit_jet}])
            produit_jet_browse=product_obj.browse(cr,uid,produit_jet)
        
        for product in conf_product_lines:
            if product[2]:
                products.append(product[2]['product_id'])
                prod=product_obj.browse(cr,uid,product[2]['product_id'])
                #[Env/???]
                if jet_fournies and product[2]['product_id']==produit_jet:
                    product[2]['cout']=quantite_jet*prod.list_price
                    product[2]['quantite']=quantite_jet
                elif product[2]['product_id']==produit_jet:
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                prix_revient+=product[2]['cout']
        for workcenter in conf_workcenter_lines:
            if workcenter[2] and impression_jet:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_jet/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0
                #[Rou/Adr/Adressage préparation]
                if work.name==u'Adressage : Préparation':
                    if adressage_jet:
                        workcenter[2]['cout_theo']=quantite_jet*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=quantite_jet*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=quantite_jet
                        workcenter[2]['temps']=temps
                #[Off/Jet/Impression jet d'encre petite image]
                if work.name=='Impression jet d\'encre petite image':
                    if not adressage_jet and zone_jet=='petite':
                        if impression_jet == 'recto':
                            workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_jet + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_jet + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_jet
                            workcenter[2]['temps']=temps
                        else:
                            workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_jet*2) + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_jet*2) + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_jet*2
                            workcenter[2]['temps']=temps
                #[Off/Jet/Impression jet d’encre grande image]
                if work.name=='Impression jet d\'encre grande image':
                    if adressage_jet or zone_jet=='grande':
                        if impression_jet == 'recto':
                            workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_jet + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_jet + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_jet
                            workcenter[2]['temps']=temps
                        else:
                            workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_jet*2) + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_jet*2) + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_jet*2
                            workcenter[2]['temps']=temps
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
              
        a=quantite_jet
        b=produit_jet_browse and produit_jet_browse.name or 'N/A'
        c=jet_fournies and ' ' or ' - Enveloppes fournies par vos soins.'
        if impression_jet=='recto':
            d=' recto seul '
        elif impression_jet=='recto_verso':
            d=' recto-verso '
        else: d='N/A'
        f=adressage_jet and u' et personalisées' or ' '
        v['name'] = 'Fourniture de ' + str(a) + ' enveloppes ' + b + u' imprimées ' + d + f + c
            
        v['quantite'] = quantite_jet
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}
    
    #ATELIER OFFSET : Impression offset sur papier
    def onchange_papier(self, cr, uid, ids, quantite_pap,produit_pap,pose_pap,
        impression_pap,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0
        produit_pap_browse=False
        if produit_pap:
            produit_pap_browse=product_obj.browse(cr,uid,produit_pap)
        if produit_pap and produit_pap not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
            if len(conf_product_lines)==3:
                del conf_product_lines[-1]
            conf_product_lines.append([0,False,{'product_id':produit_pap}])
            produit_pap_browse=product_obj.browse(cr,uid,produit_pap)
        if pose_pap==0:
            pose_pap2=1
        else:
            pose_pap2=pose_pap
        for product in conf_product_lines:
            if product[2]:
                products.append(product[2]['product_id'])
                prod=product_obj.browse(cr,uid,product[2]['product_id'])
                #[Pap/???]
                if product[2]['product_id']==produit_pap:
                    product[2]['cout']=(quantite_pap/pose_pap2)*prod.list_price
                    product[2]['quantite']=(quantite_pap/pose_pap2)
                elif product[2]['product_id']==produit_pap:
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                #[Off/Plaque]
                if prod.name=='Plaque' and impression_pap:
                    product[2]['cout']=(int(impression_pap[0])+int(impression_pap[1]))*prod.list_price
                    product[2]['quantite']=(int(impression_pap[0])+int(impression_pap[1]))
                prix_revient+=product[2]['cout']
        for workcenter in conf_workcenter_lines:
            if workcenter[2] and impression_pap:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_pap/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0
                #[Off/Pla/Offset]
                if work.name=='Offset : Sortie plaque':
                    workcenter[2]['cout_theo']=(int(impression_pap[0])+int(impression_pap[1]))*work.prix_theo_variable + work.prix_theo_fixe
                    workcenter[2]['cout_marche']=(int(impression_pap[0])+int(impression_pap[1]))*work.prix_marche_variable + work.prix_marche_fixe
                    workcenter[2]['quantite']=(int(impression_pap[0])+int(impression_pap[1]))
                    workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 1 couleur]
                if work.name=='Offset : Calage 1:0':
                    if impression_pap in ('10','21','41'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_pap in ('11'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 2 couleurs]
                if work.name=='Offset : Calage 2:0':
                    if impression_pap in ('20','21','42'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_pap in ('22'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Cal/Offset:Calage 4 couleurs]
                if work.name=='Offset : Calage 4:0':
                    if impression_pap in ('40','41','42'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                    elif impression_pap in ('44'):
                        workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                        workcenter[2]['quantite']=2
                        workcenter[2]['temps']=temps
                #[Off/Rou/Offset:Roulage]
                if work.name=='Offset : Roulage grand format':
                    workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_pap/pose_pap2) + work.prix_theo_fixe 
                    workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_pap/pose_pap2) + work.prix_marche_fixe 
                    workcenter[2]['quantite']=(quantite_pap/pose_pap2)
                    workcenter[2]['temps']=temps
                #[Coupe]
                if work.name=='Coupe':
                    if pose_pap>0:
                        workcenter[2]['cout_theo']=4*pose_pap*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=4*pose_pap*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=4*pose_pap
                        workcenter[2]['temps']=temps
                    else:
                        workcenter[2]['cout_theo']=0.0
                        workcenter[2]['cout_marche']=0.0
                        workcenter[2]['quantite']=0.0
                        workcenter[2]['temps']=0.0  
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
              
        a=quantite_pap
        b=produit_pap_browse and produit_pap_browse.name or 'N/A'
        c=pose_pap
        if impression_pap:
           d=impression_pap[0] + ' couleur(s) recto et ' + impression_pap[1] + ' couleur(s) verso'
        else: d='N/A'
        v['name'] = 'Fourniture de ' + str(a) + ' documents ' + str(c) + u' imprimés sur papier ' + b + ' - Impression ' + d
            
        v['quantite'] = quantite_pap
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}
    
    #ATELIER EDITIQUE : Campagne email
    def onchange_email(self, cr, uid, ids, quantite_email,heures_email,notes_email,
        conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0
        for product in conf_product_lines:
            if product[2]:
                prod=product_obj.browse(cr,uid,product[2]['product_id'])
                #[Ema/Envoi]
                if prod.name=='Envoi':
                    product[2]['cout']=quantite_email*prod.list_price
                    product[2]['quantite']=quantite_email
                prix_revient+=product[2]['cout']
        for workcenter in conf_workcenter_lines:
            if workcenter[2]:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_pap/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0
                #[Edi/Ema/Email : Mise en page]
                if work.name=='Email : Mise en page':
                    workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                    workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                    workcenter[2]['quantite']=1
                    workcenter[2]['temps']=temps
                #[Edi/Ema/Email : Tests de campagne]
                if work.name=='Email : Test de campagne':
                    workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                    workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                    workcenter[2]['quantite']=1
                    workcenter[2]['temps']=temps
                #[Service : MO Editique]
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
              
        a=quantite_email
        b=heures_email
        if b>0:
            c=u'\nDéveloppement spécifique: ' + (notes_email and notes_email or ' ')
        else:
            c=' '
        v['name'] = u'Campagne email envoyée à ' +\
        str(a) +\
        u' destinataires.\nPréparation de la mise en page et tests de déliverabilité et de rendu inclus.\n' + c
            
        v['quantite'] = quantite_email
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}
        
    #ATELIER EDITIQUE : Préparation données
    def onchange_prepa(self, cr, uid, ids, type_prepa,heures_prepa,
        conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0

        for workcenter in conf_workcenter_lines:
            if workcenter[2]:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_pap/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0
                #[Edi/Dat/Data : Préparation données simples]
                if work.name==u'Data : Préparation données simple':
                    if type_prepa == 'simple':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                #[Edi/Dat/Data : Préparation données complexes]
                if work.name==u'Data : Préparation données complexe':
                    if type_prepa == 'complexe':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=temps
                #[Service : MO Editique]
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
              
        v['name'] = u'Forfait pour préparation des données'
            
        v['quantite'] = 0.0
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}
    
    #ATELIER NUMERIQUE : Fabrication d’un imprimé
    def onchange_imprime(self, cr, uid, ids, quantite_imp, perso_imp, impression_imp, pose_imp, produit_imp, 
        perforation_imp, rainage_imp, pliage_imp,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        product_obj=self.pool.get('product.product')
        workcenter_obj=self.pool.get('mrp.workcenter')
        products=[]
        workcenters=[]
        prix_revient=prix_theo=prix_marche=0.0
        produit_imp_browse=False
        if produit_imp:
            produit_imp_browse=product_obj.browse(cr,uid,produit_imp)
        if produit_imp and produit_imp not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
            if len(conf_product_lines)==4:
                del conf_product_lines[-1]
            conf_product_lines.append([0,False,{'product_id':produit_imp}])
            produit_imp_browse=product_obj.browse(cr,uid,produit_imp)
        if pose_imp==0:
            pose_imp2=1
        else:
            pose_imp2=pose_imp
        for product in conf_product_lines:
            if product[2]:
                products.append(product[2]['product_id'])
                prod=product_obj.browse(cr,uid,product[2]['product_id'])
                #[Pap/???]
                if product[2]['product_id']==produit_imp:
                    product[2]['cout']=(quantite_imp/pose_imp2)*prod.list_price
                    product[2]['quantite']=(quantite_imp/pose_imp2)
                if impression_imp:
                    #[Sor/Noir]
                    if prod.name=='Noir' and impression_imp in ('10','41'):
                        product[2]['cout']=(quantite_imp/pose_imp2)*prod.list_price
                        product[2]['quantite']=(quantite_imp/pose_imp2)
                    elif prod.name=='Noir' and impression_imp in ('11'):
                        product[2]['cout']=2*(quantite_imp/pose_imp2)*prod.list_price
                        product[2]['quantite']=2*(quantite_imp/pose_imp2)
                    elif prod.name=='Noir':
                        product[2]['cout']=0.0
                        product[2]['quantite']=0.0
                    #[Sor/Couleur]
                    if prod.name=='Couleur' and impression_imp in ('40','41'):
                        product[2]['cout']=(quantite_imp/pose_imp2)*prod.list_price
                        product[2]['quantite']=(quantite_imp/pose_imp2)
                    elif prod.name=='Couleur' and impression_imp in ('44'):
                        product[2]['cout']=2*(quantite_imp/pose_imp2)*prod.list_price
                        product[2]['quantite']=2*(quantite_imp/pose_imp2)
                    elif prod.name=='Couleur':
                        product[2]['cout']=0.0
                        product[2]['quantite']=0.0
                prix_revient+=product[2]['cout']
        for workcenter in conf_workcenter_lines:
            if workcenter[2] and impression_imp:
                workcenters.append(workcenter[2]['workcenter_id'])
                work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                temps = work.capacity_per_hour and (quantite_imp/work.capacity_per_hour) or 0.0 + work.time_cycle
                workcenter[2]['cout_theo']=0.0
                workcenter[2]['cout_marche']=0.0
                workcenter[2]['quantite']=0.0
                workcenter[2]['temps']=0.0   
                #[Fusion]
                if work.name=='Fusion simple':
                    if perso_imp=='simple':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['temps']=temps
                if work.name==u'Fusion paramétrée':
                    if perso_imp=='param':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['temps']=temps
                #[Sorties numériques]
                if work.name==u'Sorties numériques - n:0 SRA3 <135g':
                    if produit_imp_browse and produit_imp_browse.tag2=='inf.135':
                        if impression_imp in ('10','40'):
                            workcenter[2]['cout_theo']=(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                        if impression_imp in ('11','41','44'):
                            workcenter[2]['cout_theo']=2*(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=2*(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2*(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                if work.name==u'Sorties numériques - n:0 SRA3 <176g':
                    if produit_imp_browse and produit_imp_browse.tag2=='inf.176':
                        if impression_imp in ('10','40'):
                            workcenter[2]['cout_theo']=(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                        if impression_imp in ('11','41','44'):
                            workcenter[2]['cout_theo']=2*(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=2*(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2*(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                if work.name==u'Sorties numériques - n:0 SRA3 <300g':
                    if produit_imp_browse and produit_imp_browse.tag2=='inf.300':
                        if impression_imp in ('10','40'):
                            workcenter[2]['cout_theo']=(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                        if impression_imp in ('11','41','44'):
                            workcenter[2]['cout_theo']=2*(quantite_imp/pose_imp2)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=2*(quantite_imp/pose_imp2)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2*(quantite_imp/pose_imp2)
                            workcenter[2]['temps']=temps
                #[Coupe]
                if work.name=='Coupe':
                    if pose_imp>0:
                        workcenter[2]['cout_theo']=4*pose_imp*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=4*pose_imp*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=4*pose_imp
                        workcenter[2]['temps']=temps
                    else:
                        workcenter[2]['cout_theo']=0.0
                        workcenter[2]['cout_marche']=0.0
                        workcenter[2]['quantite']=0.0
                        workcenter[2]['temps']=0.0  
                #[Faconnage], [Rainage]
                if work.name=='Faconnage : Perforation':
                    if perforation_imp:
                        workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=quantite_imp
                        workcenter[2]['temps']=temps
                if work.name=='Faconnage : Rainage':
                    if rainage_imp:
                        workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=quantite_imp
                        workcenter[2]['temps']=temps
                #[Pliage]
                if work.name=='Pliage feuilles SRA3' and (produit_imp_browse and produit_imp_browse.tag1!='lourd'):
                    if pliage_imp:
                        if pose_imp==0 or pose_imp==1:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=temps
                if work.name=='Pliage feuilles SRA3 : Grammage lourd' and (produit_imp_browse and produit_imp_browse.tag1=='lourd'):
                    if pliage_imp:
                        if pose_imp==0 or pose_imp==1:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=temps
                if work.name=='Pliage feuilles A4' and (produit_imp_browse and produit_imp_browse.tag1!='lourd'):
                    if pliage_imp:
                        if pose_imp>1:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=temps
                if work.name=='Pliage feuilles A4 : Grammage lourd' and (produit_imp_browse and produit_imp_browse.tag1=='lourd'):
                    if pliage_imp:
                        if pose_imp>1:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=temps
                prix_marche+=workcenter[2]['cout_marche']
                prix_theo+=workcenter[2]['cout_theo']
                
        v['quantite'] = quantite_imp
        v['conf_product_lines'] = conf_product_lines
        v['conf_workcenter_lines'] = conf_workcenter_lines
        v['prix_revient'] = prix_revient
        v['prix_theo'] = prix_theo
        v['prix_marche'] = prix_marche
        v['prix_global_theo'] = prix_revient+prix_theo
        v['prix_global_marche'] = prix_revient+prix_marche
        v['prix_offert'] = prix_revient+prix_theo
        return {'value': v}

    def make_order_line(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('sale.order')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        newinv = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        for sale_order in order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            fpos = sale_order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
            for composant in self.pool.get('configurator.product.line').read(cr,uid,data['conf_product_lines'],['cout','product_id','quantite']):
                product=self.pool.get('product.product').browse(cr,uid,composant['product_id'][0])
                if composant['cout']:
                    self.pool.get('sale.order.line').create(cr, uid, {
                        'order_id': sale_order.id,
                        'name': product.name,
                        'price_unit': product.list_price,
                        'product_uom_qty': composant['quantite'],
                        'product_uos_qty': composant['quantite'],
                        'product_uos': product.uos_id.id,
                        'product_uom': product.uom_id.id,
                        'product_id': product.id,
                        'discount': False,
                        'tax_id': self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product.taxes_id),
                        'type': 'make_to_order',
                        'delay':0,
                        'state':'draft',
                    }, context)
            self.pool.get('sale.order.line').create(cr, uid, {
                'order_id': sale_order.id,
                'name': data['name'],
                'price_unit': data['prix_offert']/data['quantite'],
                'product_uom_qty': data['quantite'],
                'product_uos_qty': data['quantite'],
                #~ 'product_uos': product.uos_id.id,
                #~ 'product_uom': product.uom_id.id,
                'product_id': False,
                'discount': False,
                #~ 'tax_id': self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product.taxes_id),
                'type': 'make_to_order',
                'delay':0,
                'state':'draft',
            }, context)
        return {}

configurator()
