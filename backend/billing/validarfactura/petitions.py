import requests
from connect_api_bills import obtener_access_token
import os
import json
from dotenv import load_dotenv
load_dotenv()
SCOPE ="/v1/bills/show/"
NUMBER ="SETP990012266"
print("antes de la funcion")

def hacer_peticion():
    print("dentro la funcion")
    token =os.getenv("TOKEN_ACCES") #obtener_access_token()
    if not token:
        print("no llego token")
        return None

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    url_protegido = os.getenv("url_api")+SCOPE+NUMBER
    response = requests.get(url_protegido, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("Datos recibidos desde la API:")
        print(json.dumps(data, indent=4))  # Imprime en formato bonito (pretty)
        return data
    else:
        print(f"Error en solicitud protegida: {response.status_code}")
        return None

hacer_peticion()    