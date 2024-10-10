import os
import requests
import json
from flask import Flask, request, jsonify, render_template, redirect

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
    # Caminho absoluto para o arquivo
    file_path = os.path.join(os.getcwd(), 'tokens.json')
    
    print(f"Salvando tokens no arquivo: {file_path}")  # Log para verificar o caminho do arquivo
    
    # Salvando tokens no arquivo
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

# Função para buscar os detalhes de um item
def get_item_details(item_id):
    url = f'https://api.mercadolibre.com/items/{item_id}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# Rota para buscar anúncios e renderizar página de alteração de estoque
@app.route('/update_items', methods=['GET'])
def update_items_page():
    print(f"ACCESS_TOKEN usado: {ACCESS_TOKEN}")  # Log para verificar o token
    print(f"USER_ID usado: {USER_ID}")  # Log para verificar o User ID

    url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)
    print(f"Resposta da API ao buscar anúncios: {response.text}")  # Log da resposta da API

    if response.status_code == 200:
        item_ids = response.json().get('results', [])
        items = []
        
        # Para cada item_id, buscar os detalhes do item
        for item_id in item_ids:
            item_details = get_item_details(item_id)
            if item_details:
                items.append({
                    'id': item_details['id'],
                    'title': item_details['title'],
                    'price': item_details['price'],
                    'available_quantity': item_details['available_quantity'],
                    'thumbnail': item_details['thumbnail']
                })
        
        return render_template('update_items.html', items=items)
    else:
        return jsonify({'error': 'Erro ao buscar anúncios', 'message': response.json()}), response.status_code

# Rota para processar o código de autorização e obter os tokens
@app.route('/')
def callback():
    # O Mercado Livre retorna o código de autorização
    code = request.args.get('code')

    if code:
        # Usar o código de autorização para obter o access token
        token_url = 'https://api.mercadolibre.com/oauth/token'
        payload = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        response = requests.post(token_url, data=payload)

        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens['access_token']
            refresh_token = tokens['refresh_token']

            # Aqui você salva os tokens e obtém o user_id
            user_info_url = 'https://api.mercadolibre.com/users/me'
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            user_info_response = requests.get(user_info_url, headers=headers)

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                user_id = user_info['id']  # Pega o user_id da resposta
                global USER_ID
                USER_ID = user_id  # Atualiza o USER_ID globalmente
                
                # Salvar tokens e user_id
                save_tokens(access_token, refresh_token, user_id)

                # Atualiza o ACCESS_TOKEN global
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
    port = int(os.environ.get('PORT', 8080))  # Usando a porta 8080 no Railway
    app.run(host='0.0.0.0', port=port)
