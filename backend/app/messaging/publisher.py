import pika
import os
import json

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
EXCHANGE_NAME = 'plantos.events'

def get_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    return connection

def setup_exchange():
    connection = get_connection()
    channel = connection.channel()
    # Usando Direct Exchange para roteamento 1-a-1 com as filas dinâmicas dos usuários
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)
    connection.close()

def publish_event(user_id, event_type, payload):
    """
    Publica um evento para um usuário específico.
    user_id: string identificando o usuário (ex: 'op_123', 'tec_456')
    """
    connection = get_connection()
    channel = connection.channel()
    
    # Garante que a exchange existe
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)
    
    message = {
        'event_type': event_type,
        'payload': payload
    }
    
    # No AMQP Direct, a routing_key deve corresponder EXATAMENTE à binding_key
    # usada pelo app cliente ao criar sua fila temporária.
    routing_key = str(user_id)
    
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=1,  # Não precisa ser persistente na fila, pois filas são efémeras (auto-delete)
            content_type='application/json'
        )
    )
    
    print(f" [x] Sent {event_type} to routing_key {routing_key}")
    connection.close()
