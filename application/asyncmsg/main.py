import sys
import os
import json
from django.shortcuts import redirect
from apipkg import api_manager


from apipkg import queue_manager as queue
sys.dont_write_bytecode = True

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from application.djangoapp import api
from application.djangoapp import simulate
from application.djangoapp.models import *
from application.djangoapp import internalFunctions


def main():
    print("Liste des ventes:")
    for v in Vente.objects.all():
        print("ID: " + str(v.id) + "\tArticle: " + v.article.nom + "\tDate: " + str(v.date))


def dispatch(ch, method, properties, body):
    jsonLoad = json.loads(body)
    fromApp = jsonLoad["from"]
    functionName = ""
    if 'functionname' in jsonLoad:
        functionName = jsonLoad["functionname"]
    internalFunctions.myprint(" [x] Received async from", fromApp, "with function '" + functionName + "'")

    if fromApp == 'catalogue-produit':
        #if functionName == 'get_new_products':
        api.get_new_products(jsonLoad)

    elif fromApp == 'gestion-stock':
        if functionName == 'get_stock':
            api.get_stocks(jsonLoad, simulate=False) # enlever "simulate=true" une fois le fournisseur implémenté
        elif functionName == "get_stock_order_response":
            api.get_stock_order_response(jsonLoad)

    elif fromApp == 'gestion-magasin':
        # if functionName == 'get_order_magasin
        id_order = "No id reached"
        try:
            id_order = jsonLoad["body"]
            try:
                id_order = id_order["idCommande"]
            except:
                internalFunctions.myprint("[!] There are no command id in the json received from magasin")
        except:
            internalFunctions.myprint(" [!] There are no body in the json received from magasin")
        try:
            length = len(jsonLoad["body"]['produits'])
        except:
            internalFunctions.myprint(" [!] There are either no body or no produits in body in the json received from magasin")
        internalFunctions.myprint("     --> Order from magasin, command ID is :", id_order, "length of list is :", length)
        api.get_order_magasin(jsonLoad)

    elif fromApp == 'gestion-commerciale':
        if functionName == "get_new_products":
            api.get_new_products(jsonLoad)
        elif functionName == "get_stocks":
            api.get_stocks(jsonLoad, simulate=True)
        elif functionName == "get_order_magasin":
            api.get_order_magasin(jsonLoad, simulate=True)
        elif functionName == "simulate_get_order_stocks":
            simulate.simulate_get_order_stocks(jsonLoad)
        elif functionName == "get_stock_order_response":
            api.get_stock_order_response(jsonLoad, simulate=True)
        elif functionName =="simulate_magasin_get_order_response":
            internalFunctions.myprint("Magasin receive response")
        elif functionName == "simulate_fournisseur_stock":
            simulate.simulate_fournisseur_stock(jsonLoad)
        elif functionName == "fournisseur_stock_response":
            api.fournisseur_stock_response(jsonLoad, simulate=True)
        elif functionName == "simulate_stock_reorder":
            internalFunctions.myprint("Stock reordered")
        else:
            internalFunctions.myprint("Le nom de la fonction dans le json n est pas valide")

    else:
        internalFunctions.myprint("Le nom de l application du json n est pas valide")



if __name__ == '__main__':
    queue.receive('gestion-commerciale', dispatch)
    main()
