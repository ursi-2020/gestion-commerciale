from django.http import HttpResponse
from django.shortcuts import redirect
from apipkg import api_manager
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import random
from .models import *
from . import internalFunctions
import os
from apipkg import queue_manager as queue



#Catalogue
# Récupère les nouveaux produits du catalogue
def get_new_products(jsonLoad):
    products = jsonLoad["body"]["produits"]
    for product in products:
        new_product = Product.objects.create(
            codeProduit=product["codeProduit"],
            familleProduit=product["familleProduit"],
            descriptionProduit=product["descriptionProduit"],
            quantiteMin=product["quantiteMin"],
            packaging=product["packaging"],
            prix=product["prix"],
            quantite=0
        )

        new_product.save()
    nb_products = len(products)
    print(str(nb_products) + " products were saved")

    return redirect(internalFunctions.display_products)

# Magasin

# Récupère la commande du magasin
def get_order_magasin(jsonLoad, simulate=False):
    body = jsonLoad["body"]
    body["livraison"] = 0
    products = body["produits"]


    newDeliveryRequest = DeliveryRequest.objects.create( identifiantBon=body["idCommande"])
    newDeliveryRequest.save()
    for product in products:
        newRequestProduct = RequestProduct.objects.create(
            deliveryRequest= newDeliveryRequest,
            product=Product.objects.filter(codeProduit=product["codeProduit"])[0],
            quantiteDemandee=product["quantite"],
            quantiteLivree=0
        )
        newRequestProduct.save()

    time = api_manager.send_request('scheduler', 'clock/time')
    message = None
    if simulate:
        internalFunctions.sendAsyncMsg("gestion-commerciale", body, "simulate_get_order_stocks")
    else:
        internalFunctions.sendAsyncMsg("gestion-stock", body, "get_order_stocks")
    return redirect(internalFunctions.display_products)


# Stock

# Reçoit l'état des stocks
def get_stocks(jsonLoad, simulate=False):
    products = jsonLoad["body"]["produits"]
    for product in products:
        p = Product.objects.filter(codeProduit=product["codeProduit"])[0]
        p.quantite = product["quantite"]
        p.save()
    internalFunctions.reorderStock(simulate)

# Reçoit la réponse des stocks pour la demande de restock du magasin
def get_stock_order_response(jsonLoad, simulate=False):
    body = jsonLoad["body"]
    products = jsonLoad["body"]["produits"]
    deliveryRequest = DeliveryRequest.objects.filter(identifiantBon=body["idCommande"])[0]
    for product in products:
        p = Product.objects.filter(codeProduit=product["codeProduit"])[0]
        p.quantite += product["quantite"]
        p.save()

        requestProduct = RequestProduct.objects.filter(deliveryRequest=deliveryRequest, product=p)[0]

        requestProduct.quantiteLivree = product["quantite"]
        requestProduct.save()

    time = api_manager.send_request('scheduler', 'clock/time')
    if simulate:
        internalFunctions.sendAsyncMsg("gestion-commerciale", body, "simulate_magasin_get_order°response")
    else:
        internalFunctions.sendAsyncMsg("gestion-magasin", body, "get_order_response")
    return redirect(internalFunctions.display_products)

# Reçoit la réponse du fournisseur pour la demande de stock
def fournisseur_stock_response(jsonLoad, simulate=False):
    body = jsonLoad["body"]
    products = jsonLoad["body"]["produits"]

    stockReorder = StockReorder.objects.filter(identifiantBon=body["identifiantBon"])[0]
    for product in products:
        p = Product.objects.filter(codeProduit=product["codeProduit"])[0]
        p.quantite = product["quantite"]
        p.save()

        reorderProduct = ReorderProduct.objects.filter(stockReorder=stockReorder, product=p)[0]
        reorderProduct.quantiteLivree = product["quantite"]
        reorderProduct.save()


    if simulate:
        internalFunctions.sendAsyncMsg("gestion-commerciale", body, "simulate_stock_reorder")
    else:
        internalFunctions.sendAsyncMsg("gestion-stock", body, "gestion-stock")
    return redirect(internalFunctions.display_products)



