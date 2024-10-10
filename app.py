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

# Rota para buscar pedidos
@app.route('/orders', methods=['GET'])
def get_orders():
    url = f'https://api.mercadolibre.com/orders/search?seller={USER_ID}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        orders = response.json()
        return jsonify(orders), 200
    else:
        return jsonify({'error': 'Erro ao buscar pedidos', 'message': response.json()}), response.status_code

# Rota para o webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Pega os dados enviados no webhook
    print(f'Dados recebidos do webhook: {data}')
    return jsonify({'status': 'success'}), 200

# Rota para atualizar estoque de um item via formulário
@app.route('/update_stock/<item_id>', methods=['PUT'])
def update_stock(item_id):
    new_quantity = request.json.get('quantity')
    
    if new_quantity is None:
        return jsonify({'error': 'Quantidade não fornecida ou formato incorreto.'}), 400
    
    print(f'Atualizando estoque do item {item_id} para {new_quantity} unidades')

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

# Rota para exibir o formulário de atualização de estoque
@app.route('/update_item', methods=['GET'])
def update_item_page():
    return render_template('update_item.html')

# Configuração do servidor
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Usando a porta 8080 no Railway
    app.run(host='0.0.0.0', port=port)
