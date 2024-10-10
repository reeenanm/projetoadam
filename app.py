import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Mercado Livre!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Usa a porta 8080 ou a que estiver configurada no ambiente
    app.run(host='0.0.0.0', port=port)
