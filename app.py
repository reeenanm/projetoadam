from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Dados da notificação do Mercado Livre
    print(f'Dados recebidos: {data}')
    return jsonify({'status': 'received'}), 200

@app.route('/orders', methods=['GET'])
def get_orders():
    # Access Token obtido anteriormente
    access_token = os.getenv('ACCESS_TOKEN')  # Coloque seu Access Token aqui ou pegue-o dinamicamente

    url = f'https://api.mercadolibre.com/orders/search?seller={os.getenv("USER_ID")}'  # Use seu user_id
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        orders = response.json()
        return jsonify(orders), 200
    else:
        return jsonify({'error': 'Erro ao buscar pedidos', 'message': response.json()}), response.status_code
