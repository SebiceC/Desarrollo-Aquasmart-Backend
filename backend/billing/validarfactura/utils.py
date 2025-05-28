from .models import InvoiceApi
from django.utils import timezone
from datetime import timedelta
import os
import requests
from dotenv import load_dotenv
load_dotenv()

def get_valid_access_token():
    scope = "/oauth/token"
    
    instancia, _ = InvoiceApi.objects.get_or_create(id=1)  # asumes una única fila

    # 1. Si el token actual es válido
    if instancia.token and instancia.expires_at and instancia.expires_at > timezone.now():
        return instancia.token

    print("Token expirado. Intentando refrescar...")

    # 2. Intentar renovar el token con el refresh_token
    refresh_url = os.getenv("url_api_f") + scope
    data = {
        'grant_type': 'refresh_token',
        'client_id': os.getenv("client_id_f"),
        'client_secret': os.getenv("client_secret_f"),
        'refresh_token': instancia.refresh
    }

    headers = {'Accept': 'application/json'}
    response = requests.post(refresh_url, data=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        new_token = response_data.get('access_token')
        new_refresh = response_data.get('refresh_token', instancia.refresh)  # puede venir igual
        expires_in = response_data.get('expires_in', 3600)

        instancia.token = new_token
        instancia.refresh = new_refresh
        instancia.expires_at = timezone.now() + timedelta(seconds=expires_in)
        instancia.save()
        return new_token

    print("El refresh_token no es válido. Obteniendo nuevo token...")

    # 3. Obtener nuevo token desde cero
    data = {
        'grant_type': "password",
        'client_id': os.getenv("client_id_f"),
        'client_secret': os.getenv("client_secret_f"),
        'username': os.getenv("username_f"),
        'password': os.getenv("password_f")
    }

    response = requests.post(refresh_url, data=data, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        new_token = response_data.get('access_token')
        new_refresh = response_data.get('refresh_token')
        expires_in = response_data.get('expires_in', 3600)

        instancia.token = new_token
        instancia.refresh = new_refresh
        instancia.expires_at = timezone.now() + timedelta(seconds=expires_in)
        instancia.save()
        return new_token

    print(f"No se pudo obtener token nuevo: {response.status_code} - {response.text}")
    return None

import json
def consult_validated_invoice(number):
    print("dentro la funcion")
    token = get_valid_access_token()
    if not token:
        print("no se pudo obtener un token válido")
        return None

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    scope ="/v1/bills/show/"
    url_protegido = os.getenv("url_api_f") + scope + number
    response = requests.get(url_protegido, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("Datos recibidos desde la API:")
        print(json.dumps(data, indent=4))
        return data
    else:
        print(f"Error en solicitud protegida: {response.status_code} - {response.text}")
        return None

