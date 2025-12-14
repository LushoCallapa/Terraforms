from flask import Flask, request
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import logging
import sys

app = Flask(__name__)

# Logging a stdout (ideal para Docker + Promtail)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stdout
)

# Métrica Prometheus
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total de solicitudes HTTP',
    ['method', 'endpoint']
)

@app.route('/')
def index():
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    logging.error("Error de prueba: variable no definida")
    return "Hola, mundo!"

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {
        'Content-Type': CONTENT_TYPE_LATEST
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
