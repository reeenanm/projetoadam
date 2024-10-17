from flask import Flask, request, redirect, jsonify
import requests
import sqlite3

app = Flask(__name__)

# Configurações do Mercado Livre
CLIENT_ID = '6141251411464395'
CLIENT_SECRET = 'ddLnHy0Dty6zhkqkI1ihLt7f1ms08r1e'
REDIRECT_URI = 'projetoadam-production.up.railway.appprojetoadam-production.up.railway.app/ad4m/callback'

# Função para salvar o token no banco de dados
def save_token(user_id, platform, access_token, refresh_token, expires_in):
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO tokens (user_id, platform, access_token, refresh_token, expires_in)
                      VALUES (?, ?, ?, ?, ?)''', (user_id, platform, access_token, refresh_token, expires_in))
    conn.commit()
    conn.close()

# Rota para iniciar a autenticação com o Mercado Livre
@app.route('/login_mercadolivre')
def login_mercadolivre():
    auth_url = f'https://auth.mercadolivre.com.br/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}'
    return redirect(auth_url)

# Callback do Mercado Livre após a autorização
@app.route('/callback_mercadolivre')
def callback_mercadolivre():
    auth_code = request.args.get('code')
    if not auth_code:
        return 'Erro: Código de autorização não fornecido pelo Mercado Livre', 400

    # Faz a troca do código de autorização pelo Access Token
    token_url = 'https://api.mercadolibre.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }

    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        user_id = token_data.get('user_id')

        # Salvar os tokens no banco de dados
        save_token(user_id, 'Mercado Livre', access_token, refresh_token, expires_in)
        return jsonify({
            'message': 'Conta Mercado Livre conectada com sucesso!',
            'access_token': access_token
        })
    else:
        return 'Erro ao trocar o código de autorização pelo token', 400

# Teste para ver se o servidor está funcionando
@app.route('/')
def home():
    return 'Servidor backend está rodando!'

if __name__ == '__main__':
    app.run(debug=True)
