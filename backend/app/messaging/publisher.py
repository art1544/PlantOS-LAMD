import pika
import os
import json
from datetime import datetime, timezone

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
EXCHANGE_NAME = 'plantos.events'

def get_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    return connection

def setup_queues():
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

    channel.queue_declare(queue='fila.operador', durable=True)
    for key in ['os.aceita', 'os.recusada', 'os.em_andamento', 'os.concluida']:
        channel.queue_bind(exchange=EXCHANGE_NAME, queue='fila.operador', routing_key=key)

    channel.queue_declare(queue='fila.tecnico', durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue='fila.tecnico', routing_key='os.criada')

    connection.close()


def publish_event(routing_key, payload):

    connection = get_connection()
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

    message = {
        'evento': routing_key,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dados': payload
    }

    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type='application/json'
        )
    )

    print(f" [x] Published {routing_key}")
    connection.close()
