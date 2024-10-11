import os
import requests
import json
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Configurações da API do Mercado Livre
CLIENT_ID = '7511527097985348'  # Seu Client ID
CLIENT_SECRET = 'IvUCyebIc9QqDrLKxwPOANMFE82p8Gz8'  # Seu Client Secret
REDIRECT_URI = 'https://projetoadam-production.up.railway.app'
ACCESS_TOKEN = None  # Será atualizado dinamicamente
USER_ID = None  # Será atualizado dinamicamente

# Função para buscar detalhes de um item
def get_item_details(item_id):
    url = f'https://api.mercadolibre.com/items/{item_id}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar detalhes do item {item_id}: {response.status_code}")
        return None

# Função para carregar tokens
def load_tokens():
    global ACCESS_TOKEN, USER_ID
    try:
        with open('tokens.json', 'r') as token_file:
            tokens = json.load(token_file)
            ACCESS_TOKEN = tokens.get('access_token')
            USER_ID = tokens.get('user_id')
    except FileNotFoundError:
        print("Arquivo de tokens não encontrado.")

# Carregar tokens ao iniciar a aplicação
load_tokens()

# Função para salvar tokens
def save_tokens(access_token, refresh_token, user_id):
    with open('tokens.json', 'w') as token_file:
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user_id
        }
        json.dump(token_data, token_file)
        print("Tokens salvos com sucesso.")

# Rota para exibir e buscar anúncios
@app.route('/update_items', methods=['GET'])
def update_items_page():
    search_query = request.args.get('search')  # Captura o termo de busca
    page = int(request.args.get('page', 1))  # Página atual (padrão 1)
    limit = 10
    offset = (page - 1) * limit

    if search_query:
        url = f'https://api.mercadolibre.com/sites/MLB/search?q={search_query}&limit={limit}&offset={offset}'
    else:
        url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search?offset={offset}&limit={limit}'

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        item_ids = data.get('results', [])
        total_items = data['paging']['total']
        
        items = []
        for item_id in item_ids:
            item_details = get_item_details(item_id)
            if item_details:
                items.append({
                    'id': item_details['id'],
                    'title': item_details['title'],
                    'price': item_details['price'],
                    'available_quantity': item_details['available_quantity'],
                    'thumbnail': item_details['thumbnail'],
                    'visits': item_details.get('visits', 'N/A'),
                    'sold_quantity': item_details.get('sold_quantity', 'N/A'),
                    'status': item_details['status'],
                    'date_created': item_details['date_created']
                })
        
        total_pages = (total_items + limit - 1) // limit
        return render_template('update_items.html', items=items, page=page, total_pages=total_pages)
    else:
        return "Erro ao buscar anúncios", 500

# Função para atualizar itens em massa
@app.route('/update_all_items', methods=['POST'])
def update_all_items():
    for item_id in request.form.keys():
        if item_id.startswith('stock_'):
            real_item_id = item_id.split('_')[1]
            new_stock = request.form[item_id]
            update_stock(real_item_id, new_stock)
        elif item_id.startswith('price_'):
            real_item_id = item_id.split('_')[1]
            new_price = request.form[item_id]
            update_price(real_item_id, new_price)
    
    return "Todos os itens foram atualizados com sucesso!"

# Função para atualizar estoque
def update_stock(item_id, new_stock):
    url = f'https://api.mercadolibre.com/items/{item_id}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    payload = {
        'available_quantity': int(new_stock)
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Estoque do item {item_id} atualizado com sucesso.")
    else:
        print(f"Erro ao atualizar o estoque do item {item_id}: {response.text}")

# Função para atualizar preço
def update_price(item_id, new_price):
    url = f'https://api.mercadolibre.com/items/{item_id}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    payload = {
        'price': float(new_price)
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"Preço do item {item_id} atualizado com sucesso.")
    else:
        print(f"Erro ao atualizar o preço do item {item_id}: {response.text}")

# Iniciando a aplicação
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
