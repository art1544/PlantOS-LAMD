import pika
import os
import json

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
EXCHANGE_NAME = 'plantos.events'

def get_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    return connection

def setup_queues():
    """Declara as filas duráveis e seus bindings."""
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

    # Fila do operador (recebe eventos de aceite, recusa, andamento e conclusão)
    channel.queue_declare(queue='fila.operador', durable=True)
    for key in ['os.aceita', 'os.recusada', 'os.em_andamento', 'os.concluida']:
        channel.queue_bind(exchange=EXCHANGE_NAME, queue='fila.operador', routing_key=key)

    # Fila do técnico (recebe eventos de criação de OS)
    channel.queue_declare(queue='fila.tecnico', durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue='fila.tecnico', routing_key='os.criada')

    connection.close()


def publish_event(routing_key, payload):
    """
    Publica um evento na exchange plantos.events.
    routing_key: tipo do evento (ex: 'os.criada', 'os.aceita')
    payload: dicionário com os dados do evento
    """
    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

    from datetime import datetime
    message = {
        'evento': routing_key,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'dados': payload
    }

    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Mensagem persistente
            content_type='application/json'
        )
    )

    print(f" [x] Published {routing_key}")
    connection.close()
