import os
import requests
import json
from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime, timedelta

app = Flask(__name__)

# Configurações da API do Mercado Livre
OAUTH_URL = "https://auth.mercadolivre.com.br/authorization"
CLIENT_ID = '7511527097985348'  # Substitua pelo seu Client ID
CLIENT_SECRET = 'IvUCyebIc9QqDrLKxwPOANMFE82p8Gz8'  # Substitua pelo seu Client Secret
REDIRECT_URI = 'https://projetoadam-production.up.railway.app'  # Sem o /callback, conforme o registrado no painel
ACCESS_TOKEN = None  # Access Token será atualizado dinamicamente
USER_ID = None  # User ID será atualizado dinamicamente

# Função para carregar tokens do arquivo
def load_tokens():
    global ACCESS_TOKEN, USER_ID
    try:
        with open('tokens.json', 'r') as token_file:
            tokens = json.load(token_file)
            ACCESS_TOKEN = tokens.get('access_token')
            USER_ID = tokens.get('user_id')
            print(f"Tokens carregados: ACCESS_TOKEN={ACCESS_TOKEN}, USER_ID={USER_ID}")
    except FileNotFoundError:
        print("Arquivo de tokens não encontrado.")

# Função para salvar tokens no arquivo (com caminho absoluto)
def save_tokens(access_token, refresh_token, user_id):
    file_path = os.path.join(os.getcwd(), 'tokens.json')
    with open(file_path, 'w') as token_file:
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user_id
        }
        json.dump(token_data, token_file)
        print("Tokens salvos com sucesso.")

# Carregar tokens ao iniciar a aplicação
load_tokens()

# Função para buscar anúncios com paginação
def get_items_with_pagination(offset=0, limit=10):
    url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search?offset={offset}&limit={limit}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        total_items = data['paging']['total']  # Total de anúncios disponíveis
        items = data.get('results', [])
        return items, total_items
    return [], 0

# Rota para buscar anúncios e renderizar página de alteração de estoque com paginação
@app.route('/update_items', methods=['GET'])
def update_items_page():
    # Parâmetros de paginação
    page = int(request.args.get('page', 1))  # Página atual (padrão é 1)
    limit = 10  # Quantidade de itens por página
    offset = (page - 1) * limit  # Calcular o offset com base na página

    # Buscar anúncios com paginação
    items, total_items = get_items_with_pagination(offset, limit)
    
    # Cálculo de páginas
    total_pages = (total_items + limit - 1) // limit  # Número total de páginas
    
    # Renderizar a página de itens com paginação
    return render_template('update_items.html', items=items, page=page, total_pages=total_pages)

# Rota para processar o código de autorização e obter os tokens
@app.route('/')
def callback():
    print("Callback recebido")
    code = request.args.get('code')
    print(f"Código de autorização recebido: {code}")

    if code:
        token_url = 'https://api.mercadolibre.com/oauth/token'
        payload = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        response = requests.post(token_url, data=payload)
        print(f"Resposta da API ao obter token: {response.text}")

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']

            user_info_url = 'https://api.mercadolibre.com/users/me'
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            user_info_response = requests.get(user_info_url, headers=headers)
            print(f"Resposta da API ao obter user_id: {user_info_response.text}")

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                user_id = user_info['id']
                global USER_ID
                USER_ID = user_id

                save_tokens(access_token, refresh_token, user_id)
                global ACCESS_TOKEN
                ACCESS_TOKEN = access_token

                return "Conta alterada com sucesso! Tokens salvos."
            else:
                return jsonify({'error': 'Erro ao obter o user_id', 'message': user_info_response.json()}), 400
        else:
            return jsonify({'error': 'Erro ao obter o token de acesso', 'message': response.json()}), 400
    else:
        return "Código de autorização não recebido", 400

# Configuração do servidor
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
