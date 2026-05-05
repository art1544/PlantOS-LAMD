# app/

Módulo principal do backend, organizado por responsabilidade:

- **database.py** — Conexão com SQLite, inicialização do schema
- **models/** — Classes de acesso a dados (OrdemServico, Material)
- **routes/** — Blueprints Flask com endpoints REST
- **services/** — Lógica de negócio (validação de transições, regras)
- **messaging/** — Publicador de eventos AMQP para o RabbitMQ
