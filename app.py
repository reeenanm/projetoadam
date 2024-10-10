import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Access Token atualizado
ACCESS_TOKEN = 'APP_USR-7511527097985348-101014-a028bfcbfa9fdd92660908a308b8ea9e-1281315022'
USER_ID = '1281315022'  # Seu user_id

# Rota principal
@app.route('/')
def home():
    return "Integração Mercado Livre", 200

# Rota para buscar anúncios e renderizar página de alteração de estoque
@app.route('/update_items', methods=['GET'])
def update_items_page():
    url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        items = response.json().get('results', [])
        return render_template('update_items.html', items=items)
    else:
        return jsonify({'error': 'Erro ao buscar anúncios', 'message': response.json()}), response.status_code

# Rota para atualizar estoque de um item via formulário
@app.route('/update_stock/<item_id>', methods=['PUT'])
def update_stock(item_id):
    new_quantity = request.json.get('quantity')
    
    if new_quantity is None:
        return jsonify({'error': 'Quantidade não fornecida ou formato incorreto.'}), 400

    url = f'https://api.mercadolibre.com/items/{item_id}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    payload = {
        "available_quantity": new_quantity
    }

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 200:
        return jsonify({'status': 'Estoque atualizado com sucesso'}), 200
    else:
        return jsonify({'error': 'Erro ao atualizar estoque', 'message': response.json()}), response.status_code

# Configuração do servidor
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Usando a porta 8080 no Railway
    app.run(host='0.0.0.0', port=port)
