# lib/

Código-fonte do App Técnico, organizado em Clean Architecture:

- **models/** — Classes de dados Dart (OrdemServico, Material)
- **services/** — ApiService (REST), AmqpService (AMQP), SyncService (outbox + reconexão), ConnectivityService
- **screens/** — Telas: Lista de OS pendentes, Detalhes (aceitar/recusar/iniciar), OS em andamento
