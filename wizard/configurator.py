# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class configurator_edit(osv.osv_memory):
    _name = "configurator.edit"
    
    _columns = {
        'name': fields.many2one('configurator',u'Configuration à éditer'),
    }

class configurator_product_line(osv.osv):
    _name = "configurator.product.line"
    
    _columns = {
        'conf_id': fields.many2one('configurator','Configurateur'),
        'product_id': fields.many2one('product.product','Composant'),
        'cout': fields.float(u'Coût'),
        'quantite': fields.float(u'Quantité'),
    }
class configurator_workcenter_line(osv.osv):
    _name = "configurator.workcenter.line"
    
    _columns = {
        'conf_id': fields.many2one('configurator','Configurateur'),
        'workcenter_id': fields.many2one('mrp.workcenter',u'Tâche'),
        'cout_marche': fields.float(u'Coût marché'),
        'cout_theo': fields.float(u'Coût théorique'),
        'quantite': fields.float(u'Quantité'),
        'temps': fields.float(u'Temps',digits=(12,3)),
    }

class configurator(osv.osv):
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
        'name': fields.text('Nom',required=True),
        'quantite': fields.integer(u'Quantité'),
        
        'sale_id': fields.many2one('sale.order','Bon de commande'),
        
        #ATELIER OFFSET : Impression offset sur enveloppes
        'quantite_env': fields.integer(u'Quantité d\'enveloppes à fabriquer'),
        'produit_env': fields.many2one('product.product','Enveloppes'),
        'env_fournies': fields.boolean('Enveloppes fournies par le client',help="Coché pour Oui"),
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
        'pose_l_pap': fields.integer('Longueur',help="Longueur<450 / Largeur<320"),
        'pose_w_pap': fields.integer('Largeur'),
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
        'perforation_pap': fields.boolean('Perforation',help="Coché pour Oui"),
        'rainage_pap': fields.boolean('Rainage',help="Coché pour Oui"),
        'pliage_pap': fields.boolean('Pliage',help="Coché pour Oui"),
        #ATELIER OFFSET : Impression jet d'encre
        'quantite_jet': fields.integer(u'Quantité d\'enveloppes à imprimer'),
        'produit_jet': fields.many2one('product.product','Enveloppes'),
        'zone_jet': fields.selection([
            ('petite', 'Petite'),
            ('grande', 'Grande'),
            ], u'Zone d\'impression',
            help="Zone d\'impression"),
        'jet_fournies': fields.boolean('Enveloppes fournies par le client',help="Coché pour Oui"),
        'adressage_jet': fields.boolean('Adressage',help="Coché pour Oui"),
        'impression_jet': fields.selection([
            ('recto', 'Recto'),
            ('recto_verso', 'Recto/Verso'),
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
        #ATELIER FACONNAGE : Collage de documents
        'quantite_col': fields.integer(u'Nombre de documents à coller'),
        'bandes_col': fields.integer(u'Nombre de bandes de collage'),
        'pliures_col': fields.integer(u'Nombre de pliures à marquer'),
        'stockage_col': fields.selection([
            ('vrac', 'Vrac'),
            ('carton', 'Carton'),
            ], u'Stockage',
            help="Stockage"),
        'cartons_col': fields.integer(u'Nombre de documents'),
        'realisation_col': fields.selection([
            ('interne', 'Interne'),
            ('interim', 'Intérimaires'),
            ], u'Réalisation',
            help="Par carton"),
        #ATELIER FACONNAGE : Travaux divers
        'note_div': fields.text(u'Note calcul'),
        'heures_div': fields.integer(u'Nombre heures MO'),
        'produit1_div': fields.many2one('product.product','Fourniture 1'),
        'quantite1_div': fields.integer(u'Quantité fourniture 1'),
        'produit2_div': fields.many2one('product.product','Fourniture 2'),
        'quantite2_div': fields.integer(u'Quantité fourniture 2'),
        #ATELIER FACONNAGE : Encartage
        'quantite_enc': fields.integer(u'Nb pièces à encarter'),
        'depose_enc': fields.boolean(u'Dépose avec point de colle'),
        'type_enc': fields.selection([
            ('placee', 'Placée'),
            ('non_placee', 'Non placée'),
            ], u'Type de dépose',
            help="Type de dépose"),
        'stockage_enc': fields.selection([
            ('vrac', 'Vrac'),
            ('carton', 'Carton'),
            ], u'Stockage',
            help="Stockage"),
        'cartons_enc': fields.integer(u'Nombre de doc par carton'),
        'realisation_enc': fields.selection([
            ('interne', 'Interne'),
            ('interim', 'Intérimaires'),
            ], u'Réalisation',
            help="Réalisation"),
        #ATELIER NUMERIQUE : Fabrication d’un imprimé
        'quantite_imp': fields.integer(u'Quantité d\'imprimés à fabriquer'),
        'perso_imp': fields.selection([
            ('sans', 'Sans'),
            ('simple', 'Simple'),
            ('complexe', 'Complexe'),
            ], u'Personnalisation',
            help="Personnalisation"),
        'mise_page_imp': fields.selection([
            ('simple', 'Simple'),
            ('param', 'Paramétrée'),
            ], u'Mise en page',
            help="Mise en page"),
        'impression_imp': fields.selection([
            ('10', '1:0'),
            ('11', '1:1'),
            ('40', '4:0'),
            ('41', '4:1'),
            ('44', '4:4'),
            ], u'Type d\'impression',
            help="Type d'impression"),
        'pose_l_imp': fields.integer('Longueur',help="Longueur<450 / Largeur<320"),
        'pose_w_imp': fields.integer('Largeur'),
        'produit_imp': fields.many2one('product.product','Papier'),
        'perforation_imp': fields.boolean('Perforation',help="Coché pour Oui"),
        'rainage_imp': fields.boolean('Rainage',help="Coché pour Oui"),
        'pliage_imp': fields.boolean('Pliage',help="Coché pour Oui"),
        #ATELIER NUMERIQUE : Fabrication de livres reliés en dos carré
        'quantite_liv': fields.integer(u'Nombre de livres'),
        'heures_liv': fields.integer(u'Heures de remise en page nécessaires'),
        'pose_l_liv': fields.integer('Longueur',help="Longueur<320 / Largeur<225"),
        'pose_w_liv': fields.integer('Largeur'),
        'pages_noir_liv': fields.integer('Nb de pages imprimées en noir'),
        'produit_noir_liv': fields.many2one('product.product','Papier pages noir'),
        'pages_couleur_liv': fields.integer('Nb de pages imprimées en couleur'),
        'produit_couleur_liv': fields.many2one('product.product','Papier pages couleur'),
        #ATELIER NUMERIQUE : Personnalisation d’un document
        'quantite_doc': fields.integer(u'Quantité d\'imprimés à fabriquer'),
        'mise_page_doc': fields.selection([
            ('simple', 'Simple'),
            ('complexe', 'Complexe'),
            ], u'Mise en page',
            help="Mise en page"),
        'prepa_doc': fields.selection([
            ('simple', 'Simple'),
            ('complexe', 'Complexe'),
            ('par_ailleurs', 'Par ailleurs'),
            ], u'Préparation données',
            help="Préparation données"),
        'perso_doc': fields.selection([
            ('encre', 'Adressage jet d\'encre'),
            ('couleur', 'Laser couleur'),
            ('noir', 'Laser noir'),
            ], u'Procédé de personnalisation',
            help="Procédé de personnalisation"),
        'format_doc': fields.selection([
            ('infa4', '<=A4'),
            ('supa4', '>A4'),
            ], u'Format papier à personnaliser',
            help="Format papier à personnaliser"),
        'gram_doc': fields.selection([
            ('inf135', '<135'),
            ('inf176', '<176'),
            ('inf300', '<300'),
            ], u'Grammage papier à personnaliser',
            help="Grammage papier à personnaliser"),
        'perforation_doc': fields.boolean('Perforation',help="Coché pour Oui"),
        'rainage_doc': fields.boolean('Rainage',help="Coché pour Oui"),
        'pliage_doc': fields.boolean('Pliage',help="Coché pour Oui"),
        #ATELIER NUMERIQUE : Fabrication d’un livret
        'quantite_livret': fields.integer(u'Quantité de livrets à fabriquer'),
        'perso_livret': fields.boolean(u'Livrets personnalisés'),
        'pages_livret': fields.integer(u'Nb pages (y/c couverture)',help="Maximum 48"),
        'pose_l_livret': fields.integer('Longueur',help="Longueur<420 / Largeur<300"),
        'pose_w_livret': fields.integer('Largeur'),
        'produit_inter_livret': fields.many2one('product.product','Papier intérieur souhaité'),
        'produit_couve_livret': fields.many2one('product.product','Papier couverture souhaité'),
        'type_livret': fields.selection([
            ('couleur', 'Couleur'),
            ('noire', 'Noire'),
            ('couve', 'Couverture couleur et intérieur noir'),
            ], u'Type impression',
            help="Type impression"),
        #ATELIER ROUTAGE : Insertion manuelle sous enveloppes
        'quantite_man': fields.integer(u'Nombre plis à produire'),
        'produit_man': fields.many2one('product.product','Enveloppes'),
        'fournies_man': fields.boolean('Enveloppes fournies par le client',help="Coché pour Oui"),
        'documents_man': fields.integer(u'Nombre de documents à insérer'),
        'insertion_man': fields.boolean('Insertion avec concordance',help="Coché pour Oui"),
        'pliage_man': fields.integer('Nombre de documents à plier'),
        'fermeture_man': fields.selection([
            ('bande', 'Bande autocollante'),
            ('patte', 'Patte gommée'),
            ], u'Fermeture',
            help="Fermeture"),
        'adressage_man': fields.boolean('Adressage',help="Coché pour Oui"),
        'machine_man': fields.boolean(u'Passage machine à affranchir',help="Coché pour Oui"),
        #ATELIER ROUTAGE : Insertion mécanisée sous enveloppes
        'quantite_mec': fields.integer(u'Nombre plis à produire'),
        'produit_mec': fields.many2one('product.product','Enveloppes porteuses'),
        'fournies_mec': fields.boolean('Enveloppes fournies par ailleurs',help="Coché pour Oui"),
        'documents_mec': fields.integer(u'Nombre de documents à insérer'),
        'pliage_mec': fields.integer('Nombre de documents à plier'),
        'adressage_mec': fields.boolean('Adressage',help="Coché pour Oui"),
        'machine_mec': fields.boolean(u'Passage machine à affranchir',help="Coché pour Oui"),
        #ATELIER ROUTAGE : Mise sous film
        'quantite_fil': fields.integer(u'Nombre de paquets à conditionner'),
        'porte_fil': fields.selection([
            ('non', 'Non'),
            ('noir', 'Noir'),
            ('couleur', 'Couleur'),
            ], u'Fourniture d\'un porte adresse',
            help="Fourniture d\'un porte adresse"),
        'prepa_fil': fields.selection([
            ('simple', 'Simple'),
            ('complexe', 'Complexe'),
            ], u'Type de préparation des données',
            help="Type de préparation des données"),
        'documents_fil': fields.integer(u'Nb docs par paquet (y/c porte adresse)'),
        'livraison_fil': fields.boolean('Livraison palette',help="Coché pour Oui"),
        'palettes_fil': fields.integer('Nombre de paquets par palette'),
        #ATELIER ROUTAGE : Traitement NPAI
        'quantite_npa': fields.integer(u'Nombre de plis traités'),
        'type_npa': fields.selection([
            ('saisie', 'Saisie code'),
            ('scan', 'Scan code'),
            ('recherche', 'Recherche dans une liste'),
            ], u'Type de lecture',
            help="Type de lecture"),
        'ref_npa': fields.char(u'Référence de l\'opération'),    
        #ATELIER ROUTAGE : Affranchissement
        'quantite_plis': fields.integer(u'Nombre de plis'),
        'masse_plis': fields.integer(u'Masse d\'1 pli'),
        'category_plis': fields.many2one('product.category',u'Catégorie'),
        'article_plis': fields.many2one('product.product',u'Article'),
        
        'conf_product_lines': fields.one2many('configurator.product.line','conf_id',u'Détails composants'),
        'conf_workcenter_lines': fields.one2many('configurator.workcenter.line','conf_id',u'Détails tâches'),
        'prix_revient': fields.float('Revient des composants'),
        'prix_theo': fields.float(u'Estimation des tâches sur base horaire'),
        'prix_marche': fields.float(u'Estimation des tâches sur base marché'),
        'prix_global_theo': fields.float(u'Prix à proposer sur base horaire'),
        'prix_global_marche': fields.float(u'Prix à proposer sur base marché'),
        'prix_offert': fields.float(u'Prix proposé'),
    }
    _defaults = {
        'impression_env': '40',
        'impression_pap': '40',
        'impression_jet': 'recto',
        'zone_jet': 'petite',
        'mise_page_doc': 'simple',
        'perso_doc': 'noir',
        'format_doc': 'infa4',
        'gram_doc': 'inf135',
        'perso_imp': 'simple',
        'mise_page_imp': 'simple',
        'impression_imp': '40',
        'pose_l_imp': 297,
        'pose_w_imp': 210,
        'pose_l_livret': 300,
        'pose_w_livret': 210,
        'type_livret': 'couleur',
        'pose_l_liv': 210,
        'pose_w_liv': 150,
        'stockage_col': 'vrac',
        'realisation_col': 'interim',
        'type_enc': 'non_placee',
        'stockage_enc': 'vrac',
        'realisation_enc': 'interim',
        'fermeture_man': 'bande',
        'fournies_mec': True,
        'documents_mec': 1,
        'porte_fil': 'noir',
        'prepa_fil': 'simple',
        'type_npa': 'scan',
        
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(configurator, self).default_get(cr, uid, fields, context=context)
        
        record_id = context and context.get('active_id', False) or False
        if context.get('active_model',False)=='sale.order':
            res.update({'sale_id': record_id})
        if context.get('active_model',False)=='configurator':
            read=self.read(cr,uid,record_id,[],context)
            res.update(read)
            
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        if context.get('active_model',False)=='sale.order':
            order = self.pool.get('sale.order').browse(cr, uid, record_id, context=context)
            if not order.partner_id:
                raise osv.except_osv(_('Attention!'), _('Pas de client.'))
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
    
    def _temps(self, cr, uid, quantite_env, capacity_per_hour, time_cycle, context=None):
        return (capacity_per_hour and (quantite_env/capacity_per_hour) or 0.0) + time_cycle
    
    #ATELIER OFFSET : Impression offset sur enveloppes
    def onchange_enveloppe(self, cr, uid, ids, quantite_env,produit_env,env_fournies,
        impression_env,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            quantite_env=quantite_env+150
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_env_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_env:
                produit_env_browse=product_obj.browse(cr,uid,produit_env)
            if produit_env and produit_env not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_env}])
                produit_env_browse=product_obj.browse(cr,uid,produit_env)
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Env/???]
                    if not env_fournies and product[2]['product_id']==produit_env:
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
                    temps = (work.capacity_per_hour and (quantite_env/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Off/Pla/Offset]
                    if work.name=='Offset : Sortie plaque':
                        workcenter[2]['cout_theo']=(int(impression_env[0])+int(impression_env[1]))*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=(int(impression_env[0])+int(impression_env[1]))*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=(int(impression_env[0])+int(impression_env[1]))
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 1 couleur]
                    if work.name=='Offset : Calage 1:0':
                        if impression_env in ('10','21','41'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_env in ('11'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 2 couleurs]
                    if work.name=='Offset : Calage 2:0':
                        if impression_env in ('20','21','42'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_env in ('22'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 4 couleurs]
                    if work.name=='Offset : Calage 4:0':
                        if impression_env in ('40','41','42'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_env in ('44'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Rou/Offset:Roulage]
                    if work.name=='Offset : Roulage':
                        if produit_env_browse and 'grandes' not in [(x.name).lower() for x in produit_env_browse.tag_ids]:
                            workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_env + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_env + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_env
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Offset : Roulage grand format':
                        if produit_env_browse and 'grandes' in [(x.name).lower() for x in produit_env_browse.tag_ids]:
                            workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_env + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_env + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_env
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
                  
            a=quantite_env
            b=produit_env_browse and produit_env_browse.name or 'N/A'
            c=env_fournies and '\nEnveloppes fournies par vos soins.' or ' - Enveloppes fournies par nos soins.'
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
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER OFFSET : Impression jet d’encre
    def onchange_jet(self, cr, uid, ids, quantite_jet,produit_jet,jet_fournies,
        impression_jet, zone_jet,adressage_jet,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_jet_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_jet:
                produit_jet_browse=product_obj.browse(cr,uid,produit_jet)
            if produit_jet and produit_jet not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_jet}])
                produit_jet_browse=product_obj.browse(cr,uid,produit_jet)
            
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Env/???]
                    if not jet_fournies and product[2]['product_id']==produit_jet:
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
                    temps = (work.capacity_per_hour and (quantite_jet/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Edi/Dat/Data : Préparation données simple]
                    if work.name==u'Editique : Data : Préparation simple':
                        if adressage_jet:
                            workcenter[2]['cout_theo']=quantite_jet*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_jet*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_jet
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Jet/Impression jet d'encre petite image]
                    if work.name=='Offset : Jet d\'encre petite image':
                        if not adressage_jet and zone_jet=='petite':
                            if impression_jet == 'recto':
                                workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_jet + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_jet + work.prix_marche_fixe 
                                workcenter[2]['quantite']=quantite_jet
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            else:
                                workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_jet*2) + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_jet*2) + work.prix_marche_fixe 
                                workcenter[2]['quantite']=quantite_jet*2
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Jet/Impression jet d’encre grande image]
                    if work.name=='Offset : Jet d\'encre grande image':
                        if adressage_jet or zone_jet=='grande':
                            if impression_jet == 'recto':
                                workcenter[2]['cout_theo']=work.prix_theo_variable*quantite_jet + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=work.prix_marche_variable*quantite_jet + work.prix_marche_fixe 
                                workcenter[2]['quantite']=quantite_jet
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            else:
                                workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_jet*2) + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_jet*2) + work.prix_marche_fixe 
                                workcenter[2]['quantite']=quantite_jet*2
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
                  
            a=quantite_jet
            b=produit_jet_browse and produit_jet_browse.name or 'N/A'
            c=jet_fournies and '\nEnveloppes fournies par vos soins.' or '\nEnveloppes fournies par nos soins.'
            if impression_jet=='recto':
                d=' recto seul '
            elif impression_jet=='recto_verso':
                d=' recto-verso '
            else: d='N/A'
            f=adressage_jet and u' et personnalisées' or ' '
            v['name'] = 'Fourniture de ' + str(a) + ' enveloppes ' + b + u' imprimées ' + d + f + c
                
            v['quantite'] = quantite_jet
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER OFFSET : Impression offset sur papier
    def onchange_papier(self, cr, uid, ids, quantite_pap,produit_pap,pose_l_pap,pose_w_pap,
        impression_pap,perforation_pap,rainage_pap,pliage_pap,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_pap_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_pap:
                produit_pap_browse=product_obj.browse(cr,uid,produit_pap)
            if produit_pap and produit_pap not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_pap}])
                produit_pap_browse=product_obj.browse(cr,uid,produit_pap)
            if pose_l_pap>450:
                raise osv.except_osv(_('Attention!'),_("La longueur ne peut être supérieure à 450"))
            if pose_w_pap>320:
                raise osv.except_osv(_('Attention!'),_("La largeur ne peut être supérieure à 320"))
            if (pose_l_pap==450 and pose_w_pap==320) or (pose_l_pap==0 and pose_w_pap==0):
                pose_pap=0
            else:
                pose_pap=max(math.floor(450/(pose_l_pap+10)*320/(pose_w_pap+10)),math.floor(450/(pose_w_pap+10)*320/(pose_l_pap+10)))
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Pap/???]
                    if product[2]['product_id']==produit_pap:
                        product[2]['cout']=(quantite_pap/(pose_pap or 1))*prod.list_price
                        product[2]['quantite']=(quantite_pap/(pose_pap or 1))
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
                    temps = (work.capacity_per_hour and (quantite_pap/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Off/Pla/Offset]
                    if work.name=='Offset : Sortie plaque':
                        workcenter[2]['cout_theo']=(int(impression_pap[0])+int(impression_pap[1]))*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=(int(impression_pap[0])+int(impression_pap[1]))*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=(int(impression_pap[0])+int(impression_pap[1]))
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 1 couleur]
                    if work.name=='Offset : Calage 1:0':
                        if impression_pap in ('10','21','41'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_pap in ('11'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 2 couleurs]
                    if work.name=='Offset : Calage 2:0':
                        if impression_pap in ('20','21','42'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_pap in ('22'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Cal/Offset:Calage 4 couleurs]
                    if work.name=='Offset : Calage 4:0':
                        if impression_pap in ('40','41','42'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        elif impression_pap in ('44'):
                            workcenter[2]['cout_theo']=work.prix_theo_variable*2 + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*2 + work.prix_marche_fixe 
                            workcenter[2]['quantite']=2
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Off/Rou/Offset:Roulage]
                    if work.name=='Offset : Roulage grand format':
                        workcenter[2]['cout_theo']=work.prix_theo_variable*(quantite_pap/(pose_pap or 1)) + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*(quantite_pap/(pose_pap or 1)) + work.prix_marche_fixe 
                        workcenter[2]['quantite']=(quantite_pap/(pose_pap or 1))
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Coupe]
                    if work.name==u'Numérique : Coupe':
                        if pose_pap>0:
                            x=(quantite_pap/pose_pap/500)
                            if x<1:
                                x=1
                            q=math.ceil((4*pose_pap - 2)*x)
                            workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=q
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Perforation], [Rainage]
                    if work.name==u'Numérique : Perforation':
                        if perforation_pap:
                            workcenter[2]['cout_theo']=quantite_pap*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_pap*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_pap
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Rainage':
                        if rainage_pap:
                            workcenter[2]['cout_theo']=quantite_pap*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_pap*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_pap
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Pliage]
                    if work.name=='Routage : Pliage SRA3 lourd':
                        if pliage_pap and pose_pap<2:
                            workcenter[2]['cout_theo']=quantite_pap*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_pap*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_pap
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage A4 lourd':
                        if pliage_pap and pose_pap>=2:
                            workcenter[2]['cout_theo']=quantite_pap*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_pap*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_pap
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
                  
            a=quantite_pap
            b=produit_pap_browse and produit_pap_browse.name or 'N/A'
            c=str(pose_l_pap)+'x'+str(pose_w_pap)+'mm'
            if impression_pap:
               d=impression_pap[0] + ' couleur(s) recto et ' + impression_pap[1] + ' couleur(s) verso'
            else: d='N/A'
            e=(perforation_pap and ' Perforation' or '') + (rainage_pap and ' Rainage' or '') + (pliage_pap and ' Pliage' or '')

            v['name'] = 'Fourniture de ' + str(a) + ' documents format ouvert ' + str(c) + u' imprimés sur papier ' + b +\
             '\nImpression ' + d + (e and ('\nFinition:' + e) or '')
                
            v['quantite'] = quantite_pap
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER EDITIQUE : Campagne email
    def onchange_email(self, cr, uid, ids, quantite_email,heures_email,notes_email,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            for product in conf_product_lines:
                if product[2]:
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Ema/Envoi]
                    if prod.name=='Routage emails':
                        product[2]['cout']=quantite_email*prod.list_price
                        product[2]['quantite']=quantite_email
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_email/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Edi/Ema/Email : Mise en page]
                    if work.name=='Editique : Email : Mise en page':
                        if heures_email==0:
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Edi/Ema/Email : Tests de campagne]
                    if work.name=='Editique : Email : Test de campagne':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Service : MO Editique]
                    if work.name=='Editique : MO':
                        workcenter[2]['cout_theo']=work.prix_theo_variable*heures_email + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=work.prix_marche_variable*heures_email + work.prix_marche_fixe 
                        workcenter[2]['quantite']=heures_email
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
                  
            a=quantite_email
            b=heures_email
            if b>0:
                c=u'\n' + (notes_email and notes_email or ' ')
            else:
                c=''
            v['name'] = u'Campagne email envoyée à ' +\
            str(a) +\
            u' destinataires.\nPréparation de la mise en page et tests de déliverabilité et de rendu inclus.' + c
                
            v['quantite'] = quantite_email
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
        
    #ATELIER EDITIQUE : Préparation données
    def onchange_prepa(self, cr, uid, ids, type_prepa,heures_prepa,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0

            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (1/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Edi/Dat/Data : Préparation données simples]
                    if work.name==u'Editique : Data : Préparation simple':
                        if type_prepa == 'simple':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Edi/Dat/Data : Préparation données complexes]
                    if work.name==u'Editique : Data : Préparation complexe':
                        if type_prepa == 'complexe':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Service : MO Editique]
                    if work.name=='Editique : MO':
                        if type_prepa == 'specifique':
                            workcenter[2]['cout_theo']=work.prix_theo_variable*heures_prepa + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=work.prix_marche_variable*heures_prepa + work.prix_marche_fixe 
                            workcenter[2]['quantite']=heures_prepa
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
                  
            v['name'] = u'Forfait pour préparation des données'
                
            v['quantite'] = 1.0
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER FACONNAGE : Collage de documents
    def onchange_collage(self, cr, uid, ids, quantite_col,bandes_col,pliures_col,stockage_col,cartons_col,realisation_col,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=prix_marche_tache=0.0
            total_temps=0.0
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (1/work.capacity_per_hour) or 0.0) + work.time_cycle
                    
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    
                    #[Fac/Enc/Encollage manuel avec pinceau 1 bande]
                    if work.name==u'Faconnage : Encollage manuel 1 bande':
                        workcenter[2]['cout_theo']=(quantite_col*bandes_col)*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=(quantite_col*bandes_col)*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=(quantite_col*bandes_col)
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Fac/Pli/Pliure]
                    if work.name==u'Faconnage : Pliure':
                        workcenter[2]['cout_theo']=(quantite_col*pliures_col)*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=(quantite_col*pliures_col)*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=(quantite_col*pliures_col)
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche_tache+=workcenter[2]['cout_marche']
                    if realisation_col=='interim':
                        workcenter[2]['cout_theo']=0.0
                        workcenter[2]['cout_marche']=0.0
                    total_temps+=workcenter[2]['temps']
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            for product in conf_product_lines:
                if product[2]:
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Div/Carton 92]
                    if prod.name=='Carton 92':
                        if stockage_col=='carton':
                            product[2]['cout']=(quantite_col/(cartons_col or 1))*prod.list_price
                            product[2]['quantite']=quantite_col/(cartons_col or 1)
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    #[MO/Intérimaires]
                    if prod.name==u'Intérimaires':
                        if realisation_col=='interim':
                            product[2]['cout']=prix_marche_tache
                            product[2]['quantite']=total_temps
                        elif realisation_col=='interne':
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
                    
            a=quantite_col
            b=bandes_col
            if pliures_col:
                c='\nPliage de ' + str(pliures_col) + ' rabats.'
            else: c=''
            if stockage_col=='carton':
                e='\nLivraison en ' + str(quantite_col/(cartons_col or 1)) + ' cartons de ' + str(cartons_col) + u' pièces.'
            else: e=''
            v['name'] = u'Application de ' + str(b) + ' bande(s) de collage sur ' + str(a) +\
            u' imprimés fournis par ailleurs.' + c + e
                
            v['quantite'] = quantite_col
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER FACONNAGE : Travaux divers
    def onchange_divers(self, cr, uid, ids, note_div, heures_div, produit1_div, quantite1_div, produit2_div, quantite2_div,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit1_div_browse=False
            produit2_div_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit1_div:
                produit1_div_browse=product_obj.browse(cr,uid,produit1_div)
            if produit1_div and produit1_div not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit1_div}])
                produit1_div_browse=product_obj.browse(cr,uid,produit1_div)
            if produit2_div:
                produit2_div_browse=product_obj.browse(cr,uid,produit2_div)
            if produit2_div and produit2_div not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit2_div}])
                produit2_div_browse=product_obj.browse(cr,uid,produit2_div)
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Fourniture 1]
                    if product[2]['product_id']==produit1_div:
                        product[2]['cout']=quantite1_div*prod.list_price
                        product[2]['quantite']=quantite1_div
                    #[Fourniture 2]
                    if product[2]['product_id']==produit2_div:
                        product[2]['cout']=quantite2_div*prod.list_price
                        product[2]['quantite']=quantite2_div
                    #[MO/Intérimaires]
                    if prod.name==u'Intérimaires':
                        if heures_div:
                            product[2]['cout']=heures_div*prod.list_price
                            product[2]['quantite']=heures_div
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
                  
            #~ v['name'] = u''
                
            v['quantite'] = 0.0
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER FACONNAGE : Encartage
    def onchange_encartage(self, cr, uid, ids, quantite_enc,depose_enc,type_enc,stockage_enc,cartons_enc,realisation_enc,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=prix_marche_tache=0.0
            total_temps=0.0
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (1/work.capacity_per_hour) or 0.0) + work.time_cycle
                    
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    
                    #[Fac/Enc/Encartage avec collage pastille]
                    if work.name==u'Faconnage : Encartage avec point de colle':
                        if depose_enc:
                            if type_enc=='placee':
                                workcenter[2]['cout_theo']=quantite_enc*(work.prix_theo_variable*1.3) + work.prix_theo_fixe*1.3
                                workcenter[2]['cout_marche']=quantite_enc*(work.prix_marche_variable*1.3) + work.prix_marche_fixe*1.3
                                workcenter[2]['quantite']=quantite_enc
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            else:
                                workcenter[2]['cout_theo']=quantite_enc*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_enc*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_enc
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Fac/Enc/Encartage sans collage]
                    if work.name==u'Faconnage : Encartage sans collage':
                        if not depose_enc:
                            if type_enc=='placee':
                                workcenter[2]['cout_theo']=quantite_enc*(work.prix_theo_variable*1.3) + work.prix_theo_fixe*1.3
                                workcenter[2]['cout_marche']=quantite_enc*(work.prix_marche_variable*1.3) + work.prix_marche_fixe*1.3
                                workcenter[2]['quantite']=quantite_enc
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            else:
                                workcenter[2]['cout_theo']=quantite_enc*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_enc*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_enc
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche_tache+=workcenter[2]['cout_marche']
                    if realisation_enc=='interim':
                        workcenter[2]['cout_theo']=0.0
                        workcenter[2]['cout_marche']=0.0
                    total_temps+=workcenter[2]['temps']
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            for product in conf_product_lines:
                if product[2]:
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Div/Carton 92]
                    if prod.name=='Carton 92':
                        if stockage_enc=='carton':
                            product[2]['cout']=(quantite_enc/(cartons_enc or 1))*prod.list_price
                            product[2]['quantite']=quantite_enc/(cartons_enc or 1)
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    #[Div/Pastilles adhésives]
                    if prod.name==u'Pastilles adhésives':
                        if depose_enc:
                            product[2]['cout']=quantite_enc*prod.list_price
                            product[2]['quantite']=quantite_enc
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    #[MO/Intérimaires]
                    if prod.name==u'Intérimaires':
                        if realisation_enc=='interim':
                            product[2]['cout']=prix_marche_tache
                            product[2]['quantite']=total_temps
                        elif realisation_enc=='interne':
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
                    
            a=quantite_enc
            b=(type_enc=='placee' and u'placé' or '') + (type_enc=='non_placee' and u'non placée' or '') +\
             (depose_enc and ' avec fixation par pastille de colle fugitive.' or '')
            if stockage_enc=='carton':
                e='\nLivraison en ' + str(quantite_enc/(cartons_enc or 1)) + ' cartons de ' + str(cartons_enc) + u' pièces.'
            else: e=''
            v['name'] = u'Encartage d\'un document dans une brochure. Eléments fournis par ailleurs.' +\
            u'\nQuantité : ' + str(a) + 'ex.' + (b and ('\nEncartage ' + b) or '') + e
            
            v['quantite'] = quantite_enc
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER NUMERIQUE : Fabrication d’un imprimé
    def onchange_imprime(self, cr, uid, ids, quantite_imp, perso_imp, mise_page_imp, impression_imp, pose_l_imp, pose_w_imp, produit_imp, 
        perforation_imp, rainage_imp, pliage_imp,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_imp_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_imp:
                produit_imp_browse=product_obj.browse(cr,uid,produit_imp)
            if produit_imp and produit_imp not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_imp}])
                produit_imp_browse=product_obj.browse(cr,uid,produit_imp)
            if pose_l_imp>450:
                raise osv.except_osv(_('Attention!'),_("La longueur ne peut être supérieure à 450"))
            if pose_w_imp>320:
                raise osv.except_osv(_('Attention!'),_("La largeur ne peut être supérieure à 320"))
            if (pose_l_imp==450 and pose_w_imp==320) or (pose_l_imp==0 and pose_w_imp==0):
                pose_imp=0
            else:
                pose_imp=max(math.floor(450/(pose_l_imp+10)*320/(pose_w_imp+10)),math.floor(450/(pose_w_imp+10)*320/(pose_l_imp+10)))
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Pap/???]
                    if product[2]['product_id']==produit_imp:
                        product[2]['cout']=(quantite_imp/(pose_imp or 1))*prod.list_price
                        product[2]['quantite']=(quantite_imp/(pose_imp or 1))
                    if impression_imp:
                        #[Sor/Noir]
                        if prod.name==u'Sortie numérique noir' and impression_imp in ('10','41'):
                            product[2]['cout']=(quantite_imp/(pose_imp or 1))*prod.list_price
                            product[2]['quantite']=(quantite_imp/(pose_imp or 1))
                        elif prod.name==u'Sortie numérique noir' and impression_imp in ('11'):
                            product[2]['cout']=2*(quantite_imp/(pose_imp or 1))*prod.list_price
                            product[2]['quantite']=2*(quantite_imp/(pose_imp or 1))
                        elif prod.name==u'Sortie numérique noir':
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                        #[Sor/Couleur]
                        if prod.name==u'Sortie numérique couleur' and impression_imp in ('40','41'):
                            product[2]['cout']=(quantite_imp/(pose_imp or 1))*prod.list_price
                            product[2]['quantite']=(quantite_imp/(pose_imp or 1))
                        elif prod.name==u'Sortie numérique couleur' and impression_imp in ('44'):
                            product[2]['cout']=2*(quantite_imp/(pose_imp or 1))*prod.list_price
                            product[2]['quantite']=2*(quantite_imp/(pose_imp or 1))
                        elif prod.name==u'Sortie numérique couleur':
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2] and impression_imp:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_imp/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0   
                    #[Edi/Prepa données]
                    if work.name==u'Editique : Data : Préparation simple':
                        if perso_imp!='sans' and mise_page_imp=='simple':
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Editique : Data : Préparation complexe':
                        if perso_imp!='sans' and mise_page_imp=='complexe':
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Fusion]
                    if work.name==u'Numérique : Fusion simple':
                        if perso_imp=='simple':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Fusion paramétrée':
                        if perso_imp=='complexe':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Sorties numériques]
                    if work.name==u'Numérique : Sorties n:0 SRA3 <135g':
                        if produit_imp_browse and 'inf.135' in [x.name for x in produit_imp_browse.tag_ids] :
                            if impression_imp in ('10','40'):
                                workcenter[2]['cout_theo']=(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            if impression_imp in ('11','41','44'):
                                workcenter[2]['cout_theo']=2*(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=2*(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=2*(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <176g':
                        if produit_imp_browse and 'inf.176' in [x.name for x in produit_imp_browse.tag_ids]:
                            if impression_imp in ('10','40'):
                                workcenter[2]['cout_theo']=(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            if impression_imp in ('11','41','44'):
                                workcenter[2]['cout_theo']=2*(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=2*(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=2*(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <300g':
                        if produit_imp_browse and 'inf.300' in [x.name for x in produit_imp_browse.tag_ids]:
                            if impression_imp in ('10','40'):
                                workcenter[2]['cout_theo']=(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                            if impression_imp in ('11','41','44'):
                                workcenter[2]['cout_theo']=2*(quantite_imp/(pose_imp or 1))*work.prix_theo_variable + work.prix_theo_fixe 
                                workcenter[2]['cout_marche']=2*(quantite_imp/(pose_imp or 1))*work.prix_marche_variable + work.prix_marche_fixe 
                                workcenter[2]['quantite']=2*(quantite_imp/(pose_imp or 1))
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Coupe]
                    if work.name==u'Numérique : Coupe':
                        if pose_imp>0:
                            x=(quantite_imp/pose_imp/500)
                            if x<1:
                                x=1
                            q=math.ceil((4*pose_imp - 2)*x)
                            workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=q
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        else:
                            workcenter[2]['cout_theo']=0.0
                            workcenter[2]['cout_marche']=0.0
                            workcenter[2]['quantite']=0.0
                            workcenter[2]['temps']=0.0  
                    #[Faconnage], [Rainage]
                    if work.name==u'Numérique : Perforation':
                        if perforation_imp:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Rainage':
                        if rainage_imp:
                            workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_imp
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Pliage]
                    if work.name=='Routage : Pliage SRA3' and (produit_imp_browse and 'lourd' not in [(x.name).lower() for x in produit_imp_browse.tag_ids]):
                        if pliage_imp:
                            if pose_imp==0 or pose_imp==1:
                                workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_imp
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage SRA3 lourd' and (produit_imp_browse and 'lourd' in [(x.name).lower() for x in produit_imp_browse.tag_ids]):
                        if pliage_imp:
                            if pose_imp==0 or pose_imp==1:
                                workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_imp
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage A4' and (produit_imp_browse and 'lourd' not in [(x.name).lower() for x in produit_imp_browse.tag_ids]):
                        if pliage_imp:
                            if pose_imp>1:
                                workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_imp
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage A4 lourd' and (produit_imp_browse and 'lourd' in [(x.name).lower() for x in produit_imp_browse.tag_ids]):
                        if pliage_imp:
                            if pose_imp>1:
                                workcenter[2]['cout_theo']=quantite_imp*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_imp*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_imp
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_imp
            if perso_imp=='sans':
                b=''
            else:
                b=u'personnalisé'
            c=str(pose_l_imp)+'x'+str(pose_w_imp)
            if impression_imp:
                if impression_imp=='10':
                    d='noire recto'
                if impression_imp=='11':
                    d='noire recto-verso'
                if impression_imp=='40':
                    d='couleur recto'
                if impression_imp=='41':
                    d='couleur recto et noire verso'
                if impression_imp=='44':
                    d='couleur recto-verso'
            else: d='N/A'
            e=(perforation_imp and ' Perforation' or '') + (rainage_imp and ' Rainage' or '') + (pliage_imp and ' Pliage' or '')
            f=produit_imp_browse and produit_imp_browse.name or 'N/A'

            v['name'] = 'Fourniture d\'un document ' + b + ' format ouvert ' + str(c) +\
             '\nImpression ' + d + ' sur papier ' + f + (e and ('\nFinition:' + e) or '')
                    
            v['quantite'] = quantite_imp
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}

    #ATELIER NUMERIQUE : Fabrication de livres reliés en dos carré
    def onchange_livre(self, cr, uid, ids, quantite_liv, heures_liv, pose_l_liv, pose_w_liv,
        pages_noir_liv, produit_noir_liv, pages_couleur_liv, produit_couleur_liv,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_noir_liv_browse=False
            produit_couleur_liv_browse=False
            
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_noir_liv:
                produit_noir_liv_browse=product_obj.browse(cr,uid,produit_noir_liv)
            if produit_noir_liv and produit_noir_liv not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_noir_liv}])
                produit_noir_liv_browse=product_obj.browse(cr,uid,produit_noir_liv)
            if produit_couleur_liv:
                produit_couleur_liv_browse=product_obj.browse(cr,uid,produit_couleur_liv)
            if produit_couleur_liv and produit_couleur_liv not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_couleur_liv}])
                produit_couleur_liv_browse=product_obj.browse(cr,uid,produit_couleur_liv)
            if pose_l_liv>310:
                raise osv.except_osv(_('Attention!'),_("La longueur ne peut être supérieure à 310"))
            if pose_w_liv>220:
                raise osv.except_osv(_('Attention!'),_("La largeur ne peut être supérieure à 220"))
            if (pose_l_liv==450 and pose_w_liv==320) or (pose_l_liv==0 and pose_w_liv==0):
                pose_liv=0
            else:
                pose_liv=max(math.floor(450/(pose_l_liv+10)*320/(pose_w_liv+10)),math.floor(450/(pose_w_liv+10)*320/(pose_l_liv+10)))
            for product in conf_product_lines:
                if product[2]:
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Pap/???]noir
                    if product[2]['product_id']==produit_noir_liv:
                        product[2]['cout']+=(((pages_noir_liv/(pose_liv or 1))/2)*quantite_liv)*prod.list_price
                        product[2]['quantite']+=((pages_noir_liv/(pose_liv or 1))/2)*quantite_liv
                    #[Pap/???]couleur
                    if product[2]['product_id']==produit_couleur_liv:
                        product[2]['cout']+=(((pages_couleur_liv/(pose_liv or 1))/2)*quantite_liv)*prod.list_price
                        product[2]['quantite']+=((pages_couleur_liv/(pose_liv or 1))/2)*quantite_liv
                    #[Pap/CB300]
                    if prod.name==u'300 gsm couché brillant':
                        q=0.0
                        if pose_liv:
                            q=quantite_liv/(pose_liv/2)
                        else:
                            q=quantite_liv/0.5
                        product[2]['cout']=q*prod.list_price
                        product[2]['quantite']=q
                    #[Sor/Noir]
                    if prod.name==u'Sortie numérique noir':
                        product[2]['cout']=((pages_noir_liv/(pose_liv or 1))*quantite_liv)*prod.list_price
                        product[2]['quantite']=(pages_noir_liv/(pose_liv or 1))*quantite_liv
                    #[Sor/Couleur]
                    if prod.name==u'Sortie numérique couleur':
                        q=0.0
                        q_couve=0.0
                        q=quantite_liv*(pages_couleur_liv/(pose_liv or 1))
                        q_couve=quantite_liv*(1/(((pose_liv)/2) or 1))
                        product[2]['cout']=q*prod.list_price
                        product[2]['quantite']=q
                        product[2]['cout']+=q_couve*prod.list_price
                        product[2]['quantite']+=q_couve
                    #[Sor/Couleur]couverture
                    #~ if prod.name==u'Sortie numérique couleur couverture':
                        #~ q=0.0
                        #~ if pose_liv:
                            #~ q=quantite_liv/(pose_liv/2)
                        #~ else:
                            #~ q=quantite_liv/0.5
                        #~ product[2]['cout']=q*prod.list_price
                        #~ product[2]['quantite']=q
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_liv/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0   
                    #[MO Atelier]
                    if work.name==u'Numérique : MO':
                        workcenter[2]['cout_theo']=work.prix_theo_variable*heures_liv + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=work.prix_marche_variable*heures_liv + work.prix_marche_fixe
                        workcenter[2]['quantite']=heures_liv
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Sorties numériques]
                    if work.name==u'Numérique : Sorties n:0 SRA3 <135g':
                        q=0.0
                        if produit_noir_liv_browse and 'inf.135' in [x.name for x in produit_noir_liv_browse.tag_ids] :
                            q+=(pages_noir_liv/(pose_liv or 1))
                        if produit_couleur_liv_browse and 'inf.135' in [x.name for x in produit_couleur_liv_browse.tag_ids] :
                            q+=(pages_couleur_liv/(pose_liv or 1))
                        workcenter[2]['cout_theo']=(q*quantite_liv)*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=(q*quantite_liv)*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=q*quantite_liv
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <176g':
                        q=0.0
                        if produit_noir_liv_browse and 'inf.176' in [x.name for x in produit_noir_liv_browse.tag_ids] :
                            q+=(pages_noir_liv/(pose_liv or 1))
                        if produit_couleur_liv_browse and 'inf.176' in [x.name for x in produit_couleur_liv_browse.tag_ids] :
                            q+=(pages_couleur_liv/(pose_liv or 1))
                        workcenter[2]['cout_theo']=(q*quantite_liv)*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=(q*quantite_liv)*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=q*quantite_liv
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <300g':
                        q=0.0
                        if pose_liv:
                            q=quantite_liv/(pose_liv/2)
                        else:
                            q=quantite_liv/0.5
                        workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=q
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Coupe]
                    if work.name==u'Numérique : Coupe':
                        if pose_liv>0:
                            x=((quantite_liv*(pages_noir_liv+pages_couleur_liv))/pose_liv/2/500)
                            if x<1:
                                x=1
                            q=(4*pose_liv - 2)*math.ceil(x)
                            workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=q
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        else:
                            workcenter[2]['cout_theo']=0.0
                            workcenter[2]['cout_marche']=0.0
                            workcenter[2]['quantite']=0.0
                            workcenter[2]['temps']=0.0  
                    #[Dos carré collé]
                    if work.name==u'Numérique : Reliure dos carré collé':
                        workcenter[2]['cout_theo']=quantite_liv*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=quantite_liv*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=quantite_liv
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_liv
            b=pages_noir_liv+pages_couleur_liv
            c=str(pose_l_liv)+'x'+str(pose_w_liv)
            e=produit_noir_liv_browse and produit_noir_liv_browse.name or 'N/A'
            f=produit_couleur_liv_browse and produit_couleur_liv_browse.name or 'N/A'
            print str(pages_noir_liv),str(pages_couleur_liv)
            v['name'] = 'Fabrication de ' + str(a) + ' livres de ' + str(b) + u' pages reliés en dos carré collé.\nFormat fermé ' + str(c) +\
             '.\n' + str(pages_noir_liv) + u' pages intérieures imprimées noir sur papier ' + e +\
             '.\n' + str(pages_couleur_liv) + u' pages intérieures imprimées couleur sur papier ' + f +\
             u'.\nCouverture sur papier CB300gsm imprimée couleur'
                    
            v['quantite'] = quantite_liv
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}

    #ATELIER NUMERIQUE : Personnalisation d’un document
    def onchange_doc(self, cr, uid, ids, quantite_doc, mise_page_doc, prepa_doc, perso_doc,
        format_doc, gram_doc, perforation_doc, rainage_doc, pliage_doc,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Sor/Noir]
                    if prod.name==u'Sortie numérique noir':
                        if perso_doc=='noir':
                            product[2]['cout']=quantite_doc*prod.list_price
                            product[2]['quantite']=quantite_doc
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    #[Sor/Couleur]
                    if prod.name==u'Sortie numérique couleur':
                        if perso_doc=='couleur':
                            product[2]['cout']=quantite_doc*prod.list_price
                            product[2]['quantite']=quantite_doc
                        else:
                            product[2]['cout']=0.0
                            product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_doc/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0   
                    #[Data]
                    if work.name==u'Editique : Data : Préparation simple':
                        if prepa_doc=='simple':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Editique : Data : Préparation complexe':
                        if prepa_doc=='complexe':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Fusion]
                    if work.name==u'Numérique : Fusion simple':
                        if mise_page_doc=='simple' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Fusion paramétrée':
                        if mise_page_doc=='complexe' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Sorties numériques]
                    if work.name==u'Numérique : Sorties n:0 A4 <135g':
                        if format_doc=='infa4' and gram_doc=='inf135' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 A4 <176g':
                        if format_doc=='infa4' and gram_doc=='inf176' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 A4 <300g':
                        if format_doc=='infa4' and gram_doc=='inf300' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <135g':
                        if format_doc=='supa4' and gram_doc=='inf135' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <176g':
                        if format_doc=='supa4' and gram_doc=='inf176' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <300g':
                        if format_doc=='supa4' and gram_doc=='inf300' and perso_doc!='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Adressage]
                    if work.name==u'Routage : Adressage hors ligne':
                        if perso_doc=='encre':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Faconnage], [Rainage]
                    if work.name==u'Numérique : Perforation':
                        if perforation_doc:
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Rainage':
                        if rainage_doc:
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Pliage]
                    if work.name=='Routage : Pliage SRA3':
                        if pliage_doc and format_doc=='supa4' and gram_doc=='inf135':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage SRA3 lourd':
                        if pliage_doc and format_doc=='supa4' and (gram_doc=='inf176' or gram_doc=='inf300'):
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage A4':
                        if pliage_doc and format_doc=='infa4' and gram_doc=='inf135':
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Pliage A4 lourd':
                        if pliage_doc and format_doc=='infa4' and (gram_doc=='inf176' or gram_doc=='inf300'):
                            workcenter[2]['cout_theo']=quantite_doc*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_doc*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_doc
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_doc
            if format_doc=='infa4':
                e='<=A4'
            elif format_doc=='supa4':
                e='>A4'
            else:
                e='N/A'
            if gram_doc=='inf135':
                f='<135 gsm'
            elif gram_doc=='inf176':
                f='<176 gsm'
            elif gram_doc=='inf300':
                f='<300 gsm'
            else:
                f='N/A'
            b= (perforation_doc and ' Perforation' or '') + (rainage_doc and ' Rainage' or '') + (pliage_doc and ' Pliage' or '')
            if perso_doc=='couleur':
                c='couleur'
            else:
                c=''
            v['name'] = u'Personnalisation ' + c + ' de ' +\
            str(a) +\
            u' imprimés format ' + e + u' sur papier ' + f + (b and ('.\nFinition:' + b) or '') +\
            u'\nDocuments à personnaliser fournis par vos soins'
                    
            v['quantite'] = quantite_doc
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER NUMERIQUE : Fabrication d'un livret
    def onchange_livret(self, cr, uid, ids, quantite_livret, perso_livret, pages_livret, pose_l_livret, pose_w_livret,
        produit_inter_livret, produit_couve_livret, type_livret,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_inter_livret_browse=False
            produit_couve_livret_browse=False
            
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_inter_livret:
                produit_inter_livret_browse=product_obj.browse(cr,uid,produit_inter_livret)
            if produit_inter_livret and produit_inter_livret not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_inter_livret}])
                produit_inter_livret_browse=product_obj.browse(cr,uid,produit_inter_livret)
            if produit_couve_livret:
                produit_couve_livret_browse=product_obj.browse(cr,uid,produit_couve_livret)
            if produit_couve_livret and produit_couve_livret not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_couve_livret}])
                produit_couve_livret_browse=product_obj.browse(cr,uid,produit_couve_livret)
            if pages_livret>48:
                raise osv.except_osv(_('Attention!'),_("Le nombre de pages ne peut être supérieur à 48"))
            if pages_livret%4!=0:
                raise osv.except_osv(_('Attention!'),_("Le nombre de pages doit être un multiple de 4"))
            if pose_l_livret>420:
                raise osv.except_osv(_('Attention!'),_("La longueur ne peut être supérieure à 420"))
            if pose_l_livret<250 and pose_l_livret!=0:
                raise osv.except_osv(_('Attention!'),_("La longueur ne peut être inférieure à 250"))
            if pose_w_livret>300:
                raise osv.except_osv(_('Attention!'),_("La largeur ne peut être supérieure à 300"))
            if pose_w_livret<210 and pose_w_livret!=0:
                raise osv.except_osv(_('Attention!'),_("La largeur ne peut être inférieure à 210"))
            if (pose_l_livret==420 and pose_w_livret==300) or (pose_l_livret==0 and pose_w_livret==0):
                pose_livret=0
            else:
                pose_livret=max(math.floor(450/(pose_l_livret+10)*320/(pose_w_livret+10)),math.floor(450/(pose_w_livret+10)*320/(pose_l_livret+10)))
            for product in conf_product_lines:
                if product[2]:
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Pap/???]intérieur
                    if product[2]['product_id']==produit_inter_livret:
                        q=quantite_livret*((pages_livret-4)/4)/(pose_livret or 1)
                        product[2]['cout']+=q*prod.list_price
                        product[2]['quantite']+=q
                    #[Pap/???]couverture
                    if product[2]['product_id']==produit_couve_livret:
                        q=quantite_livret/(pose_livret or 1)
                        product[2]['cout']+=q*prod.list_price
                        product[2]['quantite']+=q
                    #[Sor/Noir]
                    if prod.name==u'Sortie numérique noir':
                        q=0.0
                        if type_livret=='noire':
                            q=quantite_livret*(pages_livret/2)/(pose_livret or 1)
                        elif type_livret=='couve':
                            q=quantite_livret*((pages_livret-4)/2)/(pose_livret or 1)
                        product[2]['cout']=q*prod.list_price
                        product[2]['quantite']=q
                    #[Sor/Couleur]
                    if prod.name==u'Sortie numérique couleur':
                        q=0.0
                        if type_livret=='couleur':
                            q=quantite_livret*(pages_livret/2)/(pose_livret or 1)
                        elif type_livret=='couve':
                            q=quantite_livret*2/(pose_livret or 1)
                        product[2]['cout']=q*prod.list_price
                        product[2]['quantite']=q
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_livret/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0   
                    #[Editique : Data : Préparation simple]
                    if work.name==u'Editique : Data : Préparation simple':
                        if perso_livret:
                            workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=1
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Fusion]
                    if work.name==u'Numérique : Fusion paramétrée':
                        workcenter[2]['cout_theo']=work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=1
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Sorties numériques]
                    if work.name==u'Numérique : Sorties n:0 SRA3 <135g':
                        q=0.0
                        if produit_inter_livret_browse and 'inf.135' in [x.name for x in produit_inter_livret_browse.tag_ids] :
                            q+=quantite_livret*((pages_livret-4)/2)/(pose_livret or 1)
                        if produit_couve_livret_browse and 'inf.135' in [x.name for x in produit_couve_livret_browse.tag_ids] :
                            q+=quantite_livret*2/(pose_livret or 1)
                        workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=q
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name==u'Numérique : Sorties n:0 SRA3 <176g':
                        q=0.0
                        if produit_inter_livret_browse and 'inf.176' in [x.name for x in produit_inter_livret_browse.tag_ids] :
                            q+=quantite_livret*((pages_livret-4)/2)/(pose_livret or 1)
                        if produit_couve_livret_browse and 'inf.176' in [x.name for x in produit_couve_livret_browse.tag_ids] :
                            q+=quantite_livret*2/(pose_livret or 1)
                        workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=q
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Coupe]
                    if work.name==u'Numérique : Coupe':
                        if pose_livret>0:
                            x=(quantite_livret*(pages_livret/4)/pose_livret/500)
                            if x<1:
                                x=1
                            q=(4*pose_livret - 2)*math.ceil(x)
                            workcenter[2]['cout_theo']=q*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=q*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=q
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        else:
                            workcenter[2]['cout_theo']=0.0
                            workcenter[2]['cout_marche']=0.0
                            workcenter[2]['quantite']=0.0
                            workcenter[2]['temps']=0.0  
                    #[Piquage]
                    if work.name==u'Numérique : Piquage':
                        workcenter[2]['cout_theo']=quantite_livret*work.prix_theo_variable + work.prix_theo_fixe
                        workcenter[2]['cout_marche']=quantite_livret*work.prix_marche_variable + work.prix_marche_fixe
                        workcenter[2]['quantite']=quantite_livret
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_livret
            b=perso_livret and u' et personnalisés' or ''
            c=pages_livret
            e=produit_inter_livret_browse and produit_inter_livret_browse.name or 'N/A'
            f=produit_couve_livret_browse and produit_couve_livret_browse.name or 'N/A'
            g_inter=type_livret in ('noire','couve') and 'noir' or type_livret=='couleur' and 'couleur' or ''
            g_couve=type_livret in ('couleur','couve') and 'couleur' or type_livret=='noire' and 'noir' or ''

            v['name'] = 'Fourniture de ' + str(a) + u' livrets piqués' + b + ' de ' + str(c) + ' pages.' +\
             u'\nPages intérieures imprimées en ' + g_inter + ' sur papier ' + e +\
             u'\nCouverture imprimée en ' + g_couve + ' sur papier ' + f
                    
            v['quantite'] = quantite_livret
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER ROUTAGE : Insertion manuelle sous enveloppes
    def onchange_manuelle(self, cr, uid, ids, quantite_man,produit_man,fournies_man,documents_man,insertion_man,
        pliage_man,fermeture_man,adressage_man,machine_man,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_man_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_man:
                produit_man_browse=product_obj.browse(cr,uid,produit_man)
            if produit_man and produit_man not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_man}])
                produit_man_browse=product_obj.browse(cr,uid,produit_man)
            if pliage_man>documents_man:
                raise osv.except_osv(_('Attention!'),_("Le nombre de documents à plier ne peut être supérieur au nombre de documents à insérer"))
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Env/???]
                    if not fournies_man and product[2]['product_id']==produit_man:
                        product[2]['cout']=quantite_man*prod.list_price
                        product[2]['quantite']=quantite_man
                    elif product[2]['product_id']==produit_man:
                        product[2]['cout']=0.0
                        product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_man/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Rou/Ins/Insert manuelle : * doc]
                    if work.name=='Routage : Insert manuelle : 1 doc':
                        if documents_man==1:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert manuelle : 2 docs':
                        if documents_man==2:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert manuelle : 3 docs':
                        if documents_man==3:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert manuelle : 4 docs':
                        if documents_man==4:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert manuelle : 5 docs':
                        if documents_man>=5:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Ins/Rapprochement docs]
                    if work.name=='Routage : Rapprochement docs':
                        if insertion_man:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Pli/Pliage feuilles A4]
                    if work.name=='Routage : Pliage A4':
                        if pliage_man>0:
                            workcenter[2]['cout_theo']=(pliage_man*quantite_man)*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=(pliage_man*quantite_man)*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=(pliage_man*quantite_man)
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Ins/Insert manuelle : Passage encolleuse rabat]
                    if work.name=='Routage : Passage encolleuse':
                        if fermeture_man=='patte':
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Adr/Adressage hors ligne]
                    if work.name=='Routage : Adressage hors ligne':
                        if adressage_man:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Aff/Passage machine à affranchir : Hors ligne]
                    if work.name==u'Routage : Affranchissement hors ligne':
                        if machine_man:
                            workcenter[2]['cout_theo']=quantite_man*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_man*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_man
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_man
            b=produit_man_browse and produit_man_browse.name or 'N/A'
            c=fournies_man  and 'vos' or 'nos'
            d=documents_man
            e=insertion_man and u'\nConcordance à respecter entre les documents et/ou les enveloppes' or ''
            f=pliage_man and ('\nPliage de ' + str(pliage_man) + ' document(s)') or ''
            h=adressage_man and '\nAdressage des enveloppes' or ''
            v['name'] = 'Insertion manuelle sous enveloppes ' + b + ', fournies par ' + c + ' soins, de ' + str(d) +\
             ' document(s) fournis par ailleurs.' + e + f + h + u'\nQuantité de plis à produire : ' + str(a)
                
            v['quantite'] = quantite_man
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER ROUTAGE : Insertion mécanisée sous enveloppes
    def onchange_mecanise(self, cr, uid, ids, quantite_mec,produit_mec,fournies_mec,documents_mec,
        pliage_mec,adressage_mec,machine_mec,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            produit_mec_browse=False
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if produit_mec:
                produit_mec_browse=product_obj.browse(cr,uid,produit_mec)
            if produit_mec and produit_mec not in [x[2] and x[2]['product_id'] for x in conf_product_lines]:
                conf_product_lines.append([0,False,{'product_id':produit_mec}])
                produit_mec_browse=product_obj.browse(cr,uid,produit_mec)
            if pliage_mec>documents_mec:
                raise osv.except_osv(_('Attention!'),_("Le nombre de documents à plier ne peut être supérieur au nombre de documents à insérer"))
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    #[Env/???]
                    if not fournies_mec and product[2]['product_id']==produit_mec:
                        product[2]['cout']=quantite_mec*prod.list_price
                        product[2]['quantite']=quantite_mec
                    elif product[2]['product_id']==produit_mec:
                        product[2]['cout']=0.0
                        product[2]['quantite']=0.0
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_mec/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Rou/Ins/Insert meca : * doc]
                    if work.name=='Routage : Insert meca : 1 doc':
                        if documents_mec==1:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert meca : 2 docs':
                        if documents_mec==2:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert meca : 3 docs':
                        if documents_mec==3:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert meca : 4 docs':
                        if documents_mec==4:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Insert meca : 5 docs':
                        if documents_mec>=5:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Pli/Pliage feuilles A4]
                    if work.name=='Routage : Pliage A4':
                        workcenter[2]['cout_theo']=(pliage_mec*quantite_mec)*work.prix_theo_variable + work.prix_theo_fixe 
                        workcenter[2]['cout_marche']=(pliage_mec*quantite_mec)*work.prix_marche_variable + work.prix_marche_fixe 
                        workcenter[2]['quantite']=(pliage_mec*quantite_mec)
                        workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Adr/Adressage en ligne]
                    if work.name=='Routage : Adressage en ligne':
                        if adressage_mec:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Aff/Passage machine à affranchir : Hors ligne]
                    if work.name==u'Routage : Affranchissement hors ligne':
                        if machine_mec:
                            workcenter[2]['cout_theo']=quantite_mec*work.prix_theo_variable + work.prix_theo_fixe 
                            workcenter[2]['cout_marche']=quantite_mec*work.prix_marche_variable + work.prix_marche_fixe 
                            workcenter[2]['quantite']=quantite_mec
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_mec
            b=produit_mec_browse and produit_mec_browse.name or 'N/A'
            c=fournies_mec and 'vos soins' or 'ailleurs'
            d=documents_mec
            f=pliage_mec and ('\nPliage de ' + str(pliage_mec) + ' document(s)') or ''
            h=adressage_mec and '\nAdressage des enveloppes' or ''
            v['name'] = u'Insertion mécanisée sous enveloppes ' + b + ', fournies par ' + c + ', de ' + str(d) +\
             ' document(s) fournis par ailleurs.' + f + h + u'\nQuantité de plis à produire : ' + str(a)
                
            v['quantite'] = quantite_mec
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER ROUTAGE : Mise sous film
    def onchange_film(self, cr, uid, ids, quantite_fil,porte_fil,prepa_fil,documents_fil,
        livraison_fil,palettes_fil,article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            conf_product_lines=[]
            conf_workcenter_lines=[]
            if ids:
                products=self.pool.get('configurator.product.line').search(cr,uid,[('conf_id','=',ids[0])])
                if products:
                    self.pool.get('configurator.product.line').unlink(cr,uid,products)
                workcenters=self.pool.get('configurator.workcenter.line').search(cr,uid,[('conf_id','=',ids[0])])
                if workcenters:
                    self.pool.get('configurator.workcenter.line').unlink(cr,uid,workcenters)
            if article_id:
                mrp_bom=self.pool.get('mrp.bom')
                article = self.pool.get('product.product').browse(cr, uid, article_id, context=context)
                mrp_bom_id=mrp_bom.search(cr,uid,[('product_id','=',article.id)])
                if mrp_bom_id:
                    bom=mrp_bom.browse(cr,uid,mrp_bom_id[0])
                    for bom_line in bom.bom_lines:
                        conf_product_lines.append([0,False,{'product_id':bom_line.product_id.id,'cout':0.0}])
                    if bom.routing_id:
                        for workcenter_line in bom.routing_id.workcenter_lines:
                            conf_workcenter_lines.append([0,False,{'workcenter_id':workcenter_line.workcenter_id.id}])
            if palettes_fil>quantite_fil:
                raise osv.except_osv(_('Attention!'),_("Le nombre de documents par palette ne peut être supérieur au nombre de documents total."))
            for product in conf_product_lines:
                if product[2]:
                    products.append(product[2]['product_id'])
                    prod=product_obj.browse(cr,uid,product[2]['product_id'])
                    product[2]['cout']=0.0
                    product[2]['quantite']=0.0
                    if porte_fil in ('noir','couleur'):
                        #[Pap/OF90]
                        if prod.name==u'090 gsm offset':
                            product[2]['cout']=(quantite_fil/2)*prod.list_price
                            product[2]['quantite']=(quantite_fil/2)
                        #[Sor/Noir]
                        if prod.name==u'Sortie numérique noir':
                            if porte_fil=='noir':
                                product[2]['cout']=(quantite_fil/2)*prod.list_price
                                product[2]['quantite']=(quantite_fil/2)
                        #[Sor/Couleur]
                        if prod.name==u'Sortie numérique couleur':
                            if porte_fil=='couleur':
                                product[2]['cout']=(quantite_fil/2)*prod.list_price
                                product[2]['quantite']=(quantite_fil/2)
                        #[Liv/Palette]
                        if prod.name==u'Palette':
                            if livraison_fil:
                                product[2]['cout']=(quantite_fil/(palettes_fil or 1))*prod.list_price
                                product[2]['quantite']=(quantite_fil/(palettes_fil or 1))
                    prix_revient+=product[2]['cout']
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_fil/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    if porte_fil in ('noir','couleur'):
                        #[Edi/Dat/Data : Préparation données simple]
                        if work.name==u'Editique : Data : Préparation simple':
                            if prepa_fil=='simple':
                                workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_fil
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        #[Edi/Dat/Data : Préparation données complexe]
                        if work.name==u'Editique : Data : Préparation complexe':
                            if prepa_fil=='complexe':
                                workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                                workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                                workcenter[2]['quantite']=quantite_fil
                                workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        #[Num/Sor/Sorties numériques - n:0 SRA3 <135g]
                        if work.name==u'Numérique : Sorties n:0 SRA3 <135g':
                            workcenter[2]['cout_theo']=(quantite_fil/2)*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=(quantite_fil/2)*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=(quantite_fil/2)
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                        #[Num/Mas/Coupe]
                        if work.name==u'Numérique : Coupe':
                            workcenter[2]['cout_theo']=6*((quantite_fil/2)/500)*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=6*((quantite_fil/2)/500)*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=6*((quantite_fil/2)/500)
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/Fil/Mise sous film : * doc]
                    if work.name=='Routage : Mise sous film : 1 doc':
                        if documents_fil==1:
                            workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_fil
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Mise sous film : 2 docs':
                        if documents_fil==2:
                            workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_fil
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Mise sous film : 3 docs':
                        if documents_fil==3:
                            workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_fil
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Mise sous film : 4 docs':
                        if documents_fil==4:
                            workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_fil
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    if work.name=='Routage : Mise sous film : 5 docs':
                        if documents_fil>=5:
                            workcenter[2]['cout_theo']=quantite_fil*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_fil*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_fil
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            a=quantite_fil
            b=porte_fil in ('noir','couleur') and (u'\nDont un porte adresse A4 imprimé ' + (porte_fil=='noir' and 'noir recto' or '') +\
             (porte_fil=='couleur' and 'couleur recto' or '')) or ''
            d=documents_fil
            v['name'] = u'Conditionnement sous film de ' + str(a) + ' paquets contenant ' + str(d) + ' document(s).' + b
                
            v['quantite'] = quantite_fil
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
        
    #ATELIER ROUTAGE : Traitement NPAI
    def onchange_npai(self, cr, uid, ids, quantite_npa,type_npa,ref_npa,
        article_id,conf_product_lines,conf_workcenter_lines, context=None):
        v = {}
        if article_id:
            product_obj=self.pool.get('product.product')
            workcenter_obj=self.pool.get('mrp.workcenter')
            products=[]
            workcenters=[]
            prix_revient=prix_theo=prix_marche=0.0
            
            for workcenter in conf_workcenter_lines:
                if workcenter[2]:
                    workcenters.append(workcenter[2]['workcenter_id'])
                    work=workcenter_obj.browse(cr,uid,workcenter[2]['workcenter_id'])
                    temps = (work.capacity_per_hour and (quantite_npa/work.capacity_per_hour) or 0.0) + work.time_cycle
                    workcenter[2]['cout_theo']=0.0
                    workcenter[2]['cout_marche']=0.0
                    workcenter[2]['quantite']=0.0
                    workcenter[2]['temps']=0.0
                    #[Rou/NPA/NPAI - Saisie code]
                    if work.name==u'Routage : NPAI : Saisie code':
                        if type_npa=='saisie':
                            workcenter[2]['cout_theo']=quantite_npa*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_npa*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_npa
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/NPA/NPAI - Scan code]
                    if work.name==u'Routage : NPAI : Scan code':
                        if type_npa=='scan':
                            workcenter[2]['cout_theo']=quantite_npa*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_npa*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_npa
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    #[Rou/NPA/NPAI - Recherche dans liste]
                    if work.name==u'Routage : NPAI : Recherche dans liste':
                        if type_npa=='recherche':
                            workcenter[2]['cout_theo']=quantite_npa*work.prix_theo_variable + work.prix_theo_fixe
                            workcenter[2]['cout_marche']=quantite_npa*work.prix_marche_variable + work.prix_marche_fixe
                            workcenter[2]['quantite']=quantite_npa
                            workcenter[2]['temps']=self._temps(cr,uid,workcenter[2]['quantite'],work.capacity_per_hour,work.time_cycle)
                    prix_marche+=workcenter[2]['cout_marche']
                    prix_theo+=workcenter[2]['cout_theo']
            
            v['name'] = u'Restitution du fichier des contacts en NPAI pour l\'opération ' + (ref_npa or '') +\
             u' à partir des courriers retournés.'
                
            v['quantite'] = quantite_npa
            v['conf_product_lines'] = conf_product_lines
            v['conf_workcenter_lines'] = conf_workcenter_lines
            v['prix_revient'] = prix_revient
            v['prix_theo'] = prix_theo
            v['prix_marche'] = prix_marche
            v['prix_global_theo'] = prix_revient+prix_theo
            v['prix_global_marche'] = prix_revient+prix_marche
            v['prix_offert'] = prix_revient+prix_marche
        return {'value': v}
    
    #ATELIER ROUTAGE : Affranchissement
    def onchange_affran(self, cr, uid, ids, quantite_plis,masse_plis,article_plis, context=None):
        v = {}
        article=self.pool.get('product.product').browse(cr,uid,article_plis)
        v['name'] = article and article.name or ''
        return {'value': v}
    

    def make_order_line(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('sale.order')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        newinv = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        product_browse=self.pool.get('product.product').browse(cr,uid,data['article_id'][0])
        if context.get('active_model',False)=='sale.order':
            sale_order=order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context)[0]
        else:
            sale_order=order_obj.browse(cr, uid, [data['sale_id'][0]],context=context)[0]
        if sale_order.state!='draft':
            raise osv.except_osv(_('Attention!'), _('Modification possible uniquement en devis.'))
        for line in sale_order.order_line:
            if line.configurator_id.id==data['id']:
                self.pool.get('sale.order.line').unlink(cr,uid,[line.id])
        fpos = sale_order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        read_conf_product_lines=self.pool.get('configurator.product.line').read(cr,uid,data['conf_product_lines'],['cout','product_id','quantite'])
        #~ for composant in read_conf_product_lines:
            #~ product=self.pool.get('product.product').browse(cr,uid,composant['product_id'][0])
            #~ if composant['cout']:
                #~ self.pool.get('sale.order.line').create(cr, uid, {
                    #~ 'order_id': sale_order.id,
                    #~ 'name': product.name,
                    #~ 'price_unit': 0.0,
                    #~ 'product_uom_qty': composant['quantite'],
                    #~ 'product_uos_qty': composant['quantite'],
                    #~ 'product_uos': product.uos_id.id,
                    #~ 'product_uom': product.uom_id.id,
                    #~ 'configurator_id': ids[0],
                    #~ 'product_id': product.id,
                    #~ 'discount': False,
                    #~ 'tax_id': self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product.taxes_id),
                    #~ 'type': 'make_to_order',
                    #~ 'delay':0,
                    #~ 'state':'draft',
                    #~ 'composant':True
                #~ }, context)
        print 'name',product_browse.name
        if product_browse.name=='Affranchissement':
            self.pool.get('sale.order.line').create(cr, uid, {
                'order_id': sale_order.id,
                'name': data['name'],
                'price_unit': self.pool.get('product.product').browse(cr,uid,data['article_plis'][0]).list_price,
                'product_uom_qty': data['quantite_plis'] or 1,
                'product_uos_qty': data['quantite_plis'] or 1,
                'configurator_id': ids[0],
                'product_id': data['article_plis'][0],
                'discount': False,
                'type': 'make_to_order',
                'delay':0,
                'state':'draft',
                'affranchissement': True
            }, context)
        else:
            self.pool.get('sale.order.line').create(cr, uid, {
                'order_id': sale_order.id,
                'name': data['name'],
                'price_unit': data['prix_offert']/(data['quantite'] or 1),
                'product_uom_qty': data['quantite'] or 1,
                'product_uos_qty': data['quantite'] or 1,
                'configurator_id': ids[0],
                'product_id': data['article_id'][0],
                'discount': False,
                'type': 'make_to_order',
                'delay':0,
                'state':'draft',
                'produit_fini':True
            }, context)
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'name' : _('Quotation'),
                'res_id': sale_order and sale_order.id    
                }
        
    def unlink(self, cr, uid, ids,  context=None):
        if context is None:
            context={}
        if isinstance(ids, (str, int, long)):
            ids = [ids]
        sale_lines=self.pool.get('sale.order.line').search(cr,uid,[('configurator_id','in',ids)])
        self.pool.get('sale.order.line').unlink(cr,uid,sale_lines)
        return super(configurator,self).unlink(cr, uid, ids, context=context)
    
    def create(self, cr, uid, vals, context=None):
        res=super(configurator, self).create(cr, uid, vals, context=context)
        configurator_browse=self.pool.get('configurator').browse(cr,uid,res)
        sale=self.pool.get('sale.order').browse(cr,uid,configurator_browse.sale_id.id,context=context)
        for sale_line in sale.order_line:
            sale_line.configurator_id.name,configurator_browse.name
            if sale_line.configurator_id.name==configurator_browse.name:
                self.pool.get('sale.order.line').write(cr,uid,sale_line.id,{'configurator_id':res},context=context)
        return res

configurator()
