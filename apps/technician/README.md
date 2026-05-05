# App Técnico — PlantOS

Aplicativo Flutter para o **técnico de manutenção** (perfil prestador de serviço).

## Funcionalidades

- Receber novas OS em tempo real via AMQP
- Aceitar ou recusar ordens de serviço
- Iniciar execução e registrar materiais utilizados
- Concluir OS com laudo técnico
- Funcionar offline com sync automático ao reconectar

## Estrutura

```
lib/
├── models/       # Classes de dados (OrdemServico, Material)
├── services/     # ApiService, AmqpService, SyncService, ConnectivityService
└── screens/      # Lista de OS pendentes, Detalhes, OS em andamento
```

## Dependências principais

- `http` ou `dio` — REST
- `dart_amqp` — AMQP direto com RabbitMQ
- `sqflite` — SQLite local (cache + outbox)
- `connectivity_plus` — Detecção de rede
- `provider` — Gerenciamento de estado
