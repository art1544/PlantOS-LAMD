# infra/

Infraestrutura do PlantOS via Podman Compose.

## Serviços

- **RabbitMQ 3.12-management** — Message broker AMQP
  - Porta 5672: AMQP (comunicação de eventos)
  - Porta 15672: Painel de administração web
  - Credenciais dev: guest / guest

## Como usar

```bash
cd infra
podman compose up -d
```

Painel admin: http://localhost:15672

## Topologia configurada pelo backend

- Exchange: `plantos.events` (direct, durable)
- Filas: `fila.operador` e `fila.tecnico` (duráveis, mensagens persistentes)
- Bindings: routing keys `os.criada`, `os.aceita`, `os.recusada`, `os.em_andamento`, `os.concluida`
