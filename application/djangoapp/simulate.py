from . import internalFunctions
from . import api
from apipkg import api_manager

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.shortcuts import render, redirect

import os
from apipkg import queue_manager as queue


def index(request):
    context = {}
    return render(request, "simulate.html", context)

def simulate_catalogue_add_new_products(request):
    body = \
        {
            "produits": [
                {
                    "id": 1664,
                    "codeProduit": "X1664",
                    "familleProduit": "Bière",
                    "descriptionProduit": "1664",
                    "quantiteMin": 24,
                    "packaging": 1,
                    "prix": 666,
                    "exclusivite": ""
                },
                {
                    "id": 1,
                    "codeProduit": "X3-0",
                    "familleProduit": "Surgelés",
                    "descriptionProduit": "Pizza",
                    "quantiteMin": 1,
                    "packaging": 2,
                    "prix": 12,
                    "exclusivite": "ecommerce"
                },
            ]
        }

    time = api_manager.send_request('scheduler', 'clock/time')
    message = '{ "from":"' + os.environ[
        'DJANGO_APP_NAME'] + '", "to":"gestion-commerciale", "datetime": ' + time + ', "body": ' + json.dumps(body) + ', "functionname":"simulate_get_new_products"}'
    queue.send('gestion-commerciale', message)
    return redirect(internalFunctions.display_products)


# Simule le comportement du magain quand il commande du stock

def simulate_placing_order(request):
    body = \
        {
            "idCommande": 123,
            "Produits": [
                {
                    "codeProduit": "X1-1",
                    "quantite": 1,
                },
                {
                    "codeProduit": "X1-2",
                    "quantite": 11,
                },
            ]
        }
    headers = {"Host": "gestion-commerciale"}
    r = requests.post(api_manager.api_services_url + "place-order", headers=headers, json=internalFunctions.dict_to_json(body))
    print(r.text)
    return redirect(internalFunctions.display_orders)


# Simule le comportement de stock vis à vis du bon de commande

def simulate_stock_reorder(request):
    api.stock_reorder(request, simulate=True)

@csrf_exempt
def simulate_stock_response(request):
    return JsonResponse(json.loads(request.body))