# App Operador — PlantOS

Aplicativo Flutter para o **operador** de planta industrial (perfil cliente).

## Funcionalidades

- Criar ordens de serviço (título, descrição, setor, equipamento, prioridade)
- Listar e acompanhar status das OS em tempo real
- Receber notificações AMQP de aceite/recusa/conclusão
- Visualizar laudo técnico e materiais utilizados
- Funcionar offline com sync automático ao reconectar

## Estrutura

```
lib/
├── models/       # Classes de dados (OrdemServico, Material)
├── services/     # ApiService, AmqpService, SyncService, ConnectivityService
└── screens/      # Lista de OS, Detalhes, Criar OS
```

## Dependências principais

- `http` ou `dio` — REST
- `dart_amqp` — AMQP direto com RabbitMQ
- `sqflite` — SQLite local (cache + outbox)
- `connectivity_plus` — Detecção de rede
- `provider` — Gerenciamento de estado
