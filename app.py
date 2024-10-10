from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Dados da notificação do Mercado Livre
    print(f'Dados recebidos: {data}')
    return jsonify({'status': 'received'}), 200
