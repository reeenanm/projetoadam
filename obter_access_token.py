import requests

# Dados para a requisição
CLIENT_ID = '7511527097985348'
CLIENT_SECRET = 'IvUCyebIc9QqDrLKxwPOANMFE82p8Gz8'
AUTHORIZATION_CODE = 'TG-67082132af8165000135175b-1281315022'
REDIRECT_URI = 'https://projetoadam-production.up.railway.app'

url = 'https://api.mercadolibre.com/oauth/token'

payload = {
    'grant_type': 'authorization_code',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': AUTHORIZATION_CODE,
    'redirect_uri': REDIRECT_URI
}

response = requests.post(url, data=payload)

# Exibir o Access Token e o Refresh Token
print(response.json())
