from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pika

from app.database import get_connection, init_db
from app.messaging.consumer import run as run_consumer
from app.messaging.publisher import EXCHANGE_NAME, publish_event, setup_queues


def _ping_rabbit() -> bool:
    try:
        c = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', socket_timeout=2))
        c.close()
        return True
    except Exception as exc:
        print(f"[ERRO] RabbitMQ indisponível: {exc}")
        return False


def main() -> int:
    if not _ping_rabbit():
        print("\nSuba o RabbitMQ primeiro:")
        print("    cd infra && docker compose up -d   (ou podman compose up -d)\n")
        return 1

    print("[1/5] Inicializando banco e filas...")
    init_db()
    setup_queues()

    conn = get_connection()
    conn.execute("DELETE FROM evento_log")
    conn.commit()
    conn.close()

    print("[2/5] Disparando consumer em thread (esperando 1 mensagem)...")
    consumer_thread = threading.Thread(
        target=run_consumer, kwargs={'max_messages': 1}, daemon=True
    )
    consumer_thread.start()
    time.sleep(2)

    print("[3/5] Publicando evento os.criada...")
    payload = {
        'id': 99999,
        'titulo': 'Teste Sprint 2',
        'status': 'aberta',
        'prioridade': 'alta',
        'operador_id': 'user-test',
        'criado_em': datetime.now(timezone.utc).isoformat(),
    }
    publish_event('os.criada', payload)

    print("[4/5] Aguardando consumer processar (até 10s)...")
    consumer_thread.join(timeout=10)

    print("[5/5] Verificando audit log...")
    conn = get_connection()
    rows = conn.execute(
        "SELECT fila, routing_key, payload, recebido_em FROM evento_log ORDER BY id DESC LIMIT 5"
    ).fetchall()
    conn.close()

    if not rows:
        print("\nFALHA: nenhum evento gravado em evento_log.")
        return 2

    print(f"\nSUCESSO — {len(rows)} evento(s) consumido(s):")
    for r in rows:
        data = json.loads(r['payload'])
        print(f"  • fila={r['fila']:<15} key={r['routing_key']:<18} "
              f"os_id={data.get('dados', {}).get('id')} recebido_em={r['recebido_em']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
