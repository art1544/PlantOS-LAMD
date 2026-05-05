# services/

Camada de comunicação e sincronização:

- **ApiService** — Requisições HTTP REST ao backend (CRUD de OS e materiais)
- **AmqpService** — Conexão AMQP direta com RabbitMQ (fila.operador, durável) + reconexão com backoff exponencial
- **SyncService** — Orquestra o fluxo de reconexão: sync-first (GET /os) → reconcile outbox → drain outbox
- **ConnectivityService** — Monitora estado da rede via `connectivity_plus`
- **DatabaseService** — Acesso ao SQLite local (cache + outbox)
