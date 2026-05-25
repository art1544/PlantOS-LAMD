"""
Consumidor RabbitMQ do PlantOS.

Esta é a **evidência de comunicação assíncrona** exigida pela Sprint 2.

O worker executa fora do processo Flask (entry-point `backend/worker.py`) e:

  * Conecta às filas duráveis `fila.operador` e `fila.tecnico`
  * Consome cada evento publicado pelo backend (sem qualquer chamada REST)
  * Persiste o evento em uma tabela de auditoria (`evento_log`)
  * Imprime no console um log estruturado, simulando a notificação que será
    posteriormente entregue aos apps Flutter nas Sprints 3 e 4.

Como rodar:
    cd backend
    python worker.py
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone

import pika

from app.database import get_connection
from app.messaging.publisher import EXCHANGE_NAME, get_connection as get_amqp_connection


QUEUES = ('fila.operador', 'fila.tecnico')


def _log_evento(queue: str, routing_key: str, payload: dict) -> None:
    """Persiste evento recebido na tabela `evento_log` (auditoria)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evento_log (fila, routing_key, payload, recebido_em)
            VALUES (?, ?, ?, ?)
            """,
            (
                queue,
                routing_key,
                json.dumps(payload, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _build_handler(queue_name: str):
    def handler(channel, method, properties, body):
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            print(f" [!] [{queue_name}] mensagem inválida (não-JSON), descartando")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        routing_key = method.routing_key
        os_id = (payload.get('dados') or {}).get('id', '?')
        status = (payload.get('dados') or {}).get('status', '?')

        print(
            f" [<] [{queue_name}] {routing_key} | OS #{os_id} | status={status} "
            f"| ts={payload.get('timestamp')}"
        )

        try:
            _log_evento(queue_name, routing_key, payload)
        except Exception as exc:
            print(f" [!] falha ao gravar audit log: {exc}")

        channel.basic_ack(delivery_tag=method.delivery_tag)

    return handler


def run(max_messages: int | None = None) -> int:
    """
    Inicia o consumer em loop. Bloqueia até receber SIGINT/SIGTERM.

    Args:
        max_messages: Se informado, encerra após processar N mensagens
                      (útil para testes automatizados).
    Returns:
        Quantidade de mensagens processadas antes do encerramento.
    """
    print(f" [*] Conectando ao RabbitMQ em {os.getenv('RABBITMQ_HOST', 'localhost')}...")

    while True:
        try:
            connection = get_amqp_connection()
            break
        except pika.exceptions.AMQPConnectionError as exc:
            print(f" [!] RabbitMQ indisponível ({exc}). Tentando novamente em 3s...")
            time.sleep(3)

    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)

    for q in QUEUES:
        channel.queue_declare(queue=q, durable=True)

    channel.basic_qos(prefetch_count=10)

    processed = {'count': 0}

    def wrap(queue_name: str):
        inner = _build_handler(queue_name)

        def cb(ch, method, props, body):
            inner(ch, method, props, body)
            processed['count'] += 1
            if max_messages is not None and processed['count'] >= max_messages:
                ch.stop_consuming()

        return cb

    for q in QUEUES:
        channel.basic_consume(queue=q, on_message_callback=wrap(q), auto_ack=False)

    print(f" [*] Aguardando eventos nas filas {QUEUES}. CTRL+C para sair.")

    def _shutdown(*_):
        print("\n [*] Encerrando consumer...")
        try:
            channel.stop_consuming()
        except Exception:
            pass

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        channel.start_consuming()
    finally:
        try:
            connection.close()
        except Exception:
            pass

    print(f" [*] Consumer encerrado. Mensagens processadas: {processed['count']}")
    return processed['count']


if __name__ == "__main__":
    sys.exit(0 if run() is not None else 1)
