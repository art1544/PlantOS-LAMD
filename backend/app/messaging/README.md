# messaging/

Integração com RabbitMQ via biblioteca `pika`:

- **publisher.py** — Publica eventos na exchange `plantos.events` (direct, durable) com mensagens persistentes (delivery_mode=2)

Routing keys usadas: `os.criada`, `os.aceita`, `os.recusada`, `os.em_andamento`, `os.concluida`
