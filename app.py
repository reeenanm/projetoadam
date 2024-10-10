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
ACCESS_TOKEN = 'APP_USR-7511527097985348-101014-a028bfcbfa9fdd92660908a308b8ea9e-1281315022'  # Access Token inicial
USER_ID = '1281315022'  # Substitua pelo seu user_id

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
    url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)

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

# Rota para atualizar estoque e preço de um item
@app.route('/update_stock_price/<item_id>', methods=['PUT'])
def update_stock_price(item_id):
    data = request.json
    if not data:
        return jsonify({'error': 'Nenhum dado fornecido.'}), 400

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {}
    if 'available_quantity' in data:
        payload['available_quantity'] = data['available_quantity']
    if 'price' in data:
        payload['price'] = data['price']

    url = f'https://api.mercadolibre.com/items/{item_id}'
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        return jsonify({'status': 'Atualização bem-sucedida'}), 200
    else:
        return jsonify({'error': 'Erro ao atualizar', 'message': response.json()}), response.status_code

# Rota para redirecionar o usuário para a página de autorização do Mercado Livre
@app.route('/change_account')
def change_account():
    # Redireciona o usuário para a página de autorização do Mercado Livre
    auth_url = f'{OAUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}'
    return redirect(auth_url)

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

            # Aqui você pode salvar os tokens em um arquivo, banco de dados, ou outro local seguro
            with open('tokens.json', 'w') as token_file:
                token_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                json.dump(token_data, token_file)

            # Atualiza o ACCESS_TOKEN global
            global ACCESS_TOKEN
            ACCESS_TOKEN = access_token

            return "Conta alterada com sucesso! Tokens salvos."
        else:
            return jsonify({'error': 'Erro ao obter o token de acesso', 'message': response.json()}), 400
    else:
        return "Código de autorização não recebido", 400

# Configuração do servidor
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Usando a porta 8080 no Railway
    app.run(host='0.0.0.0', port=port)
