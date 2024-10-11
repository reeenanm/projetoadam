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

# Função para buscar pedidos filtrados por data
def get_orders_by_date(from_date, to_date):
    url = f'https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={from_date}&order.date_created.to={to_date}'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['results']
    return []

# Função para calcular o total de vendas e faturamento
def calculate_sales_metrics(orders):
    total_orders = len(orders)
    total_revenue = sum(order['total_amount'] for order in orders)
    return total_orders, total_revenue

# Função para obter as vendas do dia
def get_today_sales():
    today = datetime.now().strftime('%Y-%m-%dT00:00:00.000-00:00')
    now = datetime.now().strftime('%Y-%m-%dT23:59:59.999-00:00')
    orders = get_orders_by_date(today, now)
    return calculate_sales_metrics(orders)

# Função para obter as vendas da semana
def get_week_sales():
    today = datetime.now()
    start_of_week = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%dT00:00:00.000-00:00')
    now = today.strftime('%Y-%m-%dT23:59:59.999-00:00')
    orders = get_orders_by_date(start_of_week, now)
    return calculate_sales_metrics(orders)

# Função para obter as vendas do mês
def get_month_sales():
    today = datetime.now()
    start_of_month = today.replace(day=1).strftime('%Y-%m-%dT00:00:00.000-00:00')
    now = today.strftime('%Y-%m-%dT23:59:59.999-00:00')
    orders = get_orders_by_date(start_of_month, now)
    return calculate_sales_metrics(orders)

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

# Rota para buscar anúncios e renderizar página de alteração de estoque com métricas de vendas
@app.route('/update_items', methods=['GET'])
def update_items_page():
    # Obter métricas de vendas
    today_orders, today_revenue = get_today_sales()
    week_orders, week_revenue = get_week_sales()
    month_orders, month_revenue = get_month_sales()

    # Buscar os itens
    url = f'https://api.mercadolibre.com/users/{USER_ID}/items/search'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        item_ids = response.json().get('results', [])
        items = []
        
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
        
        # Renderizar a página com métricas de vendas no cabeçalho
        return render_template('update_items.html', items=items, 
                               today_orders=today_orders, today_revenue=today_revenue, 
                               week_orders=week_orders, week_revenue=week_revenue, 
                               month_orders=month_orders, month_revenue=month_revenue)
    else:
        return jsonify({'error': 'Erro ao buscar anúncios', 'message': response.json()}), response.status_code

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
