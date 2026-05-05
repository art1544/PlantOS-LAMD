# lib/

Código-fonte do App Operador, organizado em Clean Architecture:

- **models/** — Classes de dados Dart (OrdemServico, Material)
- **services/** — ApiService (REST), AmqpService (AMQP), SyncService (outbox + reconexão), ConnectivityService
- **screens/** — Telas: Lista de OS, Detalhes da OS, Criar nova OS
