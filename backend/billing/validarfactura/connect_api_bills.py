import requests
import os
from dotenv import load_dotenv
load_dotenv()
SCOPE = "/oauth/token"
def obtener_access_token():
    url = os.getenv("url_api")+SCOPE
    data = {
        'grant_type': os.getenv("grant_type"),
        'client_id': os.getenv("client_idF"),
        'client_secret': os.getenv("client_secretF"),
        'username':os.getenv("usernameF"),
        'password':os.getenv("password")
    }

    headers = {
        'Accept': 'application/json'
    }
    
    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        return access_token
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None